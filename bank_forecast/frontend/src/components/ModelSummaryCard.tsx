import type { ForecastByType } from '../types'
import { MODEL_LABELS } from '../constants'

const FLAG_LABELS: Record<string, string> = {
  is_public_holiday: 'Resmi tatil',
  is_religious_holiday: 'Dini bayram',
  is_eve_of_holiday: 'Tatil arifesi',
  is_month_start: 'Ay başı',
  is_month_end: 'Ay sonu',
}

export default function ModelSummaryCard({
  type,
  info,
  active,
  onSelect,
}: {
  type: string
  info: ForecastByType
  active: boolean
  onSelect: () => void
}) {
  const flagSet = new Set<string>()
  for (const entry of info.daily ?? []) {
    for (const flag of entry.calendar_flags) flagSet.add(flag)
  }

  return (
    <button
      type="button"
      onClick={onSelect}
      className={`rounded-xl border p-4 text-left transition-all ${
        active
          ? 'border-blue-400 bg-blue-50 shadow-sm ring-1 ring-blue-200'
          : 'border-slate-200 bg-white shadow-sm hover:border-slate-300 hover:shadow'
      }`}
    >
      <div className="text-sm font-semibold text-slate-900">{type}</div>
      <div className="mt-1 text-xs text-slate-500">
        Kullanılan algoritma: <span className="font-medium text-amber-600">{MODEL_LABELS[info.model_used] ?? info.model_used}</span>
      </div>
      {info.models && Object.keys(info.models).length > 1 && (
        <div className="mt-1 text-xs text-slate-500">
          Karşılaştırılan algoritmalar:{' '}
          <span className="text-slate-700">
            {Object.keys(info.models)
              .sort()
              .map((m) => MODEL_LABELS[m] ?? m)
              .join(', ')}
          </span>
        </div>
      )}
      {flagSet.size > 0 && (
        <div className="mt-3 flex flex-wrap gap-1.5">
          {[...flagSet].map((flag) => (
            <span key={flag} className="rounded-full bg-slate-100 px-2 py-0.5 text-[11px] text-slate-600">
              {FLAG_LABELS[flag] ?? flag}
            </span>
          ))}
        </div>
      )}
    </button>
  )
}
