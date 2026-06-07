import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import RandomizedSearchCV, TimeSeriesSplit
from src.models.base_model import BaseForecaster


RF_PARAM_GRID = {
    "n_estimators": [100, 300],
    "max_depth": [8, 12, None],
    "max_features": ["sqrt", 0.5, 0.7],
    "min_samples_leaf": [2, 5, 10],
}


class RandomForestForecaster(BaseForecaster):
    def __init__(self, transaction_type: str, freq: str, n_iter: int = 20,
                 cv_folds: int = 5, random_state: int = 42, n_jobs: int = -1):
        super().__init__(transaction_type, freq)
        self.n_iter = n_iter
        self.cv_folds = cv_folds
        self.random_state = random_state
        self.n_jobs = n_jobs

    def fit(self, X: pd.DataFrame, y: pd.Series) -> None:
        self.feature_names = list(X.columns)
        tscv = TimeSeriesSplit(n_splits=self.cv_folds)

        base_estimator = RandomForestRegressor(
            random_state=self.random_state,
            n_jobs=self.n_jobs,
        )

        search = RandomizedSearchCV(
            base_estimator,
            RF_PARAM_GRID,
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

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        preds = self.model.predict(X[self.feature_names])
        return np.maximum(preds, 0)

    def predict_quantiles(self, X: pd.DataFrame, quantiles: list[float] = [0.1, 0.5, 0.9]) -> dict:
        # RF için bootstrap ile quantile tahmini
        Xf = X[self.feature_names]
        tree_preds = np.array([tree.predict(Xf) for tree in self.model.estimators_])
        result = {}
        for q in quantiles:
            result[q] = np.maximum(np.quantile(tree_preds, q, axis=0), 0)
        return result

    def get_feature_importance(self) -> pd.DataFrame:
        return pd.DataFrame({
            "feature": self.feature_names,
            "gain": self.model.feature_importances_,
        }).sort_values("gain", ascending=False).reset_index(drop=True)
