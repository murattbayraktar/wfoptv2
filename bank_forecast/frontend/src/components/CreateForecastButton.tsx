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
        className="w-full rounded-md bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-slate-200 disabled:text-slate-400"
      >
        {uiStep === 'progress' ? 'Tahmin oluşturuluyor…' : 'Tahmin Oluştur'}
      </button>
      {!dataset?.loaded && (
        <p className="mt-2 text-center text-xs text-slate-400">Önce CSV yükleyin</p>
      )}
      {forecastError && (
        <p className="mt-2 text-center text-xs text-red-500">{forecastError}</p>
      )}
    </div>
  )
}
