"""Kalibrasyon desenleri (Cuma, ayın ilk pazartesi, yarım gün) için bayrak üretimi.

`calendar_features.add_calendar_features` zaten hesapladığı `day_of_week` /
`week_of_month` sütunlarını yeniden kullanır — burada sadece 3 yeni sütun
eklenir. `half_days` config-bağımlı olduğundan (kullanıcının elle bakımını
yaptığı bir tarih listesi) `calendar_features.py`'a değil, bu sibling modüle
konur; böylece takvim özellikleri eğitim/tahmin arasında config'ten bağımsız
kalır.

`PATTERN_PRECEDENCE`, bir günün birden fazla desene uyması durumunda hangi
desenin geçerli sayılacağını belirler (en spesifik önce): bir yarım gün zaten
hacim anomalisini açıklıyorsa üzerine ayrıca cuma çarpanı da binmemeli. Hem
çarpan uygulama adımı (`pipeline.py`) hem kalibrasyon motoru
(`analysis/calibration_multipliers.py`) bu tek listeyi kullanır.
"""
import pandas as pd

PATTERN_PRECEDENCE = ["half_day", "first_monday_of_month", "friday"]

PATTERN_LABELS_TR = {
    "friday": "Cuma",
    "first_monday_of_month": "Ayın İlk Pazartesi",
    "half_day": "Yarım Gün",
}


def add_pattern_flags(df: pd.DataFrame, half_days: set) -> pd.DataFrame:
    """`df`'nin `add_calendar_features` görmüş olması (day_of_week, week_of_month
    içermesi) ve bir `date` sütunu barındırması gerekir."""
    df = df.copy()
    date_str = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")

    df["is_friday"] = (df["day_of_week"] == 4).astype(int)
    df["is_first_monday_of_month"] = ((df["day_of_week"] == 0) & (df["week_of_month"] == 1)).astype(int)
    df["is_half_day"] = date_str.isin(half_days).astype(int)

    return df


def resolve_pattern(row: dict) -> str | None:
    """`{"is_half_day":1, "is_friday":1, ...}` -> `PATTERN_PRECEDENCE` sırasına göre ilk eşleşen desen."""
    for pattern in PATTERN_PRECEDENCE:
        if row.get(f"is_{pattern}"):
            return pattern
    return None
