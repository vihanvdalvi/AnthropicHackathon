export default function EmpathyResults({ stats, issueLabel, onBack }) {
  const shift = Math.round((stats?.perspective_shift_rate || 0) * 100)
  const deepen = Math.round((stats?.conflict_deepening_rate || 0) * 100)
  const conflicted = Math.max(0, 100 - shift - deepen)
  const empathy = Math.round((stats?.cross_position_empathy_score || 0) * 100)
  const sharedIdx = stats?.shared_concern_index != null
    ? (stats.shared_concern_index * 10).toFixed(1)
    : '—'
  const delta = stats?.intensity_delta || 0
  const respondents = stats?.total_respondents || 0

  return (
    <div className="bg-slate-800 border border-slate-700 rounded-xl p-6 space-y-6">
      <div className="flex items-start gap-3">
        <div className="text-3xl">🌱</div>
        <div>
          <h2 className="text-white text-xl font-semibold">Thank you for sharing.</h2>
          <p className="text-slate-400 text-sm mt-1">
            Your response has been added to the campus pulse
            {issueLabel ? ` on ${issueLabel}.` : '.'}
          </p>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-3 text-center">
        <StatCard tone="emerald" value={`${shift}%`} label="understood the other side better" />
        <StatCard tone="amber" value={`${conflicted}%`} label="felt more conflicted" />
        <StatCard tone="rose" value={`${deepen}%`} label="felt more strongly in their view" />
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <MetricBox label="Cross-position empathy" value={`${empathy}%`} tone="indigo" />
        <MetricBox label="Shared concern index" value={`${sharedIdx}/10`} tone="indigo" />
        <MetricBox
          label="Intensity change"
          value={`${delta >= 0 ? '+' : ''}${delta.toFixed(2)}`}
          tone={delta > 0 ? 'amber' : 'emerald'}
          hint={delta > 0 ? 'People feel more strongly after reading' : 'People feel calmer after reading'}
        />
        <MetricBox label="Total respondents" value={`${respondents}`} tone="slate" />
      </div>

      {onBack && (
        <button
          onClick={onBack}
          className="w-full bg-indigo-600 hover:bg-indigo-500 text-white font-medium py-3 rounded-xl transition-colors"
        >
          Back to issue
        </button>
      )}
    </div>
  )
}

function StatCard({ tone, value, label }) {
  const tones = {
    emerald: 'bg-emerald-950/40 border-emerald-800/30 text-emerald-400',
    amber: 'bg-amber-950/40 border-amber-800/30 text-amber-400',
    rose: 'bg-rose-950/40 border-rose-800/30 text-rose-400',
  }
  return (
    <div className={`border rounded-lg p-3 ${tones[tone]}`}>
      <div className="text-2xl font-bold">{value}</div>
      <div className="text-xs text-slate-400 mt-1">{label}</div>
    </div>
  )
}

function MetricBox({ label, value, tone, hint }) {
  const tones = {
    indigo: 'text-indigo-400',
    amber: 'text-amber-400',
    emerald: 'text-emerald-400',
    slate: 'text-slate-200',
  }
  return (
    <div className="bg-slate-900/50 border border-slate-700 rounded-lg p-4">
      <div className="text-xs uppercase tracking-wide text-slate-500">{label}</div>
      <div className={`text-2xl font-bold mt-1 ${tones[tone]}`}>{value}</div>
      {hint && <div className="text-xs text-slate-500 mt-1">{hint}</div>}
    </div>
  )
}
