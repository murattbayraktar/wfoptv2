"""Tahmin sonuçlarını yüklenen geçmiş veriyle karşılaştırma yardımcıları.

Tahmin aralığı, elde mevcut olan geçmiş veriyle (daily_agg/hourly_agg)
örtüşüyorsa "gerçekleşen vs tahmin" grafiği için eşleştirilmiş satırlar üretir.
Yeni aggregation kodu yazılmaz — mevcut aggregate_daily/aggregate_hourly
çıktıları üzerinde basit filtre + sözlük eşlemesi yapılır.
"""
import pandas as pd


def _empty_result() -> dict:
    return {"has_overlap": False, "overlap_range": None, "by_type": {}}


def build_daily_comparison(daily_agg: pd.DataFrame | None, by_type: dict, start: str, end: str) -> dict:
    if daily_agg is None:
        return _empty_result()

    start_dt, end_dt = pd.Timestamp(start), pd.Timestamp(end)
    subset = daily_agg[daily_agg["date"].between(start_dt, end_dt)]
    if subset.empty:
        return _empty_result()

    overlap_start = str(subset["date"].min().date())
    overlap_end = str(subset["date"].max().date())

    result_by_type: dict[str, list[dict]] = {}
    for tt, info in by_type.items():
        daily_list = info.get("daily")
        if not daily_list:
            continue

        actual_by_date = dict(
            zip(
                subset.loc[subset["transaction_type"] == tt, "date"].dt.strftime("%Y-%m-%d"),
                subset.loc[subset["transaction_type"] == tt, "count"].astype(int),
            )
        )
        rows = [
            {
                "date": entry["date"],
                "predicted_count": entry["predicted_count"],
                "actual_count": actual_by_date[entry["date"]],
            }
            for entry in daily_list
            if entry["date"] in actual_by_date
        ]
        if rows:
            result_by_type[tt] = rows

    return {
        "has_overlap": bool(result_by_type),
        "overlap_range": {"start": overlap_start, "end": overlap_end} if result_by_type else None,
        "by_type": result_by_type,
    }


def build_hourly_comparison(hourly_agg: pd.DataFrame | None, by_type: dict, start: str, end: str) -> dict:
    if hourly_agg is None:
        return _empty_result()

    start_dt, end_dt = pd.Timestamp(start), pd.Timestamp(end)
    subset = hourly_agg[hourly_agg["date"].between(start_dt, end_dt)]
    if subset.empty:
        return _empty_result()

    overlap_start = str(subset["date"].min().date())
    overlap_end = str(subset["date"].max().date())

    result_by_type: dict[str, list[dict]] = {}
    for tt, info in by_type.items():
        hourly_by_date = info.get("hourly")
        if not hourly_by_date:
            continue

        tt_subset = subset[subset["transaction_type"] == tt]
        actual_by_dt = {
            (row["date"].strftime("%Y-%m-%d"), int(row["hour"])): int(row["count"])
            for _, row in tt_subset.iterrows()
        }

        rows = []
        for date_str, hours in hourly_by_date.items():
            for entry in hours:
                key = (date_str, entry["hour"])
                if key in actual_by_dt:
                    rows.append({
                        "date": date_str,
                        "hour": entry["hour"],
                        "predicted_count": entry["count"],
                        "actual_count": actual_by_dt[key],
                    })
        if rows:
            result_by_type[tt] = rows

    return {
        "has_overlap": bool(result_by_type),
        "overlap_range": {"start": overlap_start, "end": overlap_end} if result_by_type else None,
        "by_type": result_by_type,
    }


def compute_totals(by_type: dict) -> dict:
    total_predicted = 0.0
    per_type: dict[str, dict] = {}

    for tt, info in by_type.items():
        model_used = info.get("model_used")
        daily_list = info.get("daily")
        if daily_list:
            tt_total = sum(entry["predicted_count"] for entry in daily_list)
        else:
            tt_total = sum(
                entry["count"]
                for hours in (info.get("hourly") or {}).values()
                for entry in hours
            )
        total_predicted += tt_total
        per_type[tt] = {"model_used": model_used, "predicted_count": round(tt_total, 1)}

    return {
        "total_predicted": round(total_predicted, 1),
        "by_type": per_type,
    }
