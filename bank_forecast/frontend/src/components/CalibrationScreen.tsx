import { useEffect, useMemo, useState } from 'react'
import { useData } from '../context/DataContext'
import * as api from '../api/client'
import type {
  CalibrationConfig,
  CalibrationPreviewResponse,
  CalibrationReport,
  CalibrationScope,
} from '../types'
import { CALIBRATION_PATTERNS, CALIBRATION_PATTERN_LABELS, METRIC_LABELS, METRIC_TYPES } from '../types'
import type { MetricType } from '../types'
import CalibrationPreviewModal from './CalibrationPreviewModal'

type Tab = 'report' | 'multipliers'

const WEEKDAY_LABELS_TR = ['Pazartesi', 'Salı', 'Çarşamba', 'Perşembe', 'Cuma', 'Cumartesi', 'Pazar']

function defaultRange(): { start: string; end: string } {
  const today = new Date()
  const start = new Date(today)
  start.setDate(start.getDate() - 90)
  const fmt = (d: Date) => d.toISOString().slice(0, 10)
  return { start: fmt(start), end: fmt(today) }
}

function emptyConfig(): CalibrationConfig {
  return { multipliers: {}, half_days: [], updated_at: null }
}

export default function CalibrationScreen({ initialScope }: { initialScope: CalibrationScope | null }) {
  const { datasetMap } = useData()

  const [metricType, setMetricType] = useState<MetricType>(initialScope?.metricType ?? 'talimat')
  const [start, setStart] = useState(initialScope?.start ?? defaultRange().start)
  const [end, setEnd] = useState(initialScope?.end ?? defaultRange().end)
  const [team, setTeam] = useState(initialScope?.team ?? '')
  const [type, setType] = useState(initialScope?.type ?? '')
  const [tab, setTab] = useState<Tab>('report')

  const teamOptions = datasetMap[metricType]?.teams ?? []
  const typeOptions = datasetMap[metricType]?.transaction_types ?? []

  // ── Analiz raporu ──────────────────────────────────────────────
  const [minSamples, setMinSamples] = useState(4)
  const [errorThreshold, setErrorThreshold] = useState(15)
  const [report, setReport] = useState<CalibrationReport | null>(null)
  const [analyzing, setAnalyzing] = useState(false)
  const [analyzeError, setAnalyzeError] = useState<string | null>(null)

  const runAnalysis = async () => {
    setAnalyzing(true)
    setAnalyzeError(null)
    try {
      const result = await api.analyzeCalibration({
        metric_type: metricType,
        start,
        end,
        teams: team ? [team] : undefined,
        types: type ? [type] : undefined,
        min_samples: minSamples,
        error_threshold_pct: errorThreshold,
      })
      setReport(result)
    } catch (e) {
      setAnalyzeError(e instanceof Error ? e.message : 'Analiz çalıştırılamadı.')
    } finally {
      setAnalyzing(false)
    }
  }

  useEffect(() => {
    // Yalnızca Tahminleme ekranından bir bağlamla gelindiğinde otomatik çalıştır.
    // setTimeout ile ertelenir ki effect gövdesi içinde senkron setState çağrılmasın.
    if (!initialScope) return
    const timer = setTimeout(() => void runAnalysis(), 0)
    return () => clearTimeout(timer)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // ── Çarpan ayarları ─────────────────────────────────────────────
  const knownTypes = useMemo(() => {
    const set = new Set<string>()
    for (const mt of METRIC_TYPES) datasetMap[mt]?.transaction_types?.forEach((t) => set.add(t))
    return set
  }, [datasetMap])

  const [config, setConfig] = useState<CalibrationConfig>(emptyConfig())
  const [newHalfDay, setNewHalfDay] = useState('')
  const [configError, setConfigError] = useState<string | null>(null)
  const [suggesting, setSuggesting] = useState(false)

  useEffect(() => {
    api
      .getCalibrationConfig()
      .then(setConfig)
      .catch((e) => setConfigError(e instanceof Error ? e.message : 'Kalibrasyon ayarları yüklenemedi.'))
  }, [])

  const displayedTypes = useMemo(() => {
    const set = new Set(knownTypes)
    Object.keys(config.multipliers).forEach((t) => set.add(t))
    return [...set].sort()
  }, [knownTypes, config.multipliers])

  const setMultiplierValue = (tt: string, pattern: string, value: number) => {
    setConfig((prev) => ({
      ...prev,
      multipliers: { ...prev.multipliers, [tt]: { ...prev.multipliers[tt], [pattern]: value } },
    }))
  }

  const fillSuggested = async () => {
    setSuggesting(true)
    setConfigError(null)
    try {
      const result = await api.suggestMultipliers({
        metric_type: metricType,
        start,
        end,
        teams: team ? [team] : undefined,
        types: type ? [type] : undefined,
      })
      setConfig((prev) => {
        const multipliers = { ...prev.multipliers }
        for (const [tt, byPattern] of Object.entries(result.by_type)) {
          multipliers[tt] = { ...multipliers[tt] }
          for (const [pattern, info] of Object.entries(byPattern)) {
            multipliers[tt][pattern] = info.multiplier
          }
        }
        return { ...prev, multipliers }
      })
    } catch (e) {
      setConfigError(e instanceof Error ? e.message : 'Öneri alınamadı — önce bu aralık için bir tahmin/karşılaştırma olduğundan emin olun.')
    } finally {
      setSuggesting(false)
    }
  }

  const addHalfDay = () => {
    if (!newHalfDay) return
    setConfig((prev) => ({
      ...prev,
      half_days: prev.half_days.includes(newHalfDay) ? prev.half_days : [...prev.half_days, newHalfDay].sort(),
    }))
    setNewHalfDay('')
  }
  const removeHalfDay = (d: string) =>
    setConfig((prev) => ({ ...prev, half_days: prev.half_days.filter((x) => x !== d) }))

  const [previewing, setPreviewing] = useState(false)
  const [previewError, setPreviewError] = useState<string | null>(null)
  const [previewResult, setPreviewResult] = useState<CalibrationPreviewResponse | null>(null)
  const [saving, setSaving] = useState(false)

  const requestPreview = async () => {
    setPreviewing(true)
    setPreviewError(null)
    try {
      const result = await api.previewCalibrationConfig({
        metric_type: metricType,
        start,
        end,
        teams: team ? [team] : undefined,
        types: type ? [type] : undefined,
        proposed: { multipliers: config.multipliers, half_days: config.half_days },
      })
      setPreviewResult(result)
    } catch (e) {
      setPreviewError(e instanceof Error ? e.message : 'Önizleme oluşturulamadı — önce bu aralık için kayıtlı bir model/veri olduğundan emin olun.')
    } finally {
      setPreviewing(false)
    }
  }

  const confirmSave = async () => {
    setSaving(true)
    try {
      const saved = await api.saveCalibrationConfig({ multipliers: config.multipliers, half_days: config.half_days })
      setConfig(saved)
      setPreviewResult(null)
    } catch (e) {
      setConfigError(e instanceof Error ? e.message : 'Kaydedilemedi.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="space-y-6">
      <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <h1 className="mb-2 text-base font-semibold text-slate-900">Kalibrasyon</h1>
        <p className="text-sm text-slate-500">
          Gerçekleşen ile tahmin arasındaki sistematik sapmaları ekip × işlem tipi × gün/saat
          kırılımında inceleyin, buradan işlem tipi bazında kalibrasyon çarpanları türetip
          kaydedin — kaydedilen çarpanlar sonraki tüm tahminlere otomatik uygulanır.
        </p>
      </div>

      <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-5">
          <label className="block">
            <span className="mb-1 block text-xs text-slate-500">Metrik</span>
            <select
              value={metricType}
              onChange={(e) => setMetricType(e.target.value as MetricType)}
              className="w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm outline-none focus:border-blue-500"
            >
              {METRIC_TYPES.map((mt) => (
                <option key={mt} value={mt}>{METRIC_LABELS[mt]}</option>
              ))}
            </select>
          </label>
          <label className="block">
            <span className="mb-1 block text-xs text-slate-500">Başlangıç</span>
            <input type="date" value={start} onChange={(e) => setStart(e.target.value)}
              className="w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm outline-none focus:border-blue-500" />
          </label>
          <label className="block">
            <span className="mb-1 block text-xs text-slate-500">Bitiş</span>
            <input type="date" value={end} onChange={(e) => setEnd(e.target.value)}
              className="w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm outline-none focus:border-blue-500" />
          </label>
          <label className="block">
            <span className="mb-1 block text-xs text-slate-500">Ekip (opsiyonel)</span>
            <select value={team} onChange={(e) => setTeam(e.target.value)}
              className="w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm outline-none focus:border-blue-500">
              <option value="">Tümü</option>
              {teamOptions.map((t) => <option key={t} value={t}>{t}</option>)}
            </select>
          </label>
          <label className="block">
            <span className="mb-1 block text-xs text-slate-500">İşlem Tipi (opsiyonel)</span>
            <select value={type} onChange={(e) => setType(e.target.value)}
              className="w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm outline-none focus:border-blue-500">
              <option value="">Tümü</option>
              {typeOptions.map((t) => <option key={t} value={t}>{t}</option>)}
            </select>
          </label>
        </div>
      </div>

      <div className="flex gap-1 border-b border-slate-200">
        {(
          [
            { id: 'report' as const, label: 'Analiz Raporu' },
            { id: 'multipliers' as const, label: 'Çarpan Ayarları' },
          ]
        ).map((t) => (
          <button
            key={t.id}
            type="button"
            onClick={() => setTab(t.id)}
            className={`-mb-px rounded-t-lg border border-b-0 px-5 py-2.5 text-sm font-medium transition-colors ${
              tab === t.id ? 'border-slate-200 bg-white text-blue-600' : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {tab === 'report' && (
        <div className="space-y-4 rounded-2xl border border-slate-200 bg-slate-50/60 p-5">
          <div className="flex flex-wrap items-end gap-4">
            <label className="block">
              <span className="mb-1 block text-xs text-slate-500">Min. gözlem (n)</span>
              <input type="number" min={1} value={minSamples} onChange={(e) => setMinSamples(Number(e.target.value))}
                className="w-24 rounded-md border border-slate-300 bg-white px-3 py-2 text-sm outline-none focus:border-blue-500" />
            </label>
            <label className="block">
              <span className="mb-1 block text-xs text-slate-500">Hata eşiği (%)</span>
              <input type="number" min={0} value={errorThreshold} onChange={(e) => setErrorThreshold(Number(e.target.value))}
                className="w-24 rounded-md border border-slate-300 bg-white px-3 py-2 text-sm outline-none focus:border-blue-500" />
            </label>
            <button
              type="button"
              onClick={() => void runAnalysis()}
              disabled={analyzing}
              className="rounded-md border border-blue-300 bg-blue-50 px-5 py-2.5 text-sm font-medium text-blue-600 transition-colors hover:bg-blue-100 disabled:opacity-50"
            >
              {analyzing ? 'Analiz çalışıyor…' : 'Analizi Çalıştır'}
            </button>
          </div>

          {analyzeError && <p className="text-xs text-red-500">{analyzeError}</p>}

          {report && (
            <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
              <div className="mb-3 text-xs text-slate-500">
                {report.summary.groups_checked} kombinasyon incelendi, {report.summary.hotspot_count} sapma bulundu.
              </div>
              {report.hotspots.length === 0 ? (
                <p className="text-sm text-slate-400">Belirlenen eşiklerde sistematik bir sapma bulunamadı.</p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full min-w-[860px] text-left text-xs text-slate-700">
                    <thead>
                      <tr className="text-slate-500">
                        <th className="pb-1 pr-3 font-medium">Ekip</th>
                        <th className="pb-1 pr-3 font-medium">İşlem Tipi</th>
                        <th className="pb-1 pr-3 font-medium">Gün / Saat</th>
                        <th className="pb-1 pr-3 font-medium">Desen</th>
                        <th className="pb-1 pr-3 font-medium">n</th>
                        <th className="pb-1 pr-3 font-medium">Ort. Gerçekleşen</th>
                        <th className="pb-1 pr-3 font-medium">Ort. Tahmin</th>
                        <th className="pb-1 pr-3 font-medium">%Hata</th>
                        <th className="pb-1 font-medium">Öneri</th>
                      </tr>
                    </thead>
                    <tbody>
                      {report.hotspots.map((h, i) => (
                        <tr key={i} className="border-t border-slate-100 align-top">
                          <td className="py-1.5 pr-3 font-medium text-slate-900">{h.team}</td>
                          <td className="py-1.5 pr-3">{h.transaction_type}</td>
                          <td className="py-1.5 pr-3 whitespace-nowrap">
                            {WEEKDAY_LABELS_TR[h.weekday]}{h.hour !== null ? ` ${String(h.hour).padStart(2, '0')}:00` : ''}
                          </td>
                          <td className="py-1.5 pr-3">{h.pattern ? CALIBRATION_PATTERN_LABELS[h.pattern] : '—'}</td>
                          <td className="py-1.5 pr-3">{h.n}</td>
                          <td className="py-1.5 pr-3">{h.mean_actual.toFixed(0)}</td>
                          <td className="py-1.5 pr-3">{h.mean_predicted.toFixed(0)}</td>
                          <td className={`py-1.5 pr-3 font-semibold ${h.direction === 'under_forecast' ? 'text-red-500' : 'text-amber-600'}`}>
                            {h.pct_error > 0 ? '+' : ''}{h.pct_error.toFixed(1)}%
                          </td>
                          <td className="py-1.5 text-slate-500">{h.recommendation}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {tab === 'multipliers' && (
        <div className="space-y-4 rounded-2xl border border-slate-200 bg-slate-50/60 p-5">
          {configError && <p className="text-xs text-red-500">{configError}</p>}

          <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
            <div className="mb-3 flex items-center justify-between">
              <div className="text-sm font-medium text-slate-800">İşlem Tipi × Desen Çarpanları</div>
              <button
                type="button"
                onClick={() => void fillSuggested()}
                disabled={suggesting}
                className="rounded-md border border-slate-200 px-3 py-1.5 text-xs font-medium text-slate-600 transition-colors hover:border-blue-300 hover:text-blue-600 disabled:opacity-50"
              >
                {suggesting ? 'Hesaplanıyor…' : 'Önerilen değerleri doldur'}
              </button>
            </div>
            {displayedTypes.length === 0 ? (
              <p className="text-sm text-slate-400">Henüz bir işlem tipi bulunamadı — önce veri yükleyin.</p>
            ) : (
              <table className="w-full text-left text-xs text-slate-700">
                <thead>
                  <tr className="text-slate-500">
                    <th className="pb-1 pr-3 font-medium">İşlem Tipi</th>
                    {CALIBRATION_PATTERNS.map((p) => (
                      <th key={p} className="pb-1 pr-3 font-medium">{CALIBRATION_PATTERN_LABELS[p]}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {displayedTypes.map((tt) => (
                    <tr key={tt} className="border-t border-slate-100">
                      <td className="py-1.5 pr-3 font-medium text-slate-900">{tt}</td>
                      {CALIBRATION_PATTERNS.map((p) => (
                        <td key={p} className="py-1.5 pr-3">
                          <input
                            type="number"
                            step="0.01"
                            min={0.1}
                            max={5}
                            value={config.multipliers[tt]?.[p] ?? 1.0}
                            onChange={(e) => setMultiplierValue(tt, p, Number(e.target.value))}
                            className="w-20 rounded-md border border-slate-300 bg-white px-2 py-1 text-xs outline-none focus:border-blue-500"
                          />
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>

          <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
            <div className="mb-3 text-sm font-medium text-slate-800">Yarım Gün Tarihleri</div>
            <div className="mb-3 flex flex-wrap gap-2">
              {config.half_days.length === 0 && <span className="text-xs text-slate-400">Tanımlı yarım gün yok.</span>}
              {config.half_days.map((d) => (
                <span key={d} className="inline-flex items-center gap-1.5 rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs text-slate-600">
                  {d}
                  <button type="button" onClick={() => removeHalfDay(d)} className="text-slate-400 hover:text-red-500">×</button>
                </span>
              ))}
            </div>
            <div className="flex items-center gap-2">
              <input type="date" value={newHalfDay} onChange={(e) => setNewHalfDay(e.target.value)}
                className="rounded-md border border-slate-300 bg-white px-3 py-2 text-sm outline-none focus:border-blue-500" />
              <button type="button" onClick={addHalfDay}
                className="rounded-md border border-slate-200 px-3 py-2 text-xs font-medium text-slate-600 transition-colors hover:border-blue-300 hover:text-blue-600">
                Ekle
              </button>
            </div>
          </div>

          {previewError && <p className="text-xs text-red-500">{previewError}</p>}

          <div className="flex items-center justify-between">
            {config.updated_at && (
              <p className="text-xs text-slate-400">Son kayıt: {new Date(config.updated_at).toLocaleString('tr-TR')}</p>
            )}
            <button
              type="button"
              onClick={() => void requestPreview()}
              disabled={previewing}
              className="ml-auto rounded-md border border-blue-300 bg-blue-600 px-5 py-2.5 text-sm font-medium text-white transition-colors hover:bg-blue-700 disabled:opacity-50"
            >
              {previewing ? 'Önizleme hazırlanıyor…' : 'Kaydet'}
            </button>
          </div>
        </div>
      )}

      {previewResult && (
        <CalibrationPreviewModal
          preview={previewResult}
          saving={saving}
          onConfirm={() => void confirmSave()}
          onCancel={() => setPreviewResult(null)}
        />
      )}
    </div>
  )
}
