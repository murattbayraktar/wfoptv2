import type {
  AvailableModelsResponse,
  CalibrationConfig,
  CalibrationPreviewResponse,
  CalibrationReport,
  DatasetSummaryMap,
  ForecastResponse,
  MetricType,
  RetrainStatus,
  SuggestedMultipliersResponse,
} from '../types'

async function handleJson<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let detail = res.statusText
    try {
      const body = await res.json()
      detail = body.detail ?? detail
    } catch {
      // yanıt JSON değilse statusText kullanılır
    }
    throw new Error(detail)
  }
  return res.json() as Promise<T>
}

export async function getDatasetSummary(): Promise<DatasetSummaryMap> {
  const res = await fetch('/api/dataset/summary')
  return handleJson<DatasetSummaryMap>(res)
}

/** CSV içeriğine göre metrik tipi (talimat/işlem) otomatik algılanır — çağıran taraf belirtmez. */
export async function uploadCsv(file: File): Promise<DatasetSummaryMap> {
  const form = new FormData()
  form.append('file', file)
  const res = await fetch('/api/upload', { method: 'POST', body: form })
  return handleJson<DatasetSummaryMap>(res)
}

export interface ForecastParams {
  start: string
  end: string
  metric_type?: MetricType | 'both'
  teams?: string[]
  types?: string[]
  freq?: string
  models?: string[]
}

export async function runForecast(params: ForecastParams): Promise<ForecastResponse> {
  const res = await fetch('/api/forecast', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  })
  return handleJson<ForecastResponse>(res)
}

export async function exportForecastExcel(params: ForecastParams): Promise<Blob> {
  const res = await fetch('/api/forecast/export', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  })
  if (!res.ok) {
    let detail = res.statusText
    try {
      const body = await res.json()
      detail = body.detail ?? detail
    } catch {
      // yanıt JSON değilse statusText kullanılır
    }
    throw new Error(detail)
  }
  return res.blob()
}

export async function getAvailableModels(metricType: MetricType): Promise<AvailableModelsResponse> {
  const res = await fetch(`/api/models/available?metric_type=${metricType}`)
  return handleJson<AvailableModelsResponse>(res)
}

export async function startRetrain(params: {
  metric_type: MetricType
  freq?: string
  teams?: string[]
  types?: string[]
  models?: string[]
  holdout_days?: number
}): Promise<{ status: string }> {
  const res = await fetch('/api/retrain', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  })
  return handleJson<{ status: string }>(res)
}

export async function getRetrainStatus(metricType: MetricType): Promise<RetrainStatus> {
  const res = await fetch(`/api/retrain/status?metric_type=${metricType}`)
  return handleJson<RetrainStatus>(res)
}

export interface CalibrationAnalyzeParams {
  metric_type: MetricType
  start: string
  end: string
  teams?: string[]
  types?: string[]
  min_samples?: number
  error_threshold_pct?: number
}

export async function analyzeCalibration(params: CalibrationAnalyzeParams): Promise<CalibrationReport> {
  const res = await fetch('/api/calibration/analyze', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  })
  return handleJson<CalibrationReport>(res)
}

export async function suggestMultipliers(params: CalibrationAnalyzeParams): Promise<SuggestedMultipliersResponse> {
  const res = await fetch('/api/calibration/multipliers/suggest', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  })
  return handleJson<SuggestedMultipliersResponse>(res)
}

export async function getCalibrationConfig(): Promise<CalibrationConfig> {
  const res = await fetch('/api/calibration/config')
  return handleJson<CalibrationConfig>(res)
}

export async function saveCalibrationConfig(body: {
  multipliers: CalibrationConfig['multipliers']
  half_days: string[]
}): Promise<CalibrationConfig> {
  const res = await fetch('/api/calibration/config', {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  return handleJson<CalibrationConfig>(res)
}

export async function previewCalibrationConfig(
  params: CalibrationAnalyzeParams & { proposed: { multipliers: CalibrationConfig['multipliers']; half_days: string[] } },
): Promise<CalibrationPreviewResponse> {
  const res = await fetch('/api/calibration/preview', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  })
  return handleJson<CalibrationPreviewResponse>(res)
}
