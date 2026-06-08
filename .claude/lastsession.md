
d:\Projects\wfoptv2\bank_forecast\README.md
eğitim için tüm modelleri çalıştırmak uzun sürüyor bu nedenle bu seçimi data yüklerken seçebileyim. Hepsini seçersem mevcut akış devam ama spesifik birini seçersem sadece onunla ilerle. Ek olarak günlük tahminler gerçekleşene yakındı fakat saatlik gösterim de çok fark vardı bunu da araştır ve düzelt.
Bash List bank_forecast directory files
IN
find "d:/Projects/wfoptv2/bank_forecast" -maxdepth 2 -type f | head -100

OUT
d:/Projects/wfoptv2/bank_forecast/api/comparison.py
d:/Projects/wfoptv2/bank_forecast/api/main.py
d:/Projects/wfoptv2/bank_forecast/api/routes_data.py
d:/Projects/wfoptv2/bank_forecast/api/routes_forecast.py
d:/Projects/wfoptv2/bank_forecast/api/routes_train.py
d:/Projects/wfoptv2/bank_forecast/api/schemas.py
d:/Projects/wfoptv2/bank_forecast/api/state.py
d:/Projects/wfoptv2/bank_forecast/api/__init__.py
d:/Projects/wfoptv2/bank_forecast/config/settings.yaml
d:/Projects/wfoptv2/bank_forecast/evaluate.py
d:/Projects/wfoptv2/bank_forecast/forecast.py
d:/Projects/wfoptv2/bank_forecast/frontend/.gitignore
d:/Projects/wfoptv2/bank_forecast/frontend/eslint.config.js
d:/Projects/wfoptv2/bank_forecast/frontend/index.html
d:/Projects/wfoptv2/bank_forecast/frontend/package-lock.json
d:/Projects/wfoptv2/bank_forecast/frontend/package.json
d:/Projects/wfoptv2/bank_forecast/frontend/README.md
d:/Projects/wfoptv2/bank_forecast/frontend/tsconfig.app.json
d:/Projects/wfoptv2/bank_forecast/frontend/tsconfig.json
d:/Projects/wfoptv2/bank_forecast/frontend/tsconfig.node.json
d:/Projects/wfoptv2/bank_forecast/frontend/vite.config.ts
d:/Projects/wfoptv2/bank_forecast/README.md
d:/Projects/wfoptv2/bank_forecast/requirements.txt
d:/Projects/wfoptv2/bank_forecast/scripts/generate_demo_data.py
d:/Projects/wfoptv2/bank_forecast/src/pipeline.py
d:/Projects/wfoptv2/bank_forecast/src/__init__.py
d:/Projects/wfoptv2/bank_forecast/train.py
d:/Projects/wfoptv2/bank_forecast/uvicorn.log
d:/Projects/wfoptv2/bank_forecast/venv/.gitignore
d:/Projects/wfoptv2/bank_forecast/venv/pyvenv.cfg
Read d:\Projects\wfoptv2\bank_forecast\README.md
Read d:\Projects\wfoptv2\bank_forecast\api\routes_train.py, d:\Projects\wfoptv2\bank_forecast\src\pipeline.py
Read d:\Projects\wfoptv2\bank_forecast\api\schemas.py
Bash List model and frontend src files
IN
find "d:/Projects/wfoptv2/bank_forecast/src/models" -type f; find "d:/Projects/wfoptv2/bank_forecast/frontend/src" -type f | head -100

OUT
d:/Projects/wfoptv2/bank_forecast/src/models/base_model.py
d:/Projects/wfoptv2/bank_forecast/src/models/holt_winters_model.py
d:/Projects/wfoptv2/bank_forecast/src/models/lightgbm_model.py
d:/Projects/wfoptv2/bank_forecast/src/models/model_selector.py
d:/Projects/wfoptv2/bank_forecast/src/models/random_forest_model.py
d:/Projects/wfoptv2/bank_forecast/src/models/ridge_model.py
d:/Projects/wfoptv2/bank_forecast/src/models/xgboost_model.py
d:/Projects/wfoptv2/bank_forecast/src/models/__init__.py
d:/Projects/wfoptv2/bank_forecast/src/models/__pycache__/base_model.cpython-314.pyc
d:/Projects/wfoptv2/bank_forecast/src/models/__pycache__/holt_winters_model.cpython-314.pyc
d:/Projects/wfoptv2/bank_forecast/src/models/__pycache__/lightgbm_model.cpython-314.pyc
d:/Projects/wfoptv2/bank_forecast/src/models/__pycache__/model_selector.cpython-314.pyc
d:/Projects/wfoptv2/bank_forecast/src/models/__pycache__/random_forest_model.cpython-314.pyc
d:/Projects/wfoptv2/bank_forecast/src/models/__pycache__/ridge_model.cpython-314.pyc
d:/Projects/wfoptv2/bank_forecast/src/models/__pycache__/xgboost_model.cpython-314.pyc
d:/Projects/wfoptv2/bank_forecast/src/models/__pycache__/__init__.cpython-314.pyc
d:/Projects/wfoptv2/bank_forecast/frontend/src/api/client.ts
d:/Projects/wfoptv2/bank_forecast/frontend/src/App.tsx
d:/Projects/wfoptv2/bank_forecast/frontend/src/components/ActualVsPredictedChart.tsx
d:/Projects/wfoptv2/bank_forecast/frontend/src/components/CreateForecastButton.tsx
d:/Projects/wfoptv2/bank_forecast/frontend/src/components/DailyForecastChart.tsx
d:/Projects/wfoptv2/bank_forecast/frontend/src/components/DateRangePicker.tsx
d:/Projects/wfoptv2/bank_forecast/frontend/src/components/HourlyBreakdownChart.tsx
d:/Projects/wfoptv2/bank_forecast/frontend/src/components/ModelSummaryCard.tsx
d:/Projects/wfoptv2/bank_forecast/frontend/src/components/ProgressStepper.tsx
d:/Projects/wfoptv2/bank_forecast/frontend/src/components/ResultsPanel.tsx
d:/Projects/wfoptv2/bank_forecast/frontend/src/components/Sidebar.tsx
d:/Projects/wfoptv2/bank_forecast/frontend/src/components/TopBar.tsx
d:/Projects/wfoptv2/bank_forecast/frontend/src/components/TotalCountCard.tsx
d:/Projects/wfoptv2/bank_forecast/frontend/src/components/TrainingProgress.tsx
d:/Projects/wfoptv2/bank_forecast/frontend/src/components/TrainingScreen.tsx
d:/Projects/wfoptv2/bank_forecast/frontend/src/components/UploadDropzone.tsx
d:/Projects/wfoptv2/bank_forecast/frontend/src/context/DataContext.tsx
d:/Projects/wfoptv2/bank_forecast/frontend/src/index.css
d:/Projects/wfoptv2/bank_forecast/frontend/src/main.tsx
d:/Projects/wfoptv2/bank_forecast/frontend/src/types.ts
Read d:\Projects\wfoptv2\bank_forecast\src\models\model_selector.py
Read d:\Projects\wfoptv2\bank_forecast\frontend\src\components\UploadDropzone.tsx
Read d:\Projects\wfoptv2\bank_forecast\frontend\src\context\DataContext.tsx
Read d:\Projects\wfoptv2\bank_forecast\frontend\src\api\client.ts
Read d:\Projects\wfoptv2\bank_forecast\frontend\src\components\TrainingScreen.tsx
Read d:\Projects\wfoptv2\bank_forecast\frontend\src\types.ts
Read d:\Projects\wfoptv2\bank_forecast\api\comparison.py
Bash List data and feature module files
IN
find "d:/Projects/wfoptv2/bank_forecast/src/data" "d:/Projects/wfoptv2/bank_forecast/src/features" -type f -name "*.py"

OUT
d:/Projects/wfoptv2/bank_forecast/src/data/aggregator.py
d:/Projects/wfoptv2/bank_forecast/src/data/loader.py
d:/Projects/wfoptv2/bank_forecast/src/data/validator.py
d:/Projects/wfoptv2/bank_forecast/src/data/__init__.py
d:/Projects/wfoptv2/bank_forecast/src/features/calendar_features.py
d:/Projects/wfoptv2/bank_forecast/src/features/feature_pipeline.py
d:/Projects/wfoptv2/bank_forecast/src/features/lag_features.py
d:/Projects/wfoptv2/bank_forecast/src/features/seasonal_features.py
d:/Projects/wfoptv2/bank_forecast/src/features/__init__.py
Read d:\Projects\wfoptv2\bank_forecast\src\data\aggregator.py, d:\Projects\wfoptv2\bank_forecast\frontend\src\components\HourlyBreakdownChart.tsx
Read d:\Projects\wfoptv2\bank_forecast\frontend\src\components\ActualVsPredictedChart.tsx
Read d:\Projects\wfoptv2\bank_forecast\frontend\src\components\ResultsPanel.tsx
Read d:\Projects\wfoptv2\bank_forecast\src\features\feature_pipeline.py
Read d:\Projects\wfoptv2\bank_forecast\src\features\lag_features.py, d:\Projects\wfoptv2\bank_forecast\src\features\seasonal_features.py
Read d:\Projects\wfoptv2\bank_forecast\api\routes_forecast.py
Read d:\Projects\wfoptv2\bank_forecast\api\state.py
Read d:\Projects\wfoptv2\bank_forecast\src\features\calendar_features.py
Read d:\Projects\wfoptv2\bank_forecast\forecast.py
Bash Check trained models, data, and config
IN
cd "d:/Projects/wfoptv2/bank_forecast" && ls models/saved 2>/dev/null; ls data/raw 2>/dev/null; cat config/settings.yaml 2>/dev/null | head -80

OUT
EFT_daily_best.pkl
EFT_daily_encoder.pkl
EFT_hourly_best.pkl
EFT_hourly_encoder.pkl
Havale_daily_best.pkl
Havale_daily_encoder.pkl
Havale_hourly_best.pkl
Havale_hourly_encoder.pkl
Kredi Ãdemesi_daily_best.pkl
Kredi Ãdemesi_daily_encoder.pkl
Kredi Ãdemesi_hourly_best.pkl
Kredi Ãdemesi_hourly_encoder.pkl
Mevduat_daily_best.pkl
Mevduat_daily_encoder.pkl
Mevduat_hourly_best.pkl
Mevduat_hourly_encoder.pkl
model_registry.json
Ãek Tahsilat_daily_best.pkl
Ãek Tahsilat_daily_encoder.pkl
Ãek Tahsilat_hourly_best.pkl
Ãek Tahsilat_hourly_encoder.pkl
_uploads
demo.csv
data:
  date_formats: ["%Y-%m-%d", "%d.%m.%Y", "%d/%m/%Y", "%Y%m%d"]
  working_hours: [7, 18]
  min_training_days: 60

features:
  lag_days_daily: [1, 2, 3, 5, 7, 14, 21, 28]
  lag_hours_hourly: [1, 2, 3, 24, 48, 168]
  rolling_windows_daily: [7, 14, 30]
  fourier_weekly_terms: 3
  fourier_yearly_terms: 5

models:
  cv_folds: 5
  cv_metric: rmse
  random_state: 42
  n_jobs: -1
  xgboost_n_iter: 30
  lightgbm_n_iter: 30
  rf_n_iter: 20

forecast:
  confidence_method: quantile
  confidence_level: 0.80
  max_horizon_daily: 90
  max_horizon_hourly: 30

output:
  float_precision: 1
  include_feature_importance: true
Bash
IN
cd "d:/Projects/wfoptv2/bank_forecast" && python -c "
import json
with open('models/saved/model_registry.json', encoding='utf-8') as f:
    r = json.load(f)
for k, v in r['models'].items():
    print(k, '->', v['best_model'], 'cv_rmse=', round(v['cv_rmse'],3), 'top5=', v['feature_importance_top5'])
"

OUT
EFT_daily -> random_forest cv_rmse= 306.817 top5= ['day_of_week', 'is_weekend', 'sin_7_1', 'sin_7_3', 'lag_14']
EFT_hourly -> random_forest cv_rmse= 74.994 top5= ['lag_168', 'lag_1', 'sin_24_2', 'day_of_week', 'is_weekend']
Bash
IN
cd "d:/Projects/wfoptv2/bank_forecast" && python -c "
import pandas as pd, numpy as np, json, joblib
from src.pipeline import load_config, _load_registry
from src.data.loader import load_transactions
from src.data.aggregator import aggregate_daily, aggregate_hourly
from src.features.feature_pipeline import build_features, get_feature_matrix
from src.models.base_model import BaseForecaster

cfg = load_config()
df = load_transactions('data/raw/demo.csv')
hourly = aggregate_hourly(df, working_hours=tuple(cfg['data']['working_hours']))
sub = hourly[hourly['transaction_type']=='EFT'].copy()
print('hourly rows', len(sub), 'date range', sub.date.min(), sub.date.max())

# pick a forecast window near the end that overlaps with data (last 5 days)
end_date = sub['date'].max()
start_date = end_date - pd.Timedelta(days=4)
print('forecast window', start_date.date(), end_date.date())

actual_window = sub[(sub.date>=start_date)&(sub.date<=end_date)]
print('actual count stats in window:')
print(actual_window['count'].describe())

# what would lag_1 and lag_168 actually be at the start of this window (last known values)?
sub_sorted = sub.sort_values(['date','hour']).reset_index(drop=True)
# index of first row in window
first_idx = sub_sorted[(sub_sorted.date==start_date)].index.min()
print('lag_1 actual (prev row count):', sub_sorted.loc[first_idx-1,'count'])
print('lag_168 actual (168 rows back):', sub_sorted.loc[first_idx-168,'count'])
print('median count overall:', sub_sorted['count'].median())
"

OUT
hourly rows 6552 date range 2024-01-02 00:00:00 2025-06-30 00:00:00
forecast window 2025-06-26 2025-06-30
actual count stats in window:
count    60.000000
mean     20.416667
std      25.210498
min       0.000000
25%       0.000000
50%       8.000000
75%      34.000000
max      84.000000
Name: count, dtype: float64
lag_1 actual (prev row count): 11
lag_168 actual (168 rows back): 11
median count overall: 7.0
Bash
IN
cd "d:/Projects/wfoptv2/bank_forecast" && python -c "
import pandas as pd, numpy as np
from src.pipeline import forecast_pipeline
from src.data.loader import load_transactions
from src.data.aggregator import aggregate_daily, aggregate_hourly
from src.pipeline import load_config
import api.state as st

cfg = load_config()
df = load_transactions('data/raw/demo.csv')
daily = aggregate_daily(df)
hourly = aggregate_hourly(df, working_hours=tuple(cfg['data']['working_hours']))

start, end = '2025-06-26','2025-06-30'
res = forecast_pipeline(start=start, end=end, types=['EFT'], freq='both', fmt=[], plot=False)

# daily compare
d_pred = {e['date']: e['predicted_count'] for e in res['by_type']['EFT']['daily']}
d_act = daily[(daily.transaction_type=='EFT')&(daily.date.between(start,end))].set_index(daily.date.dt.strftime('%Y-%m-%d'))['count']
print('--- DAILY ---')
for dt in d_pred:
    if dt in d_act.index:
        print(dt, 'pred=', d_pred[dt], 'actual=', d_act[dt])

print()
print('--- HOURLY (first 2 days) ---')
h_pred = res['by_type']['EFT']['hourly']
hourly_sub = hourly[(hourly.transaction_type=='EFT')]
for dt in sorted(h_pred.keys())[:2]:
    for entry in h_pred[dt]:
        h = entry['hour']
        row = hourly_sub[(hourly_sub.date==pd.Timestamp(dt))&(hourly_sub.hour==h)]
        actual = int(row['count'].iloc[0]) if len(row) else None
        print(dt, f'{h:02d}:00', 'pred=', entry['count'], 'actual=', actual)
"

OUT
Exit code 1
D:\Projects\wfoptv2\bank_forecast\venv\Lib\site-packages\sklearn\utils\validation.py:2820: UserWarning: X has feature names, but DecisionTreeRegressor was fitted without feature names
  warnings.warn(
D:\Projects\wfoptv2\bank_forecast\venv\Lib\site-packages\sklearn\utils\validation.py:2820: UserWarning: X has feature names, but DecisionTreeRegressor was fitted without feature names
  warnings.warn(
D:\Projects\wfoptv2\bank_forecast\venv\Lib\site-packages\sklearn\utils\validation.py:2820: UserWarning: X has feature names, but DecisionTreeRegressor was fitted without feature names
  warnings.warn(
D:\Projects\wfoptv2\bank_forecast\venv\Lib\site-packages\sklearn\utils\validation.py:2820: UserWarning: X has feature names, but DecisionTreeRegressor was fitted without feature names
  warnings.warn(
D:\Projects\wfoptv2\bank_forecast\venv\Lib\site-packages\sklearn\utils\validation.py:2820: UserWarning: X has feature names, but DecisionTreeRegressor was fitted without feature names
  warnings.warn(
D:\Projects\wfoptv2\bank_forecast\venv\Lib\site-packages\sklearn\utils\validation.py:2820: UserWarning: X has feature names, but DecisionTreeRegressor was fitted without feature names
  warnings.warn(
D:\Projects\wfoptv2\bank_forecast\venv\Lib\site-packages\sklearn\utils\validation.py:2820: UserWarning: X has feature names, but DecisionTreeRegressor was fitted without feature names
  warnings.warn(
D:\Projects\wfoptv2\bank_forecast\venv\Lib\site-packages\sklearn\utils\validation.py:2820: UserWarning: X has feature names, but DecisionTreeRegressor was fitted without feature names
  warnings.warn(
D:\Projects\wfoptv2\bank_forecast\venv\Lib\site-packages\sklearn\utils\validation.py:2820: UserWarning: X has feature names, but DecisionTreeRegressor was fitted without feature names
  warnings.warn(
D:\Projects\wfoptv2\bank_forecast\venv\Lib\site-packages\sklearn\utils\validation.py:2820: UserWarning: X has feature names, but DecisionTreeRegressor was fitted without feature names
  warnings.warn(
D:\Projects\wfoptv2\bank_forecast\venv\Lib\site-packages\sklearn\utils\validation.py:2820: UserWarning: X has feature names, but DecisionTreeRegressor was fitted without feature names
  warnings.warn(
D:\Projects\wfoptv2\bank_forecast\venv\Lib\site-packages\sklearn\utils\validation.py:2820: UserWarning: X has feature names, but DecisionTreeRegressor was fitted without feature names
  warnings.warn(
D:\Projects\wfoptv2\bank_forecast\venv\Lib\site-packages\sklearn\utils\validation.py:2820: UserWarning: X has feature names, but DecisionTreeRegressor was fitted without feature names
  warnings.warn(
D:\Projects\wfoptv2\bank_forecast\venv\Lib\site-packages\sklearn\utils\validation.py:2820: UserWarning: X has feature names, but DecisionTreeRegressor was fitted without feature names
  warnings.warn(
D:\Projects\wfoptv2\bank_forecast\venv\Lib\site-packages\sklearn\utils\validation.py:2820: UserWarning: X has feature names, but DecisionTreeRegressor was fitted without feature names
  warnings.warn(
D:\Projects\wfoptv2\bank_forecast\venv\Lib\site-packages\sklearn\utils\validation.py:2820: UserWarning: X has feature names, but DecisionTreeRegressor was fitted without feature names
  warnings.warn(
D:\Projects\wfoptv2\bank_forecast\venv\Lib\site-packages\sklearn\utils\validation.py:2820: UserWarning: X has feature names, but DecisionTreeRegressor was fitted without feature names
  warnings.warn(
D:\Projects\wfoptv2\bank_forecast\venv\Lib\site-packages\sklearn\utils\validation.py:2820: UserWarning: X has feature names, but DecisionTreeRegressor was fitted without feature names
  warnings.warn(
D:\Projects\wfoptv2\bank_forecast\venv\Lib\site-packages\sklearn\utils\validation.py:2820: UserWarning: X has feature names, but DecisionTreeRegressor was fitted without feature names
  warnings.warn(
D:\Projects\wfoptv2\bank_forecast\venv\Lib\site-packages\sklearn\utils\validation.py:2820: UserWarning: X has feature names, but DecisionTreeRegressor was fitted without feature names
  warnings.warn(
D:\Projects\wfoptv2\bank_forecast\venv\Lib\site-packages\sklearn\utils\validation.py:2820: UserWarning: X has feature names, but DecisionTreeRegressor was fitted without feature names
  warnings.warn(
D:\Projects\wfoptv2\bank_forecast\venv\Lib\site-packages\sklearn\utils\validation.py:2820: UserWarning: X has feature names, but DecisionTreeRegressor was fitted without feature names
  warnings.warn(
D:\Projects\wfoptv2\bank_forecast\venv\Lib\site-packages\sklearn\utils\validation.py:2820: UserWarning: X has feature names, but DecisionTreeRegressor was fitted without feature names
  warnings.warn(
D:\Projects\wfoptv2\bank_forecast\venv\Lib\site-packages\sklearn\utils\validation.py:2820: UserWarning: X has feature names, but DecisionTreeRegressor was fitted without feature names
  warnings.warn(
D:\Projects\wfoptv2\bank_forecast\venv\Lib\site-packages\sklearn\utils\validation.py:2820: UserWarning: X has featur

... [20012 characters truncated] ...

st\venv\Lib\site-packages\sklearn\utils\validation.py:2820: UserWarning: X has feature names, but DecisionTreeRegressor was fitted without feature names
  warnings.warn(
D:\Projects\wfoptv2\bank_forecast\venv\Lib\site-packages\sklearn\utils\validation.py:2820: UserWarning: X has feature names, but DecisionTreeRegressor was fitted without feature names
  warnings.warn(
D:\Projects\wfoptv2\bank_forecast\venv\Lib\site-packages\sklearn\utils\validation.py:2820: UserWarning: X has feature names, but DecisionTreeRegressor was fitted without feature names
  warnings.warn(
D:\Projects\wfoptv2\bank_forecast\venv\Lib\site-packages\sklearn\utils\validation.py:2820: UserWarning: X has feature names, but DecisionTreeRegressor was fitted without feature names
  warnings.warn(
D:\Projects\wfoptv2\bank_forecast\venv\Lib\site-packages\sklearn\utils\validation.py:2820: UserWarning: X has feature names, but DecisionTreeRegressor was fitted without feature names
  warnings.warn(
D:\Projects\wfoptv2\bank_forecast\venv\Lib\site-packages\sklearn\utils\validation.py:2820: UserWarning: X has feature names, but DecisionTreeRegressor was fitted without feature names
  warnings.warn(
D:\Projects\wfoptv2\bank_forecast\venv\Lib\site-packages\sklearn\utils\validation.py:2820: UserWarning: X has feature names, but DecisionTreeRegressor was fitted without feature names
  warnings.warn(
D:\Projects\wfoptv2\bank_forecast\venv\Lib\site-packages\sklearn\utils\validation.py:2820: UserWarning: X has feature names, but DecisionTreeRegressor was fitted without feature names
  warnings.warn(
D:\Projects\wfoptv2\bank_forecast\venv\Lib\site-packages\sklearn\utils\validation.py:2820: UserWarning: X has feature names, but DecisionTreeRegressor was fitted without feature names
  warnings.warn(
D:\Projects\wfoptv2\bank_forecast\venv\Lib\site-packages\sklearn\utils\validation.py:2820: UserWarning: X has feature names, but DecisionTreeRegressor was fitted without feature names
  warnings.warn(
D:\Projects\wfoptv2\bank_forecast\venv\Lib\site-packages\sklearn\utils\validation.py:2820: UserWarning: X has feature names, but DecisionTreeRegressor was fitted without feature names
  warnings.warn(
D:\Projects\wfoptv2\bank_forecast\venv\Lib\site-packages\sklearn\utils\validation.py:2820: UserWarning: X has feature names, but DecisionTreeRegressor was fitted without feature names
  warnings.warn(
D:\Projects\wfoptv2\bank_forecast\venv\Lib\site-packages\sklearn\utils\validation.py:2820: UserWarning: X has feature names, but DecisionTreeRegressor was fitted without feature names
  warnings.warn(
D:\Projects\wfoptv2\bank_forecast\venv\Lib\site-packages\sklearn\utils\validation.py:2820: UserWarning: X has feature names, but DecisionTreeRegressor was fitted without feature names
  warnings.warn(
D:\Projects\wfoptv2\bank_forecast\venv\Lib\site-packages\sklearn\utils\validation.py:2820: UserWarning: X has feature names, but DecisionTreeRegressor was fitted without feature names
  warnings.warn(
D:\Projects\wfoptv2\bank_forecast\venv\Lib\site-packages\sklearn\utils\validation.py:2820: UserWarning: X has feature names, but DecisionTreeRegressor was fitted without feature names
  warnings.warn(
D:\Projects\wfoptv2\bank_forecast\venv\Lib\site-packages\sklearn\utils\validation.py:2820: UserWarning: X has feature names, but DecisionTreeRegressor was fitted without feature names
  warnings.warn(
D:\Projects\wfoptv2\bank_forecast\venv\Lib\site-packages\sklearn\utils\validation.py:2820: UserWarning: X has feature names, but DecisionTreeRegressor was fitted without feature names
  warnings.warn(
D:\Projects\wfoptv2\bank_forecast\venv\Lib\site-packages\sklearn\utils\validation.py:2820: UserWarning: X has feature names, but DecisionTreeRegressor was fitted without feature names
  warnings.warn(
D:\Projects\wfoptv2\bank_forecast\venv\Lib\site-packages\sklearn\utils\validation.py:2820: UserWarning: X has feature names, but DecisionTreeRegressor was fitted without feature names
  warnings.warn(
D:\Projects\wfoptv2\bank_forecast\venv\Lib\site-packages\sklearn\utils\validation.py:2820: UserWarning: X has feature names, but DecisionTreeRegressor was fitted without feature names
  warnings.warn(
D:\Projects\wfoptv2\bank_forecast\venv\Lib\site-packages\sklearn\utils\validation.py:2820: UserWarning: X has feature names, but DecisionTreeRegressor was fitted without feature names
  warnings.warn(
D:\Projects\wfoptv2\bank_forecast\venv\Lib\site-packages\sklearn\utils\validation.py:2820: UserWarning: X has feature names, but DecisionTreeRegressor was fitted without feature names
  warnings.warn(
D:\Projects\wfoptv2\bank_forecast\venv\Lib\site-packages\sklearn\utils\validation.py:2820: UserWarning: X has feature names, but DecisionTreeRegressor was fitted without feature names
  warnings.warn(
D:\Projects\wfoptv2\bank_forecast\venv\Lib\site-packages\sklearn\utils\validation.py:2820: UserWarning: X has feature names, but DecisionTreeRegressor was fitt
Bash
IN
cd "d:/Projects/wfoptv2/bank_forecast" && python -W ignore -c "
import warnings; warnings.filterwarnings('ignore')
import pandas as pd, numpy as np
from src.pipeline import forecast_pipeline
from src.data.loader import load_transactions
from src.data.aggregator import aggregate_daily, aggregate_hourly
from src.pipeline import load_config

cfg = load_config()
df = load_transactions('data/raw/demo.csv')
daily = aggregate_daily(df)
hourly = aggregate_hourly(df, working_hours=tuple(cfg['data']['working_hours']))

start, end = '2025-06-26','2025-06-30'
res = forecast_pipeline(start=start, end=end, types=['EFT'], freq='both', fmt=[], plot=False)
" 2> nul

OUT
(Bash completed with no output)
Bash
IN
cd "d:/Projects/wfoptv2/bank_forecast" && python -W ignore -c "
import warnings; warnings.filterwarnings('ignore')
import sys, io
import pandas as pd, numpy as np
from src.pipeline import forecast_pipeline
from src.data.loader import load_transactions
from src.data.aggregator import aggregate_daily, aggregate_hourly
from src.pipeline import load_config

cfg = load_config()
df = load_transactions('data/raw/demo.csv')
daily = aggregate_daily(df)
hourly = aggregate_hourly(df, working_hours=tuple(cfg['data']['working_hours']))

start, end = '2025-06-26','2025-06-30'

# silence rich console prints by redirecting stdout temporarily during the call
old_stdout = sys.stdout
sys.stdout = io.StringIO()
try:
    res = forecast_pipeline(start=start, end=end, types=['EFT'], freq='both', fmt=[], plot=False)
finally:
    sys.stdout = old_stdout

with open('zz_out.txt','w', encoding='utf-8') as out:
    d_pred = {e['date']: e['predicted_count'] for e in res['by_type']['EFT']['daily']}
    d_act = daily[(daily.transaction_type=='EFT')&(daily.date.between(start,end))].set_index(daily.date.dt.strftime('%Y-%m-%d'))['count']
    out.write('--- DAILY ---\n')
    for dt in d_pred:
        if dt in d_act.index:
            out.write(f'{dt} pred={d_pred[dt]} actual={d_act[dt]}\n')

    out.write('\n--- HOURLY ---\n')
    h_pred = res['by_type']['EFT']['hourly']
    hourly_sub = hourly[(hourly.transaction_type==\"EFT\")]
    for dt in sorted(h_pred.keys()):
        for entry in h_pred[dt]:
            h = entry['hour']
            row = hourly_sub[(hourly_sub.date==pd.Timestamp(dt))&(hourly_sub.hour==h)]
            actual = int(row['count'].iloc[0]) if len(row) else None
            out.write(f'{dt} {h:02d}:00 pred={entry[\"count\"]} actual={actual}\n')
"
type zz_out.txt

OUT
Exit code 1
Traceback (most recent call last):
  File "<string>", line 27, in <module>
    d_act = daily[(daily.transaction_type=='EFT')&(daily.date.between(start,end))].set_index(daily.date.dt.strftime('%Y-%m-%d'))['count']
            ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Projects\wfoptv2\bank_forecast\venv\Lib\site-packages\pandas\core\frame.py", line 7039, in set_index
    raise ValueError(
    ...<2 lines>...
    )
ValueError: Length mismatch: Expected 5 rows, received array of length 2730
/usr/bin/bash: line 85: type: zz_out.txt: not found
Write d:\Projects\wfoptv2\bank_forecast\zz_check.py
49 lines
import warnings; warnings.filterwarnings('ignore')
import sys, io
import pandas as pd, numpy as np
from src.pipeline import forecast_pipeline, load_config
from src.data.loader import load_transactions
from src.data.aggregator import aggregate_daily, aggregate_hourly

cfg = load_config()
df = load_transactions('data/raw/demo.csv')
daily = aggregate_daily(df)
hourly = aggregate_hourly(df, working_hours=tuple(cfg['data']['working_hours']))

start, end = '2025-06-26', '2025-06-30'

old_stdout = sys.stdout
sys.stdout = io.StringIO()
try:
    res = forecast_pipeline(start=start, end=end, types=['EFT'], freq='both', fmt=[], plot=False)
finally:
    sys.stdout = old_stdout

with open('zz_out.txt', 'w', encoding='utf-8') as out:
    d_sub = daily[(daily.transaction_type == 'EFT') & (daily.date.between(start, end))].copy()
    d_sub['ds'] = d_sub['date'].dt.strftime('%Y-%m-%d')
    d_act = dict(zip(d_sub['ds'], d_sub['count']))
    d_pred = {e['date']: e['predicted_count'] for e in res['by_type']['EFT']['daily']}
    out.write('--- DAILY ---\n')
    diffs = []
    for dt in sorted(d_pred):
        if dt in d_act:
            out.write(f'{dt} pred={d_pred[dt]:.1f} actual={d_act[dt]} diff={d_pred[dt]-d_act[dt]:+.1f}\n')
            diffs.append(abs(d_pred[dt] - d_act[dt]))
    out.write(f'mean abs diff daily = {np.mean(diffs):.2f}\n')

    out.write('\n--- HOURLY ---\n')
    h_pred = res['by_type']['EFT']['hourly']
    hourly_sub = hourly[(hourly.transaction_type == 'EFT')]
    diffs_h = []
    for dt in sorted(h_pred.keys()):
        for entry in h_pred[dt]:
            h = entry['hour']
            row = hourly_sub[(hourly_sub.date == pd.Timestamp(dt)) & (hourly_sub.hour == h)]
            actual = int(row['count'].iloc[0]) if len(row) else None
            d = entry['count'] - actual if actual is not None else None
            out.write(f'{dt} {h:02d}:00 pred={entry["count"]:.1f} actual={actual} diff={d:+.1f}\n')
            if actual is not None:
                diffs_h.append(abs(d))
    out.write(f'mean abs diff hourly = {np.mean(diffs_h):.2f}\n')
Bash
IN
cd "d:/Projects/wfoptv2/bank_forecast" && python -W ignore zz_check.py 2>nul; echo ---; cat zz_out.txt

OUT
---
--- DAILY ---
2025-06-26 pred=2458.2 actual=369 diff=+2089.2
2025-06-27 pred=2730.8 actual=365 diff=+2365.8
2025-06-28 pred=861.9 actual=0 diff=+861.9
2025-06-29 pred=857.0 actual=0 diff=+857.0
2025-06-30 pred=3069.0 actual=640 diff=+2429.0
mean abs diff daily = 1720.58

--- HOURLY ---
2025-06-26 07:00 pred=2.1 actual=9 diff=-6.9
2025-06-26 08:00 pred=48.2 actual=34 diff=+14.2
2025-06-26 09:00 pred=58.7 actual=32 diff=+26.7
2025-06-26 10:00 pred=78.5 actual=63 diff=+15.5
2025-06-26 11:00 pred=76.2 actual=32 diff=+44.2
2025-06-26 12:00 pred=71.5 actual=25 diff=+46.5
2025-06-26 13:00 pred=70.1 actual=16 diff=+54.1
2025-06-26 14:00 pred=82.2 actual=42 diff=+40.2
2025-06-26 15:00 pred=87.6 actual=70 diff=+17.6
2025-06-26 16:00 pred=96.2 actual=12 diff=+84.2
2025-06-26 17:00 pred=82.4 actual=15 diff=+67.4
2025-06-26 18:00 pred=49.9 actual=6 diff=+43.9
2025-06-27 07:00 pred=3.3 actual=1 diff=+2.3
2025-06-27 08:00 pred=48.4 actual=7 diff=+41.4
2025-06-27 09:00 pred=60.4 actual=21 diff=+39.4
2025-06-27 10:00 pred=77.5 actual=27 diff=+50.5
2025-06-27 11:00 pred=73.9 actual=7 diff=+66.9
2025-06-27 12:00 pred=71.2 actual=65 diff=+6.2
2025-06-27 13:00 pred=74.6 actual=78 diff=-3.4
2025-06-27 14:00 pred=93.5 actual=71 diff=+22.5
2025-06-27 15:00 pred=106.5 actual=26 diff=+80.5
2025-06-27 16:00 pred=114.7 actual=3 diff=+111.7
2025-06-27 17:00 pred=96.8 actual=24 diff=+72.8
2025-06-27 18:00 pred=51.0 actual=12 diff=+39.0
2025-06-28 07:00 pred=2.8 actual=0 diff=+2.8
2025-06-28 08:00 pred=5.7 actual=0 diff=+5.7
2025-06-28 09:00 pred=8.6 actual=0 diff=+8.6
2025-06-28 10:00 pred=10.1 actual=0 diff=+10.1
2025-06-28 11:00 pred=10.1 actual=0 diff=+10.1
2025-06-28 12:00 pred=9.6 actual=0 diff=+9.6
2025-06-28 13:00 pred=11.4 actual=0 diff=+11.4
2025-06-28 14:00 pred=11.6 actual=0 diff=+11.6
2025-06-28 15:00 pred=13.9 actual=0 diff=+13.9
2025-06-28 16:00 pred=13.9 actual=0 diff=+13.9
2025-06-28 17:00 pred=14.1 actual=0 diff=+14.1
2025-06-28 18:00 pred=7.0 actual=0 diff=+7.0
2025-06-29 07:00 pred=2.7 actual=0 diff=+2.7
2025-06-29 08:00 pred=5.8 actual=0 diff=+5.8
2025-06-29 09:00 pred=8.5 actual=0 diff=+8.5
2025-06-29 10:00 pred=10.0 actual=0 diff=+10.0
2025-06-29 11:00 pred=10.0 actual=0 diff=+10.0
2025-06-29 12:00 pred=11.5 actual=0 diff=+11.5
2025-06-29 13:00 pred=18.1 actual=0 diff=+18.1
2025-06-29 14:00 pred=17.8 actual=0 diff=+17.8
2025-06-29 15:00 pred=19.9 actual=0 diff=+19.9
2025-06-29 16:00 pred=24.4 actual=0 diff=+24.4
2025-06-29 17:00 pred=19.9 actual=0 diff=+19.9
2025-06-29 18:00 pred=10.5 actual=0 diff=+10.5
2025-06-30 07:00 pred=3.5 actual=48 diff=-44.5
2025-06-30 08:00 pred=54.1 actual=56 diff=-1.9
2025-06-30 09:00 pred=65.3 actual=40 diff=+25.3
2025-06-30 10:00 pred=87.5 actual=84 diff=+3.5
2025-06-30 11:00 pred=86.2 actual=72 diff=+14.2
2025-06-30 12:00 pred=79.0 actual=17 diff=+62.0
2025-06-30 13:00 pred=88.1 actual=4 diff=+84.1
2025-06-30 14:00 pred=108.7 actual=34 diff=+74.7
2025-06-30 15:00 pred=120.6 actual=63 diff=+57.6
2025-06-30 16:00 pred=131.0 actual=41 diff=+90.0
2025-06-30 17:00 pred=120.3 actual=51 diff=+69.3
2025-06-30 18:00 pred=53.9 actual=17 diff=+36.9
mean abs diff hourly = 30.67
Bash
IN
cd "d:/Projects/wfoptv2/bank_forecast" && python -W ignore -c "
import pandas as pd
from src.data.loader import load_transactions
from src.data.aggregator import aggregate_daily
df = load_transactions('data/raw/demo.csv')
daily = aggregate_daily(df)
sub = daily[daily.transaction_type=='EFT'].sort_values('date').tail(35)
for _, r in sub.iterrows():
    print(r['date'].date(), r['date'].day_name(), int(r['count']))
" 2>nul

OUT
2025-05-27 Tuesday 265
2025-05-28 Wednesday 223
2025-05-29 Thursday 169
2025-05-30 Friday 393
2025-05-31 Saturday 0
2025-06-01 Sunday 0
2025-06-02 Monday 279
2025-06-03 Tuesday 236
2025-06-04 Wednesday 301
2025-06-05 Thursday 351
2025-06-06 Friday 0
2025-06-07 Saturday 0
2025-06-08 Sunday 0
2025-06-09 Monday 0
2025-06-10 Tuesday 264
2025-06-11 Wednesday 275
2025-06-12 Thursday 278
2025-06-13 Friday 249
2025-06-14 Saturday 0
2025-06-15 Sunday 0
2025-06-16 Monday 359
2025-06-17 Tuesday 339
2025-06-18 Wednesday 106
2025-06-19 Thursday 267
2025-06-20 Friday 265
2025-06-21 Saturday 0
2025-06-22 Sunday 0
2025-06-23 Monday 478
2025-06-24 Tuesday 376
2025-06-25 Wednesday 340
2025-06-26 Thursday 369
2025-06-27 Friday 365
2025-06-28 Saturday 0
2025-06-29 Sunday 0
2025-06-30 Monday 640
Read d:\Projects\wfoptv2\bank_forecast\src\models\base_model.py
Read d:\Projects\wfoptv2\bank_forecast\api\routes_data.py
Şimdi planımı netleştirdim. Önce kısaca özetleyeyim: Test ettiğimde hem günlük hem saatlik tahminlerin gerçek değerlerden çok uzak olduğunu, bunun da forecast_pipeline'da lag/rolling özelliklerinin tahmin sırasında sıfırla doldurulmasından (gerçek geçmiş veriler yerine) kaynaklandığını gördüm — kayıtlı modellerde lag_1, lag_168, lag_14 gibi özellikler en önemli özellikler arasında ama tahminde bunlar hep 0 yapılıyor (model hiç görmediği bir bölgeye ekstrapolasyon yapıyor). Ayrıca Fourier mevsimsellik özelliklerinde referans tarih (t0) eğitimde veri setinin başlangıcı, tahminde ise tahmin aralığının başlangıcı olarak hesaplanıyor — bu da haftalık/yıllık periyodik özelliklerde faz kayması yaratıyor (özellikle saatlikte, çünkü saatlik modelde "saat" özelliği yok, sadece Fourier kodlamasına dayanıyor).

Şimdi düzeltmelere başlıyorum.

Edit d:\Projects\wfoptv2\bank_forecast\src\features\seasonal_features.py
Added 6 lines
Şimdi pipeline.py'a yardımcı fonksiyonları ve recursive tahmin mantığını ekliyorum.

Edit d:\Projects\wfoptv2\bank_forecast\src\pipeline.py
Added 117 lines
Şimdi forecast_pipeline fonksiyonuna historical_data parametresini ekleyip ana döngüyü yeni recursive yaklaşıma göre düzenliyorum.

Edit d:\Projects\wfoptv2\bank_forecast\src\pipeline.py
Added 10 lines
Şimdi ana per-type/freq döngüsünü değiştiriyorum.

Edit d:\Projects\wfoptv2\bank_forecast\src\pipeline.py
Removed 1 line
Edit d:\Projects\wfoptv2\bank_forecast\src\pipeline.py
Added 34 lines
Edit d:\Projects\wfoptv2\bank_forecast\api\routes_forecast.py
Added 1 line
Edit d:\Projects\wfoptv2\bank_forecast\forecast.py
Added 2 lines
Edit d:\Projects\wfoptv2\bank_forecast\forecast.py
Added 3 lines
Edit d:\Projects\wfoptv2\bank_forecast\forecast.py
Added 11 lines
Edit d:\Projects\wfoptv2\bank_forecast\forecast.py
Added 1 line
Şimdi yeni forecast_pipeline'ı test edip eski sonuçlarla karşılaştırıyorum (önce mevcut kayıtlı modellerle, eski Fourier epoch ile eğitilmiş olsa da recursive lag besleme etkisini görmek için).

Write d:\Projects\wfoptv2\bank_forecast\zz_check2.py
55 lines
import warnings; warnings.filterwarnings('ignore')
import sys, io
import pandas as pd, numpy as np
from src.pipeline import forecast_pipeline, load_config
from src.data.loader import load_transactions
from src.data.aggregator import aggregate_daily, aggregate_hourly

cfg = load_config()
df = load_transactions('data/raw/demo.csv')
daily = aggregate_daily(df)
hourly = aggregate_hourly(df, working_hours=tuple(cfg['data']['working_hours']))
hist = {"daily": daily, "hourly": hourly}

start, end = '2025-06-26', '2025-06-30'

old_stdout = sys.stdout
sys.stdout = io.StringIO()
try:
    res = forecast_pipeline(start=start, end=end, types=['EFT'], freq='both', fmt=[], plot=False, historical_data=hist)
finally:
    sys.stdout = old_stdout

with open('zz_out2.txt', 'w', encoding='utf-8') as out:
    d_sub = daily[(daily.transaction_type == 'EFT') & (daily.date.between(start, end))].copy()
    d_sub['ds'] = d_sub['date'].dt.strftime('%Y-%m-%d')
    d_act = dict(zip(d_sub['ds'], d_sub['count']))
    d_pred = {e['date']: e['predicted_count'] for e in res['by_type']['EFT']['daily']}
    out.write('--- DAILY (with historical_data, OLD model/fourier) ---\n')
    diffs = []
    for dt in sorted(d_pred):
        if dt in d_act:
            out.write(f'{dt} pred={d_pred[dt]:.1f} actual={d_act[dt]} diff={d_pred[dt]-d_act[dt]:+.1f}\n')
            diffs.append(abs(d_pred[dt] - d_act[dt]))
    out.write(f'mean abs diff daily = {np.mean(diffs):.2f}\n')

    out.write('\n--- HOURLY ---\n')
    h_pred = res['by_type']['EFT']['hourly']
    hourly_sub = hourly[(hourly.transaction_type == 'EFT')]
    diffs_h = []
    for dt in sorted(h_pred.keys()):
        day_pred_sum = 0.0
        day_actual_sum = 0
        for entry in h_pred[dt]:
            h = entry['hour']
            row = hourly_sub[(hourly_sub.date == pd.Timestamp(dt)) & (hourly_sub.hour == h)]
            actual = int(row['count'].iloc[0]) if len(row) else None
            d = entry['count'] - actual if actual is not None else None
            out.write(f'{dt} {h:02d}:00 pred={entry["count"]:.1f} actual={actual} diff={d:+.1f}\n')
            day_pred_sum += entry['count']
            if actual is not None:
                diffs_h.append(abs(d))
                day_actual_sum += actual
        out.write(f'  >> {dt} TOPLAM  hourly_pred_sum={day_pred_sum:.1f}  daily_pred={d_pred.get(dt):.1f}  actual_sum={day_actual_sum}\n')
    out.write(f'mean abs diff hourly = {np.mean(diffs_h):.2f}\n')
Bash
IN
cd "d:/Projects/wfoptv2/bank_forecast" && python -W ignore zz_check2.py 2>nul; echo ---; cat zz_out2.txt

OUT
---
--- DAILY (with historical_data, OLD model/fourier) ---
2025-06-26 pred=2587.7 actual=369 diff=+2218.7
2025-06-27 pred=3217.4 actual=365 diff=+2852.4
2025-06-28 pred=0.0 actual=0 diff=+0.0
2025-06-29 pred=0.0 actual=0 diff=+0.0
2025-06-30 pred=2847.1 actual=640 diff=+2207.1
mean abs diff daily = 1455.64

--- HOURLY ---
2025-06-26 07:00 pred=0.7 actual=9 diff=-8.3
2025-06-26 08:00 pred=76.2 actual=34 diff=+42.2
2025-06-26 09:00 pred=55.6 actual=32 diff=+23.6
2025-06-26 10:00 pred=116.5 actual=63 diff=+53.5
2025-06-26 11:00 pred=77.9 actual=32 diff=+45.9
2025-06-26 12:00 pred=95.2 actual=25 diff=+70.2
2025-06-26 13:00 pred=70.8 actual=16 diff=+54.8
2025-06-26 14:00 pred=89.4 actual=42 diff=+47.4
2025-06-26 15:00 pred=117.5 actual=70 diff=+47.5
2025-06-26 16:00 pred=117.3 actual=12 diff=+105.3
2025-06-26 17:00 pred=91.8 actual=15 diff=+76.8
2025-06-26 18:00 pred=46.9 actual=6 diff=+40.9
  >> 2025-06-26 TOPLAM  hourly_pred_sum=955.8  daily_pred=2587.7  actual_sum=356
2025-06-27 07:00 pred=0.5 actual=1 diff=-0.5
2025-06-27 08:00 pred=46.5 actual=7 diff=+39.5
2025-06-27 09:00 pred=58.9 actual=21 diff=+37.9
2025-06-27 10:00 pred=77.5 actual=27 diff=+50.5
2025-06-27 11:00 pred=76.2 actual=7 diff=+69.2
2025-06-27 12:00 pred=106.5 actual=65 diff=+41.5
2025-06-27 13:00 pred=180.6 actual=78 diff=+102.6
2025-06-27 14:00 pred=116.4 actual=71 diff=+45.4
2025-06-27 15:00 pred=135.4 actual=26 diff=+109.4
2025-06-27 16:00 pred=137.9 actual=3 diff=+134.9
2025-06-27 17:00 pred=127.0 actual=24 diff=+103.0
2025-06-27 18:00 pred=50.1 actual=12 diff=+38.1
  >> 2025-06-27 TOPLAM  hourly_pred_sum=1113.5  daily_pred=3217.4  actual_sum=342
2025-06-28 07:00 pred=0.2 actual=0 diff=+0.2
2025-06-28 08:00 pred=0.2 actual=0 diff=+0.2
2025-06-28 09:00 pred=0.2 actual=0 diff=+0.2
2025-06-28 10:00 pred=0.2 actual=0 diff=+0.2
2025-06-28 11:00 pred=0.2 actual=0 diff=+0.2
2025-06-28 12:00 pred=0.2 actual=0 diff=+0.2
2025-06-28 13:00 pred=0.2 actual=0 diff=+0.2
2025-06-28 14:00 pred=0.2 actual=0 diff=+0.2
2025-06-28 15:00 pred=0.2 actual=0 diff=+0.2
2025-06-28 16:00 pred=0.2 actual=0 diff=+0.2
2025-06-28 17:00 pred=0.2 actual=0 diff=+0.2
2025-06-28 18:00 pred=0.2 actual=0 diff=+0.2
  >> 2025-06-28 TOPLAM  hourly_pred_sum=2.4  daily_pred=0.0  actual_sum=0
2025-06-29 07:00 pred=0.2 actual=0 diff=+0.2
2025-06-29 08:00 pred=0.2 actual=0 diff=+0.2
2025-06-29 09:00 pred=0.2 actual=0 diff=+0.2
2025-06-29 10:00 pred=0.2 actual=0 diff=+0.2
2025-06-29 11:00 pred=0.2 actual=0 diff=+0.2
2025-06-29 12:00 pred=0.2 actual=0 diff=+0.2
2025-06-29 13:00 pred=0.2 actual=0 diff=+0.2
2025-06-29 14:00 pred=0.4 actual=0 diff=+0.4
2025-06-29 15:00 pred=1.0 actual=0 diff=+1.0
2025-06-29 16:00 pred=1.0 actual=0 diff=+1.0
2025-06-29 17:00 pred=1.0 actual=0 diff=+1.0
2025-06-29 18:00 pred=1.3 actual=0 diff=+1.3
  >> 2025-06-29 TOPLAM  hourly_pred_sum=6.1  daily_pred=0.0  actual_sum=0
2025-06-30 07:00 pred=3.2 actual=48 diff=-44.8
2025-06-30 08:00 pred=81.8 actual=56 diff=+25.8
2025-06-30 09:00 pred=105.2 actual=40 diff=+65.2
2025-06-30 10:00 pred=127.9 actual=84 diff=+43.9
2025-06-30 11:00 pred=89.7 actual=72 diff=+17.7
2025-06-30 12:00 pred=81.0 actual=17 diff=+64.0
2025-06-30 13:00 pred=82.3 actual=4 diff=+78.3
2025-06-30 14:00 pred=174.2 actual=34 diff=+140.2
2025-06-30 15:00 pred=91.0 actual=63 diff=+28.0
2025-06-30 16:00 pred=102.9 actual=41 diff=+61.9
2025-06-30 17:00 pred=91.8 actual=51 diff=+40.8
2025-06-30 18:00 pred=51.6 actual=17 diff=+34.6
  >> 2025-06-30 TOPLAM  hourly_pred_sum=1082.6  daily_pred=2847.1  actual_sum=527
mean abs diff hourly = 34.04
Bash
IN
cd "d:/Projects/wfoptv2/bank_forecast" && python -W ignore -c "
import pandas as pd
from src.data.loader import load_transactions
from src.data.aggregator import aggregate_daily
df = load_transactions('data/raw/demo.csv')
daily = aggregate_daily(df)
sub = daily[daily.transaction_type=='EFT'].sort_values('date')
sub['ym'] = sub['date'].dt.to_period('M')
print(sub.groupby('ym')['count'].mean().round(1))
print()
print('overall describe:')
print(sub['count'].describe())
" 2>nul

OUT
ym
2024-01    156.9
2024-02    165.5
2024-03    159.7
2024-04    141.0
2024-05    163.7
2024-06    125.6
2024-07    171.5
2024-08    143.6
2024-09    163.3
2024-10    183.4
2024-11    176.7
2024-12    179.5
2025-01    178.9
2025-02    189.5
2025-03    169.0
2025-04    167.9
2025-05    170.6
2025-06    204.6
Freq: M, Name: count, dtype: float64

overall describe:
count    546.000000
mean     167.232601
std      131.933925
min        0.000000
25%        0.000000
50%      189.000000
75%      262.000000
max      640.000000
Name: count, dtype: float64
Bash
IN
cd "d:/Projects/wfoptv2/bank_forecast" && python -W ignore -c "
import json
with open('models/saved/model_registry.json', encoding='utf-8') as f:
    r = json.load(f)
print('trained_at:', r['trained_at'])
print('data_range:', r['data_range'])
print()
m = r['models']['EFT_daily']
print('feature_names:', m['feature_names'])
print('feature_importance_top5:', m['feature_importance_top5'])
print('all_scores:', m['all_scores'])
" 2>nul

OUT
trained_at: 2026-06-07T20:58:44.680987
data_range: {'start': '2025-06-02', 'end': '2025-10-24'}

feature_names: ['is_public_holiday', 'is_religious_holiday', 'is_eve_of_holiday', 'is_bridge_day', 'is_weekend', 'day_of_week', 'day_of_month', 'month', 'quarter', 'week_of_month', 'month_quarter', 'is_month_start', 'is_month_end', 'is_last_friday', 'days_to_month_end', 'days_from_month_start', 'days_to_next_holiday', 'days_from_last_holiday', 'post_holiday_day1', 'post_holiday_day2', 'lag_1', 'lag_2', 'lag_3', 'lag_5', 'lag_7', 'lag_14', 'lag_21', 'lag_28', 'rolling_mean_7', 'rolling_std_7', 'rolling_max_7', 'rolling_mean_14', 'rolling_std_14', 'rolling_max_14', 'rolling_mean_30', 'rolling_std_30', 'rolling_max_30', 'sin_7_1', 'cos_7_1', 'sin_7_2', 'cos_7_2', 'sin_7_3', 'cos_7_3', 'sin_365_1', 'cos_365_1', 'sin_365_2', 'cos_365_2', 'sin_365_3', 'cos_365_3', 'sin_365_4', 'cos_365_4', 'sin_365_5', 'cos_365_5', 'transaction_type_enc']
feature_importance_top5: ['day_of_week', 'is_weekend', 'sin_7_1', 'sin_7_3', 'lag_14']
all_scores: {'xgboost': 344.9349, 'lightgbm': 495.0463, 'random_forest': 306.8166, 'holt_winters': 373.2679, 'ridge': 321.192}
Önemli bir bulgu: kayıtlı modeller demo.csv ile değil, farklı bir veri aralığıyla (2025-06-02 – 2025-10-24) eğitilmiş — bu yüzden demo veriyle karşılaştırmam tutarsızdı. Demo veriyle yeniden eğitip doğru bir karşılaştırma yapmam gerekiyor. Eğitimi arka planda başlatıyorum (uzun sürebilir).

Bash Start retraining models on demo.csv in background
IN
cd "d:/Projects/wfoptv2/bank_forecast" && rm -f zz_train.log && nohup python -W ignore train.py --input data/raw/demo.csv --freq both --models auto --report > zz_train.log 2>&1 &
echo "started pid $!"

OUT
started pid 4365
Bash Check training progress
IN
sleep 30; cd "d:/Projects/wfoptv2/bank_forecast" && tail -n 30 zz_train.log

OUT
<tool_use_error>Blocked: sleep 30 followed by: cd "d:/Projects/wfoptv2/bank_forecast" tail -n 30 zz_train.log. To wait for a condition, use Monitor with an until-loop (e.g. `until <check>; do sleep 2; done`). To wait for a command you started, use run_in_background: true. Do not chain shorter sleeps to work around this block.</tool_use_error>
Bash Check training log and process status
IN
cd "d:/Projects/wfoptv2/bank_forecast" && tail -n 20 zz_train.log 2>/dev/null; echo "---procs---"; ps aux | grep -i "train.py" | grep -v grep

OUT
    ~~~~~~~~~~~~~~~~~^^
  File "D:\Projects\wfoptv2\bank_forecast\venv\Lib\site-packages\rich\console.py", line 820, in _exit_buffer
    self._check_buffer()
    ~~~~~~~~~~~~~~~~~~^^
  File "D:\Projects\wfoptv2\bank_forecast\venv\Lib\site-packages\rich\console.py", line 2055, in _check_buffer
    self._write_buffer()
    ~~~~~~~~~~~~~~~~~~^^
  File "D:\Projects\wfoptv2\bank_forecast\venv\Lib\site-packages\rich\console.py", line 2091, in _write_buffer
    legacy_windows_render(buffer, LegacyWindowsTerm(self.file))
    ~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\Projects\wfoptv2\bank_forecast\venv\Lib\site-packages\rich\_windows_renderer.py", line 19, in legacy_windows_render
    term.write_text(text)
    ~~~~~~~~~~~~~~~^^^^^^
  File "D:\Projects\wfoptv2\bank_forecast\venv\Lib\site-packages\rich\_win32_console.py", line 402, in write_text
    self.write(text)
    ~~~~~~~~~~^^^^^^
  File "C:\Users\MURAT\AppData\Local\Programs\Python\Python314\Lib\encodings\cp1254.py", line 19, in encode
    return codecs.charmap_encode(input,self.errors,encoding_table)[0]
           ~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
UnicodeEncodeError: 'charmap' codec can't encode character '\u2192' in position 1: character maps to <undefined>
---procs---
Bash Restart training with UTF-8 encoding env vars
IN
cd "d:/Projects/wfoptv2/bank_forecast" && rm -f zz_train.log && PYTHONIOENCODING=utf-8 PYTHONUTF8=1 nohup python -W ignore train.py --input data/raw/demo.csv --freq both --models auto --report > zz_train.log 2>&1 &
echo "started pid $!"

OUT
started pid 4376
Bash Check training status
IN
cd "d:/Projects/wfoptv2/bank_forecast" && tail -n 15 zz_train.log 2>/dev/null; echo "---procs---"; ps aux | grep -i "train.py" | grep -v grep | head -5

OUT
Eğitim başlıyor
  Giriş   : data/raw/demo.csv
  Frekans : both
  Tipler  : tüm tipler
  Modeller: otomatik seçim
Veri yükleniyor...
---procs---
Bash Wait for training to complete (up to 30 min) and show tail of log
IN
cd "d:/Projects/wfoptv2/bank_forecast" && timeout 1800 bash -c 'until grep -q "Registry kaydedildi\|Hata\|Traceback" zz_train.log 2>/dev/null; do sleep 15; done; echo DONE'; tail -n 40 zz_train.log

OUT
Command running in background with ID: b6e8lqess. Output is being written to: C:\Users\MURAT\AppData\Local\Temp\claude\d--Projects-wfoptv2\e902adc7-1dea-4e59-bdde-5c8a175b1a99\tasks\b6e8lqess.output. You will be notified when it completes. To check interim output, use Read on that file path.
Eğitim arka planda devam ederken, frontend ve backend'deki "model seçimi" ve diğer iyileştirmeleri uygulamaya devam ediyorum.

Read d:\Projects\wfoptv2\bank_forecast\frontend\src\components\TrainingProgress.tsx
Edit d:\Projects\wfoptv2\bank_forecast\api\schemas.py
Added 1 line
