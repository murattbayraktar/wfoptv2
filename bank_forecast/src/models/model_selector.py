import pandas as pd
import numpy as np
from sklearn.model_selection import TimeSeriesSplit
from rich.console import Console
from rich.table import Table

from src.models.base_model import BaseForecaster
from src.models.xgboost_model import XGBoostForecaster
from src.models.lightgbm_model import LightGBMForecaster
from src.models.random_forest_model import RandomForestForecaster
from src.models.holt_winters_model import HoltWintersForecaster
from src.models.ridge_model import RidgeForecaster
from src.evaluation.metrics import rmse, mae, mape

console = Console()

MODEL_REGISTRY = {
    "xgboost": XGBoostForecaster,
    "lightgbm": LightGBMForecaster,
    "random_forest": RandomForestForecaster,
    "holt_winters": HoltWintersForecaster,
    "ridge": RidgeForecaster,
}

ML_MODELS = {"xgboost", "lightgbm", "random_forest"}
NEEDS_FEATURES = {"xgboost", "lightgbm", "random_forest", "ridge"}


def _make_model(name: str, transaction_type: str, freq: str, cfg: dict) -> BaseForecaster:
    cls = MODEL_REGISTRY[name]
    kwargs = {"transaction_type": transaction_type, "freq": freq}
    if name in ML_MODELS:
        kwargs["cv_folds"] = cfg.get("cv_folds", 5)
        kwargs["random_state"] = cfg.get("random_state", 42)
        kwargs["n_jobs"] = cfg.get("n_jobs", -1)
        if name == "xgboost":
            kwargs["n_iter"] = cfg.get("xgboost_n_iter", 30)
        elif name == "lightgbm":
            kwargs["n_iter"] = cfg.get("lightgbm_n_iter", 30)
        elif name == "random_forest":
            kwargs["n_iter"] = cfg.get("rf_n_iter", 20)
    return cls(**kwargs)


def _cv_score(
    model_name: str,
    transaction_type: str,
    freq: str,
    X: pd.DataFrame,
    y: pd.Series,
    cfg: dict,
    metric: str = "rmse",
    cv_folds: int = 5,
) -> float:
    tscv = TimeSeriesSplit(n_splits=cv_folds)
    scores = []

    for train_idx, val_idx in tscv.split(X):
        X_tr, X_val = X.iloc[train_idx], X.iloc[val_idx]
        y_tr, y_val = y.iloc[train_idx], y.iloc[val_idx]

        m = _make_model(model_name, transaction_type, freq, cfg)

        if model_name in NEEDS_FEATURES:
            m.fit(X_tr, y_tr)
            preds = m.predict(X_val)
        else:
            # Holt-Winters: X gereksiz, y zaman sırası önemli
            m.fit(X_tr, y_tr)
            preds = m.predict(X_val)

        if metric == "rmse":
            scores.append(rmse(y_val.values, preds))
        elif metric == "mae":
            scores.append(mae(y_val.values, preds))
        elif metric == "mape":
            scores.append(mape(y_val.values, preds))

    return float(np.mean(scores))


class ModelSelector:
    CANDIDATE_MODELS = ["xgboost", "lightgbm", "random_forest", "holt_winters", "ridge"]

    def select_best(
        self,
        transaction_type: str,
        freq: str,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        cv_folds: int = 5,
        metric: str = "rmse",
        candidates: list[str] = None,
        cfg: dict = None,
        min_training_days: int = 60,
        progress_callback=None,
    ) -> dict:
        if cfg is None:
            cfg = {}
        if candidates is None:
            candidates = self.CANDIDATE_MODELS

        # Veri azsa sadece Holt-Winters ve Ridge kullan
        if len(y_train) < min_training_days:
            candidates = [c for c in candidates if c in {"holt_winters", "ridge"}]
            if not candidates:
                candidates = ["holt_winters"]

        all_scores = {}
        console.print(f"\n[cyan]Model seçimi: {transaction_type} / {freq}[/cyan]")
        if progress_callback:
            progress_callback({
                "kind": "selection_start",
                "type": transaction_type,
                "freq": freq,
                "candidates": candidates,
            })

        for model_name in candidates:
            try:
                score = _cv_score(
                    model_name, transaction_type, freq,
                    X_train, y_train, cfg, metric, cv_folds
                )
                all_scores[model_name] = round(score, 4)
                console.print(f"  {model_name:20s} {metric.upper()} = {score:.4f}")
            except Exception as e:
                console.print(f"  [red]{model_name}: hata — {e}[/red]")
                all_scores[model_name] = float("inf")
            if progress_callback:
                progress_callback({
                    "kind": "model_evaluated",
                    "type": transaction_type,
                    "freq": freq,
                    "model": model_name,
                    "score": all_scores[model_name],
                    "metric": metric,
                })

        best_model = min(all_scores, key=all_scores.get)
        best_score = all_scores[best_model]

        reason = _build_reason(best_model, best_score, all_scores, metric)
        console.print(f"  [green]Seçilen: {best_model} ({metric.upper()}={best_score:.4f})[/green]")
        if progress_callback:
            progress_callback({
                "kind": "model_selected",
                "type": transaction_type,
                "freq": freq,
                "model": best_model,
                "score": best_score,
                "reason": reason,
            })

        return {
            "best_model": best_model,
            "best_score": best_score,
            "all_scores": all_scores,
            "selection_reason": reason,
        }

    def train_best(
        self,
        selection_result: dict,
        transaction_type: str,
        freq: str,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        cfg: dict = None,
    ) -> BaseForecaster:
        if cfg is None:
            cfg = {}
        name = selection_result["best_model"]
        model = _make_model(name, transaction_type, freq, cfg)
        model.fit(X_train, y_train)
        return model

    def train_selected(
        self,
        transaction_type: str,
        freq: str,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        candidate_names: list[str],
        cfg: dict = None,
    ) -> dict:
        """candidate_names listesindeki HER modeli tüm veri üzerinde eğitir.

        CV skorlaması (`select_best`) zaten her aday için ayrı ayrı yapıldığından
        burada tekrarlanmaz — sadece tam veri ile final-fit gerçekleştirilir.
        Döner: {model_name: fitted_model}
        """
        if cfg is None:
            cfg = {}
        trained = {}
        for name in candidate_names:
            model = _make_model(name, transaction_type, freq, cfg)
            model.fit(X_train, y_train)
            trained[name] = model
        return trained


class WeightedEnsemble(BaseForecaster):
    def __init__(self, transaction_type: str, freq: str):
        super().__init__(transaction_type, freq)
        self._models: list[BaseForecaster] = []
        self._weights: np.ndarray = np.array([])

    def fit(self, X: pd.DataFrame, y: pd.Series) -> None:
        raise NotImplementedError("WeightedEnsemble fit() yerine add_model() kullanın.")

    def add_model(self, model: BaseForecaster, cv_rmse: float) -> None:
        self._models.append(model)
        raw_weights = np.array([1.0 / (m_rmse + 1e-9) for m_rmse in
                                 [getattr(m, "metrics", {}).get("cv_rmse", cv_rmse)
                                  for m in self._models]])
        self._weights = raw_weights / raw_weights.sum()

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        preds = np.array([m.predict(X) for m in self._models])
        return np.maximum(np.average(preds, axis=0, weights=self._weights), 0)

    def predict_quantiles(self, X: pd.DataFrame, quantiles: list[float] = [0.1, 0.5, 0.9]) -> dict:
        result = {}
        for q in quantiles:
            all_q = []
            for m in self._models:
                qp = m.predict_quantiles(X, [q])
                all_q.append(qp[q])
            result[q] = np.maximum(np.average(np.array(all_q), axis=0, weights=self._weights), 0)
        return result


def _build_reason(best: str, best_score: float, all_scores: dict, metric: str) -> str:
    sorted_scores = sorted(all_scores.items(), key=lambda x: x[1])
    runner_up = sorted_scores[1][0] if len(sorted_scores) > 1 else None
    runner_score = sorted_scores[1][1] if len(sorted_scores) > 1 else None
    reason = f"{best} en düşük CV {metric.upper()}'yi verdi ({best_score:.4f})."
    if runner_up:
        reason += f" İkinci sıra: {runner_up} ({runner_score:.4f})."
    return reason
