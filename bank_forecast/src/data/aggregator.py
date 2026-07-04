import pandas as pd
import numpy as np


def aggregate_daily(df: pd.DataFrame) -> pd.DataFrame:
    grouped = (
        df.groupby(["date", "team", "transaction_type"])
        .agg(count=("count", "sum"), amount=("amount", "sum"))
        .reset_index()
    )

    # Yalnızca gerçekte gözlemlenmiş (team, transaction_type) çiftleri için tarih
    # boşluklarını doldur — tüm ekip x tip kartezyen çarpımı yapılırsa çoğu ekip
    # her işlem tipini yapmadığından spurious tüm-sıfır satırlar üretilir ve
    # eğitim biriminin sayısı (bkz. pipeline.py) gereksiz yere şişer.
    pairs = grouped[["team", "transaction_type"]].drop_duplicates()
    date_range = pd.date_range(grouped["date"].min(), grouped["date"].max(), freq="D")

    full_parts = []
    for _, pair in pairs.iterrows():
        idx = pd.MultiIndex.from_product(
            [date_range, [pair["team"]], [pair["transaction_type"]]],
            names=["date", "team", "transaction_type"],
        )
        full_parts.append(pd.DataFrame(index=idx).reset_index())
    full_df = pd.concat(full_parts, ignore_index=True)

    result = full_df.merge(grouped, on=["date", "team", "transaction_type"], how="left")
    result["count"] = result["count"].fillna(0).astype(int)
    result["amount"] = result["amount"].fillna(0.0)
    result = result.sort_values(["team", "transaction_type", "date"]).reset_index(drop=True)
    return result


def aggregate_hourly(df: pd.DataFrame, working_hours: tuple = (7, 18)) -> pd.DataFrame:
    if df["hour"].isna().all():
        raise ValueError("Saatlik aggregation için 'hour' sütunu gerekli ancak mevcut değil.")

    df = df.dropna(subset=["hour"]).copy()
    df["hour"] = df["hour"].astype(int)

    grouped = (
        df.groupby(["date", "hour", "team", "transaction_type"])
        .agg(count=("count", "sum"), amount=("amount", "sum"))
        .reset_index()
    )

    pairs = grouped[["team", "transaction_type"]].drop_duplicates()
    date_range = pd.date_range(grouped["date"].min(), grouped["date"].max(), freq="D")
    hours = list(range(working_hours[0], working_hours[1] + 1))

    full_parts = []
    for _, pair in pairs.iterrows():
        idx = pd.MultiIndex.from_product(
            [date_range, hours, [pair["team"]], [pair["transaction_type"]]],
            names=["date", "hour", "team", "transaction_type"],
        )
        full_parts.append(pd.DataFrame(index=idx).reset_index())
    full_df = pd.concat(full_parts, ignore_index=True)

    result = full_df.merge(grouped, on=["date", "hour", "team", "transaction_type"], how="left")
    result["count"] = result["count"].fillna(0).astype(int)
    result["amount"] = result["amount"].fillna(0.0)
    result = result.sort_values(["team", "transaction_type", "date", "hour"]).reset_index(drop=True)
    return result
