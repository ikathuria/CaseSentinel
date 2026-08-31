import type { AuditEntry, DriftStatus, RunResult } from './types'

export const STATUS_STYLES: Record<DriftStatus, string> = {
  overdue: 'bg-red-100 text-red-800 ring-red-600/20',
  due_soon: 'bg-amber-100 text-amber-800 ring-amber-600/20',
  compliant: 'bg-emerald-100 text-emerald-800 ring-emerald-600/20',
}

export const STATUS_LABEL: Record<DriftStatus, string> = {
  overdue: 'Overdue',
  due_soon: 'Due soon',
  compliant: 'Compliant',
}

// Friendly, human-readable agent names (no snake_case in the UI).
export const AGENT_LABEL: Record<string, string> = {
  supervisor: 'Supervisor',
  timekeeper: 'Timekeeper',
  evidence_ingestor: 'Evidence Ingestor',
  document_drafter: 'Document Drafter',
  backup_drafter: 'Backup Drafter',
  compliance_reporter: 'Compliance Reporter',
  approval_gate: 'Approval Gate',
}

// Plain-English descriptions of each fault.
export const FAULT_PLAIN: Record<string, string> = {
  tool_error: 'a tool timed out',
  loop: 'it got stuck in a loop',
  hallucination: 'it drafted the wrong content',
  model_error: 'the model errored',
}

export function agentLabel(id: string | null): string {
  if (!id) return 'Supervisor'
  return AGENT_LABEL[id] ?? id
}

type Tone = 'ok' | 'warn' | 'bad' | 'muted'

export interface StepView {
  tone: Tone
  agent: string
  title: string
  detail?: string
}

/** Turn a raw audit entry into a friendly, plain-language timeline step.
 *  Returns null for steps we hide to keep the story clean. */
export function stepView(e: AuditEntry): StepView | null {
  const d = (e.detail || {}) as Record<string, unknown>
  const agent = agentLabel(e.agent)
  switch (e.action) {
    case 'pipeline_start': {
      const f = d.inject_fault as string
      return {
        tone: 'muted',
        agent: 'Supervisor',
        title: 'Compliance sweep started',
        detail: f && f !== 'none' ? `fault injected into the Document Drafter: ${f}` : undefined,
      }
    }
    case 'agent_complete':
      if (e.agent === 'timekeeper')
        return { tone: 'ok', agent, title: 'Scanned every caseload', detail: `${d.alerts} drift alerts · ${d.overdue} overdue` }
      if (e.agent === 'evidence_ingestor')
        return { tone: 'ok', agent, title: `Normalized the source notes for ${d.student}` }
      if (e.agent === 'compliance_reporter')
        return { tone: 'ok', agent, title: 'Rolled up district posture', detail: `${Math.round(Number(d.on_time_rate) * 100)}% on time · ${d.overdue} overdue` }
      return { tone: 'ok', agent, title: 'Done' }
    case 'delegate':
      return { tone: 'muted', agent: 'Supervisor', title: 'Asked the Document Drafter to write the goal' }
    case 'judge':
      // Only show the positive "passed review"; a rejection is covered by the
      // following "kill" step, so we hide it here to avoid a duplicate.
      return d.ok ? { tone: 'ok', agent, title: 'Draft passed review' } : null
    case 'kill': {
      const plain = FAULT_PLAIN[String(d.fault)] ?? String(d.fault)
      return { tone: 'bad', agent, title: `Draft failed — ${plain}`, detail: String(d.detection ?? '') }
    }
    case 'retry':
      return { tone: 'warn', agent, title: 'Retried the same agent once' }
    case 'reroute':
      return { tone: 'warn', agent: 'Supervisor', title: `Handed the task to the ${agent}` }
    case 'incident':
      return null // shown in the outcome summary + Incident log; hidden here to reduce noise
    case 'resolved':
      return { tone: 'ok', agent: agentLabel(String(d.served_by ?? '')), title: 'Goal ready for approval' }
    case 'approval_requested':
      return { tone: 'muted', agent: 'Approval Gate', title: 'Sent to a human for sign-off' }
    case 'escalate_to_human':
      return { tone: 'bad', agent: 'Supervisor', title: 'Escalated for manual review' }
    case 'pipeline_complete':
      return null
    default:
      return { tone: 'muted', agent, title: e.action }
  }
}

export const TONE_DOT: Record<Tone, string> = {
  ok: 'bg-emerald-500',
  warn: 'bg-amber-500',
  bad: 'bg-red-500',
  muted: 'bg-slate-300',
}

export const TONE_TEXT: Record<Tone, string> = {
  ok: 'text-slate-700',
  warn: 'text-amber-700',
  bad: 'text-red-700',
  muted: 'text-slate-500',
}

export interface Outcome {
  tone: 'ok' | 'bad'
  headline: string
  detail: string
}

/** A plain-English summary of what the whole run did. */
export function describeOutcome(run: RunResult): Outcome {
  const student = run.evidence?.student_name ?? 'the student'
  const fault = run.incidents[0]?.fault_type
  const plain = fault ? FAULT_PLAIN[fault] ?? fault : ''
  switch (run.action_taken) {
    case null:
    case undefined:
      return {
        tone: 'ok',
        headline: 'Sweep complete — no problems',
        detail: `All four agents ran cleanly. A measurable goal for ${student} is ready for your approval.`,
      }
    case 'retried_recovered':
      return {
        tone: 'ok',
        headline: 'Recovered automatically',
        detail: `The Document Drafter failed (${plain}). The supervisor retried it and it recovered on its own — no backup needed. Goal for ${student} is ready for approval.`,
      }
    case 'reroute_to_fallback':
      return {
        tone: 'ok',
        headline: 'Caught the failure and recovered',
        detail: `The Document Drafter failed (${plain}). The supervisor stopped it, logged an incident, and handed the task to the Backup Drafter — which produced a valid goal for ${student}, now awaiting your approval.`,
      }
    case 'escalate_to_human':
      return {
        tone: 'bad',
        headline: 'Flagged for manual review',
        detail: `Both the Document Drafter and the Backup Drafter failed. Nothing was auto-accepted — this case needs a human to handle it directly.`,
      }
    default:
      return { tone: 'ok', headline: 'Sweep complete', detail: '' }
  }
}
