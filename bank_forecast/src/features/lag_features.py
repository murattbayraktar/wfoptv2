import pandas as pd
import numpy as np

LAG_DAYS = [1, 2, 3, 5, 7, 14, 21, 28]
LAG_HOURS = [1, 2, 3, 24, 48, 168]
ROLLING_WINDOWS = [7, 14, 30]
ROLLING_WINDOWS_H = [24, 48, 168]


def add_lag_features(df: pd.DataFrame, target_col: str, freq: str) -> pd.DataFrame:
    lags = LAG_DAYS if freq == "daily" else LAG_HOURS
    windows = ROLLING_WINDOWS if freq == "daily" else ROLLING_WINDOWS_H
    sort_cols = ["date", "hour"] if (freq != "daily" and "hour" in df.columns) else ["date"]

    # Her işlem tipi için grubu numpy düzeyinde hesapla, sonra birleştir
    parts = []
    for _tt, grp in df.groupby("transaction_type", sort=False):
        grp = grp.sort_values(sort_cols).copy()
        s = grp[target_col].values
        n = len(s)

        for lag in lags:
            arr = np.full(n, np.nan)
            if lag < n:
                arr[lag:] = s[:-lag]
            grp[f"lag_{lag}"] = arr

        # shift(1) bir kez hesaplanır, tüm rolling window'lar bu seri üzerinden
        s_shifted = pd.Series(s).shift(1)
        for w in windows:
            grp[f"rolling_mean_{w}"] = s_shifted.rolling(w, min_periods=1).mean().values
            grp[f"rolling_std_{w}"]  = s_shifted.rolling(w, min_periods=2).std().values
            grp[f"rolling_max_{w}"]  = s_shifted.rolling(w, min_periods=1).max().values

        parts.append(grp)

    df = pd.concat(parts).loc[df.index]  # orijinal satır sıralamasını koru

    # Tüm özellik sütunları için tek groupby+transform ile median fill
    all_feat_cols = (
        [f"lag_{l}" for l in lags]
        + [f"rolling_{stat}_{w}" for w in windows for stat in ("mean", "std", "max")]
    )
    existing = [c for c in all_feat_cols if c in df.columns]
    if existing:
        medians = df.groupby("transaction_type")[existing].transform("median")
        df[existing] = df[existing].fillna(medians)

    return df
