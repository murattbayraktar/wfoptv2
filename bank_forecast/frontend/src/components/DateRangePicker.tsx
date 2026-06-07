import { useData } from '../context/DataContext'

export default function DateRangePicker() {
  const { rangeStart, rangeEnd, setRangeStart, setRangeEnd } = useData()

  return (
    <div>
      <div className="mb-3 text-xs font-semibold uppercase tracking-wider text-slate-400">
        Tahmin Aralığı
      </div>
      <label className="mb-3 block">
        <span className="mb-1 block text-xs text-slate-400">Başlangıç</span>
        <input
          type="date"
          value={rangeStart}
          onChange={(e) => setRangeStart(e.target.value)}
          className="w-full rounded-md border border-navy-600 bg-navy-800 px-3 py-2 text-sm text-slate-100 outline-none focus:border-gold-500"
        />
      </label>
      <label className="block">
        <span className="mb-1 block text-xs text-slate-400">Bitiş</span>
        <input
          type="date"
          value={rangeEnd}
          onChange={(e) => setRangeEnd(e.target.value)}
          className="w-full rounded-md border border-navy-600 bg-navy-800 px-3 py-2 text-sm text-slate-100 outline-none focus:border-gold-500"
        />
      </label>
    </div>
  )
}
