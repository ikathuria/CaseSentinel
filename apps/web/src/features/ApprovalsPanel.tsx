import { useState } from 'react'
import type { Approval } from '../lib/types'

export function ApprovalsPanel({
  approvals,
  onDecide,
}: {
  approvals: Approval[]
  onDecide: (id: string, decision: 'approved' | 'rejected', approver: string) => void
}) {
  const [approver, setApprover] = useState('Dr. Alvarez (SpEd Director)')

  // Show one active draft per student (the most recent), so repeated runs
  // don't pile up duplicate pending cards.
  const latestPerStudent = new Map<string, Approval>()
  for (const a of approvals) {
    if (a.status !== 'pending') continue
    const prev = latestPerStudent.get(a.student_id)
    if (!prev || a.created_ts > prev.created_ts) latestPerStudent.set(a.student_id, a)
  }
  const pending = [...latestPerStudent.values()].sort((a, b) => b.created_ts.localeCompare(a.created_ts))
  const decided = approvals.filter((a) => a.status !== 'pending')

  return (
    <div className="rounded-xl border border-slate-200 bg-white shadow-sm">
      <div className="border-b border-slate-100 px-5 py-4">
        <h2 className="text-sm font-semibold text-slate-800">Your approvals</h2>
        <p className="text-xs text-slate-400">
          The AI only drafts. Nothing is final until you sign off.
        </p>
      </div>

      <div className="px-5 py-4">
        <label className="mb-1 block text-xs font-medium text-slate-500">Signing as</label>
        <input
          value={approver}
          onChange={(e) => setApprover(e.target.value)}
          className="mb-4 w-full rounded-lg border border-slate-300 px-3 py-1.5 text-sm focus:border-indigo-500 focus:outline-none"
        />

        {pending.length === 0 && (
          <div className="rounded-lg border border-dashed border-slate-200 py-8 text-center text-sm text-slate-400">
            No drafts waiting. Run a sweep to generate one.
          </div>
        )}

        {pending.map((a) => (
          <div key={a.id} className="mb-3 rounded-lg border border-slate-200 bg-slate-50/50 p-4">
            <div className="mb-2 flex items-center justify-between">
              <span className="text-sm font-semibold text-slate-800">{a.student_name}</span>
              <span className="rounded-full bg-amber-100 px-2 py-0.5 text-xs font-medium text-amber-800">
                needs your sign-off
              </span>
            </div>
            <div className="mb-2 text-xs uppercase tracking-wide text-slate-400">Proposed IEP reading goal</div>
            <p className="mb-3 rounded-md bg-white p-3 text-sm leading-relaxed text-slate-700 ring-1 ring-slate-100">
              {a.content}
            </p>
            <div className="flex gap-2">
              <button
                onClick={() => onDecide(a.id, 'approved', approver)}
                className="rounded-lg bg-emerald-600 px-4 py-1.5 text-sm font-semibold text-white hover:bg-emerald-500"
              >
                Approve
              </button>
              <button
                onClick={() => onDecide(a.id, 'rejected', approver)}
                className="rounded-lg bg-white px-4 py-1.5 text-sm font-semibold text-slate-600 ring-1 ring-inset ring-slate-300 hover:bg-slate-50"
              >
                Reject
              </button>
            </div>
          </div>
        ))}

        {decided.length > 0 && (
          <div className="mt-4 border-t border-slate-100 pt-3">
            <div className="mb-2 text-xs font-medium uppercase tracking-wide text-slate-400">
              Recently decided
            </div>
            {decided.slice(-4).reverse().map((a) => (
              <div key={a.id} className="flex items-center justify-between py-1 text-sm">
                <span className="text-slate-600">{a.student_name}</span>
                <span className={a.status === 'approved' ? 'text-emerald-600' : 'text-slate-500'}>
                  {a.status === 'approved' ? '✓ approved' : '✕ rejected'} · {a.approver}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
