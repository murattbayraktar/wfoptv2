"""WFOpt — İşlem Hacmi Tahmin Sistemi için FastAPI uygulaması.

Çalıştırma (bank_forecast/ dizininden — registry/config göreli yollar buna bağlı):
    uvicorn api.main:app --reload --port 8000
"""
import os
import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from . import routes_calibration, routes_data, routes_forecast, routes_train

# Windows konsolunun varsayılan kodlaması (cp1252/"charmap"), pipeline'ın bastığı
# özel karakterleri (→, ✓ vb.) UnicodeEncodeError ile patlatır — arka plan eğitim
# thread'i bu yüzden ilk console.print çağrısında hemen hata veriyordu.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

app = FastAPI(title="WFOpt İşlem Hacmi Tahmin API")

_allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routes_data.router)
app.include_router(routes_forecast.router)
app.include_router(routes_train.router)
app.include_router(routes_calibration.router)


@app.get("/api/health")
async def health():
    return {"status": "ok"}


# Production'da Vite build çıktısını serve et
_static_dir = Path(__file__).parent.parent / "frontend" / "dist"
if _static_dir.exists():
    app.mount("/assets", StaticFiles(directory=_static_dir / "assets"), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        return FileResponse(_static_dir / "index.html")
