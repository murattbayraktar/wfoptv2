import { useState } from 'react'
import type { CalibrationScope, ComparisonResult, ForecastByType, MetricType } from '../types'

export default function TypeBreakdownTable({
  metricType,
  team,
  types,
  byType,
  rangeStart,
  rangeEnd,
  comparison,
  onGoToCalibration,
}: {
  metricType: MetricType
  team: string
  types: string[]
  byType: Record<string, ForecastByType>
  rangeStart: string
  rangeEnd: string
  comparison: ComparisonResult
  onGoToCalibration: (scope: CalibrationScope) => void
}) {
  const dateSet = new Set<string>()
  for (const type of types) {
    for (const d of byType[type]?.daily ?? []) dateSet.add(d.date)
  }
  const dates = [...dateSet].sort()

  const [openDates, setOpenDates] = useState<Set<string>>(() => new Set(dates.slice(0, 1)))

  const toggleDate = (date: string) => {
    setOpenDates((prev) => {
      const next = new Set(prev)
      if (next.has(date)) next.delete(date)
      else next.add(date)
      return next
    })
  }

  if (dates.length === 0) {
    return <p className="text-sm text-slate-400">Tablo için günlük tahmin verisi yok.</p>
  }

  const valueAt = (type: string, date: string) =>
    (byType[type]?.daily ?? []).find((d) => d.date === date)?.predicted_count

  const actualAt = (type: string, date: string) =>
    comparison.by_team[team]?.[type]?.find((r) => r.date === date)?.actual_count

  const hasActual = (date: string) =>
    comparison.has_overlap && types.some((type) => actualAt(type, date) !== undefined)

  const fmt = (v: number | undefined) => (v !== undefined ? v.toLocaleString('tr-TR', { maximumFractionDigits: 0 }) : '—')

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="mb-4 text-sm font-medium text-slate-800">{team} — Tarih / İşlem Tipi Kırılımı</div>
      <div className="space-y-2">
        {dates.map((date) => {
          const rowTotal = types.reduce((sum, type) => sum + (valueAt(type, date) ?? 0), 0)
          const dateHasActual = hasActual(date)
          const actualRowTotal = dateHasActual
            ? types.reduce((sum, type) => sum + (actualAt(type, date) ?? 0), 0)
            : undefined
          const isOpen = openDates.has(date)
          return (
            <div key={date} className="overflow-hidden rounded-lg border border-slate-200">
              <button
                type="button"
                onClick={() => toggleDate(date)}
                className="flex w-full items-center justify-between bg-slate-50 px-4 py-2.5 text-left transition-colors hover:bg-slate-100"
              >
                <span className="flex items-center gap-2">
                  <svg
                    width="14"
                    height="14"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    className={`text-slate-400 transition-transform ${isOpen ? 'rotate-90' : ''}`}
                  >
                    <path d="M9 6l6 6-6 6" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                  <span className="text-sm font-medium text-slate-900">{date}</span>
                </span>
                <span className="text-sm text-slate-700">
                  <span className="font-semibold">{rowTotal.toLocaleString('tr-TR', { maximumFractionDigits: 0 })}</span>
                  {actualRowTotal !== undefined && (
                    <span className="ml-2 font-normal text-slate-500">
                      (gerçekleşen: <span className="font-semibold text-slate-700">{actualRowTotal.toLocaleString('tr-TR', { maximumFractionDigits: 0 })}</span>)
                    </span>
                  )}
                </span>
              </button>

              {isOpen && (
                <div className="border-t border-slate-100 px-4 py-2">
                  <table className="w-full text-left text-xs text-slate-700">
                    <thead>
                      <tr className="text-slate-500">
                        <th className="pb-1.5 pr-4 font-medium">İşlem Tipi</th>
                        <th className="pb-1.5 pr-4 font-medium">Tahmin</th>
                        {dateHasActual && <th className="pb-1.5 pr-4 font-medium">Gerçekleşen</th>}
                        <th className="pb-1.5 font-medium" />
                      </tr>
                    </thead>
                    <tbody>
                      {types.map((type) => {
                        const v = valueAt(type, date)
                        const actual = dateHasActual ? actualAt(type, date) : undefined
                        return (
                          <tr key={type} className="border-t border-slate-100">
                            <td className="py-1.5 pr-4 font-medium text-slate-900">{type}</td>
                            <td className="py-1.5 pr-4 text-slate-600">{fmt(v)}</td>
                            {dateHasActual && (
                              <td className="py-1.5 pr-4 font-medium text-slate-900">{fmt(actual)}</td>
                            )}
                            <td className="py-1.5 text-right">
                              <button
                                type="button"
                                onClick={() =>
                                  onGoToCalibration({ metricType, team, type, start: rangeStart, end: rangeEnd })
                                }
                                className="rounded-full border border-blue-200 bg-blue-50 px-2 py-0.5 text-[10px] font-medium text-blue-600 transition-colors hover:bg-blue-100"
                              >
                                Kalibrasyon
                              </button>
                            </td>
                          </tr>
                        )
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
