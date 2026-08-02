import { useEffect, useMemo, useState } from 'react'
import { useData } from '../context/DataContext'
import type { CalibrationScope, MetricForecastResult, MetricType } from '../types'
import { METRIC_LABELS, METRIC_TYPES } from '../types'
import ModelSummaryCard from './ModelSummaryCard'
import TotalCountCard from './TotalCountCard'
import MapeSummaryCard from './MapeSummaryCard'
import DailyForecastChart from './DailyForecastChart'
import HourlyBreakdownChart from './HourlyBreakdownChart'
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

  const combos = useMemo(() => {
    const list: { team: string; type: string }[] = []
    for (const [team, byType] of Object.entries(result.forecast.by_team)) {
      for (const type of Object.keys(byType)) list.push({ team, type })
    }
    return list
  }, [result])

  const [activeKey, setActiveKey] = useState(combos[0] ? `${combos[0].team}::${combos[0].type}` : '')
  const active = combos.find((c) => `${c.team}::${c.type}` === activeKey) ?? combos[0]

  return (
    <div className="space-y-4 rounded-2xl border border-slate-200 bg-slate-50/60 p-5">
      <div className="text-base font-semibold text-slate-900">{METRIC_LABELS[metricType]}</div>

      <TotalCountCard result={result} />
      <MapeSummaryCard mapeSummary={result.mape_summary} label={METRIC_LABELS[metricType]} />

      {!active ? (
        <p className="text-sm text-slate-400">Bu metrik için tahmin sonucu yok.</p>
      ) : (
        <>
          <div>
            <div className="mb-3 text-xs font-semibold uppercase tracking-wider text-slate-500">
              Ekip ve İşlem Tipi
            </div>
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {combos.map(({ team, type }) => {
                const key = `${team}::${type}`
                return (
                  <ModelSummaryCard
                    key={key}
                    type={`${team} / ${type}`}
                    info={result.forecast.by_team[team][type]}
                    active={key === activeKey}
                    onSelect={() => setActiveKey(key)}
                  />
                )
              })}
            </div>
          </div>

          {(() => {
            const info = result.forecast.by_team[active.team][active.type]
            const hasHourly = !!info.hourly && Object.keys(info.hourly).length > 0
            const dailyComparisonHasType = result.comparison.daily.by_team[active.team]?.[active.type]
            const hourlyComparisonHasType = result.comparison.hourly.by_team[active.team]?.[active.type]

            return (
              <>
                <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
                  <div className="mb-4 flex items-center justify-between">
                    <span className="text-xs font-medium uppercase tracking-wider text-slate-500">
                      Grafik görünümü — {active.team} / {active.type}
                    </span>
                    <div className="flex items-center gap-3">
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
                      <button
                        type="button"
                        onClick={() =>
                          onGoToCalibration({
                            metricType,
                            team: active.team,
                            type: active.type,
                            start: result.forecast.forecast_range.start,
                            end: result.forecast.forecast_range.end,
                          })
                        }
                        className="rounded-full border border-blue-200 bg-blue-50 px-3 py-1 text-xs font-medium text-blue-600 transition-colors hover:bg-blue-100"
                      >
                        Kalibrasyon Analizi Çalıştır
                      </button>
                    </div>
                  </div>

                  {showHourly && hasHourly ? (
                    <HourlyBreakdownChart
                      team={active.team}
                      type={active.type}
                      info={info}
                      comparison={result.comparison.hourly}
                    />
                  ) : (
                    <DailyForecastChart type={`${active.team} / ${active.type}`} info={info} />
                  )}
                </div>

                {(dailyComparisonHasType || hourlyComparisonHasType) && (
                  <ActualVsPredictedChart
                    team={active.team}
                    type={active.type}
                    info={info}
                    comparison={showHourly && hourlyComparisonHasType ? result.comparison.hourly : result.comparison.daily}
                  />
                )}
              </>
            )
          })()}
        </>
      )}
    </div>
  )
}

export default function ResultsPanel({ onGoToCalibration }: { onGoToCalibration: (scope: CalibrationScope) => void }) {
  const { forecastResult, resetResults } = useData()

  const loadedMetrics = useMemo(
    () => METRIC_TYPES.filter((mt) => forecastResult?.[mt]),
    [forecastResult],
  )

  const [activeMetric, setActiveMetric] = useState<MetricType | undefined>(loadedMetrics[0])

  useEffect(() => {
    if (!activeMetric || !loadedMetrics.includes(activeMetric)) {
      setActiveMetric(loadedMetrics[0])
    }
  }, [loadedMetrics, activeMetric])

  if (!forecastResult) return null

  const generatedAt = loadedMetrics.map((mt) => forecastResult[mt]?.forecast.generated_at).find(Boolean)
  const active = activeMetric && loadedMetrics.includes(activeMetric) ? activeMetric : loadedMetrics[0]

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

      {loadedMetrics.length > 1 && (
        <div className="flex gap-1 border-b border-slate-200">
          {loadedMetrics.map((mt) => (
            <button
              key={mt}
              type="button"
              onClick={() => setActiveMetric(mt)}
              className={`-mb-px rounded-t-lg border border-b-0 px-5 py-2.5 text-sm font-medium transition-colors ${
                active === mt
                  ? 'border-slate-200 bg-white text-blue-600'
                  : 'border-transparent text-slate-500 hover:text-slate-800'
              }`}
            >
              {METRIC_LABELS[mt]}
            </button>
          ))}
        </div>
      )}

      {active && forecastResult[active] && (
        <MetricSection
          key={active}
          metricType={active}
          result={forecastResult[active]!}
          onGoToCalibration={onGoToCalibration}
        />
      )}
    </div>
  )
}
