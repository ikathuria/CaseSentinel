import { useEffect, useMemo, useState } from 'react'
import { getDistrict } from './lib/api'
import type { District, DriftStatus } from './lib/types'

const STATUS_STYLES: Record<DriftStatus, string> = {
  overdue: 'bg-red-100 text-red-800 ring-red-600/20',
  due_soon: 'bg-amber-100 text-amber-800 ring-amber-600/20',
  compliant: 'bg-emerald-100 text-emerald-800 ring-emerald-600/20',
}

const STATUS_LABEL: Record<DriftStatus, string> = {
  overdue: 'Overdue',
  due_soon: 'Due soon',
  compliant: 'Compliant',
}

function StatCard({ label, value, accent }: { label: string; value: number | string; accent?: string }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="text-sm font-medium text-slate-500">{label}</div>
      <div className={`mt-1 text-3xl font-semibold ${accent ?? 'text-slate-900'}`}>{value}</div>
    </div>
  )
}

export default function App() {
  const [district, setDistrict] = useState<District | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    getDistrict().then(setDistrict).catch((e) => setError(String(e)))
  }, [])

  const counts = useMemo(() => {
    if (!district) return null
    const tally = (s: DriftStatus) => district.cases.filter((c) => c.seeded_status === s).length
    return {
      overdue: tally('overdue'),
      due_soon: tally('due_soon'),
      compliant: tally('compliant'),
    }
  }, [district])

  const nameOf = (id: string) => {
    const s = district?.students.find((x) => x.id === id)
    return s ? `${s.first_name} ${s.last_name}` : id
  }

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto max-w-6xl px-6 py-5">
          <h1 className="text-xl font-semibold tracking-tight">
            Case<span className="text-indigo-600">Sentinel</span>
          </h1>
          <p className="text-sm text-slate-500">
            District-wide IDEA compliance, watched continuously.
          </p>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-6 py-8">
        {error && (
          <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
            {error}
            <div className="mt-1 text-red-500">
              Is the API running? <code>npm run dev:api</code> (port 8000).
            </div>
          </div>
        )}

        {!district && !error && <div className="text-slate-500">Loading district…</div>}

        {district && counts && (
          <>
            <div className="mb-1 text-sm text-slate-500">
              {district.name} · as of {district.as_of}
            </div>
            <div className="mb-8 grid grid-cols-2 gap-4 sm:grid-cols-4">
              <StatCard label="Students" value={district.students.length} />
              <StatCard label="Overdue" value={counts.overdue} accent="text-red-600" />
              <StatCard label="Due soon" value={counts.due_soon} accent="text-amber-600" />
              <StatCard label="Compliant" value={counts.compliant} accent="text-emerald-600" />
            </div>

            <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-500">
              Caseload — annual review drift
            </h2>
            <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white shadow-sm">
              <table className="min-w-full divide-y divide-slate-200 text-sm">
                <thead className="bg-slate-50 text-left text-slate-500">
                  <tr>
                    <th className="px-4 py-3 font-medium">Student</th>
                    <th className="px-4 py-3 font-medium">Disability category</th>
                    <th className="px-4 py-3 font-medium">Annual review due</th>
                    <th className="px-4 py-3 font-medium">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {[...district.cases]
                    .sort((a, b) => a.annual_review_due.localeCompare(b.annual_review_due))
                    .map((c) => {
                      const student = district.students.find((s) => s.id === c.student_id)
                      return (
                        <tr key={c.student_id} className="hover:bg-slate-50">
                          <td className="px-4 py-3 font-medium">{nameOf(c.student_id)}</td>
                          <td className="px-4 py-3 text-slate-600">
                            {student?.disability_category}
                          </td>
                          <td className="px-4 py-3 text-slate-600">{c.annual_review_due}</td>
                          <td className="px-4 py-3">
                            <span
                              className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ring-1 ring-inset ${STATUS_STYLES[c.seeded_status]}`}
                            >
                              {STATUS_LABEL[c.seeded_status]}
                            </span>
                          </td>
                        </tr>
                      )
                    })}
                </tbody>
              </table>
            </div>
            <p className="mt-6 text-xs text-slate-400">
              Synthetic data only — no real student records. M1 shell; live agent
              runs, approval gates, and the failure-recovery demo arrive in M2–M4.
            </p>
          </>
        )}
      </main>
    </div>
  )
}
