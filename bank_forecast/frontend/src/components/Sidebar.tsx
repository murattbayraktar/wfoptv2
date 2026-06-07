import DateRangePicker from './DateRangePicker'
import CreateForecastButton from './CreateForecastButton'

export default function Sidebar() {
  return (
    <aside className="flex w-64 shrink-0 flex-col justify-between border-r border-navy-700 bg-navy-900 p-5">
      <DateRangePicker />
      <div className="mt-8">
        <CreateForecastButton />
      </div>
    </aside>
  )
}
