import {
  Area,
  CartesianGrid,
  ComposedChart,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import type { ForecastByType } from '../types'

export default function DailyForecastChart({ type, info }: { type: string; info: ForecastByType }) {
  const daily = info.daily ?? []
  if (daily.length === 0) {
    return <p className="text-sm text-slate-500">Bu tip için günlük tahmin verisi yok.</p>
  }

  const data = daily.map((d) => ({
    date: d.date,
    predicted: d.predicted_count,
    lower: d.lower_80,
    band: Math.max(d.upper_80 - d.lower_80, 0),
  }))

  return (
    <div>
      <div className="mb-3 text-sm font-medium text-slate-200">
        {type} — Günlük Tahmin <span className="text-slate-500">(%80 güven bandı ile)</span>
      </div>
      <ResponsiveContainer width="100%" height={300}>
        <ComposedChart data={data} margin={{ top: 8, right: 16, bottom: 0, left: -16 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1b2740" />
          <XAxis dataKey="date" tick={{ fill: '#94a3b8', fontSize: 11 }} minTickGap={24} />
          <YAxis tick={{ fill: '#94a3b8', fontSize: 11 }} />
          <Tooltip
            contentStyle={{ background: '#0c1322', border: '1px solid #2a3a5c', borderRadius: 8, fontSize: 12 }}
            labelStyle={{ color: '#e2e8f0' }}
          />
          <Area dataKey="lower" stackId="band" stroke="none" fill="transparent" isAnimationActive={false} />
          <Area
            dataKey="band"
            stackId="band"
            stroke="none"
            fill="#e8b54a"
            fillOpacity={0.12}
            isAnimationActive={false}
            name="80% güven aralığı"
          />
          <Line
            dataKey="predicted"
            stroke="#e8b54a"
            strokeWidth={2}
            dot={false}
            name="Tahmin edilen kayıt"
            isAnimationActive={false}
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  )
}
