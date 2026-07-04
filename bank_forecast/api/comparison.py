"""Tahmin sonuçlarını yüklenen geçmiş veriyle karşılaştırma yardımcıları.

Tahmin aralığı, elde mevcut olan geçmiş veriyle (daily_agg/hourly_agg)
örtüşüyorsa "gerçekleşen vs tahmin" grafiği için eşleştirilmiş satırlar üretir.
Yeni aggregation kodu yazılmaz — mevcut aggregate_daily/aggregate_hourly
çıktıları üzerinde basit filtre + sözlük eşlemesi yapılır.

Yapı `by_team[team][transaction_type]` şeklinde nested'dır (ekip boyutu
eklendiğinden — bkz. pipeline.py `forecast_pipeline`'ın `by_team` çıktısı).
"""
import numpy as np
import pandas as pd

from src.evaluation.metrics import mape as calc_mape


def _empty_result() -> dict:
    return {"has_overlap": False, "overlap_range": None, "by_team": {}}


def build_daily_comparison(daily_agg: pd.DataFrame | None, by_team: dict, start: str, end: str) -> dict:
    if daily_agg is None:
        return _empty_result()

    start_dt, end_dt = pd.Timestamp(start), pd.Timestamp(end)
    subset = daily_agg[daily_agg["date"].between(start_dt, end_dt)]
    if subset.empty:
        return _empty_result()

    overlap_start = str(subset["date"].min().date())
    overlap_end = str(subset["date"].max().date())

    result_by_team: dict[str, dict[str, list[dict]]] = {}
    for team, by_type in by_team.items():
        team_subset = subset[subset["team"] == team]
        if team_subset.empty:
            continue
        for tt, info in by_type.items():
            daily_list = info.get("daily")
            if not daily_list:
                continue

            actual_by_date = dict(
                zip(
                    team_subset.loc[team_subset["transaction_type"] == tt, "date"].dt.strftime("%Y-%m-%d"),
                    team_subset.loc[team_subset["transaction_type"] == tt, "count"].astype(int),
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
                result_by_team.setdefault(team, {})[tt] = rows

    return {
        "has_overlap": bool(result_by_team),
        "overlap_range": {"start": overlap_start, "end": overlap_end} if result_by_team else None,
        "by_team": result_by_team,
    }


def build_hourly_comparison(hourly_agg: pd.DataFrame | None, by_team: dict, start: str, end: str) -> dict:
    if hourly_agg is None:
        return _empty_result()

    start_dt, end_dt = pd.Timestamp(start), pd.Timestamp(end)
    subset = hourly_agg[hourly_agg["date"].between(start_dt, end_dt)]
    if subset.empty:
        return _empty_result()

    overlap_start = str(subset["date"].min().date())
    overlap_end = str(subset["date"].max().date())

    result_by_team: dict[str, dict[str, list[dict]]] = {}
    for team, by_type in by_team.items():
        team_subset = subset[subset["team"] == team]
        if team_subset.empty:
            continue
        for tt, info in by_type.items():
            hourly_by_date = info.get("hourly")
            if not hourly_by_date:
                continue

            tt_subset = team_subset[team_subset["transaction_type"] == tt]
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
                result_by_team.setdefault(team, {})[tt] = rows

    return {
        "has_overlap": bool(result_by_team),
        "overlap_range": {"start": overlap_start, "end": overlap_end} if result_by_team else None,
        "by_team": result_by_team,
    }


def compute_totals(by_team: dict) -> dict:
    total_predicted = 0.0
    per_team: dict[str, dict] = {}

    for team, by_type in by_team.items():
        team_total = 0.0
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
            team_total += tt_total
            per_type[tt] = {"model_used": model_used, "predicted_count": round(tt_total, 1)}

        total_predicted += team_total
        per_team[team] = {"predicted_count": round(team_total, 1), "by_type": per_type}

    return {
        "total_predicted": round(total_predicted, 1),
        "by_team": per_team,
    }


def compute_mape_summary(daily_comparison: dict) -> dict:
    """Karşılaştırma overlap'inden (gerçekleşen vs tahmin) ekip bazlı ve toplam
    MAPE hesaplar — `metrics.mape` kullanır (bkz. `src/evaluation/metrics.py`).

    Yalnızca günlük karşılaştırma kullanılır (saatlik veri çok daha gürültülü
    ve MAPE'yi anlamsızlaştırır); ekran tarafında "ekip bazlı ve toplam tahmin
    doğruluğu" ihtiyacı için günlük kırılım yeterli.
    """
    by_team = daily_comparison.get("by_team", {})
    if not by_team:
        return {"overall_mape": None, "by_team": {}}

    all_true: list = []
    all_pred: list = []
    result_by_team: dict = {}

    for team, by_type in by_team.items():
        team_true: list = []
        team_pred: list = []
        by_type_mape: dict = {}
        for tt, rows in by_type.items():
            y_true = [r["actual_count"] for r in rows]
            y_pred = [r["predicted_count"] for r in rows]
            m = calc_mape(np.array(y_true), np.array(y_pred)) if y_true else float("nan")
            by_type_mape[tt] = round(float(m), 2) if not np.isnan(m) else None
            team_true.extend(y_true)
            team_pred.extend(y_pred)

        team_mape = calc_mape(np.array(team_true), np.array(team_pred)) if team_true else float("nan")
        result_by_team[team] = {
            "mape": round(float(team_mape), 2) if not np.isnan(team_mape) else None,
            "by_type": by_type_mape,
        }
        all_true.extend(team_true)
        all_pred.extend(team_pred)

    overall = calc_mape(np.array(all_true), np.array(all_pred)) if all_true else float("nan")
    return {
        "overall_mape": round(float(overall), 2) if not np.isnan(overall) else None,
        "by_team": result_by_team,
    }
