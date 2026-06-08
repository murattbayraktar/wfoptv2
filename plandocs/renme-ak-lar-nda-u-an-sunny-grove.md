# Öğrenme Akışını Hızlandırma Planı (özellikle saatlik eğitim)

## Bağlam

`bank_forecast` projesinde şu an sadece **EFT** işlem tipi için öğrenme (training) akışı çalıştırılıyor, ancak yakında çok daha fazla işlem tipi (10-20+) eklenecek. Kullanıcı, özellikle **saatlik (hourly) frekansta model eğitiminin** çok uzun sürdüğünü belirtti. `_recursive_predict` (forecast-time, pipeline.py:92) `train_pipeline` içinde KULLANILMIYOR — yani şikayet, eğitim/CV/model-seçim aşamasıyla ilgili.

Saatlik aggregation ~33.000 satır üretirken (550 gün × 12 saat × N tip), günlük sadece ~2.750 satır üretiyor (~12x fark) — bu da saatlikte her bir model `fit()` çağrısını orantısız pahalı kılıyor.

Kod incelemesinde tespit edilen **asıl darboğaz, "iç içe (nested) cross-validation"** — bu, hem daily hem hourly'de var ama hourly'de mutlak süreyi katlanarak büyütüyor. Bunu çözmek, gelecekte eklenecek 10-20 işlem tipi için de doğrudan zaman tasarrufu sağlayacak (her tip × frekans biriminin maliyeti ~6x azalacak).

## Tespit Edilen Darboğazlar (öncelik sırasına göre)

### 1. Nested Cross-Validation (EN BÜYÜK KAZANÇ — ~5-6x)

`ModelSelector.select_best` ([model_selector.py:85](bank_forecast/src/models/model_selector.py#L85)) her aday model için `_cv_score` ([model_selector.py:45](bank_forecast/src/models/model_selector.py#L45)) çağırıyor; bu fonksiyon kendi `TimeSeriesSplit(cv_folds=5)` döngüsünde her "dış" fold'da `m.fit()` çağırıyor.

Ama ML modelleri (`XGBoostForecaster.fit` — [xgboost_model.py:30](bank_forecast/src/models/xgboost_model.py#L30), `LightGBMForecaster.fit` — [lightgbm_model.py:33](bank_forecast/src/models/lightgbm_model.py#L33), `RandomForestForecaster.fit` — [random_forest_model.py:25](bank_forecast/src/models/random_forest_model.py#L25)) `fit()` içinde **kendi başına** `RandomizedSearchCV(n_iter=30, cv=TimeSeriesSplit(5))` çalıştırıyor — yani zaten kendi iç-CV'si üzerinden bir `best_score_` (CV-RMSE) üretiyor.

Sonuç: tek bir (tip, frekans, xgboost) birimi için skor hesaplamak üzere **5 dış-fold × (5 iç-fold × 30 iter + 3 quantile-fit) ≈ 765 model.fit()** çağrısı yapılıyor — sonra seçilen model `train_best`/`train_selected` ([model_selector.py:162-200](bank_forecast/src/models/model_selector.py#L162-L200)) ile **sıfırdan tekrar** arama + quantile fit yapıyor (~153 fit daha). **Toplam ≈ 918 fit**, pratikte gerekli olan ise sadece ~157 (1 arama + 1 final tam-veri refit + quantile'lar).

**Çözüm — "search-once, score-from-search, refit-with-best-params":**

- ML model sınıflarına (`XGBoostForecaster`, `LightGBMForecaster`, `RandomForestForecaster`) `fit_from_params(X, y, params, cv_rmse=None)` adlı YENİ, opsiyonel bir metot eklenir — arama YAPMADAN, verilen hiperparametrelerle tek seferlik tam-veri fit + 3 quantile-fit yapar. Mevcut `fit()` (search + quantile) sözleşmesi bozulmaz; iç akışı küçük bir refactor ile `_search_best_params` + `_fit_quantiles` yardımcılarına bölünür.
- `ModelSelector.select_best` ([model_selector.py:119-138](bank_forecast/src/models/model_selector.py#L119-L138)), `ML_MODELS` kümesindeki adaylar için artık `_cv_score` çağırmaz — bunun yerine `m.fit(X_train, y_train)` (search BİR KEZ çalışır) sonrası `m.metrics["cv_rmse"]` (= `search.best_score_`) doğrudan karşılaştırma metriği olarak kullanılır. Arama sırasında bulunan `best_params_` ve fit edilmiş model `_search_artifacts` adlı dahili bir sözlükte saklanır. `holt_winters`/`ridge` için mevcut `_cv_score` akışı korunur (onlarda nested-search problemi yok).
- `train_best`/`train_selected` ([model_selector.py:162, 178](bank_forecast/src/models/model_selector.py#L162)) artık seçilen ML modeli için sıfırdan arama yapmaz — `_search_artifacts`'ten alınan `best_params` ile `fit_from_params(X, y, params)` çağrılır (tam veri `X` üzerinde tek final-fit). `hasattr(model, "fit_from_params")` kontrolüyle holt_winters/ridge etkilenmez.
- Registry alanları (`cv_rmse`, `all_scores`, `selection_reason`, `best_model` — [pipeline.py:316-327](bank_forecast/src/pipeline.py#L316-L327)) ile `_build_reason` ([model_selector.py:234](bank_forecast/src/models/model_selector.py#L234)) DEĞİŞMEDEN çalışır; tek anlamsal fark, `cv_rmse`'nin artık dış-5-fold ortalaması yerine RandomizedSearchCV'nin iç-5-fold `best_score_`'u olmasıdır (istatistiksel olarak benzer bir CV-RMSE tahmini, sadece dış döngü kaldırılmış olur).

### 2. Aggregation Tekrarı (düşük risk, hızlı kazanç)

[pipeline.py:247-250](bank_forecast/src/pipeline.py#L247-L250)'de `aggregate_daily(df)`/`aggregate_hourly(df, ...)` HER (tip × frekans) biriminde yeniden hesaplanıyor. Ama [aggregator.py:5-50](bank_forecast/src/data/aggregator.py#L5-L50)'deki bu fonksiyonlar tip-bağımsızdır — tüm tipler için tek seferde kartesyen tablo (`MultiIndex.from_product`) kurar, sonradan `subset = agg[agg["transaction_type"] == transaction_type]` ile filtrelenir.

**Çözüm:** `for transaction_type in types` döngüsünden ÖNCE her frekans için aggregation'ı bir kez hesaplayıp `agg_cache: dict[str, pd.DataFrame]` içinde sakla, döngü içinde sadece filtrele. Davranış değişmez — saf önbellekleme. 5 tip için 5x, gelecekte 20 tip için 20x tekrarlı kartesyen-çarpım kurulumu engellenir.

### 3. Frekansa Duyarlı CV/Arama Bütçesi (madde 1'den SONRA değerlendirilmeli)

`settings.yaml`'daki `cv_folds: 5`, `xgboost_n_iter: 30`, `lightgbm_n_iter: 30`, `rf_n_iter: 20` frekanstan bağımsız sabit; saatlik veri ~12x daha büyük olduğu için her fit orantısız pahalı.

**Çözüm:** `settings.yaml`'a opsiyonel `models.hourly_overrides` bloğu eklenir (örn. `cv_folds: 3`, `xgboost_n_iter: 15`, ...), `_make_model` ([model_selector.py:29](bank_forecast/src/models/model_selector.py#L29)) `freq == "hourly"` ise bu override'ları `cfg` üzerine uygular. Config-tabanlı, şeffaf ve geri alınabilir bir yaklaşım — "akıllı" otomatik ölçeklemeden daha öngörülebilir.

> **Not:** Bu adımı madde 1'den önce uygulamayın — nested-CV düzeltmesi zaten ~6x kazanç sağlayacağı için, bütçe küçültme ihtiyacı yeniden değerlendirilmeli (belki gereksiz kalır ya da daha hafif bir küçültme yeterli olur).

### 4. Tip Bazında Paralelleştirme (en yüksek karmaşıklık — gelecek için not)

`for transaction_type in types: for f in freqs` ([pipeline.py:231-232](bank_forecast/src/pipeline.py#L231-L232)) döngüsündeki birimler birbirinden bağımsızdır (ayrı registry anahtarı, ayrı dosyalar) ve teorik olarak paralelleştirilebilir. Ancak:
- ML modelleri zaten `n_jobs=-1` ile iç-paralellik kullanıyor → dış paralellik CPU oversubscription riski taşır (worker başına `n_jobs = cpu_count() // n_workers` olarak override edilmeli).
- `progress_callback` (routes_train.py'deki threading/SSE akışı) closure'ları `ProcessPoolExecutor` ile pickle edilemez → event-buffering gerekir (her birim event listesi döndürür, ana süreç sırayla `progress_callback`'e besler).
- `rich.Console` çıktıları alt-süreçlerde karışabilir.

**Öneri:** Bu adımı şimdilik ERTELEYİN — madde 1 (~6x) ve madde 2 uygulandıktan sonra gerçek süre ölçümü yapılıp, hâlâ gerekiyorsa ayrı bir görev olarak ele alınmalı. Gerekirse ilk adım olarak düşük-riskli `ThreadPoolExecutor` denenebilir (xgboost/lightgbm/sklearn native uzantıları GIL'i serbest bırakır, pickling sorunu olmaz).

## Uygulama Sırası

| Sıra | Değişiklik | Dosyalar | Risk | Beklenen Kazanç |
|---|---|---|---|---|
| 1 | Nested CV elimination | `model_selector.py`, `xgboost_model.py`, `lightgbm_model.py`, `random_forest_model.py` | Orta | ~5-6x (ML modelleri, hem daily hem hourly) |
| 2 | Aggregation cache | `pipeline.py` (~satır 231-250) | Çok düşük | Tip sayısıyla orantılı tekrarın elenmesi |
| 3 | Frekansa duyarlı bütçe | `settings.yaml`, `model_selector.py:_make_model` | Düşük | Ek ~1.5-2x (hourly), madde 1 sonrası değerlendirilir |
| 4 | Tip bazında paralelleştirme | (ertelendi) | Yüksek | CPU sayısına yakın, ayrı görev |

## Doğrulama

1. **A/B karşılaştırma (küçük alt-küme):** `train_pipeline(input_path=..., freq="hourly", types=["EFT"], models=["auto"])` değişiklik öncesi/sonrası iki ayrı `output_dir` (`models/saved_old`, `models/saved_new`) ile çalıştırılır:
   - Toplam süre karşılaştırması (`progress_callback` event zaman damgaları veya basit `time.perf_counter()` sarmalayıcı ile)
   - `registry["models"]["EFT_hourly"]` içindeki `all_scores`, `cv_rmse`, `best_model`, `selection_reason` alanları öncesi/sonrası karşılaştırılır — `best_model` aynı kalmalı (ya da çok yakın skorlu ikinci sırayla yer değiştirebilir), `cv_rmse` değerleri yakın olmalı (büyük sapma, search-budget'ın CV-tahminini bozduğunu gösterir; `random_state=42` ile tekrarlanabilirlik sağlanmalı).
2. **Birim doğrulama:** `fit()` ile `fit_from_params(best_params)` çağrılarının aynı veri üzerinde (yaklaşık) aynı `predict()` çıktısını ürettiği, ve `select_best` çağrısında ML modelleri için `_cv_score`'un artık ÇAĞRILMADIĞI (mock/patch ile call-count = 0) doğrulanır.
3. **Uçtan-uca smoke test:** `/api/retrain` (routes_train.py) üzerinden tetiklenip SSE/status akışının (`selection_start → model_evaluated × N → model_selected → unit_done`) hâlâ tutarlı sırada üretildiği, ve eğitim süresinin gözle görülür şekilde kısaldığı doğrulanır.
4. **Aggregation cache kontrolü:** `aggregate_hourly`/`aggregate_daily`'nin artık `len(types)` değil `len(freqs)` kez çağrıldığı doğrulanır.
