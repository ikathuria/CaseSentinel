import type { Incident } from '../lib/types'

export function IncidentsPanel({ incidents }: { incidents: Incident[] }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white shadow-sm">
      <div className="border-b border-slate-200 px-4 py-3">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-500">
          Incident log
        </h2>
        <p className="mt-0.5 text-xs text-slate-400">
          Every detected agent failure and how the supervisor recovered.
        </p>
      </div>
      <div className="max-h-[300px] overflow-y-auto p-3">
        {incidents.length === 0 && (
          <div className="p-2 text-sm text-slate-400">No incidents yet.</div>
        )}
        {[...incidents].reverse().map((inc) => (
          <div key={inc.id} className="mb-2 rounded-lg border border-red-200 bg-red-50/50 p-3">
            <div className="flex items-center justify-between">
              <span className="text-sm font-semibold text-red-800">{inc.fault_type}</span>
              <span className="text-xs text-slate-500">{inc.agent}</span>
            </div>
            <div className="mt-1 text-xs text-slate-600">{inc.detection}</div>
            <div className="mt-1 text-xs">
              <span className="text-slate-400">action: </span>
              <span className="font-medium text-slate-700">{inc.action_taken}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
