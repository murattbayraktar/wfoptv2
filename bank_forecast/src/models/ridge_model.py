import pandas as pd
import numpy as np
from sklearn.linear_model import RidgeCV
from sklearn.preprocessing import StandardScaler
from src.models.base_model import BaseForecaster


CALENDAR_ONLY_FEATURES = [
    "is_public_holiday", "is_religious_holiday", "is_eve_of_holiday",
    "is_bridge_day", "is_month_start", "is_month_end", "is_last_friday",
    "days_to_month_end", "days_from_month_start", "days_to_next_holiday",
    "days_from_last_holiday", "post_holiday_day1", "post_holiday_day2",
    "day_of_week", "day_of_month", "week_of_month", "month", "quarter",
    "is_weekend", "month_quarter",
]


class RidgeForecaster(BaseForecaster):
    def __init__(self, transaction_type: str, freq: str):
        super().__init__(transaction_type, freq)
        self._scaler = StandardScaler()

    def fit(self, X: pd.DataFrame, y: pd.Series) -> None:
        # Sadece takvim özelliklerini kullan
        avail = [c for c in CALENDAR_ONLY_FEATURES if c in X.columns]
        self.feature_names = avail

        Xs = self._scaler.fit_transform(X[avail])
        self.model = RidgeCV(alphas=[0.1, 1.0, 10.0, 100.0], cv=5)
        self.model.fit(Xs, y)
        self.metrics["alpha"] = float(self.model.alpha_)

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        Xs = self._scaler.transform(X[self.feature_names])
        preds = self.model.predict(Xs)
        return np.maximum(preds, 0)

    def get_feature_importance(self) -> pd.DataFrame:
        return pd.DataFrame({
            "feature": self.feature_names,
            "coefficient": self.model.coef_,
        }).sort_values("coefficient", key=abs, ascending=False).reset_index(drop=True)
