import { useNavigate } from 'react-router-dom'

export default function IssueCard({ issue, rank }) {
  const navigate = useNavigate()

  const sentimentColor = issue.sentiment_avg >= 0
    ? 'text-emerald-400'
    : 'text-rose-400'

  const intensityWidth = `${(issue.intensity_avg / 10) * 100}%`

  return (
    <div
      onClick={() => navigate(`/issue/${issue.id}`)}
      className="bg-slate-800 border border-slate-700 rounded-xl p-4 cursor-pointer hover:border-indigo-500 hover:bg-slate-750 transition-all group"
    >
      <div className="flex items-start gap-3">
        <span className="text-2xl font-bold text-slate-500 w-8 shrink-0 group-hover:text-indigo-400 transition-colors">
          {rank}
        </span>
        <div className="flex-1 min-w-0">
          <h3 className="text-white font-semibold text-base truncate group-hover:text-indigo-300 transition-colors">
            {issue.label}
          </h3>
          <div className="flex items-center gap-4 mt-2 text-sm text-slate-400">
            <span>{issue.post_count} voices</span>
            <span className={sentimentColor}>
              {issue.sentiment_avg >= 0 ? '▲' : '▼'} {Math.abs(issue.sentiment_avg).toFixed(2)}
            </span>
          </div>
          <div className="mt-2">
            <div className="flex justify-between text-xs text-slate-500 mb-1">
              <span>intensity</span>
              <span>{issue.intensity_avg?.toFixed(1)}/10</span>
            </div>
            <div className="h-1.5 bg-slate-700 rounded-full overflow-hidden">
              <div
                className="h-full bg-indigo-500 rounded-full transition-all"
                style={{ width: intensityWidth }}
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
