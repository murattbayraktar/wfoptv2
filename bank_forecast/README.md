# Banka Müşteri Talimat Sistemi — ML Tahmin Uygulaması

İşlem tipi bazında günlük ve saatlik banka işlem hacmini tahmin eden Python ML sistemi.

## Hızlı Başlangıç

```bash
# 1. Sanal ortam kur
python -m venv venv
venv\Scripts\activate      # Windows
# source venv/bin/activate  # Linux/Mac

# 2. Bağımlılıkları yükle
pip install -r requirements.txt

# 3. Demo veri üret
python scripts/generate_demo_data.py --output data/raw/demo.csv

# 4. Modeli eğit
python train.py --input data/raw/demo.csv --freq both --models auto --report

# 5. Tahmin yap
python forecast.py --start 2025-07-01 --end 2025-07-31 --freq daily --plot

# 6. Değerlendir
python evaluate.py --input data/raw/demo.csv --backtest-days 60 --plot
```

## CSV Giriş Formatı

```
islem_tipi,tarih,saat,islem_hacmi
EFT,2025-06-02,8,71
EFT,2025-06-02,9,180
EFT,2025-06-02,18,201
```

`tutar` (amount) sütunu opsiyoneldir; yoksa model yalnızca işlem hacmi (`count`) üzerinde eğitilir.
Sütun adı varyantları otomatik tanınır: `islem_hacmi`, `adet`, `volume`, `count` → standart `count`.

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

CSV yükleme + arka planda otomatik model eğitimi burada toplanmış (`TrainingScreen.tsx`):

- `UploadDropzone`: CSV sürükle-bırak / dosya seç ya da "Demo Data Yükle"
- Gerçek bir CSV yüklenince (`source_kind === 'upload'`) `DataContext.upload()` otomatik olarak `POST /api/retrain {freq: 'both'}` tetikler — demo veri ile eğitim **yapılmaz** (uyarı notu gösterilir)
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
