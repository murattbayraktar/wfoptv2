"""
Gerçekçi 18 aylık sentetik işlem datası üretir.
Kullanım: python scripts/generate_demo_data.py --output data/raw/demo.csv
"""
import argparse
import numpy as np
import pandas as pd
from datetime import date, timedelta
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


DEMO_CONFIG = {
    "start_date": "2024-01-01",
    "end_date": "2025-06-30",
    "transaction_types": {
        "EFT":           {"base_daily": 200, "trend": +0.15, "cv": 0.28, "calendar_sensitivity": 1.4},
        "Havale":        {"base_daily": 350, "trend": +0.05, "cv": 0.22, "calendar_sensitivity": 1.3},
        "Kredi Ödemesi": {"base_daily": 180, "trend": -0.02, "cv": 0.55, "calendar_sensitivity": 2.1},
        "Mevduat":       {"base_daily": 120, "trend": +0.08, "cv": 0.35, "calendar_sensitivity": 1.6},
        "Çek Tahsilat":  {"base_daily":  60, "trend": -0.10, "cv": 0.72, "calendar_sensitivity": 2.4},
    },
    "hourly_profile": [
        0, 0, 0, 0, 0, 0,
        0.02, 0.05, 0.12, 0.14, 0.13, 0.11,
        0.08, 0.09, 0.10, 0.09, 0.07, 0.05,
        0.03, 0.02, 0, 0, 0, 0,
    ],
}

TR_PUBLIC_HOLIDAYS_MMDD = [
    "01-01", "04-23", "05-01", "05-19", "07-15", "08-30", "10-29"
]

RELIGIOUS_HOLIDAYS_DATES = [
    "2024-04-10", "2024-04-11", "2024-04-12",
    "2024-06-16", "2024-06-17", "2024-06-18", "2024-06-19",
    "2025-03-30", "2025-03-31", "2025-04-01",
    "2025-06-06", "2025-06-07", "2025-06-08", "2025-06-09",
]

WEEKEND_DAYS = {5, 6}  # Cumartesi, Pazar (weekday)


def is_holiday(d: date) -> bool:
    mmdd = d.strftime("%m-%d")
    if mmdd in TR_PUBLIC_HOLIDAYS_MMDD:
        return True
    if d.strftime("%Y-%m-%d") in RELIGIOUS_HOLIDAYS_DATES:
        return True
    return False


def is_working_day(d: date) -> bool:
    return d.weekday() not in WEEKEND_DAYS and not is_holiday(d)


def day_multiplier(d: date, calendar_sensitivity: float) -> float:
    """Gün bazlı çarpan: tatil/hafta sonu/ay sonu etkileri."""
    if not is_working_day(d):
        return 0.0

    mult = 1.0

    # Tatil sonrası yığılma
    prev = d - timedelta(days=1)
    if not is_working_day(prev):
        mult *= (1 + (calendar_sensitivity - 1) * 0.5)

    prev2 = d - timedelta(days=2)
    if not is_working_day(prev2) and is_working_day(prev):
        mult *= (1 + (calendar_sensitivity - 1) * 0.2)

    # Ay sonu
    tomorrow = d + timedelta(days=1)
    if tomorrow.month != d.month:
        mult *= (1 + (calendar_sensitivity - 1) * 0.6)

    # Ay başı
    if d.day == 1:
        mult *= (1 + (calendar_sensitivity - 1) * 0.3)

    # Pazartesi efekti (hafta sonu birikimi)
    if d.weekday() == 0:
        mult *= 1.15

    # Cuma efekti (düşük)
    if d.weekday() == 4:
        mult *= 0.92

    return mult


def generate(output_path: str, seed: int = 42) -> None:
    rng = np.random.default_rng(seed)
    cfg = DEMO_CONFIG

    start = pd.Timestamp(cfg["start_date"])
    end = pd.Timestamp(cfg["end_date"])
    dates = pd.date_range(start, end, freq="D")
    n_days = len(dates)
    hourly_profile = np.array(cfg["hourly_profile"])

    rows = []

    for tt, params in cfg["transaction_types"].items():
        base = params["base_daily"]
        trend = params["trend"]
        cv = params["cv"]
        cal_sens = params["calendar_sensitivity"]

        # Trend faktörü (yıllık büyüme)
        trend_factors = np.array([
            1 + trend * (i / 365) for i, _ in enumerate(dates)
        ])

        for i, d in enumerate(dates):
            dm = day_multiplier(d.date(), cal_sens)
            if dm == 0:
                continue

            expected = base * trend_factors[i] * dm
            # Negatif binom dağılımı (overdispersed Poisson)
            r = 1 / (cv ** 2)
            p = r / (r + expected)
            daily_count = int(rng.negative_binomial(r, p))

            # Saatlik dağılım
            hour_probs = hourly_profile.copy()
            noise = rng.dirichlet(hour_probs * 20 + 0.1)
            hourly_counts = rng.multinomial(daily_count, noise)

            for h, cnt in enumerate(hourly_counts):
                if cnt == 0:
                    continue
                rows.append({
                    "islem_tipi": tt,
                    "tarih": d.strftime("%Y-%m-%d"),
                    "saat": h,
                    "islem_hacmi": int(cnt),
                })

    df = pd.DataFrame(rows, columns=["islem_tipi", "tarih", "saat", "islem_hacmi"])
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
    df.to_csv(output_path, index=False, encoding="utf-8")
    print(f"Demo veri oluşturuldu: {output_path}")
    print(f"  Toplam satır  : {len(df):,}")
    print(f"  İşlem tipleri : {sorted(df['islem_tipi'].unique())}")
    print(f"  Tarih araligi : {df['tarih'].min()} - {df['tarih'].max()}")
    print(f"  Toplam hacim  : {df['islem_hacmi'].sum():,}")


def main():
    p = argparse.ArgumentParser(description="Demo veri üretici")
    p.add_argument("--output", default="data/raw/demo.csv", help="Çıktı CSV dosyası")
    p.add_argument("--seed", type=int, default=42, help="Rastgele tohum")
    args = p.parse_args()
    generate(args.output, seed=args.seed)


if __name__ == "__main__":
    main()
