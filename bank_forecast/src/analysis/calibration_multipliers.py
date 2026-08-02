"""İşlem tipi bazında kalibrasyon çarpanı önerisi — şeffaf "ratio-of-ratios"
yaklaşımı (kara kutu ML değil, kullanıcı gözle denetleyebilsin diye).

Her (işlem tipi, desen) çifti için: o desene uyan günlerin hacim-ağırlıklı
gerçekleşen/tahmin oranı, desene uymayan (ve daha yüksek öncelikli bir desene
de uymayan) "temel" günlerin aynı oranına bölünür. Bu, modelin genel
sapmasını (varsa) sadeleştirip yalnızca o desene özgü ek etkiyi izole eder —
model her yerde %5 az tahmin ediyorsa bu, hem pay hem paydada iptal olur.

Çarpanın **tahmin akışında nasıl uygulanacağının tek kaynağı** da burada
(`apply_multiplier`) — hem `pipeline.py`'daki gerçek uygulama hem
`routes_calibration.py`'daki önizleme aynı fonksiyonu kullanır, ikisi asla
birbirinden sapmaz.
"""
from src.analysis.calibration_analysis import flatten_comparison, with_pattern_context
from src.features.calibration_patterns import PATTERN_PRECEDENCE, resolve_pattern  # noqa: F401 (re-exported)

MIN_PATTERN_SAMPLES = 8
MIN_BASELINE_SAMPLES = 20
CLIP_MIN, CLIP_MAX = 0.5, 2.0


def _bias_ratio(df) -> float | None:
    sum_pred = df["predicted_count"].sum()
    if sum_pred <= 0:
        return None
    return float(df["actual_count"].sum() / sum_pred)


def compute_suggested_multipliers(
    daily_comparison: dict,
    half_days: set,
    patterns: list[str] = PATTERN_PRECEDENCE,
) -> dict:
    df = with_pattern_context(flatten_comparison(daily_comparison, has_hour=False), half_days)

    by_type: dict[str, dict] = {}
    if df.empty:
        return {"generated_at": _now(), "by_type": by_type}

    for tt, subset in df.groupby("transaction_type"):
        type_result: dict = {}
        for pattern in patterns:
            higher_precedence = patterns[: patterns.index(pattern)] if pattern in patterns else []

            pattern_days = subset[subset[f"is_{pattern}"] == 1]
            baseline_mask = subset[f"is_{pattern}"] == 0
            for higher in higher_precedence:
                baseline_mask &= subset[f"is_{higher}"] == 0
            baseline_days = subset[baseline_mask]

            n_pattern, n_baseline = len(pattern_days), len(baseline_days)

            if n_pattern < MIN_PATTERN_SAMPLES or n_baseline < MIN_BASELINE_SAMPLES:
                type_result[pattern] = {
                    "multiplier": 1.0, "n_pattern": n_pattern, "n_baseline": n_baseline,
                    "confidence": "low_sample",
                }
                continue

            bias_pattern = _bias_ratio(pattern_days)
            bias_baseline = _bias_ratio(baseline_days)
            if not bias_pattern or not bias_baseline:
                type_result[pattern] = {
                    "multiplier": 1.0, "n_pattern": n_pattern, "n_baseline": n_baseline,
                    "confidence": "low_sample",
                }
                continue

            raw_multiplier = bias_pattern / bias_baseline
            clipped = max(CLIP_MIN, min(CLIP_MAX, raw_multiplier))
            type_result[pattern] = {
                "multiplier": round(clipped, 2), "n_pattern": n_pattern, "n_baseline": n_baseline,
                "confidence": "ok",
            }

        by_type[tt] = type_result

    return {"generated_at": _now(), "by_type": by_type}


def apply_multiplier(base_value: float, transaction_type: str, pattern: str | None, calibration_cfg: dict) -> float:
    if pattern is None:
        return base_value
    multiplier = calibration_cfg.get("multipliers", {}).get(transaction_type, {}).get(pattern, 1.0)
    return base_value * multiplier


def _now() -> str:
    import pandas as pd
    return pd.Timestamp.now().isoformat()
