import type { DriftStatus } from './types'

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

// Audit actions that mark trouble/recovery get emphasis in the trace panel.
export const ACTION_TONE: Record<string, string> = {
  kill: 'text-red-600',
  incident: 'text-red-600',
  reroute: 'text-amber-600',
  retry: 'text-amber-600',
  escalate_to_human: 'text-red-700 font-semibold',
  resolved: 'text-emerald-600',
  approval_requested: 'text-indigo-600',
  approval_decision: 'text-indigo-600',
  pipeline_start: 'text-slate-500',
  pipeline_complete: 'text-slate-500',
}

export const ACTION_ICON: Record<string, string> = {
  pipeline_start: '▶',
  agent_complete: '✓',
  delegate: '→',
  judge: '⚖',
  kill: '✕',
  retry: '↻',
  reroute: '⇄',
  incident: '⚠',
  resolved: '✓',
  approval_requested: '✋',
  approval_decision: '✍',
  escalate_to_human: '🙋',
  pipeline_complete: '■',
}

export function tone(action: string): string {
  return ACTION_TONE[action] ?? 'text-slate-600'
}

export function icon(action: string): string {
  return ACTION_ICON[action] ?? '·'
}
