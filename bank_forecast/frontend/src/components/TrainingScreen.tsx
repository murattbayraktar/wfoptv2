import { useData } from '../context/DataContext'
import UploadDropzone from './UploadDropzone'
import TrainingProgress from './TrainingProgress'

function DatasetSummaryCard() {
  const { dataset } = useData()
  if (!dataset?.loaded) return null

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
  const { dataset } = useData()
  const showProgress = dataset?.loaded && dataset.source_kind === 'upload'

  return (
    <div className="space-y-6">
      <div className="rounded-xl border border-navy-700 bg-navy-900 p-6">
        <h1 className="mb-2 text-base font-semibold text-slate-100">Veri & Model Eğitimi</h1>
        <p className="text-sm text-slate-400">
          Buradan yeni bir CSV yükleyin — sistem veriyi analiz edip işlem tipi ve frekans (günlük /
          saatlik) başına en uygun tahmin algoritmasını arka planda otomatik olarak seçer ve eğitir.
          Aşağıda eğitim sürecinin adımlarını ve ilerlemesini canlı olarak izleyebilirsiniz.
        </p>
      </div>

      <UploadDropzone />
      <DatasetSummaryCard />
      {showProgress && <TrainingProgress key={dataset.loaded_at} />}
    </div>
  )
}
