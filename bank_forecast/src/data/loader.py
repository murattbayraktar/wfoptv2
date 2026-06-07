import pandas as pd
import chardet
import yaml
import os
from pathlib import Path


COLUMN_ALIASES = {
    "date": ["tarih", "DATE", "TARIH", "dt"],
    "hour": ["saat", "SAAT", "HOUR", "hr"],
    "transaction_type": ["islem_tipi", "TIP", "type", "TYPE"],
    "count": ["adet", "ADET", "COUNT", "volume"],
    "amount": ["tutar", "TUTAR", "AMOUNT"],
}

DATE_FORMATS = ["%Y-%m-%d", "%d.%m.%Y", "%d/%m/%Y", "%Y%m%d"]


def detect_encoding(filepath: str) -> str:
    with open(filepath, "rb") as f:
        raw = f.read(50000)
    result = chardet.detect(raw)
    return result.get("encoding", "utf-8") or "utf-8"


def standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    rename_map = {}
    lower_cols = {c.lower(): c for c in df.columns}
    for standard, aliases in COLUMN_ALIASES.items():
        if standard in df.columns:
            continue
        for alias in [standard] + aliases:
            if alias.lower() in lower_cols:
                rename_map[lower_cols[alias.lower()]] = standard
                break
    return df.rename(columns=rename_map)


def parse_date_column(series: pd.Series) -> pd.Series:
    for fmt in DATE_FORMATS:
        try:
            parsed = pd.to_datetime(series, format=fmt)
            if parsed.notna().sum() > len(series) * 0.9:
                return parsed
        except Exception:
            pass
    return pd.to_datetime(series, infer_datetime_format=True)


def load_transactions(filepath: str) -> pd.DataFrame:
    enc = detect_encoding(filepath)
    try:
        df = pd.read_csv(filepath, encoding=enc)
    except UnicodeDecodeError:
        df = pd.read_csv(filepath, encoding="latin-1")

    df = standardize_columns(df)

    required = ["date", "transaction_type", "count"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Zorunlu sütunlar eksik: {missing}. Mevcut sütunlar: {list(df.columns)}")

    df["date"] = parse_date_column(df["date"])

    if "hour" not in df.columns:
        df["hour"] = None
    else:
        df["hour"] = pd.to_numeric(df["hour"], errors="coerce")

    df["count"] = pd.to_numeric(df["count"], errors="coerce").fillna(0).astype(int)

    if "amount" not in df.columns:
        df["amount"] = 0.0
    else:
        df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0.0)

    df["transaction_type"] = df["transaction_type"].astype(str).str.strip()

    df = df.dropna(subset=["date", "transaction_type"])
    df = df.sort_values("date").reset_index(drop=True)

    return df
