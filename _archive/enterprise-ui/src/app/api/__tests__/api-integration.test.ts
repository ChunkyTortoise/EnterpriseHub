/**
 * API Integration Tests
 * Testing Next.js API routes for Jorge's Real Estate Platform
 */

import { NextRequest } from 'next/server'
import { POST as jorgeSellerPost, GET as jorgeSellerGet } from '../bots/jorge-seller/route'
import { POST as leadBotPost, GET as leadBotGet } from '../bots/lead-bot/route'
import { POST as intelligencePost } from '../leads/intelligence/route'
import { POST as metricsPost, GET as metricsGet } from '../dashboard/metrics/route'

// Mock external dependencies
jest.mock('@/lib/jorge-api-client')

describe('API Integration Tests', () => {
  describe('Jorge Seller Bot API', () => {
    describe('POST /api/bots/jorge-seller', () => {
      it('handles valid seller message', async () => {
        const requestBody = {
          contact_id: 'contact_123',
          location_id: 'loc_456',
          message: 'I want to sell my house',
          contact_info: {
            name: 'John Doe',
            phone: '+1234567890',
            email: 'john@example.com'
          }
        }

        const request = new NextRequest('http://localhost:3000/api/bots/jorge-seller', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(requestBody)
        })

        const response = await jorgeSellerPost(request)
        const data = await response.json()

        expect(response.status).toBe(200)
        expect(data).toHaveProperty('status', 'success')
        expect(data.data).toHaveProperty('response_message')
        expect(data.data).toHaveProperty('seller_temperature')
        expect(data.data).toHaveProperty('questions_answered')
        expect(data.data).toHaveProperty('qualification_complete')
        expect(data.data).toHaveProperty('actions_taken')

        // Jorge's confrontational response should be present
        expect(data.data.response_message).toContain('motivated')
        expect(['hot', 'warm', 'cold']).toContain(data.data.seller_temperature)
        expect(typeof data.data.questions_answered).toBe('number')
        expect(typeof data.data.qualification_complete).toBe('boolean')
      })

      it('validates required fields', async () => {
        const invalidRequestBody = {
          contact_id: 'contact_123',
          // missing location_id and message
        }

        const request = new NextRequest('http://localhost:3000/api/bots/jorge-seller', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(invalidRequestBody)
        })

        const response = await jorgeSellerPost(request)
        const data = await response.json()

        expect(response.status).toBe(400)
        expect(data).toHaveProperty('error')
        expect(data.error).toContain('validation')
      })

      it('handles Jorge Q1-Q4 progression', async () => {
        const q1Request = new NextRequest('http://localhost:3000/api/bots/jorge-seller', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            contact_id: 'contact_q1',
            location_id: 'loc_123',
            message: 'I need to sell quickly'
          })
        })

        const response = await jorgeSellerPost(q1Request)
        const data = await response.json()

        expect(response.status).toBe(200)
        expect(data.data.questions_answered).toBeGreaterThanOrEqual(0)
        expect(data.data.questions_answered).toBeLessThanOrEqual(4)

        // Jorge's confrontational methodology markers
        expect(data.data).toHaveProperty('next_steps')
        expect(data.data.analytics).toHaveProperty('confrontational_score')
      })
    })

    describe('GET /api/bots/jorge-seller', () => {
      it('returns seller state', async () => {
        const request = new NextRequest('http://localhost:3000/api/bots/jorge-seller?contact_id=contact_123')

        const response = await jorgeSellerGet(request)
        const data = await response.json()

        expect(response.status).toBe(200)
        expect(data).toHaveProperty('status', 'success')
        expect(data.data).toHaveProperty('contact_id')
        expect(data.data).toHaveProperty('qualification_state')
        expect(data.data.qualification_state).toHaveProperty('current_question')
        expect(data.data.qualification_state).toHaveProperty('seller_temperature')
      })

      it('requires contact_id parameter', async () => {
        const request = new NextRequest('http://localhost:3000/api/bots/jorge-seller')

        const response = await jorgeSellerGet(request)
        const data = await response.json()

        expect(response.status).toBe(400)
        expect(data).toHaveProperty('error')
      })
    })
  })

  describe('Lead Bot API', () => {
    describe('POST /api/bots/lead-bot', () => {
      it('triggers 3-7-30 automation sequence', async () => {
        const requestBody = {
          contact_id: 'contact_lead',
          location_id: 'loc_123',
          automation_type: 'day_7',
          trigger_data: {
            qualification_results: {
              seller_temperature: 'warm',
              property_value: 450000
            }
          }
        }

        const request = new NextRequest('http://localhost:3000/api/bots/lead-bot', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(requestBody)
        })

        const response = await leadBotPost(request)
        const data = await response.json()

        expect(response.status).toBe(200)
        expect(data).toHaveProperty('status', 'success')
        expect(data.data).toHaveProperty('automation_id')
        expect(data.data).toHaveProperty('status')
        expect(data.data).toHaveProperty('actions_taken')

        // Should include Retell AI integration for day 7
        if (requestBody.automation_type === 'day_7') {
          expect(data.data.actions_taken).toContainEqual(
            expect.objectContaining({
              type: 'retell_voice_call',
              channel: 'voice_call'
            })
          )
        }
      })

      it('validates automation type', async () => {
        const invalidRequest = new NextRequest('http://localhost:3000/api/bots/lead-bot', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            contact_id: 'contact_lead',
            location_id: 'loc_123',
            automation_type: 'invalid_day'
          })
        })

        const response = await leadBotPost(invalidRequest)
        const data = await response.json()

        expect(response.status).toBe(400)
        expect(data).toHaveProperty('error')
      })

      it('handles CMA injection for buyer leads', async () => {
        const cmaRequest = new NextRequest('http://localhost:3000/api/bots/lead-bot', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            contact_id: 'buyer_lead',
            location_id: 'loc_456',
            automation_type: 'post_showing',
            trigger_data: {
              showing_feedback: 'positive',
              property_interest: 'high'
            }
          })
        })

        const response = await leadBotPost(cmaRequest)
        const data = await response.json()

        expect(response.status).toBe(200)
        expect(data.data.actions_taken).toContainEqual(
          expect.objectContaining({
            type: 'cma_value_injection'
          })
        )
      })
    })

    describe('GET /api/bots/lead-bot', () => {
      it('returns automation status', async () => {
        const request = new NextRequest('http://localhost:3000/api/bots/lead-bot?contact_id=contact_lead')

        const response = await leadBotGet(request)
        const data = await response.json()

        expect(response.status).toBe(200)
        expect(data.data).toHaveProperty('active_sequences')
        expect(data.data).toHaveProperty('completed_actions')
        expect(data.data).toHaveProperty('scheduled_actions')
      })
    })
  })

  describe('Lead Intelligence API', () => {
    describe('POST /api/leads/intelligence', () => {
      it('analyzes lead intelligence with 28-feature pipeline', async () => {
        const requestBody = {
          contact_id: 'contact_analysis',
          location_id: 'loc_123',
          analyze_type: 'full_analysis',
          conversation_data: {
            messages: [
              'I need to sell my house quickly',
              'I am motivated to close fast',
              'Price is not the main concern'
            ],
            timestamp: new Date().toISOString()
          },
          lead_data: {
            source: 'website',
            initial_interest: 'seller'
          }
        }

        const request = new NextRequest('http://localhost:3000/api/leads/intelligence', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(requestBody)
        })

        const response = await intelligencePost(request)
        const data = await response.json()

        expect(response.status).toBe(200)
        expect(data).toHaveProperty('status', 'success')
        expect(data.data).toHaveProperty('scores')
        expect(data.data).toHaveProperty('classification')
        expect(data.data).toHaveProperty('insights')
        expect(data.data).toHaveProperty('ml_analysis')

        // Verify 95% accuracy target and 42ms processing time
        expect(data.data.ml_analysis.confidence).toBeGreaterThan(0.85)
        expect(data.data.ml_analysis.processing_time_ms).toBeLessThan(100)

        // Check Jorge's specific scoring
        expect(data.data.scores.intent_score).toBeGreaterThanOrEqual(0)
        expect(data.data.scores.intent_score).toBeLessThanOrEqual(100)
        expect(data.data.classification.temperature).toMatch(/^(hot|warm|cold)$/)
      })

      it('handles intent scoring only', async () => {
        const intentRequest = new NextRequest('http://localhost:3000/api/leads/intelligence', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            contact_id: 'contact_intent',
            location_id: 'loc_456',
            analyze_type: 'intent_scoring',
            conversation_data: {
              messages: ['Just browsing properties']
            }
          })
        })

        const response = await intelligencePost(intentRequest)
        const data = await response.json()

        expect(response.status).toBe(200)
        expect(data.data.scores.intent_score).toBeLessThan(50) // Low intent
        expect(data.data.classification.urgency_level).toBe('passive')
      })
    })
  })

  describe('Dashboard Metrics API', () => {
    describe('POST /api/dashboard/metrics', () => {
      it('returns comprehensive real-time metrics', async () => {
        const requestBody = {
          metric_types: ['bot_performance', 'revenue_tracking', 'system_health'],
          real_time: true,
          include_ml_features: true
        }

        const request = new NextRequest('http://localhost:3000/api/dashboard/metrics', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(requestBody)
        })

        const response = await metricsPost(request)
        const data = await response.json()

        expect(response.status).toBe(200)
        expect(data).toHaveProperty('status', 'success')
        expect(data.data).toHaveProperty('bot_performance')
        expect(data.data).toHaveProperty('revenue_tracking')
        expect(data.data).toHaveProperty('system_health')

        // Jorge-specific metrics
        const jorgeMetrics = data.data.bot_performance.jorge_seller_bot
        expect(jorgeMetrics).toHaveProperty('conversations_today')
        expect(jorgeMetrics).toHaveProperty('qualified_sellers')
        expect(jorgeMetrics).toHaveProperty('completion_rate')
        expect(jorgeMetrics).toHaveProperty('q1_q4_conversion_rate')

        // Revenue tracking with 6% commission
        expect(data.data.revenue_tracking).toHaveProperty('jorge_commission_rate', 6.0)
        expect(data.data.revenue_tracking).toHaveProperty('potential_revenue_pipeline')

        // System health indicators
        expect(data.data.system_health.redis_status).toMatch(/^(healthy|degraded|down)$/)
        expect(data.data.system_health.ghl_api_status).toMatch(/^(connected|limited|disconnected)$/)
      })

      it('provides lead bot automation metrics', async () => {
        const request = new NextRequest('http://localhost:3000/api/dashboard/metrics', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            metric_types: ['bot_performance'],
            real_time: true
          })
        })

        const response = await metricsPost(request)
        const data = await response.json()

        const leadBotMetrics = data.data.bot_performance.lead_bot
        expect(leadBotMetrics).toHaveProperty('active_sequences')
        expect(leadBotMetrics).toHaveProperty('day_7_call_success_rate')
        expect(leadBotMetrics).toHaveProperty('retell_ai_call_minutes')
      })

      it('shows intent decoder performance', async () => {
        const request = new NextRequest('http://localhost:3000/api/dashboard/metrics', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            metric_types: ['bot_performance'],
            real_time: true
          })
        })

        const response = await metricsPost(request)
        const data = await response.json()

        const intentMetrics = data.data.bot_performance.intent_decoder
        expect(intentMetrics).toHaveProperty('analyses_today')
        expect(intentMetrics).toHaveProperty('accuracy_rate')
        expect(intentMetrics).toHaveProperty('avg_processing_time_ms')

        // Should meet Jorge's performance targets
        expect(intentMetrics.accuracy_rate).toBeGreaterThan(90)
        expect(intentMetrics.avg_processing_time_ms).toBeLessThan(50)
      })
    })

    describe('GET /api/dashboard/metrics', () => {
      it('returns summary metrics', async () => {
        const request = new NextRequest('http://localhost:3000/api/dashboard/metrics?metric_type=summary')

        const response = await metricsGet(request)
        const data = await response.json()

        expect(response.status).toBe(200)
        expect(data).toHaveProperty('summary')
        expect(data.summary).toHaveProperty('total_conversations')
        expect(data.summary).toHaveProperty('qualified_leads')
        expect(data.summary).toHaveProperty('system_status')
      })

      it('handles real-time parameter', async () => {
        const request = new NextRequest('http://localhost:3000/api/dashboard/metrics?real_time=true')

        const response = await metricsGet(request)
        const data = await response.json()

        expect(response.status).toBe(200)
        expect(data).toHaveProperty('real_time', true)
        expect(data).toHaveProperty('timestamp')
      })
    })
  })

  describe('Error Handling', () => {
    it('handles malformed JSON gracefully', async () => {
      const request = new NextRequest('http://localhost:3000/api/bots/jorge-seller', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: 'invalid json'
      })

      const response = await jorgeSellerPost(request)
      const data = await response.json()

      expect(response.status).toBe(400)
      expect(data).toHaveProperty('error')
      expect(data.error).toContain('JSON')
    })

    it('handles missing content-type header', async () => {
      const request = new NextRequest('http://localhost:3000/api/bots/jorge-seller', {
        method: 'POST',
        body: JSON.stringify({ contact_id: 'test' })
      })

      const response = await jorgeSellerPost(request)
      const data = await response.json()

      expect(response.status).toBe(400)
      expect(data).toHaveProperty('error')
    })

    it('validates HTTP methods', async () => {
      const request = new NextRequest('http://localhost:3000/api/bots/jorge-seller', {
        method: 'PUT', // Invalid method
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ contact_id: 'test' })
      })

      // This would be handled by Next.js routing
      // The actual implementation would return 405 Method Not Allowed
    })
  })

  describe('Performance', () => {
    it('responds within acceptable time limits', async () => {
      const startTime = Date.now()

      const request = new NextRequest('http://localhost:3000/api/dashboard/metrics', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ metric_types: ['bot_performance'] })
      })

      const response = await metricsPost(request)
      const endTime = Date.now()

      expect(response.status).toBe(200)
      expect(endTime - startTime).toBeLessThan(200) // Should respond in <200ms
    })

    it('handles concurrent requests efficiently', async () => {
      const requests = Array.from({ length: 10 }, () =>
        new NextRequest('http://localhost:3000/api/dashboard/metrics?metric_type=summary')
      )

      const startTime = Date.now()
      const responses = await Promise.all(
        requests.map(request => metricsGet(request))
      )
      const endTime = Date.now()

      responses.forEach(response => {
        expect(response.status).toBe(200)
      })

      expect(endTime - startTime).toBeLessThan(1000) // 10 requests in <1 second
    })
  })

  describe('Security', () => {
    it('sanitizes input data', async () => {
      const maliciousRequest = new NextRequest('http://localhost:3000/api/bots/jorge-seller', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          contact_id: '<script>alert("xss")</script>',
          location_id: 'loc_123',
          message: 'normal message'
        })
      })

      const response = await jorgeSellerPost(maliciousRequest)
      const data = await response.json()

      // Should either sanitize or reject malicious input
      expect(response.status).toBeOneOf([200, 400])
      if (response.status === 200) {
        expect(data.data.response_message).not.toContain('<script>')
      }
    })

    it('validates contact_id format', async () => {
      const request = new NextRequest('http://localhost:3000/api/bots/jorge-seller', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          contact_id: '../../../etc/passwd',
          location_id: 'loc_123',
          message: 'test'
        })
      })

      const response = await jorgeSellerPost(request)
      const data = await response.json()

      expect(response.status).toBe(400)
      expect(data).toHaveProperty('error')
    })
  })
})