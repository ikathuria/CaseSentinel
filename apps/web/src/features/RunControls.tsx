import type { Fault, RunResult } from '../lib/types'
import { describeOutcome } from '../lib/ui'

const FAULTS: { value: Fault; label: string }[] = [
  { value: 'none', label: "Don't break anything — healthy run" },
  { value: 'hallucination', label: 'Make it hallucinate (wrong student / vague goal)' },
  { value: 'loop', label: 'Make it get stuck in a loop' },
  { value: 'tool_error', label: 'Make a tool fail (keeps failing)' },
  { value: 'transient_tool_error', label: 'Make a tool fail once (recovers on retry)' },
]

function OutcomeCard({ run }: { run: RunResult }) {
  const o = describeOutcome(run)
  const ok = o.tone === 'ok'
  return (
    <div
      className={`mt-4 rounded-lg border-l-4 p-4 ${
        ok ? 'border-emerald-500 bg-emerald-50/60' : 'border-red-500 bg-red-50/60'
      }`}
    >
      <div className="flex items-start gap-3">
        <span
          className={`mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-sm font-bold text-white ${
            ok ? 'bg-emerald-500' : 'bg-red-500'
          }`}
        >
          {ok ? '✓' : '!'}
        </span>
        <div className="min-w-0">
          <div className={`text-sm font-semibold ${ok ? 'text-emerald-900' : 'text-red-900'}`}>
            {o.headline}
          </div>
          <p className="mt-1 text-sm text-slate-600">{o.detail}</p>
          {run.incidents.length > 0 && (
            <p className="mt-1.5 text-xs text-slate-400">
              {run.incidents.length} incident{run.incidents.length > 1 ? 's' : ''} written to the audit log · run {run.run_id.slice(0, 8)}
            </p>
          )}
        </div>
      </div>
    </div>
  )
}

export function RunControls({
  fault,
  setFault,
  running,
  onRun,
  run,
}: {
  fault: Fault
  setFault: (f: Fault) => void
  running: boolean
  onRun: () => void
  run: RunResult | null
}) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex flex-wrap items-end gap-3">
        <div className="flex-1 min-w-[280px]">
          <label className="mb-1 block text-sm font-medium text-slate-700">
            Run a compliance sweep
          </label>
          <p className="mb-2 text-xs text-slate-400">
            Optionally break the Document Drafter to see the supervisor detect and recover from it.
          </p>
          <select
            value={fault}
            onChange={(e) => setFault(e.target.value as Fault)}
            disabled={running}
            className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:outline-none"
          >
            {FAULTS.map((f) => (
              <option key={f.value} value={f.value}>
                {f.label}
              </option>
            ))}
          </select>
        </div>
        <button
          onClick={onRun}
          disabled={running}
          className="rounded-lg bg-indigo-600 px-5 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 disabled:opacity-50"
        >
          {running ? 'Running…' : 'Run compliance sweep'}
        </button>
      </div>

      {run && <OutcomeCard run={run} />}
    </div>
  )
}
