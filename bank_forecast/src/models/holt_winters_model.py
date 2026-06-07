import pandas as pd
import numpy as np
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from src.models.base_model import BaseForecaster


class HoltWintersForecaster(BaseForecaster):
    def __init__(self, transaction_type: str, freq: str):
        super().__init__(transaction_type, freq)
        self._fitted_model = None
        self._y_train: pd.Series = None
        self._residual_std: float = 0.0

    def fit(self, X: pd.DataFrame, y: pd.Series) -> None:
        self.feature_names = []
        self._y_train = y.copy().reset_index(drop=True)

        seasonal_periods = 7 if self.freq == "daily" else 24
        # Veri yeterli mi kontrol et
        min_len = seasonal_periods * 2
        if len(y) < min_len:
            seasonal_periods = min(seasonal_periods, len(y) // 2)

        try:
            hw = ExponentialSmoothing(
                self._y_train,
                trend="add",
                seasonal="add",
                seasonal_periods=seasonal_periods,
                initialization_method="estimated",
            )
            self._fitted_model = hw.fit(optimized=True)
        except Exception:
            # Fallback: trend olmadan dene
            hw = ExponentialSmoothing(
                self._y_train,
                seasonal="add",
                seasonal_periods=seasonal_periods,
                initialization_method="estimated",
            )
            self._fitted_model = hw.fit(optimized=True)

        residuals = self._y_train.values - self._fitted_model.fittedvalues.values
        self._residual_std = float(np.std(residuals))

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        n = len(X)
        forecast = self._fitted_model.forecast(n)
        return np.maximum(forecast.values, 0)

    def predict_quantiles(self, X: pd.DataFrame, quantiles: list[float] = [0.1, 0.5, 0.9]) -> dict:
        n = len(X)
        forecast = self._fitted_model.forecast(n).values
        result = {}
        for q in quantiles:
            z = np.sqrt(2) * np.math.erfinv(2 * q - 1) if hasattr(np.math, "erfinv") else (q - 0.5) * 2 * 1.645
            result[q] = np.maximum(forecast + z * self._residual_std, 0)
        return result
