"""
Kullanım:
  python forecast.py --metric-type talimat --start 2025-07-01 --end 2025-07-31 --freq daily --plot
"""
import argparse
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from src.pipeline import forecast_pipeline, load_config, registry_filename
from src.data.loader import load_transactions
from src.data.aggregator import aggregate_daily, aggregate_hourly
from rich.console import Console

console = Console()


def parse_args():
    p = argparse.ArgumentParser(description="Banka işlem tahmini")
    p.add_argument("--metric-type", required=True, choices=["talimat", "islem"],
                   help="Hangi metrik registry'si kullanılacak")
    p.add_argument("--input", default=None,
                   help="Eğitimde kullanılan CSV (verilirse lag/rolling özellikleri "
                        "gerçek geçmiş verilerden beslenir; verilmezse tip medyanına düşer)")
    p.add_argument("--start", required=True, help="Tahmin başlangıç tarihi (YYYY-MM-DD)")
    p.add_argument("--end", required=True, help="Tahmin bitiş tarihi (YYYY-MM-DD)")
    p.add_argument("--teams", default="", help="Virgülle ayrılmış ekip adları (boş = hepsi)")
    p.add_argument("--types", default="", help="Virgülle ayrılmış işlem tipleri (boş = hepsi)")
    p.add_argument("--freq", default="daily", choices=["daily", "hourly", "both"],
                   help="Tahmin frekansı")
    p.add_argument("--format", default="csv,json,html",
                   help="Virgülle ayrılmış çıktı formatları: csv,json,html")
    p.add_argument("--plot", action="store_true", help="Grafik üret")
    p.add_argument("--output-dir", default="outputs/forecasts", help="Çıktı dizini")
    p.add_argument("--registry", default=None,
                   help="Model registry dosyası (boş = models/saved/model_registry_<metric_type>.json)")
    p.add_argument("--config", default="config/settings.yaml", help="Ayar dosyası")
    return p.parse_args()


def main():
    args = parse_args()

    teams = [t.strip() for t in args.teams.split(",") if t.strip()] or None
    types = [t.strip() for t in args.types.split(",") if t.strip()] or None
    fmt = [f.strip() for f in args.format.split(",") if f.strip()]
    registry_path = args.registry or registry_filename(args.metric_type)

    historical_data = None
    if args.input:
        cfg = load_config(args.config)
        working_hours = tuple(cfg.get("data", {}).get("working_hours", [7, 18]))
        df, _detected_metric = load_transactions(args.input)
        historical_data = {"daily": aggregate_daily(df)}
        try:
            historical_data["hourly"] = aggregate_hourly(df, working_hours=working_hours)
        except ValueError:
            historical_data["hourly"] = None

    console.print(f"\n[bold cyan]Tahmin başlıyor[/bold cyan]")
    console.print(f"  Metrik  : {args.metric_type}")
    console.print(f"  Aralık  : {args.start} → {args.end}")
    console.print(f"  Ekipler : {teams or 'tüm kayıtlı ekipler'}")
    console.print(f"  Tipler  : {types or 'tüm kayıtlı tipler'}")
    console.print(f"  Frekans : {args.freq}")

    result = forecast_pipeline(
        start=args.start,
        end=args.end,
        metric_type=args.metric_type,
        teams=teams,
        types=types,
        freq=args.freq,
        output_dir=args.output_dir,
        fmt=fmt,
        plot=args.plot,
        registry_path=registry_path,
        config_path=args.config,
        historical_data=historical_data,
    )

    total = sum(
        sum(d.get("predicted_count", 0) for d in info.get("daily", []))
        for by_type in result.get("by_team", {}).values()
        for info in by_type.values()
    )
    console.print(f"\n[bold green]Tahmin tamamlandı. Toplam tahmin: {total:,.0f} işlem[/bold green]")


if __name__ == "__main__":
    main()
