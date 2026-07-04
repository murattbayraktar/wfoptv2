import { useMemo, useState } from 'react'
import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import type { ComparisonResult, ForecastByType } from '../types'
import { MODEL_COLORS, MODEL_LABELS } from '../constants'

const ACTUAL_COLOR = '#94a3b8'

const CHART_STYLE = {
  grid: '#e2e8f0',
  tick: '#64748b',
  tooltip: { background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: 8, fontSize: 12 },
  tooltipLabel: { color: '#0f172a' },
}

function OverlayHourlyChart({
  team,
  type,
  models,
  comparison,
}: {
  team: string
  type: string
  models: Record<string, ForecastByType>
  comparison?: ComparisonResult
}) {
  const names = Object.keys(models).sort()

  const dateSet = new Set<string>()
  for (const name of names) {
    for (const date of Object.keys(models[name].hourly ?? {})) dateSet.add(date)
  }
  const dates = [...dateSet].sort()
  const [selectedDate, setSelectedDate] = useState(dates[0] ?? '')

  if (dates.length === 0) {
    return <p className="text-sm text-slate-400">Bu tip için saatlik kırılım verisi yok.</p>
  }

  const activeDate = dates.includes(selectedDate) ? selectedDate : dates[0]

  const actualByHour = new Map<number, number>()
  for (const row of comparison?.by_team[team]?.[type] ?? []) {
    if (row.date === activeDate && row.hour !== undefined) {
      actualByHour.set(row.hour, row.actual_count)
    }
  }
  const hasActual = actualByHour.size > 0

  const hourSet = new Set<number>()
  for (const name of names) {
    for (const h of models[name].hourly?.[activeDate] ?? []) hourSet.add(h.hour)
  }
  const hours = [...hourSet].sort((a, b) => a - b)

  const data = hours.map((hour) => {
    const row: Record<string, string | number> = { hour: `${hour}:00` }
    for (const name of names) {
      const entry = (models[name].hourly?.[activeDate] ?? []).find((h) => h.hour === hour)
      if (entry) row[name] = entry.count
    }
    if (actualByHour.has(hour)) row.actual = actualByHour.get(hour) as number
    return row
  })

  return (
    <div>
      <div className="mb-3 flex items-center justify-between">
        <div className="text-sm font-medium text-slate-700">{type} — Saatlik Kırılım Karşılaştırması</div>
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
      <ResponsiveContainer width="100%" height={280}>
        <BarChart data={data} margin={{ top: 8, right: 16, bottom: 0, left: -16 }}>
          <CartesianGrid strokeDasharray="3 3" stroke={CHART_STYLE.grid} />
          <XAxis dataKey="hour" tick={{ fill: CHART_STYLE.tick, fontSize: 11 }} />
          <YAxis tick={{ fill: CHART_STYLE.tick, fontSize: 11 }} />
          <Tooltip contentStyle={CHART_STYLE.tooltip} labelStyle={CHART_STYLE.tooltipLabel} />
          <Legend wrapperStyle={{ fontSize: 12 }} />
          {names.map((name, i) => (
            <Bar
              key={name}
              dataKey={name}
              name={MODEL_LABELS[name] ?? name}
              fill={MODEL_COLORS[i % MODEL_COLORS.length]}
              radius={[4, 4, 0, 0]}
              isAnimationActive={false}
            />
          ))}
          {hasActual && (
            <Bar dataKey="actual" name="Gerçekleşen kayıt" fill={ACTUAL_COLOR} radius={[4, 4, 0, 0]} isAnimationActive={false} />
          )}
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}

export default function HourlyBreakdownChart({
  team,
  type,
  info,
  comparison,
}: {
  team: string
  type: string
  info: ForecastByType
  comparison?: ComparisonResult
}) {
  const hourly = info.hourly
  const dates = useMemo(() => (hourly ? Object.keys(hourly).sort() : []), [hourly])
  const [selectedDate, setSelectedDate] = useState(dates[0] ?? '')

  if (info.models && Object.keys(info.models).length > 1) {
    return <OverlayHourlyChart team={team} type={type} models={info.models} comparison={comparison} />
  }

  if (!hourly || dates.length === 0) {
    return <p className="text-sm text-slate-400">Bu tip için saatlik kırılım verisi yok.</p>
  }

  const activeDate = dates.includes(selectedDate) ? selectedDate : dates[0]

  const actualByHour = new Map<number, number>()
  for (const row of comparison?.by_team[team]?.[type] ?? []) {
    if (row.date === activeDate && row.hour !== undefined) {
      actualByHour.set(row.hour, row.actual_count)
    }
  }
  const hasActual = actualByHour.size > 0

  const data = (hourly[activeDate] ?? [])
    .slice()
    .sort((a, b) => a.hour - b.hour)
    .map((h) => ({ hour: `${h.hour}:00`, count: h.count, actual: actualByHour.get(h.hour) }))

  return (
    <div>
      <div className="mb-3 flex items-center justify-between">
        <div className="text-sm font-medium text-slate-700">{type} — Saatlik Kırılım</div>
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
      <ResponsiveContainer width="100%" height={260}>
        <BarChart data={data} margin={{ top: 8, right: 16, bottom: 0, left: -16 }}>
          <CartesianGrid strokeDasharray="3 3" stroke={CHART_STYLE.grid} />
          <XAxis dataKey="hour" tick={{ fill: CHART_STYLE.tick, fontSize: 11 }} />
          <YAxis tick={{ fill: CHART_STYLE.tick, fontSize: 11 }} />
          <Tooltip contentStyle={CHART_STYLE.tooltip} labelStyle={CHART_STYLE.tooltipLabel} />
          {hasActual && <Legend wrapperStyle={{ fontSize: 12 }} />}
          <Bar dataKey="count" name="Tahmin edilen kayıt" fill="#3b82f6" radius={[4, 4, 0, 0]} isAnimationActive={false} />
          {hasActual && (
            <Bar dataKey="actual" name="Gerçekleşen kayıt" fill="#10b981" radius={[4, 4, 0, 0]} isAnimationActive={false} />
          )}
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
