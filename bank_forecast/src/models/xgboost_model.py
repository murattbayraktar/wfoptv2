import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.model_selection import RandomizedSearchCV, TimeSeriesSplit
from src.models.base_model import BaseForecaster


XGBOOST_PARAM_GRID = {
    "n_estimators": [200, 500, 1000],
    "max_depth": [4, 6, 8],
    "learning_rate": [0.01, 0.05, 0.1],
    "subsample": [0.7, 0.9],
    "colsample_bytree": [0.7, 0.9],
    "min_child_weight": [1, 3, 5],
    "reg_alpha": [0, 0.1, 1.0],
    "reg_lambda": [1.0, 2.0],
}


class XGBoostForecaster(BaseForecaster):
    def __init__(self, transaction_type: str, freq: str, n_iter: int = 30,
                 cv_folds: int = 5, random_state: int = 42, n_jobs: int = -1):
        super().__init__(transaction_type, freq)
        self.n_iter = n_iter
        self.cv_folds = cv_folds
        self.random_state = random_state
        self.n_jobs = n_jobs
        self._q_models: dict = {}  # quantile modelleri

    def fit(self, X: pd.DataFrame, y: pd.Series) -> None:
        self.feature_names = list(X.columns)
        tscv = TimeSeriesSplit(n_splits=self.cv_folds)

        base_estimator = xgb.XGBRegressor(
            objective="reg:squarederror",
            eval_metric="rmse",
            random_state=self.random_state,
            n_jobs=self.n_jobs,
            tree_method="hist",
        )

        search = RandomizedSearchCV(
            base_estimator,
            XGBOOST_PARAM_GRID,
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

        # Quantile modelleri eğit (XGBoost 3.x: reg:quantileerror)
        best_params = {k: v for k, v in search.best_params_.items()}
        for q in [0.1, 0.5, 0.9]:
            qm = xgb.XGBRegressor(
                objective="reg:quantileerror",
                quantile_alpha=q,
                **best_params,
                random_state=self.random_state,
                n_jobs=self.n_jobs,
                tree_method="hist",
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
        gain = self.model.get_booster().get_score(importance_type="gain")
        weight = self.model.get_booster().get_score(importance_type="weight")
        df = pd.DataFrame({
            "feature": list(gain.keys()),
            "gain": list(gain.values()),
        })
        df["weight"] = df["feature"].map(weight).fillna(0)
        return df.sort_values("gain", ascending=False).reset_index(drop=True)
