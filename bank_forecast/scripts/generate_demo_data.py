"""
Gerçekçi 18 aylık sentetik işlem datası üretir — ekip kırılımlı, iki ayrı
metrik dosyası olarak (talimat_adet / islem_adet).

Kullanım: python scripts/generate_demo_data.py --output-dir data/raw
  -> data/raw/demo_talimat.csv ve data/raw/demo_islem.csv üretir.
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
    # Her işlem tipini hangi ekiplerin ne oranda işlediği — bazı ekipler bazı
    # tipleri hiç işlemez (aggregator.py'nin yalnızca gözlemlenen (ekip, tip)
    # çiftlerini kullandığı senaryoyu demo veride de yansıtmak için).
    "team_weights": {
        "EFT":           {"Merkez Ekip": 0.45, "İstanbul Ekip": 0.35, "Ankara Ekip": 0.20},
        "Havale":        {"Merkez Ekip": 0.30, "İstanbul Ekip": 0.30, "Ankara Ekip": 0.25, "İzmir Ekip": 0.15},
        "Kredi Ödemesi": {"Merkez Ekip": 0.50, "İzmir Ekip": 0.50},
        "Mevduat":       {"İstanbul Ekip": 0.60, "Ankara Ekip": 0.40},
        "Çek Tahsilat":  {"Merkez Ekip": 1.0},
    },
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


def generate(output_dir: str, seed: int = 42) -> None:
    rng = np.random.default_rng(seed)
    cfg = DEMO_CONFIG

    start = pd.Timestamp(cfg["start_date"])
    end = pd.Timestamp(cfg["end_date"])
    dates = pd.date_range(start, end, freq="D")
    hourly_profile = np.array(cfg["hourly_profile"])

    # Ekip bazında sabit "tamamlanma oranı" (talimat -> islem dönüşümü) —
    # gerçekçi olması için ekip/tip başına biraz farklı, zamanla sabit.
    completion_rates: dict[tuple[str, str], float] = {}
    for tt, weights in cfg["team_weights"].items():
        for team in weights:
            completion_rates[(team, tt)] = float(rng.uniform(0.82, 0.97))

    talimat_rows = []
    islem_rows = []

    for tt, params in cfg["transaction_types"].items():
        base = params["base_daily"]
        trend = params["trend"]
        cv = params["cv"]
        cal_sens = params["calendar_sensitivity"]
        team_weights = cfg["team_weights"][tt]
        teams = list(team_weights.keys())
        weight_arr = np.array(list(team_weights.values()))
        weight_arr = weight_arr / weight_arr.sum()

        trend_factors = np.array([1 + trend * (i / 365) for i in range(len(dates))])

        for i, d in enumerate(dates):
            dm = day_multiplier(d.date(), cal_sens)
            if dm == 0:
                continue

            expected = base * trend_factors[i] * dm
            r = 1 / (cv ** 2)
            p = r / (r + expected)
            daily_count = int(rng.negative_binomial(r, p))
            if daily_count == 0:
                continue

            # Saatlik dağılım
            hour_probs = hourly_profile.copy()
            noise = rng.dirichlet(hour_probs * 20 + 0.1)
            hourly_counts = rng.multinomial(daily_count, noise)

            date_str = d.strftime("%Y-%m-%d")
            for h, hour_total in enumerate(hourly_counts):
                if hour_total == 0:
                    continue
                # Bu saatlik toplamı ekipler arasında paylaştır
                team_counts = rng.multinomial(hour_total, weight_arr) if len(teams) > 1 else [hour_total]
                for team, talimat_cnt in zip(teams, team_counts):
                    if talimat_cnt == 0:
                        continue
                    talimat_rows.append({
                        "ekip_adi": team,
                        "islem_tipi": tt,
                        "tarih": date_str,
                        "saat": h,
                        "talimat_adet": int(talimat_cnt),
                    })

                    rate = completion_rates[(team, tt)]
                    islem_cnt = int(rng.binomial(talimat_cnt, rate))
                    if islem_cnt > 0:
                        islem_rows.append({
                            "ekip_adi": team,
                            "islem_tipi": tt,
                            "tarih": date_str,
                            "saat": h,
                            "islem_adet": islem_cnt,
                        })

    os.makedirs(output_dir, exist_ok=True)

    talimat_df = pd.DataFrame(
        talimat_rows, columns=["ekip_adi", "islem_tipi", "tarih", "saat", "talimat_adet"]
    )
    talimat_path = os.path.join(output_dir, "demo_talimat.csv")
    talimat_df.to_csv(talimat_path, index=False, encoding="utf-8")

    islem_df = pd.DataFrame(
        islem_rows, columns=["ekip_adi", "islem_tipi", "tarih", "saat", "islem_adet"]
    )
    islem_path = os.path.join(output_dir, "demo_islem.csv")
    islem_df.to_csv(islem_path, index=False, encoding="utf-8")

    for label, path, df, col in (
        ("Talimat", talimat_path, talimat_df, "talimat_adet"),
        ("İşlem", islem_path, islem_df, "islem_adet"),
    ):
        print(f"{label} demo veri oluşturuldu: {path}")
        print(f"  Toplam satır  : {len(df):,}")
        print(f"  Ekipler       : {sorted(df['ekip_adi'].unique())}")
        print(f"  İşlem tipleri : {sorted(df['islem_tipi'].unique())}")
        print(f"  Tarih araligi : {df['tarih'].min()} - {df['tarih'].max()}")
        print(f"  Toplam adet   : {df[col].sum():,}")


def main():
    p = argparse.ArgumentParser(description="Demo veri üretici (talimat + işlem, ekip kırılımlı)")
    p.add_argument("--output-dir", default="data/raw", help="Çıktı dizini")
    p.add_argument("--seed", type=int, default=42, help="Rastgele tohum")
    args = p.parse_args()
    generate(args.output_dir, seed=args.seed)


if __name__ == "__main__":
    main()
