# Banka Müşteri Talimat Sistemi — ML Tahmin Uygulaması

Ekip × işlem tipi bazında günlük ve saatlik banka işlem hacmini (talimat ve işlem
adedi ayrı ayrı) tahmin eden Python ML sistemi.

## Hızlı Başlangıç

```bash
# 1. Sanal ortam kur
python -m venv venv
venv\Scripts\activate      # Windows
# source venv/bin/activate  # Linux/Mac

# 2. Bağımlılıkları yükle
pip install -r requirements.txt

# 3. Demo veri üret
# NOT: scripts/generate_demo_data.py şu an repoda mevcut değil (eski format için
# yazılmıştı, kaldırıldı). Yeni format için elle hazırlanmış bir test CSV'si kullanın
# (bkz. "CSV Giriş Formatı" altındaki örnek).

# 4. Modeli eğit (metrik --metric-type ile seçilir, aynı CSV'den 'talimat' ve
# EntryProcessCount kolonu varsa 'islem' ayrı ayrı eğitilebilir)
python train.py --input data/raw/talimatlar.csv --metric-type talimat --freq both --models auto --report
python train.py --input data/raw/talimatlar.csv --metric-type islem --freq both --models auto --report

# 5. Tahmin yap
python forecast.py --metric-type talimat --start 2025-07-01 --end 2025-07-31 --freq daily --plot

# 6. Değerlendir
python evaluate.py --input data/raw/talimatlar.csv --metric-type talimat --backtest-days 60 --plot
```

## CSV Giriş Formatı

Her satır bir talimatı (referansı) temsil eder — önceden agregatlanmış sayım
DEĞİLDİR. Sistem, satırları hem karşılayıcı (dispatcher) hem işlemci (operator)
ekibin kendi zaman diliminden görecek şekilde otomatik dönüştürür:

```
Reference,TaskType,SubTaskType,OrderDate,DispatcherMainPortfolio,FirstForwardOmDate,OperatorMainPortfolio,EntryProcessCount
100234,SOG,EFT,2025-06-02 11:00,MHS,2025-06-02 12:05,TLO,1
100235,SOG,EFT,2025-06-02 09:15,PSO,2025-06-02 09:20,PSO,1
100236,VIR,HVL,2025-06-02 14:40,MHS,,TLO,2
```

- `Reference`: talimatın tekil numarası.
- `TaskType` + `SubTaskType`: birleştirilip model kırılımı için `transaction_type`
  olarak kullanılır (örn. `"SOG-EFT"`).
- `OrderDate`: talimatın bankaya geliş zamanı — **karşılayıcı** (`DispatcherMainPortfolio`)
  ekibin göreceği zaman.
- `FirstForwardOmDate`: işlemci ekibe ilk yönlendirme zamanı (boş bırakılabilir —
  henüz yönlendirilmemişse) — **işlemci** (`OperatorMainPortfolio`) ekibin göreceği zaman.
- `DispatcherMainPortfolio` == `OperatorMainPortfolio` ise (aynı ekip karşılayıp
  kendi işliyor), talimat yalnızca `OrderDate` ile tek kez sayılır. Farklıysa ve
  `FirstForwardOmDate` doluysa, talimat **iki ekibin de** iş yükünde (kendi zaman
  damgasıyla) ayrı ayrı sayılır — bu kasıtlıdır.
- `EntryProcessCount` **opsiyoneldir**: mevcutsa aynı CSV'den `islem` metriği de
  (talimat başına işlem adedi toplamı) üretilir; yoksa yalnızca `talimat` metriği
  (referans/satır sayısı) üretilir.

Modeller **ekip × (TaskType-SubTaskType) × frekans** tam kırılımında eğitilir (her
kombinasyon için ayrı model) — bu yüzden ekip/tip sayısı arttıkça eğitim süresi de artar.

> Format değişikliği nedeniyle `models/saved/` altındaki önceden eğitilmiş modeller
> yeni `transaction_type` değerleriyle uyumsuzdur — geçiş sonrası yeniden eğitim gerekir.

## Web Arayüzü (FastAPI + React)

CLI akışının yanında `api/` (FastAPI) + `frontend/` (React + Vite + TS, Tailwind) ile bir web arayüzü de var.

```bash
# Backend (bank_forecast/ dizininden — registry/config göreli yollar buna bağlı)
uvicorn api.main:app --reload --port 8000

# Frontend
cd frontend && npm run dev   # http://localhost:5173
```

Durum in-memory tutulur (`api/state.py` — `STATE`, `RETRAIN_STATUS`); sayfa/sunucu yenilenince sıfırlanır.

İki sekme var (üstte `TopBar`'da geçiş yapılır):

### 1) "Tahmin" ekranı

Sadece **kayıtlı / öğrenilmiş** modellerle (`models/saved/model_registry.json`) çalışır — burada eğitim yapılmaz.

- Sol `Sidebar`: tarih aralığı seçimi (varsayılan: yüklenen verinin **son 30 günü** — `rangeFromDataset`, [DataContext.tsx](frontend/src/context/DataContext.tsx)) + "Tahmin Oluştur"
- `POST /api/forecast` → `forecast_pipeline(...)` ile tahmin üretir; seçilen aralık yüklenen veriyle örtüşüyorsa **gerçekleşen vs. tahmin** karşılaştırması da döner ([routes_forecast.py](api/routes_forecast.py), `comparison.py`)
- Veri yüklenmemişse kullanıcıyı "Veri & Model Eğitimi" sekmesine yönlendiren bir kart gösterilir (`NoDataCard`, [App.tsx](frontend/src/App.tsx))

### 2) "Veri & Model Eğitimi" ekranı

CSV yükleme + arka planda model eğitimi burada toplanmış (`TrainingScreen.tsx`):

- `UploadDropzone`: CSV sürükle-bırak / dosya seç; ayrıca eğitimde hangi algoritmanın kullanılacağını
  seçen bir açılır liste içerir ("Tümü (otomatik en iyi seçim)" ya da belirli bir algoritma —
  `xgboost`, `lightgbm`, `random_forest`, `holt_winters`, `ridge`)
- CSV yüklendikten sonra `DatasetSummaryCard` üzerinde beliren **"Eğitimi Başlat"** butonuna
  basılınca `DataContext.startTraining()` seçilen algoritmayla `POST /api/retrain {freq: 'both', models}`
  tetikler
- `TrainingProgress.tsx`: `GET /api/retrain/status`'u ~1.2 sn'de bir poll'layıp **adım adım ilerlemeyi** canlı gösterir — ilerleme çubuğu (`progress`, `completed_units/total_units`), Türkçe adım günlüğü (`steps[]`: `data_ready → plan → unit_start → selection_start → model_evaluated × N → model_selected → unit_done → ... → completed`), tamamlanınca seçilen algoritma + CV RMSE özet tablosu, hata durumunda banner

Backend tarafında bu adım akışı `progress_callback` enjeksiyonuyla sağlanıyor — `train_pipeline` ([pipeline.py](src/pipeline.py)) ve `ModelSelector.select_best` ([model_selector.py](src/models/model_selector.py)) opsiyonel `progress_callback=None` parametresi alır (CLI davranışını etkilemez), event'ler `routes_train.py`'de Türkçe mesajlara çevrilip `RETRAIN_STATUS`'a (`steps`, `progress`, `total_units`, `completed_units`) yazılır.

> Not: Windows'ta arka plan thread'inden `rich.console` ile özel karakter (`→` vb.) basmak `charmap` kodlama hatası verir — `api/main.py` başında `sys.stdout/stderr.reconfigure(encoding="utf-8")` ile çözüldü.

## Modeller

| Model | Kullanım Durumu |
|---|---|
| XGBoost | Güçlü trend + haftalık mevsimsellik |
| LightGBM | Yüksek takvim hassasiyeti |
| RandomForest | Stabil, düşük varyans |
| Holt-Winters | Az veri / basit mevsimsellik |
| Ridge | Yalnızca takvim etkisi (baseline) |

Model seçimi otomatik: her `(işlem_tipi, frekans)` çifti için walk-forward CV ile en iyi model seçilir.
