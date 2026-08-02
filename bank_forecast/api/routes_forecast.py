"""Tahmin üretme ucu: kayıtlı modellerle tahmin + gerçekleşen-vs-tahmin karşılaştırması
+ Excel'e aktarma.

Talimat ve işlem verileri aynı anda yüklü olabildiğinden, `/api/forecast`
`metric_type="both"` ile her iki metrik için de (yüklü ve eğitilmiş olanlar)
tahmin üretip aynı yanıt içinde döner — frontend bu ikisini yan yana gösterir.
"""
import io
import os

import pandas as pd
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from src.pipeline import forecast_pipeline, registry_filename, _load_registry

from . import comparison
from .schemas import ForecastRequest
from .state import STATE, METRIC_TYPES

router = APIRouter(prefix="/api", tags=["forecast"])


@router.get("/models/available")
async def available_models(metric_type: str = "talimat"):
    """Tahmin için seçilebilir, kayıtlı modelleri (ekip, işlem tipi, frekans) bazında döner."""
    if metric_type not in METRIC_TYPES:
        raise HTTPException(status_code=400, detail=f"Geçersiz metric_type: {metric_type}")

    registry_path = registry_filename(metric_type)
    if not os.path.exists(registry_path):
        return {"available": {}}

    registry = _load_registry(registry_path)
    out: dict = {}
    for team, by_type in registry["models"].items():
        for tt, by_freq in by_type.items():
            for f, entry in by_freq.items():
                avail = entry.get("available_models") or {entry["best_model"]: {}}
                out.setdefault(team, {}).setdefault(tt, {})[f] = {
                    "best_model": entry["best_model"],
                    "models": sorted(avail.keys()),
                }
    return {"available": out}


def _run_forecast_for_metric(metric_type: str, req: ForecastRequest, calibration_override: dict | None = None) -> dict | None:
    registry_path = registry_filename(metric_type)
    ds = STATE.get(metric_type)
    if not ds.is_loaded() or not os.path.exists(registry_path):
        return None

    try:
        forecast_result = forecast_pipeline(
            start=req.start,
            end=req.end,
            metric_type=metric_type,
            teams=req.teams,
            types=req.types,
            freq=req.freq,
            fmt=[],
            plot=False,
            registry_path=registry_path,
            historical_data={"daily": ds.daily_agg, "hourly": ds.hourly_agg},
            models=req.models,
            calibration_override=calibration_override,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Tahmin üretilemedi ({metric_type}): {e}")

    by_team = forecast_result.get("by_team", {})
    # Kayıt bulunamayan ekip/tipler boş sözlük olarak kalır — sonuçtan ayıkla
    by_team = {
        team: {tt: info for tt, info in by_type.items() if info}
        for team, by_type in by_team.items()
    }
    by_team = {team: by_type for team, by_type in by_team.items() if by_type}

    if not by_team:
        return None

    daily_comparison = comparison.build_daily_comparison(ds.daily_agg, by_team, req.start, req.end)
    hourly_comparison = comparison.build_hourly_comparison(ds.hourly_agg, by_team, req.start, req.end)
    totals = comparison.compute_totals(by_team)
    mape_summary = comparison.compute_mape_summary(daily_comparison)

    return {
        "forecast": {
            "generated_at": forecast_result["generated_at"],
            "forecast_range": forecast_result["forecast_range"],
            "by_team": by_team,
        },
        "comparison": {
            "daily": daily_comparison,
            "hourly": hourly_comparison,
        },
        "totals": totals,
        "mape_summary": mape_summary,
    }


@router.post("/forecast")
async def create_forecast(req: ForecastRequest):
    metric_types = list(METRIC_TYPES) if req.metric_type == "both" else [req.metric_type]
    for mt in metric_types:
        if mt not in METRIC_TYPES:
            raise HTTPException(status_code=400, detail=f"Geçersiz metric_type: {mt}")

    if not any(STATE.get(mt).is_loaded() for mt in metric_types):
        raise HTTPException(status_code=400, detail="Önce bir CSV veya demo veri yükleyin.")

    results = {mt: _run_forecast_for_metric(mt, req) for mt in metric_types}

    if not any(results.values()):
        raise HTTPException(
            status_code=404,
            detail="Seçilen metrik(ler) için kayıtlı model veya yüklü veri bulunamadı. Önce ilgili verinin eğitimi yapılmalı.",
        )

    return results


def _flatten_forecast_rows(results: dict) -> pd.DataFrame:
    """Excel için: metrik × ekip × işlem tipi × tarih bazlı düz (tidy) tablo."""
    rows = []
    for metric_type, payload in results.items():
        if not payload:
            continue
        by_team = payload["forecast"]["by_team"]
        for team, by_type in by_team.items():
            for tt, info in by_type.items():
                model_used = info.get("model_used")
                for entry in info.get("daily", []):
                    rows.append({
                        "Metrik": metric_type,
                        "Ekip": team,
                        "İşlem Tipi": tt,
                        "Tarih": entry["date"],
                        "Tahmin": entry["predicted_count"],
                        "Alt Sınır (%80)": entry["lower_80"],
                        "Üst Sınır (%80)": entry["upper_80"],
                        "Model": model_used,
                    })
    return pd.DataFrame(rows)


def _summary_rows(results: dict) -> pd.DataFrame:
    """Excel özet sayfası için: metrik × ekip × işlem tipi toplam referans adedi."""
    rows = []
    for metric_type, payload in results.items():
        if not payload:
            continue
        totals = payload["totals"]["by_team"]
        for team, team_info in totals.items():
            for tt, tt_info in team_info["by_type"].items():
                rows.append({
                    "Metrik": metric_type,
                    "Ekip": team,
                    "İşlem Tipi": tt,
                    "Toplam Tahmin": tt_info["predicted_count"],
                    "Model": tt_info["model_used"],
                })
    return pd.DataFrame(rows)


@router.post("/forecast/export")
async def export_forecast(req: ForecastRequest):
    """Mevcut tahmin parametreleriyle tahmini yeniden üretip ekip × işlem tipi ×
    metrik kırılımlı bir `.xlsx` döner (bkz. plan madde 5)."""
    metric_types = list(METRIC_TYPES) if req.metric_type == "both" else [req.metric_type]
    for mt in metric_types:
        if mt not in METRIC_TYPES:
            raise HTTPException(status_code=400, detail=f"Geçersiz metric_type: {mt}")

    results = {mt: _run_forecast_for_metric(mt, req) for mt in metric_types}
    if not any(results.values()):
        raise HTTPException(status_code=404, detail="Aktarılacak tahmin sonucu bulunamadı.")

    detail_df = _flatten_forecast_rows(results)
    summary_df = _summary_rows(results)

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        summary_df.to_excel(writer, sheet_name="Özet", index=False)
        detail_df.to_excel(writer, sheet_name="Günlük Detay", index=False)
    buffer.seek(0)

    filename = f"tahmin_{req.start}_{req.end}.xlsx"
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
