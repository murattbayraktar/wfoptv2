"""Ana orkestratör: train | forecast | evaluate akışlarını yönetir."""
import json
import os
from datetime import datetime
import pandas as pd
import numpy as np
import yaml
from rich.console import Console

from src.data.loader import load_transactions
from src.data.validator import validate, print_validation_report
from src.data.aggregator import aggregate_daily, aggregate_hourly
from src.features.feature_pipeline import build_features, get_feature_matrix
from src.models.model_selector import ModelSelector
from src.evaluation.metrics import full_report, rmse, mae
from src.reporting.plot_builder import plot_forecast, plot_hourly_heatmap, plot_model_comparison, plot_feature_importance
from src.reporting.html_reporter import generate_training_report, generate_forecast_report

console = Console()

REGISTRY_FILE = "models/saved/model_registry.json"


def load_config(config_path: str = "config/settings.yaml") -> dict:
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    return {}


def _save_registry(registry: dict, path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(registry, f, ensure_ascii=False, indent=2, default=str)


def _load_registry(path: str = REGISTRY_FILE) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def train_pipeline(
    input_path: str,
    freq: str = "daily",
    types: list[str] = None,
    models: list[str] = None,
    cv_folds: int = 5,
    metric: str = "rmse",
    output_dir: str = "models/saved",
    report: bool = True,
    config_path: str = "config/settings.yaml",
    progress_callback=None,
) -> dict:
    cfg = load_config(config_path)
    models_cfg = cfg.get("models", {})
    features_cfg = cfg.get("features", {})
    data_cfg = cfg.get("data", {})
    min_days = data_cfg.get("min_training_days", 60)
    working_hours = tuple(data_cfg.get("working_hours", [7, 18]))

    console.print("[bold green]Veri yükleniyor...[/bold green]")
    df = load_transactions(input_path)
    val_report = validate(df, min_days)
    print_validation_report(val_report)

    if val_report["errors"]:
        raise ValueError("Veri doğrulama hatası: " + "; ".join(val_report["errors"]))

    available_types = val_report["transaction_types"]
    if types:
        types = [t for t in types if t in available_types]
    else:
        types = available_types

    if models and models != ["auto"]:
        candidate_models = models
    else:
        candidate_models = None  # ModelSelector tüm adayları dener

    freqs = ["daily", "hourly"] if freq == "both" else [freq]

    registry = {
        "trained_at": datetime.now().isoformat(),
        "data_range": {
            "start": str(df["date"].min().date()),
            "end": str(df["date"].max().date()),
        },
        "models": {},
    }

    if progress_callback:
        progress_callback({
            "kind": "data_ready",
            "row_count": int(len(df)),
            "transaction_types": available_types,
            "data_range": registry["data_range"],
        })
        total_units = len(types) * len(freqs)
        progress_callback({
            "kind": "plan",
            "total_units": total_units,
            "types": types,
            "freqs": freqs,
        })

    selector = ModelSelector()
    all_scores_for_plot = {}

    unit_index = 0
    for transaction_type in types:
        for f in freqs:
            key = f"{transaction_type}_{f}"
            unit_index += 1
            console.print(f"\n[bold]{'─'*50}[/bold]")
            console.print(f"[bold yellow]Eğitim: {key}[/bold yellow]")
            if progress_callback:
                progress_callback({
                    "kind": "unit_start",
                    "type": transaction_type,
                    "freq": f,
                    "index": unit_index,
                    "total": len(types) * len(freqs),
                })

            try:
                if f == "daily":
                    agg = aggregate_daily(df)
                else:
                    agg = aggregate_hourly(df, working_hours=working_hours)

                subset = agg[agg["transaction_type"] == transaction_type].copy()

                feat_df, feat_cols, encoder = build_features(
                    subset, freq=f, target_col="count",
                    fit_encoder=True, cfg=features_cfg,
                )
                X, y = get_feature_matrix(feat_df, feat_cols)

                # Eğitim / doğrulama bölünmesi (son %20 veya son 60 gün)
                n = len(X)
                split_idx = max(int(n * 0.8), n - 60)
                X_tr, y_tr = X.iloc[:split_idx], y.iloc[:split_idx]

                # Model seçimi
                sel_result = selector.select_best(
                    transaction_type=transaction_type,
                    freq=f,
                    X_train=X_tr,
                    y_train=y_tr,
                    cv_folds=cv_folds,
                    metric=metric,
                    candidates=candidate_models,
                    cfg=models_cfg,
                    min_training_days=min_days,
                    progress_callback=progress_callback,
                )

                # Final model tüm veri üzerinde eğit
                final_model = selector.train_best(sel_result, transaction_type, f, X, y, models_cfg)

                # Kaydet
                model_path = os.path.join(output_dir, f"{key}_best.pkl")
                final_model.save(model_path)

                # Feature importance
                fi_df = final_model.get_feature_importance()
                top5 = fi_df["feature"].head(5).tolist() if not fi_df.empty else []

                registry["models"][key] = {
                    "best_model": sel_result["best_model"],
                    "cv_rmse": sel_result["best_score"],
                    "cv_mae": sel_result["all_scores"].get(sel_result["best_model"], 0),
                    "all_scores": sel_result["all_scores"],
                    "selection_reason": sel_result["selection_reason"],
                    "feature_importance_top5": top5,
                    "model_path": model_path,
                    "encoder_path": os.path.join(output_dir, f"{key}_encoder.pkl"),
                    "feature_names": feat_cols,
                }

                # Encoder kaydet
                import joblib
                joblib.dump(encoder, registry["models"][key]["encoder_path"])

                all_scores_for_plot[key] = sel_result["all_scores"]

                # Feature importance grafiği
                if not fi_df.empty and report:
                    fi_path = f"outputs/plots/fi_{key}.html"
                    plot_feature_importance(fi_df, f"Feature Önemi: {key}", fi_path)

                if progress_callback:
                    progress_callback({
                        "kind": "unit_done",
                        "type": transaction_type,
                        "freq": f,
                        "model": sel_result["best_model"],
                        "cv_rmse": sel_result["best_score"],
                        "feature_importance_top5": top5,
                    })

            except Exception as e:
                console.print(f"[red]Hata ({key}): {e}[/red]")
                import traceback
                traceback.print_exc()
                if progress_callback:
                    progress_callback({
                        "kind": "unit_failed",
                        "type": transaction_type,
                        "freq": f,
                        "error": str(e),
                    })

    registry_path = os.path.join(output_dir, "model_registry.json")
    _save_registry(registry, registry_path)
    console.print(f"\n[green]Registry kaydedildi: {registry_path}[/green]")
    if progress_callback:
        progress_callback({"kind": "completed", "registry_path": registry_path})

    if report:
        try:
            plot_paths = {}
            if all_scores_for_plot:
                # her işlem tipi için aynı modelleri karşılaştır
                by_type_scores = {}
                for key, scores in all_scores_for_plot.items():
                    tt = "_".join(key.split("_")[:-1])
                    by_type_scores.setdefault(tt, {}).update(scores)
                mc_path = "outputs/plots/model_comparison.html"
                plot_model_comparison(by_type_scores, metric, mc_path)
                plot_paths["Model Karşılaştırması"] = mc_path

            report_path = "outputs/reports/training_report.html"
            generate_training_report(registry, report_path, plot_paths)
            console.print(f"[green]Eğitim raporu: {report_path}[/green]")
        except Exception as e:
            console.print(f"[yellow]Rapor oluşturulamadı: {e}[/yellow]")

    return registry


def forecast_pipeline(
    start: str,
    end: str,
    types: list[str] = None,
    freq: str = "daily",
    output_dir: str = "outputs/forecasts",
    fmt: list[str] = None,
    plot: bool = True,
    registry_path: str = REGISTRY_FILE,
    config_path: str = "config/settings.yaml",
) -> dict:
    cfg = load_config(config_path)
    features_cfg = cfg.get("features", {})
    forecast_cfg = cfg.get("forecast", {})

    if fmt is None:
        fmt = ["csv", "json", "html"]

    registry = _load_registry(registry_path)
    base_dir = os.path.dirname(registry_path)

    start_dt = pd.Timestamp(start)
    end_dt = pd.Timestamp(end)
    date_range = pd.date_range(start_dt, end_dt, freq="D")

    if not types:
        # Registry'deki tüm tipleri çıkar
        all_keys = list(registry["models"].keys())
        types = list({
            "_".join(k.split("_")[:-1]) for k in all_keys
        })

    freqs = ["daily", "hourly"] if freq == "both" else [freq]

    result = {
        "generated_at": datetime.now().isoformat(),
        "forecast_range": {"start": start, "end": end},
        "by_type": {},
    }

    import joblib
    from src.features.calendar_features import add_calendar_features
    from src.features.lag_features import add_lag_features
    from src.features.seasonal_features import add_daily_fourier, add_hourly_fourier
    from src.models.base_model import BaseForecaster

    for transaction_type in types:
        result["by_type"][transaction_type] = {}
        for f in freqs:
            key = f"{transaction_type}_{f}"
            if key not in registry["models"]:
                console.print(f"[yellow]Model bulunamadı: {key}, atlanıyor.[/yellow]")
                continue

            model_info = registry["models"][key]

            try:
                model: BaseForecaster = BaseForecaster.load(model_info["model_path"])
                encoder = joblib.load(model_info["encoder_path"])
                feat_cols = model_info["feature_names"]
            except Exception as e:
                console.print(f"[red]Model yüklenemedi ({key}): {e}[/red]")
                continue

            if f == "daily":
                forecast_df = pd.DataFrame({
                    "date": date_range,
                    "transaction_type": transaction_type,
                    "count": 0,
                    "amount": 0,
                })
            else:
                working_hours = cfg.get("data", {}).get("working_hours", [7, 18])
                hours = list(range(working_hours[0], working_hours[1] + 1))
                rows = [(d, h, transaction_type) for d in date_range for h in hours]
                forecast_df = pd.DataFrame(rows, columns=["date", "hour", "transaction_type"])
                forecast_df["count"] = 0
                forecast_df["amount"] = 0

            forecast_df["date"] = pd.to_datetime(forecast_df["date"])
            forecast_df = add_calendar_features(forecast_df)

            # Lag özellikleri için sıfır doldur (tahmin modunda geçmiş bilinmiyor)
            lag_keys = [c for c in feat_cols if c.startswith("lag_") or c.startswith("rolling_")]
            for col in lag_keys:
                forecast_df[col] = 0

            # Fourier
            if f == "daily":
                forecast_df = add_daily_fourier(
                    forecast_df,
                    weekly_terms=features_cfg.get("fourier_weekly_terms", 3),
                    yearly_terms=features_cfg.get("fourier_yearly_terms", 5),
                )
            else:
                forecast_df = add_hourly_fourier(forecast_df)

            # Target encoding
            forecast_df["transaction_type_enc"] = encoder.transform(
                forecast_df[["transaction_type"]]
            )

            # Eksik sütunları sıfırla
            for col in feat_cols:
                if col not in forecast_df.columns:
                    forecast_df[col] = 0

            X_pred = forecast_df[feat_cols].fillna(0)
            preds = model.predict(X_pred)

            try:
                qpreds = model.predict_quantiles(X_pred, [0.1, 0.9])
                lower = qpreds[0.1]
                upper = qpreds[0.9]
            except Exception:
                lower = preds * 0.8
                upper = preds * 1.2

            forecast_df["predicted_count"] = np.round(preds, 1)
            forecast_df["lower_80"] = np.round(lower, 1)
            forecast_df["upper_80"] = np.round(upper, 1)
            forecast_df["confidence"] = "high"
            forecast_df["model_used"] = model_info["best_model"]

            calendar_cols = ["is_public_holiday", "is_religious_holiday", "is_month_start",
                             "is_month_end", "is_eve_of_holiday"]
            def _flags(row):
                return [c for c in calendar_cols if row.get(c, 0) == 1]
            forecast_df["calendar_flags"] = forecast_df.apply(
                lambda r: ",".join(_flags(r)), axis=1
            )

            if f == "daily":
                result["by_type"][transaction_type]["model_used"] = model_info["best_model"]
                daily_list = []
                for _, row in forecast_df.iterrows():
                    daily_list.append({
                        "date": str(row["date"].date()),
                        "predicted_count": float(row["predicted_count"]),
                        "lower_80": float(row["lower_80"]),
                        "upper_80": float(row["upper_80"]),
                        "confidence": row["confidence"],
                        "calendar_flags": row["calendar_flags"].split(",") if row["calendar_flags"] else [],
                    })
                result["by_type"][transaction_type]["daily"] = daily_list
            else:
                hourly_by_date = {}
                for _, row in forecast_df.iterrows():
                    d = str(row["date"].date())
                    hourly_by_date.setdefault(d, []).append({
                        "hour": int(row["hour"]),
                        "count": float(row["predicted_count"]),
                    })
                result["by_type"][transaction_type]["hourly"] = hourly_by_date

            # CSV çıktı
            if "csv" in fmt:
                os.makedirs(output_dir, exist_ok=True)
                csv_path = os.path.join(output_dir, f"forecast_{start}_{transaction_type}_{f}.csv")
                out_cols = ["date", "transaction_type", "predicted_count", "lower_80", "upper_80",
                            "confidence", "model_used", "calendar_flags"]
                if f == "hourly":
                    out_cols.insert(1, "hour")
                forecast_df[out_cols].to_csv(csv_path, index=False)

            # Grafik
            if plot and f == "daily":
                plot_path = f"outputs/plots/forecast_{transaction_type}_{f}_{start}.html"
                plot_forecast(forecast_df, transaction_type, plot_path)

    # JSON çıktı
    if "json" in fmt:
        os.makedirs(output_dir, exist_ok=True)
        json_path = os.path.join(output_dir, f"forecast_{start}.json")
        with open(json_path, "w", encoding="utf-8") as jf:
            json.dump(result, jf, ensure_ascii=False, indent=2, default=str)
        console.print(f"[green]JSON: {json_path}[/green]")

    # HTML rapor
    if "html" in fmt:
        plot_paths = {}
        if plot:
            for transaction_type in types:
                pp = f"outputs/plots/forecast_{transaction_type}_daily_{start}.html"
                if os.path.exists(pp):
                    plot_paths[f"{transaction_type} Günlük Tahmin"] = pp
        report_path = f"outputs/reports/forecast_report_{start}.html"
        generate_forecast_report(result, report_path, plot_paths)
        console.print(f"[green]HTML Rapor: {report_path}[/green]")

    return result
