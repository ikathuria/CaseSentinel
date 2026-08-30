// Mirrors the synthetic district JSON served by GET /api/district.

export interface School {
  id: string
  name: string
}

export interface Staff {
  id: string
  name: string
  role: string
  school_id: string
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
  staff: Staff[]
  students: Student[]
  cases: Case[]
  documents: SourceDocument[]
}
