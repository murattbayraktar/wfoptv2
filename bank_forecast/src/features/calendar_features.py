import pandas as pd
import numpy as np
from datetime import date, timedelta


TR_PUBLIC_HOLIDAYS = {
    "01-01": "Yılbaşı",
    "04-23": "Ulusal Egemenlik ve Çocuk Bayramı",
    "05-01": "Emek ve Dayanışma Günü",
    "05-19": "Atatürk'ü Anma",
    "07-15": "Demokrasi ve Millî Birlik Günü",
    "08-30": "Zafer Bayramı",
    "10-29": "Cumhuriyet Bayramı",
}

RELIGIOUS_HOLIDAYS = {
    2023: {
        "ramadan": ["2023-04-21", "2023-04-22", "2023-04-23"],
        "eid": ["2023-06-28", "2023-06-29", "2023-06-30", "2023-07-01"],
    },
    2024: {
        "ramadan": ["2024-04-10", "2024-04-11", "2024-04-12"],
        "eid": ["2024-06-16", "2024-06-17", "2024-06-18", "2024-06-19"],
    },
    2025: {
        "ramadan": ["2025-03-30", "2025-03-31", "2025-04-01"],
        "eid": ["2025-06-06", "2025-06-07", "2025-06-08", "2025-06-09"],
    },
    2026: {
        "ramadan": ["2026-03-20", "2026-03-21", "2026-03-22"],
        "eid": ["2026-05-27", "2026-05-28", "2026-05-29", "2026-05-30"],
    },
    2027: {
        "ramadan": ["2027-03-09", "2027-03-10", "2027-03-11"],
        "eid": ["2027-05-16", "2027-05-17", "2027-05-18", "2027-05-19"],
    },
}


def _build_holiday_set(years: list[int]) -> set:
    holidays = set()
    for year in years:
        for mmdd in TR_PUBLIC_HOLIDAYS:
            holidays.add(pd.Timestamp(f"{year}-{mmdd}"))
        if year in RELIGIOUS_HOLIDAYS:
            for days in RELIGIOUS_HOLIDAYS[year].values():
                for d in days:
                    holidays.add(pd.Timestamp(d))
    return holidays


def add_calendar_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    dates = pd.to_datetime(df["date"])

    years = list(dates.dt.year.unique())
    # Komşu yılları da ekle (köprü gün ve tatil mesafeleri için)
    all_years = sorted(set(years + [y - 1 for y in years] + [y + 1 for y in years]))
    holiday_set = _build_holiday_set(all_years)
    holiday_sorted = sorted(holiday_set)

    df["is_public_holiday"] = dates.apply(
        lambda d: int(pd.Timestamp(d.date()) in holiday_set)
    )

    religious_dates = set()
    for year in all_years:
        if year in RELIGIOUS_HOLIDAYS:
            for days in RELIGIOUS_HOLIDAYS[year].values():
                for d in days:
                    religious_dates.add(pd.Timestamp(d))

    df["is_religious_holiday"] = dates.apply(
        lambda d: int(pd.Timestamp(d.date()) in religious_dates)
    )

    # Arife: tatil öncesi son iş günü
    df["is_eve_of_holiday"] = dates.apply(
        lambda d: _is_eve_of_holiday(d, holiday_set)
    )

    # Köprü günü: tatil ile hafta sonu arasında kalan tek iş günü
    df["is_bridge_day"] = dates.apply(
        lambda d: _is_bridge_day(d, holiday_set)
    )

    df["is_weekend"] = (dates.dt.dayofweek >= 5).astype(int)
    df["day_of_week"] = dates.dt.dayofweek  # 0=Pazartesi, 6=Pazar
    df["day_of_month"] = dates.dt.day
    df["month"] = dates.dt.month
    df["quarter"] = dates.dt.quarter
    df["week_of_month"] = ((dates.dt.day - 1) // 7 + 1).astype(int)

    df["month_quarter"] = dates.dt.day.apply(
        lambda d: 0 if d <= 10 else (1 if d <= 20 else 2)
    )

    # Ay başı/sonu
    df["is_month_start"] = (dates.dt.day == 1).astype(int)
    df["is_month_end"] = dates.apply(
        lambda d: int(d.day == (d + pd.offsets.MonthEnd(0)).day)
    )

    df["is_last_friday"] = dates.apply(
        lambda d: int(d.dayofweek == 4 and (d + timedelta(days=7)).month != d.month)
    )

    # Ay sonuna ve başına uzaklık
    df["days_to_month_end"] = dates.apply(
        lambda d: (d + pd.offsets.MonthEnd(0)).day - d.day
    )
    df["days_from_month_start"] = dates.dt.day - 1

    # Tatile mesafe
    df["days_to_next_holiday"] = dates.apply(
        lambda d: _days_to_next_holiday(d, holiday_sorted)
    )
    df["days_from_last_holiday"] = dates.apply(
        lambda d: _days_from_last_holiday(d, holiday_sorted)
    )

    # Tatil sonrası yığılma
    df["post_holiday_day1"] = dates.apply(
        lambda d: _is_post_holiday(d, holiday_set, offset=1)
    )
    df["post_holiday_day2"] = dates.apply(
        lambda d: _is_post_holiday(d, holiday_set, offset=2)
    )

    return df


def _is_eve_of_holiday(d: pd.Timestamp, holiday_set: set) -> int:
    next_day = d + timedelta(days=1)
    while next_day.dayofweek >= 5:
        next_day += timedelta(days=1)
    return int(pd.Timestamp(next_day.date()) in holiday_set)


def _is_bridge_day(d: pd.Timestamp, holiday_set: set) -> int:
    if d.dayofweek >= 5:
        return 0
    if pd.Timestamp(d.date()) in holiday_set:
        return 0
    prev_day = d - timedelta(days=1)
    next_day = d + timedelta(days=1)
    prev_is_off = (prev_day.dayofweek >= 5) or (pd.Timestamp(prev_day.date()) in holiday_set)
    next_is_off = (next_day.dayofweek >= 5) or (pd.Timestamp(next_day.date()) in holiday_set)
    return int(prev_is_off and next_is_off)


def _days_to_next_holiday(d: pd.Timestamp, holiday_sorted: list) -> int:
    dt = pd.Timestamp(d.date())
    for h in holiday_sorted:
        if h > dt:
            return (h - dt).days
    return 999


def _days_from_last_holiday(d: pd.Timestamp, holiday_sorted: list) -> int:
    dt = pd.Timestamp(d.date())
    last = None
    for h in holiday_sorted:
        if h <= dt:
            last = h
        else:
            break
    if last is None:
        return 999
    return (dt - last).days


def _is_post_holiday(d: pd.Timestamp, holiday_set: set, offset: int) -> int:
    target = d - timedelta(days=offset)
    # Geriye doğru offset gün say, hafta sonlarını atla
    steps = 0
    cur = d - timedelta(days=1)
    while steps < offset - 1:
        if cur.dayofweek < 5:
            steps += 1
        cur -= timedelta(days=1)
    return int(pd.Timestamp(cur.date()) in holiday_set or cur.dayofweek >= 5)
