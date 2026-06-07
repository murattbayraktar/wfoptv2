import pandas as pd
import numpy as np


def aggregate_daily(df: pd.DataFrame) -> pd.DataFrame:
    grouped = (
        df.groupby(["date", "transaction_type"])
        .agg(count=("count", "sum"), amount=("amount", "sum"))
        .reset_index()
    )

    date_range = pd.date_range(grouped["date"].min(), grouped["date"].max(), freq="D")
    types = grouped["transaction_type"].unique()
    full_idx = pd.MultiIndex.from_product([date_range, types], names=["date", "transaction_type"])
    full_df = pd.DataFrame(index=full_idx).reset_index()

    result = full_df.merge(grouped, on=["date", "transaction_type"], how="left")
    result["count"] = result["count"].fillna(0).astype(int)
    result["amount"] = result["amount"].fillna(0.0)
    result = result.sort_values(["transaction_type", "date"]).reset_index(drop=True)
    return result


def aggregate_hourly(df: pd.DataFrame, working_hours: tuple = (7, 18)) -> pd.DataFrame:
    if df["hour"].isna().all():
        raise ValueError("Saatlik aggregation için 'hour' sütunu gerekli ancak mevcut değil.")

    df = df.dropna(subset=["hour"]).copy()
    df["hour"] = df["hour"].astype(int)

    grouped = (
        df.groupby(["date", "hour", "transaction_type"])
        .agg(count=("count", "sum"), amount=("amount", "sum"))
        .reset_index()
    )

    date_range = pd.date_range(grouped["date"].min(), grouped["date"].max(), freq="D")
    hours = list(range(working_hours[0], working_hours[1] + 1))
    types = grouped["transaction_type"].unique()

    full_idx = pd.MultiIndex.from_product(
        [date_range, hours, types], names=["date", "hour", "transaction_type"]
    )
    full_df = pd.DataFrame(index=full_idx).reset_index()

    result = full_df.merge(grouped, on=["date", "hour", "transaction_type"], how="left")
    result["count"] = result["count"].fillna(0).astype(int)
    result["amount"] = result["amount"].fillna(0.0)
    result = result.sort_values(["transaction_type", "date", "hour"]).reset_index(drop=True)
    return result
