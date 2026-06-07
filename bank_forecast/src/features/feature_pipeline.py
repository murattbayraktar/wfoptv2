import pandas as pd
import numpy as np
import category_encoders as ce
from src.features.calendar_features import add_calendar_features
from src.features.lag_features import add_lag_features
from src.features.seasonal_features import add_daily_fourier, add_hourly_fourier


CALENDAR_FEATURES = [
    "is_public_holiday", "is_religious_holiday", "is_eve_of_holiday",
    "is_bridge_day", "is_month_start", "is_month_end", "is_last_friday",
    "days_to_month_end", "days_from_month_start", "days_to_next_holiday",
    "days_from_last_holiday", "post_holiday_day1", "post_holiday_day2",
    "day_of_week", "day_of_month", "week_of_month", "month", "quarter",
    "is_weekend", "month_quarter",
]

CATEGORICAL_FEATURES = ["day_of_week", "month_quarter", "month", "quarter", "week_of_month"]


def build_features(
    df: pd.DataFrame,
    freq: str,
    target_col: str = "count",
    fit_encoder: bool = True,
    encoder=None,
    cfg: dict = None,
) -> tuple[pd.DataFrame, list[str], object]:
    """
    Returns (feature_df, feature_names, fitted_encoder)
    fit_encoder=False kullanırken encoder parametresi gerekli (tahmin modu).
    """
    if cfg is None:
        cfg = {}

    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])

    # Takvim özellikleri
    df = add_calendar_features(df)

    # Lag özellikleri (sızıntısız: her tip kendi grubunda)
    df = add_lag_features(df, target_col=target_col, freq=freq)

    # Fourier özellikleri
    if freq == "daily":
        weekly_terms = cfg.get("fourier_weekly_terms", 3)
        yearly_terms = cfg.get("fourier_yearly_terms", 5)
        df = add_daily_fourier(df, weekly_terms=weekly_terms, yearly_terms=yearly_terms)
    else:
        df = add_hourly_fourier(df)

    # Target encoding — işlem tipi
    if fit_encoder:
        encoder = ce.TargetEncoder(cols=["transaction_type"], smoothing=1.0)
        df["transaction_type_enc"] = encoder.fit_transform(df[["transaction_type"]], df[target_col])
    else:
        df["transaction_type_enc"] = encoder.transform(df[["transaction_type"]])

    # Feature listesi oluştur
    exclude = {"date", "hour", "transaction_type", target_col, "amount"}
    feature_cols = [c for c in df.columns if c not in exclude]

    # NaN temizle
    df[feature_cols] = df[feature_cols].fillna(0)

    return df, feature_cols, encoder


def get_feature_matrix(
    df: pd.DataFrame,
    feature_cols: list[str],
    target_col: str = "count",
) -> tuple[pd.DataFrame, pd.Series]:
    X = df[feature_cols].copy()
    y = df[target_col].copy()
    return X, y
