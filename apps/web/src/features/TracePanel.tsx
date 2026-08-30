import { useEffect, useRef } from 'react'
import type { AuditEntry } from '../lib/types'
import { icon, tone } from '../lib/ui'

function summarize(e: AuditEntry): string {
  const d = e.detail || {}
  switch (e.action) {
    case 'pipeline_start':
      return `district sweep started${d.inject_fault && d.inject_fault !== 'none' ? ` (fault injected: ${d.inject_fault})` : ''}`
    case 'agent_complete':
      return e.agent === 'timekeeper'
        ? `scanned caseloads — ${d.alerts} drift alerts (${d.overdue} overdue)`
        : e.agent === 'evidence_ingestor'
          ? `normalized ${d.docs} source doc(s) for ${d.student}`
          : e.agent === 'compliance_reporter'
            ? `district posture — on-time ${Math.round(Number(d.on_time_rate) * 100)}%, ${d.overdue} overdue`
            : 'done'
    case 'delegate':
      return `delegated draft to ${e.agent}`
    case 'judge':
      return d.ok ? 'output passed validation' : `output REJECTED: ${d.detection}`
    case 'kill':
      return `killed ${e.agent} — ${d.fault}${d.detection ? `: ${d.detection}` : ''}`
    case 'retry':
      return `retrying ${e.agent} (attempt ${d.attempt})`
    case 'reroute':
      return `rerouted from ${d.from} to ${e.agent}`
    case 'incident':
      return `incident logged: ${d.fault_type} → ${d.action_taken}`
    case 'resolved':
      return `resolved — served by ${d.served_by}`
    case 'approval_requested':
      return `approval requested for ${d.student} (${d.artifact_type})`
    case 'approval_decision':
      return `${d.decision} by ${d.approver}`
    case 'escalate_to_human':
      return 'escalated to a human — no draft accepted'
    case 'pipeline_complete':
      return `sweep complete (${d.status})`
    default:
      return e.action
  }
}

export function TracePanel({ trace, running }: { trace: AuditEntry[]; running: boolean }) {
  const endRef = useRef<HTMLDivElement>(null)
  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [trace.length])

  return (
    <div className="rounded-xl border border-slate-200 bg-white shadow-sm">
      <div className="flex items-center justify-between border-b border-slate-200 px-4 py-3">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-500">
          Live agent trace
        </h2>
        {running && (
          <span className="flex items-center gap-1.5 text-xs text-indigo-600">
            <span className="h-2 w-2 animate-pulse rounded-full bg-indigo-500" /> streaming
          </span>
        )}
      </div>
      <div className="max-h-[420px] overflow-y-auto p-3 font-mono text-xs">
        {trace.length === 0 && (
          <div className="p-4 text-slate-400">
            Run a compliance sweep to watch the supervisor delegate, monitor, and
            recover — live.
          </div>
        )}
        {trace.map((e, i) => (
          <div key={i} className="flex gap-2 px-1 py-1">
            <span className={`w-4 shrink-0 text-center ${tone(e.action)}`}>{icon(e.action)}</span>
            <span className="w-40 shrink-0 text-slate-400">
              {e.agent ?? 'supervisor'}
            </span>
            <span className={tone(e.action)}>{summarize(e)}</span>
          </div>
        ))}
        <div ref={endRef} />
      </div>
    </div>
  )
}
