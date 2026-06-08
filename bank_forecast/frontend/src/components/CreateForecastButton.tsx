import { useData } from '../context/DataContext'

export default function CreateForecastButton() {
  const { dataset, uiStep, createForecast, forecastError } = useData()
  const disabled = !dataset?.loaded || uiStep === 'progress'

  return (
    <div>
      <button
        type="button"
        onClick={() => void createForecast()}
        disabled={disabled}
        className="w-full rounded-md bg-gold-500 px-4 py-2.5 text-sm font-semibold text-navy-950 transition-colors hover:bg-gold-400 disabled:cursor-not-allowed disabled:bg-navy-700 disabled:text-slate-500"
      >
        {uiStep === 'progress' ? 'Tahmin oluşturuluyor…' : 'Tahmin Oluştur'}
      </button>
      {!dataset?.loaded && (
        <p className="mt-2 text-center text-xs text-slate-500">Önce CSV yükleyin</p>
      )}
      {forecastError && (
        <p className="mt-2 text-center text-xs text-red-400">{forecastError}</p>
      )}
    </div>
  )
}
