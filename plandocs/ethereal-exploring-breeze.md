# WFOpt — "Veri & Model Eğitimi" Ekranı + Adım Adım Eğitim İlerlemesi

## Context

Şu an `bank_forecast/frontend` tek ekranlı bir SPA: TopBar + Sidebar (tarih aralığı + "Tahmin Oluştur") + ana panelde CSV yükleme/demo data alanı + sonuç paneli — hepsi aynı yerde. Kullanıcı bunun karışık olduğunu, asıl tahmin ekranının **sadece öğrenilmiş (kayıtlı) modellerle** istediği tarih aralığı için çalışmasını, CSV yükleme + model eğitimi akışının ise **ayrı bir ekrana** taşınmasını istiyor. O ekranda CSV yüklenince arka planda eğitim otomatik başlamalı ve kullanıcı "hangi aşamadayız / hangi algoritma seçildi" gibi adım adım detayları + bir ilerleme çubuğu görebilmeli.

Backend tarafında bu akış zaten `POST /api/retrain` + `GET /api/retrain/status` ile tasarlanmış ([routes_train.py](bank_forecast/api/routes_train.py)) ama **adım bazlı detay yok** — sadece `status/message/started_at/finished_at`. `train_pipeline` ([pipeline.py:42](bank_forecast/src/pipeline.py#L42)) ve `ModelSelector.select_best` ([model_selector.py:91](bank_forecast/src/models/model_selector.py#L91)) konsola (`rich.console`) zengin adım bilgisi (hangi tip/frekans işleniyor, hangi model deneniyor, skorları, seçilen model + gerekçe) basıyor ama bunu API'ye aktaran bir mekanizma yok. Bu bilgiyi UI'ya taşımak için pipeline'a **opsiyonel `progress_callback` enjekte edip** (varsayılan `None`, CLI davranışı değişmez) event'leri `RETRAIN_STATUS`'a topluyoruz — pipeline yeniden yazılmıyor, sadece anahtar noktalara ek bir callback çağrısı ekleniyor.

Kullanıcı onayı: CSV yüklenince eğitim **otomatik** başlayacak (ayrı bir "Eğitimi Başlat" butonuna gerek yok).

---

## 1. Backend — adım bazlı eğitim ilerlemesi

### 1.1 `state.py` — `RetrainStatus` genişletme
[state.py:31](bank_forecast/api/state.py#L31) içindeki `RetrainStatus`'a ekle:
- `steps: list[dict]` — sıralı event log (`{"at": iso_ts, "kind": ..., "message": <TR insan-okur metin>, ...ek alanlar}`)
- `progress: float` (0.0–1.0)
- `total_units: int`, `completed_units: int` (iç sayaçlar; `progress = completed_units/total_units`)
- `add_step(event: dict)` yardımcı metodu — `at` damgası ekleyip `steps`'e ekler
- `reset()` zaten `__init__`'i çağırıyor, yeni alanları da sıfırlar

### 1.2 `src/models/model_selector.py` — `ModelSelector.select_best` içine event hook
[model_selector.py:91](bank_forecast/src/models/model_selector.py#L91) imzasına `progress_callback: Callable[[dict], None] | None = None` ekle. Mevcut `console.print` çağrılarının yanına (onları silmeden) şu noktalarda çağır:
- döngü başlamadan önce: `{"kind": "selection_start", "type": tt, "freq": f, "candidates": candidates}`
- her `_cv_score` sonucundan sonra (başarı/hata fark etmeksizin): `{"kind": "model_evaluated", "type": tt, "freq": f, "model": model_name, "score": score, "metric": metric}`
- en iyi seçildikten sonra: `{"kind": "model_selected", "type": tt, "freq": f, "model": best_model, "score": best_score, "reason": reason}`

`tt`/`f` parametreleri zaten `select_best`'e `transaction_type`/`freq` olarak geliyor — event'lere ekle.

### 1.3 `src/pipeline.py` — `train_pipeline` içine event hook
[pipeline.py:42](bank_forecast/src/pipeline.py#L42) imzasına `progress_callback: Callable[[dict], None] | None = None` ekle ve şu noktalarda çağır (her biri `if progress_callback:` ile korumalı):
- veri yüklenip doğrulandıktan sonra: `{"kind": "data_ready", "row_count": len(df), "transaction_types": available_types, "data_range": registry["data_range"]}`
- `types`/`freqs` belirlendikten hemen sonra: `{"kind": "plan", "total_units": len(types)*len(freqs), "types": types, "freqs": freqs}` — bu, frontend'de "X/Y tamamlandı" göstermek ve backend'in `total_units`'i seed etmesi için kritik
- her `(transaction_type, f)` döngüsü başında: `{"kind": "unit_start", "type": tt, "freq": f, "index": i, "total": total_units}`
- `selector.select_best(...)` çağrısına `progress_callback=progress_callback` parametresini geçir (pas-through)
- final model eğitilip kaydedildikten sonra: `{"kind": "unit_done", "type": tt, "freq": f, "model": best_model, "cv_rmse": sel_result["best_score"], "feature_importance_top5": top5}`
- registry kaydedildikten sonra: `{"kind": "completed", "registry_path": ...}`

### 1.4 `routes_train.py` — `_run_training` içinde callback + state güncelleme
[routes_train.py:15](bank_forecast/api/routes_train.py#L15) içindeki `_run_training`'i güncelle:
- Başlamadan önce `RETRAIN_STATUS.reset()`'e benzer şekilde `steps`/`progress`/sayaçları sıfırla (mevcut `status="running"` ataması yanına)
- `def _on_event(event: dict)` closure'ı tanımla; `event["kind"]`'e göre **Türkçe, insan-okur `message`** üret (örn. `model_evaluated` → `f"{type} / {freq}: {model} deneniyor — CV RMSE = {score:.2f}"`, `model_selected` → `f"{type} / {freq} için seçilen algoritma: {model} ({reason})"`, `unit_done` → `f"{type} / {freq} tamamlandı — model: {model}, CV RMSE: {cv_rmse:.2f}"`, `plan` → `f"{len(types)} işlem tipi × {len(freqs)} frekans = {total_units} model eğitilecek"`, `data_ready` → `f"{row_count} kayıt yüklendi, {len(types)} işlem tipi tespit edildi"`, `completed` → `"Tüm modeller eğitildi ve kaydedildi"`)
- `plan` event'inde `RETRAIN_STATUS.total_units` set et; `unit_done` event'inde `completed_units += 1` ve `progress = completed_units/total_units`
- her event'i `RETRAIN_STATUS.add_step(event_with_message)` ile logla, `RETRAIN_STATUS.message`'ı en son event'in `message`'ına güncelle
- `train_pipeline(..., progress_callback=_on_event)` çağır
- hata durumunda mevcut `except` bloğu aynen kalır, ek olarak `{"kind": "error", "message": ...}` step'i ekle

### 1.5 `/api/retrain/status` yanıtına yeni alanlar
[routes_train.py:51](bank_forecast/api/routes_train.py#L51) — dönen dict'e `progress`, `steps`, `total_units`, `completed_units` ekle.

---

## 2. Frontend — yeni ekran + gezinme

### 2.1 Ekranlar arası geçiş
Router gerekmez — `App.tsx`'te basit bir `useState<'forecast' | 'training'>('forecast')` ile ekran seçimi yapılır. [TopBar.tsx](bank_forecast/frontend/src/components/TopBar.tsx)'a `screen`/`onScreenChange` prop'ları geçirilip marka biriminin yanına iki sekme butonu eklenir: **"Tahmin"** ve **"Veri & Model Eğitimi"**. Aktif sekme `gold` vurgusuyla işaretlenir (mevcut `gold-500`/`navy` tema renkleri ile, [index.css](bank_forecast/frontend/src/index.css) içindeki `--color-gold-*`/`--color-navy-*` tokenleriyle tutarlı).

### 2.2 `Layout`/`MainContent` ayrımı — `App.tsx`
- `screen === 'forecast'` → mevcut `Sidebar` + `MainContent` (Tahmin akışı) gösterilir, **ancak**:
  - `MainContent`'ten `<UploadDropzone />` kaldırılır
  - `dataset?.loaded === false` durumunda `WelcomeCard` yerine yeni bir **"Veri yüklenmedi"** kartı gösterilir: kısa açıklama + kullanıcıyı "Veri & Model Eğitimi" sekmesine yönlendiren bir buton/link (örn. `onClick={() => onScreenChange('training')}`)
  - `ReadyToForecastCard` (önceki turda eklenen) aynen kalır — artık tek "veri hazır" göstergesi budur
- `screen === 'training'` → yeni `TrainingScreen` bileşeni gösterilir (Sidebar gizlenir — bu ekranda tarih aralığı seçimi anlamsız)

### 2.3 Yeni bileşen: `TrainingScreen.tsx`
İçerik akışı:
1. **`UploadDropzone`** — olduğu gibi taşınır/yeniden kullanılır (CSV sürükle-bırak + "Demo Data Yükle"). `upload`/`loadDemo` zaten `DataContext`'te var, davranışı değişmez.
2. Yükleme başarılı olduğunda (mevcut `dataset.loaded`), **dataset özet kartı**: dosya adı, satır sayısı, tarih aralığı, işlem tipleri (mevcut `ReadyToForecastCard`'daki bilgi gösterim deseniyle tutarlı stil)
3. **Otomatik eğitim tetikleme**: `source_kind === 'upload'` olduğunda (demo data'da `uploaded_path=None`, retrain desteklenmiyor — [routes_train.py:33](bank_forecast/api/routes_train.py#L33)) `DataContext` içinde upload başarılı olur olmaz `api.startRetrain({freq: 'both'})` tetiklenir (kullanıcı onayı: otomatik başlatma). Demo data yüklenirse "Bu örnek veri ile model eğitimi desteklenmiyor — gerçek bir CSV yükleyin" notu gösterilir.
4. **`TrainingProgress`** — eğitim durumu `idle` değilse gösterilir (bkz. §2.4)

### 2.4 Yeni bileşen: `TrainingProgress.tsx`
- `status === 'running'` iken `getRetrainStatus()`'u ~1.2sn aralıkla polling yapar (mevcut `ProgressStepper`'daki `setInterval` deseni referans alınabilir, ama bu kez gerçek backend verisiyle); `status !== 'running'` olduğunda polling durur
- **İlerleme çubuğu**: `progress` (0–1) ile genişliği animasyonlu `div` — `gold-500` arkaplan, `navy-700` track (TopBar/Sidebar'daki `gold`/`navy` paletiyle tutarlı), üstünde `"{completed_units}/{total_units} model eğitildi"` metni
- **Adım listesi**: `steps` dizisini ters kronolojik veya kronolojik sırayla (en güncel altta, otomatik aşağı kaydırma) render eder; her satırda `kind`'e göre ikon (📊 plan, 🧪 model_evaluated, ✅ model_selected/unit_done, 🏁 completed, ⚠️ error) + `message` metni + zaman damgası
- `status === 'done'` olduğunda: başarı banner'ı + `unit_done` event'lerinden türetilmiş özet tablo (işlem tipi / frekans / seçilen algoritma / CV RMSE) — [ModelSummaryCard.tsx](bank_forecast/frontend/src/components/ModelSummaryCard.tsx)'daki "Kullanılan algoritma: X" gösterim deseniyle tutarlı
- `status === 'error'` olduğunda: hata banner'ı + `message`

### 2.5 `types.ts` güncelleme
`RetrainStatus` interface'ine ekle:
```ts
export interface TrainingStep {
  at: string
  kind: string
  message: string
  type?: string
  freq?: string
  model?: string
  score?: number
  metric?: string
  reason?: string
  cv_rmse?: number
  candidates?: string[]
  index?: number
  total?: number
}
// RetrainStatus'a: progress: number; steps: TrainingStep[]; total_units: number; completed_units: number
```

### 2.6 `client.ts`
Değişiklik gerekmez — `startRetrain`/`getRetrainStatus` zaten mevcut ([client.ts:48-60](bank_forecast/frontend/src/api/client.ts#L48-L60)); sadece `RetrainStatus` tip güncellemesi onları kapsar.

### 2.7 `DataContext.tsx`
- Upload akışında (`upload` fonksiyonu, [DataContext.tsx](bank_forecast/frontend/src/context/DataContext.tsx)), başarılı `uploadCsv` sonrası `summary.source_kind === 'upload'` ise `api.startRetrain({freq: 'both'})` çağrılır (hataları sessizce yutmaz — `trainingError` benzeri bir state'e yazılabilir, ama `TrainingProgress` zaten `status==='error'` durumunu da `/retrain/status`'tan okuyacağı için bu çağrının kendisi `try/catch` ile sarılıp sadece konsola loglanması yeterli; `409 Zaten devam eden bir eğitim var` gibi durumlar polling tarafından zaten yansıtılır)
- `loadDemo` akışında retrain tetiklenmez

---

## 3. Doğrulama Planı

1. **Backend smoke test**: `POST /api/upload` (gerçek CSV) → ardından `POST /api/retrain {"freq":"both"}` → `GET /api/retrain/status` polling ile `steps` listesinin `plan → unit_start → selection_start → model_evaluated (xN) → model_selected → unit_done → ... → completed` sırasıyla dolduğunu, `progress`'in 0→1 arası monoton arttığını doğrula
2. **CLI regresyon kontrolü**: `progress_callback=None` (varsayılan) ile `train.py` üzerinden CLI eğitiminin öncekiyle aynı şekilde çalıştığını ve konsol çıktısının değişmediğini doğrula (mevcut `console.print` çağrıları korunduğu için otomatik sağlanır, ama bir kez çalıştırıp teyit et)
3. **Frontend E2E** (her iki sunucu çalışırken):
   - TopBar'da "Tahmin" / "Veri & Model Eğitimi" sekmeleri görünür ve geçiş çalışır
   - "Tahmin" sekmesinde artık CSV yükleme alanı yok; veri yüklenmemişse kullanıcıyı diğer sekmeye yönlendiren kart görünür
   - "Veri & Model Eğitimi" sekmesinde gerçek bir CSV yüklenince: özet kartı belirir, eğitim otomatik başlar, ilerleme çubuğu ve adım adım log canlı güncellenir (her birkaç saniyede yeni satırlar), tamamlanınca özet tablo + "model_registry.json güncellendi" mesajı görünür
   - Demo data yüklenince eğitim tetiklenmez, bilgilendirme notu görünür
   - Eğitim bittikten sonra "Tahmin" sekmesine geçilip yeni eğitilen modellerle tahmin üretilebildiği (registry güncel) doğrulanır
