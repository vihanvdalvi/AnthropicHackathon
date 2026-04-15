export default function StatementSliders({ statements, values, onChange }) {
  return (
    <div className="space-y-5">
      {statements.map((stmt, i) => (
        <div key={i}>
          <div className="flex justify-between items-start gap-3 mb-2">
            <label htmlFor={`stmt-${i}`} className="text-slate-200 text-sm leading-snug">
              {stmt}
            </label>
            <span className="shrink-0 text-indigo-400 font-semibold text-sm tabular-nums">
              {values[i]}/10
            </span>
          </div>
          <input
            id={`stmt-${i}`}
            type="range"
            min={1}
            max={10}
            step={1}
            value={values[i]}
            onChange={(e) => onChange(i, Number(e.target.value))}
            className="w-full accent-indigo-500"
          />
          <div className="flex justify-between text-[10px] text-slate-500 mt-1">
            <span>Disagree</span>
            <span>Agree</span>
          </div>
        </div>
      ))}
    </div>
  )
}
