'use client'

import { FormEvent, useEffect, useState } from 'react'

import { DataState } from '@/components/ui/DataState'
import {
  claudeConciergeAPI,
  type ConciergeInsight,
  type ConciergeResponse,
  type ProactiveSuggestion,
} from '@/lib/api/ClaudeConciergeAPI'

export default function ConciergePage() {
  const [insights, setInsights] = useState<ConciergeInsight[]>([])
  const [suggestions, setSuggestions] = useState<ProactiveSuggestion[]>([])
  const [message, setMessage] = useState('Summarize top revenue risks for today.')
  const [response, setResponse] = useState<ConciergeResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [sending, setSending] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let active = true

    async function load() {
      try {
        const [insightData, suggestionData] = await Promise.all([
          claudeConciergeAPI.getRealtimeInsights(),
          claudeConciergeAPI.getProactiveSuggestions(),
        ])

        if (!active) {
          return
        }

        setInsights(insightData)
        setSuggestions(suggestionData)
        setError(null)
      } catch (loadError) {
        if (!active) {
          return
        }

        setError(loadError instanceof Error ? loadError.message : 'Unable to load concierge intelligence')
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

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()

    try {
      setSending(true)
      const chatResponse = await claudeConciergeAPI.sendMessage({
        message,
        sessionId: 'enterprise-ui-demo-session',
        context: {
          currentPage: 'concierge',
          userRole: 'executive',
          activeLeads: [],
          businessMetrics: {},
        },
      })

      setResponse(chatResponse)
      setError(null)
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : 'Failed to send message')
    } finally {
      setSending(false)
    }
  }

  return (
    <>
      <section className="card">
        <h2>Claude Concierge</h2>
        <p>Live assistant channel for executive guidance, risk triage, and next-best actions.</p>
      </section>

      <DataState
        loading={loading}
        error={error}
        empty={insights.length === 0 && suggestions.length === 0}
        emptyLabel="No insights or suggestions are available right now."
      />

      <section className="grid-2">
        <article className="card">
          <h3>Realtime Insights</h3>
          <div className="list">
            {insights.slice(0, 6).map((insight) => (
              <div key={`${insight.title}-${insight.timestamp}`} className="row">
                <p className="row-title">{insight.title}</p>
                <p className="row-subtitle">{insight.description}</p>
                <span className="tag">{insight.value}</span>
              </div>
            ))}
          </div>
        </article>

        <article className="card">
          <h3>Proactive Suggestions</h3>
          <div className="list">
            {suggestions.slice(0, 5).map((suggestion) => (
              <div key={suggestion.id} className="row">
                <p className="row-title">{suggestion.title}</p>
                <p className="row-subtitle">{suggestion.description}</p>
                <span className="tag">{suggestion.priority}</span>
              </div>
            ))}
          </div>
        </article>
      </section>

      <section className="card">
        <h3>Ask Concierge</h3>
        <form onSubmit={onSubmit}>
          <textarea
            value={message}
            onChange={(event) => setMessage(event.target.value)}
            className="input"
            aria-label="Message"
          />
          <div style={{ marginTop: '0.75rem' }}>
            <button type="submit" className="button" disabled={sending || message.trim().length === 0}>
              {sending ? 'Sending...' : 'Send'}
            </button>
          </div>
        </form>
        {response ? (
          <div className="row" style={{ marginTop: '0.75rem' }}>
            <p className="row-title">Concierge Response</p>
            <p className="row-subtitle">{response.response}</p>
            <p className="small">Confidence: {Math.round(response.confidence * 100)}%</p>
          </div>
        ) : null}
      </section>
    </>
  )
}
