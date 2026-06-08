import type { AvailableModelsResponse, DatasetSummary, ForecastResponse, RetrainStatus } from '../types'

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

export async function getDatasetSummary(): Promise<DatasetSummary> {
  const res = await fetch('/api/dataset/summary')
  return handleJson<DatasetSummary>(res)
}

export async function loadDemoData(): Promise<DatasetSummary> {
  const res = await fetch('/api/demo-data', { method: 'POST' })
  return handleJson<DatasetSummary>(res)
}

export async function uploadCsv(file: File): Promise<DatasetSummary> {
  const form = new FormData()
  form.append('file', file)
  const res = await fetch('/api/upload', { method: 'POST', body: form })
  return handleJson<DatasetSummary>(res)
}

export async function runForecast(params: {
  start: string
  end: string
  freq?: string
  types?: string[]
  models?: string[]
}): Promise<ForecastResponse> {
  const res = await fetch('/api/forecast', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  })
  return handleJson<ForecastResponse>(res)
}

export async function getAvailableModels(): Promise<AvailableModelsResponse> {
  const res = await fetch('/api/models/available')
  return handleJson<AvailableModelsResponse>(res)
}

export async function startRetrain(params: { freq?: string; types?: string[]; models?: string[]; holdout_days?: number }): Promise<{ status: string }> {
  const res = await fetch('/api/retrain', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  })
  return handleJson<{ status: string }>(res)
}

export async function getRetrainStatus(): Promise<RetrainStatus> {
  const res = await fetch('/api/retrain/status')
  return handleJson<RetrainStatus>(res)
}
