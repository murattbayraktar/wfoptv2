import type { ForecastResponse } from '../types'

export default function TotalCountCard({ result }: { result: ForecastResponse }) {
  const { totals, forecast } = result
  const { start, end } = forecast.forecast_range

  return (
    <div className="rounded-xl border border-navy-700 bg-navy-900 p-6">
      <div className="text-xs uppercase tracking-wider text-slate-400">
        {start} – {end} aralığında beklenen toplam işlem kaydı
      </div>
      <div className="mt-2 text-4xl font-semibold text-gold-400">
        {totals.total_predicted.toLocaleString('tr-TR', { maximumFractionDigits: 0 })}
      </div>
      <div className="mt-4 flex flex-wrap gap-2">
        {Object.entries(totals.by_type).map(([type, info]) => (
          <span
            key={type}
            className="rounded-full border border-navy-600 bg-navy-800 px-3 py-1 text-xs text-slate-300"
          >
            {type}: {info.predicted_count.toLocaleString('tr-TR', { maximumFractionDigits: 0 })}
          </span>
        ))}
      </div>
    </div>
  )
}
