import { useRef, useState, type DragEvent } from 'react'
import { useData } from '../context/DataContext'
import { MODEL_LABELS, MODEL_OPTIONS } from '../constants'

export default function UploadDropzone() {
  const { upload, loadDemo, loadingDataset, datasetError, trainModels, toggleTrainModel } = useData()
  const inputRef = useRef<HTMLInputElement>(null)
  const [dragOver, setDragOver] = useState(false)

  function handleFiles(files: FileList | null) {
    const file = files?.[0]
    if (file) void upload(file)
  }

  function onDrop(e: DragEvent<HTMLDivElement>) {
    e.preventDefault()
    setDragOver(false)
    handleFiles(e.dataTransfer.files)
  }

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-8 shadow-sm">
      <div className="mb-6">
        <label className="mb-2 block text-xs font-medium text-slate-500">
          Eğitim için algoritma seçimi
        </label>
        <div className="flex flex-col gap-1.5 rounded-md border border-slate-200 bg-slate-50 px-3 py-2.5">
          {MODEL_OPTIONS.map((opt) => {
            return (
              <label
                key={opt}
                className={`flex items-center gap-2 text-sm text-slate-700 ${loadingDataset ? 'opacity-50' : 'cursor-pointer'}`}
              >
                <input
                  type="checkbox"
                  checked={trainModels.includes(opt)}
                  onChange={() => toggleTrainModel(opt)}
                  disabled={loadingDataset}
                  className="h-4 w-4 rounded border-slate-300 bg-white accent-blue-600"
                />
                {MODEL_LABELS[opt] ?? opt}
              </label>
            )
          })}
        </div>
        <p className="mt-1.5 text-xs text-slate-400">
          "Tümü" seçilirse her aday algoritma denenip en iyisi otomatik seçilir (daha uzun sürer).
          Tek bir spesifik algoritma seçilirse eğitim yalnızca onunla yapılır (daha hızlıdır).
          Birden fazla spesifik algoritma seçerseniz HEPSİ tam veri ile eğitilip kaydedilir —
          tahmin ekranında aralarında karşılaştırma yapabilirsiniz (daha uzun sürer ve daha fazla disk alanı kullanır).
        </p>
      </div>
      <div
        onDragOver={(e) => {
          e.preventDefault()
          setDragOver(true)
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={onDrop}
        className={`flex flex-col items-center justify-center rounded-lg border-2 border-dashed px-8 py-12 text-center transition-colors ${
          dragOver ? 'border-blue-400 bg-blue-50' : 'border-slate-300 hover:border-slate-400'
        }`}
      >
        <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-full border border-slate-200 bg-slate-50 text-slate-400">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M12 16V4m0 0L7 9m5-5 5 5M5 20h14" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </div>
        <div className="mb-1 font-medium text-slate-900">CSV dosyasını sürükleyin veya seçin</div>
        <div className="mb-4 text-xs text-slate-400">tarih, saat, işlem tipi, adet, tutar</div>
        <button
          type="button"
          onClick={() => inputRef.current?.click()}
          disabled={loadingDataset}
          className="rounded-md border border-slate-300 bg-white px-4 py-2 text-sm text-slate-700 transition-colors hover:border-blue-400 hover:text-blue-600 disabled:opacity-50"
        >
          Dosya Seç
        </button>
        <input
          ref={inputRef}
          type="file"
          accept=".csv"
          className="hidden"
          onChange={(e) => handleFiles(e.target.files)}
        />
      </div>

      <div className="my-6 flex items-center gap-4 text-xs text-slate-400">
        <div className="h-px flex-1 bg-slate-200" />
        veya
        <div className="h-px flex-1 bg-slate-200" />
      </div>

      <div className="flex justify-center">
        <button
          type="button"
          onClick={() => void loadDemo()}
          disabled={loadingDataset}
          className="rounded-md border border-blue-300 bg-blue-50 px-5 py-2.5 text-sm font-medium text-blue-600 transition-colors hover:bg-blue-100 disabled:opacity-50"
        >
          ✦ Demo Data Yükle (2024 – 12 aylık sentetik)
        </button>
      </div>

      {loadingDataset && (
        <p className="mt-4 text-center text-xs text-slate-400">Veri yükleniyor ve analiz ediliyor…</p>
      )}
      {datasetError && (
        <p className="mt-4 text-center text-xs text-red-500">{datasetError}</p>
      )}
    </div>
  )
}
