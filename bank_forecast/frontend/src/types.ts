export interface DateRange {
  start: string
  end: string
}

export type MetricType = 'talimat' | 'islem'

export const METRIC_TYPES: MetricType[] = ['talimat', 'islem']

export const METRIC_LABELS: Record<MetricType, string> = {
  talimat: 'Talimat',
  islem: 'İşlem',
}

export interface PerTeamTypeCount {
  team: string
  transaction_type: string
  count: number
}

export interface DatasetSummary {
  loaded: boolean
  metric_type?: MetricType
  filename?: string
  source_kind?: 'upload' | 'demo'
  row_count?: number
  date_range?: DateRange
  teams?: string[]
  transaction_types?: string[]
  per_team_counts?: Record<string, number>
  per_type_counts?: Record<string, number>
  per_team_type_counts?: PerTeamTypeCount[]
  has_hourly?: boolean
  loaded_at?: string
}

/** `/api/dataset/summary` yanıtı — her iki metrik için de (yüklenmemişse null) özet döner */
export type DatasetSummaryMap = Record<MetricType, DatasetSummary | null>

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

/** Tek bir (ekip, işlem tipi) birimi için tahmin sonucu — ekip/metrik boyutu eklenmeden önceki şekliyle aynı */
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

/** ekip -> işlem tipi -> tahmin sonucu */
export type ByTeam = Record<string, Record<string, ForecastByType>>

export interface AvailableModelsResponse {
  /** available[ekip][işlem_tipi][frekans] = { best_model, models: [...] } */
  available: Record<string, Record<string, Record<string, { best_model: string; models: string[] }>>>
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
  by_team: Record<string, Record<string, ComparisonRow[]>>
}

export interface ForecastTotalsByType {
  model_used: string
  predicted_count: number
}

export interface ForecastTotalsByTeam {
  predicted_count: number
  by_type: Record<string, ForecastTotalsByType>
}

export interface ForecastTotals {
  total_predicted: number
  by_team: Record<string, ForecastTotalsByTeam>
}

export interface MapeByTeam {
  mape: number | null
  by_type: Record<string, number | null>
}

/** Tahmin ekranındaki "gerçekleşen vs tahmin" örtüşmesinden hesaplanan ekip bazlı + toplam MAPE */
export interface MapeSummary {
  overall_mape: number | null
  by_team: Record<string, MapeByTeam>
}

export interface MetricForecastResult {
  forecast: {
    generated_at: string
    forecast_range: DateRange
    by_team: ByTeam
  }
  comparison: {
    daily: ComparisonResult
    hourly: ComparisonResult
  }
  totals: ForecastTotals
  mape_summary: MapeSummary
}

/** `/api/forecast` yanıtı — talimat ve işlem aynı anda yüklüyse ikisi de dolu döner */
export type ForecastResponse = Partial<Record<MetricType, MetricForecastResult | null>>

export interface TrainingStep {
  at: string
  kind: string
  message: string
  team?: string
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
  teams?: string[]
  feature_importance_top5?: string[]
}

export interface HoldoutRow {
  date: string
  actual: number
  predicted: number
}

export interface HoldoutTypeResult {
  mape: number | null
  rows: HoldoutRow[]
  /** Birden fazla model eğitildiyse her model için bu (ekip, işlem tipi) MAPE değeri */
  model_mapes?: Record<string, number | null>
}

export interface HoldoutTeamResult {
  mape: number | null
  by_type: Record<string, HoldoutTypeResult>
}

export interface HoldoutResult {
  holdout_range: DateRange
  by_team: Record<string, HoldoutTeamResult>
  overall_mape: number | null
  /** Birden fazla model eğitildiyse her model için genel (tüm ekip/tip) MAPE değeri */
  model_overall_mapes?: Record<string, number | null>
}

export interface RetrainStatus {
  metric_type?: MetricType
  status: 'idle' | 'running' | 'done' | 'error'
  message: string
  started_at: string | null
  finished_at: string | null
  progress: number
  total_units: number
  completed_units: number
  steps: TrainingStep[]
  holdout_days?: number
  holdout_result?: HoldoutResult | null
}

/** Kalibrasyon desenleri — sırasıyla en yüksekten en düşük önceliğe (bkz. backend `PATTERN_PRECEDENCE`) */
export const CALIBRATION_PATTERNS = ['half_day', 'first_monday_of_month', 'friday'] as const
export type CalibrationPattern = (typeof CALIBRATION_PATTERNS)[number]

export const CALIBRATION_PATTERN_LABELS: Record<CalibrationPattern, string> = {
  half_day: 'Yarım Gün',
  first_monday_of_month: 'Ayın İlk Pazartesi',
  friday: 'Cuma',
}

export interface CalibrationHotspot {
  team: string
  transaction_type: string
  granularity: 'daily' | 'hourly'
  weekday: number
  hour: number | null
  pattern: CalibrationPattern | null
  n: number
  mean_actual: number
  mean_predicted: number
  pct_error: number
  direction: 'under_forecast' | 'over_forecast'
  impact_score: number
  recommendation: string
}

export interface CalibrationReport {
  generated_at: string
  params: { min_samples: number; error_threshold_pct: number }
  hotspots: CalibrationHotspot[]
  summary: { groups_checked: number; hotspot_count: number }
}

export interface SuggestedMultiplier {
  multiplier: number
  n_pattern: number
  n_baseline: number
  confidence: 'ok' | 'low_sample'
}

export interface SuggestedMultipliersResponse {
  generated_at: string
  by_type: Record<string, Record<string, SuggestedMultiplier>>
}

export interface CalibrationConfig {
  multipliers: Record<string, Record<string, number>>
  half_days: string[]
  updated_at: string | null
}

export interface CalibrationPreviewMetric {
  overall_mape: number | null
  by_team: Record<string, MapeByTeam>
}

export interface CalibrationPreviewResponse {
  current: CalibrationPreviewMetric
  proposed: CalibrationPreviewMetric
  delta: CalibrationPreviewMetric
}

/** Tahmin ekranından Kalibrasyon ekranına geçerken taşınan bağlam (bkz. `ResultsPanel.tsx`) */
export interface CalibrationScope {
  metricType: MetricType
  team: string
  type: string
  start: string
  end: string
}
