# Plan: Eğitim Ekranına Holdout Doğrulama + Otomatik Tahmin + MAPE

## Context

Kullanıcı, eğitim ekranına "son N günü eğitime dahil etme" özelliği istiyor. Bu sayede:
- Eğitim verisinden son 10 gün **hariç tutulur** (holdout seti)
- Eğitim tamamlandığında bu 10 gün için **otomatik tahmin** çalışır
- Gerçekleşen vs tahmin karşılaştırılarak **MAPE** hesaplanır ve eğitim ekranında gösterilir

Mevcut MAPE fonksiyonu `bank_forecast/src/evaluation/metrics.py:13`'te hazır. Karşılaştırma altyapısı `bank_forecast/api/comparison.py`'de mevcut. Yalnızca bu ikisini bağlamak ve UI'a yeni seçenek eklemek gerekiyor.

---

## Yapılacak Değişiklikler

### 1. `bank_forecast/api/state.py`
`RetrainStatus` sınıfına iki alan ekle:
```python
self.holdout_days: int = 0
self.holdout_result: dict | None = None
```
`reset()` metodu `__init__`'i çağırdığından otomatik temizlenir.

---

### 2. `bank_forecast/api/schemas.py`
`RetrainRequest`'e ekle:
```python
holdout_days: int = 0   # 0 = devre dışı; >0 = son N günü hariç tut
```

---

### 3. `bank_forecast/src/pipeline.py` — `train_pipeline()`
Parametre ekle: `holdout_days: int = 0`

`validate()` çağrısından ve `available_types` tespitinden **sonra**, `agg_cache` döngüsünden **önce**:
```python
holdout_period = None
if holdout_days > 0:
    max_date = df["date"].max()
    holdout_start = max_date - pd.Timedelta(days=holdout_days - 1)
    holdout_period = {
        "start": str(holdout_start.date()),
        "end": str(max_date.date()),
    }
    df = df[df["date"] < holdout_start].copy()   # eğitim verisi
    if progress_callback:
        progress_callback({
            "kind": "holdout_set",
            "holdout_start": str(holdout_start.date()),
            "holdout_end": str(max_date.date()),
            "holdout_days": holdout_days,
        })
```
`registry` sözlüğüne de ekle: `registry["holdout_period"] = holdout_period`

Return değeri değişmez; `train_pipeline()` zaten registry sözlüğünü döndürüyor.

---

### 4. `bank_forecast/api/routes_train.py`

**`_run_training()` imzası** `holdout_days: int = 0` alacak şekilde güncelle.

Eğitim tamamlandıktan sonra (`RETRAIN_STATUS.status = "done"` atamadan önce), `holdout_days > 0` ise:

```python
# Holdout period için otomatik tahmin + MAPE
from src.pipeline import forecast_pipeline, REGISTRY_FILE
from src.evaluation.metrics import mape as calc_mape
import numpy as np
import pandas as pd

max_date = STATE.daily_agg["date"].max()
holdout_start = max_date - pd.Timedelta(days=holdout_days - 1)

RETRAIN_STATUS.add_step({
    "kind": "holdout_forecast",
    "message": f"Son {holdout_days} gün için doğrulama tahmini hesaplanıyor…",
})

forecast_result = forecast_pipeline(
    start=holdout_start.strftime("%Y-%m-%d"),
    end=max_date.strftime("%Y-%m-%d"),
    freq="daily",
    fmt=[],
    plot=False,
    registry_path=REGISTRY_FILE,
    historical_data={"daily": STATE.daily_agg, "hourly": STATE.hourly_agg},
)

by_type_result = {}
all_y_true, all_y_pred = [], []
for tt, info in forecast_result.get("by_type", {}).items():
    daily_list = info.get("daily", [])
    if not daily_list:
        continue
    actual_subset = STATE.daily_agg[
        (STATE.daily_agg["transaction_type"] == tt) &
        (STATE.daily_agg["date"] >= holdout_start)
    ]
    actual_by_date = dict(zip(
        actual_subset["date"].dt.strftime("%Y-%m-%d"),
        actual_subset["count"].astype(float),
    ))
    rows, y_true, y_pred = [], [], []
    for entry in daily_list:
        d = entry["date"]
        if d in actual_by_date:
            actual = actual_by_date[d]
            predicted = entry["predicted_count"]
            rows.append({"date": d, "actual": round(actual, 1), "predicted": round(predicted, 1)})
            y_true.append(actual); y_pred.append(predicted)
    mape_val = calc_mape(np.array(y_true), np.array(y_pred)) if y_true else None
    by_type_result[tt] = {"mape": round(mape_val, 2) if mape_val else None, "rows": rows}
    all_y_true.extend(y_true); all_y_pred.extend(y_pred)

overall = calc_mape(np.array(all_y_true), np.array(all_y_pred)) if all_y_true else None
RETRAIN_STATUS.holdout_result = {
    "holdout_range": {
        "start": holdout_start.strftime("%Y-%m-%d"),
        "end": max_date.strftime("%Y-%m-%d"),
    },
    "by_type": by_type_result,
    "overall_mape": round(overall, 2) if overall else None,
}
RETRAIN_STATUS.add_step({
    "kind": "holdout_done",
    "message": f"Doğrulama tamamlandı — Genel MAPE: {overall:.1f}%" if overall else "Doğrulama tamamlandı.",
})
```

**`_on_event()`** fonksiyonuna "holdout_set" ve "holdout_done" mesaj biçimlendirmesi ekle.

**`/api/retrain` endpoint'i**: `req.holdout_days`'i `_run_training`'e ilet.

**`/api/retrain/status` endpoint'i**: yanıta `holdout_result` ekle.

---

### 5. `bank_forecast/frontend/src/types.ts`

```typescript
export interface HoldoutRow {
  date: string
  actual: number
  predicted: number
}

export interface HoldoutTypeResult {
  mape: number | null
  rows: HoldoutRow[]
}

export interface HoldoutResult {
  holdout_range: DateRange
  by_type: Record<string, HoldoutTypeResult>
  overall_mape: number | null
}
```

`RetrainStatus` arayüzüne ekle: `holdout_result?: HoldoutResult | null`

---

### 6. `bank_forecast/frontend/src/api/client.ts`
`startRetrain` params'a ekle: `holdout_days?: number`

---

### 7. `bank_forecast/frontend/src/context/DataContext.tsx`
- `holdoutDays: number` state'i ekle (varsayılan: `0`)
- `setHoldoutDays: (v: number) => void` ekle
- `startTraining()`'de `holdout_days: holdoutDays` olarak `startRetrain`'e ilet
- Context value'a `holdoutDays` ve `setHoldoutDays` ekle

---

### 8. `bank_forecast/frontend/src/components/TrainingScreen.tsx`
**DatasetSummaryCard** içinde "Eğitimi Başlat" butonunun üstüne bir seçenek grubu ekle:

```
Doğrulama için son günler:
  ○ Yok  ● 10 gün  ○ 30 gün
```
(radio button veya segmented control)

**TrainingProgress** bileşeninde `status === 'done'` bloğuna yeni bölüm:
- `holdout_result` varsa → "Doğrulama Sonuçları (MAPE)" başlığı altında tablo:
  - Kolonlar: İşlem Tipi | Dönem | MAPE% | Yorum (iyi/kabul/zayıf)
  - Alt satır: Genel MAPE

---

## Doğrulama / Test Adımları

1. Backend başlat: `uvicorn api.main:app --reload --port 8000` (bank_forecast/ dizininden)
2. Frontend başlat: `npm run dev` (frontend/ dizininden)
3. CSV yükle → "10 gün" seçeneğini seç → "Eğitimi Başlat" 
4. Eğitim log'unda `holdout_set` adımının göründüğünü kontrol et
5. Eğitim bittikten sonra `holdout_forecast` ve `holdout_done` adımlarını doğrula
6. Eğitim tamamlandı panelinde MAPE tablosunun göründüğünü ve değerlerin mantıklı olduğunu doğrula
7. `GET /api/retrain/status` ile `holdout_result` alanının dolu geldiğini kontrol et
