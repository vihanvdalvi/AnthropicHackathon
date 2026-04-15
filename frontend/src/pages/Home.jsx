import { useEffect, useState } from 'react'
import { getIssues } from '../api/client'
import IssueCard from '../components/IssueCard'
import PulseMap from '../components/PulseMap'

export default function Home() {
  const [issues, setIssues] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    getIssues()
      .then(setIssues)
      .catch(() => setError('Could not load issues. Is the backend running?'))
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-slate-400 animate-pulse">Loading campus pulse...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-rose-400 bg-rose-950/30 border border-rose-800/40 rounded-xl p-6">{error}</div>
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white">Campus Pulse</h1>
        <p className="text-slate-400 mt-1">What students care about most this week</p>
      </div>

      {issues.length > 0 && (
        <div className="mb-8">
          <PulseMap issues={issues} />
        </div>
      )}

      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-slate-200 font-semibold text-lg">Top Issues This Week</h2>
        <span className="text-slate-500 text-sm">{issues.length} topics</span>
      </div>

      {issues.length === 0 ? (
        <div className="text-center py-16 text-slate-500">
          No issues yet. <a href="/submit" className="text-indigo-400 hover:underline">Submit the first opinion.</a>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {issues.map((issue, i) => (
            <IssueCard key={issue.id} issue={issue} rank={i + 1} />
          ))}
        </div>
      )}
    </div>
  )
}
