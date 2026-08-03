"""Opsiyonel yeniden eğitim ucu: yüklenen veriyle modelleri arka planda yeniden eğitir.

Talimat ve işlem verileri bağımsız yüklenip eğitilebildiğinden, her eğitim
isteği bir `metric_type` ("talimat" | "islem") taşır ve kendi `RETRAIN_STATUS`
girdisine yazar — böylece ikisi paralel/ardışık tetiklenip birbirinin
ilerleme durumunu ezmez.
"""
import threading
from datetime import datetime

import numpy as np
import pandas as pd
from fastapi import APIRouter, HTTPException

from src.evaluation.metrics import mape as calc_mape
from src.pipeline import registry_filename, _load_registry, forecast_pipeline, train_pipeline

from .schemas import RetrainRequest
from .state import RETRAIN_STATUS, STATE, METRIC_TYPES

router = APIRouter(prefix="/api", tags=["train"])


def _event_message(event: dict) -> str:
    kind = event["kind"]
    if kind == "data_ready":
        return (
            f"{event['row_count']} kayıt yüklendi, "
            f"{len(event['transaction_types'])} işlem tipi, {len(event.get('teams', []))} ekip tespit edildi "
            f"({', '.join(event['transaction_types'])})."
        )
    if kind == "holdout_set":
        return (
            f"Son {event['holdout_days']} gün doğrulama için ayrıldı "
            f"({event['holdout_start']} – {event['holdout_end']}). "
            f"Model bu tarihler hariç eğitilecek."
        )
    if kind == "plan":
        return (
            f"{len(event.get('teams', []))} ekip × {len(event['types'])} işlem tipi × "
            f"{len(event['freqs'])} frekans = {event['total_units']} model eğitilecek."
        )
    if kind == "unit_start":
        return f"[{event['index']}/{event['total']}] {event['team']} / {event['type']} / {event['freq']} için eğitim başlıyor..."
    if kind == "selection_start":
        return (
            f"{event['type']} / {event['freq']}: {len(event['candidates'])} algoritma "
            f"deneniyor ({', '.join(event['candidates'])})."
        )
    if kind == "model_evaluated":
        return (
            f"{event['type']} / {event['freq']}: {event['model']} değerlendirildi — "
            f"CV {event['metric'].upper()} = {event['score']:.4f}"
        )
    if kind == "model_selected":
        return f"{event['type']} / {event['freq']} için seçilen algoritma: {event['model']} — {event['reason']}"
    if kind == "unit_done":
        return (
            f"{event['team']} / {event['type']} / {event['freq']} tamamlandı — "
            f"model: {event['model']}, CV RMSE: {event['cv_rmse']:.4f}"
        )
    if kind == "unit_failed":
        return f"{event['team']} / {event['type']} / {event['freq']} eğitilemedi — hata: {event['error']}"
    if kind == "completed":
        return f"Tüm modeller eğitildi ve kaydedildi: {event['registry_path']}"
    if kind == "holdout_forecast":
        return event.get("message", "Doğrulama tahmini hesaplanıyor…")
    if kind == "holdout_done":
        return event.get("message", "Doğrulama tamamlandı.")
    return kind


def _on_event(status, event: dict) -> None:
    step = {**event, "message": _event_message(event)}
    status.add_step(step)
    status.message = step["message"]

    if event["kind"] == "plan":
        status.total_units = event["total_units"]
        status.completed_units = 0
        status.progress = 0.0
    elif event["kind"] in ("unit_done", "unit_failed"):
        status.completed_units += 1
        if status.total_units:
            status.progress = status.completed_units / status.total_units


def _clean_mape(value) -> float | None:
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return None
    return round(float(value), 2)


def _run_holdout_forecast(metric_type: str, holdout_days: int) -> None:
    """Eğitim sonrası holdout dönemi için otomatik tahmin + ekip bazlı/toplam MAPE hesabı.

    Kayıtlı tüm modeller için ayrı ayrı tahmin üretir; her modelin MAPE değerini
    hesaplayıp karşılaştırma yapılabilmesi için sonuca ekler.
    """
    status = RETRAIN_STATUS[metric_type]
    ds = STATE.get(metric_type)
    if ds.daily_agg is None or ds.daily_agg.empty:
        return

    max_date = ds.daily_agg["date"].max()
    holdout_start = max_date - pd.Timedelta(days=holdout_days - 1)
    holdout_start_str = holdout_start.strftime("%Y-%m-%d")
    max_date_str = max_date.strftime("%Y-%m-%d")

    status.add_step({
        "kind": "holdout_forecast",
        "message": f"Son {holdout_days} gün ({holdout_start_str} – {max_date_str}) için doğrulama tahmini hesaplanıyor…",
    })
    status.message = f"Doğrulama tahmini hesaplanıyor ({holdout_start_str} – {max_date_str})…"

    registry_path = registry_filename(metric_type)

    # Kayıtlı tüm model isimlerini bul (daily frekans için)
    models_to_run = None
    try:
        registry = _load_registry(registry_path)
        avail_names: set = set()
        for team, by_type in registry["models"].items():
            for tt, by_freq in by_type.items():
                entry = by_freq.get("daily")
                if not entry:
                    continue
                avail = entry.get("available_models") or {entry["best_model"]: {}}
                avail_names.update(avail.keys())
        if len(avail_names) > 1:
            models_to_run = sorted(avail_names)
    except Exception:
        pass

    try:
        forecast_result = forecast_pipeline(
            start=holdout_start_str,
            end=max_date_str,
            metric_type=metric_type,
            freq="daily",
            fmt=[],
            plot=False,
            registry_path=registry_path,
            historical_data={"daily": ds.daily_agg, "hourly": ds.hourly_agg},
            models=models_to_run,
        )
    except Exception as e:
        status.add_step({
            "kind": "holdout_failed",
            "message": f"Doğrulama tahmini başarısız: {e}",
        })
        return

    by_team_result: dict = {}
    all_y_true: list = []
    all_y_pred: list = []
    # Model bazında tüm ekip/tip toplamı için biriktiriciler
    model_all_true: dict = {}
    model_all_pred: dict = {}

    for team, by_type in forecast_result.get("by_team", {}).items():
        team_y_true: list = []
        team_y_pred: list = []
        by_type_result: dict = {}

        for tt, info in by_type.items():
            daily_list = info.get("daily", [])
            if not daily_list:
                continue

            actual_subset = ds.daily_agg[
                (ds.daily_agg["team"] == team)
                & (ds.daily_agg["transaction_type"] == tt)
                & (ds.daily_agg["date"] >= holdout_start)
            ]
            actual_by_date = dict(
                zip(
                    actual_subset["date"].dt.strftime("%Y-%m-%d"),
                    actual_subset["count"].astype(float),
                )
            )

            rows: list = []
            y_true: list = []
            y_pred: list = []
            for entry in daily_list:
                d = entry["date"]
                if d in actual_by_date:
                    actual = actual_by_date[d]
                    predicted = entry["predicted_count"]
                    rows.append({"date": d, "actual": round(actual, 1), "predicted": round(predicted, 1)})
                    y_true.append(actual)
                    y_pred.append(predicted)

            mape_val = calc_mape(np.array(y_true), np.array(y_pred)) if y_true else None

            # Her model için bu (ekip, işlem tipi) MAPE'sini hesapla
            model_mapes: dict = {}
            for model_name, model_info in info.get("models", {}).items():
                yt_m: list = []
                yp_m: list = []
                for entry in model_info.get("daily", []):
                    d = entry["date"]
                    if d in actual_by_date:
                        yt_m.append(actual_by_date[d])
                        yp_m.append(entry["predicted_count"])
                mape_m = calc_mape(np.array(yt_m), np.array(yp_m)) if yt_m else None
                model_mapes[model_name] = _clean_mape(mape_m)
                model_all_true.setdefault(model_name, []).extend(yt_m)
                model_all_pred.setdefault(model_name, []).extend(yp_m)

            by_type_result[tt] = {
                "mape": _clean_mape(mape_val),
                "rows": rows,
                "model_mapes": model_mapes,
            }
            team_y_true.extend(y_true)
            team_y_pred.extend(y_pred)

        team_mape = calc_mape(np.array(team_y_true), np.array(team_y_pred)) if team_y_true else None
        by_team_result[team] = {
            "mape": _clean_mape(team_mape),
            "by_type": by_type_result,
        }
        all_y_true.extend(team_y_true)
        all_y_pred.extend(team_y_pred)

    overall = calc_mape(np.array(all_y_true), np.array(all_y_pred)) if all_y_true else None
    overall_clean = _clean_mape(overall)

    # Model bazında genel MAPE (tüm ekip/tip birleşik)
    model_overall_mapes: dict = {}
    for model_name, yt_list in model_all_true.items():
        yp_list = model_all_pred.get(model_name, [])
        m = calc_mape(np.array(yt_list), np.array(yp_list)) if yt_list else None
        model_overall_mapes[model_name] = _clean_mape(m)

    status.holdout_result = {
        "holdout_range": {"start": holdout_start_str, "end": max_date_str},
        "by_team": by_team_result,
        "overall_mape": overall_clean,
        "model_overall_mapes": model_overall_mapes,
    }

    mape_txt = f"{overall_clean:.1f}%" if overall_clean is not None else "—"
    done_msg = f"Doğrulama tamamlandı — Genel MAPE: {mape_txt}"
    status.add_step({"kind": "holdout_done", "message": done_msg})
    status.message = done_msg


def _run_training(
    metric_type: str,
    input_path: str,
    freq: str,
    teams: list[str] | None,
    types: list[str] | None,
    models: list[str] | None,
    holdout_days: int = 0,
) -> None:
    status = RETRAIN_STATUS[metric_type]
    status.reset()
    status.metric_type = metric_type
    status.status = "running"
    status.holdout_days = holdout_days
    status.message = "Modeller yeniden eğitiliyor..."
    status.started_at = datetime.now()
    status.finished_at = None
    try:
        train_pipeline(
            input_path=input_path, freq=freq, teams=teams, types=types, models=models or ["auto"],
            report=False, progress_callback=lambda e: _on_event(status, e), holdout_days=holdout_days,
        )
        if holdout_days > 0:
            _run_holdout_forecast(metric_type, holdout_days)
        status.status = "done"
        status.message = "Modeller başarıyla yeniden eğitildi."
        status.progress = 1.0
    except Exception as e:
        status.status = "error"
        status.message = f"Eğitim sırasında hata oluştu: {e}"
        status.add_step({"kind": "error", "message": status.message})
    finally:
        status.finished_at = datetime.now()


@router.post("/retrain")
async def start_retrain(req: RetrainRequest):
    if req.metric_type not in METRIC_TYPES:
        raise HTTPException(status_code=400, detail=f"Geçersiz metric_type: {req.metric_type}")

    ds = STATE.get(req.metric_type)
    if not ds.is_loaded() or not ds.uploaded_path:
        raise HTTPException(
            status_code=400,
            detail="Yeniden eğitim için yüklenmiş bir CSV gerekir.",
        )
    if RETRAIN_STATUS[req.metric_type].status == "running":
        raise HTTPException(status_code=409, detail="Bu metrik için zaten devam eden bir eğitim var.")

    thread = threading.Thread(
        target=_run_training,
        args=(req.metric_type, ds.uploaded_path, req.freq, req.teams, req.types, req.models, req.holdout_days),
        daemon=True,
    )
    thread.start()

    return {"status": "started"}


@router.get("/retrain/status")
async def retrain_status(metric_type: str = "talimat"):
    if metric_type not in METRIC_TYPES:
        raise HTTPException(status_code=400, detail=f"Geçersiz metric_type: {metric_type}")
    status = RETRAIN_STATUS[metric_type]
    return {
        "metric_type": metric_type,
        "status": status.status,
        "message": status.message,
        "started_at": status.started_at.isoformat() if status.started_at else None,
        "finished_at": status.finished_at.isoformat() if status.finished_at else None,
        "progress": status.progress,
        "total_units": status.total_units,
        "completed_units": status.completed_units,
        "steps": status.steps,
        "holdout_days": status.holdout_days,
        "holdout_result": status.holdout_result,
    }
