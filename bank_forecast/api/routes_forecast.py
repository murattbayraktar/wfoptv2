"""Tahmin üretme ucu: kayıtlı modellerle tahmin + gerçekleşen-vs-tahmin karşılaştırması."""
import os

from fastapi import APIRouter, HTTPException

from src.pipeline import forecast_pipeline, REGISTRY_FILE

from . import comparison
from .schemas import ForecastRequest
from .state import STATE

router = APIRouter(prefix="/api", tags=["forecast"])


@router.post("/forecast")
async def create_forecast(req: ForecastRequest):
    if not STATE.is_loaded():
        raise HTTPException(status_code=400, detail="Önce bir CSV veya demo veri yükleyin.")

    if not os.path.exists(REGISTRY_FILE):
        raise HTTPException(
            status_code=400,
            detail="Eğitilmiş model bulunamadı (model_registry.json yok). Önce `python train.py` çalıştırılmalı.",
        )

    try:
        forecast_result = forecast_pipeline(
            start=req.start,
            end=req.end,
            types=req.types,
            freq=req.freq,
            fmt=[],
            plot=False,
            registry_path=REGISTRY_FILE,
            historical_data={"daily": STATE.daily_agg, "hourly": STATE.hourly_agg},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Tahmin üretilemedi: {e}")

    by_type = forecast_result.get("by_type", {})
    # Kayıt bulunamayan tipler boş sözlük olarak kalır — sonuçtan ayıkla
    by_type = {tt: info for tt, info in by_type.items() if info}

    if not by_type:
        raise HTTPException(
            status_code=404,
            detail="Seçilen tipler için kayıtlı model bulunamadı. Önce ilgili tipler eğitilmeli.",
        )

    daily_comparison = comparison.build_daily_comparison(STATE.daily_agg, by_type, req.start, req.end)
    hourly_comparison = comparison.build_hourly_comparison(STATE.hourly_agg, by_type, req.start, req.end)
    totals = comparison.compute_totals(by_type)

    return {
        "forecast": {
            "generated_at": forecast_result["generated_at"],
            "forecast_range": forecast_result["forecast_range"],
            "by_type": by_type,
        },
        "comparison": {
            "daily": daily_comparison,
            "hourly": hourly_comparison,
        },
        "totals": totals,
    }
