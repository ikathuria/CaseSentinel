import { useCallback, useEffect, useMemo, useState } from 'react'
import { decideApproval, getApprovals, getDistrict, getIncidents, openRunStream } from './lib/api'
import type { Approval, AuditEntry, District, DriftStatus, Fault, Incident, RunResult } from './lib/types'
import { ApprovalsPanel } from './features/ApprovalsPanel'
import { CaseloadTable } from './features/CaseloadTable'
import { IncidentsPanel } from './features/AuditIncidents'
import { PostureCards } from './features/PostureCards'
import { RunControls } from './features/RunControls'
import { TracePanel } from './features/TracePanel'

export default function App() {
  const [district, setDistrict] = useState<District | null>(null)
  const [error, setError] = useState<string | null>(null)

  const [fault, setFault] = useState<Fault>('hallucination')
  const [running, setRunning] = useState(false)
  const [trace, setTrace] = useState<AuditEntry[]>([])
  const [run, setRun] = useState<RunResult | null>(null)
  const [approvals, setApprovals] = useState<Approval[]>([])
  const [incidents, setIncidents] = useState<Incident[]>([])

  useEffect(() => {
    getDistrict().then(setDistrict).catch((e) => setError(String(e)))
    getApprovals().then(setApprovals).catch(() => {})
    getIncidents().then(setIncidents).catch(() => {})
  }, [])

  const refresh = useCallback(() => {
    getApprovals().then(setApprovals).catch(() => {})
    getIncidents().then(setIncidents).catch(() => {})
  }, [])

  const onRun = useCallback(() => {
    setTrace([])
    setRun(null)
    setRunning(true)
    openRunStream(
      fault,
      (e) => setTrace((prev) => [...prev, e]),
      (r) => {
        setRun(r)
        setRunning(false)
        refresh()
      },
      (msg) => {
        setError(msg)
        setRunning(false)
      },
    )
  }, [fault, refresh])

  const onDecide = useCallback(
    (id: string, decision: 'approved' | 'rejected', approver: string) => {
      decideApproval(id, approver, decision)
        .then(refresh)
        .catch((e) => setError(String(e)))
    },
    [refresh],
  )

  const counts = useMemo(() => {
    if (!district) return null
    const tally = (s: DriftStatus) => district.cases.filter((c) => c.seeded_status === s).length
    return { overdue: tally('overdue'), due_soon: tally('due_soon'), compliant: tally('compliant') }
  }, [district])

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto max-w-7xl px-6 py-5">
          <h1 className="text-xl font-semibold tracking-tight">
            Case<span className="text-indigo-600">Sentinel</span>
          </h1>
          <p className="text-sm text-slate-500">District-wide IDEA compliance, watched continuously.</p>
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-6 py-8">
        {error && (
          <div className="mb-6 rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
            {error}
            <div className="mt-1 text-red-500">
              Is the API running? <code>npm run dev:api</code> (port 8000).
            </div>
          </div>
        )}

        {!district && !error && <div className="text-slate-500">Loading district…</div>}

        {district && counts && (
          <div className="space-y-6">
            <div className="text-sm text-slate-500">
              {district.name} · as of {district.as_of}
            </div>

            <PostureCards
              students={district.students.length}
              overdue={run?.posture.totals.overdue ?? counts.overdue}
              dueSoon={run?.posture.totals.due_soon ?? counts.due_soon}
              compliant={counts.compliant}
              onTimeRate={run?.posture.on_time_rate}
            />

            <RunControls fault={fault} setFault={setFault} running={running} onRun={onRun} run={run} />

            <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
              <TracePanel trace={trace} running={running} />
              <ApprovalsPanel approvals={approvals} onDecide={onDecide} />
            </div>

            <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
              <CaseloadTable district={district} />
              <IncidentsPanel incidents={incidents} />
            </div>

            <p className="text-xs text-slate-400">
              Synthetic data only — no real student records. Gemini 3.5 via Google ADK 2.8;
              offline scripted models when no API key is set.
            </p>
          </div>
        )}
      </main>
    </div>
  )
}
