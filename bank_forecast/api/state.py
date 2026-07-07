"""Tek kullanıcılı yerel araç için bellek-içi (in-memory) global durum.

Sayfa yenilenince frontend state'i sıfırlanır; bu modüldeki STATE ise
sunucu süreci ayakta olduğu sürece korunur (DB/oturum yönetimi yok).

Talimat ve işlem verileri aynı anda yüklü tutulup aynı ekranda yan yana
gösterilebilmesi gerektiğinden (bkz. plan), `AppState` iki bağımsız
`DatasetState` slotu barındırır — biri "talimat", biri "islem" metriği için.
"""
from datetime import datetime

import pandas as pd

METRIC_TYPES = ("talimat", "islem")


class DatasetState:
    def __init__(self) -> None:
        self.raw_df: pd.DataFrame | None = None
        self.daily_agg: pd.DataFrame | None = None
        self.hourly_agg: pd.DataFrame | None = None
        self.source_filename: str | None = None
        self.source_kind: str | None = None  # "upload" | "demo"
        self.uploaded_path: str | None = None
        self.loaded_at: datetime | None = None

    def is_loaded(self) -> bool:
        return self.raw_df is not None

    def reset(self) -> None:
        self.__init__()


class AppState:
    def __init__(self) -> None:
        self.datasets: dict[str, DatasetState] = {m: DatasetState() for m in METRIC_TYPES}

    def get(self, metric_type: str) -> DatasetState:
        return self.datasets[metric_type]

    def is_loaded(self, metric_type: str | None = None) -> bool:
        if metric_type is not None:
            return self.datasets[metric_type].is_loaded()
        return any(d.is_loaded() for d in self.datasets.values())

    def reset(self, metric_type: str | None = None) -> None:
        if metric_type is not None:
            self.datasets[metric_type].reset()
        else:
            self.__init__()


STATE = AppState()


class RetrainStatus:
    def __init__(self) -> None:
        self.status: str = "idle"  # idle | running | done | error
        self.message: str = ""
        self.started_at: datetime | None = None
        self.finished_at: datetime | None = None
        self.steps: list[dict] = []
        self.progress: float = 0.0
        self.total_units: int = 0
        self.completed_units: int = 0
        self.holdout_days: int = 0
        self.holdout_result: dict | None = None
        self.metric_type: str | None = None

    def reset(self) -> None:
        self.__init__()

    def add_step(self, event: dict) -> None:
        self.steps.append({"at": datetime.now().isoformat(), **event})


# Talimat ve işlem eğitimleri bağımsız tetiklenebildiğinden, her metrik için
# ayrı bir retrain durumu takip edilir.
RETRAIN_STATUS: dict[str, RetrainStatus] = {m: RetrainStatus() for m in METRIC_TYPES}
