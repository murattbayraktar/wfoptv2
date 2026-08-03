import { useData } from '../context/DataContext'
import DateRangePicker from './DateRangePicker'
import ForecastModelPicker from './ForecastModelPicker'
import CreateForecastButton from './CreateForecastButton'

function TeamPicker() {
  const { teamOptions, selectedTeam, setSelectedTeam } = useData()
  if (teamOptions.length === 0) return null

  return (
    <div className="mt-5">
      <div className="mb-3 text-xs font-semibold uppercase tracking-wider text-slate-500">
        Ekip
      </div>
      <select
        value={selectedTeam}
        onChange={(e) => setSelectedTeam(e.target.value)}
        className="w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-200"
      >
        <option value="">Tüm ekipler</option>
        {teamOptions.map((team) => (
          <option key={team} value={team}>
            {team}
          </option>
        ))}
      </select>
    </div>
  )
}

export default function Sidebar() {
  return (
    <aside className="flex w-64 shrink-0 flex-col border-r border-slate-200 bg-white p-5">
      <DateRangePicker />
      <TeamPicker />
      <ForecastModelPicker />
      <div className="mt-5">
        <CreateForecastButton />
      </div>
    </aside>
  )
}
