/**
 * K6 Load Testing Script for RAG API
 *
 * Comprehensive load testing with multiple scenarios:
 * - Ramp-up testing with graduated load increases
 * - Sustained load testing under target user levels
 * - Spike testing for sudden load increases
 * - Performance threshold validation
 *
 * Targets:
 * - p95 latency < 50ms under normal load
 * - Error rate < 1%
 * - Throughput > 1000 req/min sustained
 */

import http from 'k6/http';
import { check, sleep, group } from 'k6';
import { Rate, Trend, Counter } from 'k6/metrics';
import { randomItem, randomIntBetween } from 'k6/utils';

// Custom metrics for detailed performance analysis
const queryLatency = new Trend('query_latency', true);
const hybridLatency = new Trend('hybrid_latency', true);
const streamingLatency = new Trend('streaming_latency', true);
const ingestionLatency = new Trend('ingestion_latency', true);
const errorRate = new Rate('errors');
const timeoutRate = new Rate('timeouts');
const successfulQueries = new Counter('successful_queries');

// Test configuration with multiple load profiles
export const options = {
  scenarios: {
    // Baseline performance test
    baseline_load: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '2m', target: 50 },   // Gradual ramp to 50 users
        { duration: '5m', target: 50 },   // Sustain 50 users
        { duration: '2m', target: 0 },    // Ramp down
      ],
      gracefulRampDown: '30s',
      tags: { test_type: 'baseline' },
    },

    // Target performance test
    target_load: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '3m', target: 100 },  // Ramp to target 100 users
        { duration: '10m', target: 100 }, // Sustain target load
        { duration: '2m', target: 150 },  // Brief spike test
        { duration: '3m', target: 150 },  // Sustain spike
        { duration: '2m', target: 0 },    // Ramp down
      ],
      gracefulRampDown: '60s',
      tags: { test_type: 'target' },
    },

    // Stress test - beyond normal capacity
    stress_test: {
      executor: 'ramping-vus',
      startVUs: 100,
      stages: [
        { duration: '2m', target: 200 },  // Quick ramp to stress level
        { duration: '5m', target: 300 },  // Push to stress limit
        { duration: '2m', target: 500 },  // Maximum stress
        { duration: '3m', target: 500 },  // Sustain maximum
        { duration: '3m', target: 0 },    // Recovery ramp down
      ],
      gracefulRampDown: '60s',
      tags: { test_type: 'stress' },
    }
  },

  // Performance thresholds - tests fail if these are exceeded
  thresholds: {
    // Latency requirements
    'http_req_duration': ['p(95)<50'],        // 95th percentile under 50ms
    'http_req_duration{name:query_basic}': ['p(95)<30'],     // Basic queries faster
    'http_req_duration{name:query_hybrid}': ['p(95)<75'],    // Hybrid queries moderate
    'http_req_duration{name:query_streaming}': ['p(95)<100'], // Streaming queries slower

    // Reliability requirements
    'http_req_failed': ['rate<0.01'],         // Less than 1% errors
    'errors': ['rate<0.01'],                  // Custom error tracking
    'timeouts': ['rate<0.005'],               // Less than 0.5% timeouts

    // Custom metric thresholds
    'query_latency': ['p(95)<50', 'p(99)<100'],
    'hybrid_latency': ['p(95)<75'],
    'streaming_latency': ['p(95)<100'],
    'ingestion_latency': ['p(95)<200'],
  },
};

// Test data configuration
const testQueries = {
  technical: [
    'What is vector similarity search and how does it work?',
    'Explain the architecture of retrieval-augmented generation systems',
    'How do embedding models transform text into vectors?',
    'What are the trade-offs between dense and sparse retrieval methods?',
    'How to optimize RAG system performance for production use?',
    'What are best practices for document chunking in RAG systems?',
    'Explain hybrid search approaches and their benefits',
    'How to implement context-aware retrieval systems?',
    'What metrics should be used to evaluate retrieval quality?',
    'How to handle multi-modal data in vector databases?'
  ],
  business: [
    'What is the ROI of implementing RAG systems in enterprise?',
    'How to scale knowledge management with AI-powered search?',
    'What are compliance considerations for enterprise AI systems?',
    'How to ensure data privacy in retrieval-augmented systems?',
    'What infrastructure costs should be expected for production RAG?',
    'How to manage change when implementing AI search systems?',
    'What training is needed for teams adopting RAG technology?',
    'How to measure business impact of intelligent search systems?',
    'What are common implementation challenges and solutions?',
    'How to integrate RAG with existing enterprise systems?'
  ],
  operational: [
    'How to monitor RAG system health and performance?',
    'What alerting should be configured for production systems?',
    'How to debug and troubleshoot poor search results?',
    'What backup and disaster recovery procedures are needed?',
    'How to perform rolling updates on knowledge bases?',
    'What are effective caching strategies for retrieval systems?',
    'How to handle system failures and graceful degradation?',
    'What security measures should be implemented for RAG?',
    'How to optimize memory and compute resource usage?',
    'What A/B testing approaches work for search systems?'
  ]
};

const documentTemplates = [
  'Technical documentation covering {topic} with detailed implementation guidelines and architectural considerations.',
  'Business strategy guide for {topic} including ROI analysis, risk assessment, and implementation roadmap.',
  'Operational playbook for {topic} with monitoring procedures, troubleshooting guides, and maintenance schedules.',
  'Research findings on {topic} presenting experimental methodology, data analysis, and practical conclusions.',
  'Training material explaining {topic} with step-by-step tutorials, examples, and practical exercises.',
  'Compliance documentation for {topic} covering regulatory requirements, audit procedures, and governance frameworks.'
];

const topics = [
  'artificial intelligence', 'machine learning', 'data engineering', 'cloud computing',
  'system architecture', 'performance optimization', 'security protocols', 'API design',
  'data analytics', 'automation systems', 'microservices', 'database optimization',
  'network security', 'scalability patterns', 'monitoring systems', 'DevOps practices'
];

// Helper functions
function getRandomQuery() {
  const categories = Object.keys(testQueries);
  const category = randomItem(categories);
  return randomItem(testQueries[category]);
}

function generateTestDocument() {
  const template = randomItem(documentTemplates);
  const topic = randomItem(topics);
  return {
    id: `k6_test_${Date.now()}_${randomIntBetween(1000, 9999)}`,
    content: template.replace('{topic}', topic),
    metadata: {
      source: 'k6_load_test',
      category: randomItem(Object.keys(testQueries)),
      timestamp: Date.now(),
      test_run: __ENV.TEST_RUN_ID || 'unknown'
    }
  };
}

function validateResponse(response, expectedFields = []) {
  const checks = {
    'status is 200': (r) => r.status === 200,
    'response time acceptable': (r) => r.timings.duration < 5000, // 5s timeout
    'response has body': (r) => r.body && r.body.length > 0,
  };

  // Add field-specific checks
  if (expectedFields.length > 0) {
    checks['has required fields'] = (r) => {
      try {
        const data = JSON.parse(r.body);
        return expectedFields.every(field => field in data);
      } catch (e) {
        return false;
      }
    };
  }

  const result = check(response, checks);

  if (!result) {
    errorRate.add(1);
  }

  if (response.timings.duration > 5000) {
    timeoutRate.add(1);
  }

  return result;
}

// Main test function - executed by each virtual user
export default function () {
  // User session setup
  const baseUrl = __ENV.BASE_URL || 'http://localhost:8000';
  const headers = { 'Content-Type': 'application/json' };

  // Weight different operations to simulate realistic usage
  const operationType = randomIntBetween(1, 100);

  if (operationType <= 50) {
    // 50% - Basic queries (most common)
    group('Basic Query', () => {
      const query = getRandomQuery();
      const start = Date.now();

      const response = http.post(`${baseUrl}/query`, JSON.stringify({
        query: query,
        retrieval_config: {
          top_k: 5,
          retrieval_mode: 'dense'
        }
      }), {
        headers: headers,
        tags: { name: 'query_basic' },
        timeout: '10s'
      });

      const latency = Date.now() - start;
      queryLatency.add(latency);

      if (validateResponse(response, ['answer', 'sources', 'metadata'])) {
        successfulQueries.add(1);
      }
    });

  } else if (operationType <= 75) {
    // 25% - Hybrid queries (moderate complexity)
    group('Hybrid Query', () => {
      const query = getRandomQuery();
      const start = Date.now();

      const response = http.post(`${baseUrl}/query`, JSON.stringify({
        query: query,
        retrieval_config: {
          top_k: 10,
          retrieval_mode: 'hybrid',
          rerank: true,
          alpha: 0.7
        }
      }), {
        headers: headers,
        tags: { name: 'query_hybrid' },
        timeout: '15s'
      });

      const latency = Date.now() - start;
      hybridLatency.add(latency);

      if (validateResponse(response, ['answer', 'sources', 'metadata'])) {
        successfulQueries.add(1);
      }
    });

  } else if (operationType <= 85) {
    // 10% - Streaming queries (resource intensive)
    group('Streaming Query', () => {
      const query = getRandomQuery();
      const start = Date.now();

      const response = http.post(`${baseUrl}/query/stream`, JSON.stringify({
        query: query,
        generation_config: {
          stream: true,
          max_tokens: 300,
          temperature: 0.7
        },
        retrieval_config: { top_k: 5 }
      }), {
        headers: headers,
        tags: { name: 'query_streaming' },
        timeout: '30s'
      });

      const latency = Date.now() - start;
      streamingLatency.add(latency);

      // Streaming responses have different validation
      const streamingChecks = check(response, {
        'status is 200': (r) => r.status === 200,
        'is streaming response': (r) => r.headers['Content-Type'] &&
          r.headers['Content-Type'].includes('stream'),
      });

      if (!streamingChecks) {
        errorRate.add(1);
      }
    });

  } else if (operationType <= 95) {
    // 10% - Document ingestion (background load)
    group('Document Ingestion', () => {
      const document = generateTestDocument();
      const start = Date.now();

      const response = http.post(`${baseUrl}/ingest`, JSON.stringify({
        documents: [document]
      }), {
        headers: headers,
        tags: { name: 'ingest_document' },
        timeout: '20s'
      });

      const latency = Date.now() - start;
      ingestionLatency.add(latency);

      validateResponse(response, ['status']);
    });

  } else {
    // 5% - Health checks and batch operations
    group('System Operations', () => {
      // Health check
      const healthResponse = http.get(`${baseUrl}/health`, {
        tags: { name: 'health_check' },
        timeout: '5s'
      });

      check(healthResponse, {
        'health check successful': (r) => r.status === 200,
      });

      // Batch query (if time permits)
      if (randomIntBetween(1, 2) === 1) {
        const queries = [getRandomQuery(), getRandomQuery(), getRandomQuery()];

        const batchResponse = http.post(`${baseUrl}/query/batch`, JSON.stringify({
          queries: queries,
          retrieval_config: { top_k: 3 }
        }), {
          headers: headers,
          tags: { name: 'batch_query' },
          timeout: '25s'
        });

        validateResponse(batchResponse);
      }
    });
  }

  // Variable sleep time to simulate realistic user behavior
  sleep(randomIntBetween(1, 4));
}

// Setup function - runs once at test start
export function setup() {
  console.log('Starting K6 load test for RAG API');
  console.log(`Target URL: ${__ENV.BASE_URL || 'http://localhost:8000'}`);
  console.log(`Test configuration: ${JSON.stringify(options.scenarios)}`);

  // Verify API is available
  const baseUrl = __ENV.BASE_URL || 'http://localhost:8000';
  const response = http.get(`${baseUrl}/health`);

  if (response.status !== 200) {
    throw new Error(`API not available: ${response.status} ${response.body}`);
  }

  console.log('API health check passed - starting load test');
  return { startTime: Date.now() };
}

// Teardown function - runs once at test end
export function teardown(data) {
  const testDuration = (Date.now() - data.startTime) / 1000;
  console.log(`Load test completed in ${testDuration.toFixed(1)}s`);
}

// Handle summary data for custom reporting
export function handleSummary(data) {
  return {
    'load_test_summary.json': JSON.stringify(data, null, 2),
    'stdout': createTextSummary(data)
  };
}

function createTextSummary(data) {
  const summary = `
K6 Load Test Summary
===================

Test Duration: ${data.state.testRunDurationMs / 1000}s
Virtual Users: ${data.metrics.vus.values.max}

Performance Metrics:
- HTTP Request Duration (p95): ${data.metrics.http_req_duration.values['p(95)'].toFixed(1)}ms
- HTTP Request Duration (p99): ${data.metrics.http_req_duration.values['p(99)'].toFixed(1)}ms
- HTTP Request Failed Rate: ${(data.metrics.http_req_failed.values.rate * 100).toFixed(2)}%

Custom Metrics:
- Query Latency (p95): ${data.metrics.query_latency?.values['p(95)']?.toFixed(1) || 'N/A'}ms
- Successful Queries: ${data.metrics.successful_queries?.values.count || 'N/A'}
- Error Rate: ${((data.metrics.errors?.values.rate || 0) * 100).toFixed(2)}%

Thresholds:
${Object.entries(data.thresholds || {}).map(([name, threshold]) =>
  `- ${name}: ${threshold.ok ? '✅ PASS' : '❌ FAIL'}`
).join('\n')}
`;

  return summary;
}