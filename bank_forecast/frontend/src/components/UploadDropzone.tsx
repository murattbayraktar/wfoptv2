import { useRef, useState, type DragEvent } from 'react'
import { useData } from '../context/DataContext'

export default function UploadDropzone() {
  const { upload, loadDemo, loadingDataset, datasetError } = useData()
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
    <div className="rounded-xl border border-navy-700 bg-navy-900 p-8">
      <div
        onDragOver={(e) => {
          e.preventDefault()
          setDragOver(true)
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={onDrop}
        className={`flex flex-col items-center justify-center rounded-lg border-2 border-dashed px-8 py-12 text-center transition-colors ${
          dragOver ? 'border-gold-400 bg-navy-800' : 'border-navy-600'
        }`}
      >
        <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-full border border-navy-600 text-slate-400">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M12 16V4m0 0L7 9m5-5 5 5M5 20h14" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </div>
        <div className="mb-1 font-medium text-slate-100">CSV dosyasını sürükleyin veya seçin</div>
        <div className="mb-4 text-xs text-slate-500">tarih, saat, işlem tipi, adet, tutar</div>
        <button
          type="button"
          onClick={() => inputRef.current?.click()}
          disabled={loadingDataset}
          className="rounded-md border border-navy-600 px-4 py-2 text-sm text-slate-200 transition-colors hover:border-gold-500 disabled:opacity-50"
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

      <div className="my-6 flex items-center gap-4 text-xs text-slate-500">
        <div className="h-px flex-1 bg-navy-700" />
        veya
        <div className="h-px flex-1 bg-navy-700" />
      </div>

      <div className="flex justify-center">
        <button
          type="button"
          onClick={() => void loadDemo()}
          disabled={loadingDataset}
          className="rounded-md border border-gold-500/60 bg-gold-500/10 px-5 py-2.5 text-sm font-medium text-gold-400 transition-colors hover:bg-gold-500/20 disabled:opacity-50"
        >
          ✦ Demo Data Yükle (2024 – 12 aylık sentetik)
        </button>
      </div>

      {loadingDataset && (
        <p className="mt-4 text-center text-xs text-slate-500">Veri yükleniyor ve analiz ediliyor…</p>
      )}
      {datasetError && (
        <p className="mt-4 text-center text-xs text-red-400">{datasetError}</p>
      )}
    </div>
  )
}
