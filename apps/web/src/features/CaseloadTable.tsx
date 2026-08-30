import { useState } from 'react'
import type { District } from '../lib/types'
import { STATUS_LABEL, STATUS_STYLES } from '../lib/ui'

export function CaseloadTable({ district }: { district: District }) {
  const [onlyAtRisk, setOnlyAtRisk] = useState(true)

  const rows = [...district.cases]
    .filter((c) => (onlyAtRisk ? c.seeded_status !== 'compliant' : true))
    .sort((a, b) => a.annual_review_due.localeCompare(b.annual_review_due))

  const nameOf = (id: string) => {
    const s = district.students.find((x) => x.id === id)
    return s ? `${s.first_name} ${s.last_name}` : id
  }
  const catOf = (id: string) => district.students.find((x) => x.id === id)?.disability_category

  return (
    <div>
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-500">
          Caseload — annual review drift
        </h2>
        <label className="flex items-center gap-1.5 text-xs text-slate-500">
          <input
            type="checkbox"
            checked={onlyAtRisk}
            onChange={(e) => setOnlyAtRisk(e.target.checked)}
          />
          at-risk only
        </label>
      </div>
      <div className="max-h-[420px] overflow-auto rounded-xl border border-slate-200 bg-white shadow-sm">
        <table className="min-w-full divide-y divide-slate-200 text-sm">
          <thead className="sticky top-0 bg-slate-50 text-left text-slate-500">
            <tr>
              <th className="px-4 py-3 font-medium">Student</th>
              <th className="px-4 py-3 font-medium">Disability category</th>
              <th className="px-4 py-3 font-medium">Annual review due</th>
              <th className="px-4 py-3 font-medium">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {rows.map((c) => (
              <tr key={c.student_id} className="hover:bg-slate-50">
                <td className="px-4 py-3 font-medium">{nameOf(c.student_id)}</td>
                <td className="px-4 py-3 text-slate-600">{catOf(c.student_id)}</td>
                <td className="px-4 py-3 text-slate-600">{c.annual_review_due}</td>
                <td className="px-4 py-3">
                  <span
                    className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ring-1 ring-inset ${STATUS_STYLES[c.seeded_status]}`}
                  >
                    {STATUS_LABEL[c.seeded_status]}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
