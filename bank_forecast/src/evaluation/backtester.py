import pandas as pd
import numpy as np
from sklearn.model_selection import TimeSeriesSplit
from rich.console import Console
from rich.table import Table

from src.evaluation.metrics import rmse, mae, mape, smape, coverage_95
from src.features.feature_pipeline import build_features, get_feature_matrix
from src.models.model_selector import ModelSelector

console = Console()


class WalkForwardBacktester:
    def __init__(
        self,
        transaction_type: str,
        freq: str,
        cv_folds: int = 5,
        min_train_days: int = 90,
        cfg: dict = None,
    ):
        self.transaction_type = transaction_type
        self.freq = freq
        self.cv_folds = cv_folds
        self.min_train_days = min_train_days
        self.cfg = cfg or {}

    def run(
        self,
        df: pd.DataFrame,
        model_name: str = "xgboost",
        models_cfg: dict = None,
    ) -> dict:
        if models_cfg is None:
            models_cfg = {}

        subset = df[df["transaction_type"] == self.transaction_type].copy()
        subset = subset.sort_values("date").reset_index(drop=True)

        if len(subset) < self.min_train_days * 2:
            return {"error": f"Yetersiz veri ({len(subset)} gün < {self.min_train_days * 2})"}

        tscv = TimeSeriesSplit(n_splits=self.cv_folds)
        fold_results = []

        all_y_true = []
        all_y_pred = []
        holiday_y_true = []
        holiday_y_pred = []
        normal_y_true = []
        normal_y_pred = []

        for fold_i, (train_idx, val_idx) in enumerate(tscv.split(subset)):
            if len(train_idx) < self.min_train_days:
                continue

            train_df = subset.iloc[train_idx].copy()
            val_df = subset.iloc[val_idx].copy()

            # Feature pipeline
            train_feat, feat_cols, encoder = build_features(
                train_df, self.freq, target_col="count", fit_encoder=True, cfg=self.cfg
            )
            val_feat, _, _ = build_features(
                val_df, self.freq, target_col="count",
                fit_encoder=False, encoder=encoder, cfg=self.cfg
            )

            X_tr, y_tr = get_feature_matrix(train_feat, feat_cols)
            X_val, y_val = get_feature_matrix(val_feat, feat_cols)

            # Model yükle ve eğit
            from src.models.model_selector import _make_model
            m = _make_model(model_name, self.transaction_type, self.freq, models_cfg)
            m.fit(X_tr, y_tr)
            preds = m.predict(X_val)

            # Quantile tahminleri (PI kapsamı için)
            try:
                qpreds = m.predict_quantiles(X_val, [0.1, 0.9])
                lower = qpreds[0.1]
                upper = qpreds[0.9]
                cov = coverage_95(y_val.values, lower, upper)
            except Exception:
                cov = float("nan")

            fold_res = {
                "fold": fold_i + 1,
                "train_size": len(train_idx),
                "val_size": len(val_idx),
                "rmse": rmse(y_val.values, preds),
                "mae": mae(y_val.values, preds),
                "mape": mape(y_val.values, preds),
                "smape": smape(y_val.values, preds),
                "pi_coverage": cov,
            }
            fold_results.append(fold_res)

            all_y_true.extend(y_val.tolist())
            all_y_pred.extend(preds.tolist())

            # Tatil günleri vs normal günler
            is_holiday = val_feat["is_public_holiday"].values | val_feat["is_religious_holiday"].values
            h_mask = is_holiday.astype(bool)
            if h_mask.any():
                holiday_y_true.extend(y_val.values[h_mask].tolist())
                holiday_y_pred.extend(preds[h_mask].tolist())
            if (~h_mask).any():
                normal_y_true.extend(y_val.values[~h_mask].tolist())
                normal_y_pred.extend(preds[~h_mask].tolist())

        fold_df = pd.DataFrame(fold_results)

        summary = {
            "transaction_type": self.transaction_type,
            "freq": self.freq,
            "model": model_name,
            "folds": fold_results,
            "overall": {
                "rmse": rmse(np.array(all_y_true), np.array(all_y_pred)),
                "mae": mae(np.array(all_y_true), np.array(all_y_pred)),
                "mape": mape(np.array(all_y_true), np.array(all_y_pred)),
            },
            "holiday_vs_normal": {
                "holiday_mape": mape(np.array(holiday_y_true), np.array(holiday_y_pred)) if holiday_y_true else None,
                "normal_mape": mape(np.array(normal_y_true), np.array(normal_y_pred)) if normal_y_true else None,
            },
        }
        return summary

    def print_summary(self, summary: dict) -> None:
        if "error" in summary:
            console.print(f"[red]Backtest hatası: {summary['error']}[/red]")
            return

        table = Table(title=f"Backtest: {summary['transaction_type']} / {summary['freq']}")
        table.add_column("Fold", style="dim")
        table.add_column("Train n")
        table.add_column("Val n")
        table.add_column("RMSE")
        table.add_column("MAE")
        table.add_column("MAPE%")
        table.add_column("PI Cov%")

        for f in summary["folds"]:
            cov = f"{f['pi_coverage']:.1f}%" if not np.isnan(f["pi_coverage"]) else "-"
            table.add_row(
                str(f["fold"]),
                str(f["train_size"]),
                str(f["val_size"]),
                f"{f['rmse']:.2f}",
                f"{f['mae']:.2f}",
                f"{f['mape']:.1f}%",
                cov,
            )
        console.print(table)

        ov = summary["overall"]
        console.print(f"  Genel RMSE={ov['rmse']:.2f}  MAE={ov['mae']:.2f}  MAPE={ov['mape']:.1f}%")
