"""WFOpt — İşlem Hacmi Tahmin Sistemi için FastAPI uygulaması.

Çalıştırma (bank_forecast/ dizininden — registry/config göreli yollar buna bağlı):
    uvicorn api.main:app --reload --port 8000
"""
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import routes_data, routes_forecast, routes_train

# Windows konsolunun varsayılan kodlaması (cp1252/"charmap"), pipeline'ın bastığı
# özel karakterleri (→, ✓ vb.) UnicodeEncodeError ile patlatır — arka plan eğitim
# thread'i bu yüzden ilk console.print çağrısında hemen hata veriyordu.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

app = FastAPI(title="WFOpt İşlem Hacmi Tahmin API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routes_data.router)
app.include_router(routes_forecast.router)
app.include_router(routes_train.router)


@app.get("/api/health")
async def health():
    return {"status": "ok"}
