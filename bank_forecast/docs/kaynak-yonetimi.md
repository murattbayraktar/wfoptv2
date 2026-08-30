# Kaynak Yönetimi — Eğitim CPU/Bellek Sınırlaması ve Forecast Bloklaması

Farklı bir sunucuda veya OpenShift gibi kaynak-limitli (cgroup) bir ortamda
devreye alırken CPU/bellek kullanımının stabil ve yönetilebilir kalması için
yapılan düzenleme.

## Sorun

1. **Eğitim havuzu container limitini görmüyordu.** `train_pipeline`
   (`src/pipeline.py`), her (ekip × işlem tipi × frekans) birimini ayrı bir
   process'te (`ProcessPoolExecutor`) eğitir. Havuz boyutu eskiden
   `os.cpu_count()`'a göre belirleniyordu — bu, container'ın cgroup CPU
   kotasını değil **host'un** toplam çekirdek sayısını döner. CPU-limitli bir
   pod'da, birim sayısı arttıkça gereğinden fazla process aynı anda açılır;
   her process pandas/xgboost/lightgbm/sklearn'i sıfırdan import ettiğinden
   (~150-400MB taban bellek) CFS throttling ve OOMKilled riski oluşur.
2. **`/api/forecast` (ve kalibrasyon uçları) API'yi geçici kilitleyebiliyordu.**
   Tahmin üretimi senkron ve CPU-yoğundur; tek process/tek event-loop ile
   çalışan uvicorn'da bu, ağır bir istek sırasında `/api/health` dahil hiçbir
   isteğin yanıt vermemesine yol açar — OpenShift'in liveness/readiness
   probe'u bu sırada pod'u yeniden başlatabilir.

## Çözüm

**Eğitim havuzu artık `resolve_max_workers()` (`src/pipeline.py`) ile
boyutlandırılıyor.** Öncelik sırası:

1. `MAX_TRAIN_WORKERS` ortam değişkeni (elle override)
2. `config/settings.yaml` → `models.max_workers` (elle override)
3. Otomatik tespit — cgroup CPU kotası **ve** cgroup bellek limitinin ikisi
   birden hesaba katılır, hangisi daha kısıtlayıcıysa o kullanılır
   (`models.est_worker_memory_mb`, varsayılan 400MB, süreç başına kaba bellek
   tahmini olarak devreye girer)
4. cgroup dosyaları okunamıyorsa (ör. macOS geliştirme ortamı) sessizce
   `os.cpu_count()`'a düşülür — hata fırlatmaz.

Çözülen değer, Eğitim ekranındaki adım logunda görünür:

> `3 ekip × 2 işlem tipi × 2 frekans = 12 model eğitilecek (2 paralel işçi ile, kaynak: auto:cgroup).`

**`/api/forecast`, `/api/forecast/export` ve kalibrasyon uçları (`/api/calibration/analyze`,
`/multipliers/suggest`, `/preview`)** artık tahmin hesaplamasını `run_in_threadpool`
ile ayrı bir thread'e devrediyor — bu sırada `/api/health` ve diğer istekler
normal yanıt vermeye devam eder.

## Yapılandırma

```yaml
# config/settings.yaml → models:
max_workers: null          # boş = otomatik (cgroup CPU + bellek limiti)
est_worker_memory_mb: 400  # bellek bazlı sınırlama için süreç başı tahmini
```

Ops ekibi, pod'un bellek/CPU limitine göre işçi sayısını elle sabitlemek
isterse ortam değişkeniyle geçersiz kılabilir:

```bash
MAX_TRAIN_WORKERS=2 uvicorn api.main:app --host 0.0.0.0 --port 8000
```

## Kapsam dışı

- OpenShift restricted SCC / rastgele non-root UID için dosya izinleri
- Çoklu replica için paylaşımlı state (`STATE`/`RETRAIN_STATUS` hâlâ in-memory)
- `uvicorn --workers` / çoklu API process
- Hiperparametre arama bütçesi (`cv_folds`, `xgboost_n_iter` vb.)
