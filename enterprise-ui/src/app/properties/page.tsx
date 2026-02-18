'use client'

import { useEffect, useState } from 'react'

import { DataState } from '@/components/ui/DataState'
import { MetricCard } from '@/components/ui/MetricCard'
import { propertyIntelligenceAPI, type PropertyAnalysis } from '@/lib/api/PropertyIntelligenceAPI'

export default function PropertiesPage() {
  const [analyses, setAnalyses] = useState<PropertyAnalysis[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let active = true

    async function load() {
      try {
        const analysisData = await propertyIntelligenceAPI.getAnalyses()

        if (!active) {
          return
        }

        setAnalyses(analysisData)
        setError(null)
      } catch (loadError) {
        if (!active) {
          return
        }

        setError(loadError instanceof Error ? loadError.message : 'Unable to load property analyses')
      } finally {
        if (active) {
          setLoading(false)
        }
      }
    }

    void load()

    return () => {
      active = false
    }
  }, [])

  const readyCount = analyses.filter((item) => item.status === 'ready').length

  return (
    <>
      <section className="card">
        <h2>Property Intelligence</h2>
        <p>Review analysis readiness, valuation context, and recommendation quality.</p>
      </section>

      <section className="grid-3">
        <MetricCard label="Analyses" value={`${analyses.length}`} />
        <MetricCard label="Ready" value={`${readyCount}`} />
        <MetricCard label="Processing" value={`${Math.max(analyses.length - readyCount, 0)}`} />
      </section>

      <DataState
        loading={loading}
        error={error}
        empty={analyses.length === 0}
        emptyLabel="No property analysis data is currently available."
      />

      {analyses.length > 0 ? (
        <section className="card">
          <h3>Analysis Queue</h3>
          <div className="list">
            {analyses.map((analysis) => (
              <div key={analysis.id} className="row">
                <p className="row-title">{analysis.address}</p>
                <p className="row-subtitle">Status: {analysis.status}</p>
                {analysis.valuation ? (
                  <p className="small">Valuation: {JSON.stringify(analysis.valuation)}</p>
                ) : null}
              </div>
            ))}
          </div>
        </section>
      ) : null}
    </>
  )
}
