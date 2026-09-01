"""
Kullanım:
  python evaluate.py --input data/raw/transactions_talimat.csv --backtest-days 60 --plot
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
    p.add_argument("--input", required=True, help="CSV giriş dosyası (ham talimat/referans formatında)")
    p.add_argument("--metric-type", default="talimat", choices=["talimat", "islem"],
                   help="Hangi metrik değerlendirilecek ('islem' için CSV'de EntryProcessCount kolonu gerekir)")
    p.add_argument("--backtest-days", type=int, default=60,
                   help="Son N günü test seti olarak ayır")
    p.add_argument("--teams", default="", help="Virgülle ayrılmış ekip adları")
    p.add_argument("--types", default="", help="Virgülle ayrılmış işlem tipleri")
    p.add_argument("--freq", default="daily", choices=["daily", "hourly", "both"])
    p.add_argument("--registry", default=None,
                   help="Model registry dosyası (boş = models/saved/model_registry_<metric_type>.json)")
    p.add_argument("--plot", action="store_true", help="Grafik üret")
    p.add_argument("--output-dir", default="outputs/reports")
    p.add_argument("--config", default="config/settings.yaml")
    return p.parse_args()


def main():
    args = parse_args()
    teams = [t.strip() for t in args.teams.split(",") if t.strip()] or None
    types = [t.strip() for t in args.types.split(",") if t.strip()] or None

    from src.pipeline import load_config, registry_filename
    cfg = load_config(args.config)
    data_cfg = cfg.get("data", {})
    features_cfg = cfg.get("features", {})
    models_cfg = cfg.get("models", {})
    working_hours = tuple(data_cfg.get("working_hours", [7, 18]))

    results = load_transactions(args.input)
    df = results.get(args.metric_type)
    if df is None:
        console.print(f"[red]CSV'de '{args.metric_type}' metriği için veri yok "
                       "(islem için EntryProcessCount kolonu gerekli).[/red]")
        sys.exit(1)
    metric_type = args.metric_type

    if not teams:
        teams = sorted(df["team"].unique().tolist())
    if not types:
        types = sorted(df["transaction_type"].unique().tolist())

    freqs = ["daily", "hourly"] if args.freq == "both" else [args.freq]
    registry_path = args.registry or registry_filename(metric_type)

    # Registry'den en iyi modelleri oku (nested: team -> type -> freq)
    model_map: dict = {}
    if os.path.exists(registry_path):
        with open(registry_path, "r", encoding="utf-8") as f:
            reg = json.load(f)
        for team, by_type in reg.get("models", {}).items():
            for tt, by_freq in by_type.items():
                for f_freq, info in by_freq.items():
                    model_map[(team, tt, f_freq)] = info.get("best_model", "xgboost")

    summary_rows = []

    for team in teams:
        for transaction_type in types:
            for f in freqs:
                model_name = model_map.get((team, transaction_type, f), "xgboost")

                if f == "daily":
                    agg = aggregate_daily(df)
                else:
                    try:
                        agg = aggregate_hourly(df, working_hours=working_hours)
                    except ValueError:
                        continue

                if not ((agg["team"] == team) & (agg["transaction_type"] == transaction_type)).any():
                    continue

                backtester = WalkForwardBacktester(
                    transaction_type=transaction_type,
                    team=team,
                    freq=f,
                    cv_folds=models_cfg.get("cv_folds", 5),
                    min_train_days=90,
                    cfg=features_cfg,
                )
                summary = backtester.run(agg, model_name=model_name, models_cfg=models_cfg)

                label = f"{team} / {transaction_type} / {f}"
                if "error" in summary:
                    console.print(f"[yellow]{label}: {summary['error']}[/yellow]")
                    continue

                backtester.print_summary(summary)

                ov = summary["overall"]
                summary_rows.append({
                    "ekip": team,
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
        table.add_column("Ekip")
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
                r["ekip"], r["tip"], r["freq"], r["model"],
                f"{r['rmse']:.2f}", f"{r['mae']:.2f}", mape_str,
            )
        console.print(table)

        # JSON çıktı
        os.makedirs(args.output_dir, exist_ok=True)
        out_path = os.path.join(args.output_dir, f"evaluation_results_{metric_type}.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(summary_rows, f, ensure_ascii=False, indent=2, default=str)
        console.print(f"[green]Değerlendirme sonuçları: {out_path}[/green]")


if __name__ == "__main__":
    main()
