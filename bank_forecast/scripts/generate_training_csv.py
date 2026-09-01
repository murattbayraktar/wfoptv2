"""Sentetik eğitim verisi (talimat) CSV üretici.

`src/data/loader.py`'nin beklediği ham şemayı üretir:
Reference, TaskType, SubTaskType, OrderDate, DispatcherMainPortfolio,
FirstForwardOmDate, OperatorMainPortfolio, EntryProcessCount

Kullanım:
    python bank_forecast/scripts/generate_training_csv.py \
        --start 2026-01-01 --end 2026-01-31 --count 2000

Çıktı, varsayılan olarak bank_forecast/data/synthetic/ altına yazılır (bu
dizin .gitignore'dadır); --output ile farklı bir yol verilebilir.
"""
import argparse
import random
from datetime import date, datetime, timedelta
from pathlib import Path

import holidays
import numpy as np
import pandas as pd

# Değer kümeleri: gerçek portföy/işlem kodlarınıza göre burayı genişletin.
TASK_TYPES = ["SOG"]
SUB_TASK_TYPES = ["EFT", "HVL", "VIR", "KRD", "YDT"]
DISPATCHER_TEAMS = ["PŞO", "MHS"]
OPERATOR_TEAMS = ["TLO", "KRD", "DIG", "YPO"]

WORK_START_HOUR = 8
WORK_END_HOUR = 18


def business_days(start: date, end: date, include_weekends: bool, include_holidays: bool) -> list[date]:
    tr_holidays = holidays.Turkey(years=range(start.year, end.year + 1))
    days = []
    d = start
    while d <= end:
        is_weekend = d.weekday() >= 5
        is_holiday = d in tr_holidays
        if (include_weekends or not is_weekend) and (include_holidays or not is_holiday):
            days.append(d)
        d += timedelta(days=1)
    return days


def random_business_time(d: date) -> datetime:
    total_seconds = (WORK_END_HOUR - WORK_START_HOUR) * 3600
    offset = random.randint(0, total_seconds - 1)
    return datetime(d.year, d.month, d.day, WORK_START_HOUR) + timedelta(seconds=offset)


def forward_time(order_dt: datetime) -> datetime:
    """Yönlendirme zamanı: aynı gün, order_dt'den sonra, 18:00'ı aşmayan
    sağa çarpık (çoğunlukla kısa) bir gecikmeyle."""
    day_end = order_dt.replace(hour=WORK_END_HOUR, minute=0, second=0, microsecond=0)
    max_delay = int((day_end - order_dt).total_seconds())
    if max_delay <= 60:
        return order_dt + timedelta(seconds=max(0, max_delay))
    delay = min(max_delay, int(np.random.exponential(scale=1800)) + 60)
    return order_dt + timedelta(seconds=delay)


def sample_entry_process_count() -> int:
    # Çoğu talimat 1-3 işlemden oluşur, kuyruk uzundur.
    return int(np.clip(np.random.geometric(p=0.4), 1, 50))


def generate(
    start: date,
    end: date,
    count: int,
    seed: int | None,
    include_weekends: bool,
    include_holidays: bool,
) -> pd.DataFrame:
    if seed is not None:
        random.seed(seed)
        np.random.seed(seed)

    days = business_days(start, end, include_weekends, include_holidays)
    if not days:
        raise ValueError(
            "Belirtilen aralıkta uygun gün bulunamadı "
            "(hafta sonu/tatil hariç tutuluyor olabilir; --include-weekends / --include-holidays deneyin)."
        )

    rows = []
    for i in range(count):
        d = random.choice(days)
        order_dt = random_business_time(d)
        rows.append(
            {
                "Reference": f"REF{i + 1:07d}",
                "TaskType": random.choice(TASK_TYPES),
                "SubTaskType": random.choice(SUB_TASK_TYPES),
                "OrderDate": order_dt.strftime("%Y-%m-%d %H:%M:%S"),
                "DispatcherMainPortfolio": random.choice(DISPATCHER_TEAMS),
                "FirstForwardOmDate": forward_time(order_dt).strftime("%Y-%m-%d %H:%M:%S"),
                "OperatorMainPortfolio": random.choice(OPERATOR_TEAMS),
                "EntryProcessCount": sample_entry_process_count(),
            }
        )
    return pd.DataFrame(rows)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Eğitim için sentetik talimat CSV'si üretir.")
    p.add_argument("--start", required=True, help="Başlangıç tarihi YYYY-MM-DD")
    p.add_argument("--end", required=True, help="Bitiş tarihi YYYY-MM-DD")
    p.add_argument("--count", type=int, required=True, help="Üretilecek talimat (satır) sayısı")
    p.add_argument(
        "--output",
        default=None,
        help="Çıktı CSV yolu (varsayılan: bank_forecast/data/synthetic/synthetic_<start>_<end>.csv)",
    )
    p.add_argument("--seed", type=int, default=None, help="Rastgelelik için sabit tohum (tekrarlanabilirlik)")
    p.add_argument("--include-weekends", action="store_true", help="Hafta sonlarını da tarih havuzuna dahil et")
    p.add_argument("--include-holidays", action="store_true", help="Resmi tatilleri de tarih havuzuna dahil et")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    start = datetime.strptime(args.start, "%Y-%m-%d").date()
    end = datetime.strptime(args.end, "%Y-%m-%d").date()
    if end < start:
        raise SystemExit("--end, --start tarihinden önce olamaz.")
    if args.count <= 0:
        raise SystemExit("--count pozitif bir tam sayı olmalı.")

    df = generate(start, end, args.count, args.seed, args.include_weekends, args.include_holidays)
    df = df.sort_values("OrderDate").reset_index(drop=True)

    default_dir = Path(__file__).resolve().parent.parent / "data" / "synthetic"
    output = Path(args.output) if args.output else default_dir / f"synthetic_{args.start}_{args.end}.csv"
    output.parent.mkdir(parents=True, exist_ok=True)
    # BOM'suz utf-8: loader.py ilk denemesini bununla yapıyor, BOM kolon adlarını bozar.
    df.to_csv(output, index=False, encoding="utf-8")
    print(f"{len(df)} satır üretildi -> {output}")


if __name__ == "__main__":
    main()
