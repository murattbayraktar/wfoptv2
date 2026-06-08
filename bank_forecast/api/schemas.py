"""İstek gövdeleri için pydantic modelleri.

Yanıtlar (özet, tahmin, karşılaştırma) iç içe ve pipeline'ın ürettiği
sözlük yapısına yakın olduğundan düz `dict` olarak döndürülür; burada
yalnızca istemciden gelen istek gövdeleri doğrulanır.
"""
from pydantic import BaseModel


class ForecastRequest(BaseModel):
    start: str  # "YYYY-MM-DD"
    end: str  # "YYYY-MM-DD"
    types: list[str] | None = None
    freq: str = "daily"  # "daily" | "hourly" | "both"
    models: list[str] | None = None  # None: registry'nin best_model'ı kullanılır; birden fazla verilirse karşılaştırma üretilir


class RetrainRequest(BaseModel):
    freq: str = "daily"  # "daily" | "hourly" | "both"
    types: list[str] | None = None
    models: list[str] | None = None  # None/["auto"] = tüm adaylar denenir; tek model verilirse yalnızca o eğitilir
    holdout_days: int = 0  # 0 = devre dışı; >0 = son N günü eğitime dahil etme (doğrulama seti)
