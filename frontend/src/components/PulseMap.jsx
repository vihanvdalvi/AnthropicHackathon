import { ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ZAxis } from 'recharts'
import { useNavigate } from 'react-router-dom'

const CustomDot = (props) => {
  const { cx, cy, payload, navigate } = props
  const size = 20 + (payload.intensity_avg / 10) * 40
  const sentiment = payload.sentiment_avg || 0
  const r = Math.round(sentiment < 0 ? 239 : 100)
  const g = Math.round(sentiment < 0 ? 68 : 200)
  const b = Math.round(sentiment < 0 ? 68 : 100)
  return (
    <g
      style={{ cursor: 'pointer' }}
      onClick={() => navigate(`/issue/${payload.id}`)}
    >
      <circle cx={cx} cy={cy} r={size / 2} fill={`rgba(${r},${g},${b},0.25)`} stroke={`rgb(${r},${g},${b})`} strokeWidth={1.5} />
      <text x={cx} y={cy + 4} textAnchor="middle" fontSize={10} fill="#cbd5e1">
        {payload.label?.split(' ')[0]}
      </text>
    </g>
  )
}

const CustomTooltip = ({ active, payload }) => {
  if (!active || !payload?.length) return null
  const d = payload[0]?.payload
  return (
    <div className="bg-slate-900 border border-slate-600 rounded-lg p-3 text-sm shadow-xl">
      <p className="text-white font-medium">{d.label}</p>
      <p className="text-slate-400 mt-1">Intensity: <span className="text-indigo-300">{d.intensity_avg?.toFixed(1)}/10</span></p>
      <p className="text-slate-400">Sentiment: <span className={d.sentiment_avg >= 0 ? 'text-emerald-400' : 'text-rose-400'}>{d.sentiment_avg?.toFixed(2)}</span></p>
      <p className="text-slate-400">{d.post_count} voices</p>
    </div>
  )
}

export default function PulseMap({ issues }) {
  const navigate = useNavigate()

  const data = issues.map(issue => ({
    ...issue,
    x: issue.sentiment_avg ?? 0,
    y: issue.intensity_avg ?? 5,
    z: issue.post_count ?? 1,
  }))

  return (
    <div className="bg-slate-800 border border-slate-700 rounded-xl p-5">
      <h2 className="text-slate-200 font-semibold mb-4">Campus Pulse Map</h2>
      <p className="text-slate-400 text-sm mb-4">
        Bubble size = post volume · X axis = sentiment · Y axis = intensity · Click to explore
      </p>
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <ScatterChart margin={{ top: 10, right: 20, bottom: 10, left: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
            <XAxis
              dataKey="x"
              type="number"
              domain={[-1, 1]}
              tickFormatter={v => v === 0 ? 'neutral' : v > 0 ? 'positive' : 'negative'}
              tick={{ fill: '#94a3b8', fontSize: 11 }}
              label={{ value: 'Sentiment', position: 'insideBottom', offset: -4, fill: '#64748b', fontSize: 12 }}
            />
            <YAxis
              dataKey="y"
              type="number"
              domain={[0, 10]}
              tick={{ fill: '#94a3b8', fontSize: 11 }}
              label={{ value: 'Intensity', angle: -90, position: 'insideLeft', fill: '#64748b', fontSize: 12 }}
            />
            <ZAxis dataKey="z" range={[40, 400]} />
            <Tooltip content={<CustomTooltip />} />
            <Scatter
              data={data}
              shape={(props) => <CustomDot {...props} navigate={navigate} />}
            />
          </ScatterChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
