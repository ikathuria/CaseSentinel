import type { Incident } from '../lib/types'
import { agentLabel, FAULT_PLAIN } from '../lib/ui'

const ACTION_PLAIN: Record<string, string> = {
  reroute_to_fallback: 'recovered by rerouting to the Backup Drafter',
  retried_recovered: 'recovered by retrying',
  escalate_to_human: 'escalated to a human',
}

export function IncidentsPanel({ incidents }: { incidents: Incident[] }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white shadow-sm">
      <div className="border-b border-slate-100 px-5 py-4">
        <h2 className="text-sm font-semibold text-slate-800">Failures caught</h2>
        <p className="text-xs text-slate-400">Every agent failure and how the supervisor handled it.</p>
      </div>
      <div className="max-h-[320px] overflow-y-auto px-5 py-4">
        {incidents.length === 0 && (
          <div className="rounded-lg border border-dashed border-slate-200 py-8 text-center text-sm text-slate-400">
            No failures yet. Break an agent to see recovery in action.
          </div>
        )}
        {[...incidents].reverse().map((inc) => (
          <div key={inc.id} className="mb-2 flex gap-3 rounded-lg bg-slate-50/60 p-3">
            <span className="mt-1 h-2 w-2 shrink-0 rounded-full bg-red-500" />
            <div className="min-w-0 text-sm">
              <span className="font-medium text-slate-800">{agentLabel(inc.agent)}</span>{' '}
              <span className="text-slate-600">
                failed — {FAULT_PLAIN[inc.fault_type] ?? inc.fault_type}
              </span>
              <div className="text-xs text-emerald-700">
                → {ACTION_PLAIN[inc.action_taken] ?? inc.action_taken}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
