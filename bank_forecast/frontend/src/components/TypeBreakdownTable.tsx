import type { CalibrationScope, ForecastByType, MetricType } from '../types'

export default function TypeBreakdownTable({
  metricType,
  team,
  types,
  byType,
  rangeStart,
  rangeEnd,
  onGoToCalibration,
}: {
  metricType: MetricType
  team: string
  types: string[]
  byType: Record<string, ForecastByType>
  rangeStart: string
  rangeEnd: string
  onGoToCalibration: (scope: CalibrationScope) => void
}) {
  const dateSet = new Set<string>()
  for (const type of types) {
    for (const d of byType[type]?.daily ?? []) dateSet.add(d.date)
  }
  const dates = [...dateSet].sort()

  if (dates.length === 0) {
    return <p className="text-sm text-slate-400">Tablo için günlük tahmin verisi yok.</p>
  }

  const valueAt = (type: string, date: string) =>
    (byType[type]?.daily ?? []).find((d) => d.date === date)?.predicted_count

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="mb-4 text-sm font-medium text-slate-800">{team} — Tarih / İşlem Tipi Kırılımı</div>
      <div className="overflow-x-auto">
        <table className="w-full min-w-max text-left text-xs text-slate-700">
          <thead>
            <tr className="text-slate-500">
              <th className="sticky left-0 bg-white pb-2 pr-4 font-medium">Tarih</th>
              {types.map((type) => (
                <th key={type} className="pb-2 pr-4 font-medium">
                  <div className="flex items-center gap-2">
                    <span>{type}</span>
                    <button
                      type="button"
                      onClick={() =>
                        onGoToCalibration({ metricType, team, type, start: rangeStart, end: rangeEnd })
                      }
                      className="rounded-full border border-blue-200 bg-blue-50 px-2 py-0.5 text-[10px] font-medium text-blue-600 transition-colors hover:bg-blue-100"
                    >
                      Kalibrasyon
                    </button>
                  </div>
                </th>
              ))}
              <th className="pb-2 font-medium">Toplam</th>
            </tr>
          </thead>
          <tbody>
            {dates.map((date) => {
              const rowTotal = types.reduce((sum, type) => sum + (valueAt(type, date) ?? 0), 0)
              return (
                <tr key={date} className="border-t border-slate-100">
                  <td className="sticky left-0 bg-white py-1.5 pr-4 font-medium text-slate-900">{date}</td>
                  {types.map((type) => {
                    const v = valueAt(type, date)
                    return (
                      <td key={type} className="py-1.5 pr-4 text-slate-600">
                        {v !== undefined ? v.toLocaleString('tr-TR', { maximumFractionDigits: 0 }) : '—'}
                      </td>
                    )
                  })}
                  <td className="py-1.5 font-semibold text-slate-900">
                    {rowTotal.toLocaleString('tr-TR', { maximumFractionDigits: 0 })}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}
