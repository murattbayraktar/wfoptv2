import type { CalibrationPreviewResponse } from '../types'

function fmtMape(v: number | null): string {
  return v === null ? '—' : `${v.toFixed(1)}%`
}

function fmtDelta(v: number | null): { text: string; cls: string } {
  if (v === null) return { text: '—', cls: 'text-slate-400' }
  if (Math.abs(v) < 0.05) return { text: '±0.0', cls: 'text-slate-400' }
  const cls = v < 0 ? 'text-emerald-600' : 'text-red-500'
  return { text: `${v > 0 ? '+' : ''}${v.toFixed(1)}`, cls }
}

export default function CalibrationPreviewModal({
  preview,
  saving,
  onConfirm,
  onCancel,
}: {
  preview: CalibrationPreviewResponse
  saving: boolean
  onConfirm: () => void
  onCancel: () => void
}) {
  const teams = Array.from(
    new Set([...Object.keys(preview.current.by_team), ...Object.keys(preview.proposed.by_team)]),
  )
  const overallDelta = fmtDelta(preview.delta.overall_mape)

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 p-4">
      <div className="w-full max-w-2xl rounded-2xl border border-slate-200 bg-white p-6 shadow-xl">
        <div className="mb-1 text-base font-semibold text-slate-900">Kalibrasyon Önizlemesi</div>
        <p className="mb-4 text-xs text-slate-500">
          Aşağıda önerilen çarpanların mevcut duruma göre geçmiş veri üzerindeki MAPE'yi nasıl
          değiştireceği gösteriliyor. Kaydetmeden önce gözden geçirin — <span className="text-emerald-600 font-medium">yeşil</span>{' '}
          iyileşmeyi, <span className="text-red-500 font-medium">kırmızı</span> kötüleşmeyi gösterir.
        </p>

        <div className="mb-4 flex items-center justify-between rounded-xl border border-slate-200 bg-slate-50 px-4 py-3">
          <span className="text-sm font-medium text-slate-700">Genel MAPE</span>
          <span className="flex items-center gap-3 text-sm">
            <span className="text-slate-500">{fmtMape(preview.current.overall_mape)}</span>
            <span className="text-slate-300">→</span>
            <span className="font-semibold text-slate-900">{fmtMape(preview.proposed.overall_mape)}</span>
            <span className={`font-semibold ${overallDelta.cls}`}>({overallDelta.text})</span>
          </span>
        </div>

        {teams.length > 0 && (
          <table className="mb-4 w-full text-left text-xs text-slate-700">
            <thead>
              <tr className="text-slate-500">
                <th className="pb-1 pr-4 font-medium">Ekip</th>
                <th className="pb-1 pr-4 font-medium">Mevcut</th>
                <th className="pb-1 pr-4 font-medium">Önerilen</th>
                <th className="pb-1 font-medium">Fark</th>
              </tr>
            </thead>
            <tbody>
              {teams.map((team) => {
                const cur = preview.current.by_team[team]?.mape ?? null
                const prop = preview.proposed.by_team[team]?.mape ?? null
                const d = fmtDelta(preview.delta.by_team[team]?.mape ?? null)
                return (
                  <tr key={team} className="border-t border-slate-100">
                    <td className="py-1.5 pr-4 font-medium text-slate-900">{team}</td>
                    <td className="py-1.5 pr-4 text-slate-500">{fmtMape(cur)}</td>
                    <td className="py-1.5 pr-4 text-slate-900">{fmtMape(prop)}</td>
                    <td className={`py-1.5 font-semibold ${d.cls}`}>{d.text}</td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        )}

        <div className="flex justify-end gap-3">
          <button
            type="button"
            onClick={onCancel}
            disabled={saving}
            className="rounded-md border border-slate-200 px-4 py-2 text-sm text-slate-600 transition-colors hover:border-slate-300 disabled:opacity-50"
          >
            Vazgeç
          </button>
          <button
            type="button"
            onClick={onConfirm}
            disabled={saving}
            className="rounded-md border border-blue-300 bg-blue-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-blue-700 disabled:opacity-50"
          >
            {saving ? 'Kaydediliyor…' : 'Onayla ve Kaydet'}
          </button>
        </div>
      </div>
    </div>
  )
}
