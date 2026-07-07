import type { MetricForecastResult } from '../types'

export default function TotalCountCard({ result }: { result: MetricForecastResult }) {
  const { totals, forecast } = result
  const { start, end } = forecast.forecast_range

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="text-xs uppercase tracking-wider text-slate-500">
        {start} – {end} aralığında beklenen toplam kayıt
      </div>
      <div className="mt-2 text-4xl font-semibold text-blue-700">
        {totals.total_predicted.toLocaleString('tr-TR', { maximumFractionDigits: 0 })}
      </div>
      <div className="mt-4 space-y-2">
        {Object.entries(totals.by_team).map(([team, teamInfo]) => (
          <div key={team}>
            <div className="mb-1 text-xs font-medium text-slate-600">
              {team}: {teamInfo.predicted_count.toLocaleString('tr-TR', { maximumFractionDigits: 0 })}
            </div>
            <div className="flex flex-wrap gap-2">
              {Object.entries(teamInfo.by_type).map(([type, info]) => (
                <span
                  key={type}
                  className="rounded-full border border-slate-200 bg-slate-100 px-3 py-1 text-xs text-slate-600"
                >
                  {type}: {info.predicted_count.toLocaleString('tr-TR', { maximumFractionDigits: 0 })}
                </span>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
