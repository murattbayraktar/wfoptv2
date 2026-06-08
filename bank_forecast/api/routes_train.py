"""Opsiyonel yeniden eğitim ucu: yüklenen veriyle modelleri arka planda yeniden eğitir."""
import threading
from datetime import datetime

from fastapi import APIRouter, HTTPException

from src.pipeline import train_pipeline

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


def _run_training(input_path: str, freq: str, types: list[str] | None, models: list[str] | None) -> None:
    RETRAIN_STATUS.reset()
    RETRAIN_STATUS.status = "running"
    RETRAIN_STATUS.message = "Modeller yeniden eğitiliyor..."
    RETRAIN_STATUS.started_at = datetime.now()
    RETRAIN_STATUS.finished_at = None
    try:
        train_pipeline(
            input_path=input_path, freq=freq, types=types, models=models or ["auto"],
            report=False, progress_callback=_on_event,
        )
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
        args=(STATE.uploaded_path, req.freq, req.types, req.models),
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
    }
