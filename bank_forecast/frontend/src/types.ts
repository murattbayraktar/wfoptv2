export interface DateRange {
  start: string
  end: string
}

export interface DatasetSummary {
  loaded: boolean
  filename?: string
  source_kind?: 'upload' | 'demo'
  row_count?: number
  date_range?: DateRange
  transaction_types?: string[]
  per_type_counts?: Record<string, number>
  has_hourly?: boolean
  loaded_at?: string
}

export interface DailyForecastEntry {
  date: string
  predicted_count: number
  lower_80: number
  upper_80: number
  confidence: string
  calendar_flags: string[]
}

export interface HourlyForecastEntry {
  hour: number
  count: number
}

export interface ForecastByType {
  model_used: string
  daily?: DailyForecastEntry[]
  hourly?: Record<string, HourlyForecastEntry[]>
  /** Birden fazla model seçildiğinde dolu olur — model adı -> o modelin tahmin sonucu (overlay/karşılaştırma için) */
  models?: Record<string, {
    model_used: string
    daily?: DailyForecastEntry[]
    hourly?: Record<string, HourlyForecastEntry[]>
  }>
}

export interface AvailableModelsResponse {
  /** available[işlem_tipi][frekans] = { best_model, models: [...] } */
  available: Record<string, Record<string, { best_model: string; models: string[] }>>
}

export interface ComparisonRow {
  date: string
  hour?: number
  predicted_count: number
  actual_count: number
}

export interface ComparisonResult {
  has_overlap: boolean
  overlap_range: DateRange | null
  by_type: Record<string, ComparisonRow[]>
}

export interface ForecastTotals {
  total_predicted: number
  by_type: Record<string, { model_used: string; predicted_count: number }>
}

export interface ForecastResponse {
  forecast: {
    generated_at: string
    forecast_range: DateRange
    by_type: Record<string, ForecastByType>
  }
  comparison: {
    daily: ComparisonResult
    hourly: ComparisonResult
  }
  totals: ForecastTotals
}

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
  row_count?: number
  transaction_types?: string[]
  feature_importance_top5?: string[]
}

export interface RetrainStatus {
  status: 'idle' | 'running' | 'done' | 'error'
  message: string
  started_at: string | null
  finished_at: string | null
  progress: number
  total_units: number
  completed_units: number
  steps: TrainingStep[]
}
