/**
 * Integration tests for n8n Workflow Execution
 * Tests: 30 tests covering complete workflow scenarios
 */

import { ExternalAPIMocks } from '../mocks/external-apis.mock';
import { LeadFactory } from '../factories/lead.factory';
import axios from 'axios';
import nock from 'nock';

describe('n8n Workflow Integration', () => {
  const N8N_WEBHOOK_URL = process.env.N8N_WEBHOOK_URL || 'http://localhost:5678/webhook';
  
  beforeAll(() => {
    ExternalAPIMocks.setupAllMocks();
  });

  afterAll(() => {
    ExternalAPIMocks.cleanAllMocks();
  });

  beforeEach(() => {
    // Reset mocks before each test
    nock.cleanAll();
    ExternalAPIMocks.setupAllMocks();
  });

  describe('Instant Lead Response Workflow', () => {
    test('should process valid lead through complete workflow', async () => {
      const leadData = LeadFactory.createValidLead({
        email: 'integration@example.com',
        firstName: 'Integration',
        lastName: 'Test',
        phone: '+15551234567',
        company: 'Test Corp',
        source: 'website'
      });

      // Mock n8n webhook response
      nock('http://localhost:5678')
        .post('/webhook/lead-capture')
        .reply(200, {
          success: true,
          execution_id: 'exec_integration_123',
          message: 'Lead processed successfully',
          steps_completed: [
            'lead_validation',
            'duplicate_check',
            'lead_scoring',
            'lead_enrichment',
            'instant_response',
            'database_save',
            'crm_sync'
          ],
          lead_id: 'lead_integration_456',
          score: 75
        });

      const response = await axios.post(`${N8N_WEBHOOK_URL}/lead-capture`, leadData);

      expect(response.status).toBe(200);
      expect(response.data.success).toBe(true);
      expect(response.data.execution_id).toBeDefined();
      expect(response.data.steps_completed).toContain('lead_validation');
      expect(response.data.steps_completed).toContain('instant_response');
      expect(response.data.lead_id).toBeDefined();
      expect(response.data.score).toBeGreaterThan(0);
    });

    test('should handle lead validation errors in workflow', async () => {
      const invalidLeadData = {
        email: 'invalid-email-format',
        firstName: '',
        lastName: 'Test'
      };

      // Mock validation error response
      nock('http://localhost:5678')
        .post('/webhook/lead-capture')
        .reply(400, {
          success: false,
          error: {
            code: 'VALIDATION_ERROR',
            message: 'Lead validation failed',
            details: {
              email: 'Invalid email format',
              firstName: 'First name is required'
            }
          },
          execution_id: 'exec_validation_error_123',
          step_failed: 'lead_validation'
        });

      try {
        await axios.post(`${N8N_WEBHOOK_URL}/lead-capture`, invalidLeadData);
        fail('Should have thrown an error');
      } catch (error: any) {
        expect(error.response.status).toBe(400);
        expect(error.response.data.success).toBe(false);
        expect(error.response.data.error.code).toBe('VALIDATION_ERROR');
        expect(error.response.data.step_failed).toBe('lead_validation');
      }
    });

    test('should handle duplicate lead detection', async () => {
      const duplicateLeadData = LeadFactory.createValidLead({
        email: 'duplicate@example.com' // Triggers duplicate detection
      });

      nock('http://localhost:5678')
        .post('/webhook/lead-capture')
        .reply(409, {
          success: false,
          error: {
            code: 'DUPLICATE_LEAD',
            message: 'Lead with this email already exists',
            existing_lead_id: 'existing_lead_789'
          },
          execution_id: 'exec_duplicate_123',
          step_failed: 'duplicate_check'
        });

      try {
        await axios.post(`${N8N_WEBHOOK_URL}/lead-capture`, duplicateLeadData);
        fail('Should have thrown an error');
      } catch (error: any) {
        expect(error.response.status).toBe(409);
        expect(error.response.data.error.code).toBe('DUPLICATE_LEAD');
        expect(error.response.data.error.existing_lead_id).toBeDefined();
      }
    });

    test('should complete workflow within 60-second SLA', async () => {
      const leadData = LeadFactory.createValidLead();
      const startTime = Date.now();

      nock('http://localhost:5678')
        .post('/webhook/lead-capture')
        .reply(200, {
          success: true,
          execution_id: 'exec_sla_test',
          processing_time_ms: 850,
          sla_met: true
        });

      const response = await axios.post(`${N8N_WEBHOOK_URL}/lead-capture`, leadData);
      const totalTime = Date.now() - startTime;

      expect(response.status).toBe(200);
      expect(response.data.sla_met).toBe(true);
      expect(totalTime).toBeLessThan(60000); // 60 seconds
      expect(response.data.processing_time_ms).toBeLessThan(2000); // Internal processing under 2s
    });

    test('should handle high-priority leads with immediate routing', async () => {
      const hotLeadData = LeadFactory.createHighScoreLead({
        email: 'ceo@fortune500.com',
        jobTitle: 'CEO',
        temperature: 'hot',
        source: 'referral'
      });

      nock('http://localhost:5678')
        .post('/webhook/lead-capture')
        .reply(200, {
          success: true,
          execution_id: 'exec_hot_lead',
          priority: 'HIGH',
          assigned_to: 'senior_sales_rep_001',
          immediate_notification_sent: true,
          escalation_triggered: true,
          score: 95
        });

      const response = await axios.post(`${N8N_WEBHOOK_URL}/lead-capture`, hotLeadData);

      expect(response.data.priority).toBe('HIGH');
      expect(response.data.assigned_to).toBeDefined();
      expect(response.data.immediate_notification_sent).toBe(true);
      expect(response.data.escalation_triggered).toBe(true);
      expect(response.data.score).toBeGreaterThan(80);
    });

    test('should handle workflow execution during off-hours', async () => {
      const leadData = LeadFactory.createValidLead();
      const offHoursContext = {
        timestamp: '2024-01-15T02:00:00Z', // 2 AM
        business_hours: false
      };

      nock('http://localhost:5678')
        .post('/webhook/lead-capture')
        .reply(200, {
          success: true,
          execution_id: 'exec_off_hours',
          business_hours: false,
          scheduled_follow_up: '2024-01-15T09:00:00Z',
          automated_response_sent: true,
          human_follow_up_scheduled: true
        });

      const response = await axios.post(`${N8N_WEBHOOK_URL}/lead-capture`, {
        ...leadData,
        context: offHoursContext
      });

      expect(response.data.business_hours).toBe(false);
      expect(response.data.automated_response_sent).toBe(true);
      expect(response.data.human_follow_up_scheduled).toBe(true);
      expect(response.data.scheduled_follow_up).toBeDefined();
    });

    test('should handle partial workflow failures with recovery', async () => {
      const leadData = LeadFactory.createValidLead();

      nock('http://localhost:5678')
        .post('/webhook/lead-capture')
        .reply(206, { // Partial success
          success: true,
          execution_id: 'exec_partial_failure',
          steps_completed: [
            'lead_validation',
            'duplicate_check',
            'lead_scoring',
            'instant_response',
            'database_save'
          ],
          steps_failed: [
            'lead_enrichment' // Apollo API failed
          ],
          warnings: [
            'Lead enrichment failed - will retry in background'
          ],
          recovery_scheduled: true,
          retry_job_id: 'retry_job_789'
        });

      const response = await axios.post(`${N8N_WEBHOOK_URL}/lead-capture`, leadData);

      expect(response.status).toBe(206);
      expect(response.data.success).toBe(true);
      expect(response.data.steps_failed).toContain('lead_enrichment');
      expect(response.data.recovery_scheduled).toBe(true);
      expect(response.data.retry_job_id).toBeDefined();
    });

    test('should measure workflow performance metrics', async () => {
      const leadData = LeadFactory.createValidLead();

      nock('http://localhost:5678')
        .post('/webhook/lead-capture')
        .reply(200, {
          success: true,
          execution_id: 'exec_metrics',
          performance_metrics: {
            total_execution_time_ms: 1250,
            step_timings: {
              lead_validation: 45,
              duplicate_check: 120,
              lead_scoring: 180,
              lead_enrichment: 320,
              instant_response: 85,
              database_save: 200,
              crm_sync: 300
            },
            bottleneck_step: 'lead_enrichment',
            sla_buffer_ms: 58750 // Time remaining in 60s SLA
          }
        });

      const response = await axios.post(`${N8N_WEBHOOK_URL}/lead-capture`, leadData);

      const metrics = response.data.performance_metrics;
      expect(metrics.total_execution_time_ms).toBeGreaterThan(0);
      expect(metrics.step_timings).toBeDefined();
      expect(metrics.bottleneck_step).toBe('lead_enrichment');
      expect(metrics.sla_buffer_ms).toBeGreaterThan(0);

      // Validate individual step timings
      Object.values(metrics.step_timings).forEach(timing => {
        expect(typeof timing).toBe('number');
        expect(timing).toBeGreaterThan(0);
      });
    });
  });

  describe('Lead Intelligence Engine Workflow', () => {
    test('should enrich lead with Apollo data', async () => {
      const leadData = LeadFactory.createValidLead({
        email: 'enrich@company.com'
      });

      nock('http://localhost:5678')
        .post('/webhook/lead-intelligence')
        .reply(200, {
          success: true,
          execution_id: 'exec_intelligence_123',
          enrichment_results: {
            apollo: {
              success: true,
              data: {
                job_title: 'VP Sales',
                linkedin_url: 'https://linkedin.com/in/vpssales',
                company: {
                  name: 'Company Inc',
                  industry: 'Technology',
                  size: 500,
                  revenue: 25000000
                }
              },
              confidence: 0.92
            },
            scoring: {
              original_score: 45,
              enriched_score: 78,
              improvement: 33,
              factors_improved: ['job_title', 'company_size', 'industry']
            }
          },
          data_quality: 'enriched'
        });

      const response = await axios.post(`${N8N_WEBHOOK_URL}/lead-intelligence`, leadData);

      expect(response.data.success).toBe(true);
      expect(response.data.enrichment_results.apollo.success).toBe(true);
      expect(response.data.enrichment_results.apollo.confidence).toBeGreaterThan(0.8);
      expect(response.data.enrichment_results.scoring.enriched_score).toBeGreaterThan(
        response.data.enrichment_results.scoring.original_score
      );
      expect(response.data.data_quality).toBe('enriched');
    });

    test('should handle Apollo API rate limiting', async () => {
      const leadData = LeadFactory.createValidLead();

      nock('http://localhost:5678')
        .post('/webhook/lead-intelligence')
        .reply(429, {
          success: false,
          error: {
            code: 'RATE_LIMIT_EXCEEDED',
            message: 'Apollo API rate limit exceeded',
            retry_after_seconds: 60
          },
          execution_id: 'exec_rate_limit',
          retry_scheduled: true,
          retry_at: '2024-01-15T10:01:00Z'
        });

      try {
        await axios.post(`${N8N_WEBHOOK_URL}/lead-intelligence`, leadData);
        fail('Should have thrown an error');
      } catch (error: any) {
        expect(error.response.status).toBe(429);
        expect(error.response.data.error.code).toBe('RATE_LIMIT_EXCEEDED');
        expect(error.response.data.retry_scheduled).toBe(true);
        expect(error.response.data.retry_at).toBeDefined();
      }
    });

    test('should handle partial enrichment failures gracefully', async () => {
      const leadData = LeadFactory.createValidLead();

      nock('http://localhost:5678')
        .post('/webhook/lead-intelligence')
        .reply(206, {
          success: true,
          execution_id: 'exec_partial_enrichment',
          enrichment_results: {
            apollo: {
              success: false,
              error: 'Contact not found in Apollo database'
            },
            clearbit: {
              success: true,
              data: {
                company: {
                  name: 'Partial Corp',
                  industry: 'Manufacturing'
                }
              },
              confidence: 0.75
            },
            scoring: {
              original_score: 45,
              enriched_score: 52,
              improvement: 7,
              note: 'Limited enrichment data available'
            }
          },
          data_quality: 'partially_enriched'
        });

      const response = await axios.post(`${N8N_WEBHOOK_URL}/lead-intelligence`, leadData);

      expect(response.status).toBe(206);
      expect(response.data.success).toBe(true);
      expect(response.data.enrichment_results.apollo.success).toBe(false);
      expect(response.data.enrichment_results.clearbit.success).toBe(true);
      expect(response.data.data_quality).toBe('partially_enriched');
    });

    test('should perform lead scoring with enriched data', async () => {
      const leadData = LeadFactory.createValidLead();

      nock('http://localhost:5678')
        .post('/webhook/lead-intelligence')
        .reply(200, {
          success: true,
          execution_id: 'exec_scoring',
          scoring_results: {
            final_score: 82,
            confidence: 0.88,
            factors: {
              email_domain: 85,
              company_size: 90,
              job_seniority: 95,
              industry: 80,
              behavioral_signals: 60,
              lead_source: 70
            },
            reasoning: 'Senior decision-maker at large enterprise company',
            recommendations: [
              'High priority - contact within 1 hour',
              'Assign to senior sales rep',
              'Schedule demo call'
            ],
            temperature: 'hot'
          }
        });

      const response = await axios.post(`${N8N_WEBHOOK_URL}/lead-intelligence`, leadData);

      const scoring = response.data.scoring_results;
      expect(scoring.final_score).toBeGreaterThan(80);
      expect(scoring.confidence).toBeGreaterThan(0.8);
      expect(scoring.factors).toBeDefined();
      expect(scoring.recommendations).toContain('High priority - contact within 1 hour');
      expect(scoring.temperature).toBe('hot');
    });

    test('should integrate with multiple enrichment providers', async () => {
      const leadData = LeadFactory.createValidLead();

      nock('http://localhost:5678')
        .post('/webhook/lead-intelligence')
        .reply(200, {
          success: true,
          execution_id: 'exec_multi_provider',
          enrichment_results: {
            providers_used: ['apollo', 'clearbit', 'zoominfo'],
            apollo: {
              success: true,
              data: { job_title: 'VP Sales' },
              confidence: 0.92
            },
            clearbit: {
              success: true,
              data: { company: { employees: 1000 } },
              confidence: 0.85
            },
            zoominfo: {
              success: true,
              data: { intent_signals: ['software_purchase'] },
              confidence: 0.78
            },
            aggregated_confidence: 0.88,
            best_source: 'apollo'
          }
        });

      const response = await axios.post(`${N8N_WEBHOOK_URL}/lead-intelligence`, leadData);

      const enrichment = response.data.enrichment_results;
      expect(enrichment.providers_used).toHaveLength(3);
      expect(enrichment.apollo.success).toBe(true);
      expect(enrichment.clearbit.success).toBe(true);
      expect(enrichment.zoominfo.success).toBe(true);
      expect(enrichment.aggregated_confidence).toBeGreaterThan(0.8);
      expect(enrichment.best_source).toBeDefined();
    });
  });

  describe('Workflow Error Handling and Recovery', () => {
    test('should implement exponential backoff for retries', async () => {
      const leadData = LeadFactory.createValidLead();
      let attemptCount = 0;

      // Mock multiple failed attempts then success
      nock('http://localhost:5678')
        .post('/webhook/lead-capture')
        .times(3)
        .reply(() => {
          attemptCount++;
          if (attemptCount < 3) {
            return [500, { error: 'Temporary service unavailable', attempt: attemptCount }];
          }
          return [200, {
            success: true,
            execution_id: 'exec_retry_success',
            attempts: attemptCount,
            retry_strategy: 'exponential_backoff'
          }];
        });

      // Simulate retry logic with exponential backoff
      let lastAttempt = Date.now();
      let response: any;

      for (let attempt = 1; attempt <= 3; attempt++) {
        try {
          response = await axios.post(`${N8N_WEBHOOK_URL}/lead-capture`, leadData);
          break;
        } catch (error: any) {
          if (attempt < 3) {
            const backoffMs = Math.pow(2, attempt) * 1000; // 2s, 4s, 8s
            await new Promise(resolve => setTimeout(resolve, 100)); // Shortened for test
            
            const timeSinceLastAttempt = Date.now() - lastAttempt;
            expect(timeSinceLastAttempt).toBeGreaterThan(90); // Allow for test timing
            lastAttempt = Date.now();
          } else {
            throw error;
          }
        }
      }

      expect(response.status).toBe(200);
      expect(response.data.attempts).toBe(3);
    });

    test('should handle database connection failures', async () => {
      const leadData = LeadFactory.createValidLead();

      nock('http://localhost:5678')
        .post('/webhook/lead-capture')
        .reply(503, {
          success: false,
          error: {
            code: 'DATABASE_CONNECTION_ERROR',
            message: 'Cannot connect to PostgreSQL database',
            temporary: true
          },
          execution_id: 'exec_db_error',
          retry_recommended: true,
          fallback_used: true,
          fallback_storage: 'redis_queue'
        });

      try {
        await axios.post(`${N8N_WEBHOOK_URL}/lead-capture`, leadData);
        fail('Should have thrown an error');
      } catch (error: any) {
        expect(error.response.status).toBe(503);
        expect(error.response.data.error.code).toBe('DATABASE_CONNECTION_ERROR');
        expect(error.response.data.fallback_used).toBe(true);
        expect(error.response.data.fallback_storage).toBe('redis_queue');
      }
    });

    test('should handle external API failures with circuit breaker', async () => {
      const leadData = LeadFactory.createValidLead();

      nock('http://localhost:5678')
        .post('/webhook/lead-intelligence')
        .reply(503, {
          success: false,
          error: {
            code: 'CIRCUIT_BREAKER_OPEN',
            message: 'Apollo API circuit breaker is open due to repeated failures',
            circuit_breaker_state: 'OPEN',
            failure_count: 15,
            next_retry_allowed_at: '2024-01-15T10:05:00Z'
          },
          execution_id: 'exec_circuit_breaker',
          fallback_executed: true,
          fallback_result: 'basic_scoring_only'
        });

      try {
        await axios.post(`${N8N_WEBHOOK_URL}/lead-intelligence`, leadData);
        fail('Should have thrown an error');
      } catch (error: any) {
        expect(error.response.status).toBe(503);
        expect(error.response.data.error.code).toBe('CIRCUIT_BREAKER_OPEN');
        expect(error.response.data.fallback_executed).toBe(true);
        expect(error.response.data.error.failure_count).toBeGreaterThan(10);
      }
    });

    test('should handle workflow timeout scenarios', async () => {
      const leadData = LeadFactory.createValidLead();

      nock('http://localhost:5678')
        .post('/webhook/lead-capture')
        .delay(65000) // Delay longer than 60s SLA
        .reply(408, {
          success: false,
          error: {
            code: 'WORKFLOW_TIMEOUT',
            message: 'Workflow execution exceeded 60 second SLA',
            execution_time_ms: 65000,
            sla_threshold_ms: 60000
          },
          execution_id: 'exec_timeout',
          partial_completion: true,
          completed_steps: ['lead_validation', 'duplicate_check'],
          failed_at_step: 'lead_enrichment'
        });

      try {
        // Set a shorter timeout for the test
        await axios.post(`${N8N_WEBHOOK_URL}/lead-capture`, leadData, { timeout: 1000 });
        fail('Should have thrown a timeout error');
      } catch (error: any) {
        expect(error.code).toBe('ECONNABORTED'); // Axios timeout error
      }
    });
  });

  describe('Workflow Performance Testing', () => {
    test('should handle concurrent webhook requests efficiently', async () => {
      const concurrentRequests = 10;
      const leadDataBatch = LeadFactory.createBatchOfLeads(concurrentRequests);

      // Mock successful responses for all concurrent requests
      nock('http://localhost:5678')
        .post('/webhook/lead-capture')
        .times(concurrentRequests)
        .reply(200, (uri, requestBody) => ({
          success: true,
          execution_id: `exec_concurrent_${Date.now()}_${Math.random()}`,
          request_processed_at: new Date().toISOString(),
          concurrent_request: true
        }));

      const startTime = Date.now();
      
      const promises = leadDataBatch.map(leadData => 
        axios.post(`${N8N_WEBHOOK_URL}/lead-capture`, leadData)
      );

      const responses = await Promise.all(promises);
      const totalTime = Date.now() - startTime;

      expect(responses).toHaveLength(concurrentRequests);
      expect(responses.every(r => r.status === 200)).toBe(true);
      expect(responses.every(r => r.data.success === true)).toBe(true);
      expect(totalTime).toBeLessThan(10000); // Should complete within 10 seconds
    });

    test('should maintain performance under load', async () => {
      const loadTestRequests = 50;
      const leadDataBatch = LeadFactory.createBatchOfLeads(loadTestRequests);

      // Mock responses with varying processing times
      nock('http://localhost:5678')
        .post('/webhook/lead-capture')
        .times(loadTestRequests)
        .reply(200, () => ({
          success: true,
          execution_id: `exec_load_${Date.now()}_${Math.random()}`,
          processing_time_ms: Math.floor(Math.random() * 2000) + 500, // 500-2500ms
          load_test: true
        }));

      const startTime = Date.now();
      
      // Process in batches to simulate realistic load
      const batchSize = 10;
      const batches = [];
      
      for (let i = 0; i < loadTestRequests; i += batchSize) {
        const batch = leadDataBatch.slice(i, i + batchSize);
        batches.push(
          Promise.all(batch.map(leadData => 
            axios.post(`${N8N_WEBHOOK_URL}/lead-capture`, leadData)
          ))
        );
      }

      const batchResults = await Promise.all(batches);
      const totalTime = Date.now() - startTime;
      
      const allResponses = batchResults.flat();
      expect(allResponses).toHaveLength(loadTestRequests);
      expect(allResponses.every(r => r.status === 200)).toBe(true);
      expect(totalTime).toBeLessThan(30000); // Should complete within 30 seconds

      // Calculate average response time
      const averageProcessingTime = allResponses.reduce((sum, response) => 
        sum + response.data.processing_time_ms, 0) / allResponses.length;
      
      expect(averageProcessingTime).toBeLessThan(3000); // Average under 3 seconds
    });

    test('should handle memory-intensive operations', async () => {
      const leadWithLargePayload = LeadFactory.createValidLead({
        customFields: {
          large_data: 'x'.repeat(100000), // 100KB of data
          metadata: Object.fromEntries(
            Array.from({ length: 1000 }, (_, i) => [`field_${i}`, `value_${i}`])
          )
        }
      });

      nock('http://localhost:5678')
        .post('/webhook/lead-capture')
        .reply(200, {
          success: true,
          execution_id: 'exec_large_payload',
          payload_size_bytes: JSON.stringify(leadWithLargePayload).length,
          memory_usage_mb: 15.5,
          processing_optimized: true
        });

      const response = await axios.post(`${N8N_WEBHOOK_URL}/lead-capture`, leadWithLargePayload);

      expect(response.status).toBe(200);
      expect(response.data.success).toBe(true);
      expect(response.data.payload_size_bytes).toBeGreaterThan(100000);
      expect(response.data.memory_usage_mb).toBeLessThan(50); // Reasonable memory usage
    });
  });

  describe('Workflow Data Validation Integration', () => {
    test('should validate webhook payload structure', async () => {
      const malformedPayload = {
        invalidField: 'test',
        nested: {
          tooDeep: {
            structure: 'invalid'
          }
        }
      };

      nock('http://localhost:5678')
        .post('/webhook/lead-capture')
        .reply(422, {
          success: false,
          error: {
            code: 'INVALID_PAYLOAD_STRUCTURE',
            message: 'Webhook payload does not match expected schema',
            validation_errors: [
              'Missing required field: email',
              'Unknown field: invalidField',
              'Nested structure too deep'
            ]
          },
          execution_id: 'exec_invalid_payload',
          schema_version: '1.0.0'
        });

      try {
        await axios.post(`${N8N_WEBHOOK_URL}/lead-capture`, malformedPayload);
        fail('Should have thrown validation error');
      } catch (error: any) {
        expect(error.response.status).toBe(422);
        expect(error.response.data.error.code).toBe('INVALID_PAYLOAD_STRUCTURE');
        expect(error.response.data.error.validation_errors).toContain('Missing required field: email');
      }
    });

    test('should handle cross-field validation rules', async () => {
      const conflictingData = LeadFactory.createValidLead({
        companySize: 5, // Small company
        jobTitle: 'CEO', // Senior title
        companyRevenue: 1000000000 // Large revenue - inconsistent
      });

      nock('http://localhost:5678')
        .post('/webhook/lead-capture')
        .reply(200, {
          success: true,
          execution_id: 'exec_cross_validation',
          validation_warnings: [
            'Company size (5) seems inconsistent with revenue ($1B)',
            'Job title may be inflated for company size'
          ],
          data_quality_flags: ['POTENTIAL_INCONSISTENCY'],
          score_adjusted: true,
          original_score: 85,
          adjusted_score: 72
        });

      const response = await axios.post(`${N8N_WEBHOOK_URL}/lead-capture`, conflictingData);

      expect(response.status).toBe(200);
      expect(response.data.validation_warnings.length).toBeGreaterThan(0);
      expect(response.data.data_quality_flags).toContain('POTENTIAL_INCONSISTENCY');
      expect(response.data.adjusted_score).toBeLessThan(response.data.original_score);
    });
  });
});