import { useEffect, useRef } from 'react'
import type { RetrainStatus, TrainingStep } from '../types'

const KIND_ICON: Record<string, string> = {
  data_ready: '📥',
  plan: '🗂️',
  unit_start: '▶️',
  selection_start: '🔍',
  model_evaluated: '🧪',
  model_selected: '✅',
  unit_done: '🏁',
  unit_failed: '⚠️',
  completed: '🎉',
  error: '❌',
}

function StepRow({ step }: { step: TrainingStep }) {
  const icon = KIND_ICON[step.kind] ?? '•'
  const time = new Date(step.at).toLocaleTimeString('tr-TR')
  const emphasized = step.kind === 'model_selected' || step.kind === 'unit_done' || step.kind === 'completed'
  return (
    <li className="flex items-start gap-3 py-1.5">
      <span className="mt-0.5 text-sm leading-none">{icon}</span>
      <span className={`flex-1 text-sm ${emphasized ? 'text-slate-100' : 'text-slate-400'}`}>{step.message}</span>
      <span className="shrink-0 text-[11px] text-slate-600">{time}</span>
    </li>
  )
}

function unitSummaries(steps: TrainingStep[]) {
  return steps.filter((s) => s.kind === 'unit_done')
}

export default function TrainingProgress({ status }: { status: RetrainStatus | null }) {
  const logRef = useRef<HTMLOListElement>(null)

  useEffect(() => {
    logRef.current?.scrollTo({ top: logRef.current.scrollHeight, behavior: 'smooth' })
  }, [status?.steps.length])

  if (!status) return null

  const pct = Math.round(status.progress * 100)
  const summaries = unitSummaries(status.steps)

  return (
    <div className="rounded-xl border border-navy-700 bg-navy-900 p-6">
      <div className="mb-1 flex items-center justify-between">
        <div className="text-sm font-medium text-slate-200">Model eğitimi — adım adım ilerleme</div>
        {status.total_units > 0 && (
          <span className="text-xs text-slate-400">
            {status.completed_units}/{status.total_units} model eğitildi
          </span>
        )}
      </div>

      <div className="mb-4 h-2 overflow-hidden rounded-full bg-navy-700">
        <div
          className={`h-full rounded-full transition-all duration-500 ease-out ${
            status.status === 'error' ? 'bg-red-500' : status.status === 'done' ? 'bg-emerald-400' : 'bg-gold-500'
          }`}
          style={{ width: `${Math.max(pct, status.status === 'running' ? 4 : 0)}%` }}
        />
      </div>

      <p className="mb-4 text-xs text-slate-400">{status.message || 'Eğitim başlatılıyor…'}</p>

      {status.steps.length > 0 && (
        <ol ref={logRef} className="mb-4 max-h-64 divide-y divide-navy-800 overflow-y-auto rounded-lg border border-navy-800 bg-navy-950/60 px-4">
          {status.steps.map((step, i) => (
            <StepRow key={`${step.at}-${i}`} step={step} />
          ))}
        </ol>
      )}

      {status.status === 'done' && (
        <div className="rounded-lg border border-emerald-500/30 bg-emerald-500/5 p-4">
          <div className="mb-2 text-sm font-medium text-emerald-400">Eğitim tamamlandı</div>
          {summaries.length > 0 && (
            <table className="w-full text-left text-xs text-slate-300">
              <thead>
                <tr className="text-slate-500">
                  <th className="pb-1 pr-4 font-medium">İşlem Tipi</th>
                  <th className="pb-1 pr-4 font-medium">Frekans</th>
                  <th className="pb-1 pr-4 font-medium">Seçilen Algoritma</th>
                  <th className="pb-1 font-medium">CV RMSE</th>
                </tr>
              </thead>
              <tbody>
                {summaries.map((s, i) => (
                  <tr key={i} className="border-t border-navy-800">
                    <td className="py-1 pr-4">{s.type}</td>
                    <td className="py-1 pr-4">{s.freq === 'daily' ? 'Günlük' : 'Saatlik'}</td>
                    <td className="py-1 pr-4 text-gold-400">{s.model}</td>
                    <td className="py-1">{s.cv_rmse?.toFixed(2)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
          <p className="mt-3 text-xs text-slate-500">
            Modeller kaydedildi — "Tahmin" sekmesine geçip güncel modellerle tahmin oluşturabilirsiniz.
          </p>
        </div>
      )}

      {status.status === 'error' && (
        <div className="rounded-lg border border-red-500/30 bg-red-500/5 p-4 text-sm text-red-400">
          {status.message}
        </div>
      )}
    </div>
  )
}
