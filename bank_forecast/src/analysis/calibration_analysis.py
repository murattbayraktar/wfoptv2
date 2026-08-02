"""Gerçekleşen-vs-tahmin karşılaştırmasından (bkz. `api/comparison.py`) sistematik
sapma ("hotspot") tespiti — hangi ekip/işlem tipi/gün(-saat) kombinasyonunda
model sistematik olarak az ya da çok tahmin ediyor, ve eğitim aşamasında ne
eklenebileceğine dair Türkçe, şablon tabanlı bir öneri.

`comparison.build_daily_comparison`/`build_hourly_comparison` çıktısı zaten
ekip×tip×tarih(/saat) join'ini yapmış durumda — burada join tekrar
yazılmaz, sadece düz bir tabloya çevrilip (`_flatten_comparison`) gün/desen
bazında gruplanır.
"""
import numpy as np
import pandas as pd

from src.features.calibration_patterns import PATTERN_PRECEDENCE, add_pattern_flags

WEEKDAY_LABELS_TR = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]

MIN_SAMPLES_DEFAULT = 4
ERROR_THRESHOLD_PCT_DEFAULT = 15.0


def flatten_comparison(comparison: dict, has_hour: bool) -> pd.DataFrame:
    """`{"by_team": {team: {type: [rows]}}}` -> düz (tidy) DataFrame.

    Zaten `comparison.py` tarafından join edilmiş satırları düzleştirir —
    yeni bir birleştirme (join) işlemi yapılmaz.
    """
    records: list[dict] = []
    for team, by_type in comparison.get("by_team", {}).items():
        for tt, rows in by_type.items():
            for row in rows:
                rec = {
                    "team": team,
                    "transaction_type": tt,
                    "date": row["date"],
                    "predicted_count": row["predicted_count"],
                    "actual_count": row["actual_count"],
                }
                if has_hour:
                    rec["hour"] = row["hour"]
                records.append(rec)

    cols = ["team", "transaction_type", "date", "predicted_count", "actual_count"]
    if has_hour:
        cols.insert(3, "hour")
    return pd.DataFrame(records, columns=cols)


def with_pattern_context(df: pd.DataFrame, half_days: set) -> pd.DataFrame:
    """Desen tespiti için gereken `day_of_week`/`week_of_month` sütunlarını ekler
    (tam `add_calendar_features` yerine, sadece bu iki basit türetilmiş sütun
    yeterli — büyük takvim özellik setini burada yeniden hesaplamaya gerek yok)
    ve `add_pattern_flags` ile desen bayraklarını (`is_friday` vb.) uygular.
    """
    if df.empty:
        return df
    df = df.copy()
    dates = pd.to_datetime(df["date"])
    df["day_of_week"] = dates.dt.dayofweek
    df["weekday"] = df["day_of_week"]
    df["week_of_month"] = ((dates.dt.day - 1) // 7 + 1).astype(int)
    df = add_pattern_flags(df, half_days)

    # Tekil, önceliğe göre çözümlenmiş desen: PATTERN_PRECEDENCE ters sırada
    # uygulanır ki en yüksek öncelikli (listede ilk) desen en son yazılıp kazansın.
    df["pattern"] = None
    for pattern in reversed(PATTERN_PRECEDENCE):
        df.loc[df[f"is_{pattern}"] == 1, "pattern"] = pattern
    return df


def _recommendation(row: dict, granularity: str) -> str:
    direction_tr = "az" if row["direction"] == "under_forecast" else "fazla"
    where = f"{row['team']} ekibinde {row['transaction_type']} işleminde"
    when = WEEKDAY_LABELS_TR[row["weekday"]]
    if granularity == "hourly" and row.get("hour") is not None:
        when = f"{when} saat {int(row['hour']):02d}:00 civarında"

    base = (
        f"{where} {when} ortalama %{abs(row['pct_error']):.0f} {direction_tr} tahmin oluşuyor "
        f"(n={row['n']} gözlem, ort. gerçekleşen {row['mean_actual']:.0f} vs tahmin {row['mean_predicted']:.0f})."
    )

    pattern = row.get("pattern")
    if pattern == "friday":
        return base + " Öneri: saat×haftanın-günü etkileşim özelliği eklenmesi veya bu işlem tipi için 'friday' kalibrasyon çarpanının kalibre edilmesi düşünülebilir."
    if pattern == "first_monday_of_month":
        return base + " Öneri: 'first_monday_of_month' kalibrasyon çarpanının gözden geçirilmesi ve ay-başı yoğunluğunu yakalayan bir özelliğin eğitime eklenmesi düşünülebilir."
    if pattern == "half_day":
        return base + " Öneri: yarım gün tarih listesinin güncel olduğundan emin olunması ve 'half_day' çarpanının kalibre edilmesi düşünülebilir."
    return base + " Öneri: bu desen bilinen bir takvim örüntüsüyle açıklanamıyor; lag/rolling pencerelerinin ve saat-bazlı özelliklerin gözden geçirilmesi önerilir."


def _score_groups(df: pd.DataFrame, group_cols: list[str], granularity: str, min_samples: int, error_threshold_pct: float) -> list[dict]:
    if df.empty:
        return []

    grouped = df.groupby(group_cols, dropna=False).agg(
        n=("actual_count", "size"),
        mean_actual=("actual_count", "mean"),
        mean_predicted=("predicted_count", "mean"),
    ).reset_index()

    grouped = grouped[grouped["n"] >= min_samples]
    grouped = grouped[grouped["mean_predicted"] > 0]
    if grouped.empty:
        return []

    grouped["pct_error"] = (grouped["mean_actual"] - grouped["mean_predicted"]) / grouped["mean_predicted"] * 100
    grouped["direction"] = np.where(grouped["mean_actual"] > grouped["mean_predicted"], "under_forecast", "over_forecast")
    grouped["impact_score"] = (grouped["mean_actual"] - grouped["mean_predicted"]).abs() * grouped["n"]

    hotspots = grouped[grouped["pct_error"].abs() >= error_threshold_pct]

    rows: list[dict] = []
    for _, r in hotspots.iterrows():
        row = {
            "team": r["team"],
            "transaction_type": r["transaction_type"],
            "granularity": granularity,
            "weekday": int(r["weekday"]),
            "hour": int(r["hour"]) if granularity == "hourly" else None,
            "pattern": r["pattern"] if pd.notna(r["pattern"]) else None,
            "n": int(r["n"]),
            "mean_actual": round(float(r["mean_actual"]), 1),
            "mean_predicted": round(float(r["mean_predicted"]), 1),
            "pct_error": round(float(r["pct_error"]), 1),
            "direction": r["direction"],
            "impact_score": round(float(r["impact_score"]), 1),
        }
        row["recommendation"] = _recommendation(row, granularity)
        rows.append(row)
    return rows


def compute_hotspots(
    daily_comparison: dict,
    hourly_comparison: dict,
    half_days: set,
    min_samples: int = MIN_SAMPLES_DEFAULT,
    error_threshold_pct: float = ERROR_THRESHOLD_PCT_DEFAULT,
) -> dict:
    df_daily = with_pattern_context(flatten_comparison(daily_comparison, has_hour=False), half_days)
    df_hourly = with_pattern_context(flatten_comparison(hourly_comparison, has_hour=True), half_days)

    daily_hotspots = _score_groups(
        df_daily, ["team", "transaction_type", "weekday", "pattern"], "daily", min_samples, error_threshold_pct,
    )
    hourly_hotspots = _score_groups(
        df_hourly, ["team", "transaction_type", "weekday", "hour", "pattern"], "hourly", min_samples, error_threshold_pct,
    )

    hotspots = sorted(daily_hotspots + hourly_hotspots, key=lambda r: r["impact_score"], reverse=True)
    groups_checked = (len(df_daily.groupby(["team", "transaction_type", "weekday", "pattern"], dropna=False)) if not df_daily.empty else 0) + (
        len(df_hourly.groupby(["team", "transaction_type", "weekday", "hour", "pattern"], dropna=False)) if not df_hourly.empty else 0
    )

    return {
        "generated_at": pd.Timestamp.now().isoformat(),
        "params": {"min_samples": min_samples, "error_threshold_pct": error_threshold_pct},
        "hotspots": hotspots,
        "summary": {"groups_checked": groups_checked, "hotspot_count": len(hotspots)},
    }
