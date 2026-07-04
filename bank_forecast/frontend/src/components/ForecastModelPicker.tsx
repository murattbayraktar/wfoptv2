import { useMemo } from 'react'
import { useData } from '../context/DataContext'
import { MODEL_LABELS } from '../constants'

export default function ForecastModelPicker() {
  const { talimat, islem, forecastModels, toggleForecastModel } = useData()

  const modelNames = useMemo(() => {
    const names = new Set<string>()
    for (const availableModels of [talimat.availableModels, islem.availableModels]) {
      if (!availableModels) continue
      for (const byType of Object.values(availableModels.available)) {
        for (const byFreq of Object.values(byType)) {
          for (const entry of Object.values(byFreq)) {
            for (const name of entry.models) names.add(name)
          }
        }
      }
    }
    return [...names].sort()
  }, [talimat.availableModels, islem.availableModels])

  if (modelNames.length < 2) return null

  return (
    <div className="mt-8">
      <div className="mb-3 text-xs font-semibold uppercase tracking-wider text-slate-500">
        Tahmin Algoritması
      </div>
      <div className="flex flex-col gap-1.5 rounded-md border border-slate-200 bg-slate-50 px-3 py-2.5">
        {modelNames.map((name) => (
          <label key={name} className="flex cursor-pointer items-center gap-2 text-sm text-slate-700">
            <input
              type="checkbox"
              checked={forecastModels.includes(name)}
              onChange={() => toggleForecastModel(name)}
              className="h-4 w-4 rounded border-slate-300 bg-white accent-blue-600"
            />
            {MODEL_LABELS[name] ?? name}
          </label>
        ))}
      </div>
      <p className="mt-1.5 text-xs text-slate-400">
        Boş bırakırsanız her ekip/tip için otomatik en iyi model kullanılır. Birden fazla algoritma
        seçerseniz sonuçlar grafik üzerinde renkli çizgiler olarak üst üste karşılaştırmalı gösterilir.
      </p>
    </div>
  )
}
