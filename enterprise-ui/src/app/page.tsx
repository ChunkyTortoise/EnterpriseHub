'use client'

import { useEffect, useMemo, useState } from 'react'

import { MetricCard } from '@/components/ui/MetricCard'
import { agentEcosystemAPI, type AgentMetrics } from '@/lib/api/AgentEcosystemAPI'
import { claudeConciergeAPI, type ProactiveSuggestion } from '@/lib/api/ClaudeConciergeAPI'
import { customerJourneyAPI, type JourneyAnalytics } from '@/lib/api/CustomerJourneyAPI'
import { propertyIntelligenceAPI, type PropertyAnalysis } from '@/lib/api/PropertyIntelligenceAPI'

interface OverviewState {
  metrics: AgentMetrics
  analytics: JourneyAnalytics
  suggestions: ProactiveSuggestion[]
  analyses: PropertyAnalysis[]
}

const EMPTY_OVERVIEW: OverviewState = {
  metrics: {
    totalAgents: 0,
    activeAgents: 0,
    totalInteractions: 0,
    avgAccuracy: 0,
    totalHandoffs: 0,
    systemHealth: 0,
  },
  analytics: {
    totalJourneys: 0,
    activeJourneys: 0,
    completedJourneys: 0,
    avgCompletionTime: 0,
    avgSatisfactionScore: 0,
    completionRateByType: {},
    stageAnalysis: {},
    agentPerformance: {},
    bottleneckAnalysis: [],
  },
  suggestions: [],
  analyses: [],
}

export default function OverviewPage() {
  const [data, setData] = useState<OverviewState>(EMPTY_OVERVIEW)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let active = true

    async function load() {
      try {
        setLoading(true)
        const [metrics, analytics, suggestions, analyses] = await Promise.all([
          agentEcosystemAPI.getAgentMetrics(),
          customerJourneyAPI.getAnalytics(),
          claudeConciergeAPI.getProactiveSuggestions(),
          propertyIntelligenceAPI.getAnalyses(),
        ])

        if (!active) {
          return
        }

        setData({
          metrics,
          analytics,
          suggestions,
          analyses,
        })
        setError(null)
      } catch (loadError) {
        if (!active) {
          return
        }

        setError(loadError instanceof Error ? loadError.message : 'Unexpected load error')
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

  const isDemoMode = useMemo(() => Boolean(data.metrics.data_provenance?.demo_mode), [data.metrics])

  return (
    <>
      <section className="card">
        <h2>Executive Overview</h2>
        <p>
          Problem: response-time delays lose qualified leads. Intervention: orchestrated bots enforce SLA and guided
          handoffs. Outcome: measurable lift in conversion and pipeline throughput.
        </p>
        <p className={isDemoMode ? 'status-warn' : 'status-ok'}>
          Data source: {isDemoMode ? 'Demo fallback mode' : 'Live API responses'}
        </p>
        {loading ? <p className="small">Loading operational summary...</p> : null}
        {error ? <p className="status-error">{error}</p> : null}
      </section>

      <section className="grid-4">
        <MetricCard label="Total Agents" value={`${data.metrics.totalAgents}`} />
        <MetricCard label="Active Agents" value={`${data.metrics.activeAgents}`} />
        <MetricCard label="Active Journeys" value={`${data.analytics.activeJourneys}`} />
        <MetricCard label="System Health" value={`${data.metrics.systemHealth}%`} />
      </section>

      <section className="grid-2">
        <article className="card">
          <h3>Top Recommendations</h3>
          <div className="list">
            {data.suggestions.length === 0 ? (
              <p className="small">No proactive suggestions available.</p>
            ) : (
              data.suggestions.slice(0, 4).map((item) => (
                <div key={item.id} className="row">
                  <p className="row-title">{item.title}</p>
                  <p className="row-subtitle">{item.description}</p>
                  <span className="tag">{item.priority}</span>
                </div>
              ))
            )}
          </div>
        </article>

        <article className="card">
          <h3>Property Intelligence Snapshot</h3>
          <div className="list">
            {data.analyses.length === 0 ? (
              <p className="small">No analyses currently available.</p>
            ) : (
              data.analyses.slice(0, 3).map((item) => (
                <div key={item.id} className="row">
                  <p className="row-title">{item.address}</p>
                  <p className="row-subtitle">Status: {item.status}</p>
                </div>
              ))
            )}
          </div>
        </article>
      </section>
    </>
  )
}
