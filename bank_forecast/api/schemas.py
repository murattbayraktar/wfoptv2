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


class RetrainRequest(BaseModel):
    freq: str = "daily"  # "daily" | "hourly" | "both"
    types: list[str] | None = None
