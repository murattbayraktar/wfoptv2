"""İstek gövdeleri için pydantic modelleri.

Yanıtlar (özet, tahmin, karşılaştırma) iç içe ve pipeline'ın ürettiği
sözlük yapısına yakın olduğundan düz `dict` olarak döndürülür; burada
yalnızca istemciden gelen istek gövdeleri doğrulanır.
"""
from pydantic import BaseModel


class ForecastRequest(BaseModel):
    start: str  # "YYYY-MM-DD"
    end: str  # "YYYY-MM-DD"
    metric_type: str = "both"  # "talimat" | "islem" | "both"
    teams: list[str] | None = None
    types: list[str] | None = None
    freq: str = "daily"  # "daily" | "hourly" | "both"
    models: list[str] | None = None  # None: registry'nin best_model'ı kullanılır; birden fazla verilirse karşılaştırma üretilir


class RetrainRequest(BaseModel):
    metric_type: str  # "talimat" | "islem" — hangi yüklü veri eğitilecek
    freq: str = "daily"  # "daily" | "hourly" | "both"
    teams: list[str] | None = None
    types: list[str] | None = None
    models: list[str] | None = None  # None/["auto"] = tüm adaylar denenir; tek model verilirse yalnızca o eğitilir
    holdout_days: int = 0  # 0 = devre dışı; >0 = son N günü eğitime dahil etme (doğrulama seti)


class CalibrationAnalyzeRequest(BaseModel):
    metric_type: str  # "talimat" | "islem"
    start: str
    end: str
    teams: list[str] | None = None
    types: list[str] | None = None
    min_samples: int = 4
    error_threshold_pct: float = 15.0


class CalibrationConfigBody(BaseModel):
    multipliers: dict[str, dict[str, float]] = {}
    half_days: list[str] = []


class CalibrationPreviewRequest(CalibrationAnalyzeRequest):
    proposed: CalibrationConfigBody
