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
      <span className={`flex-1 text-sm ${emphasized ? 'text-slate-900' : 'text-slate-500'}`}>{step.message}</span>
      <span className="shrink-0 text-[11px] text-slate-400">{time}</span>
    </li>
  )
}

function unitSummaries(steps: TrainingStep[]) {
  return steps.filter((s) => s.kind === 'unit_done')
}

function mapeQuality(mape: number): { label: string; cls: string } {
  if (mape < 10) return { label: 'İyi', cls: 'text-emerald-600' }
  if (mape < 20) return { label: 'Kabul', cls: 'text-amber-600' }
  return { label: 'Zayıf', cls: 'text-red-500' }
}

function HoldoutPanel({ result }: { result: HoldoutResult }) {
  const teams = Object.entries(result.by_team)
  // Düz (ekip, tip) satırları — tablo ve detay bölümleri için
  const flatRows = teams.flatMap(([team, teamInfo]) =>
    Object.entries(teamInfo.by_type).map(([tt, info]) => ({ team, tt, info })),
  )

  return (
    <div className="mt-4 rounded-lg border border-blue-200 bg-blue-50 p-4">
      <div className="mb-3 flex items-center justify-between">
        <div className="text-sm font-medium text-blue-700">
          Doğrulama Sonuçları — Ekip Bazlı ve Toplam MAPE
        </div>
        <span className="text-xs text-slate-500">
          {result.holdout_range.start} – {result.holdout_range.end}
        </span>
      </div>

      {result.overall_mape !== null && result.overall_mape !== undefined && (
        <div className="mb-3 flex items-center gap-2">
          <span className="text-xs text-slate-500">Genel MAPE:</span>
          <span className={`text-sm font-semibold ${mapeQuality(result.overall_mape).cls}`}>
            {result.overall_mape.toFixed(1)}%
          </span>
          <span className={`text-xs ${mapeQuality(result.overall_mape).cls}`}>
            ({mapeQuality(result.overall_mape).label})
          </span>
        </div>
      )}

      {teams.length > 0 && (
        <table className="mb-3 w-full text-left text-xs text-slate-700">
          <thead>
            <tr className="text-slate-500">
              <th className="pb-1 pr-4 font-medium">Ekip</th>
              <th className="pb-1 pr-4 font-medium">Ekip MAPE</th>
              <th className="pb-1 font-medium">Yorum</th>
            </tr>
          </thead>
          <tbody>
            {teams.map(([team, info]) => {
              const q = info.mape !== null ? mapeQuality(info.mape) : null
              return (
                <tr key={team} className="border-t border-blue-100">
                  <td className="py-1 pr-4 font-medium">{team}</td>
                  <td className={`py-1 pr-4 font-medium ${q?.cls ?? 'text-slate-400'}`}>
                    {info.mape !== null ? `${info.mape.toFixed(1)}%` : '—'}
                  </td>
                  <td className={`py-1 ${q?.cls ?? 'text-slate-400'}`}>{q?.label ?? '—'}</td>
                </tr>
              )
            })}
          </tbody>
        </table>
      )}

      {flatRows.length > 0 && (
        <table className="w-full text-left text-xs text-slate-700">
          <thead>
            <tr className="text-slate-500">
              <th className="pb-1 pr-4 font-medium">Ekip</th>
              <th className="pb-1 pr-4 font-medium">İşlem Tipi</th>
              <th className="pb-1 pr-4 font-medium">MAPE</th>
              <th className="pb-1 font-medium">Gün sayısı</th>
            </tr>
          </thead>
          <tbody>
            {flatRows.map(({ team, tt, info }) => {
              const q = info.mape !== null ? mapeQuality(info.mape) : null
              return (
                <tr key={`${team}::${tt}`} className="border-t border-blue-100">
                  <td className="py-1 pr-4 text-slate-500">{team}</td>
                  <td className="py-1 pr-4">{tt}</td>
                  <td className={`py-1 pr-4 font-medium ${q?.cls ?? 'text-slate-400'}`}>
                    {info.mape !== null ? `${info.mape.toFixed(1)}%` : '—'}
                  </td>
                  <td className="py-1 text-slate-500">{info.rows.length}</td>
                </tr>
              )
            })}
          </tbody>
        </table>
      )}

      {flatRows.map(({ team, tt, info }) =>
        info.rows.length > 0 ? (
          <details key={`${team}::${tt}`} className="mt-3">
            <summary className="cursor-pointer text-xs text-slate-500 hover:text-slate-700">
              {team} / {tt} — gün bazlı gerçekleşen vs tahmin
            </summary>
            <div className="mt-2 max-h-48 overflow-y-auto rounded border border-slate-200">
              <table className="w-full text-left text-xs">
                <thead className="sticky top-0 bg-white">
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
                      <tr key={row.date} className="border-t border-slate-100 text-slate-700">
                        <td className="px-3 py-1">{row.date}</td>
                        <td className="px-3 py-1">{row.actual.toLocaleString('tr-TR')}</td>
                        <td className="px-3 py-1">{row.predicted.toLocaleString('tr-TR')}</td>
                        <td className={`px-3 py-1 ${diff !== null && diff > 20 ? 'text-red-500' : 'text-slate-500'}`}>
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

      {result.model_overall_mapes && Object.keys(result.model_overall_mapes).length > 1 && (
        <div className="mt-4 border-t border-blue-100 pt-4">
          <div className="mb-2 text-xs font-medium text-slate-500">Model Karşılaştırması — Genel MAPE</div>
          <div className="flex flex-wrap gap-2">
            {Object.entries(result.model_overall_mapes)
              .sort(([, a], [, b]) => (a ?? 999) - (b ?? 999))
              .map(([model, mape]) => {
                const q = mape !== null ? mapeQuality(mape) : null
                return (
                  <div
                    key={model}
                    className="flex items-center gap-1.5 rounded-md border border-slate-200 bg-white px-2.5 py-1.5 text-xs shadow-sm"
                  >
                    <span className="text-slate-500">{MODEL_LABELS[model] ?? model}:</span>
                    <span className={`font-semibold ${q?.cls ?? 'text-slate-400'}`}>
                      {mape !== null ? `${mape.toFixed(1)}%` : '—'}
                    </span>
                    {q && (
                      <span className={`${q.cls} opacity-75`}>({q.label})</span>
                    )}
                  </div>
                )
              })}
          </div>

          {(() => {
            const rowsWithModelMapes = flatRows.filter(
              ({ info }) => info.model_mapes && Object.keys(info.model_mapes).length > 1,
            )
            if (rowsWithModelMapes.length === 0) return null
            const modelNames = Object.keys(result.model_overall_mapes).sort(
              (a, b) => (result.model_overall_mapes![a] ?? 999) - (result.model_overall_mapes![b] ?? 999),
            )
            return (
              <details className="mt-3">
                <summary className="cursor-pointer text-xs text-slate-500 hover:text-slate-700">
                  Ekip / işlem tipi bazında model karşılaştırması
                </summary>
                <div className="mt-2 overflow-x-auto rounded border border-slate-200">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-slate-50">
                      <tr className="text-slate-500">
                        <th className="px-3 py-1.5 font-medium">Ekip</th>
                        <th className="px-3 py-1.5 font-medium">İşlem Tipi</th>
                        {modelNames.map((m) => (
                          <th key={m} className="px-3 py-1.5 font-medium">
                            {MODEL_LABELS[m] ?? m}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {rowsWithModelMapes.map(({ team, tt, info }) => (
                        <tr key={`${team}::${tt}`} className="border-t border-slate-100 text-slate-700">
                          <td className="px-3 py-1.5 text-slate-500">{team}</td>
                          <td className="px-3 py-1.5">{tt}</td>
                          {modelNames.map((m) => {
                            const v = info.model_mapes?.[m] ?? null
                            const q = v !== null ? mapeQuality(v) : null
                            return (
                              <td key={m} className={`px-3 py-1.5 font-medium ${q?.cls ?? 'text-slate-400'}`}>
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

      <p className="mt-3 text-xs text-slate-400">
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
    <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="mb-1 flex items-center justify-between">
        <div className="text-sm font-medium text-slate-800">Model eğitimi — adım adım ilerleme</div>
        {status.total_units > 0 && (
          <span className="text-xs text-slate-500">
            {status.completed_units}/{status.total_units} model eğitildi
          </span>
        )}
      </div>

      <div className="mb-4 h-2 overflow-hidden rounded-full bg-slate-200">
        <div
          className={`h-full rounded-full transition-all duration-500 ease-out ${
            status.status === 'error' ? 'bg-red-500' : status.status === 'done' ? 'bg-emerald-500' : 'bg-blue-600'
          }`}
          style={{ width: `${Math.max(pct, status.status === 'running' ? 4 : 0)}%` }}
        />
      </div>

      <p className="mb-4 text-xs text-slate-500">{status.message || 'Eğitim başlatılıyor…'}</p>

      {status.steps.length > 0 && (
        <ol ref={logRef} className="mb-4 max-h-64 divide-y divide-slate-100 overflow-y-auto rounded-lg border border-slate-200 bg-slate-50 px-4">
          {status.steps.map((step, i) => (
            <StepRow key={`${step.at}-${i}`} step={step} />
          ))}
        </ol>
      )}

      {status.status === 'done' && (
        <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-4">
          <div className="mb-2 text-sm font-medium text-emerald-700">Eğitim tamamlandı</div>
          {summaries.length > 0 && (
            <div className="max-h-64 overflow-y-auto">
              <table className="w-full text-left text-xs text-slate-700">
                <thead className="sticky top-0 bg-emerald-50">
                  <tr className="text-slate-500">
                    <th className="pb-1 pr-4 font-medium">Ekip</th>
                    <th className="pb-1 pr-4 font-medium">İşlem Tipi</th>
                    <th className="pb-1 pr-4 font-medium">Frekans</th>
                    <th className="pb-1 pr-4 font-medium">Seçilen Algoritma</th>
                    <th className="pb-1 font-medium">CV RMSE</th>
                  </tr>
                </thead>
                <tbody>
                  {summaries.map((s, i) => (
                    <tr key={i} className="border-t border-emerald-100">
                      <td className="py-1 pr-4 text-slate-500">{s.team}</td>
                      <td className="py-1 pr-4">{s.type}</td>
                      <td className="py-1 pr-4">{s.freq === 'daily' ? 'Günlük' : 'Saatlik'}</td>
                      <td className="py-1 pr-4 font-medium text-amber-600">{s.model}</td>
                      <td className="py-1">{s.cv_rmse?.toFixed(2)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
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
        <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-600">
          {status.message}
        </div>
      )}
    </div>
  )
}
