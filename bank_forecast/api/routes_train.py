"""Opsiyonel yeniden eğitim ucu: yüklenen veriyle modelleri arka planda yeniden eğitir."""
import threading
from datetime import datetime

import numpy as np
import pandas as pd
from fastapi import APIRouter, HTTPException

from src.evaluation.metrics import mape as calc_mape
from src.pipeline import REGISTRY_FILE, _load_registry, forecast_pipeline, train_pipeline

from .schemas import RetrainRequest
from .state import RETRAIN_STATUS, STATE

router = APIRouter(prefix="/api", tags=["train"])


def _event_message(event: dict) -> str:
    kind = event["kind"]
    if kind == "data_ready":
        return (
            f"{event['row_count']} kayıt yüklendi, "
            f"{len(event['transaction_types'])} işlem tipi tespit edildi "
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
            f"{len(event['types'])} işlem tipi × {len(event['freqs'])} frekans = "
            f"{event['total_units']} model eğitilecek."
        )
    if kind == "unit_start":
        return f"[{event['index']}/{event['total']}] {event['type']} / {event['freq']} için eğitim başlıyor..."
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
            f"{event['type']} / {event['freq']} tamamlandı — "
            f"model: {event['model']}, CV RMSE: {event['cv_rmse']:.4f}"
        )
    if kind == "unit_failed":
        return f"{event['type']} / {event['freq']} eğitilemedi — hata: {event['error']}"
    if kind == "completed":
        return f"Tüm modeller eğitildi ve kaydedildi: {event['registry_path']}"
    if kind == "holdout_forecast":
        return event.get("message", "Doğrulama tahmini hesaplanıyor…")
    if kind == "holdout_done":
        return event.get("message", "Doğrulama tamamlandı.")
    return kind


def _on_event(event: dict) -> None:
    step = {**event, "message": _event_message(event)}
    RETRAIN_STATUS.add_step(step)
    RETRAIN_STATUS.message = step["message"]

    if event["kind"] == "plan":
        RETRAIN_STATUS.total_units = event["total_units"]
        RETRAIN_STATUS.completed_units = 0
        RETRAIN_STATUS.progress = 0.0
    elif event["kind"] in ("unit_done", "unit_failed"):
        RETRAIN_STATUS.completed_units += 1
        if RETRAIN_STATUS.total_units:
            RETRAIN_STATUS.progress = RETRAIN_STATUS.completed_units / RETRAIN_STATUS.total_units


def _run_holdout_forecast(holdout_days: int) -> None:
    """Eğitim sonrası holdout dönemi için otomatik tahmin + MAPE hesabı.

    Kayıtlı tüm modeller için ayrı ayrı tahmin üretir; her modelin MAPE değerini
    hesaplayıp karşılaştırma yapılabilmesi için sonuca ekler.
    """
    if STATE.daily_agg is None or STATE.daily_agg.empty:
        return

    max_date = STATE.daily_agg["date"].max()
    holdout_start = max_date - pd.Timedelta(days=holdout_days - 1)
    holdout_start_str = holdout_start.strftime("%Y-%m-%d")
    max_date_str = max_date.strftime("%Y-%m-%d")

    RETRAIN_STATUS.add_step({
        "kind": "holdout_forecast",
        "message": f"Son {holdout_days} gün ({holdout_start_str} – {max_date_str}) için doğrulama tahmini hesaplanıyor…",
    })
    RETRAIN_STATUS.message = f"Doğrulama tahmini hesaplanıyor ({holdout_start_str} – {max_date_str})…"

    # Kayıtlı tüm model isimlerini bul (daily frekans için)
    models_to_run = None
    try:
        registry = _load_registry(REGISTRY_FILE)
        avail_names: set = set()
        for key, entry in registry["models"].items():
            if key.endswith("_daily"):
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
            freq="daily",
            fmt=[],
            plot=False,
            registry_path=REGISTRY_FILE,
            historical_data={"daily": STATE.daily_agg, "hourly": STATE.hourly_agg},
            models=models_to_run,
        )
    except Exception as e:
        RETRAIN_STATUS.add_step({
            "kind": "holdout_failed",
            "message": f"Doğrulama tahmini başarısız: {e}",
        })
        return

    by_type_result: dict = {}
    all_y_true: list = []
    all_y_pred: list = []
    # Model bazında tüm işlem tipleri toplamı için biriktiriciler
    model_all_true: dict = {}
    model_all_pred: dict = {}

    for tt, info in forecast_result.get("by_type", {}).items():
        daily_list = info.get("daily", [])
        if not daily_list:
            continue

        actual_subset = STATE.daily_agg[
            (STATE.daily_agg["transaction_type"] == tt)
            & (STATE.daily_agg["date"] >= holdout_start)
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

        # Her model için bu işlem tipi MAPE'sini hesapla
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
            model_mapes[model_name] = (
                round(mape_m, 2) if mape_m is not None and not np.isnan(mape_m) else None
            )
            model_all_true.setdefault(model_name, []).extend(yt_m)
            model_all_pred.setdefault(model_name, []).extend(yp_m)

        by_type_result[tt] = {
            "mape": round(mape_val, 2) if mape_val is not None and not np.isnan(mape_val) else None,
            "rows": rows,
            "model_mapes": model_mapes,
        }
        all_y_true.extend(y_true)
        all_y_pred.extend(y_pred)

    overall = calc_mape(np.array(all_y_true), np.array(all_y_pred)) if all_y_true else None
    overall_clean = round(float(overall), 2) if overall is not None and not np.isnan(overall) else None

    # Model bazında genel MAPE (tüm işlem tipleri birleşik)
    model_overall_mapes: dict = {}
    for model_name, yt_list in model_all_true.items():
        yp_list = model_all_pred.get(model_name, [])
        m = calc_mape(np.array(yt_list), np.array(yp_list)) if yt_list else None
        model_overall_mapes[model_name] = (
            round(float(m), 2) if m is not None and not np.isnan(m) else None
        )

    RETRAIN_STATUS.holdout_result = {
        "holdout_range": {"start": holdout_start_str, "end": max_date_str},
        "by_type": by_type_result,
        "overall_mape": overall_clean,
        "model_overall_mapes": model_overall_mapes,
    }

    mape_txt = f"{overall_clean:.1f}%" if overall_clean is not None else "—"
    done_msg = f"Doğrulama tamamlandı — Genel MAPE: {mape_txt}"
    RETRAIN_STATUS.add_step({"kind": "holdout_done", "message": done_msg})
    RETRAIN_STATUS.message = done_msg


def _run_training(input_path: str, freq: str, types: list[str] | None, models: list[str] | None, holdout_days: int = 0) -> None:
    RETRAIN_STATUS.reset()
    RETRAIN_STATUS.status = "running"
    RETRAIN_STATUS.holdout_days = holdout_days
    RETRAIN_STATUS.message = "Modeller yeniden eğitiliyor..."
    RETRAIN_STATUS.started_at = datetime.now()
    RETRAIN_STATUS.finished_at = None
    try:
        train_pipeline(
            input_path=input_path, freq=freq, types=types, models=models or ["auto"],
            report=False, progress_callback=_on_event, holdout_days=holdout_days,
        )
        if holdout_days > 0:
            _run_holdout_forecast(holdout_days)
        RETRAIN_STATUS.status = "done"
        RETRAIN_STATUS.message = "Modeller başarıyla yeniden eğitildi."
        RETRAIN_STATUS.progress = 1.0
    except Exception as e:
        RETRAIN_STATUS.status = "error"
        RETRAIN_STATUS.message = f"Eğitim sırasında hata oluştu: {e}"
        RETRAIN_STATUS.add_step({"kind": "error", "message": RETRAIN_STATUS.message})
    finally:
        RETRAIN_STATUS.finished_at = datetime.now()


@router.post("/retrain")
async def start_retrain(req: RetrainRequest):
    if not STATE.is_loaded() or not STATE.uploaded_path:
        raise HTTPException(
            status_code=400,
            detail="Yeniden eğitim için yüklenmiş bir CSV gerekir (demo veri ile yeniden eğitim desteklenmez).",
        )
    if RETRAIN_STATUS.status == "running":
        raise HTTPException(status_code=409, detail="Zaten devam eden bir eğitim var.")

    thread = threading.Thread(
        target=_run_training,
        args=(STATE.uploaded_path, req.freq, req.types, req.models, req.holdout_days),
        daemon=True,
    )
    thread.start()

    return {"status": "started"}


@router.get("/retrain/status")
async def retrain_status():
    return {
        "status": RETRAIN_STATUS.status,
        "message": RETRAIN_STATUS.message,
        "started_at": RETRAIN_STATUS.started_at.isoformat() if RETRAIN_STATUS.started_at else None,
        "finished_at": RETRAIN_STATUS.finished_at.isoformat() if RETRAIN_STATUS.finished_at else None,
        "progress": RETRAIN_STATUS.progress,
        "total_units": RETRAIN_STATUS.total_units,
        "completed_units": RETRAIN_STATUS.completed_units,
        "steps": RETRAIN_STATUS.steps,
        "holdout_days": RETRAIN_STATUS.holdout_days,
        "holdout_result": RETRAIN_STATUS.holdout_result,
    }
