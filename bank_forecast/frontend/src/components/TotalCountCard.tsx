import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import type { MetricForecastResult } from '../types'
import { MapeBadge } from './MapeBadge'

const CHART_STYLE = {
  grid: '#e2e8f0',
  tick: '#64748b',
  tooltip: { background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: 8, fontSize: 12 },
  tooltipLabel: { color: '#0f172a' },
}

export default function TotalCountCard({ result, team }: { result: MetricForecastResult; team: string }) {
  const { totals, forecast } = result
  const { start, end } = forecast.forecast_range
  const teamTotals = totals.by_team[team]
  const byType = forecast.by_team[team]
  const teamMape = result.mape_summary.by_team[team]?.mape ?? null

  if (!teamTotals || !byType) return null

  const dailyTotals = new Map<string, number>()
  for (const info of Object.values(byType)) {
    for (const d of info.daily ?? []) {
      dailyTotals.set(d.date, (dailyTotals.get(d.date) ?? 0) + d.predicted_count)
    }
  }
  const data = [...dailyTotals.entries()]
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([date, count]) => ({ date, count }))

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="flex items-center justify-between">
        <div className="text-xs uppercase tracking-wider text-slate-500">
          {team} — {start} – {end} aralığında beklenen toplam kayıt
        </div>
        {teamMape !== null && (
          <div className="flex items-center gap-1">
            <span className="text-xs text-slate-400">MAPE:</span>
            <MapeBadge mape={teamMape} />
          </div>
        )}
      </div>
      <div className="mt-2 text-4xl font-semibold text-blue-700">
        {teamTotals.predicted_count.toLocaleString('tr-TR', { maximumFractionDigits: 0 })}
      </div>
      {data.length > 0 && (
        <div className="mt-4">
          <div className="mb-2 text-xs font-medium text-slate-500">Günlük toplam (tüm işlem tipleri)</div>
          <ResponsiveContainer width="100%" height={180}>
            <BarChart data={data} margin={{ top: 8, right: 16, bottom: 0, left: -16 }}>
              <CartesianGrid strokeDasharray="3 3" stroke={CHART_STYLE.grid} />
              <XAxis dataKey="date" tick={{ fill: CHART_STYLE.tick, fontSize: 11 }} minTickGap={24} />
              <YAxis tick={{ fill: CHART_STYLE.tick, fontSize: 11 }} />
              <Tooltip contentStyle={CHART_STYLE.tooltip} labelStyle={CHART_STYLE.tooltipLabel} />
              <Bar dataKey="count" name="Beklenen kayıt" fill="#2563eb" radius={[4, 4, 0, 0]} isAnimationActive={false} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  )
}
