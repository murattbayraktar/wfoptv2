import pandas as pd
import chardet
import yaml
import os
from pathlib import Path


COLUMN_ALIASES = {
    "date": ["tarih", "DATE", "TARIH", "dt"],
    "hour": ["saat", "SAAT", "HOUR", "hr"],
    "transaction_type": ["islem_tipi", "TIP", "type", "TYPE"],
    "team": ["ekip_adi", "EKIP_ADI", "ekip", "team"],
    "amount": ["tutar", "TUTAR", "AMOUNT"],
}

# Metrik sütunları birer eş anlamlı değil — hangisi CSV'de mevcutsa satırın
# `metric_type`'ını belirler (bkz. `load_transactions`). Bu yüzden diğer
# `COLUMN_ALIASES` girdileri gibi tek bir kanonik ada collapse edilmezler.
METRIC_COLUMN_ALIASES = {
    "talimat": ["talimat_adet", "TALIMAT_ADET"],
    "islem": ["islem_adet", "ISLEM_ADET"],
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


def detect_metric_column(df: pd.DataFrame) -> tuple[str, str]:
    """CSV'de hangi metrik sütununun (talimat_adet | islem_adet) mevcut olduğunu bulur.

    Döner: (metric_type, matched_column_name). İkisi birden ya da hiçbiri
    yoksa `ValueError` fırlatır — iki format birbirini dışlar (bkz. planv1.txt).
    """
    lower_cols = {c.lower(): c for c in df.columns}
    found: list[tuple[str, str]] = []
    for metric_type, aliases in METRIC_COLUMN_ALIASES.items():
        for alias in aliases:
            if alias.lower() in lower_cols:
                found.append((metric_type, lower_cols[alias.lower()]))
                break

    if not found:
        raise ValueError(
            "Metrik sütunu bulunamadı: 'talimat_adet' veya 'islem_adet' sütunlarından "
            "biri zorunlu. Mevcut sütunlar: " + str(list(df.columns))
        )
    if len(found) > 1:
        cols = ", ".join(c for _, c in found)
        raise ValueError(
            f"Birden fazla metrik sütunu bulundu ({cols}) — bir CSV yalnızca "
            "'talimat_adet' ya da 'islem_adet' içerebilir, ikisini birden değil."
        )
    return found[0]


def parse_date_column(series: pd.Series) -> pd.Series:
    for fmt in DATE_FORMATS:
        try:
            parsed = pd.to_datetime(series, format=fmt)
            if parsed.notna().sum() > len(series) * 0.9:
                return parsed
        except Exception:
            pass
    return pd.to_datetime(series, infer_datetime_format=True)


def load_transactions(filepath: str) -> tuple[pd.DataFrame, str]:
    """CSV'yi okur ve standart şemaya dönüştürür.

    Döner: (df, metric_type). `metric_type` ("talimat" | "islem"), CSV'de hangi
    metrik sütununun bulunduğuna göre belirlenir (bkz. `detect_metric_column`);
    değeri `df["count"]` sütununa normalize edilir, böylece aggregator/pipeline
    katmanları metrik tipinden bağımsız çalışmaya devam eder.
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
    metric_type, metric_col = detect_metric_column(df)
    df = df.rename(columns={metric_col: "count"})

    required = ["date", "team", "transaction_type", "count"]
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
    df["team"] = df["team"].astype(str).str.strip()

    df = df.dropna(subset=["date", "transaction_type", "team"])
    df = df.sort_values("date").reset_index(drop=True)

    return df, metric_type
