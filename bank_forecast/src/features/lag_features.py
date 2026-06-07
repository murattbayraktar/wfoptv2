import pandas as pd
import numpy as np

LAG_DAYS = [1, 2, 3, 5, 7, 14, 21, 28]
LAG_HOURS = [1, 2, 3, 24, 48, 168]
ROLLING_WINDOWS = [7, 14, 30]
ROLLING_WINDOWS_H = [24, 48, 168]


def add_lag_features(df: pd.DataFrame, target_col: str, freq: str) -> pd.DataFrame:
    df = df.copy()
    lags = LAG_DAYS if freq == "daily" else LAG_HOURS
    windows = ROLLING_WINDOWS if freq == "daily" else ROLLING_WINDOWS_H

    groups = df.groupby("transaction_type")[target_col]

    for lag in lags:
        col = f"lag_{lag}"
        df[col] = groups.shift(lag)

    for w in windows:
        col_mean = f"rolling_mean_{w}"
        col_std = f"rolling_std_{w}"
        col_max = f"rolling_max_{w}"
        df[col_mean] = groups.transform(
            lambda x: x.shift(1).rolling(w, min_periods=1).mean()
        )
        df[col_std] = groups.transform(
            lambda x: x.shift(1).rolling(w, min_periods=2).std()
        )
        df[col_max] = groups.transform(
            lambda x: x.shift(1).rolling(w, min_periods=1).max()
        )

    # Eksik lag değerlerini grup medyanı ile doldur
    lag_cols = [f"lag_{l}" for l in lags]
    for col in lag_cols:
        medians = df.groupby("transaction_type")[col].transform("median")
        df[col] = df[col].fillna(medians)

    roll_cols = [c for c in df.columns if c.startswith("rolling_")]
    for col in roll_cols:
        medians = df.groupby("transaction_type")[col].transform("median")
        df[col] = df[col].fillna(medians)

    return df
