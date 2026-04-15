export default function IssueSummary({ issue }) {
  const sideA = issue.side_a_points || []
  const sideB = issue.side_b_points || []
  const shared = issue.shared_concerns || []

  return (
    <div className="space-y-6">
      {issue.summary && (
        <div className="bg-slate-800 border border-slate-700 rounded-xl p-5">
          <h2 className="text-slate-300 text-sm font-semibold uppercase tracking-wider mb-3">
            Overview
          </h2>
          <p className="text-slate-200 leading-relaxed">{issue.summary}</p>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-rose-950/30 border border-rose-800/40 rounded-xl p-5">
          <h2 className="text-rose-300 text-sm font-semibold uppercase tracking-wider mb-3">
            One perspective
          </h2>
          {sideA.length > 0 ? (
            <ul className="space-y-2">
              {sideA.map((point, i) => (
                <li key={i} className="flex gap-2 text-slate-300 text-sm leading-relaxed">
                  <span className="text-rose-400 shrink-0 mt-0.5">•</span>
                  <span>{point}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-slate-500 text-sm">No data yet</p>
          )}
        </div>

        <div className="bg-sky-950/30 border border-sky-800/40 rounded-xl p-5">
          <h2 className="text-sky-300 text-sm font-semibold uppercase tracking-wider mb-3">
            Another perspective
          </h2>
          {sideB.length > 0 ? (
            <ul className="space-y-2">
              {sideB.map((point, i) => (
                <li key={i} className="flex gap-2 text-slate-300 text-sm leading-relaxed">
                  <span className="text-sky-400 shrink-0 mt-0.5">•</span>
                  <span>{point}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-slate-500 text-sm">No data yet</p>
          )}
        </div>
      </div>

      {shared.length > 0 && (
        <div className="bg-emerald-950/30 border border-emerald-800/40 rounded-xl p-5">
          <h2 className="text-emerald-300 text-sm font-semibold uppercase tracking-wider mb-3">
            What everyone agrees on
          </h2>
          <ul className="space-y-2">
            {shared.map((point, i) => (
              <li key={i} className="flex gap-2 text-slate-300 text-sm leading-relaxed">
                <span className="text-emerald-400 shrink-0 mt-0.5">•</span>
                <span>{point}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
