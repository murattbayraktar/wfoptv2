import functools
import pandas as pd
import numpy as np
from datetime import timedelta


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


@functools.lru_cache(maxsize=16)
def _build_holiday_data(years_tuple: tuple) -> tuple:
    """(frozenset of holidays, tuple of sorted holidays) — lru_cache ile önbelleklenmiş."""
    hs: set = set()
    for year in years_tuple:
        for mmdd in TR_PUBLIC_HOLIDAYS:
            hs.add(pd.Timestamp(f"{year}-{mmdd}"))
        if year in RELIGIOUS_HOLIDAYS:
            for days in RELIGIOUS_HOLIDAYS[year].values():
                for d in days:
                    hs.add(pd.Timestamp(d))
    return frozenset(hs), tuple(sorted(hs))


def _build_holiday_set(years: list) -> set:
    """Geriye dönük uyumluluk için korunuyor."""
    holiday_set, _ = _build_holiday_data(tuple(sorted(set(years))))
    return set(holiday_set)


def add_calendar_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    dates = pd.to_datetime(df["date"])
    date_ts = dates.dt.normalize()  # pd.Timestamp(d.date()) eşdeğeri, saat kısmı sıfır

    years = list(dates.dt.year.unique())
    all_years = tuple(sorted(set(years + [y - 1 for y in years] + [y + 1 for y in years])))

    holiday_set, holiday_sorted_tuple = _build_holiday_data(all_years)
    holiday_sorted = list(holiday_sorted_tuple)

    religious_dates: set = set()
    for year in all_years:
        if year in RELIGIOUS_HOLIDAYS:
            for days in RELIGIOUS_HOLIDAYS[year].values():
                for d in days:
                    religious_dates.add(pd.Timestamp(d))

    # ── Vektörel isin kontrolleri ────────────────────────────────────────────
    df["is_public_holiday"] = date_ts.isin(holiday_set).astype(int)
    df["is_religious_holiday"] = date_ts.isin(religious_dates).astype(int)

    # is_eve_of_holiday / is_bridge_day: iş günü mantığı içerdiğinden
    # unique tarih başına bir kez hesapla, sonra map ile uygula
    unique_ts = list(pd.DatetimeIndex(date_ts.unique()))
    eve_map = {ts: _is_eve_of_holiday(ts, holiday_set) for ts in unique_ts}
    bridge_map = {ts: _is_bridge_day(ts, holiday_set) for ts in unique_ts}
    df["is_eve_of_holiday"] = date_ts.map(eve_map)
    df["is_bridge_day"] = date_ts.map(bridge_map)

    df["is_weekend"] = (dates.dt.dayofweek >= 5).astype(int)
    df["day_of_week"] = dates.dt.dayofweek
    df["day_of_month"] = dates.dt.day
    df["month"] = dates.dt.month
    df["quarter"] = dates.dt.quarter
    df["week_of_month"] = ((dates.dt.day - 1) // 7 + 1).astype(int)

    day = dates.dt.day
    df["month_quarter"] = np.where(day <= 10, 0, np.where(day <= 20, 1, 2))

    df["is_month_start"] = (dates.dt.day == 1).astype(int)
    df["is_month_end"] = dates.dt.is_month_end.astype(int)

    is_friday = dates.dt.dayofweek == 4
    next_week_month = (dates + pd.Timedelta(days=7)).dt.month
    df["is_last_friday"] = (is_friday & (next_week_month != dates.dt.month)).astype(int)

    df["days_to_month_end"] = dates.dt.days_in_month - dates.dt.day
    df["days_from_month_start"] = dates.dt.day - 1

    # ── Tatil mesafeleri: np.searchsorted ile O(log n) ───────────────────────
    d_ords = date_ts.values.astype("datetime64[D]").astype(np.int64)
    n_h = len(holiday_sorted)
    if n_h > 0:
        h_ords = pd.DatetimeIndex(holiday_sorted).normalize().values.astype("datetime64[D]").astype(np.int64)
        next_idx = np.searchsorted(h_ords, d_ords, side="right")

        has_next = next_idx < n_h
        safe_next = np.clip(next_idx, 0, n_h - 1)
        df["days_to_next_holiday"] = np.where(has_next, h_ords[safe_next] - d_ords, 999).astype(int)

        has_prev = next_idx > 0
        safe_prev = np.clip(next_idx - 1, 0, n_h - 1)
        df["days_from_last_holiday"] = np.where(has_prev, d_ords - h_ords[safe_prev], 999).astype(int)
    else:
        df["days_to_next_holiday"] = 999
        df["days_from_last_holiday"] = 999

    # post_holiday: unique date map
    ph1_map = {ts: _is_post_holiday(ts, holiday_set, offset=1) for ts in unique_ts}
    ph2_map = {ts: _is_post_holiday(ts, holiday_set, offset=2) for ts in unique_ts}
    df["post_holiday_day1"] = date_ts.map(ph1_map)
    df["post_holiday_day2"] = date_ts.map(ph2_map)

    return df


def _is_eve_of_holiday(d: pd.Timestamp, holiday_set: frozenset) -> int:
    next_day = d + timedelta(days=1)
    while next_day.dayofweek >= 5:
        next_day += timedelta(days=1)
    return int(pd.Timestamp(next_day.date()) in holiday_set)


def _is_bridge_day(d: pd.Timestamp, holiday_set: frozenset) -> int:
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


def _is_post_holiday(d: pd.Timestamp, holiday_set: frozenset, offset: int) -> int:
    steps = 0
    cur = d - timedelta(days=1)
    while steps < offset - 1:
        if cur.dayofweek < 5:
            steps += 1
        cur -= timedelta(days=1)
    return int(pd.Timestamp(cur.date()) in holiday_set or cur.dayofweek >= 5)
