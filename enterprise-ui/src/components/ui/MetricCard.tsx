export function MetricCard({
  label,
  value,
  hint,
}: {
  label: string
  value: string
  hint?: string
}) {
  return (
    <article className="card">
      <p className="small">{label}</p>
      <div className="metric-value">{value}</div>
      {hint ? <p className="small">{hint}</p> : null}
    </article>
  )
}
