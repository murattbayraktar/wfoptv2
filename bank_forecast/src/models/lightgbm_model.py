import pandas as pd
import numpy as np
import lightgbm as lgb
from sklearn.model_selection import RandomizedSearchCV, TimeSeriesSplit
from src.models.base_model import BaseForecaster


LGBM_PARAM_GRID = {
    "n_estimators": [200, 500, 1000],
    "num_leaves": [31, 63, 127],
    "learning_rate": [0.01, 0.05, 0.1],
    "feature_fraction": [0.7, 0.9],
    "bagging_fraction": [0.7, 0.9],
    "bagging_freq": [5],
    "min_child_samples": [10, 20, 50],
    "reg_alpha": [0, 0.1],
    "reg_lambda": [0, 0.1],
}

CATEGORICAL_FEATURES = ["day_of_week", "month_quarter", "month", "quarter", "week_of_month"]


class LightGBMForecaster(BaseForecaster):
    def __init__(self, transaction_type: str, freq: str, n_iter: int = 30,
                 cv_folds: int = 5, random_state: int = 42, n_jobs: int = -1):
        super().__init__(transaction_type, freq)
        self.n_iter = n_iter
        self.cv_folds = cv_folds
        self.random_state = random_state
        self.n_jobs = n_jobs
        self._q_models: dict = {}

    def fit(self, X: pd.DataFrame, y: pd.Series) -> None:
        self.feature_names = list(X.columns)
        tscv = TimeSeriesSplit(n_splits=self.cv_folds)

        cat_cols = [c for c in CATEGORICAL_FEATURES if c in X.columns]

        base_estimator = lgb.LGBMRegressor(
            objective="regression",
            metric="rmse",
            random_state=self.random_state,
            n_jobs=self.n_jobs,
            verbose=-1,
        )

        search = RandomizedSearchCV(
            base_estimator,
            LGBM_PARAM_GRID,
            n_iter=self.n_iter,
            cv=tscv,
            scoring="neg_root_mean_squared_error",
            random_state=self.random_state,
            n_jobs=1,
            refit=True,
        )
        search.fit(X, y)
        self.model = search.best_estimator_
        self.metrics["cv_rmse"] = -search.best_score_
        self.metrics["best_params"] = search.best_params_

        best_params = {k: v for k, v in search.best_params_.items()}
        for q in [0.1, 0.5, 0.9]:
            qm = lgb.LGBMRegressor(
                objective="quantile",
                alpha=q,
                metric="quantile",
                **best_params,
                random_state=self.random_state,
                n_jobs=self.n_jobs,
                verbose=-1,
            )
            qm.fit(X, y)
            self._q_models[q] = qm

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        preds = self.model.predict(X[self.feature_names])
        return np.maximum(preds, 0)

    def predict_quantiles(self, X: pd.DataFrame, quantiles: list[float] = [0.1, 0.5, 0.9]) -> dict:
        result = {}
        Xf = X[self.feature_names]
        for q in quantiles:
            if q in self._q_models:
                result[q] = np.maximum(self._q_models[q].predict(Xf), 0)
            else:
                result[q] = self.predict(X)
        return result

    def get_feature_importance(self) -> pd.DataFrame:
        return pd.DataFrame({
            "feature": self.feature_names,
            "gain": self.model.feature_importances_,
        }).sort_values("gain", ascending=False).reset_index(drop=True)
