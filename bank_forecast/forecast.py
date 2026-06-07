"""
Kullanım:
  python forecast.py --start 2025-07-01 --end 2025-07-31 --freq daily --plot
"""
import argparse
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from src.pipeline import forecast_pipeline
from rich.console import Console

console = Console()


def parse_args():
    p = argparse.ArgumentParser(description="Banka işlem tahmini")
    p.add_argument("--start", required=True, help="Tahmin başlangıç tarihi (YYYY-MM-DD)")
    p.add_argument("--end", required=True, help="Tahmin bitiş tarihi (YYYY-MM-DD)")
    p.add_argument("--types", default="", help="Virgülle ayrılmış işlem tipleri (boş = hepsi)")
    p.add_argument("--freq", default="daily", choices=["daily", "hourly", "both"],
                   help="Tahmin frekansı")
    p.add_argument("--format", default="csv,json,html",
                   help="Virgülle ayrılmış çıktı formatları: csv,json,html")
    p.add_argument("--plot", action="store_true", help="Grafik üret")
    p.add_argument("--output-dir", default="outputs/forecasts", help="Çıktı dizini")
    p.add_argument("--registry", default="models/saved/model_registry.json",
                   help="Model registry dosyası")
    p.add_argument("--config", default="config/settings.yaml", help="Ayar dosyası")
    return p.parse_args()


def main():
    args = parse_args()

    types = [t.strip() for t in args.types.split(",") if t.strip()] or None
    fmt = [f.strip() for f in args.format.split(",") if f.strip()]

    console.print(f"\n[bold cyan]Tahmin başlıyor[/bold cyan]")
    console.print(f"  Aralık  : {args.start} → {args.end}")
    console.print(f"  Tipler  : {types or 'tüm kayıtlı tipler'}")
    console.print(f"  Frekans : {args.freq}")

    result = forecast_pipeline(
        start=args.start,
        end=args.end,
        types=types,
        freq=args.freq,
        output_dir=args.output_dir,
        fmt=fmt,
        plot=args.plot,
        registry_path=args.registry,
        config_path=args.config,
    )

    total = sum(
        sum(d.get("predicted_count", 0) for d in v.get("daily", []))
        for v in result.get("by_type", {}).values()
    )
    console.print(f"\n[bold green]Tahmin tamamlandı. Toplam tahmin: {total:,.0f} işlem[/bold green]")


if __name__ == "__main__":
    main()
