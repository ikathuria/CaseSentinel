import type { Fault, RunResult } from '../lib/types'

const FAULTS: { value: Fault; label: string }[] = [
  { value: 'none', label: 'No fault (healthy run)' },
  { value: 'hallucination', label: 'Hallucination (wrong student / non-measurable)' },
  { value: 'loop', label: 'Runaway loop' },
  { value: 'tool_error', label: 'Tool error (persistent)' },
  { value: 'transient_tool_error', label: 'Tool error (transient — recovers on retry)' },
]

const ACTION_LABEL: Record<string, string> = {
  retried_recovered: 'retried & recovered',
  reroute_to_fallback: 'rerouted to fallback',
  escalate_to_human: 'escalated to human',
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
        <div className="flex-1 min-w-[260px]">
          <label className="mb-1 block text-xs font-medium uppercase tracking-wide text-slate-500">
            Break an agent (inject a fault into the Document Drafter)
          </label>
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
          className="rounded-lg bg-indigo-600 px-5 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 disabled:opacity-50"
        >
          {running ? 'Running…' : 'Run compliance sweep'}
        </button>
      </div>

      {run && (
        <div className="mt-4 flex flex-wrap items-center gap-2 text-sm">
          <span
            className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-semibold ring-1 ring-inset ${
              run.status === 'resolved'
                ? 'bg-emerald-100 text-emerald-800 ring-emerald-600/20'
                : 'bg-red-100 text-red-800 ring-red-600/20'
            }`}
          >
            {run.status === 'resolved' ? 'Resolved' : 'Needs human'}
          </span>
          {run.action_taken && (
            <span className="text-slate-500">
              recovery: <strong className="text-slate-700">{ACTION_LABEL[run.action_taken] ?? run.action_taken}</strong>
            </span>
          )}
          {run.served_by && (
            <span className="text-slate-500">
              served by <strong className="text-slate-700">{run.served_by}</strong>
            </span>
          )}
          {run.incidents.length > 0 && (
            <span className="text-red-600">
              {run.incidents.length} incident{run.incidents.length > 1 ? 's' : ''} logged
            </span>
          )}
          <span className="text-slate-400">run {run.run_id.slice(0, 8)}</span>
        </div>
      )}
    </div>
  )
}
