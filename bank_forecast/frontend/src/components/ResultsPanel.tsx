import { useEffect, useMemo, useState } from 'react'
import { useData } from '../context/DataContext'
import type { CalibrationScope, MetricForecastResult, MetricType } from '../types'
import { METRIC_LABELS, METRIC_TYPES } from '../types'
import TypeMultiSelect from './TypeMultiSelect'
import TotalCountCard from './TotalCountCard'
import MapeOverviewCard from './MapeOverviewCard'
import MultiTypeForecastChart from './MultiTypeForecastChart'
import TypeBreakdownTable from './TypeBreakdownTable'
import ActualVsPredictedChart from './ActualVsPredictedChart'
import ExportToExcelButton from './ExportToExcelButton'

function MetricSection({
  metricType,
  result,
  onGoToCalibration,
}: {
  metricType: MetricType
  result: MetricForecastResult
  onGoToCalibration: (scope: CalibrationScope) => void
}) {
  const [showHourly, setShowHourly] = useState(false)

  const teams = useMemo(() => Object.keys(result.forecast.by_team), [result])
  const [activeTeam, setActiveTeam] = useState(teams[0] ?? '')
  const team = teams.includes(activeTeam) ? activeTeam : teams[0]

  const byType = team ? result.forecast.by_team[team] : undefined
  const types = useMemo(() => (byType ? Object.keys(byType) : []), [byType])

  const [selectedTypes, setSelectedTypes] = useState<string[]>(types)

  useEffect(() => {
    setSelectedTypes(types)
    // İşlem tipi seçimi, sadece ekip değiştiğinde veya yeni bir tahmin sonucu geldiğinde tüm tiplere sıfırlanır.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [team, result.forecast.generated_at])

  const toggleType = (type: string) => {
    setSelectedTypes((prev) => (prev.includes(type) ? prev.filter((t) => t !== type) : [...prev, type]))
  }

  if (!team || !byType) {
    return <p className="text-sm text-slate-400">Bu metrik için tahmin sonucu yok.</p>
  }

  const hasHourly = selectedTypes.some(
    (t) => byType[t]?.hourly && Object.keys(byType[t].hourly!).length > 0,
  )
  const singleType = selectedTypes.length === 1 ? selectedTypes[0] : undefined
  const singleInfo = singleType ? byType[singleType] : undefined
  const dailyComparisonHasType = singleType ? result.comparison.daily.by_team[team]?.[singleType] : undefined
  const hourlyComparisonHasType = singleType ? result.comparison.hourly.by_team[team]?.[singleType] : undefined

  return (
    <div className="space-y-4 rounded-2xl border border-slate-200 bg-slate-50/60 p-5">
      <div className="text-base font-semibold text-slate-900">{METRIC_LABELS[metricType]}</div>

      <div>
        <div className="mb-2 text-xs font-semibold uppercase tracking-wider text-slate-500">Ekip</div>
        <div className="flex w-fit flex-wrap gap-1 rounded-lg border border-slate-200 bg-white p-1 text-xs">
          {teams.map((t) => (
            <button
              key={t}
              type="button"
              onClick={() => setActiveTeam(t)}
              className={`rounded-md px-3 py-1.5 font-medium transition-colors ${
                team === t ? 'bg-blue-600 text-white shadow-sm' : 'text-slate-500 hover:text-slate-800'
              }`}
            >
              {t}
            </button>
          ))}
        </div>
      </div>

      <TotalCountCard result={result} team={team} />

      <div>
        <div className="mb-3 text-xs font-semibold uppercase tracking-wider text-slate-500">
          İşlem Tipi (çoklu seçim)
        </div>
        <TypeMultiSelect
          types={types}
          byType={byType}
          selected={selectedTypes}
          onToggle={toggleType}
          onSelectAll={() => setSelectedTypes(types)}
          onClear={() => setSelectedTypes([])}
        />
      </div>

      {selectedTypes.length === 0 ? (
        <p className="text-sm text-slate-400">Grafik için en az bir işlem tipi seçin.</p>
      ) : (
        <>
          <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
            <div className="mb-4 flex items-center justify-between">
              <span className="text-xs font-medium uppercase tracking-wider text-slate-500">
                Grafik görünümü — {team}
              </span>
              {hasHourly && (
                <div className="flex gap-2 text-xs">
                  <button
                    type="button"
                    onClick={() => setShowHourly(false)}
                    className={`rounded-full px-3 py-1 transition-colors ${
                      !showHourly ? 'bg-blue-600 text-white shadow-sm' : 'border border-slate-200 text-slate-600 hover:border-slate-300'
                    }`}
                  >
                    Günlük
                  </button>
                  <button
                    type="button"
                    onClick={() => setShowHourly(true)}
                    className={`rounded-full px-3 py-1 transition-colors ${
                      showHourly ? 'bg-blue-600 text-white shadow-sm' : 'border border-slate-200 text-slate-600 hover:border-slate-300'
                    }`}
                  >
                    Saatlik Kırılım
                  </button>
                </div>
              )}
            </div>

            <MultiTypeForecastChart
              types={selectedTypes}
              byType={byType}
              mode={showHourly && hasHourly ? 'hourly' : 'daily'}
            />
          </div>

          {singleType && singleInfo && (dailyComparisonHasType || hourlyComparisonHasType) && (
            <ActualVsPredictedChart
              team={team}
              type={singleType}
              info={singleInfo}
              comparison={showHourly && hourlyComparisonHasType ? result.comparison.hourly : result.comparison.daily}
            />
          )}

          <TypeBreakdownTable
            metricType={metricType}
            team={team}
            types={selectedTypes}
            byType={byType}
            rangeStart={result.forecast.forecast_range.start}
            rangeEnd={result.forecast.forecast_range.end}
            comparison={result.comparison.daily}
            onGoToCalibration={onGoToCalibration}
          />
        </>
      )}
    </div>
  )
}

type ResultsTab = MetricType | 'mape'

export default function ResultsPanel({ onGoToCalibration }: { onGoToCalibration: (scope: CalibrationScope) => void }) {
  const { forecastResult, resetResults } = useData()

  const loadedMetrics = useMemo(
    () => METRIC_TYPES.filter((mt) => forecastResult?.[mt]),
    [forecastResult],
  )

  const [activeTab, setActiveTab] = useState<ResultsTab | undefined>(loadedMetrics[0])

  useEffect(() => {
    if (!activeTab || (activeTab !== 'mape' && !loadedMetrics.includes(activeTab))) {
      setActiveTab(loadedMetrics[0])
    }
  }, [loadedMetrics, activeTab])

  if (!forecastResult) return null

  const generatedAt = loadedMetrics.map((mt) => forecastResult[mt]?.forecast.generated_at).find(Boolean)
  const active =
    activeTab && (activeTab === 'mape' || loadedMetrics.includes(activeTab)) ? activeTab : loadedMetrics[0]

  const tabs: { id: ResultsTab; label: string }[] = [
    ...loadedMetrics.map((mt) => ({ id: mt as ResultsTab, label: METRIC_LABELS[mt] })),
    ...(loadedMetrics.length > 0 ? [{ id: 'mape' as ResultsTab, label: 'Mape Özet' }] : []),
  ]

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <div className="text-lg font-semibold text-slate-900">Tahmin Sonuçları</div>
          {generatedAt && (
            <div className="text-xs text-slate-400">
              Oluşturulma zamanı: {new Date(generatedAt).toLocaleString('tr-TR')}
            </div>
          )}
        </div>
        <div className="flex items-center gap-3">
          <ExportToExcelButton />
          <button
            type="button"
            onClick={resetResults}
            className="rounded-md border border-slate-200 px-3 py-1.5 text-xs text-slate-600 transition-colors hover:border-blue-300 hover:text-blue-600"
          >
            Yeni tahmin
          </button>
        </div>
      </div>

      {loadedMetrics.length === 0 && (
        <p className="text-sm text-slate-400">Seçilen ekip/aralık için tahmin bulunamadı.</p>
      )}

      {tabs.length > 1 && (
        <div className="flex gap-1 border-b border-slate-200">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              type="button"
              onClick={() => setActiveTab(tab.id)}
              className={`-mb-px rounded-t-lg border border-b-0 px-5 py-2.5 text-sm font-medium transition-colors ${
                active === tab.id
                  ? 'border-slate-200 bg-white text-blue-600'
                  : 'border-transparent text-slate-500 hover:text-slate-800'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      )}

      {active === 'mape' ? (
        <div className="space-y-4">
          {loadedMetrics.map((mt) => (
            <MapeOverviewCard key={mt} label={METRIC_LABELS[mt]} mapeSummary={forecastResult[mt]!.mape_summary} />
          ))}
        </div>
      ) : (
        active &&
        forecastResult[active] && (
          <MetricSection
            key={active}
            metricType={active}
            result={forecastResult[active]!}
            onGoToCalibration={onGoToCalibration}
          />
        )
      )}
    </div>
  )
}
