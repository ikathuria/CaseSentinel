import { useEffect, useRef } from 'react'
import type { AuditEntry } from '../lib/types'
import { stepView, TONE_DOT, TONE_TEXT } from '../lib/ui'

export function TracePanel({ trace, running }: { trace: AuditEntry[]; running: boolean }) {
  const endRef = useRef<HTMLDivElement>(null)
  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [trace.length])

  const steps = trace.map((e) => stepView(e)).filter((s) => s !== null)

  return (
    <div className="rounded-xl border border-slate-200 bg-white shadow-sm">
      <div className="flex items-center justify-between border-b border-slate-100 px-5 py-4">
        <div>
          <h2 className="text-sm font-semibold text-slate-800">What the agents are doing</h2>
          <p className="text-xs text-slate-400">Live, step by step</p>
        </div>
        {running && (
          <span className="flex items-center gap-1.5 rounded-full bg-indigo-50 px-2.5 py-1 text-xs font-medium text-indigo-600">
            <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-indigo-500" /> running
          </span>
        )}
      </div>

      <div className="max-h-[440px] overflow-y-auto px-5 py-4">
        {steps.length === 0 && (
          <div className="py-10 text-center text-sm text-slate-400">
            Click <span className="font-medium text-slate-500">Run compliance sweep</span> to watch
            the agents work — and to see the supervisor catch and recover from any failure.
          </div>
        )}

        <ol className="relative">
          {steps.map((s, i) => (
            <li key={i} className="relative flex gap-3 pb-4 last:pb-0">
              {/* connector line */}
              {i < steps.length - 1 && (
                <span className="absolute left-[7px] top-4 h-full w-px bg-slate-200" aria-hidden />
              )}
              <span className={`relative mt-1 h-3.5 w-3.5 shrink-0 rounded-full ring-4 ring-white ${TONE_DOT[s.tone]}`} />
              <div className="min-w-0 flex-1">
                <div className="flex items-baseline gap-2">
                  <span className="text-[11px] font-medium uppercase tracking-wide text-slate-400">
                    {s.agent}
                  </span>
                </div>
                <div className={`text-sm ${TONE_TEXT[s.tone]}`}>{s.title}</div>
                {s.detail && <div className="mt-0.5 text-xs text-slate-400">{s.detail}</div>}
              </div>
            </li>
          ))}
        </ol>
        <div ref={endRef} />
      </div>
    </div>
  )
}
