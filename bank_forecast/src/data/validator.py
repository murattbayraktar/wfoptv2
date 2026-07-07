import pandas as pd
import numpy as np
from rich.console import Console
from rich.table import Table

console = Console()


def validate(df: pd.DataFrame, min_training_days: int = 60) -> dict:
    teams = sorted(df["team"].unique().tolist())
    report = {
        "total_rows": len(df),
        "date_range": {"start": str(df["date"].min().date()), "end": str(df["date"].max().date())},
        "n_days": (df["date"].max() - df["date"].min()).days + 1,
        "transaction_types": sorted(df["transaction_type"].unique().tolist()),
        "teams": teams,
        "null_counts": df.isnull().sum().to_dict(),
        "warnings": [],
        "errors": [],
    }

    n_days = report["n_days"]
    if n_days < min_training_days:
        report["warnings"].append(
            f"Veri {n_days} günlük. {min_training_days} günden az: ML model yerine Holt-Winters önerilir."
        )

    if df["count"].min() < 0:
        report["errors"].append("Negatif count değerleri mevcut.")

    for tt in report["transaction_types"]:
        subset = df[df["transaction_type"] == tt]
        n = (subset["date"].max() - subset["date"].min()).days + 1
        if n < min_training_days:
            report["warnings"].append(
                f"'{tt}' için yalnızca {n} günlük veri var — ML yerine Holt-Winters kullanılacak."
            )

    for team in teams:
        for tt in report["transaction_types"]:
            subset = df[(df["team"] == team) & (df["transaction_type"] == tt)]
            if subset.empty:
                continue
            n = (subset["date"].max() - subset["date"].min()).days + 1
            if n < min_training_days:
                report["warnings"].append(
                    f"'{team}' / '{tt}' için yalnızca {n} günlük veri var — ML yerine Holt-Winters kullanılacak."
                )

    counts = df["count"]
    q1, q3 = counts.quantile(0.25), counts.quantile(0.75)
    iqr = q3 - q1
    outliers = ((counts < q1 - 3 * iqr) | (counts > q3 + 3 * iqr)).sum()
    if outliers > 0:
        report["warnings"].append(f"{outliers} adet count aykırı değer tespit edildi (IQR yöntemi).")

    return report


def print_validation_report(report: dict) -> None:
    console.print("\n[bold cyan]Veri Doğrulama Raporu[/bold cyan]")
    console.print(f"  Toplam satır   : {report['total_rows']:,}")
    console.print(f"  Tarih aralığı  : {report['date_range']['start']} → {report['date_range']['end']}")
    console.print(f"  Gün sayısı     : {report['n_days']}")
    console.print(f"  İşlem tipleri  : {', '.join(report['transaction_types'])}")
    console.print(f"  Ekipler        : {', '.join(report['teams'])}")

    for w in report["warnings"]:
        console.print(f"  [yellow]⚠ {w}[/yellow]")
    for e in report["errors"]:
        console.print(f"  [red]✗ {e}[/red]")

    if not report["warnings"] and not report["errors"]:
        console.print("  [green]✓ Veri kalitesi iyi.[/green]")
