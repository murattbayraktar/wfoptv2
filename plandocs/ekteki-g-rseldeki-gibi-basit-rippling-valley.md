# WFOpt — İşlem Hacmi Tahmin Sistemi: Web Arayüzü

## Context

`bank_forecast` (d:\Projects\wfoptv2\bank_forecast) şu anda salt bir Python CLI aracı: `train.py`, `forecast.py`, `evaluate.py`. Hiçbir web/frontend katmanı yok. Kullanıcı, ekteki görseldeki gibi sade, koyu temalı bir web arayüzü istiyor: CSV yükleme / demo data, tahmin tarih aralığı seçimi, öğrenme-tahminleme adımlarını gösteren bir ilerleme paneli, ve sonunda algoritma/sonuç/grafik panelleri (toplam kayıt sayısı, saatlik kırılım, ve seçilen aralık geçmiş veriyle örtüşüyorsa gerçekleşen-vs-tahmin karşılaştırması).

Karar verilen mimari: **React + Vite SPA frontend + FastAPI backend**. Tahminleme `models/saved/model_registry.json` içindeki **mevcut eğitilmiş modellerle** doğrudan yapılacak (otomatik yeniden eğitim yok); yeniden eğitim opsiyonel ikincil bir aksiyon olarak sunulacak.

Mevcut Python pipeline fonksiyonları aynen yeniden kullanılacak — yeniden yazılmayacak:
- `forecast_pipeline(start, end, types, freq, output_dir, fmt, plot, registry_path, config_path)` → [pipeline.py:195](bank_forecast/src/pipeline.py#L195) — `fmt=[]`, `plot=False` ile çağrılırsa diske hiçbir şey yazmadan `{generated_at, forecast_range, by_type: {tip: {model_used, daily:[{date,predicted_count,lower_80,upper_80,confidence,calendar_flags}], hourly:{...}}}}` döndürür (doğrulandı: [pipeline.py:351-383](bank_forecast/src/pipeline.py#L351-L383) dosya yazımları `fmt`/`plot` koşullarına bağlı).
- `train_pipeline(...)` → [pipeline.py:42](bank_forecast/src/pipeline.py#L42) — opsiyonel "yeniden eğit" için.
- `load_transactions(filepath)` → [loader.py:50](bank_forecast/src/data/loader.py#L50) — Türkçe sütun takma adlarını (`tarih`, `islem_tipi`, `saat`, `islem_hacmi`/`adet`, `tutar`) otomatik tanır; bir dosya yoluna ihtiyaç duyar (bytes değil) → upload geçici dosyaya yazılmalı.
- `aggregate_daily(df)` / `aggregate_hourly(df, working_hours)` → [aggregator.py:5,24](bank_forecast/src/data/aggregator.py#L5) — `date, transaction_type, count, amount` (günlük) / `+hour` (saatlik) uzun-format DataFrame döndürür; "gerçekleşen vs tahmin" karşılaştırması doğrudan bunlardan beslenecek.
- `models/saved/model_registry.json` zaten 5 işlem tipi için eğitilmiş model bilgisi içeriyor (`best_model`, `cv_rmse`, `feature_importance_top5`, `model_path`...).
- Demo veri: `data/raw/demo.csv` zaten mevcut (`islem_tipi,tarih,saat,islem_hacmi`).

**Önemli**: `model_registry.json`'daki `model_path`/`encoder_path` ve `REGISTRY_FILE`/`config_path` göreli yollardır (örn. `"models/saved/model_registry.json"`, `"models/saved\\EFT_daily_best.pkl"`). Bu yüzden FastAPI süreci **`bank_forecast/` dizininden** (cwd) çalıştırılmalı.

---

## 1. Backend (FastAPI) — `bank_forecast/api/`

Yeni paket, `uvicorn api.main:app --reload --port 8000` ile `bank_forecast/` dizininden çalıştırılır.

**In-memory state** (görseldeki "In-Memory — Sayfa yenilenince sıfırlanır" rozetiyle uyumlu): tek-kullanıcılı yerel araç olduğu için DB/oturum yönetimi yok — `api/state.py` içinde tek bir global `AppState` singleton (`raw_df`, `daily_agg`, `hourly_agg`, `source_filename`, `uploaded_path`, `loaded_at`). Sayfa yenilenince frontend state'i sıfırlanır; backend state'i ise sunucu ayakta kaldığı sürece kalır — `GET /api/dataset/summary` ile yeniden senkronize edilebilir (boşsa "veri yok" döner).

### Endpoint'ler

| Endpoint | Görev |
|---|---|
| `POST /api/upload` | multipart CSV al → geçici dosyaya yaz (`tempfile` veya `data/raw/_uploads/`) → `load_transactions` + `aggregate_daily`/`aggregate_hourly` → `STATE`'e kaydet → özet döndür (`filename, row_count, date_range, transaction_types, per-type counts`) |
| `POST /api/demo-data` | `data/raw/demo.csv`'yi `load_transactions` ile yükle, aynı özet şemasıyla döndür (dosya mevcut, sentetik üretim gerekmiyor) |
| `GET /api/dataset/summary` | Mevcut `STATE` özetini döndürür (yoksa boş/204) — sayfa açılışında üst bar durumunu doldurmak için |
| `POST /api/forecast` | Body: `{start, end, types?, freq?}` → `forecast_pipeline(..., fmt=[], plot=False, registry_path="models/saved/model_registry.json")` çağırır, ardından §2'deki karşılaştırma + toplamları hesaplayıp `{forecast, comparison, totals}` döndürür |
| `POST /api/retrain` | Body: `{freq?, types?}` → `train_pipeline(input_path=STATE.uploaded_path, ...)`'i arka plan thread/`BackgroundTasks` ile başlatır (dakikalar sürebilir), `{status:"started"}` döner |
| `GET /api/retrain/status` | `{status: idle|running|done|error, message}` polling endpoint'i |

### CORS / Proxy
Vite dev server proxy'si birincil çözüm (`vite.config.ts` → `server.proxy['/api'] = 'http://localhost:8000'`), CORS middleware (`allow_origins=["http://localhost:5173"]`) yedek olarak eklenir.

### requirements.txt eklemeleri
`fastapi`, `uvicorn[standard]`, `python-multipart` (dosya yükleme ayrıştırma için zorunlu).

---

## 2. "Gerçekleşen vs Tahmin" Karşılaştırma Mantığı

`/api/forecast` handler'ı içinde, `forecast_pipeline` sonrası, ek aggregation kodu yazmadan tamamen `STATE.daily_agg`/`STATE.hourly_agg` üzerinden:

1. `STATE.daily_agg["date"].between(start, end)` ile seçilen tahmin aralığının geçmiş veriyle **örtüşüp örtüşmediğini** kontrol et.
2. Örtüşme varsa, her `transaction_type` için: `actual_by_date = {date: count}` sözlüğü kur, `forecast_result["by_type"][tt]["daily"]` listesindeki her kayıtla `date` üzerinden eşleştir → `{date, predicted_count, actual_count}` satırları üret (yalnız her iki kaynakta da bulunan tarihler).
3. Saatlik için aynı desen `(date, hour)` ile `STATE.hourly_agg`'a karşı.
4. Dönen yapı: `{"has_overlap": bool, "overlap_range": {...}, "by_type": {tt: [{date, predicted_count, actual_count}, ...]}}`. `has_overlap=False` ise frontend bu grafiği gizler.
5. Aynı handler'da **toplamlar** da hesaplanır: `totals.total_predicted` (seçilen aralık için toplam tahmini kayıt sayısı — kullanıcının "ne kadar kayıt gelecek" sorusunun cevabı), tip bazlı alt toplamlar, `model_used` haritası — böylece frontend büyük dizileri indirgemek zorunda kalmaz.

İsteğe bağlı: `comparison.py` adında ayrı bir yardımcı modülde tutulursa test edilebilirliği artar.

---

## 3. Frontend (React + Vite) — `bank_forecast/frontend/`

`npm create vite@latest frontend -- --template react-ts` ile iskelet oluşturulur (sibling: `src/`, `api/`).

**Kütüphaneler**:
- **Grafik: Recharts** — Plotly sunucu tarafında statik HTML raporları için zaten kullanılıyor, ama özelleştirilmiş koyu temalı interaktif React paneli için Recharts native React bileşenleri sunar, çok daha hafiftir (~100KB vs Plotly.js ~3MB) ve Tailwind ile kolay temalanır.
- **Stil: Tailwind CSS** — görseldeki koyu lacivert tema (`slate-900` arka plan, `slate-800` kart yüzeyleri, sarı/altın aksan rengi — görselde "Tahmin Oluştur" ve "Demo Data Yükle" butonlarında görülüyor) hızlıca uygulanabilir.
- **HTTP**: native `fetch` (axios gereksiz).
- **Tarih seçiciler**: native `<input type="date">`, Tailwind ile stillendirilmiş — görseldeki "Başlangıç"/"Bitiş" sade alanlarla birebir eşleşir.
- **State**: React Context + `useState`/`useReducer` — akış lineer (yükle → aralık seç → tahmin et → sonuç göster), Redux/Zustand gereksiz.

### Bileşen kırılımı (görsel düzene birebir karşılık gelir)
```
frontend/src/
  App.tsx, main.tsx
  api/client.ts          # uploadCsv(), loadDemo(), getSummary(), runForecast(), retrain()
  context/DataContext.tsx
  components/
    TopBar.tsx           # "WFOpt" marka + ev ikonu, "Veri yüklenmedi"/"<dosya> yüklendi", "In-Memory" rozeti
    Sidebar.tsx          # DateRangePicker + UploadDropzone + CreateForecastButton sarmalayıcı
    DateRangePicker.tsx  # "TAHMİN ARALIĞI" — Başlangıç / Bitiş <input type="date">
    UploadDropzone.tsx   # sürükle-bırak alanı + "Dosya Seç" + "Demo Data Yükle" butonu
    CreateForecastButton.tsx  # "Tahmin Oluştur"; veri yokken devre dışı + "Önce CSV yükleyin" ipucu
    ProgressStepper.tsx  # animasyonlu adım listesi (bkz. §4)
    ResultsPanel.tsx     # alt panelleri orkestre eden konteyner
    ModelSummaryCard.tsx     # tip bazlı kullanılan model + CV skor rozetleri
    TotalCountCard.tsx       # seçilen aralık için toplam tahmini kayıt sayısı
    DailyForecastChart.tsx   # güven bandlı (lower_80/upper_80) çizgi/alan grafiği
    HourlyBreakdownChart.tsx # saatlik kırılım — toggle ile açılan ayrı grafik
    ActualVsPredictedChart.tsx  # yalnız comparison.has_overlap === true ise render edilir
    RetrainPanel.tsx     # opsiyonel "yeniden eğit" + durum polling
  styles/ (tailwind giriş css)
```

### Görsel/tema notları
Görseldeki yerleşim birebir korunur: üstte ince bir TopBar (sol marka, sağ durum rozetleri), solda dar bir TAHMİN ARALIĞI sidebar'ı (alt kısımda "Tahmin Oluştur" butonu + ipucu metni), sağda ana panel — başlangıçta yükleme alanı + hoş geldiniz kartı, tahmin sonrası ise sonuç panelleri.

---

## 4. İlerleme Paneli Mekaniği

**Karar: İstemci tarafında animasyonlu/aşamalı ilerleme, gerçek backend polling/SSE yok.**

Gerekçe: `forecast_pipeline` kayıtlı modellerle saniyeler içinde tamamlanır (eğitim yok, sadece feature üretimi + `model.predict`). Gerçek bir WebSocket/SSE kanalı, sub-5-saniyelik bir işlem için backend'e ciddi karmaşıklık ekler (pipeline'ın adım bazlı event yayınlaması gerekir — şu an yok).

Yaklaşım:
1. "Tahmin Oluştur" tıklanınca `ProgressStepper` anında görünür: `["Model yükleniyor", "Özellikler oluşturuluyor", "Tahmin hesaplanıyor", "Grafikler hazırlanıyor"]` — her adım `pending → active → done` arası sabit aralıklarla (400-600ms) geçiş yapar; gerçek `fetch('/api/forecast')` isteği arka planda paralel çalışır.
2. Fetch tamamlanınca kalan adımlar anında "done" işaretlenir ve `ResultsPanel`'e geçilir (animasyon gerçek isteği bloklamaz — istek daha uzun sürerse animasyon onu bekler, daha kısa sürerse animasyon erken biter).
3. Hata durumunda stepper hata durumuna geçer.

İstisna: opsiyonel **yeniden eğitim** gerçekten dakikalar sürer — onun için zaten planlanan `GET /api/retrain/status` polling'i kullanılır (sabit animasyon yanıltıcı olurdu).

---

## 5. Geliştirme Akışı

1. **Backend**: `bank_forecast/` dizininden (göreli yollar nedeniyle önemli) → `pip install -r requirements.txt` (yeni fastapi/uvicorn/python-multipart satırlarıyla) → `uvicorn api.main:app --reload --port 8000`
2. **Frontend**: `frontend/` dizininden → `npm install` → `npm run dev` (Vite, port 5173, `/api` proxy `localhost:8000`'e yönlendirir)
3. Her iki sunucu da paralel terminal pencerelerinde çalışır.

---

## 6. Yeni/Değişecek Dosyalar

**Backend** (`bank_forecast/api/`):
- `__init__.py`, `main.py` (FastAPI app, CORS, router kayıtları)
- `state.py` (global `AppState` singleton)
- `schemas.py` (pydantic modelleri: UploadSummary, ForecastRequest/Response, ComparisonResult, RetrainStatus)
- `routes_data.py` (`/api/upload`, `/api/demo-data`, `/api/dataset/summary`)
- `routes_forecast.py` (`/api/forecast` — `forecast_pipeline` sarmalayıcı + karşılaştırma)
- `routes_train.py` (`/api/retrain`, `/api/retrain/status`)
- `comparison.py` (§2'deki gerçekleşen-vs-tahmin eşleştirme yardımcı fonksiyonları)

**Frontend** (`bank_forecast/frontend/src/`):
- `App.tsx`, `main.tsx`, `api/client.ts`, `context/DataContext.tsx`
- `components/`: `TopBar`, `Sidebar`, `DateRangePicker`, `UploadDropzone`, `CreateForecastButton`, `ProgressStepper`, `ResultsPanel`, `ModelSummaryCard`, `TotalCountCard`, `DailyForecastChart`, `HourlyBreakdownChart`, `ActualVsPredictedChart`, `RetrainPanel`
- `tailwind.config.js`, `postcss.config.js`, `vite.config.ts` (proxy ayarı)

**Değişecek mevcut dosyalar**:
- `bank_forecast/requirements.txt` — `fastapi`, `uvicorn[standard]`, `python-multipart` eklenir
- `bank_forecast/README.md` — "Web Arayüzü" çalıştırma talimatları bölümü eklenir

---

## 7. Doğrulama Planı (uçtan uca manuel test)

1. **Backend smoke test**: `GET /api/dataset/summary` → "veri yok"; `POST /api/demo-data` → `row_count`, `date_range` (`2024-01-02`–`2025-06-30`), 5 işlem tipi içeren özet.
2. **Forecast testi**: `POST /api/forecast` `{"start":"2025-07-01","end":"2025-07-31","freq":"daily"}` → `by_type` her tip için `model_used` (registry ile eşleşmeli, örn. EFT→ridge), `totals.total_predicted` mantıklı pozitif sayı, ve `outputs/forecasts/`'a hiçbir dosya yazılmadığı (fmt=[]/plot=False doğrulaması) kontrol edilir.
3. **Örtüşme testi**: `2025-06-01`–`2025-06-30` (demo veri ile örtüşür) → `comparison.has_overlap == true`, `by_type.<tip>` eşleşen `{date, predicted_count, actual_count}` satırları; `2025-08-01`–`2025-08-31` (örtüşmez) → `has_overlap == false`.
4. **Frontend E2E** (her iki sunucu çalışırken `localhost:5173`):
   - Üst bar başlangıçta "Veri yüklenmedi" gösterir.
   - "Demo Data Yükle" → durum güncellenir, "Tahmin Oluştur" aktif olur, ipucu kaybolur.
   - Demo veriyle örtüşen bir aralık seçip "Tahmin Oluştur" → ilerleme paneli adımları gösterir → sonuç paneli: model kartları, toplam tahmini kayıt sayısı, güven bantlı günlük grafik, saatlik kırılım grafiği (toggle), gerçekleşen-vs-tahmin grafiği görünür.
   - Örtüşmeyen aralık seçilirse karşılaştırma grafiği gizlenir.
   - Sayfa yenilenince üst bar "Veri yüklenmedi"ya döner (in-memory rozeti doğrulanır).
   - (Opsiyonel) "Yeniden eğit" tetiklenir → polling running→done gösterir, registry zaman damgası güncellenir.
