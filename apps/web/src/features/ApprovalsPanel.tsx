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
  const pending = approvals.filter((a) => a.status === 'pending')
  const decided = approvals.filter((a) => a.status !== 'pending')

  return (
    <div className="rounded-xl border border-slate-200 bg-white shadow-sm">
      <div className="border-b border-slate-200 px-4 py-3">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-500">
          Approval gate
        </h2>
        <p className="mt-0.5 text-xs text-slate-400">
          No agent takes a binding action — a named human signs off on every draft.
        </p>
      </div>

      <div className="p-4">
        <label className="mb-1 block text-xs font-medium text-slate-500">Approver</label>
        <input
          value={approver}
          onChange={(e) => setApprover(e.target.value)}
          className="mb-4 w-full rounded-lg border border-slate-300 px-3 py-1.5 text-sm focus:border-indigo-500 focus:outline-none"
        />

        {pending.length === 0 && (
          <div className="text-sm text-slate-400">No drafts awaiting approval.</div>
        )}

        {pending.map((a) => (
          <div key={a.id} className="mb-3 rounded-lg border border-amber-200 bg-amber-50/50 p-3">
            <div className="mb-1 flex items-center justify-between">
              <span className="text-sm font-semibold text-slate-800">{a.student_name}</span>
              <span className="rounded-full bg-amber-100 px-2 py-0.5 text-xs font-medium text-amber-800">
                pending
              </span>
            </div>
            <div className="mb-1 text-xs text-slate-400">{a.artifact_type}</div>
            <p className="mb-3 text-sm text-slate-700">{a.content}</p>
            <div className="flex gap-2">
              <button
                onClick={() => onDecide(a.id, 'approved', approver)}
                className="rounded-lg bg-emerald-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-emerald-500"
              >
                Approve
              </button>
              <button
                onClick={() => onDecide(a.id, 'rejected', approver)}
                className="rounded-lg bg-white px-3 py-1.5 text-xs font-semibold text-red-700 ring-1 ring-inset ring-red-300 hover:bg-red-50"
              >
                Reject
              </button>
            </div>
          </div>
        ))}

        {decided.length > 0 && (
          <div className="mt-4 border-t border-slate-100 pt-3">
            <div className="mb-2 text-xs font-medium uppercase tracking-wide text-slate-400">
              Decided
            </div>
            {decided.slice(-5).reverse().map((a) => (
              <div key={a.id} className="flex items-center justify-between py-1 text-xs">
                <span className="text-slate-600">{a.student_name}</span>
                <span
                  className={
                    a.status === 'approved' ? 'text-emerald-600' : 'text-red-600'
                  }
                >
                  {a.status} · {a.approver}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
