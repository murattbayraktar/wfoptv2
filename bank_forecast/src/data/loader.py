import pandas as pd
import chardet
import yaml
import os
from pathlib import Path

from src.data.reference_transform import build_dispatcher_operator_views


COLUMN_ALIASES = {
    "reference": ["Reference", "REFERENCE", "reference_no"],
    "task_type": ["TaskType", "TASK_TYPE", "task_type"],
    "sub_task_type": ["SubTaskType", "SUB_TASK_TYPE", "sub_task_type"],
    "order_date": ["OrderDate", "ORDER_DATE", "order_date"],
    "dispatcher_team": ["DispatcherMainPortfolio", "DISPATCHER_MAIN_PORTFOLIO"],
    "first_forward_date": ["FirstForwardOmDate", "FIRST_FORWARD_OM_DATE"],
    "operator_team": ["OperatorMainPortfolio", "OPERATOR_MAIN_PORTFOLIO"],
}

# EntryProcessCount opsiyoneldir — mevcutsa 'islem' metriği de bu CSV'den
# üretilir (bkz. `load_transactions`); mevcut değilse yalnızca 'talimat'
# metriği (referans/satır sayısı) üretilir.
ENTRY_PROCESS_COUNT_ALIASES = ["EntryProcessCount", "ENTRY_PROCESS_COUNT", "entry_process_count"]

DATE_FORMATS = [
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d %H:%M",
    "%d.%m.%Y %H:%M:%S",
    "%d.%m.%Y %H:%M",
    "%d/%m/%Y %H:%M:%S",
    "%d/%m/%Y %H:%M",
    "%Y-%m-%d",
    "%d.%m.%Y",
    "%d/%m/%Y",
    "%Y%m%d",
]


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

    for alias in ["entry_process_count"] + ENTRY_PROCESS_COUNT_ALIASES:
        if alias.lower() in lower_cols and "entry_process_count" not in df.columns:
            rename_map[lower_cols[alias.lower()]] = "entry_process_count"
            break

    return df.rename(columns=rename_map)


def parse_date_column(series: pd.Series) -> pd.Series:
    for fmt in DATE_FORMATS:
        try:
            parsed = pd.to_datetime(series, format=fmt)
            non_null = series.notna().sum()
            if non_null == 0 or parsed.notna().sum() > non_null * 0.9:
                return parsed
        except Exception:
            pass
    return pd.to_datetime(series, infer_datetime_format=True)


def load_transactions(filepath: str) -> dict[str, pd.DataFrame]:
    """CSV'yi okur ve standart şemaya dönüştürür.

    Girdi: her satırı bir talimatı (referansı) temsil eden ham veri
    (Reference, TaskType, SubTaskType, OrderDate, DispatcherMainPortfolio,
    FirstForwardOmDate, OperatorMainPortfolio, [EntryProcessCount]).

    Döner: `{"talimat": df}` ya da (CSV'de `EntryProcessCount` kolonu varsa)
    `{"talimat": df, "islem": df}`. Her df, aggregator'ın beklediği
    `date, hour, team, transaction_type, count, amount` şemasındadır.

    Karşılayıcı (dispatcher) ve işlemci (operator) ekip görünümleri ayrımı
    için bkz. `src.data.reference_transform.build_dispatcher_operator_views`.
    """
    df = None
    for enc in ["utf-8", detect_encoding(filepath), "latin-1"]:
        try:
            df = pd.read_csv(filepath, encoding=enc)
            break
        except (UnicodeDecodeError, LookupError):
            continue
    if df is None:
        raise ValueError("Dosya okunamadı: desteklenen bir karakter kodlaması bulunamadı.")

    df = standardize_columns(df)

    required = [
        "reference",
        "task_type",
        "sub_task_type",
        "order_date",
        "dispatcher_team",
        "first_forward_date",
        "operator_team",
    ]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Zorunlu sütunlar eksik: {missing}. Mevcut sütunlar: {list(df.columns)}")

    df["order_date"] = parse_date_column(df["order_date"])
    df["first_forward_date"] = parse_date_column(df["first_forward_date"])

    df["task_type"] = df["task_type"].astype(str).str.strip()
    df["sub_task_type"] = df["sub_task_type"].astype(str).str.strip()
    df["transaction_type"] = df["task_type"] + "-" + df["sub_task_type"]

    df["dispatcher_team"] = df["dispatcher_team"].astype(str).str.strip()
    df["operator_team"] = df["operator_team"].astype(str).str.strip()

    has_entry_process_count = "entry_process_count" in df.columns
    if has_entry_process_count:
        df["entry_process_count"] = pd.to_numeric(df["entry_process_count"], errors="coerce")

    df = df.dropna(subset=["order_date", "transaction_type", "dispatcher_team"])

    combined = build_dispatcher_operator_views(df)
    combined["date"] = combined["event_time"].dt.normalize()
    combined["hour"] = combined["event_time"].dt.hour

    results: dict[str, pd.DataFrame] = {}

    talimat_df = combined.copy()
    talimat_df["count"] = 1
    talimat_df["amount"] = 0.0
    talimat_df = talimat_df[["date", "hour", "team", "transaction_type", "count", "amount"]]
    talimat_df = talimat_df.sort_values("date").reset_index(drop=True)
    results["talimat"] = talimat_df

    if has_entry_process_count:
        islem_df = combined.dropna(subset=["entry_process_count"]).copy()
        islem_df["count"] = islem_df["entry_process_count"].astype(int)
        islem_df["amount"] = 0.0
        islem_df = islem_df[["date", "hour", "team", "transaction_type", "count", "amount"]]
        islem_df = islem_df.sort_values("date").reset_index(drop=True)
        results["islem"] = islem_df

    return results
