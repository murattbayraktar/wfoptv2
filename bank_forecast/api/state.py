"""Tek kullanıcılı yerel araç için bellek-içi (in-memory) global durum.

Sayfa yenilenince frontend state'i sıfırlanır; bu modüldeki STATE ise
sunucu süreci ayakta olduğu sürece korunur (DB/oturum yönetimi yok).
"""
from datetime import datetime

import pandas as pd


class AppState:
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

    def reset(self) -> None:
        self.__init__()

    def add_step(self, event: dict) -> None:
        self.steps.append({"at": datetime.now().isoformat(), **event})


RETRAIN_STATUS = RetrainStatus()
