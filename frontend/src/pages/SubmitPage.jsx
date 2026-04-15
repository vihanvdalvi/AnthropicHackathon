import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { submitPost } from '../api/client'

export default function SubmitPage() {
  const navigate = useNavigate()
  const [text, setText] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  const userId = localStorage.getItem('user_id')

  const handleSubmit = async () => {
    if (!text.trim()) return
    if (!userId) {
      setError('No user session found. Please refresh the page.')
      return
    }
    setSubmitting(true)
    setError(null)
    try {
      const data = await submitPost(userId, text.trim())
      setResult(data)
      setText('')
    } catch {
      setError('Failed to submit. Is the backend running?')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="max-w-2xl mx-auto px-4 py-8">
      <button
        onClick={() => navigate('/')}
        className="text-slate-400 hover:text-white text-sm mb-6 flex items-center gap-1 transition-colors"
      >
        ← Back
      </button>

      <h1 className="text-2xl font-bold text-white mb-2">Share your opinion</h1>
      <p className="text-slate-400 text-sm mb-6">
        Say anything on your mind about campus life. Your post is anonymous and will be
        classified into the most relevant issue.
      </p>

      {result && (
        <div className="bg-emerald-950/40 border border-emerald-700/40 rounded-xl p-4 mb-6">
          <p className="text-emerald-300 font-medium">Posted successfully!</p>
          <p className="text-slate-400 text-sm mt-1">
            Classified under: <span className="text-white">{result.issue_label}</span>
          </p>
          <button
            onClick={() => navigate(`/issue/${result.issue_id}`)}
            className="mt-3 text-indigo-400 hover:underline text-sm"
          >
            View the full discussion →
          </button>
        </div>
      )}

      {error && (
        <div className="bg-rose-950/30 border border-rose-800/40 rounded-xl p-4 mb-6 text-rose-300 text-sm">
          {error}
        </div>
      )}

      <textarea
        value={text}
        onChange={e => setText(e.target.value)}
        placeholder="What's on your mind? Housing costs, dining, safety, mental health..."
        rows={6}
        className="w-full bg-slate-800 border border-slate-600 rounded-xl p-4 text-slate-200 placeholder-slate-500 resize-none focus:outline-none focus:border-indigo-500 transition-colors text-sm"
      />

      <div className="flex items-center justify-between mt-3">
        <span className="text-slate-500 text-sm">{text.length} characters</span>
        <button
          onClick={handleSubmit}
          disabled={!text.trim() || submitting}
          className="bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-700 disabled:text-slate-500 text-white font-medium px-6 py-2.5 rounded-xl transition-colors text-sm"
        >
          {submitting ? 'Submitting...' : 'Submit anonymously'}
        </button>
      </div>
    </div>
  )
}
