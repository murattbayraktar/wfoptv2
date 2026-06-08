import DateRangePicker from './DateRangePicker'
import ForecastModelPicker from './ForecastModelPicker'
import CreateForecastButton from './CreateForecastButton'

export default function Sidebar() {
  return (
    <aside className="flex w-64 shrink-0 flex-col border-r border-navy-700 bg-navy-900 p-5">
      <DateRangePicker />
      <div className="mt-5">
        <CreateForecastButton />
      </div>
      <ForecastModelPicker />
    </aside>
  )
}
