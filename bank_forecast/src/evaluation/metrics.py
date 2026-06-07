import numpy as np
import pandas as pd


def rmse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    return float(np.sqrt(np.mean((y_true - y_pred) ** 2)))


def mae(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    return float(np.mean(np.abs(y_true - y_pred)))


def mape(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    mask = y_true != 0
    if not mask.any():
        return float("nan")
    return float(np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100)


def smape(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    denom = (np.abs(y_true) + np.abs(y_pred)) / 2
    mask = denom != 0
    if not mask.any():
        return float("nan")
    return float(np.mean(np.abs(y_true[mask] - y_pred[mask]) / denom[mask]) * 100)


def coverage_95(y_true: np.ndarray, lower: np.ndarray, upper: np.ndarray) -> float:
    covered = ((y_true >= lower) & (y_true <= upper)).sum()
    return float(covered / len(y_true) * 100)


def full_report(y_true: np.ndarray, y_pred: np.ndarray, label: str = "") -> dict:
    r = {
        "label": label,
        "rmse": rmse(y_true, y_pred),
        "mae": mae(y_true, y_pred),
        "mape": mape(y_true, y_pred),
        "smape": smape(y_true, y_pred),
        "n": len(y_true),
    }
    r["interpretation"] = _interpret(r)
    return r


def _interpret(r: dict) -> str:
    mape_val = r.get("mape", float("nan"))
    if np.isnan(mape_val):
        return "MAPE hesaplanamadı (sıfır değerler mevcut)."
    if mape_val < 10:
        quality = "iyi"
    elif mape_val < 20:
        quality = "kabul edilebilir"
    else:
        quality = "zayıf"
    return f"Tahmin kalitesi {quality}: MAPE={mape_val:.1f}%"
