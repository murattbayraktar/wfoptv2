import { useState } from 'react'
import {
  Bar,
  BarChart,
  CartesianGrid,
  ComposedChart,
  Legend,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import type { ForecastByType } from '../types'
import { MODEL_COLORS } from '../constants'

const CHART_STYLE = {
  grid: '#e2e8f0',
  tick: '#64748b',
  tooltip: { background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: 8, fontSize: 12 },
  tooltipLabel: { color: '#0f172a' },
}

function DailyOverlay({ types, byType }: { types: string[]; byType: Record<string, ForecastByType> }) {
  const dateSet = new Set<string>()
  for (const type of types) {
    for (const d of byType[type]?.daily ?? []) dateSet.add(d.date)
  }
  const dates = [...dateSet].sort()

  if (dates.length === 0) {
    return <p className="text-sm text-slate-400">Seçili tipler için günlük tahmin verisi yok.</p>
  }

  const data = dates.map((date) => {
    const row: Record<string, string | number> = { date }
    for (const type of types) {
      const entry = (byType[type]?.daily ?? []).find((d) => d.date === date)
      if (entry) row[type] = entry.predicted_count
    }
    return row
  })

  return (
    <ResponsiveContainer width="100%" height={320}>
      <ComposedChart data={data} margin={{ top: 8, right: 16, bottom: 0, left: -16 }}>
        <CartesianGrid strokeDasharray="3 3" stroke={CHART_STYLE.grid} />
        <XAxis dataKey="date" tick={{ fill: CHART_STYLE.tick, fontSize: 11 }} minTickGap={24} />
        <YAxis tick={{ fill: CHART_STYLE.tick, fontSize: 11 }} />
        <Tooltip contentStyle={CHART_STYLE.tooltip} labelStyle={CHART_STYLE.tooltipLabel} />
        <Legend wrapperStyle={{ fontSize: 12 }} />
        {types.map((type, i) => (
          <Line
            key={type}
            dataKey={type}
            name={type}
            stroke={MODEL_COLORS[i % MODEL_COLORS.length]}
            strokeWidth={2}
            dot={false}
            isAnimationActive={false}
            connectNulls
          />
        ))}
      </ComposedChart>
    </ResponsiveContainer>
  )
}

function HourlyOverlay({ types, byType }: { types: string[]; byType: Record<string, ForecastByType> }) {
  const dateSet = new Set<string>()
  for (const type of types) {
    for (const date of Object.keys(byType[type]?.hourly ?? {})) dateSet.add(date)
  }
  const dates = [...dateSet].sort()
  const [selectedDate, setSelectedDate] = useState(dates[0] ?? '')

  if (dates.length === 0) {
    return <p className="text-sm text-slate-400">Seçili tipler için saatlik kırılım verisi yok.</p>
  }

  const activeDate = dates.includes(selectedDate) ? selectedDate : dates[0]

  const hourSet = new Set<number>()
  for (const type of types) {
    for (const h of byType[type]?.hourly?.[activeDate] ?? []) hourSet.add(h.hour)
  }
  const hours = [...hourSet].sort((a, b) => a - b)

  const data = hours.map((hour) => {
    const row: Record<string, string | number> = { hour: `${hour}:00` }
    for (const type of types) {
      const entry = (byType[type]?.hourly?.[activeDate] ?? []).find((h) => h.hour === hour)
      if (entry) row[type] = entry.count
    }
    return row
  })

  return (
    <div>
      <div className="mb-3 flex justify-end">
        <select
          value={activeDate}
          onChange={(e) => setSelectedDate(e.target.value)}
          className="rounded-md border border-slate-300 bg-white px-2 py-1 text-xs text-slate-700 outline-none focus:border-blue-400"
        >
          {dates.map((d) => (
            <option key={d} value={d}>
              {d}
            </option>
          ))}
        </select>
      </div>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={data} margin={{ top: 8, right: 16, bottom: 0, left: -16 }}>
          <CartesianGrid strokeDasharray="3 3" stroke={CHART_STYLE.grid} />
          <XAxis dataKey="hour" tick={{ fill: CHART_STYLE.tick, fontSize: 11 }} />
          <YAxis tick={{ fill: CHART_STYLE.tick, fontSize: 11 }} />
          <Tooltip contentStyle={CHART_STYLE.tooltip} labelStyle={CHART_STYLE.tooltipLabel} />
          <Legend wrapperStyle={{ fontSize: 12 }} />
          {types.map((type, i) => (
            <Bar
              key={type}
              dataKey={type}
              name={type}
              fill={MODEL_COLORS[i % MODEL_COLORS.length]}
              radius={[4, 4, 0, 0]}
              isAnimationActive={false}
            />
          ))}
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}

export default function MultiTypeForecastChart({
  types,
  byType,
  mode,
}: {
  types: string[]
  byType: Record<string, ForecastByType>
  mode: 'daily' | 'hourly'
}) {
  if (types.length === 0) {
    return <p className="text-sm text-slate-400">Grafik için en az bir işlem tipi seçin.</p>
  }

  return mode === 'hourly' ? (
    <HourlyOverlay types={types} byType={byType} />
  ) : (
    <DailyOverlay types={types} byType={byType} />
  )
}
