import { useData } from '../context/DataContext'
import type { Screen } from '../App'

interface TopBarProps {
  screen: Screen
  onScreenChange: (screen: Screen) => void
}

export default function TopBar({ screen, onScreenChange }: TopBarProps) {
  const { datasetMap, anyLoaded } = useData()

  const loadedLabels = (['talimat', 'islem'] as const)
    .map((mt) => datasetMap[mt])
    .filter((d) => d?.loaded)
    .map((d) => `${d!.filename} (${d!.row_count?.toLocaleString('tr-TR')} kayıt)`)

  const status = anyLoaded ? `${loadedLabels.length} veri yüklü` : 'Veri yüklenmedi'
  const statusTitle = anyLoaded ? loadedLabels.join(' · ') : undefined

  return (
    <header className="flex items-center justify-between border-b border-slate-800 bg-slate-900 px-6 py-3">
      <div className="flex items-center gap-6">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-md bg-blue-600 text-white">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M3 9.5 12 3l9 6.5V21a1 1 0 0 1-1 1h-5v-7H9v7H4a1 1 0 0 1-1-1V9.5Z" />
            </svg>
          </div>
          <div>
            <div className="text-sm font-semibold tracking-wide text-slate-100">WFOpt</div>
            <div className="text-xs text-slate-400">İşlem Hacmi Tahmin Sistemi</div>
          </div>
        </div>

        <nav className="flex items-center gap-1 rounded-lg border border-slate-700 bg-slate-800/60 p-1 text-xs">
          {(
            [
              { id: 'forecast' as const, label: 'Tahmin' },
              { id: 'training' as const, label: 'Veri & Eğitim' },
              { id: 'calibration' as const, label: 'Kalibrasyon' },
            ]
          ).map((tab) => (
            <button
              key={tab.id}
              type="button"
              onClick={() => onScreenChange(tab.id)}
              className={`whitespace-nowrap rounded-md px-3 py-1.5 font-medium transition-colors ${
                screen === tab.id
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      <div className="flex items-center gap-3 text-xs">
        <span
          title={statusTitle}
          className="flex items-center gap-2 rounded-full border border-slate-700 bg-slate-800 px-3 py-1 text-slate-300"
        >
          <span className={`h-2 w-2 rounded-full ${anyLoaded ? 'bg-emerald-500' : 'bg-slate-500'}`} />
          {status}
        </span>
        <span className="rounded-full border border-slate-700 bg-slate-800 px-3 py-1 text-slate-500">
          In-Memory · Sayfa yenilenince sıfırlanır
        </span>
      </div>
    </header>
  )
}
