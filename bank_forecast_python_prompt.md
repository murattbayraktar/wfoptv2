# Banka Müşteri Talimat Sistemi — Python ML Tahmin Uygulaması

## Proje Özeti

Bir bankanın müşteri talimat sistemine ait geçmiş 1–1,5 yıllık işlem datasını kullanarak **işlem tipi bazında günlük ve saatlik işlem hacmini** tahminleyen, XGBoost ve alternatif modelleri içeren, hem eğitim hem tahmin çıktısı üreten bir Python uygulaması.

---

## Teknoloji Yığını

| Katman | Araç |
|---|---|
| Dil | Python 3.11+ |
| ML | XGBoost, LightGBM, scikit-learn (RandomForest, Ridge, SVR) |
| Zaman serisi | statsmodels (Holt-Winters / SARIMA referans) |
| Model seçimi | Otomatik CV + RMSE/MAE karşılaştırma |
| Veri işleme | pandas, numpy |
| Takvim | holidays (TR), workalendar |
| Görselleştirme | matplotlib, seaborn, plotly |
| CLI | argparse + rich (renkli terminal çıktısı) |
| Çıktı | CSV, JSON, PNG grafik, HTML rapor |

---

## Proje Dizin Yapısı

```
bank_forecast/
├── README.md
├── requirements.txt
├── config/
│   └── settings.yaml               # Model parametreleri, yollar, takvim ayarları
├── data/
│   ├── raw/                        # Ham CSV dosyaları buraya yüklenir
│   └── processed/                  # İşlenmiş feature setleri
├── models/
│   └── saved/                      # Eğitilmiş model dosyaları (.pkl / .ubj)
├── outputs/
│   ├── forecasts/                  # Tahmin CSV/JSON çıktıları
│   ├── reports/                    # HTML raporlar
│   └── plots/                      # Grafik PNG/HTML dosyaları
├── src/
│   ├── __init__.py
│   ├── pipeline.py                 # Ana orkestratör: train | forecast | evaluate
│   ├── data/
│   │   ├── loader.py               # CSV yükleme, sütun standardizasyonu
│   │   ├── validator.py            # Şema ve kalite doğrulama
│   │   └── aggregator.py           # Ham satır → günlük/saatlik aggregat
│   ├── features/
│   │   ├── calendar_features.py    # Bankacılık takvimi özellikleri
│   │   ├── lag_features.py         # Gecikmeli değerler ve hareketli ortalamalar
│   │   ├── seasonal_features.py    # Fourier, mevsimsel indeksler
│   │   └── feature_pipeline.py     # Tüm feature'ları birleştiren pipeline
│   ├── models/
│   │   ├── base_model.py           # Soyut temel sınıf
│   │   ├── xgboost_model.py        # XGBoost wrapper
│   │   ├── lightgbm_model.py       # LightGBM wrapper
│   │   ├── random_forest_model.py  # RandomForest wrapper
│   │   ├── holt_winters_model.py   # Holt-Winters baseline
│   │   ├── ridge_model.py          # Ridge regresyon (lineer baseline)
│   │   └── model_selector.py       # Otomatik model seçimi ve ensemble
│   ├── evaluation/
│   │   ├── metrics.py              # RMSE, MAE, MAPE, sMAPE, coverage
│   │   └── backtester.py           # Walk-forward CV
│   └── reporting/
│       ├── plot_builder.py         # Grafik üretimi
│       └── html_reporter.py        # HTML rapor üretimi
├── train.py                        # `python train.py --input data/raw/transactions.csv`
├── forecast.py                     # `python forecast.py --start 2025-07-01 --end 2025-07-31`
└── evaluate.py                     # `python evaluate.py --backtest-days 60`
```

---

## CSV Giriş Formatı

### Beklenen sütunlar

```
tarih,saat,islem_tipi,adet,tutar
2024-01-15,09,EFT,142,2850000
2024-01-15,10,Havale,87,950000
```

### Kabul edilen sütun adı varyantları (`src/data/loader.py`)

| Standart | Alternatifler |
|---|---|
| `date` | tarih, DATE, TARIH, dt |
| `hour` | saat, SAAT, HOUR, hr |
| `transaction_type` | islem_tipi, TIP, type, TYPE |
| `count` | adet, ADET, COUNT, volume |
| `amount` | tutar, TUTAR, AMOUNT (opsiyonel) |

`amount` sütunu yoksa 0 kabul et, model yalnızca `count` üzerinde eğitilir.

---

## Feature Engineering (`src/features/`)

### 1. Bankacılık Takvimi Özellikleri (`calendar_features.py`)

```python
# Türk resmi tatilleri (holidays kütüphanesi + manuel ekleme)
TR_PUBLIC_HOLIDAYS = {
    "01-01": "Yılbaşı",
    "04-23": "Ulusal Egemenlik ve Çocuk Bayramı",
    "05-01": "Emek ve Dayanışma Günü",
    "05-19": "Atatürk'ü Anma",
    "07-15": "Demokrasi ve Millî Birlik Günü",
    "08-30": "Zafer Bayramı",
    "10-29": "Cumhuriyet Bayramı",
}

# Dini bayramlar (2023–2027 sabit tablo)
RELIGIOUS_HOLIDAYS = {
    2023: {"ramadan": ["2023-04-21","2023-04-22","2023-04-23"],
           "eid":     ["2023-06-28","2023-06-29","2023-06-30","2023-07-01"]},
    2024: {"ramadan": ["2024-04-10","2024-04-11","2024-04-12"],
           "eid":     ["2024-06-16","2024-06-17","2024-06-18","2024-06-19"]},
    2025: {"ramadan": ["2025-03-30","2025-03-31","2025-04-01"],
           "eid":     ["2025-06-06","2025-06-07","2025-06-08","2025-06-09"]},
    2026: {"ramadan": ["2026-03-20","2026-03-21","2026-03-22"],
           "eid":     ["2026-05-27","2026-05-28","2026-05-29","2026-05-30"]},
    2027: {"ramadan": ["2027-03-09","2027-03-10","2027-03-11"],
           "eid":     ["2027-05-16","2027-05-17","2027-05-18","2027-05-19"]},
}

def add_calendar_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Üretilen binary/sayısal özellikler:
    - is_public_holiday       : Resmi tatil
    - is_religious_holiday    : Dini bayram
    - is_eve_of_holiday       : Arife (tatil öncesi son iş günü)
    - is_bridge_day           : Köprü günü
    - is_month_start          : Ayın 1'i (veya ilk iş günü)
    - is_month_end            : Ayın son iş günü
    - is_last_friday          : Ayın son Cuması
    - days_to_month_end       : Ay sonuna kaç gün
    - days_from_month_start   : Ay başından kaç gün geçti
    - days_to_next_holiday    : Bir sonraki tatile kaç gün
    - days_from_last_holiday  : Son tatilden kaç gün geçti
    - post_holiday_day1       : Tatil sonrası ilk iş günü (yığılma etkisi)
    - post_holiday_day2       : Tatil sonrası ikinci iş günü
    - day_of_week             : 0=Pazar … 6=Cumartesi
    - day_of_month            : 1–31
    - week_of_month           : 1–5
    - month                   : 1–12
    - quarter                 : 1–4
    - is_weekend              : Cumartesi veya Pazar
    - month_quarter           : 0=baş(1-10), 1=orta(11-20), 2=son(21+)
    """
```

### 2. Gecikmeli Özellikler (`lag_features.py`)

```python
# İşlem tipi bazında gecikmeli değerler
LAG_DAYS = [1, 2, 3, 5, 7, 14, 21, 28]  # Günlük model için
LAG_HOURS = [1, 2, 3, 24, 48, 168]       # Saatlik model için

# Hareketli ortalamalar
ROLLING_WINDOWS = [7, 14, 30]             # Günlük için gün
ROLLING_WINDOWS_H = [24, 48, 168]         # Saatlik için saat

def add_lag_features(df: pd.DataFrame, target_col: str, freq: str) -> pd.DataFrame:
    """
    Her işlem tipi kendi grubunda lag hesaplar.
    Data sızıntısını önlemek için min_periods=1 kullan.
    Eksik lag değerleri için forward-fill değil, grup medyanı kullan.
    """
```

### 3. Mevsimsel Özellikler — Fourier (`seasonal_features.py`)

```python
def add_fourier_features(df: pd.DataFrame, period: int, n_terms: int) -> pd.DataFrame:
    """
    Periyodik deseni sinüs/kosinüs ile yakala.
    Günlük model: period=7 (haftalık), period=365 (yıllık), n_terms=3
    Saatlik model: period=24 (günlük), period=168 (haftalık), n_terms=4
    """
    for k in range(1, n_terms + 1):
        df[f"sin_{period}_{k}"] = np.sin(2 * np.pi * k * df["t"] / period)
        df[f"cos_{period}_{k}"] = np.cos(2 * np.pi * k * df["t"] / period)
    return df
```

### 4. Hedef Kodlama — İşlem Tipi (`feature_pipeline.py`)

`transaction_type` sütununu one-hot encoding yerine **target encoding** (grup ortalaması) ile kodla. Veri sızıntısını önlemek için eğitim setinde leave-one-out ya da cross-val target encoding uygula (`category_encoders.TargetEncoder`).

---

## Model Mimarisi (`src/models/`)

### Temel Sınıf (`base_model.py`)

```python
from abc import ABC, abstractmethod

class BaseForecaster(ABC):
    def __init__(self, transaction_type: str, freq: str):  # freq: 'daily' | 'hourly'
        self.transaction_type = transaction_type
        self.freq = freq
        self.model = None
        self.feature_names: list[str] = []
        self.metrics: dict = {}

    @abstractmethod
    def fit(self, X: pd.DataFrame, y: pd.Series) -> None: ...

    @abstractmethod
    def predict(self, X: pd.DataFrame) -> np.ndarray: ...

    def save(self, path: str) -> None: ...
    def load(self, path: str) -> None: ...
```

### XGBoost (`xgboost_model.py`)

```python
import xgboost as xgb
from sklearn.model_selection import TimeSeriesSplit

XGBOOST_PARAM_GRID = {
    "n_estimators":      [200, 500, 1000],
    "max_depth":         [4, 6, 8],
    "learning_rate":     [0.01, 0.05, 0.1],
    "subsample":         [0.7, 0.9],
    "colsample_bytree":  [0.7, 0.9],
    "min_child_weight":  [1, 3, 5],
    "reg_alpha":         [0, 0.1, 1.0],   # L1
    "reg_lambda":        [1.0, 2.0],       # L2
}

class XGBoostForecaster(BaseForecaster):
    def fit(self, X, y):
        # TimeSeriesSplit ile 5-fold CV + RandomizedSearchCV
        # early_stopping_rounds=50 ile overfitting kontrolü
        # eval_metric='rmse'
        pass

    def get_feature_importance(self) -> pd.DataFrame:
        # Gain ve weight bazlı önem skorları
        pass
```

### LightGBM (`lightgbm_model.py`)

```python
LGBM_PARAMS = {
    "n_estimators":      [200, 500, 1000],
    "num_leaves":        [31, 63, 127],
    "learning_rate":     [0.01, 0.05, 0.1],
    "feature_fraction":  [0.7, 0.9],
    "bagging_fraction":  [0.7, 0.9],
    "bagging_freq":      [5],
    "min_child_samples": [10, 20, 50],
    "reg_alpha":         [0, 0.1],
    "reg_lambda":        [0, 0.1],
}
# LightGBM kategorik sütunları (day_of_week, month_quarter vb.) doğrudan handle eder
# categorical_feature parametresine geçir
```

### RandomForest (`random_forest_model.py`)

```python
RF_PARAMS = {
    "n_estimators":  [100, 300],
    "max_depth":     [8, 12, None],
    "max_features":  ["sqrt", 0.5, 0.7],
    "min_samples_leaf": [2, 5, 10],
}
```

### Holt-Winters (`holt_winters_model.py`)

```python
from statsmodels.tsa.holtwinters import ExponentialSmoothing

# Baseline model: feature engineering gerektirmez
# Günlük için seasonal_periods=7 (haftalık)
# Saatlik için seasonal_periods=24 (günlük)
# trend='add', seasonal='add'
# Otomatik alpha/beta/gamma optimizasyonu statsmodels tarafından yapılır
# Tatil günleri: 0 olarak modele girer, post_holiday_day1/2 ile telafi edilir
```

### Ridge Baseline (`ridge_model.py`)

```python
# Sadece takvim özelliklerini kullanır (lag yok)
# Yorumlanabilirlik için: katsayılar doğrudan takvim etkilerini gösterir
# Her işlem tipi için birer Ridge modeli
```

---

## Otomatik Model Seçimi (`src/models/model_selector.py`)

### Her İşlem Tipi İçin Ayrı Model

```python
class ModelSelector:
    """
    Her (transaction_type, freq) çifti için en iyi modeli seçer.
    Seçim kriteri: Walk-forward CV üzerinde RMSE.
    """

    CANDIDATE_MODELS = ["xgboost", "lightgbm", "random_forest", "holt_winters", "ridge"]

    def select_best(
        self,
        transaction_type: str,
        freq: str,          # 'daily' | 'hourly'
        X_train: pd.DataFrame,
        y_train: pd.Series,
        cv_folds: int = 5,
        metric: str = "rmse",    # rmse | mae | mape
    ) -> dict:
        """
        1. Her aday model için TimeSeriesSplit CV çalıştır
        2. Metrik tablosunu üret
        3. En iyi modeli seç
        4. Seçim gerekçesini kaydet (log + rapor için)

        Dönüş:
        {
            "best_model":    "xgboost",
            "best_score":    12.4,
            "all_scores":    {"xgboost": 12.4, "lightgbm": 13.1, ...},
            "selection_reason": "XGBoost en düşük CV RMSE'yi verdi (12.4). ..."
        }
        """
```

### Ensemble Seçeneği

```python
class WeightedEnsemble(BaseForecaster):
    """
    CV skorlarına göre ters-ağırlıklı ensemble.
    w_i = 1/RMSE_i  →  normalize

    Yalnızca en iyi 3 modeli dahil et (kötü modeller gürültü ekler).
    """
```

---

## Değerlendirme Metrikleri (`src/evaluation/metrics.py`)

```python
def rmse(y_true, y_pred) -> float: ...
def mae(y_true, y_pred) -> float: ...
def mape(y_true, y_pred) -> float: ...          # sıfır korumalı
def smape(y_true, y_pred) -> float: ...
def coverage_95(y_true, lower, upper) -> float: ...  # PI kapsamı

def full_report(y_true, y_pred, label: str) -> dict:
    """Tüm metrikleri tek sözlükte döndür + basit yorum üret."""
```

### Walk-Forward Cross-Validation (`src/evaluation/backtester.py`)

```python
class WalkForwardBacktester:
    """
    TimeSeriesSplit ile gerçekçi backtest.

    - Eğitim penceresi: min 90 gün, büyüyen pencere (expanding window)
    - Tahmin ufku: 7 gün (günlük), 24 saat (saatlik)
    - Her fold için feature'lar sıfırdan hesaplanır (data sızıntısı yok)
    - Tatil günleri ayrı kümede değerlendirilir

    Çıktı:
    - fold bazlı metrik tablosu
    - işlem tipi bazlı özet
    - tatil vs normal gün karşılaştırması
    """
```

---

## Eğitim Modülü (`train.py`)

```bash
python train.py \
    --input data/raw/transactions.csv \
    --freq daily \          # daily | hourly | both
    --types EFT,Havale \    # boş bırakırsan tüm tipler
    --models xgboost,lightgbm,random_forest \   # veya 'auto' (tümünü dene)
    --cv-folds 5 \
    --metric rmse \
    --output-dir models/saved/ \
    --report                # HTML rapor üret
```

### Eğitim Akışı

```
1. CSV yükle → sütun standardizasyonu → kalite kontrolü
2. Her (type, freq) çifti için:
   a. Aggregation (günlük/saatlik toplam)
   b. Feature engineering (takvim + lag + Fourier)
   c. Train/validation split (son %20 veya son 60 gün)
   d. ModelSelector.select_best() → CV karşılaştırma
   e. En iyi model final eğitim (tüm train data)
   f. Model kaydet: models/saved/{type}_{freq}_best.pkl
   g. Seçim gerekçesi ve metrikleri kaydet: models/saved/model_registry.json
3. Eğitim özeti raporu: outputs/reports/training_report.html
```

### `model_registry.json` Yapısı

```json
{
  "trained_at": "2025-06-15T10:30:00",
  "data_range": {"start": "2024-01-01", "end": "2025-06-01"},
  "models": {
    "EFT_daily": {
      "best_model": "xgboost",
      "cv_rmse": 12.4,
      "cv_mae": 9.1,
      "all_scores": {"xgboost": 12.4, "lightgbm": 13.1, "random_forest": 15.2, "holt_winters": 18.7, "ridge": 22.3},
      "selection_reason": "XGBoost en düşük CV RMSE'yi verdi. Güçlü haftalık mevsimsellik ve takvim hassasiyeti gradient boosting ile iyi yakalandı.",
      "feature_importance_top5": ["lag_7", "day_of_week", "is_month_end", "lag_14", "rolling_mean_7"],
      "model_path": "models/saved/EFT_daily_best.pkl"
    },
    "EFT_hourly": { ... },
    "Havale_daily": { ... }
  }
}
```

---

## Tahmin Modülü (`forecast.py`)

```bash
python forecast.py \
    --start 2025-07-01 \
    --end   2025-07-31 \
    --types EFT,Havale \        # boş = tüm kayıtlı tipler
    --freq  daily \             # daily | hourly | both
    --format csv,json,html \    # çıktı formatları
    --plot                      # grafik üret
    --output-dir outputs/forecasts/
```

### Tahmin Akışı

```
1. model_registry.json yükle
2. Her (type, freq) çifti için:
   a. Kaydedilmiş modeli yükle
   b. Tahmin edilecek günler için feature vektörü üret
      - Takvim özellikleri: deterministik (gelecek tarihler için sorunsuz)
      - Lag özellikleri: bilinen son değerlerden özyinelemeli olarak üret
        (Tahmin ufku uzadıkça lag'lar tahmine dayalı hale gelir — bunu belirt)
      - Fourier: deterministik
   c. Tahmin et → güven aralığı üret (bootstrap veya quantile regression)
   d. Post-processing:
      - Negatif tahminleri sıfıra klamp
      - Tatil günleri için ek düzeltme (registry'deki holiday multiplier)
      - Tatil sonrası yığılma: post_holiday_day1/2 modelden gelir
3. Saatlik tahmin varsa günlük toplamla ölçekle (tutarlılık için)
4. Çıktıları kaydet
```

### Güven Aralığı Üretimi

```python
# Yöntem 1 — Quantile XGBoost (önerilen)
# objective='reg:quantileloss', quantile_alpha=[0.1, 0.5, 0.9]
# Alt=%10, Merkez=%50, Üst=%90 → %80 PI

# Yöntem 2 — Bootstrap (fallback)
# Eğitim rezidüellerinin bootstrap dağılımı
# Daha yavaş ama model agnostik
```

---

## Çıktı Formatları

### CSV (`outputs/forecasts/forecast_{date}.csv`)

```
date,hour,transaction_type,predicted_count,predicted_amount,lower_80,upper_80,confidence,model_used,calendar_flags
2025-07-01,,EFT,187,3420000,156,218,high,xgboost,"is_month_start"
2025-07-01,09,EFT,23,430000,18,28,high,xgboost,""
2025-07-01,10,EFT,31,570000,25,37,high,xgboost,""
```

`hour` sütunu günlük tahminlerde boş, saatlik tahminlerde dolu.

### JSON (`outputs/forecasts/forecast_{date}.json`)

```json
{
  "generated_at": "2025-06-15T10:30:00",
  "forecast_range": {"start": "2025-07-01", "end": "2025-07-31"},
  "summary": {
    "total_predicted_transactions": 12450,
    "peak_day": {"date": "2025-07-31", "count": 892, "reason": "Ayın son iş günü"},
    "lowest_day": {"date": "2025-07-05", "count": 12, "reason": "Cumartesi"}
  },
  "by_type": {
    "EFT": {
      "model_used": "xgboost",
      "daily": [
        {
          "date": "2025-07-01",
          "predicted_count": 187,
          "lower_80": 156,
          "upper_80": 218,
          "confidence": "high",
          "calendar_flags": ["is_month_start"],
          "hourly": [
            {"hour": 9, "count": 23},
            {"hour": 10, "count": 31},
            ...
          ]
        }
      ]
    }
  }
}
```

### HTML Rapor (`outputs/reports/forecast_report_{date}.html`)

Plotly ile interaktif grafikler içeren, standalone (CDN bağımlılığı dahil) HTML dosyası:

1. **Özet Kart Tablosu**: Her işlem tipi → kullanılan model, toplam tahmin, peak gün
2. **Günlük Tahmin Grafiği**: Çizgi + güven bandı, özel gün işaretçileri
3. **Saatlik Isı Haritası**: Gün × Saat matris, renk = işlem yoğunluğu
4. **Model Karşılaştırma Tablosu**: CV metrikleri yan yana
5. **Önemli Takvim Günleri**: Tahmin dönemindeki özel günler ve beklenen etkisi

---

## Değerlendirme Modülü (`evaluate.py`)

```bash
python evaluate.py \
    --input data/raw/transactions.csv \
    --backtest-days 60 \            # son 60 günü test seti olarak ayır
    --types EFT,Havale \
    --plot \
    --output-dir outputs/reports/
```

```
Çıktı terminalde (rich tablo):
┌──────────────┬───────────┬────────┬────────┬────────┬──────────────┐
│ Tip          │ Model     │  RMSE  │  MAE   │  MAPE  │ PI Coverage  │
├──────────────┼───────────┼────────┼────────┼────────┼──────────────┤
│ EFT          │ xgboost   │  12.4  │   9.1  │  6.2%  │    81.3%     │
│ Havale       │ lightgbm  │  18.7  │  13.4  │  8.9%  │    79.1%     │
│ Çek Tahsilat │ holt_win. │  31.2  │  22.8  │ 19.4%  │    77.6%     │
└──────────────┴───────────┴────────┴────────┴────────┴──────────────┘
```

---

## `requirements.txt`

```
xgboost>=2.0.0
lightgbm>=4.3.0
scikit-learn>=1.4.0
statsmodels>=0.14.0
pandas>=2.1.0
numpy>=1.26.0
matplotlib>=3.8.0
seaborn>=0.13.0
plotly>=5.20.0
holidays>=0.45
workalendar>=16.2.0
category-encoders>=2.6.0
rich>=13.7.0
pyyaml>=6.0
joblib>=1.3.0
```

---

## `config/settings.yaml`

```yaml
data:
  date_formats: ["%Y-%m-%d", "%d.%m.%Y", "%d/%m/%Y", "%Y%m%d"]
  working_hours: [7, 18]        # Tahmin sadece bu saat aralığı için anlamlı
  min_training_days: 60         # Bu altında model eğitimi uyarı verir

features:
  lag_days_daily: [1, 2, 3, 5, 7, 14, 21, 28]
  lag_hours_hourly: [1, 2, 3, 24, 48, 168]
  rolling_windows_daily: [7, 14, 30]
  fourier_weekly_terms: 3
  fourier_yearly_terms: 5

models:
  cv_folds: 5
  cv_metric: rmse               # rmse | mae | mape
  random_state: 42
  n_jobs: -1                    # Tüm CPU çekirdekleri
  xgboost_n_iter: 30            # RandomizedSearchCV iterasyon sayısı
  lightgbm_n_iter: 30
  rf_n_iter: 20

forecast:
  confidence_method: quantile   # quantile | bootstrap
  confidence_level: 0.80        # %80 PI
  max_horizon_daily: 90         # Maksimum 90 gün ilerisi tahmin edilebilir
  max_horizon_hourly: 30        # Maksimum 30 gün ilerisi (saatlik)

output:
  float_precision: 1
  include_feature_importance: true
```

---

## Geliştirme Adımları (Sıralı)

```
1. Proje iskeletini oluştur
   mkdir -p bank_forecast/{data/{raw,processed},models/saved,outputs/{forecasts,reports,plots},src/{data,features,models,evaluation,reporting},config}
   cd bank_forecast && python -m venv venv && source venv/bin/activate
   pip install -r requirements.txt

2. Veri katmanını yaz (src/data/)
   - loader.py: sütun standardizasyonu, tarih parse, encoding tespiti
   - validator.py: boş değer raporu, tip uyumu, anomali tespiti
   - aggregator.py: günlük ve saatlik aggregation, eksik gün doldurma (0)
   Test: pytest tests/test_data.py

3. Feature engineering (src/features/)
   - calendar_features.py: tüm Türk tatili ve iş günü kuralları
   - lag_features.py: groupby(type).shift() ile sızıntısız lag
   - seasonal_features.py: Fourier
   - feature_pipeline.py: hepsini birleştir, korelasyon raporu üret
   Test: pytest tests/test_features.py

4. Model wrapperları yaz (src/models/)
   - base_model.py
   - Sırasıyla: ridge → holt_winters → random_forest → lightgbm → xgboost
   - Her model için birim testi
   Test: pytest tests/test_models.py

5. ModelSelector'ı yaz
   - Walk-forward CV
   - RandomizedSearchCV entegrasyonu
   - model_registry.json yazıcı

6. Evaluation katmanını yaz (src/evaluation/)
   - metrics.py
   - backtester.py

7. Raporlama katmanını yaz (src/reporting/)
   - plot_builder.py: matplotlib statik + plotly interaktif
   - html_reporter.py: Jinja2 veya f-string tabanlı standalone HTML

8. train.py CLI'ı yaz ve test et
   python train.py --input data/raw/sample.csv --freq both --models auto --report

9. forecast.py CLI'ı yaz ve test et
   python forecast.py --start 2025-07-01 --end 2025-07-31 --freq both --plot

10. evaluate.py CLI'ı yaz ve test et
    python evaluate.py --input data/raw/sample.csv --backtest-days 60 --plot

11. Uçtan uca entegrasyon testi
    - 50.000+ satır sentetik CSV ile tam pipeline
    - Tatil günü doğrulama
    - Çıktı dosyası kalite kontrolü
```

---

## Demo Verisi Oluşturma (`scripts/generate_demo_data.py`)

```python
"""
Gerçekçi 18 aylık sentetik işlem datası üretir.
Kullanım: python scripts/generate_demo_data.py --output data/raw/demo.csv
"""

DEMO_CONFIG = {
    "start_date": "2024-01-01",
    "end_date": "2025-06-30",
    "transaction_types": {
        "EFT":            {"base_daily": 200, "trend": +0.15, "cv": 0.28, "calendar_sensitivity": 1.4},
        "Havale":         {"base_daily": 350, "trend": +0.05, "cv": 0.22, "calendar_sensitivity": 1.3},
        "Kredi Ödemesi":  {"base_daily": 180, "trend": -0.02, "cv": 0.55, "calendar_sensitivity": 2.1},
        "Mevduat":        {"base_daily": 120, "trend": +0.08, "cv": 0.35, "calendar_sensitivity": 1.6},
        "Çek Tahsilat":   {"base_daily":  60, "trend": -0.10, "cv": 0.72, "calendar_sensitivity": 2.4},
    },
    "hourly_profile": [0,0,0,0,0,0,0.02,0.05,0.12,0.14,0.13,0.11,0.08,0.09,0.10,0.09,0.07,0.05,0.03,0.02,0,0,0,0],
}
# Her işlem tipinin farklı özelliğe sahip olması,
# model seçicinin farklı algoritmalar seçmesini sağlar:
# EFT → XGBoost (trend + haftalık mevsimsellik)
# Kredi Ödemesi → Takvim Kural / LightGBM (yüksek takvim hassasiyeti)
# Çek Tahsilat → Holt-Winters veya Takvim Kural (yüksek CV)
```

---

## Kritik Notlar

1. **Data sızıntısı**: Lag ve rolling feature hesaplarken gelecekteki verinin eğitime sızmamasına dikkat et. `groupby + shift` kullan, `transform(mean)` kullanma.

2. **Tatil günü sıfırlar**: Tatil günleri `count=0` olarak aggregation'a girer. Modelin bunları "gerçek sıfır" olarak öğrenmesi için `is_public_holiday` ve `is_religious_holiday` feature'larını ekle. Yoksa model tatil öncesi düşük değerleri öğrenir ama nedenini bilemez.

3. **Tatil sonrası yığılma**: `post_holiday_day1` ve `post_holiday_day2` feature'ları tatil sonrası oluşan işlem birikimini yakalar. Bu feature olmadan model tatil sonrası günleri kronik olarak düşük tahmin eder.

4. **Saatlik model bağımlılığı**: Saatlik model için lag_24 ve lag_168 kritik özelliklerdir. Tahmin ufku 24 saati geçtiğinde bu lag'lar tahmine dayalı hale gelir — özyinelemeli tahmin uygula ve belirsizliği güven aralığına yansıt.

5. **İşlem tipi bazında ayrı model**: Tüm tipleri tek modele sokmak yerine her `(type, freq)` çifti için bağımsız model eğit. Bu hem doğruluğu artırır hem de her tipin farklı sezonalite/trend yapısına uyum sağlar.

6. **Minimum veri eşiği**: 60 günden az verisi olan işlem tipleri için ML modeli yerine Holt-Winters veya saf takvim ortalaması kullan. Uyarı ver.

7. **Negatif tahmin koruması**: Tüm model çıktılarını `max(0, prediction)` ile klamp et.

8. **Model dosyası versiyonlama**: `model_registry.json`'a eğitim tarihi ve veri aralığını kaydet. Eski modelle yeni veri üzerinde tahmin yapılmasını önlemek için versiyon kontrolü ekle.
