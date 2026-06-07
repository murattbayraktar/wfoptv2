import pandas as pd
import numpy as np


def add_fourier_features(df: pd.DataFrame, period: int, n_terms: int, t_col: str = "t") -> pd.DataFrame:
    df = df.copy()
    t = df[t_col].values
    for k in range(1, n_terms + 1):
        df[f"sin_{period}_{k}"] = np.sin(2 * np.pi * k * t / period)
        df[f"cos_{period}_{k}"] = np.cos(2 * np.pi * k * t / period)
    return df


def add_daily_fourier(df: pd.DataFrame, weekly_terms: int = 3, yearly_terms: int = 5) -> pd.DataFrame:
    df = df.copy()
    t0 = df["date"].min()
    df["t"] = (df["date"] - t0).dt.days

    df = add_fourier_features(df, period=7, n_terms=weekly_terms)
    df = add_fourier_features(df, period=365, n_terms=yearly_terms)

    df = df.drop(columns=["t"])
    return df


def add_hourly_fourier(df: pd.DataFrame, daily_terms: int = 4, weekly_terms: int = 3) -> pd.DataFrame:
    df = df.copy()
    t0 = df["date"].min()
    df["t"] = (df["date"] - t0).dt.days * 24 + df["hour"]

    df = add_fourier_features(df, period=24, n_terms=daily_terms)
    df = add_fourier_features(df, period=168, n_terms=weekly_terms)

    df = df.drop(columns=["t"])
    return df
