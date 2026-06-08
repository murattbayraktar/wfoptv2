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
      className={`rounded-xl border p-4 text-left transition-colors ${
        active ? 'border-gold-500 bg-navy-800' : 'border-navy-700 bg-navy-900 hover:border-navy-600'
      }`}
    >
      <div className="text-sm font-semibold text-slate-100">{type}</div>
      <div className="mt-1 text-xs text-slate-400">
        Kullanılan algoritma: <span className="text-gold-400">{info.model_used}</span>
      </div>
      {info.models && Object.keys(info.models).length > 1 && (
        <div className="mt-1 text-xs text-slate-400">
          Karşılaştırılan algoritmalar:{' '}
          <span className="text-slate-300">
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
            <span key={flag} className="rounded-full bg-navy-700 px-2 py-0.5 text-[11px] text-slate-300">
              {FLAG_LABELS[flag] ?? flag}
            </span>
          ))}
        </div>
      )}
    </button>
  )
}
