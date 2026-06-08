export const MODEL_LABELS: Record<string, string> = {
  auto: 'Tümü (otomatik en iyi seçim)',
  xgboost: 'XGBoost',
  lightgbm: 'LightGBM',
  random_forest: 'Random Forest',
  holt_winters: 'Holt-Winters',
  ridge: 'Ridge',
}

export const MODEL_OPTIONS = ['auto', 'xgboost', 'lightgbm', 'random_forest', 'holt_winters', 'ridge']

/** Karşılaştırma grafiklerinde modelleri ayırt etmek için kullanılan renk paleti */
export const MODEL_COLORS = ['#e8b54a', '#60a5fa', '#34d399', '#f472b6', '#a78bfa', '#fb923c']
