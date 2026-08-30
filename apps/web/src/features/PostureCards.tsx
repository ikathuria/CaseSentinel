function StatCard({ label, value, accent }: { label: string; value: number | string; accent?: string }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="text-sm font-medium text-slate-500">{label}</div>
      <div className={`mt-1 text-3xl font-semibold ${accent ?? 'text-slate-900'}`}>{value}</div>
    </div>
  )
}

export function PostureCards({
  students,
  overdue,
  dueSoon,
  compliant,
  onTimeRate,
}: {
  students: number
  overdue: number
  dueSoon: number
  compliant: number
  onTimeRate?: number
}) {
  return (
    <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
      <StatCard label="Students" value={students} />
      <StatCard label="Overdue" value={overdue} accent="text-red-600" />
      <StatCard label="Due soon" value={dueSoon} accent="text-amber-600" />
      <StatCard
        label={onTimeRate != null ? 'On-time rate' : 'Compliant'}
        value={onTimeRate != null ? `${Math.round(onTimeRate * 100)}%` : compliant}
        accent="text-emerald-600"
      />
    </div>
  )
}
