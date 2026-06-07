import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from 'react'
import * as api from '../api/client'
import type { DatasetSummary, ForecastResponse } from '../types'

export type UiStep = 'idle' | 'progress' | 'results'

interface DataContextValue {
  dataset: DatasetSummary | null
  datasetError: string | null
  loadingDataset: boolean
  loadDemo: () => Promise<void>
  upload: (file: File) => Promise<void>

  rangeStart: string
  rangeEnd: string
  setRangeStart: (v: string) => void
  setRangeEnd: (v: string) => void

  uiStep: UiStep
  forecastResult: ForecastResponse | null
  forecastError: string | null
  createForecast: () => Promise<void>
  resetResults: () => void
}

const DataContext = createContext<DataContextValue | null>(null)

function defaultRange(): { start: string; end: string } {
  const today = new Date()
  const start = new Date(today)
  const end = new Date(today)
  end.setDate(end.getDate() + 30)
  const fmt = (d: Date) => d.toISOString().slice(0, 10)
  return { start: fmt(start), end: fmt(end) }
}

/**
 * Yüklenen veri kümesinin son 30 günü — veriyle örtüşen bir aralık önerir, böylece
 * "Tahmin Oluştur" ilk denemede hem anlamlı bir sonuç hem de gerçekleşen-vs-tahmin
 * karşılaştırmasını gösterir. Veri kümesi 30 günden kısaysa baştan başlatılır.
 */
function rangeFromDataset(dateRange?: { start: string; end: string }): { start: string; end: string } | null {
  if (!dateRange) return null
  const fmt = (d: Date) => d.toISOString().slice(0, 10)
  const dataStart = new Date(dateRange.start)
  const dataEnd = new Date(dateRange.end)
  const start = new Date(dataEnd)
  start.setUTCDate(start.getUTCDate() - 29)
  if (start < dataStart) start.setTime(dataStart.getTime())
  return { start: fmt(start), end: fmt(dataEnd) }
}

export function DataProvider({ children }: { children: ReactNode }) {
  const [dataset, setDataset] = useState<DatasetSummary | null>(null)
  const [datasetError, setDatasetError] = useState<string | null>(null)
  const [loadingDataset, setLoadingDataset] = useState(false)

  const initialRange = defaultRange()
  const [rangeStart, setRangeStart] = useState(initialRange.start)
  const [rangeEnd, setRangeEnd] = useState(initialRange.end)

  const [uiStep, setUiStep] = useState<UiStep>('idle')
  const [forecastResult, setForecastResult] = useState<ForecastResponse | null>(null)
  const [forecastError, setForecastError] = useState<string | null>(null)

  useEffect(() => {
    api
      .getDatasetSummary()
      .then((summary) => {
        if (summary.loaded) {
          setDataset(summary)
          const suggested = rangeFromDataset(summary.date_range)
          if (suggested) {
            setRangeStart(suggested.start)
            setRangeEnd(suggested.end)
          }
        }
      })
      .catch(() => {
        // sayfa açılışında özet alınamazsa sessizce "veri yok" durumunda kalınır
      })
  }, [])

  const loadDemo = useCallback(async () => {
    setLoadingDataset(true)
    setDatasetError(null)
    try {
      const summary = await api.loadDemoData()
      setDataset(summary)
      setForecastResult(null)
      setUiStep('idle')
      const suggested = rangeFromDataset(summary.date_range)
      if (suggested) {
        setRangeStart(suggested.start)
        setRangeEnd(suggested.end)
      }
    } catch (e) {
      setDatasetError(e instanceof Error ? e.message : 'Demo veri yüklenemedi.')
    } finally {
      setLoadingDataset(false)
    }
  }, [])

  const upload = useCallback(async (file: File) => {
    setLoadingDataset(true)
    setDatasetError(null)
    try {
      const summary = await api.uploadCsv(file)
      setDataset(summary)
      setForecastResult(null)
      setUiStep('idle')
      const suggested = rangeFromDataset(summary.date_range)
      if (suggested) {
        setRangeStart(suggested.start)
        setRangeEnd(suggested.end)
      }
      if (summary.source_kind === 'upload') {
        try {
          await api.startRetrain({ freq: 'both' })
        } catch (e) {
          // Eğitim tetiklenemese bile yükleme başarılıdır; durum /retrain/status üzerinden
          // TrainingProgress tarafından izlenir — burada sadece konsola loglanır.
          console.error('Otomatik model eğitimi başlatılamadı:', e)
        }
      }
    } catch (e) {
      setDatasetError(e instanceof Error ? e.message : 'Dosya yüklenemedi.')
    } finally {
      setLoadingDataset(false)
    }
  }, [])

  const createForecast = useCallback(async () => {
    setForecastError(null)
    setUiStep('progress')
    try {
      const result = await api.runForecast({ start: rangeStart, end: rangeEnd, freq: 'both' })
      setForecastResult(result)
      setUiStep('results')
    } catch (e) {
      setForecastError(e instanceof Error ? e.message : 'Tahmin oluşturulamadı.')
      setUiStep('idle')
    }
  }, [rangeStart, rangeEnd])

  const resetResults = useCallback(() => {
    setForecastResult(null)
    setForecastError(null)
    setUiStep('idle')
  }, [])

  const value: DataContextValue = {
    dataset,
    datasetError,
    loadingDataset,
    loadDemo,
    upload,
    rangeStart,
    rangeEnd,
    setRangeStart,
    setRangeEnd,
    uiStep,
    forecastResult,
    forecastError,
    createForecast,
    resetResults,
  }

  return <DataContext.Provider value={value}>{children}</DataContext.Provider>
}

export function useData(): DataContextValue {
  const ctx = useContext(DataContext)
  if (!ctx) throw new Error('useData, DataProvider içinde kullanılmalı')
  return ctx
}
