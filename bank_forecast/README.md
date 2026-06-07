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
tarih,saat,islem_tipi,adet,tutar
2024-01-15,09,EFT,142,2850000
2024-01-15,10,Havale,87,950000
```

## Modeller

| Model | Kullanım Durumu |
|---|---|
| XGBoost | Güçlü trend + haftalık mevsimsellik |
| LightGBM | Yüksek takvim hassasiyeti |
| RandomForest | Stabil, düşük varyans |
| Holt-Winters | Az veri / basit mevsimsellik |
| Ridge | Yalnızca takvim etkisi (baseline) |

Model seçimi otomatik: her `(işlem_tipi, frekans)` çifti için walk-forward CV ile en iyi model seçilir.
