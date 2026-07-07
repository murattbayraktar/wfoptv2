import { useData } from '../context/DataContext'

export default function ExportToExcelButton() {
  const { exportExcel, exporting, exportError } = useData()

  return (
    <div className="flex flex-col items-end gap-1">
      <button
        type="button"
        onClick={() => void exportExcel()}
        disabled={exporting}
        className="rounded-md border border-emerald-300 bg-emerald-50 px-3 py-1.5 text-xs font-medium text-emerald-700 transition-colors hover:bg-emerald-100 disabled:opacity-50"
      >
        {exporting ? 'Excel oluşturuluyor…' : '⭳ Excel\'e Aktar'}
      </button>
      {exportError && <p className="text-xs text-red-500">{exportError}</p>}
    </div>
  )
}
