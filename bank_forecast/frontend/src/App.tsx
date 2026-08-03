import { useState } from 'react'
import { DataProvider, useData } from './context/DataContext'
import type { CalibrationScope, DatasetSummaryMap } from './types'
import { METRIC_LABELS, METRIC_TYPES } from './types'
import TopBar from './components/TopBar'
import Sidebar from './components/Sidebar'
import ProgressStepper from './components/ProgressStepper'
import ResultsPanel from './components/ResultsPanel'
import TrainingScreen from './components/TrainingScreen'
import CalibrationScreen from './components/CalibrationScreen'

export type Screen = 'forecast' | 'training' | 'calibration'

function NoDataCard({ onGoToTraining }: { onGoToTraining: () => void }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-10 text-center shadow-sm">
      <div className="mb-4 text-4xl">🏦</div>
      <h1 className="mb-2 text-lg font-semibold text-slate-900">İşlem Hacmi Tahmin Sistemine Hoş Geldiniz</h1>
      <p className="mx-auto mb-5 max-w-md text-sm text-slate-500">
        Tahmin oluşturabilmek için önce bir veri kümesi yüklemeniz gerekir. CSV yükleme ve model
        eğitimi artık <span className="font-medium text-slate-700">Veri & Eğitim</span> sekmesinde.
      </p>
      <button
        type="button"
        onClick={onGoToTraining}
        className="rounded-md border border-blue-300 bg-blue-50 px-5 py-2.5 text-sm font-medium text-blue-600 transition-colors hover:bg-blue-100"
      >
        Veri & Eğitim sekmesine git →
      </button>
    </div>
  )
}

function ReadyToForecastCard({ datasetMap }: { datasetMap: DatasetSummaryMap }) {
  return (
    <div className="rounded-xl border border-blue-200 bg-blue-50 p-6">
      <div className="mb-1 text-sm font-semibold text-blue-700">Veri hazır — sıradaki adım: tahmin</div>
      <div className="space-y-1 text-sm text-slate-600">
        {METRIC_TYPES.map((mt) => {
          const dataset = datasetMap[mt]
          if (!dataset?.loaded) return null
          return (
            <p key={mt}>
              <span className="font-medium text-slate-800">{METRIC_LABELS[mt]}:</span>{' '}
              <span className="font-medium text-slate-900">{dataset.filename}</span> yüklendi
              {dataset.date_range && (
                <>
                  {' '}({dataset.date_range.start} – {dataset.date_range.end} arası {dataset.row_count?.toLocaleString('tr-TR')} kayıt)
                </>
              )}
              .
            </p>
          )
        })}
      </div>
      <p className="mt-2 text-sm text-slate-600">
        Solda <span className="font-medium text-slate-800">Tahmin Aralığı</span> ve{' '}
        <span className="font-medium text-slate-800">Ekip</span>'i kontrol edip{' '}
        <span className="rounded bg-blue-600 px-1.5 py-0.5 text-xs font-semibold text-white">Tahmin Oluştur</span>{' '}
        butonuna tıklayın. Aralık, yüklenen verinin son 30 günüyle örtüşecek şekilde otomatik önerildi —
        böylece sonuçta gerçekleşen ile tahmin edilen değerleri karşılaştırabilirsiniz.
      </p>
    </div>
  )
}

function MainContent({
  onGoToTraining,
  onGoToCalibration,
}: {
  onGoToTraining: () => void
  onGoToCalibration: (scope: CalibrationScope) => void
}) {
  const { datasetMap, anyLoaded, uiStep, forecastResult } = useData()

  if (uiStep === 'progress') return <ProgressStepper />
  if (uiStep === 'results' && forecastResult) return <ResultsPanel onGoToCalibration={onGoToCalibration} />

  return (
    <div className="space-y-6">
      {anyLoaded ? <ReadyToForecastCard datasetMap={datasetMap} /> : <NoDataCard onGoToTraining={onGoToTraining} />}
    </div>
  )
}

function Layout() {
  const [screen, setScreen] = useState<Screen>('forecast')
  const [calibrationScope, setCalibrationScope] = useState<CalibrationScope | null>(null)
  const { uiStep, forecastResult } = useData()
  const showingResults = screen === 'forecast' && uiStep === 'results' && !!forecastResult

  const goToCalibration = (scope: CalibrationScope) => {
    setCalibrationScope(scope)
    setScreen('calibration')
  }

  return (
    <div className="flex min-h-screen flex-col">
      <TopBar screen={screen} onScreenChange={setScreen} />
      <div className="flex flex-1">
        {screen === 'forecast' && <Sidebar />}
        <main className="flex-1 overflow-y-auto p-6">
          <div className={showingResults || screen === 'calibration' ? 'mx-auto max-w-7xl' : 'mx-auto max-w-4xl'}>
            {screen === 'forecast' && (
              <MainContent onGoToTraining={() => setScreen('training')} onGoToCalibration={goToCalibration} />
            )}
            {screen === 'training' && <TrainingScreen />}
            {screen === 'calibration' && <CalibrationScreen initialScope={calibrationScope} />}
          </div>
        </main>
      </div>
    </div>
  )
}

export default function App() {
  return (
    <DataProvider>
      <Layout />
    </DataProvider>
  )
}
