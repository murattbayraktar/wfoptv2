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
        """Hiperparametre araması (RandomizedSearchCV, kendi iç-CV'siyle CV-RMSE üretir).

        Not: `search.best_score_` zaten bir CV-temelli RMSE tahminidir — bu yüzden
        `ModelSelector` bu skoru doğrudan model-karşılaştırma metriği olarak kullanır
        (ayrı bir dış cross-validation döngüsüne gerek kalmaz).
        """
        self.feature_names = list(X.columns)
        self._search_best_params(X, y)

    def _search_best_params(self, X: pd.DataFrame, y: pd.Series) -> dict:
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
        self.metrics["best_params"] = dict(search.best_params_)
        return self.metrics["best_params"]

    def fit_from_params(self, X: pd.DataFrame, y: pd.Series, params: dict,
                        cv_rmse: float | None = None) -> None:
        """Arama YAPMADAN, verilen hiperparametrelerle tek seferlik tam-veri fit.

        Model-seçim aşamasında zaten bir `RandomizedSearchCV` çalıştırılıp en iyi
        parametreler bulunduğundan, final (tüm-veri) eğitiminde aramayı tekrarlamak
        gereksiz fit ekler. Bu metod o aramayı atlayıp doğrudan bulunan
        parametrelerle eğitir.
        """
        self.feature_names = list(X.columns)
        params = dict(params)
        self.model = RandomForestRegressor(
            random_state=self.random_state,
            n_jobs=self.n_jobs,
            **params,
        )
        self.model.fit(X, y)
        if cv_rmse is not None:
            self.metrics["cv_rmse"] = cv_rmse
        self.metrics["best_params"] = params

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
