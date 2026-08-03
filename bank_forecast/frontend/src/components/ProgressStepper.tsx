import { useEffect, useState } from 'react'
import { useData } from '../context/DataContext'

const STEPS = [
  'Model yükleniyor',
  'Özellikler oluşturuluyor',
  'Tahmin hesaplanıyor',
  'Grafikler hazırlanıyor',
]

const STEP_INTERVAL_MS = 500

export default function ProgressStepper() {
  const { uiStep } = useData()
  const [activeIndex, setActiveIndex] = useState(0)

  useEffect(() => {
    if (uiStep !== 'progress') {
      setActiveIndex(0)
      return
    }
    const timer = setInterval(() => {
      setActiveIndex((i) => Math.min(i + 1, STEPS.length - 1))
    }, STEP_INTERVAL_MS)
    return () => clearInterval(timer)
  }, [uiStep])

  const done = uiStep === 'results'

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-8 shadow-sm">
      <div className="mb-6 text-sm font-medium text-slate-700">
        Tahmin oluşturuluyor — öğrenme ve tahminleme adımları
      </div>
      <ol className="space-y-4">
        {STEPS.map((label, i) => {
          const state = done || i < activeIndex ? 'done' : i === activeIndex ? 'active' : 'pending'
          return (
            <li key={label} className="flex items-center gap-3">
              <span
                className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-full border text-xs font-medium ${
                  state === 'done'
                    ? 'border-emerald-300 bg-emerald-50 text-emerald-600'
                    : state === 'active'
                      ? 'border-blue-300 bg-blue-50 text-blue-600'
                      : 'border-slate-300 text-slate-400'
                }`}
              >
                {state === 'done' ? '✓' : i + 1}
              </span>
              <span
                className={`text-sm ${
                  state === 'pending' ? 'text-slate-400' : 'text-slate-800'
                }`}
              >
                {label}
              </span>
              {state === 'active' && (
                <span className="ml-1 inline-block h-3 w-3 animate-spin rounded-full border-2 border-blue-500 border-t-transparent" />
              )}
            </li>
          )
        })}
      </ol>
    </div>
  )
}
