import type { Approval, AuditEntry, District, Fault, Incident, RunResult } from './types'

export async function getDistrict(): Promise<District> {
  const res = await fetch('/api/district')
  if (!res.ok) throw new Error(`GET /api/district failed: ${res.status}`)
  return res.json()
}

export async function getApprovals(status?: string): Promise<Approval[]> {
  const q = status ? `?status=${status}` : ''
  const res = await fetch(`/api/approvals${q}`)
  if (!res.ok) throw new Error(`GET /api/approvals failed: ${res.status}`)
  return res.json()
}

export async function decideApproval(
  id: string,
  approver: string,
  decision: 'approved' | 'rejected',
  reason?: string,
): Promise<Approval> {
  const res = await fetch(`/api/approvals/${id}/decide`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ approver, decision, reason }),
  })
  if (!res.ok) throw new Error((await res.json()).detail ?? `decide failed: ${res.status}`)
  return res.json()
}

export async function getIncidents(): Promise<Incident[]> {
  const res = await fetch('/api/incidents')
  if (!res.ok) throw new Error(`GET /api/incidents failed: ${res.status}`)
  return res.json()
}

/**
 * Open an SSE stream for one pipeline run. Calls onAudit for each live step and
 * onResult with the final result, then closes. Returns the EventSource so the
 * caller can close it early.
 */
export function openRunStream(
  fault: Fault,
  onAudit: (e: AuditEntry) => void,
  onResult: (r: RunResult) => void,
  onError: (msg: string) => void,
): EventSource {
  const es = new EventSource(`/api/run/stream?fault=${fault}`)
  es.addEventListener('audit', (ev) => onAudit(JSON.parse((ev as MessageEvent).data)))
  es.addEventListener('result', (ev) => {
    onResult(JSON.parse((ev as MessageEvent).data))
    es.close()
  })
  es.onerror = () => {
    // EventSource fires onerror on normal close too; only surface if not yet closed.
    if (es.readyState !== EventSource.CLOSED) {
      onError('stream error')
      es.close()
    }
  }
  return es
}
