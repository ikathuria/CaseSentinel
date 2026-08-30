// Mirrors the JSON served by the CaseSentinel API.

export interface School {
  id: string
  name: string
}

export interface Student {
  id: string
  first_name: string
  last_name: string
  dob: string
  grade: number
  school_id: string
  disability_category: string
  case_manager_id: string
}

export type DriftStatus = 'compliant' | 'due_soon' | 'overdue'

export interface Case {
  student_id: string
  annual_review_due: string
  reevaluation_due: string
  initial_evaluation_due: string | null
  transition_plan_due: string | null
  seeded_status: DriftStatus
}

export interface SourceDocument {
  id: string
  student_id: string
  type: string
  author: string
  date: string
  text: string
}

export interface District {
  name: string
  as_of: string
  schools: School[]
  staff: { id: string; name: string; role: string; school_id: string }[]
  students: Student[]
  cases: Case[]
  documents: SourceDocument[]
}

export interface DriftAlert {
  student_id: string
  student_name: string
  case_manager_id: string
  deadline_type: string
  due_date: string
  days_remaining: number
  status: DriftStatus
  severity: string
}

export interface Posture {
  as_of: string
  totals: Record<DriftStatus, number>
  by_school: Record<string, Record<DriftStatus, number>>
  by_category: Record<string, Record<DriftStatus, number>>
  on_time_rate: number
  at_risk: Record<string, unknown>[]
}

export interface Evidence {
  student_id: string
  student_name: string
  summary: string
  source_doc_ids: string[]
}

export interface Approval {
  id: string
  run_id: string
  student_id: string
  student_name: string
  artifact_type: string
  content: string
  status: 'pending' | 'approved' | 'rejected'
  approver: string | null
  reason: string | null
  created_ts: string
  decided_ts: string | null
}

export interface Incident {
  id: string
  run_id: string
  ts: string
  agent: string
  fault_type: string
  detection: string
  action_taken: string
  detail: Record<string, unknown>
}

export interface AuditEntry {
  run_id: string
  ts: string
  action: string
  agent: string | null
  detail: Record<string, unknown>
  seq: number
}

export interface RunResult {
  run_id: string
  status: 'resolved' | 'needs_human'
  alerts: DriftAlert[]
  evidence: Evidence
  draft: string | null
  approval: Approval | null
  posture: Posture
  served_by: string | null
  action_taken: string | null
  incidents: Incident[]
  audit_trail: AuditEntry[]
}

export type Fault = 'none' | 'loop' | 'hallucination' | 'tool_error' | 'transient_tool_error'
