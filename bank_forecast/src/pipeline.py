"""Ana orkestratör: train | forecast | evaluate akışlarını yönetir.

Ekip (team) boyutu eklendiğinde model registry `models/saved/model_registry_<metric_type>.json`
olarak metrik başına ayrılır ve içeriği `models[team][transaction_type][freq]` şeklinde
nested bir sözlüktür (eskiden `f"{type}_{freq}"` düz string anahtardı — ekip/tip adları
boşluk içerebildiğinden ve artık 3 boyut olduğundan string ayrıştırma kırılgan hale gelirdi).
"""
import json
import os
import re
import shutil
import tempfile
import concurrent.futures
import multiprocessing
from datetime import datetime
import pandas as pd
import numpy as np
import yaml
from rich.console import Console

from src.data.loader import load_transactions
from src.data.validator import validate, print_validation_report
from src.data.aggregator import aggregate_daily, aggregate_hourly
from src.features.feature_pipeline import build_features, get_feature_matrix
from src.models.model_selector import ModelSelector
from src.evaluation.metrics import full_report, rmse, mae
from src.reporting.plot_builder import plot_forecast, plot_hourly_heatmap, plot_model_comparison, plot_feature_importance
from src.reporting.html_reporter import generate_training_report, generate_forecast_report

console = Console()

REGISTRY_DIR = "models/saved"

# Geriye dönük referans için (CLI script varsayılanları) — artık tek bir registry
# yerine metrik başına registry kullanılıyor, bkz. `registry_filename`.
REGISTRY_FILE = os.path.join(REGISTRY_DIR, "model_registry_talimat.json")


def registry_filename(metric_type: str, registry_dir: str = REGISTRY_DIR) -> str:
    return os.path.join(registry_dir, f"model_registry_{metric_type}.json")


def _safe_key(value: str) -> str:
    """Dosya adı olarak kullanılabilecek şekilde ekip/tip adını temizler."""
    return re.sub(r"[\\/]+", "-", value).strip()


def load_config(config_path: str = "config/settings.yaml") -> dict:
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    return {}


def _save_registry(registry: dict, path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(registry, f, ensure_ascii=False, indent=2, default=str)


def _load_registry(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _flatten_registry_models(models: dict) -> dict:
    """`models[team][type][freq] = entry` -> `{"team / type (freq)": entry}` —
    yalnızca `html_reporter.generate_training_report`'ın beklediği düz yapı için."""
    flat: dict = {}
    for team, by_type in models.items():
        for tt, by_freq in by_type.items():
            for f_freq, entry in by_freq.items():
                flat[f"{team} / {tt} ({f_freq})"] = entry
    return flat


def _history_lookup(hist_subset: "pd.DataFrame | None", freq: str):
    """Yüklenen verinin agregasyonundan (varsa) kronolojik (anahtar -> değer) eşlemesi çıkarır.

    Anahtar: günlük için `Timestamp(date)`, saatlik için `(Timestamp(date), hour)` —
    eğitimdeki `aggregate_daily/aggregate_hourly` çıktısının sıralamasıyla birebir
    aynıdır, böylece lag/rolling hesaplamaları eğitimdekiyle tutarlı kalır.

    Döner: (sıralı anahtar listesi, anahtar->count sözlüğü, tip bazlı medyan).
    """
    if hist_subset is None or hist_subset.empty:
        return [], {}, 0.0

    cols = ["date", "hour"] if freq == "hourly" else ["date"]
    sub = hist_subset.sort_values(cols)
    if freq == "hourly":
        keys = list(zip(sub["date"], sub["hour"].astype(int)))
    else:
        keys = list(sub["date"])
    counts = sub["count"].astype(float).tolist()
    return keys, dict(zip(keys, counts)), float(sub["count"].median())


def _lag_or_rolling_value(col: str, series: list, pos: int, fallback: float) -> float:
    """`series[:pos]` (gerçek geçmiş + o ana kadar üretilen tahminler) üzerinden
    `lag_N` veya `rolling_{istatistik}_{pencere}` özelliğinin değerini hesaplar.

    Eğitimdeki `groups.shift(lag)` / `shift(1).rolling(window)` ile aynı sırayı
    izler. Yetersiz geçmişte (ör. dizinin başı) eğitimdeki "tip medyanı ile
    doldur" yaklaşımına paralel olarak `fallback` kullanılır — sabit sıfır,
    modelin hiç görmediği bir bölgeye ekstrapolasyona zorlardı.
    """
    if col.startswith("lag_"):
        n = int(col.split("_", 1)[1])
        idx = pos - n
        if idx < 0 or series[idx] is None:
            return fallback
        return series[idx]

    _, stat, w_str = col.split("_")
    w = int(w_str)
    window = [v for v in series[max(0, pos - w):pos] if v is not None]
    if stat == "mean":
        return float(np.mean(window)) if window else fallback
    if stat == "max":
        return float(np.max(window)) if window else fallback
    if stat == "std":
        return float(np.std(window, ddof=1)) if len(window) >= 2 else 0.0
    return fallback


def _recursive_predict(
    model,
    grid_df: pd.DataFrame,
    feat_cols: list[str],
    lag_cols: list[str],
    freq: str,
    hist_keys: list,
    hist_count_map: dict,
    fallback: float,
) -> np.ndarray:
    """`grid_df` (kronolojik sırada, lag/rolling sütunları henüz boş) üzerinde
    satır satır (recursive) tahmin üretir.

    Önceki sabit-sıfır yaklaşımı, model en önemli özelliklerinden biri olan
    `lag_*`/`rolling_*` değerlerini eğitimde hiç karşılaşmadığı bir değere
    (0) sabitleyip modeli dağılım dışı bir bölgeye itiyordu — bu da özellikle
    saatlik tahminlerde büyük sapmalara yol açıyordu (saatlik modelde "saat"
    diye ayrı bir özellik yok, gün-içi örüntü büyük ölçüde lag/rolling ve
    Fourier terimlerinden geliyor).

    Burada her satır için lag/rolling değerleri, o ana kadarki **gerçek
    geçmiş veriden** (varsa) ve **daha önce bu döngüde üretilen tahminlerden**
    hesaplanır; böylece model eğitimde gördüğü dağılıma yakın bir bağlamla
    çalışır. `grid_df` lag/rolling sütunları doldurularak yerinde güncellenir
    (sonradan toplu quantile tahmini için kullanılabilsin diye).
    """
    if freq == "hourly":
        grid_keys = list(zip(grid_df["date"], grid_df["hour"].astype(int)))
    else:
        grid_keys = list(grid_df["date"])

    first_key = grid_keys[0]
    lookback_keys = [k for k in hist_keys if k < first_key]

    series: list = (
        [hist_count_map[k] for k in lookback_keys]
        + [hist_count_map.get(k) for k in grid_keys]
    )
    offset = len(lookback_keys)

    base_rows = grid_df[feat_cols].to_dict("records")
    preds = np.zeros(len(grid_keys), dtype=float)
    filled_lags: dict[str, list] = {col: [] for col in lag_cols}

    # Döngü öncesi tek template DataFrame — her iterasyonda iat ile güncellenir,
    # yeni pd.DataFrame() constructor çağrısının overhead'i ortadan kalkar.
    template_df = pd.DataFrame([base_rows[0]], columns=feat_cols)
    feat_idx = {col: i for i, col in enumerate(feat_cols)}

    for i, _key in enumerate(grid_keys):
        pos = offset + i
        row = base_rows[i]
        for col in lag_cols:
            val = _lag_or_rolling_value(col, series, pos, fallback)
            row[col] = val
            filled_lags[col].append(val)

        for col, val in row.items():
            template_df.iat[0, feat_idx[col]] = val
        pred = float(model.predict(template_df)[0])
        preds[i] = pred

        # Gerçek geçmişte yoksa (gelecekteki nokta), sonraki satırların lag
        # referansı için bu tahmini "bilinen" değer olarak zincire ekle.
        if series[pos] is None:
            series[pos] = max(pred, 0.0)

    for col in lag_cols:
        grid_df[col] = filled_lags[col]

    return preds


def _train_unit(args: tuple) -> dict:
    """ProcessPoolExecutor worker — modül seviyesinde tanımlı (pickle uyumlu).

    Her (ekip, işlem_tipi, freq) birimi için: feature engineering, model seçimi,
    final fit ve kaydetme işlemlerini bağımsız bir process'te yürütür.
    progress_callback ana thread'e geri dönüş sonucuyla iletilir.
    """
    (team, transaction_type, freq, agg_pkl_path, features_cfg, models_cfg,
     candidate_models, multi_save, cv_folds, metric, min_days, output_dir, report_flag) = args

    # Birim başına zaten ayrı bir process ayrılmış durumda (bkz. ProcessPoolExecutor
    # çağrısı); modellerin kendi içindeki n_jobs=-1 paralelliği bununla çakışıp tüm
    # çekirdekleri N kat aşırı abone ederek (oversubscription) eğitimi durmuş gibi
    # yavaşlatıyordu. Process-içi paralelliği kapatıp tüm çekirdekleri unit-düzeyindeki
    # paralellikte kullanıyoruz.
    models_cfg = {**models_cfg, "n_jobs": 1}

    label = f"{team} / {transaction_type}"
    flat_key = f"{_safe_key(team)}__{_safe_key(transaction_type)}__{freq}"
    try:
        import joblib as _joblib
        import traceback as _tb

        agg_df = pd.read_pickle(agg_pkl_path)
        subset = agg_df[
            (agg_df["team"] == team) & (agg_df["transaction_type"] == transaction_type)
        ].copy()

        feat_df, feat_cols, encoder = build_features(
            subset, freq=freq, target_col="count",
            fit_encoder=True, cfg=features_cfg,
        )
        X, y = get_feature_matrix(feat_df, feat_cols)

        n = len(X)
        split_idx = max(int(n * 0.8), n - 60)
        X_tr, y_tr = X.iloc[:split_idx], y.iloc[:split_idx]

        selector = ModelSelector()
        sel_result = selector.select_best(
            transaction_type=label,
            freq=freq,
            X_train=X_tr,
            y_train=y_tr,
            cv_folds=cv_folds,
            metric=metric,
            candidates=candidate_models,
            cfg=models_cfg,
            min_training_days=min_days,
            progress_callback=None,
        )

        os.makedirs(output_dir, exist_ok=True)
        encoder_path = os.path.join(output_dir, f"{flat_key}_encoder.pkl")
        best_name = sel_result["best_model"]
        best_model_path = os.path.join(output_dir, f"{flat_key}_best.pkl")
        available_models: dict = {}

        if multi_save:
            trained = selector.train_selected(
                label, freq, X, y, candidate_models, models_cfg,
                search_artifacts=sel_result.get("_search_artifacts", {}),
            )
            # best_name eğitilememiş olabilir — önce diğerlerini kaydet,
            # sonra gerçek best'i belirle
            effective_best = best_name if best_name in trained else min(
                trained, key=lambda n: sel_result["all_scores"].get(n, float("inf"))
            )
            for name, model in trained.items():
                m_path = best_model_path if name == effective_best else os.path.join(output_dir, f"{flat_key}_{name}.pkl")
                model.save(m_path)
                available_models[name] = {
                    "model_path": m_path,
                    "encoder_path": encoder_path,
                    "cv_rmse": sel_result["all_scores"].get(name),
                    "feature_names": feat_cols,
                }
            best_name = effective_best
            final_model = trained[best_name]
            model_path = best_model_path
        else:
            final_model = selector.train_best(sel_result, label, freq, X, y, models_cfg)
            model_path = best_model_path
            final_model.save(model_path)
            available_models[best_name] = {
                "model_path": model_path,
                "encoder_path": encoder_path,
                "cv_rmse": sel_result["all_scores"].get(best_name),
                "feature_names": feat_cols,
            }

        fi_df = final_model.get_feature_importance()
        top5 = fi_df["feature"].head(5).tolist() if not fi_df.empty else []

        _joblib.dump(encoder, encoder_path)

        if not fi_df.empty and report_flag:
            fi_path = f"outputs/plots/fi_{flat_key}.html"
            plot_feature_importance(fi_df, f"Feature Önemi: {label} ({freq})", fi_path)

        return {
            "team": team,
            "transaction_type": transaction_type,
            "freq": freq,
            "success": True,
            "registry_entry": {
                "best_model": best_name,
                "cv_rmse": sel_result["best_score"],
                "cv_mae": sel_result["all_scores"].get(best_name, 0),
                "all_scores": sel_result["all_scores"],
                "selection_reason": sel_result["selection_reason"],
                "feature_importance_top5": top5,
                "model_path": model_path,
                "encoder_path": encoder_path,
                "feature_names": feat_cols,
                "available_models": available_models,
            },
            "all_scores": sel_result["all_scores"],
        }
    except Exception as e:
        import traceback as _tb
        return {
            "team": team,
            "transaction_type": transaction_type,
            "freq": freq,
            "success": False,
            "error": str(e),
            "traceback": _tb.format_exc(),
        }


def train_pipeline(
    input_path: str,
    metric_type: str,
    freq: str = "daily",
    teams: list[str] = None,
    types: list[str] = None,
    models: list[str] = None,
    cv_folds: int = 5,
    metric: str = "rmse",
    output_dir: str = None,
    report: bool = True,
    config_path: str = "config/settings.yaml",
    progress_callback=None,
    holdout_days: int = 0,
) -> dict:
    cfg = load_config(config_path)
    models_cfg = cfg.get("models", {})
    features_cfg = cfg.get("features", {})
    data_cfg = cfg.get("data", {})
    min_days = data_cfg.get("min_training_days", 60)
    working_hours = tuple(data_cfg.get("working_hours", [7, 18]))

    console.print("[bold green]Veri yükleniyor...[/bold green]")
    results = load_transactions(input_path)
    df = results.get(metric_type)
    if df is None:
        raise ValueError(
            f"CSV'de '{metric_type}' metriği için veri yok "
            "(islem için EntryProcessCount kolonu gerekli)."
        )
    val_report = validate(df, min_days)
    print_validation_report(val_report)

    if val_report["errors"]:
        raise ValueError("Veri doğrulama hatası: " + "; ".join(val_report["errors"]))

    available_teams = val_report["teams"]
    available_types = val_report["transaction_types"]
    teams = [t for t in teams if t in available_teams] if teams else available_teams
    types = [t for t in types if t in available_types] if types else available_types

    if output_dir is None:
        output_dir = os.path.join(REGISTRY_DIR, metric_type)
    registry_path = registry_filename(metric_type)

    if models and models != ["auto"]:
        candidate_models = models
    else:
        candidate_models = None  # ModelSelector tüm adayları dener

    # Birden fazla model açıkça seçildiyse, hepsi tam veri ile eğitilip ayrı
    # dosyalar olarak kaydedilir (tahmin sırasında karşılaştırılabilmeleri için).
    multi_save = bool(candidate_models and len(candidate_models) > 1)

    freqs = ["daily", "hourly"] if freq == "both" else [freq]

    # Holdout seti: son N günü eğitime dahil etme
    holdout_period = None
    if holdout_days > 0:
        max_date = df["date"].max()
        holdout_start = max_date - pd.Timedelta(days=holdout_days - 1)
        holdout_period = {
            "start": str(holdout_start.date()),
            "end": str(max_date.date()),
        }
        if progress_callback:
            progress_callback({
                "kind": "holdout_set",
                "holdout_start": str(holdout_start.date()),
                "holdout_end": str(max_date.date()),
                "holdout_days": holdout_days,
            })
        df = df[df["date"] < holdout_start].copy()

    registry = {
        "metric_type": metric_type,
        "trained_at": datetime.now().isoformat(),
        "data_range": {
            "start": str(df["date"].min().date()),
            "end": str(df["date"].max().date()),
        },
        "holdout_period": holdout_period,
        "teams": teams,
        "transaction_types": types,
        "models": {},
    }

    if progress_callback:
        progress_callback({
            "kind": "data_ready",
            "row_count": int(len(df)),
            "transaction_types": available_types,
            "teams": available_teams,
            "data_range": registry["data_range"],
        })

    all_scores_for_plot: dict = {}

    # Aggregation, ekip/işlem_tipi'nden bağımsızdır (tüm ekip/tip kombinasyonları
    # için tek seferde hesaplanıp sonradan filtrelenir — bkz. aggregator.py).
    # Birim döngüsü içinde tekrar tekrar çağırmak yerine her frekans için bir kez
    # hesaplayıp önbelleğe al.
    agg_cache: dict[str, pd.DataFrame] = {}
    for f in freqs:
        agg_cache[f] = aggregate_daily(df) if f == "daily" else aggregate_hourly(df, working_hours=working_hours)

    # Yalnızca gerçekte gözlemlenmiş (team, transaction_type) çiftleri için birim
    # oluştur — her ekip her işlem tipini yapmaz, var olmayan kombinasyonları
    # eğitmeye çalışmak zaman kaybı ve muhtemelen hata olurdu.
    existing_pairs = set(zip(df["team"], df["transaction_type"]))

    tmp_dir = tempfile.mkdtemp()
    try:
        agg_pkl_paths: dict[str, str] = {}
        for f, agg_df in agg_cache.items():
            pkl_path = os.path.join(tmp_dir, f"{f}_agg.pkl")
            agg_df.to_pickle(pkl_path)
            agg_pkl_paths[f] = pkl_path

        unit_args = [
            (team, tt, f, agg_pkl_paths[f], features_cfg, models_cfg,
             candidate_models, multi_save, cv_folds, metric, min_days, output_dir, report)
            for team in teams for tt in types for f in freqs
            if (team, tt) in existing_pairs
        ]
        total_units = len(unit_args)

        if progress_callback:
            progress_callback({
                "kind": "plan",
                "total_units": total_units,
                "teams": teams,
                "types": types,
                "freqs": freqs,
            })

        os.makedirs(output_dir, exist_ok=True)
        mp_ctx = multiprocessing.get_context("spawn")
        max_workers = min(total_units, os.cpu_count() or 1) if total_units else 1

        unit_index = 0
        with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers, mp_context=mp_ctx) as pool:
            future_map = {}
            for args in unit_args:
                team, tt, f_freq = args[0], args[1], args[2]
                unit_index += 1
                console.print(f"\n[bold]{'─'*50}[/bold]")
                console.print(f"[bold yellow]Kuyruğa alındı: {team} / {tt} / {f_freq}[/bold yellow]")
                if progress_callback:
                    progress_callback({
                        "kind": "unit_start",
                        "team": team,
                        "type": tt,
                        "freq": f_freq,
                        "index": unit_index,
                        "total": total_units,
                    })
                future_map[pool.submit(_train_unit, args)] = (team, tt, f_freq)

            for future in concurrent.futures.as_completed(future_map):
                res = future.result()
                team = res["team"]
                tt = res["transaction_type"]
                f_freq = res["freq"]
                label = f"{team} / {tt} ({f_freq})"

                if res["success"]:
                    registry["models"].setdefault(team, {}).setdefault(tt, {})[f_freq] = res["registry_entry"]
                    all_scores_for_plot[label] = res["all_scores"]
                    console.print(f"[green]Tamamlandı: {label} — model: {res['registry_entry']['best_model']}[/green]")
                    if progress_callback:
                        re_ = res["registry_entry"]
                        progress_callback({
                            "kind": "unit_done",
                            "team": team,
                            "type": tt,
                            "freq": f_freq,
                            "model": re_["best_model"],
                            "cv_rmse": re_["cv_rmse"],
                            "feature_importance_top5": re_["feature_importance_top5"],
                        })
                else:
                    console.print(f"[red]Hata ({label}): {res['error']}[/red]")
                    if progress_callback:
                        progress_callback({
                            "kind": "unit_failed",
                            "team": team,
                            "type": tt,
                            "freq": f_freq,
                            "error": res["error"],
                        })
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)

    _save_registry(registry, registry_path)
    console.print(f"\n[green]Registry kaydedildi: {registry_path}[/green]")
    if progress_callback:
        progress_callback({"kind": "completed", "registry_path": registry_path})

    if report:
        try:
            plot_paths = {}
            if all_scores_for_plot:
                # her (ekip, işlem tipi) için aynı modelleri karşılaştır (freq'ten bağımsız)
                by_label_scores: dict = {}
                for label, scores in all_scores_for_plot.items():
                    base_label = label.rsplit(" (", 1)[0]
                    by_label_scores.setdefault(base_label, {}).update(scores)
                mc_path = f"outputs/plots/model_comparison_{metric_type}.html"
                plot_model_comparison(by_label_scores, metric, mc_path)
                plot_paths["Model Karşılaştırması"] = mc_path

            report_path = f"outputs/reports/training_report_{metric_type}.html"
            flat_view = {**registry, "models": _flatten_registry_models(registry["models"])}
            generate_training_report(flat_view, report_path, plot_paths)
            console.print(f"[green]Eğitim raporu: {report_path}[/green]")
        except Exception as e:
            console.print(f"[yellow]Rapor oluşturulamadı: {e}[/yellow]")

    return registry


def forecast_pipeline(
    start: str,
    end: str,
    metric_type: str,
    teams: list[str] = None,
    types: list[str] = None,
    freq: str = "daily",
    output_dir: str = "outputs/forecasts",
    fmt: list[str] = None,
    plot: bool = True,
    registry_path: str = None,
    config_path: str = "config/settings.yaml",
    historical_data: dict | None = None,
    models: list[str] | None = None,
    calibration_override: dict | None = None,
) -> dict:
    """
    `historical_data`: {"daily": daily_agg_df, "hourly": hourly_agg_df} biçiminde,
    yüklenen verinin agregasyonları (varsa). Verilirse, lag/rolling özellikleri
    sabit sıfır yerine gerçek geçmiş değerlerden ve döngü içinde üretilen
    tahminlerden (recursive) hesaplanır — bkz. `_recursive_predict`.

    `models`: None ise registry'deki `best_model` kullanılır (mevcut davranış).
    Bir veya daha fazla model adı verilirse, kayıtlı (`available_models`) olanlar
    için ayrı ayrı tahmin üretilir. Birden fazla model çalışırsa karşılaştırma
    için `by_team[team][type]["models"]` alanı doldurulur — bkz. modül başı yorum.

    `calibration_override`: `None` ise diskteki kayıtlı `config/calibration.yaml`
    okunur (varsayılan davranış — kaydedilen çarpanlar otomatik uygulanır). Boş
    `{}` verilirse (ör. önizleme endpoint'inin "kalibrasyonsuz" tarafı için) hiç
    çarpan uygulanmaz. Bkz. `src/analysis/calibration_multipliers.py`.
    """
    cfg = load_config(config_path)
    features_cfg = cfg.get("features", {})
    working_hours = tuple(cfg.get("data", {}).get("working_hours", [7, 18]))
    hours = list(range(working_hours[0], working_hours[1] + 1))
    historical_data = historical_data or {}

    from src.calibration_config import load_calibration
    calibration_cfg = load_calibration() if calibration_override is None else calibration_override
    half_days = set(calibration_cfg.get("half_days", []))

    if fmt is None:
        fmt = ["csv", "json", "html"]

    if registry_path is None:
        registry_path = registry_filename(metric_type)
    registry = _load_registry(registry_path)

    start_dt = pd.Timestamp(start)
    end_dt = pd.Timestamp(end)

    if not teams:
        teams = list(registry["models"].keys())

    freqs = ["daily", "hourly"] if freq == "both" else [freq]

    result = {
        "generated_at": datetime.now().isoformat(),
        "forecast_range": {"start": start, "end": end},
        "metric_type": metric_type,
        "by_team": {},
    }

    import joblib
    from src.features.calendar_features import add_calendar_features
    from src.features.calibration_patterns import PATTERN_PRECEDENCE, add_pattern_flags
    from src.features.seasonal_features import add_daily_fourier, add_hourly_fourier
    from src.models.base_model import BaseForecaster

    def _run_single_model_forecast(model_name: str, model_entry: dict, team: str, transaction_type: str, f: str):
        """Tek bir kayıtlı model ile bu (ekip, tip, frekans) için tahmin üretir.

        Döner: (piece, forecast_df). `piece`, result["by_team"][team][type] altına
        yazılacak {"model_used", "daily"} veya {"model_used", "hourly"} parçasıdır;
        `forecast_df` ise CSV/plot çıktıları için kullanılan ham tablodur.
        """
        model: BaseForecaster = BaseForecaster.load(model_entry["model_path"])
        encoder = joblib.load(model_entry["encoder_path"])
        feat_cols = model_entry["feature_names"]

        lag_cols = [c for c in feat_cols if c.startswith("lag_") or c.startswith("rolling_")]

        # Yüklenen verinin agregasyonundan bu (ekip, tip, frekans) için geçmiş seri
        hist_agg = historical_data.get(f)
        hist_subset = None
        if hist_agg is not None and not hist_agg.empty:
            candidate = hist_agg[
                (hist_agg["team"] == team) & (hist_agg["transaction_type"] == transaction_type)
            ]
            if not candidate.empty:
                hist_subset = candidate
        hist_keys, hist_count_map, fallback = _history_lookup(hist_subset, f)

        # Tahmin aralığı, geçmiş verinin bittiği yerden sonra başlıyorsa
        # (boşluk varsa) ızgarayı geçmişin hemen ardından başlatıyoruz —
        # böylece lag/rolling zinciri kopmadan (recursive) ilerleyebilir.
        grid_start_dt = start_dt
        if hist_keys:
            hist_last_date = hist_keys[-1][0] if f == "hourly" else hist_keys[-1]
            if hist_last_date < start_dt - pd.Timedelta(days=1):
                grid_start_dt = hist_last_date + pd.Timedelta(days=1)

        grid_dates = pd.date_range(grid_start_dt, end_dt, freq="D")

        if f == "daily":
            grid_df = pd.DataFrame({
                "date": grid_dates,
                "team": team,
                "transaction_type": transaction_type,
                "count": 0,
                "amount": 0,
            })
        else:
            rows = [(d, h, team, transaction_type) for d in grid_dates for h in hours]
            grid_df = pd.DataFrame(rows, columns=["date", "hour", "team", "transaction_type"])
            grid_df["count"] = 0
            grid_df["amount"] = 0

        grid_df["date"] = pd.to_datetime(grid_df["date"])
        grid_df = add_calendar_features(grid_df)

        # Lag/rolling sütunları recursive döngüde doldurulacak — şimdilik yer tutucu
        for col in lag_cols:
            grid_df[col] = np.nan

        # Fourier
        if f == "daily":
            grid_df = add_daily_fourier(
                grid_df,
                weekly_terms=features_cfg.get("fourier_weekly_terms", 3),
                yearly_terms=features_cfg.get("fourier_yearly_terms", 5),
            )
        else:
            grid_df = add_hourly_fourier(grid_df)

        # Target encoding
        grid_df["transaction_type_enc"] = encoder.transform(
            grid_df[["transaction_type"]]
        )

        # Eksik sütunları sıfırla
        for col in feat_cols:
            if col not in grid_df.columns:
                grid_df[col] = 0

        preds_raw = _recursive_predict(
            model=model,
            grid_df=grid_df,
            feat_cols=feat_cols,
            lag_cols=lag_cols,
            freq=f,
            hist_keys=hist_keys,
            hist_count_map=hist_count_map,
            fallback=fallback,
        )
        grid_df["predicted_count_raw"] = preds_raw

        # Izgara, geçmişle köprü kurmak için tahmin aralığından erken
        # başlamış olabilir (boşluk doldurma) — sonuca yalnızca istenen
        # aralığı dahil ediyoruz.
        forecast_df = grid_df.loc[grid_df["date"] >= start_dt].reset_index(drop=True)

        X_pred = forecast_df[feat_cols].fillna(0)
        try:
            qpreds = model.predict_quantiles(X_pred, [0.1, 0.9])
            lower = qpreds[0.1]
            upper = qpreds[0.9]
        except Exception:
            lower = forecast_df["predicted_count_raw"].values * 0.8
            upper = forecast_df["predicted_count_raw"].values * 1.2

        # Kalibrasyon çarpanları (Cuma / ayın ilk pazartesi / yarım gün, işlem tipi
        # bazında) — `grid_df` zaten `add_calendar_features` görmüş olduğundan
        # `forecast_df` (onun bir alt kümesi) `day_of_week`/`week_of_month` içerir,
        # `add_pattern_flags` bunları yeniden kullanır. Saatlik ızgarada aynı günün
        # tüm saatleri aynı `date` değerini paylaştığından çarpan gün içinde
        # otomatik olarak tutarlıdır — ayrı bir işlem gerekmez.
        forecast_df = add_pattern_flags(forecast_df, half_days)
        type_multipliers = calibration_cfg.get("multipliers", {}).get(transaction_type, {})
        row_multiplier = np.ones(len(forecast_df))
        applied_pattern = np.full(len(forecast_df), None, dtype=object)
        # PATTERN_PRECEDENCE ters sırada uygulanır ki en yüksek öncelikli (listede
        # ilk) desen en son yazılıp kazansın (bkz. calibration_patterns.py).
        for pattern in reversed(PATTERN_PRECEDENCE):
            mask = forecast_df[f"is_{pattern}"].values == 1
            row_multiplier[mask] = type_multipliers.get(pattern, 1.0)
            applied_pattern[mask] = pattern

        forecast_df["predicted_count"] = np.round(forecast_df["predicted_count_raw"].values * row_multiplier, 1)
        forecast_df["lower_80"] = np.round(np.maximum(lower, 0) * row_multiplier, 1)
        forecast_df["upper_80"] = np.round(np.maximum(upper, 0) * row_multiplier, 1)
        forecast_df["confidence"] = "high"
        forecast_df["model_used"] = model_name
        forecast_df["calibration_multiplier"] = row_multiplier
        forecast_df["calibration_pattern"] = applied_pattern

        calendar_cols = ["is_public_holiday", "is_religious_holiday", "is_month_start",
                         "is_month_end", "is_eve_of_holiday"]
        def _flags(row):
            return [c for c in calendar_cols if row.get(c, 0) == 1]
        forecast_df["calendar_flags"] = forecast_df.apply(
            lambda r: ",".join(_flags(r)), axis=1
        )

        if f == "daily":
            daily_list = []
            for _, row in forecast_df.iterrows():
                daily_list.append({
                    "date": str(row["date"].date()),
                    "predicted_count": float(row["predicted_count"]),
                    "lower_80": float(row["lower_80"]),
                    "upper_80": float(row["upper_80"]),
                    "confidence": row["confidence"],
                    "calendar_flags": row["calendar_flags"].split(",") if row["calendar_flags"] else [],
                    "calibration_multiplier": float(row["calibration_multiplier"]),
                    "calibration_pattern": row["calibration_pattern"] if pd.notna(row["calibration_pattern"]) else None,
                })
            piece = {"model_used": model_name, "daily": daily_list}
        else:
            hourly_by_date = {}
            for _, row in forecast_df.iterrows():
                d = str(row["date"].date())
                hourly_by_date.setdefault(d, []).append({
                    "hour": int(row["hour"]),
                    "count": float(row["predicted_count"]),
                    "calibration_multiplier": float(row["calibration_multiplier"]),
                    "calibration_pattern": row["calibration_pattern"] if pd.notna(row["calibration_pattern"]) else None,
                })
            piece = {"model_used": model_name, "hourly": hourly_by_date}

        return piece, forecast_df

    for team in teams:
        team_registry = registry["models"].get(team)
        if not team_registry:
            continue

        result["by_team"][team] = {}
        team_types = [t for t in types if t in team_registry] if types else list(team_registry.keys())

        for transaction_type in team_types:
            result["by_team"][team][transaction_type] = {}
            for f in freqs:
                type_registry = team_registry.get(transaction_type, {})
                reg_entry = type_registry.get(f)
                if reg_entry is None:
                    console.print(f"[yellow]Model bulunamadı: {team}/{transaction_type}/{f}, atlanıyor.[/yellow]")
                    continue

                best_name = reg_entry["best_model"]
                # Eski formatlı kayıtlarda available_models yok — best_model'den sentezle
                avail = reg_entry.get("available_models") or {best_name: {
                    "model_path": reg_entry["model_path"],
                    "encoder_path": reg_entry["encoder_path"],
                    "cv_rmse": reg_entry.get("cv_rmse"),
                    "feature_names": reg_entry["feature_names"],
                }}

                if not models:
                    run_models = [best_name]
                else:
                    run_models = [m for m in models if m in avail]
                    if not run_models:
                        run_models = [best_name]

                primary_name = best_name if best_name in run_models else run_models[0]

                pieces: dict[str, dict] = {}
                primary_forecast_df = None
                for model_name in run_models:
                    try:
                        piece, f_df = _run_single_model_forecast(
                            model_name, avail[model_name], team, transaction_type, f
                        )
                    except Exception as e:
                        console.print(f"[red]Tahmin üretilemedi ({team}/{transaction_type}/{f} / {model_name}): {e}[/red]")
                        continue
                    pieces[model_name] = piece
                    if model_name == primary_name:
                        primary_forecast_df = f_df

                if not pieces:
                    continue

                primary_piece = pieces.get(primary_name) or next(iter(pieces.values()))
                # Geriye dönük uyum: birincil modelin sonucu doğrudan üst seviyeye yazılır
                # (mevcut tüketiciler — comparison.py, frontend — bunu okumaya devam eder).
                result["by_team"][team][transaction_type].update(primary_piece)

                if len(pieces) > 1:
                    # Karşılaştırma verisi: her model için ayrı sonuç (overlay için).
                    # daily/hourly geçişleri arasında birikimli olarak birleştirilir.
                    models_field = result["by_team"][team][transaction_type].setdefault("models", {})
                    for name, piece in pieces.items():
                        entry = models_field.setdefault(name, {"model_used": name})
                        entry.update(piece)

                forecast_df = primary_forecast_df

                # CSV çıktı (birincil model için — mevcut davranışla aynı dosya adı)
                if "csv" in fmt and forecast_df is not None:
                    os.makedirs(output_dir, exist_ok=True)
                    csv_key = f"{_safe_key(team)}_{_safe_key(transaction_type)}"
                    csv_path = os.path.join(output_dir, f"forecast_{metric_type}_{start}_{csv_key}_{f}.csv")
                    out_cols = ["date", "team", "transaction_type", "predicted_count", "lower_80", "upper_80",
                                "confidence", "model_used", "calendar_flags"]
                    if f == "hourly":
                        out_cols.insert(1, "hour")
                    forecast_df[out_cols].to_csv(csv_path, index=False)

                # Grafik (birincil model için)
                if plot and f == "daily" and forecast_df is not None:
                    plot_key = f"{_safe_key(team)}_{_safe_key(transaction_type)}"
                    plot_path = f"outputs/plots/forecast_{metric_type}_{plot_key}_{f}_{start}.html"
                    plot_forecast(forecast_df, f"{team} / {transaction_type}", plot_path)

    # JSON çıktı
    if "json" in fmt:
        os.makedirs(output_dir, exist_ok=True)
        json_path = os.path.join(output_dir, f"forecast_{metric_type}_{start}.json")
        with open(json_path, "w", encoding="utf-8") as jf:
            json.dump(result, jf, ensure_ascii=False, indent=2, default=str)
        console.print(f"[green]JSON: {json_path}[/green]")

    # HTML rapor
    if "html" in fmt:
        plot_paths = {}
        flat_by_type: dict = {}
        for team, by_type in result["by_team"].items():
            for tt, info in by_type.items():
                flat_by_type[f"{team} / {tt}"] = info
                if plot:
                    plot_key = f"{_safe_key(team)}_{_safe_key(tt)}"
                    pp = f"outputs/plots/forecast_{metric_type}_{plot_key}_daily_{start}.html"
                    if os.path.exists(pp):
                        plot_paths[f"{team} / {tt} Günlük Tahmin"] = pp
        report_path = f"outputs/reports/forecast_report_{metric_type}_{start}.html"
        generate_forecast_report({**result, "by_type": flat_by_type}, report_path, plot_paths)
        console.print(f"[green]HTML Rapor: {report_path}[/green]")

    return result
