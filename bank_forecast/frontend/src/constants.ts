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
export const MODEL_COLORS = ['#2563eb', '#d97706', '#059669', '#db2777', '#7c3aed', '#ea580c']
