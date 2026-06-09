import { useMemo, useState } from 'react'
import { useData } from '../context/DataContext'
import ModelSummaryCard from './ModelSummaryCard'
import TotalCountCard from './TotalCountCard'
import DailyForecastChart from './DailyForecastChart'
import HourlyBreakdownChart from './HourlyBreakdownChart'
import ActualVsPredictedChart from './ActualVsPredictedChart'

export default function ResultsPanel() {
  const { forecastResult, resetResults } = useData()
  const [showHourly, setShowHourly] = useState(false)

  const types = useMemo(
    () => (forecastResult ? Object.keys(forecastResult.forecast.by_type) : []),
    [forecastResult],
  )
  const [activeType, setActiveType] = useState(types[0] ?? '')

  if (!forecastResult) return null

  const selected = types.includes(activeType) ? activeType : types[0]
  const info = forecastResult.forecast.by_type[selected]
  const hasHourly = !!info?.hourly && Object.keys(info.hourly).length > 0
  const dailyComparisonHasType = forecastResult.comparison.daily.by_type[selected]
  const hourlyComparisonHasType = forecastResult.comparison.hourly.by_type[selected]

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <div className="text-lg font-semibold text-slate-900">Tahmin Sonuçları</div>
          <div className="text-xs text-slate-400">
            Oluşturulma zamanı: {new Date(forecastResult.forecast.generated_at).toLocaleString('tr-TR')}
          </div>
        </div>
        <button
          type="button"
          onClick={resetResults}
          className="rounded-md border border-slate-200 px-3 py-1.5 text-xs text-slate-600 transition-colors hover:border-blue-300 hover:text-blue-600"
        >
          Yeni tahmin
        </button>
      </div>

      <TotalCountCard result={forecastResult} />

      <div>
        <div className="mb-3 text-xs font-semibold uppercase tracking-wider text-slate-500">
          İşlem Tipi ve Kullanılan Algoritma
        </div>
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {types.map((tt) => (
            <ModelSummaryCard
              key={tt}
              type={tt}
              info={forecastResult.forecast.by_type[tt]}
              active={tt === selected}
              onSelect={() => setActiveType(tt)}
            />
          ))}
        </div>
      </div>

      <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="mb-4 flex items-center justify-between">
          <span className="text-xs font-medium uppercase tracking-wider text-slate-500">Grafik görünümü — {selected}</span>
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

        {showHourly && hasHourly ? (
          <HourlyBreakdownChart type={selected} info={info} comparison={forecastResult.comparison.hourly} />
        ) : (
          <DailyForecastChart type={selected} info={info} />
        )}
      </div>

      {(dailyComparisonHasType || hourlyComparisonHasType) && (
        <ActualVsPredictedChart
          type={selected}
          info={info}
          comparison={showHourly && hourlyComparisonHasType ? forecastResult.comparison.hourly : forecastResult.comparison.daily}
        />
      )}
    </div>
  )
}
