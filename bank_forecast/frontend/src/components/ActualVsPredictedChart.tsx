import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import type { ComparisonResult, ForecastByType } from '../types'
import { MODEL_COLORS, MODEL_LABELS } from '../constants'

const ACTUAL_COLOR = '#94a3b8'

export default function ActualVsPredictedChart({
  type,
  info,
  comparison,
}: {
  type: string
  info: ForecastByType
  comparison: ComparisonResult
}) {
  const rows = comparison.by_type[type]
  if (!comparison.has_overlap || !rows || rows.length === 0) return null

  const modelNames = info.models && Object.keys(info.models).length > 1 ? Object.keys(info.models).sort() : []

  const data = rows.map((r) => {
    const row: Record<string, string | number> = {
      label: r.hour !== undefined ? `${r.date} ${r.hour}:00` : r.date,
      actual: r.actual_count,
    }
    if (modelNames.length === 0) {
      row.predicted = r.predicted_count
    } else {
      for (const name of modelNames) {
        const series = info.models![name]
        const entry =
          r.hour !== undefined
            ? series.hourly?.[r.date]?.find((h) => h.hour === r.hour)
            : series.daily?.find((d) => d.date === r.date)
        if (entry) row[name] = 'count' in entry ? entry.count : entry.predicted_count
      }
    }
    return row
  })

  return (
    <div className="rounded-xl border border-navy-700 bg-navy-900 p-6">
      <div className="mb-1 text-sm font-medium text-slate-200">{type} — Gerçekleşen vs Tahmin</div>
      <div className="mb-3 text-xs text-slate-500">
        Seçilen aralık geçmiş veriyle örtüşüyor ({comparison.overlap_range?.start} – {comparison.overlap_range?.end});
        gerçekleşen ve tahmin edilen değerler karşılaştırılıyor.
      </div>
      <ResponsiveContainer width="100%" height={280}>
        <LineChart data={data} margin={{ top: 8, right: 16, bottom: 0, left: -16 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1b2740" />
          <XAxis dataKey="label" tick={{ fill: '#94a3b8', fontSize: 11 }} minTickGap={24} />
          <YAxis tick={{ fill: '#94a3b8', fontSize: 11 }} />
          <Tooltip
            contentStyle={{ background: '#0c1322', border: '1px solid #2a3a5c', borderRadius: 8, fontSize: 12 }}
            labelStyle={{ color: '#e2e8f0' }}
          />
          <Legend wrapperStyle={{ fontSize: 12 }} />
          <Line
            dataKey="actual"
            name="Gerçekleşen"
            stroke={ACTUAL_COLOR}
            strokeWidth={2}
            dot={false}
            isAnimationActive={false}
          />
          {modelNames.length === 0 ? (
            <Line
              dataKey="predicted"
              name="Tahmin edilen"
              stroke="#e8b54a"
              strokeWidth={2}
              strokeDasharray="5 4"
              dot={false}
              isAnimationActive={false}
            />
          ) : (
            modelNames.map((name, i) => (
              <Line
                key={name}
                dataKey={name}
                name={MODEL_LABELS[name] ?? name}
                stroke={MODEL_COLORS[i % MODEL_COLORS.length]}
                strokeWidth={2}
                strokeDasharray="5 4"
                dot={false}
                isAnimationActive={false}
                connectNulls
              />
            ))
          )}
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
