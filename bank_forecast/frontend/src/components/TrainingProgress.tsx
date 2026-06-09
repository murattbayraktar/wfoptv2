import { useEffect, useRef } from 'react'
import type { HoldoutResult, RetrainStatus, TrainingStep } from '../types'
import { MODEL_LABELS } from '../constants'

const KIND_ICON: Record<string, string> = {
  data_ready: '📥',
  holdout_set: '✂️',
  plan: '🗂️',
  unit_start: '▶️',
  selection_start: '🔍',
  model_evaluated: '🧪',
  model_selected: '✅',
  unit_done: '🏁',
  unit_failed: '⚠️',
  completed: '🎉',
  holdout_forecast: '🔮',
  holdout_done: '📊',
  holdout_failed: '⚠️',
  error: '❌',
}

function StepRow({ step }: { step: TrainingStep }) {
  const icon = KIND_ICON[step.kind] ?? '•'
  const time = new Date(step.at).toLocaleTimeString('tr-TR')
  const emphasized =
    step.kind === 'model_selected' ||
    step.kind === 'unit_done' ||
    step.kind === 'completed' ||
    step.kind === 'holdout_done'
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

function mapeQuality(mape: number): { label: string; cls: string } {
  if (mape < 10) return { label: 'İyi', cls: 'text-emerald-400' }
  if (mape < 20) return { label: 'Kabul', cls: 'text-yellow-400' }
  return { label: 'Zayıf', cls: 'text-red-400' }
}

function HoldoutPanel({ result }: { result: HoldoutResult }) {
  const types = Object.entries(result.by_type)

  return (
    <div className="mt-4 rounded-lg border border-blue-500/30 bg-blue-500/5 p-4">
      <div className="mb-3 flex items-center justify-between">
        <div className="text-sm font-medium text-blue-300">
          Doğrulama Sonuçları — MAPE
        </div>
        <span className="text-xs text-slate-500">
          {result.holdout_range.start} – {result.holdout_range.end}
        </span>
      </div>

      {result.overall_mape !== null && result.overall_mape !== undefined && (
        <div className="mb-3 flex items-center gap-2">
          <span className="text-xs text-slate-400">Genel MAPE:</span>
          <span className={`text-sm font-semibold ${mapeQuality(result.overall_mape).cls}`}>
            {result.overall_mape.toFixed(1)}%
          </span>
          <span className={`text-xs ${mapeQuality(result.overall_mape).cls}`}>
            ({mapeQuality(result.overall_mape).label})
          </span>
        </div>
      )}

      {types.length > 0 && (
        <table className="w-full text-left text-xs text-slate-300">
          <thead>
            <tr className="text-slate-500">
              <th className="pb-1 pr-4 font-medium">İşlem Tipi</th>
              <th className="pb-1 pr-4 font-medium">MAPE</th>
              <th className="pb-1 pr-4 font-medium">Yorum</th>
              <th className="pb-1 font-medium">Gün sayısı</th>
            </tr>
          </thead>
          <tbody>
            {types.map(([tt, info]) => {
              const q = info.mape !== null ? mapeQuality(info.mape) : null
              return (
                <tr key={tt} className="border-t border-navy-800">
                  <td className="py-1 pr-4">{tt}</td>
                  <td className={`py-1 pr-4 font-medium ${q?.cls ?? 'text-slate-500'}`}>
                    {info.mape !== null ? `${info.mape.toFixed(1)}%` : '—'}
                  </td>
                  <td className={`py-1 pr-4 ${q?.cls ?? 'text-slate-500'}`}>
                    {q?.label ?? '—'}
                  </td>
                  <td className="py-1 text-slate-400">{info.rows.length}</td>
                </tr>
              )
            })}
          </tbody>
        </table>
      )}

      {/* Detay satırları: ilk eşleşen tip için gerçekleşen vs tahmin */}
      {types.map(([tt, info]) =>
        info.rows.length > 0 ? (
          <details key={tt} className="mt-3">
            <summary className="cursor-pointer text-xs text-slate-500 hover:text-slate-400">
              {tt} — gün bazlı gerçekleşen vs tahmin
            </summary>
            <div className="mt-2 max-h-48 overflow-y-auto rounded border border-navy-800">
              <table className="w-full text-left text-xs">
                <thead className="sticky top-0 bg-navy-900">
                  <tr className="text-slate-500">
                    <th className="px-3 py-1 font-medium">Tarih</th>
                    <th className="px-3 py-1 font-medium">Gerçekleşen</th>
                    <th className="px-3 py-1 font-medium">Tahmin</th>
                    <th className="px-3 py-1 font-medium">Fark %</th>
                  </tr>
                </thead>
                <tbody>
                  {info.rows.map((row) => {
                    const diff =
                      row.actual !== 0
                        ? Math.abs((row.actual - row.predicted) / row.actual) * 100
                        : null
                    return (
                      <tr key={row.date} className="border-t border-navy-800 text-slate-300">
                        <td className="px-3 py-1">{row.date}</td>
                        <td className="px-3 py-1">{row.actual.toLocaleString('tr-TR')}</td>
                        <td className="px-3 py-1">{row.predicted.toLocaleString('tr-TR')}</td>
                        <td className={`px-3 py-1 ${diff !== null && diff > 20 ? 'text-red-400' : 'text-slate-400'}`}>
                          {diff !== null ? `${diff.toFixed(1)}%` : '—'}
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          </details>
        ) : null,
      )}

      {/* Model karşılaştırma bölümü: birden fazla model eğitildiyse */}
      {result.model_overall_mapes && Object.keys(result.model_overall_mapes).length > 1 && (
        <div className="mt-4 border-t border-navy-800 pt-4">
          <div className="mb-2 text-xs font-medium text-slate-400">Model Karşılaştırması — Genel MAPE</div>
          <div className="flex flex-wrap gap-2">
            {Object.entries(result.model_overall_mapes)
              .sort(([, a], [, b]) => (a ?? 999) - (b ?? 999))
              .map(([model, mape]) => {
                const q = mape !== null ? mapeQuality(mape) : null
                return (
                  <div
                    key={model}
                    className="flex items-center gap-1.5 rounded-md border border-navy-700 bg-navy-950 px-2.5 py-1.5 text-xs"
                  >
                    <span className="text-slate-400">{MODEL_LABELS[model] ?? model}:</span>
                    <span className={`font-semibold ${q?.cls ?? 'text-slate-500'}`}>
                      {mape !== null ? `${mape.toFixed(1)}%` : '—'}
                    </span>
                    {q && (
                      <span className={`${q.cls} opacity-75`}>({q.label})</span>
                    )}
                  </div>
                )
              })}
          </div>

          {/* İşlem tipi bazında model karşılaştırması */}
          {(() => {
            const typesWithModelMapes = Object.entries(result.by_type).filter(
              ([, info]) => info.model_mapes && Object.keys(info.model_mapes).length > 1,
            )
            if (typesWithModelMapes.length === 0) return null
            const modelNames = Object.keys(result.model_overall_mapes).sort(
              (a, b) => (result.model_overall_mapes![a] ?? 999) - (result.model_overall_mapes![b] ?? 999),
            )
            return (
              <details className="mt-3">
                <summary className="cursor-pointer text-xs text-slate-500 hover:text-slate-400">
                  İşlem tipi bazında model karşılaştırması
                </summary>
                <div className="mt-2 overflow-x-auto rounded border border-navy-800">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-navy-900">
                      <tr className="text-slate-500">
                        <th className="px-3 py-1.5 font-medium">İşlem Tipi</th>
                        {modelNames.map((m) => (
                          <th key={m} className="px-3 py-1.5 font-medium">
                            {MODEL_LABELS[m] ?? m}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {typesWithModelMapes.map(([tt, info]) => (
                        <tr key={tt} className="border-t border-navy-800 text-slate-300">
                          <td className="px-3 py-1.5">{tt}</td>
                          {modelNames.map((m) => {
                            const v = info.model_mapes?.[m] ?? null
                            const q = v !== null ? mapeQuality(v) : null
                            return (
                              <td key={m} className={`px-3 py-1.5 font-medium ${q?.cls ?? 'text-slate-500'}`}>
                                {v !== null ? `${v.toFixed(1)}%` : '—'}
                              </td>
                            )
                          })}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </details>
            )
          })()}
        </div>
      )}

      <p className="mt-3 text-xs text-slate-500">
        MAPE = Ortalama Mutlak Yüzde Hata. &lt;10%: iyi, 10–20%: kabul edilebilir, &gt;20%: zayıf.
      </p>
    </div>
  )
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

          {status.holdout_result && <HoldoutPanel result={status.holdout_result} />}

          {!status.holdout_result && (
            <p className="mt-3 text-xs text-slate-500">
              Modeller kaydedildi — "Tahmin" sekmesine geçip güncel modellerle tahmin oluşturabilirsiniz.
            </p>
          )}
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
