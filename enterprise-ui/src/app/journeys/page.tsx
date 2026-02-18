'use client'

import { useEffect, useState } from 'react'

import { DataState } from '@/components/ui/DataState'
import { MetricCard } from '@/components/ui/MetricCard'
import { customerJourneyAPI, type CustomerJourney, type JourneyAnalytics } from '@/lib/api/CustomerJourneyAPI'

export default function JourneysPage() {
  const [journeys, setJourneys] = useState<CustomerJourney[]>([])
  const [analytics, setAnalytics] = useState<JourneyAnalytics | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let active = true

    async function load() {
      try {
        const [journeyData, analyticsData] = await Promise.all([
          customerJourneyAPI.getJourneys({ limit: 12 }),
          customerJourneyAPI.getAnalytics(),
        ])

        if (!active) {
          return
        }

        setJourneys(journeyData.journeys)
        setAnalytics(analyticsData)
        setError(null)
      } catch (loadError) {
        if (!active) {
          return
        }

        setError(loadError instanceof Error ? loadError.message : 'Unable to load customer journey data')
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

  return (
    <>
      <section className="card">
        <h2>Customer Journey Analytics</h2>
        <p>Monitor progression from qualification to closing and isolate bottlenecks quickly.</p>
      </section>

      {analytics ? (
        <section className="grid-4">
          <MetricCard label="Total Journeys" value={`${analytics.totalJourneys}`} />
          <MetricCard label="Active" value={`${analytics.activeJourneys}`} />
          <MetricCard label="Completed" value={`${analytics.completedJourneys}`} />
          <MetricCard label="Avg Satisfaction" value={analytics.avgSatisfactionScore.toFixed(1)} />
        </section>
      ) : null}

      <DataState
        loading={loading}
        error={error}
        empty={journeys.length === 0}
        emptyLabel="No customer journeys are currently available."
      />

      {journeys.length > 0 ? (
        <section className="card">
          <h3>Live Journey Queue</h3>
          <div className="list">
            {journeys.map((journey) => (
              <div key={journey.id} className="row">
                <p className="row-title">{journey.customerName}</p>
                <p className="row-subtitle">
                  {journey.type} · {journey.status} · {journey.completionPercentage}% complete
                </p>
              </div>
            ))}
          </div>
        </section>
      ) : null}
    </>
  )
}
