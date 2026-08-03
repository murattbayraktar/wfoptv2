import type { MapeSummary } from '../types'
import { MapeBadge } from './MapeBadge'

export default function MapeOverviewCard({ label, mapeSummary }: { label: string; mapeSummary: MapeSummary }) {
  const teams = Object.entries(mapeSummary.by_team)
  if (teams.length === 0) return null

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="mb-3 flex items-center justify-between">
        <div className="text-sm font-medium text-slate-800">{label} — Tahmin Doğruluğu (MAPE)</div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-500">Genel:</span>
          <MapeBadge mape={mapeSummary.overall_mape} />
        </div>
      </div>
      <table className="w-full text-left text-xs text-slate-700">
        <thead>
          <tr className="text-slate-500">
            <th className="pb-1 pr-4 font-medium">Ekip</th>
            <th className="pb-1 pr-4 font-medium">Ekip MAPE</th>
            <th className="pb-1 font-medium">İşlem Tipi Bazında</th>
          </tr>
        </thead>
        <tbody>
          {teams.map(([team, info]) => (
            <tr key={team} className="border-t border-slate-100">
              <td className="py-1.5 pr-4 font-medium text-slate-900">{team}</td>
              <td className="py-1.5 pr-4">
                <MapeBadge mape={info.mape} />
              </td>
              <td className="py-1.5">
                <div className="flex flex-wrap gap-x-3 gap-y-1">
                  {Object.entries(info.by_type).map(([tt, mape]) => (
                    <span key={tt} className="inline-flex items-center gap-1 text-slate-500">
                      {tt}: <MapeBadge mape={mape} />
                    </span>
                  ))}
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      <p className="mt-3 text-xs text-slate-400">
        MAPE = Ortalama Mutlak Yüzde Hata (seçilen aralığın geçmiş veriyle örtüşen kısmı üzerinden). &lt;10%: iyi,
        10–20%: kabul edilebilir, &gt;20%: zayıf.
      </p>
    </div>
  )
}
