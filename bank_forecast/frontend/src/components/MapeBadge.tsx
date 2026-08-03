function mapeQuality(mape: number): { label: string; cls: string } {
  if (mape < 10) return { label: 'İyi', cls: 'text-emerald-600' }
  if (mape < 20) return { label: 'Kabul', cls: 'text-amber-600' }
  return { label: 'Zayıf', cls: 'text-red-500' }
}

export function MapeBadge({ mape }: { mape: number | null }) {
  if (mape === null) return <span className="text-xs text-slate-400">—</span>
  const q = mapeQuality(mape)
  return (
    <span className={`text-xs font-semibold ${q.cls}`}>
      {mape.toFixed(1)}% <span className="font-normal opacity-75">({q.label})</span>
    </span>
  )
}
