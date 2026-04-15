import { useState } from 'react'
import { submitSurvey, submitPost } from '../api/client'
import StatementSliders from './StatementSliders'

const STARTING_POSITIONS = [
  'Strongly with one side',
  'Leaning one way',
  'Somewhere in the middle',
  "I hadn't thought about it",
]

const POST_FEELINGS = [
  'I understand the other side better, even if I still disagree',
  "I've shifted a little toward their view",
  'I feel more strongly in my original position',
  "I'm more conflicted than before",
]

const EMPATHY_CHOICES = [
  'They care about this for reasons I hadn’t considered',
  'Their concerns are more valid than I first thought',
  'We actually want similar things, just differently',
  "I still don't see where they're coming from",
]

const STATEMENTS = [
  'People on the other side of this issue care about fairness too.',
  'I can see why someone with different experiences would feel differently.',
  "This issue affects real people's daily lives.",
  "Even people I disagree with want what's best for the community.",
  "There's more common ground here than it first seemed.",
]

const TOTAL_STEPS = 5

export default function EmpathySurvey({ userId, issueId, onComplete }) {
  const [step, setStep] = useState(1)
  const [startingPosition, setStartingPosition] = useState(null)
  const [preIntensity, setPreIntensity] = useState(5)
  const [statementRatings, setStatementRatings] = useState([5, 5, 5, 5, 5])
  const [postFeeling, setPostFeeling] = useState(null)
  const [empathyChoice, setEmpathyChoice] = useState(null)
  const [freeText, setFreeText] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState(null)

  const canAdvance = () => {
    if (step === 1) return startingPosition !== null
    if (step === 2) return preIntensity >= 1
    if (step === 3) return statementRatings.every(v => v >= 1)
    if (step === 4) return postFeeling !== null
    if (step === 5) return empathyChoice !== null
    return true
  }

  const next = () => setStep(s => Math.min(s + 1, TOTAL_STEPS))
  const back = () => setStep(s => Math.max(s - 1, 1))

  const handleSubmit = async () => {
    setSubmitting(true)
    setError(null)
    try {
      const ratingsDict = statementRatings.reduce((acc, v, i) => {
        acc[String(i)] = v
        return acc
      }, {})
      await submitSurvey({
        user_id: userId,
        issue_id: issueId,
        starting_position: startingPosition,
        pre_intensity: preIntensity,
        post_feeling: postFeeling,
        empathy_choice: empathyChoice,
        statement_ratings: ratingsDict,
      })
      if (freeText.trim() && userId) {
        try { await submitPost(userId, freeText.trim()) } catch { /* non-blocking */ }
      }
      onComplete?.()
    } catch (e) {
      setError('Could not submit your response. Please try again.')
      setSubmitting(false)
    }
  }

  return (
    <div className="bg-slate-800 border border-slate-700 rounded-xl p-6 space-y-6">
      <ProgressBar step={step} total={TOTAL_STEPS} />

      {step === 1 && (
        <StepBlock
          heading="Where did you stand before reading this?"
          subheading="No political labels — just where you were."
        >
          <RadioList
            options={STARTING_POSITIONS}
            value={startingPosition}
            onChange={setStartingPosition}
          />
        </StepBlock>
      )}

      {step === 2 && (
        <StepBlock
          heading="How strongly do you feel about this issue?"
          subheading="1 = barely affects me · 10 = this matters deeply"
        >
          <div className="pt-2">
            <div className="flex justify-between items-center mb-3">
              <span className="text-slate-400 text-sm">Intensity</span>
              <span className="text-indigo-400 font-semibold tabular-nums">{preIntensity}/10</span>
            </div>
            <input
              type="range"
              min={1}
              max={10}
              step={1}
              value={preIntensity}
              onChange={(e) => setPreIntensity(Number(e.target.value))}
              className="w-full accent-indigo-500"
            />
            <div className="flex justify-between text-[10px] text-slate-500 mt-1">
              <span>Barely affects me</span>
              <span>Matters deeply</span>
            </div>
          </div>
        </StepBlock>
      )}

      {step === 3 && (
        <StepBlock
          heading="Rate each statement"
          subheading="How much do you agree with each, right now?"
        >
          <StatementSliders
            statements={STATEMENTS}
            values={statementRatings}
            onChange={(i, v) =>
              setStatementRatings(prev => prev.map((x, idx) => (idx === i ? v : x)))
            }
          />
        </StepBlock>
      )}

      {step === 4 && (
        <StepBlock
          heading="After reading all perspectives, how do you feel?"
          subheading="Pick what fits best."
        >
          <RadioList
            options={POST_FEELINGS}
            value={postFeeling}
            onChange={setPostFeeling}
          />
        </StepBlock>
      )}

      {step === 5 && (
        <StepBlock
          heading="What did you learn about people on the other side?"
        >
          <RadioList
            options={EMPATHY_CHOICES}
            value={empathyChoice}
            onChange={setEmpathyChoice}
          />
          <div className="pt-4">
            <label className="text-slate-300 text-sm font-medium">
              Anything you want to add? <span className="text-slate-500">(optional)</span>
            </label>
            <textarea
              value={freeText}
              onChange={(e) => setFreeText(e.target.value)}
              rows={3}
              placeholder="Your words re-enter the opinion pool."
              className="mt-2 w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-slate-200 text-sm placeholder:text-slate-600 focus:outline-none focus:border-indigo-500"
            />
          </div>
        </StepBlock>
      )}

      {error && (
        <div className="text-rose-400 text-sm bg-rose-950/30 border border-rose-800/40 rounded-lg p-3">
          {error}
        </div>
      )}

      <div className="flex items-center justify-between pt-2">
        <button
          onClick={back}
          disabled={step === 1 || submitting}
          className="text-slate-400 hover:text-white text-sm disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
        >
          ← Back
        </button>

        {step < TOTAL_STEPS ? (
          <button
            onClick={next}
            disabled={!canAdvance()}
            className="bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-700 disabled:cursor-not-allowed text-white font-medium px-5 py-2 rounded-lg transition-colors"
          >
            Next
          </button>
        ) : (
          <button
            onClick={handleSubmit}
            disabled={!canAdvance() || submitting}
            className="bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-700 disabled:cursor-not-allowed text-white font-medium px-5 py-2 rounded-lg transition-colors"
          >
            {submitting ? 'Submitting…' : 'Submit'}
          </button>
        )}
      </div>
    </div>
  )
}

function ProgressBar({ step, total }) {
  const pct = (step / total) * 100
  return (
    <div>
      <div className="flex justify-between text-xs text-slate-500 mb-2">
        <span>Step {step} of {total}</span>
        <span>{Math.round(pct)}%</span>
      </div>
      <div className="h-1.5 bg-slate-700 rounded-full overflow-hidden">
        <div className="h-full bg-indigo-500 transition-all" style={{ width: `${pct}%` }} />
      </div>
    </div>
  )
}

function StepBlock({ heading, subheading, children }) {
  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-slate-100 text-lg font-semibold">{heading}</h2>
        {subheading && <p className="text-slate-400 text-sm mt-1">{subheading}</p>}
      </div>
      {children}
    </div>
  )
}

function RadioList({ options, value, onChange }) {
  return (
    <div className="space-y-2">
      {options.map((opt, i) => {
        const val = i + 1
        const selected = value === val
        return (
          <button
            key={val}
            type="button"
            onClick={() => onChange(val)}
            className={`w-full text-left px-4 py-3 rounded-lg border text-sm transition-colors ${
              selected
                ? 'border-indigo-500 bg-indigo-950/40 text-white'
                : 'border-slate-700 bg-slate-900/40 text-slate-300 hover:border-slate-600 hover:text-white'
            }`}
          >
            <span className={`inline-block w-4 h-4 rounded-full border mr-3 align-middle ${
              selected ? 'border-indigo-400 bg-indigo-500' : 'border-slate-600'
            }`} />
            {opt}
          </button>
        )
      })}
    </div>
  )
}
