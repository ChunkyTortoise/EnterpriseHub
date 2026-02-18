'use client'

import { useEffect, useState } from 'react'

import { DataState } from '@/components/ui/DataState'
import { MetricCard } from '@/components/ui/MetricCard'
import {
  agentEcosystemAPI,
  type AgentCoordination,
  type AgentMetrics,
  type AgentStatus,
  type PlatformActivity,
} from '@/lib/api/AgentEcosystemAPI'

export default function AgentsPage() {
  const [statuses, setStatuses] = useState<AgentStatus[]>([])
  const [metrics, setMetrics] = useState<AgentMetrics | null>(null)
  const [activities, setActivities] = useState<PlatformActivity[]>([])
  const [coordinations, setCoordinations] = useState<AgentCoordination[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let active = true

    async function load() {
      try {
        const [statusList, metricData, activityList, coordinationList] = await Promise.all([
          agentEcosystemAPI.getAgentStatuses(),
          agentEcosystemAPI.getAgentMetrics(),
          agentEcosystemAPI.getPlatformActivities(10),
          agentEcosystemAPI.getActiveCoordinations(),
        ])

        if (!active) {
          return
        }

        setStatuses(statusList)
        setMetrics(metricData)
        setActivities(activityList)
        setCoordinations(coordinationList)
        setError(null)
      } catch (loadError) {
        if (!active) {
          return
        }

        setError(loadError instanceof Error ? loadError.message : 'Unable to load agent ecosystem')
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
        <h2>Agent Ecosystem</h2>
        <p>Track status, throughput, and handoffs across the operating bot fleet.</p>
      </section>

      {metrics ? (
        <section className="grid-4">
          <MetricCard label="Total Agents" value={`${metrics.totalAgents}`} />
          <MetricCard label="Active Agents" value={`${metrics.activeAgents}`} />
          <MetricCard label="Interactions" value={`${metrics.totalInteractions}`} />
          <MetricCard label="Avg Accuracy" value={`${metrics.avgAccuracy}%`} />
        </section>
      ) : null}

      <DataState
        loading={loading}
        error={error}
        empty={statuses.length === 0}
        emptyLabel="No agents are currently reporting status."
      />

      {statuses.length > 0 ? (
        <section className="grid-2">
          <article className="card">
            <h3>Agent Status</h3>
            <div className="list">
              {statuses.map((item) => (
                <div key={item.id} className="row">
                  <p className="row-title">{item.name}</p>
                  <p className="row-subtitle">{item.category}</p>
                  <p className="small">
                    <span className="tag">{item.status}</span> · {item.responseTime}ms · {item.totalInteractions}{' '}
                    interactions
                  </p>
                </div>
              ))}
            </div>
          </article>

          <article className="card">
            <h3>Recent Activity & Handoffs</h3>
            <div className="list">
              {activities.slice(0, 5).map((activity) => (
                <div key={activity.id} className="row">
                  <p className="row-title">{activity.title}</p>
                  <p className="row-subtitle">{activity.description}</p>
                </div>
              ))}
              {coordinations.slice(0, 3).map((coordination) => (
                <div key={coordination.id} className="row">
                  <p className="row-title">
                    {coordination.fromAgent} → {coordination.toAgent}
                  </p>
                  <p className="row-subtitle">{coordination.handoffType}</p>
                </div>
              ))}
            </div>
          </article>
        </section>
      ) : null}
    </>
  )
}
