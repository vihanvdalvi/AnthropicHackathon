import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { getIssue, getStats } from '../api/client'
import EmpathySurvey from '../components/EmpathySurvey'
import EmpathyResults from '../components/EmpathyResults'

export default function SurveyPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [issue, setIssue] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [stats, setStats] = useState(null)
  const [done, setDone] = useState(false)
  const userId = typeof window !== 'undefined' ? localStorage.getItem('user_id') : null

  useEffect(() => {
    getIssue(id)
      .then(setIssue)
      .catch(() => setError('Could not load issue.'))
      .finally(() => setLoading(false))
  }, [id])

  const handleComplete = async () => {
    try {
      const s = await getStats(id)
      setStats(s)
    } catch {
      setStats(null)
    }
    setDone(true)
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-slate-400 animate-pulse">Loading survey…</div>
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
    <div className="max-w-2xl mx-auto px-4 py-8">
      <button
        onClick={() => navigate(`/issue/${id}`)}
        className="text-slate-400 hover:text-white text-sm mb-6 flex items-center gap-1 transition-colors"
      >
        ← Back to issue
      </button>

      <div className="mb-6">
        <div className="text-slate-500 text-xs uppercase tracking-wide">Empathy survey</div>
        <h1 className="text-2xl font-bold text-white mt-1">{issue.label}</h1>
        <p className="text-slate-400 text-sm mt-1">
          Five quick steps. No labels. Your answers shape the campus pulse.
        </p>
      </div>

      {!done ? (
        <EmpathySurvey
          userId={userId}
          issueId={id}
          onComplete={handleComplete}
        />
      ) : (
        <EmpathyResults
          stats={stats}
          issueLabel={issue.label}
          onBack={() => navigate(`/issue/${id}`)}
        />
      )}
    </div>
  )
}
