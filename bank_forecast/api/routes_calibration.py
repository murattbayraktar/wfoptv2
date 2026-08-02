"""Kalibrasyon ucu: gerçekleşen-vs-tahmin sapma analizi (hotspot raporu),
işlem tipi bazlı çarpan önerisi, çarpan config'inin okunması/kaydedilmesi ve
kaydetmeden önce önizleme (mevcut vs önerilen MAPE farkı).

Forecast+karşılaştırma akışı `routes_forecast._run_forecast_for_metric` ile
birebir aynı — burada tekrar yazılmaz, olduğu gibi çağrılır.
"""
from fastapi import APIRouter, HTTPException

from src.analysis.calibration_analysis import compute_hotspots
from src.analysis.calibration_multipliers import compute_suggested_multipliers
from src.calibration_config import load_calibration, save_calibration

from .routes_forecast import _run_forecast_for_metric
from .schemas import CalibrationAnalyzeRequest, CalibrationConfigBody, CalibrationPreviewRequest, ForecastRequest
from .state import METRIC_TYPES

router = APIRouter(prefix="/api/calibration", tags=["calibration"])

MULTIPLIER_MIN, MULTIPLIER_MAX = 0.1, 5.0


def _validate_config_body(body: CalibrationConfigBody) -> None:
    for tt, by_pattern in body.multipliers.items():
        for pattern, value in by_pattern.items():
            if not (MULTIPLIER_MIN <= value <= MULTIPLIER_MAX):
                raise HTTPException(
                    status_code=422,
                    detail=f"Çarpan aralık dışı: {tt}/{pattern}={value} (izin verilen aralık {MULTIPLIER_MIN}-{MULTIPLIER_MAX})",
                )
    for d in body.half_days:
        try:
            year, month, day = d.split("-")
            if not (len(year) == 4 and len(month) == 2 and len(day) == 2):
                raise ValueError
        except ValueError:
            raise HTTPException(status_code=422, detail=f"Geçersiz tarih formatı (YYYY-MM-DD bekleniyor): {d}")


def _to_forecast_request(req: CalibrationAnalyzeRequest, freq: str) -> ForecastRequest:
    return ForecastRequest(
        start=req.start, end=req.end, metric_type=req.metric_type,
        teams=req.teams, types=req.types, freq=freq, models=None,
    )


@router.get("/config")
async def get_config():
    return load_calibration()


@router.put("/config")
async def put_config(body: CalibrationConfigBody):
    _validate_config_body(body)
    return save_calibration({"multipliers": body.multipliers, "half_days": body.half_days})


@router.post("/analyze")
async def analyze(req: CalibrationAnalyzeRequest):
    if req.metric_type not in METRIC_TYPES:
        raise HTTPException(status_code=400, detail=f"Geçersiz metric_type: {req.metric_type}")

    result = _run_forecast_for_metric(req.metric_type, _to_forecast_request(req, freq="both"))
    if result is None:
        raise HTTPException(status_code=404, detail="Analiz için yüklü veri veya kayıtlı model bulunamadı.")

    half_days = set(load_calibration().get("half_days", []))
    return compute_hotspots(
        result["comparison"]["daily"], result["comparison"]["hourly"], half_days,
        min_samples=req.min_samples, error_threshold_pct=req.error_threshold_pct,
    )


@router.post("/multipliers/suggest")
async def suggest_multipliers(req: CalibrationAnalyzeRequest):
    if req.metric_type not in METRIC_TYPES:
        raise HTTPException(status_code=400, detail=f"Geçersiz metric_type: {req.metric_type}")

    result = _run_forecast_for_metric(req.metric_type, _to_forecast_request(req, freq="daily"))
    if result is None:
        raise HTTPException(status_code=404, detail="Öneri için yüklü veri veya kayıtlı model bulunamadı.")

    half_days = set(load_calibration().get("half_days", []))
    return compute_suggested_multipliers(result["comparison"]["daily"], half_days)


def _mape_delta(current: dict, proposed: dict) -> dict:
    def _diff(a, b):
        return round(b - a, 2) if a is not None and b is not None else None

    by_team_delta: dict = {}
    for team in set(current.get("by_team", {})) | set(proposed.get("by_team", {})):
        cur_team = current.get("by_team", {}).get(team, {})
        prop_team = proposed.get("by_team", {}).get(team, {})
        by_type_delta = {
            tt: _diff(cur_team.get("by_type", {}).get(tt), prop_team.get("by_type", {}).get(tt))
            for tt in set(cur_team.get("by_type", {})) | set(prop_team.get("by_type", {}))
        }
        by_team_delta[team] = {"mape": _diff(cur_team.get("mape"), prop_team.get("mape")), "by_type": by_type_delta}

    return {
        "overall_mape": _diff(current.get("overall_mape"), proposed.get("overall_mape")),
        "by_team": by_team_delta,
    }


@router.post("/preview")
async def preview(req: CalibrationPreviewRequest):
    if req.metric_type not in METRIC_TYPES:
        raise HTTPException(status_code=400, detail=f"Geçersiz metric_type: {req.metric_type}")

    _validate_config_body(req.proposed)
    forecast_req = _to_forecast_request(req, freq="daily")

    current_result = _run_forecast_for_metric(req.metric_type, forecast_req, calibration_override=None)
    proposed_result = _run_forecast_for_metric(
        req.metric_type, forecast_req,
        calibration_override={"multipliers": req.proposed.multipliers, "half_days": req.proposed.half_days},
    )
    if current_result is None or proposed_result is None:
        raise HTTPException(status_code=404, detail="Önizleme için yüklü veri veya kayıtlı model bulunamadı.")

    current_mape = current_result["mape_summary"]
    proposed_mape = proposed_result["mape_summary"]
    return {
        "current": current_mape,
        "proposed": proposed_mape,
        "delta": _mape_delta(current_mape, proposed_mape),
    }
