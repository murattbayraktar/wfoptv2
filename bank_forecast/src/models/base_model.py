from abc import ABC, abstractmethod
import pandas as pd
import numpy as np
import joblib
import os


class BaseForecaster(ABC):
    def __init__(self, transaction_type: str, freq: str):
        self.transaction_type = transaction_type
        self.freq = freq  # 'daily' | 'hourly'
        self.model = None
        self.feature_names: list[str] = []
        self.metrics: dict = {}

    @abstractmethod
    def fit(self, X: pd.DataFrame, y: pd.Series) -> None: ...

    @abstractmethod
    def predict(self, X: pd.DataFrame) -> np.ndarray: ...

    def predict_quantiles(self, X: pd.DataFrame, quantiles: list[float] = [0.1, 0.5, 0.9]) -> dict:
        """
        Varsayılan: eğitim rezidüellerinin bootstrap dağılımından quantile ekle
        (Yöntem 2 — Bootstrap fallback, model agnostik).
        `self._residuals` set edilmemişse düz tahmine düşer.
        """
        preds = self.predict(X)
        residuals = getattr(self, "_residuals", None)
        if residuals is None or len(residuals) == 0:
            return {q: preds for q in quantiles}

        result = {}
        for q in quantiles:
            offset = np.quantile(residuals, q)
            result[q] = np.maximum(preds + offset, 0)
        return result

    def save(self, path: str) -> None:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        joblib.dump(self, path)

    @classmethod
    def load(cls, path: str) -> "BaseForecaster":
        return joblib.load(path)

    def get_feature_importance(self) -> pd.DataFrame:
        return pd.DataFrame()

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(type={self.transaction_type}, freq={self.freq})"
