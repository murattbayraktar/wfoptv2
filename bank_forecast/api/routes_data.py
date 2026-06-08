"""Veri yükleme uçları: CSV yükleme, demo data, mevcut veri özeti."""
import os
import tempfile
from datetime import datetime

from fastapi import APIRouter, HTTPException, UploadFile

from src.data.loader import load_transactions
from src.data.aggregator import aggregate_daily, aggregate_hourly

from .state import STATE

router = APIRouter(prefix="/api", tags=["data"])

DEMO_CSV_PATH = os.path.join("data", "raw", "demo.csv")
WORKING_HOURS = (7, 18)


def _build_summary() -> dict | None:
    if not STATE.is_loaded():
        return None

    df = STATE.raw_df
    daily = STATE.daily_agg

    per_type_counts = (
        daily.groupby("transaction_type")["count"].sum().astype(int).to_dict()
    )

    return {
        "loaded": True,
        "filename": STATE.source_filename,
        "source_kind": STATE.source_kind,
        "row_count": int(len(df)),
        "date_range": {
            "start": str(df["date"].min().date()),
            "end": str(df["date"].max().date()),
        },
        "transaction_types": sorted(per_type_counts.keys()),
        "per_type_counts": per_type_counts,
        "has_hourly": STATE.hourly_agg is not None,
        "loaded_at": STATE.loaded_at.isoformat() if STATE.loaded_at else None,
    }


def _load_into_state(csv_path: str, filename: str, source_kind: str, uploaded_path: str | None) -> None:
    df = load_transactions(csv_path)

    daily_agg = aggregate_daily(df)
    try:
        hourly_agg = aggregate_hourly(df, working_hours=WORKING_HOURS)
    except ValueError:
        hourly_agg = None

    STATE.raw_df = df
    STATE.daily_agg = daily_agg
    STATE.hourly_agg = hourly_agg
    STATE.source_filename = filename
    STATE.source_kind = source_kind
    STATE.uploaded_path = uploaded_path
    STATE.loaded_at = datetime.now()


@router.post("/upload")
async def upload_csv(file: UploadFile):
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Yalnızca CSV dosyaları kabul edilir.")

    os.makedirs(os.path.join("data", "raw", "_uploads"), exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(suffix=".csv", dir=os.path.join("data", "raw", "_uploads"))
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(await file.read())

        _load_into_state(tmp_path, file.filename, "upload", tmp_path)
    except ValueError as e:
        os.remove(tmp_path)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        os.remove(tmp_path)
        raise HTTPException(status_code=500, detail=f"Dosya işlenemedi: {e}")

    return _build_summary()


@router.post("/demo-data")
async def load_demo_data():
    if not os.path.exists(DEMO_CSV_PATH):
        raise HTTPException(
            status_code=404,
            detail=(
                "Demo veri bulunamadı. "
                "`python scripts/generate_demo_data.py --output data/raw/demo.csv` ile üretebilirsiniz."
            ),
        )

    try:
        _load_into_state(DEMO_CSV_PATH, "demo.csv", "demo", None)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Demo veri yüklenemedi: {e}")

    return _build_summary()


@router.get("/dataset/summary")
async def dataset_summary():
    summary = _build_summary()
    if summary is None:
        return {"loaded": False}
    return summary
