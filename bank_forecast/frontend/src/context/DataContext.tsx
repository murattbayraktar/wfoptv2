import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState, type ReactNode } from 'react'
import * as api from '../api/client'
import type { ForecastParams } from '../api/client'
import type {
  AvailableModelsResponse,
  DatasetSummary,
  DatasetSummaryMap,
  ForecastResponse,
  MetricType,
  RetrainStatus,
} from '../types'
import { METRIC_TYPES } from '../types'

const RETRAIN_POLL_INTERVAL_MS = 1500

export type UiStep = 'idle' | 'progress' | 'results'

interface MetricUiState {
  dataset: DatasetSummary | null
  trainModels: string[]
  toggleTrainModel: (v: string) => void
  holdoutDays: number
  setHoldoutDays: (v: number) => void
  startTraining: () => Promise<void>
  startingTraining: boolean
  trainingStartError: string | null
  retrainStatus: RetrainStatus | null
  availableModels: AvailableModelsResponse | null
}

interface DataContextValue {
  datasetMap: DatasetSummaryMap
  anyLoaded: boolean
  datasetError: string | null
  loadingDataset: boolean
  upload: (file: File) => Promise<void>

  talimat: MetricUiState
  islem: MetricUiState

  teamOptions: string[]
  selectedTeam: string
  setSelectedTeam: (v: string) => void

  rangeStart: string
  rangeEnd: string
  setRangeStart: (v: string) => void
  setRangeEnd: (v: string) => void

  forecastModels: string[]
  toggleForecastModel: (v: string) => void

  uiStep: UiStep
  forecastResult: ForecastResponse | null
  forecastError: string | null
  createForecast: () => Promise<void>
  resetResults: () => void

  exportExcel: () => Promise<void>
  exporting: boolean
  exportError: string | null
}

const DataContext = createContext<DataContextValue | null>(null)

const EMPTY_DATASET_MAP: DatasetSummaryMap = { talimat: null, islem: null }

function defaultRange(): { start: string; end: string } {
  return { start: '2026-02-02', end: '2026-02-06' }
}

function useMetricState(metricType: MetricType, dataset: DatasetSummary | null) {
  const [trainModels, setTrainModels] = useState<string[]>(['xgboost', 'lightgbm'])
  const [holdoutDays, setHoldoutDays] = useState<number>(0)
  const [startingTraining, setStartingTraining] = useState(false)
  const [trainingStartError, setTrainingStartError] = useState<string | null>(null)
  const [retrainStatus, setRetrainStatus] = useState<RetrainStatus | null>(null)
  const [availableModels, setAvailableModels] = useState<AvailableModelsResponse | null>(null)

  const refreshAvailableModels = useCallback(() => {
    api
      .getAvailableModels(metricType)
      .then(setAvailableModels)
      .catch(() => {
        // model listesi alınamazsa tahmin ekranı varsayılan (best_model) ile çalışmaya devam eder
      })
  }, [metricType])

  useEffect(() => {
    refreshAvailableModels()
  }, [refreshAvailableModels])

  const prevStatusRef = useRef<string | null>(null)
  useEffect(() => {
    const prev = prevStatusRef.current
    const current = retrainStatus?.status ?? null
    if (prev === 'running' && current === 'done') refreshAvailableModels()
    prevStatusRef.current = current
  }, [retrainStatus?.status, refreshAvailableModels])

  const trackingRetrain = dataset?.loaded

  useEffect(() => {
    if (!trackingRetrain) {
      setRetrainStatus(null)
      return
    }
    let cancelled = false
    let timer: ReturnType<typeof setTimeout> | undefined

    async function tick() {
      try {
        const next = await api.getRetrainStatus(metricType)
        if (cancelled) return
        setRetrainStatus(next)
      } finally {
        if (!cancelled) timer = setTimeout(tick, RETRAIN_POLL_INTERVAL_MS)
      }
    }

    void tick()
    return () => {
      cancelled = true
      if (timer) clearTimeout(timer)
    }
  }, [trackingRetrain, metricType])

  const toggleTrainModel = useCallback((value: string) => {
    setTrainModels((prev) => {
      if (value === 'auto') return ['auto']
      const withoutAuto = prev.filter((m) => m !== 'auto')
      const next = withoutAuto.includes(value)
        ? withoutAuto.filter((m) => m !== value)
        : [...withoutAuto, value]
      return next.length > 0 ? next : ['auto']
    })
  }, [])

  const startTraining = useCallback(async () => {
    if (retrainStatus?.status === 'running') return
    setStartingTraining(true)
    setTrainingStartError(null)
    try {
      const models = trainModels.includes('auto') ? undefined : trainModels
      await api.startRetrain({
        metric_type: metricType,
        freq: 'both',
        models,
        holdout_days: holdoutDays > 0 ? holdoutDays : undefined,
      })
      setRetrainStatus(await api.getRetrainStatus(metricType))
    } catch (e) {
      setTrainingStartError(e instanceof Error ? e.message : 'Eğitim başlatılamadı.')
    } finally {
      setStartingTraining(false)
    }
  }, [metricType, trainModels, holdoutDays, retrainStatus])

  return {
    dataset,
    trainModels,
    toggleTrainModel,
    holdoutDays,
    setHoldoutDays,
    startTraining,
    startingTraining,
    trainingStartError,
    retrainStatus,
    availableModels,
  } satisfies MetricUiState
}

export function DataProvider({ children }: { children: ReactNode }) {
  const [datasetMap, setDatasetMap] = useState<DatasetSummaryMap>(EMPTY_DATASET_MAP)
  const [datasetError, setDatasetError] = useState<string | null>(null)
  const [loadingDataset, setLoadingDataset] = useState(false)

  const initialRange = defaultRange()
  const [rangeStart, setRangeStart] = useState(initialRange.start)
  const [rangeEnd, setRangeEnd] = useState(initialRange.end)

  const [selectedTeam, setSelectedTeam] = useState<string>('')
  const [forecastModels, setForecastModels] = useState<string[]>([])

  const [uiStep, setUiStep] = useState<UiStep>('idle')
  const [forecastResult, setForecastResult] = useState<ForecastResponse | null>(null)
  const [forecastError, setForecastError] = useState<string | null>(null)
  const [lastForecastParams, setLastForecastParams] = useState<ForecastParams | null>(null)

  const [exporting, setExporting] = useState(false)
  const [exportError, setExportError] = useState<string | null>(null)

  const talimat = useMetricState('talimat', datasetMap.talimat)
  const islem = useMetricState('islem', datasetMap.islem)

  useEffect(() => {
    api
      .getDatasetSummary()
      .then((summaryMap) => {
        setDatasetMap(summaryMap)
      })
      .catch(() => {
        // sayfa açılışında özet alınamazsa sessizce "veri yok" durumunda kalınır
      })
  }, [])

  const applySummary = useCallback((summaryMap: DatasetSummaryMap) => {
    setDatasetMap(summaryMap)
    setForecastResult(null)
    setUiStep('idle')
  }, [])

  const upload = useCallback(async (file: File) => {
    setLoadingDataset(true)
    setDatasetError(null)
    try {
      const summaryMap = await api.uploadCsv(file)
      applySummary(summaryMap)
    } catch (e) {
      setDatasetError(e instanceof Error ? e.message : 'Dosya yüklenemedi.')
    } finally {
      setLoadingDataset(false)
    }
  }, [applySummary])

  const teamOptions = useMemo(() => {
    const set = new Set<string>()
    for (const avail of [talimat.availableModels, islem.availableModels]) {
      if (avail) Object.keys(avail.available).forEach((t) => set.add(t))
    }
    if (set.size === 0) {
      for (const mt of METRIC_TYPES) {
        datasetMap[mt]?.teams?.forEach((t) => set.add(t))
      }
    }
    return [...set].sort()
  }, [talimat.availableModels, islem.availableModels, datasetMap])

  const toggleForecastModel = useCallback((value: string) => {
    setForecastModels((prev) =>
      prev.includes(value) ? prev.filter((m) => m !== value) : [...prev, value],
    )
  }, [])

  const createForecast = useCallback(async () => {
    setForecastError(null)
    setUiStep('progress')
    const params: ForecastParams = {
      start: rangeStart,
      end: rangeEnd,
      freq: 'both',
      metric_type: 'both',
      teams: selectedTeam ? [selectedTeam] : undefined,
      models: forecastModels.length > 0 ? forecastModels : undefined,
    }
    try {
      const result = await api.runForecast(params)
      setForecastResult(result)
      setLastForecastParams(params)
      setUiStep('results')
    } catch (e) {
      setForecastError(e instanceof Error ? e.message : 'Tahmin oluşturulamadı.')
      setUiStep('idle')
    }
  }, [rangeStart, rangeEnd, selectedTeam, forecastModels])

  const resetResults = useCallback(() => {
    setForecastResult(null)
    setForecastError(null)
    setUiStep('idle')
  }, [])

  const exportExcel = useCallback(async () => {
    if (!lastForecastParams) return
    setExporting(true)
    setExportError(null)
    try {
      const blob = await api.exportForecastExcel(lastForecastParams)
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `tahmin_${lastForecastParams.start}_${lastForecastParams.end}.xlsx`
      document.body.appendChild(a)
      a.click()
      a.remove()
      URL.revokeObjectURL(url)
    } catch (e) {
      setExportError(e instanceof Error ? e.message : 'Excel dosyası oluşturulamadı.')
    } finally {
      setExporting(false)
    }
  }, [lastForecastParams])

  const value: DataContextValue = {
    datasetMap,
    anyLoaded: !!(datasetMap.talimat?.loaded || datasetMap.islem?.loaded),
    datasetError,
    loadingDataset,
    upload,
    talimat,
    islem,
    teamOptions,
    selectedTeam,
    setSelectedTeam,
    rangeStart,
    rangeEnd,
    setRangeStart,
    setRangeEnd,
    forecastModels,
    toggleForecastModel,
    uiStep,
    forecastResult,
    forecastError,
    createForecast,
    resetResults,
    exportExcel,
    exporting,
    exportError,
  }

  return <DataContext.Provider value={value}>{children}</DataContext.Provider>
}

export function useData(): DataContextValue {
  const ctx = useContext(DataContext)
  if (!ctx) throw new Error('useData, DataProvider içinde kullanılmalı')
  return ctx
}
