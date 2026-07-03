# Retrain "ilerlemiyor" / donma sorunu — çözüm notu

**Tarih:** 2026-07-03
**Dosya:** `src/pipeline.py` (`_train_unit`, `train_pipeline`)

## Belirti

"Eğitimi Başlat"a basınca eğitim başlıyor ama ilerlemiyormuş gibi görünüyordu
(progress 0'da kalıyor, çok uzun sürüyor).

## Kök neden

`train_pipeline`, her (işlem tipi × frekans) birimi için `ProcessPoolExecutor`
ile ayrı bir process açıyor:

```python
max_workers = min(total_units, os.cpu_count() or 1)
```

Ama her process içindeki LightGBM/XGBoost/RandomForest modelleri de
`config/settings.yaml`'daki `models.n_jobs: -1` yüzünden **kendi başına tüm
çekirdekleri** kullanmaya çalışıyordu. 10 çekirdekli bir makinede, 10 birim
varsa: 10 process × (her biri tüm çekirdekleri isteyen) iç paralellik =
ağır bir aşırı-abonelik (oversubscription). Sonuç: CPU'lar birbirini
bloke ediyor, eğitim donmuş gibi görünüyor.

Ek bir etken: `uvicorn --reload` bir `.py` dosyası kaydedildiğinde sunucuyu
yeniden başlatıyor; bu sırada `ProcessPoolExecutor` düzgün kapanamıyor ve
worker process'leri yetim (orphan, PPID=1) kalarak arka planda CPU/RAM
tüketmeye devam ediyor — sonraki denemeleri de yavaşlatıyor.

## Çözüm

`_train_unit` içinde, worker process'e geçirilen `models_cfg` kopyalanıp
`n_jobs=1` olacak şekilde override edildi — dıştaki paralellik (process
başına bir birim) zaten tüm çekirdekleri kullanıyor, içeride tekrar
paralelleşmeye gerek yok:

```python
models_cfg = {**models_cfg, "n_jobs": 1}
```

## Doğrulama

Demo veriyle (26k satır, 5 tip × 2 frekans = 10 birim) retrain koşuldu:
düzeltmeden önce ilerlemiyor gibiydi, düzeltmeden sonra ~2.5 dakikada
10/10 model başarıyla tamamlandı.

## Not: Yetim process birikimi

Eğitim sürerken backend kodunu (`.py` dosyaları) değiştirip kaydetmeyin —
`uvicorn --reload` sunucuyu yeniden başlatır, bellek-içi state (yüklü CSV
dahil) sıfırlanır ve o anki eğitimin worker process'leri yetim kalır.
Birikmiş yetim process'leri bulmak için:

```bash
ps aux | grep "multiprocessing.spawn" | grep -v grep
```

`PPID` sütunu `1` olanlar yetimdir, güvenle `kill -9` ile temizlenebilir.
