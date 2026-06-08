import { useData } from '../context/DataContext'
import UploadDropzone from './UploadDropzone'
import TrainingProgress from './TrainingProgress'
import { MODEL_LABELS } from '../constants'

const HOLDOUT_OPTIONS = [
  { value: 0, label: 'Yok' },
  { value: 10, label: '10 gün' },
  { value: 30, label: '30 gün' },
]

function DatasetSummaryCard() {
  const {
    dataset,
    trainModels,
    holdoutDays,
    setHoldoutDays,
    startTraining,
    startingTraining,
    trainingStartError,
    retrainStatus,
  } = useData()
  if (!dataset?.loaded) return null

  const isRunning = retrainStatus?.status === 'running'

  return (
    <div className="rounded-xl border border-navy-700 bg-navy-900 p-6">
      <div className="mb-1 text-sm font-semibold text-slate-100">Yüklenen veri</div>
      <p className="text-sm text-slate-300">
        <span className="font-medium text-slate-100">{dataset.filename}</span>
        {dataset.date_range && (
          <>
            {' '}— {dataset.date_range.start} – {dataset.date_range.end} arası{' '}
            {dataset.row_count?.toLocaleString('tr-TR')} kayıt
          </>
        )}
        {dataset.transaction_types && dataset.transaction_types.length > 0 && (
          <>, işlem tipleri: {dataset.transaction_types.join(', ')}</>
        )}
        .
      </p>

      {dataset.source_kind === 'upload' && (
        <div className="mt-4 flex flex-col items-start gap-4 border-t border-navy-800 pt-4">
          {/* Holdout seçeneği */}
          <div>
            <div className="mb-2 text-xs font-medium text-slate-400">Doğrulama için son günler</div>
            <div className="flex gap-2">
              {HOLDOUT_OPTIONS.map((opt) => (
                <button
                  key={opt.value}
                  type="button"
                  onClick={() => setHoldoutDays(opt.value)}
                  disabled={isRunning}
                  className={`rounded-md border px-3 py-1.5 text-xs font-medium transition-colors disabled:opacity-50 ${
                    holdoutDays === opt.value
                      ? 'border-gold-500 bg-gold-500/20 text-gold-300'
                      : 'border-navy-600 bg-navy-800 text-slate-400 hover:border-navy-500 hover:text-slate-300'
                  }`}
                >
                  {opt.label}
                </button>
              ))}
            </div>
            {holdoutDays > 0 && (
              <p className="mt-1.5 text-xs text-slate-500">
                En son {holdoutDays} gün eğitime dahil edilmez; eğitim bitince bu günler için
                otomatik tahmin yapılır ve MAPE hesaplanır.
              </p>
            )}
          </div>

          <button
            type="button"
            onClick={() => void startTraining()}
            disabled={startingTraining || isRunning}
            className="rounded-md border border-gold-500/60 bg-gold-500/10 px-5 py-2.5 text-sm font-medium text-gold-400 transition-colors hover:bg-gold-500/20 disabled:opacity-50"
          >
            {isRunning
              ? 'Eğitim devam ediyor…'
              : startingTraining
                ? 'Eğitim başlatılıyor…'
                : `Eğitimi Başlat — ${trainModels.map((m) => MODEL_LABELS[m] ?? m).join(' + ')}`}
          </button>
          {isRunning && (
            <p className="text-xs text-slate-500">
              Devam eden eğitim tamamlanmadan yeni bir eğitim başlatılamaz — ilerlemeyi aşağıdan izleyebilirsiniz.
            </p>
          )}
          {!isRunning && trainingStartError && <p className="text-xs text-red-400">{trainingStartError}</p>}
        </div>
      )}

      {dataset.source_kind === 'demo' && (
        <p className="mt-3 rounded-lg border border-navy-700 bg-navy-950/60 px-4 py-2.5 text-xs text-slate-400">
          Bu örnek (demo) veri ile model eğitimi desteklenmiyor. Modelleri yeniden eğitmek için
          gerçek bir CSV dosyası yükleyin.
        </p>
      )}
    </div>
  )
}

export default function TrainingScreen() {
  const { dataset, retrainStatus } = useData()
  const showProgress = dataset?.loaded && dataset.source_kind === 'upload' && dataset.loaded_at && retrainStatus

  return (
    <div className="space-y-6">
      <div className="rounded-xl border border-navy-700 bg-navy-900 p-6">
        <h1 className="mb-2 text-base font-semibold text-slate-100">Veri & Model Eğitimi</h1>
        <p className="text-sm text-slate-400">
          Buradan yeni bir CSV yükleyin, eğitim için kullanılacak algoritmayı seçin ve ardından
          "Eğitimi Başlat" butonuna tıklayın. Sistem veriyi analiz edip işlem tipi ve frekans
          (günlük / saatlik) başına seçtiğiniz algoritmayı (veya "Tümü" seçiliyse en uygununu
          otomatik olarak) arka planda eğitir. Aşağıda eğitim sürecinin adımlarını ve ilerlemesini
          canlı olarak izleyebilirsiniz.
        </p>
      </div>

      <UploadDropzone />
      <DatasetSummaryCard />
      {showProgress && <TrainingProgress key={dataset.loaded_at} status={retrainStatus} />}
    </div>
  )
}
