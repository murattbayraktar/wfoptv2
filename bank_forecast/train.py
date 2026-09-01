"""
Kullanım:
  python train.py --input data/raw/transactions_talimat.csv --freq daily --models auto --report
"""
import argparse
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from src.pipeline import train_pipeline
from rich.console import Console

console = Console()


def parse_args():
    p = argparse.ArgumentParser(description="Banka işlem tahmin modeli eğitimi")
    p.add_argument("--input", required=True, help="CSV giriş dosyası (ham talimat/referans formatında)")
    p.add_argument("--metric-type", default="talimat", choices=["talimat", "islem"],
                   help="Hangi metrik eğitilecek ('islem' için CSV'de EntryProcessCount kolonu gerekir)")
    p.add_argument("--freq", default="daily", choices=["daily", "hourly", "both"],
                   help="Tahmin frekansı")
    p.add_argument("--teams", default="", help="Virgülle ayrılmış ekip adları (boş = hepsi)")
    p.add_argument("--types", default="", help="Virgülle ayrılmış işlem tipleri (boş = hepsi)")
    p.add_argument("--models", default="auto",
                   help="Virgülle ayrılmış model listesi veya 'auto'")
    p.add_argument("--cv-folds", type=int, default=5, help="Cross-validation fold sayısı")
    p.add_argument("--metric", default="rmse", choices=["rmse", "mae", "mape"],
                   help="Model seçim metriği")
    p.add_argument("--output-dir", default=None, help="Model çıktı dizini (boş = models/saved/<metric_type>)")
    p.add_argument("--report", action="store_true", help="HTML rapor üret")
    p.add_argument("--config", default="config/settings.yaml", help="Ayar dosyası")
    return p.parse_args()


def main():
    args = parse_args()

    teams = [t.strip() for t in args.teams.split(",") if t.strip()] or None
    types = [t.strip() for t in args.types.split(",") if t.strip()] or None
    if args.models.lower() == "auto":
        models = None
    else:
        models = [m.strip() for m in args.models.split(",") if m.strip()]

    console.print(f"\n[bold cyan]Eğitim başlıyor[/bold cyan]")
    console.print(f"  Giriş   : {args.input}")
    console.print(f"  Frekans : {args.freq}")
    console.print(f"  Ekipler : {teams or 'tüm ekipler'}")
    console.print(f"  Tipler  : {types or 'tüm tipler'}")
    console.print(f"  Modeller: {models or 'otomatik seçim'}")

    registry = train_pipeline(
        input_path=args.input,
        metric_type=args.metric_type,
        freq=args.freq,
        teams=teams,
        types=types,
        models=models,
        cv_folds=args.cv_folds,
        metric=args.metric,
        output_dir=args.output_dir,
        report=args.report,
        config_path=args.config,
    )

    n_models = sum(
        len(by_freq)
        for by_type in registry.get("models", {}).values()
        for by_freq in by_type.values()
    )
    console.print(f"\n[bold green]Eğitim tamamlandı ({registry.get('metric_type')}). {n_models} model eğitildi.[/bold green]")


if __name__ == "__main__":
    main()
