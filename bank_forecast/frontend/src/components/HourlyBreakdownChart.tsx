import { useMemo, useState } from 'react'
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import type { ForecastByType } from '../types'

export default function HourlyBreakdownChart({ type, info }: { type: string; info: ForecastByType }) {
  const hourly = info.hourly
  const dates = useMemo(() => (hourly ? Object.keys(hourly).sort() : []), [hourly])
  const [selectedDate, setSelectedDate] = useState(dates[0] ?? '')

  if (!hourly || dates.length === 0) {
    return <p className="text-sm text-slate-500">Bu tip için saatlik kırılım verisi yok.</p>
  }

  const activeDate = dates.includes(selectedDate) ? selectedDate : dates[0]
  const data = (hourly[activeDate] ?? [])
    .slice()
    .sort((a, b) => a.hour - b.hour)
    .map((h) => ({ hour: `${h.hour}:00`, count: h.count }))

  return (
    <div>
      <div className="mb-3 flex items-center justify-between">
        <div className="text-sm font-medium text-slate-200">{type} — Saatlik Kırılım</div>
        <select
          value={activeDate}
          onChange={(e) => setSelectedDate(e.target.value)}
          className="rounded-md border border-navy-600 bg-navy-800 px-2 py-1 text-xs text-slate-200 outline-none focus:border-gold-500"
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
          <CartesianGrid strokeDasharray="3 3" stroke="#1b2740" />
          <XAxis dataKey="hour" tick={{ fill: '#94a3b8', fontSize: 11 }} />
          <YAxis tick={{ fill: '#94a3b8', fontSize: 11 }} />
          <Tooltip
            contentStyle={{ background: '#0c1322', border: '1px solid #2a3a5c', borderRadius: 8, fontSize: 12 }}
            labelStyle={{ color: '#e2e8f0' }}
          />
          <Bar dataKey="count" name="Tahmin edilen kayıt" fill="#60a5fa" radius={[4, 4, 0, 0]} isAnimationActive={false} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
