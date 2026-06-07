import { useEffect, useState } from 'react'
import { useData } from '../context/DataContext'

const STEPS = [
  'Model yükleniyor',
  'Özellikler oluşturuluyor',
  'Tahmin hesaplanıyor',
  'Grafikler hazırlanıyor',
]

const STEP_INTERVAL_MS = 500

/**
 * forecast_pipeline kayıtlı modellerle saniyeler içinde tamamlanır; gerçek
 * adım bazlı backend event'i olmadığından adımlar istemci tarafında
 * zamanlanır ve gerçek istek tamamlanınca anında "done" durumuna geçilir.
 */
export default function ProgressStepper() {
  const { uiStep, forecastResult } = useData()
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

  const done = uiStep === 'results' || forecastResult !== null

  return (
    <div className="rounded-xl border border-navy-700 bg-navy-900 p-8">
      <div className="mb-6 text-sm font-medium text-slate-200">
        Tahmin oluşturuluyor — öğrenme ve tahminleme adımları
      </div>
      <ol className="space-y-4">
        {STEPS.map((label, i) => {
          const state = done || i < activeIndex ? 'done' : i === activeIndex ? 'active' : 'pending'
          return (
            <li key={label} className="flex items-center gap-3">
              <span
                className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-full border text-xs ${
                  state === 'done'
                    ? 'border-emerald-400 bg-emerald-400/10 text-emerald-400'
                    : state === 'active'
                      ? 'border-gold-400 bg-gold-400/10 text-gold-400'
                      : 'border-navy-600 text-slate-500'
                }`}
              >
                {state === 'done' ? '✓' : i + 1}
              </span>
              <span
                className={`text-sm ${
                  state === 'pending' ? 'text-slate-500' : 'text-slate-200'
                }`}
              >
                {label}
              </span>
              {state === 'active' && (
                <span className="ml-1 inline-block h-3 w-3 animate-spin rounded-full border-2 border-gold-400 border-t-transparent" />
              )}
            </li>
          )
        })}
      </ol>
    </div>
  )
}
