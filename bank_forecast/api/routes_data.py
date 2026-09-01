"""Veri yükleme uçları: CSV yükleme, mevcut veri özeti.

Bir CSV yüklendiğinde `load_transactions` satır-bazlı ham talimat verisinden
'talimat' (referans sayısı) ve, EntryProcessCount kolonu mevcutsa, 'islem'
(işlem adedi) metriklerini birlikte üretir — kullanıcı hangi metriği
yüklediğini ayrıca seçmek zorunda kalmaz, veri kendiliğinden ilgili
`STATE` slotlarına (`talimat` ve varsa `islem`) yazılır.
"""
import os
import tempfile
from datetime import datetime

from fastapi import APIRouter, HTTPException, UploadFile

from src.data.loader import load_transactions
from src.data.aggregator import aggregate_daily, aggregate_hourly

from .state import STATE, METRIC_TYPES

router = APIRouter(prefix="/api", tags=["data"])

WORKING_HOURS = (7, 18)


def _build_dataset_summary(metric_type: str) -> dict | None:
    ds = STATE.get(metric_type)
    if not ds.is_loaded():
        return None

    df = ds.raw_df
    daily = ds.daily_agg

    per_team_type_counts = (
        daily.groupby(["team", "transaction_type"])["count"].sum().astype(int).reset_index()
    )
    per_team_counts = daily.groupby("team")["count"].sum().astype(int).to_dict()
    per_type_counts = daily.groupby("transaction_type")["count"].sum().astype(int).to_dict()

    return {
        "loaded": True,
        "metric_type": metric_type,
        "filename": ds.source_filename,
        "row_count": int(len(df)),
        "date_range": {
            "start": str(df["date"].min().date()),
            "end": str(df["date"].max().date()),
        },
        "teams": sorted(per_team_counts.keys()),
        "transaction_types": sorted(per_type_counts.keys()),
        "per_team_counts": per_team_counts,
        "per_type_counts": per_type_counts,
        "per_team_type_counts": [
            {"team": r["team"], "transaction_type": r["transaction_type"], "count": int(r["count"])}
            for r in per_team_type_counts.to_dict("records")
        ],
        "has_hourly": ds.hourly_agg is not None,
        "loaded_at": ds.loaded_at.isoformat() if ds.loaded_at else None,
    }


def _build_summary() -> dict:
    return {m: _build_dataset_summary(m) for m in METRIC_TYPES}


def _load_into_state(csv_path: str, filename: str, uploaded_path: str) -> list[str]:
    """CSV'yi yükler ve içeriğinden üretilen HER metric_type'ı ilgili STATE
    slotuna yazar (bkz. `load_transactions` — tek CSV'den 'talimat' ve,
    EntryProcessCount kolonu varsa, 'islem' birlikte üretilir).

    Döner: doldurulan metric_type listesi.
    """
    results = load_transactions(csv_path)

    filled = []
    for metric_type, df in results.items():
        daily_agg = aggregate_daily(df)
        try:
            hourly_agg = aggregate_hourly(df, working_hours=WORKING_HOURS)
        except ValueError:
            hourly_agg = None

        ds = STATE.get(metric_type)
        ds.raw_df = df
        ds.daily_agg = daily_agg
        ds.hourly_agg = hourly_agg
        ds.source_filename = filename
        ds.uploaded_path = uploaded_path
        ds.loaded_at = datetime.now()
        filled.append(metric_type)

    return filled


@router.post("/upload")
async def upload_csv(file: UploadFile):
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Yalnızca CSV dosyaları kabul edilir.")

    os.makedirs(os.path.join("data", "raw", "_uploads"), exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(suffix=".csv", dir=os.path.join("data", "raw", "_uploads"))
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(await file.read())

        _load_into_state(tmp_path, file.filename, tmp_path)
    except ValueError as e:
        os.remove(tmp_path)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        os.remove(tmp_path)
        raise HTTPException(status_code=500, detail=f"Dosya işlenemedi: {e}")

    return _build_summary()


@router.get("/dataset/summary")
async def dataset_summary():
    return _build_summary()
