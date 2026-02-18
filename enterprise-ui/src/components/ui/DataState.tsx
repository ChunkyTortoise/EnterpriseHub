export function DataState({
  loading,
  error,
  empty,
  emptyLabel,
}: {
  loading: boolean
  error: string | null
  empty: boolean
  emptyLabel: string
}) {
  if (loading) {
    return (
      <div className="card">
        <p className="small">Loading live platform data...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="card">
        <p className="status-error">Data retrieval failed</p>
        <p className="small">{error}</p>
      </div>
    )
  }

  if (empty) {
    return (
      <div className="card">
        <p className="status-warn">No data available</p>
        <p className="small">{emptyLabel}</p>
      </div>
    )
  }

  return null
}
