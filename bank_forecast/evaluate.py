"""
Kullanım:
  python evaluate.py --input data/raw/transactions.csv --backtest-days 60 --plot
"""
import argparse
import sys
import os
import json

sys.path.insert(0, os.path.dirname(__file__))

from src.data.loader import load_transactions
from src.data.aggregator import aggregate_daily, aggregate_hourly
from src.evaluation.backtester import WalkForwardBacktester
from src.evaluation.metrics import full_report
from rich.console import Console
from rich.table import Table
import numpy as np

console = Console()


def parse_args():
    p = argparse.ArgumentParser(description="Model değerlendirme ve backtest")
    p.add_argument("--input", required=True, help="CSV giriş dosyası")
    p.add_argument("--backtest-days", type=int, default=60,
                   help="Son N günü test seti olarak ayır")
    p.add_argument("--types", default="", help="Virgülle ayrılmış işlem tipleri")
    p.add_argument("--freq", default="daily", choices=["daily", "hourly", "both"])
    p.add_argument("--registry", default="models/saved/model_registry.json")
    p.add_argument("--plot", action="store_true", help="Grafik üret")
    p.add_argument("--output-dir", default="outputs/reports")
    p.add_argument("--config", default="config/settings.yaml")
    return p.parse_args()


def main():
    args = parse_args()
    types = [t.strip() for t in args.types.split(",") if t.strip()] or None

    from src.pipeline import load_config
    cfg = load_config(args.config)
    data_cfg = cfg.get("data", {})
    features_cfg = cfg.get("features", {})
    models_cfg = cfg.get("models", {})
    working_hours = tuple(data_cfg.get("working_hours", [7, 18]))

    df = load_transactions(args.input)

    if not types:
        types = sorted(df["transaction_type"].unique().tolist())

    freqs = ["daily", "hourly"] if args.freq == "both" else [args.freq]

    # Registry'den en iyi modelleri oku
    model_map = {}
    if os.path.exists(args.registry):
        with open(args.registry, "r") as f:
            reg = json.load(f)
        for key, info in reg.get("models", {}).items():
            model_map[key] = info.get("best_model", "xgboost")

    summary_rows = []

    for transaction_type in types:
        for f in freqs:
            key = f"{transaction_type}_{f}"
            model_name = model_map.get(key, "xgboost")

            if f == "daily":
                agg = aggregate_daily(df)
            else:
                try:
                    agg = aggregate_hourly(df, working_hours=working_hours)
                except ValueError:
                    continue

            backtester = WalkForwardBacktester(
                transaction_type=transaction_type,
                freq=f,
                cv_folds=models_cfg.get("cv_folds", 5),
                min_train_days=90,
                cfg=features_cfg,
            )
            summary = backtester.run(agg, model_name=model_name, models_cfg=models_cfg)

            if "error" in summary:
                console.print(f"[yellow]{key}: {summary['error']}[/yellow]")
                continue

            backtester.print_summary(summary)

            ov = summary["overall"]
            summary_rows.append({
                "tip": transaction_type,
                "freq": f,
                "model": model_name,
                "rmse": ov["rmse"],
                "mae": ov["mae"],
                "mape": ov["mape"],
            })

    # Özet tablo
    if summary_rows:
        table = Table(title="Değerlendirme Özeti")
        table.add_column("Tip")
        table.add_column("Frekans")
        table.add_column("Model")
        table.add_column("RMSE")
        table.add_column("MAE")
        table.add_column("MAPE%")

        for r in summary_rows:
            mape_val = r["mape"]
            mape_str = f"{mape_val:.1f}%" if not np.isnan(mape_val) else "-"
            table.add_row(
                r["tip"], r["freq"], r["model"],
                f"{r['rmse']:.2f}", f"{r['mae']:.2f}", mape_str,
            )
        console.print(table)

        # JSON çıktı
        os.makedirs(args.output_dir, exist_ok=True)
        out_path = os.path.join(args.output_dir, "evaluation_results.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(summary_rows, f, ensure_ascii=False, indent=2, default=str)
        console.print(f"[green]Değerlendirme sonuçları: {out_path}[/green]")


if __name__ == "__main__":
    main()
