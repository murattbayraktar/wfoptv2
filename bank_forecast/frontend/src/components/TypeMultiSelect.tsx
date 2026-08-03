import { useMemo, useState } from 'react'
import type { ForecastByType } from '../types'
import { MODEL_LABELS } from '../constants'

export default function TypeMultiSelect({
  types,
  byType,
  selected,
  onToggle,
  onSelectAll,
  onClear,
}: {
  types: string[]
  byType: Record<string, ForecastByType>
  selected: string[]
  onToggle: (type: string) => void
  onSelectAll: () => void
  onClear: () => void
}) {
  const [query, setQuery] = useState('')

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase()
    if (!q) return types
    return types.filter((t) => t.toLowerCase().includes(q))
  }, [types, query])

  return (
    <div>
      <div className="mb-2 flex flex-wrap items-center gap-2">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="İşlem tipi ara..."
          className="w-48 rounded-md border border-slate-300 bg-white px-3 py-1.5 text-xs text-slate-900 outline-none focus:border-blue-400"
        />
        <button
          type="button"
          onClick={onSelectAll}
          className="rounded-md border border-slate-200 px-2.5 py-1 text-xs text-slate-600 transition-colors hover:border-blue-300 hover:text-blue-600"
        >
          Tümünü seç
        </button>
        <button
          type="button"
          onClick={onClear}
          className="rounded-md border border-slate-200 px-2.5 py-1 text-xs text-slate-600 transition-colors hover:border-blue-300 hover:text-blue-600"
        >
          Seçimi temizle
        </button>
        <span className="text-xs text-slate-400">
          {selected.length} / {types.length} seçili
        </span>
      </div>
      <div className="flex max-h-56 flex-wrap content-start gap-2 overflow-y-auto rounded-lg border border-slate-200 bg-white p-3">
        {filtered.length === 0 ? (
          <span className="text-xs text-slate-400">Eşleşen işlem tipi yok.</span>
        ) : (
          filtered.map((type) => {
            const isActive = selected.includes(type)
            const modelUsed = byType[type]?.model_used
            return (
              <button
                key={type}
                type="button"
                onClick={() => onToggle(type)}
                title={modelUsed ? `Kullanılan algoritma: ${MODEL_LABELS[modelUsed] ?? modelUsed}` : undefined}
                className={`rounded-full border px-3 py-1 text-xs font-medium transition-colors ${
                  isActive
                    ? 'border-blue-400 bg-blue-50 text-blue-700'
                    : 'border-slate-200 bg-slate-50 text-slate-600 hover:border-slate-300'
                }`}
              >
                {type}
              </button>
            )
          })
        )}
      </div>
    </div>
  )
}
