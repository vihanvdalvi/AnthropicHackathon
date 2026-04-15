import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { getIssue } from '../api/client'
import IssueSummary from '../components/IssueSummary'
import EmpathyStats from '../components/EmpathyStats'

export default function IssuePage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [issue, setIssue] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    getIssue(id)
      .then(setIssue)
      .catch(() => setError('Could not load issue.'))
      .finally(() => setLoading(false))
  }, [id])

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-slate-400 animate-pulse">Loading issue...</div>
      </div>
    )
  }

  if (error || !issue) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-rose-400 bg-rose-950/30 border border-rose-800/40 rounded-xl p-6">
          {error || 'Issue not found.'}
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-3xl mx-auto px-4 py-8">
      <button
        onClick={() => navigate('/')}
        className="text-slate-400 hover:text-white text-sm mb-6 flex items-center gap-1 transition-colors"
      >
        ← Back to all issues
      </button>

      <div className="mb-6">
        <h1 className="text-2xl font-bold text-white">{issue.label}</h1>
        <div className="flex gap-4 mt-2 text-sm text-slate-400">
          <span>{issue.post_count} voices</span>
          <span>Intensity: {issue.intensity_avg?.toFixed(1)}/10</span>
          <span className={issue.sentiment_avg >= 0 ? 'text-emerald-400' : 'text-rose-400'}>
            Sentiment: {issue.sentiment_avg?.toFixed(2)}
          </span>
        </div>
      </div>

      <IssueSummary issue={issue} />

      <div className="mt-8">
        <EmpathyStats stats={issue.empathy_stats} />
      </div>

      <div className="mt-6 flex gap-3">
        <button
          onClick={() => navigate(`/issue/${id}/survey`)}
          className="flex-1 bg-indigo-600 hover:bg-indigo-500 text-white font-medium py-3 rounded-xl transition-colors"
        >
          How do you feel after reading this?
        </button>
        <button
          onClick={() => navigate('/submit')}
          className="px-5 bg-slate-700 hover:bg-slate-600 text-slate-200 font-medium py-3 rounded-xl transition-colors"
        >
          Share your view
        </button>
      </div>
    </div>
  )
}
