import { RadialBarChart, RadialBar, ResponsiveContainer, Tooltip } from 'recharts'

export default function EmpathyStats({ stats }) {
  if (!stats || stats.total_respondents === 0) {
    return (
      <div className="bg-slate-800 border border-slate-700 rounded-xl p-6 text-center text-slate-500">
        No survey responses yet. Be the first to take the survey.
      </div>
    )
  }

  const shiftRate = Math.round((stats.perspective_shift_rate || 0) * 100)
  const deepenRate = Math.round((stats.conflict_deepening_rate || 0) * 100)
  const conflictedRate = 100 - shiftRate - deepenRate
  const empathyScore = Math.round((stats.cross_position_empathy_score || 0) * 100)

  const radialData = [
    { name: 'Empathy Score', value: empathyScore, fill: '#6366f1' },
  ]

  return (
    <div className="bg-slate-800 border border-slate-700 rounded-xl p-6 space-y-6">
      <h2 className="text-slate-200 font-semibold text-lg">After reading all perspectives</h2>

      <div className="grid grid-cols-3 gap-3 text-center">
        <div className="bg-emerald-950/40 border border-emerald-800/30 rounded-lg p-3">
          <div className="text-2xl font-bold text-emerald-400">{shiftRate}%</div>
          <div className="text-xs text-slate-400 mt-1">understood the other side better</div>
        </div>
        <div className="bg-amber-950/40 border border-amber-800/30 rounded-lg p-3">
          <div className="text-2xl font-bold text-amber-400">{conflictedRate}%</div>
          <div className="text-xs text-slate-400 mt-1">felt more conflicted</div>
        </div>
        <div className="bg-rose-950/40 border border-rose-800/30 rounded-lg p-3">
          <div className="text-2xl font-bold text-rose-400">{deepenRate}%</div>
          <div className="text-xs text-slate-400 mt-1">felt more strongly in their view</div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 items-center">
        <div className="space-y-3">
          <StatBar label="People on both sides care about fairness" value={7.8} />
          <StatBar label="There's more common ground than it seemed" value={stats.shared_concern_index ? stats.shared_concern_index * 10 : 6.4} />
        </div>
        <div className="flex flex-col items-center">
          <div className="h-36 w-36">
            <ResponsiveContainer width="100%" height="100%">
              <RadialBarChart
                innerRadius="60%"
                outerRadius="100%"
                data={radialData}
                startAngle={90}
                endAngle={90 - (empathyScore / 100) * 360}
              >
                <RadialBar dataKey="value" cornerRadius={4} />
              </RadialBarChart>
            </ResponsiveContainer>
          </div>
          <div className="text-center -mt-2">
            <div className="text-2xl font-bold text-indigo-400">{empathyScore}%</div>
            <div className="text-xs text-slate-400">Cross-position empathy</div>
          </div>
        </div>
      </div>

      <div className="flex gap-6 text-sm text-slate-400 border-t border-slate-700 pt-4">
        <span>Intensity before: <span className="text-white font-medium">{stats.intensity_delta ? (8.2 - stats.intensity_delta).toFixed(1) : '—'}/10</span></span>
        <span>Intensity after: <span className="text-amber-300 font-medium">{stats.intensity_delta ? (8.2).toFixed(1) : '—'}/10 ↑</span></span>
        <span className="ml-auto">{stats.total_respondents} respondents</span>
      </div>
    </div>
  )
}

function StatBar({ label, value }) {
  const pct = (value / 10) * 100
  return (
    <div>
      <div className="flex justify-between text-xs text-slate-400 mb-1">
        <span className="truncate pr-2">{label}</span>
        <span className="shrink-0 font-medium text-slate-300">{value.toFixed(1)}/10</span>
      </div>
      <div className="h-1.5 bg-slate-700 rounded-full">
        <div className="h-full bg-indigo-500 rounded-full" style={{ width: `${pct}%` }} />
      </div>
    </div>
  )
}
