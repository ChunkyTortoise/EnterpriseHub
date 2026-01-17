/**
 * Test environment configuration
 * Sets up environment variables and configurations for testing
 */

// Database configuration for testing
process.env.DATABASE_URL = process.env.TEST_DATABASE_URL || 'postgresql://test:test@localhost:5433/test_lead_recovery';
process.env.REDIS_URL = process.env.TEST_REDIS_URL || 'redis://localhost:6380';

// n8n configuration
process.env.N8N_WEBHOOK_URL = 'http://localhost:5678/webhook-test';
process.env.N8N_API_KEY = 'test-api-key';

// External API configuration (mock endpoints)
process.env.APOLLO_API_KEY = 'test-apollo-key';
process.env.APOLLO_BASE_URL = 'https://api.apollo.io/v1';

process.env.TWILIO_ACCOUNT_SID = 'test-twilio-sid';
process.env.TWILIO_AUTH_TOKEN = 'test-twilio-token';
process.env.TWILIO_PHONE_NUMBER = '+15551234567';

process.env.SENDGRID_API_KEY = 'test-sendgrid-key';
process.env.SENDGRID_FROM_EMAIL = 'test@example.com';

process.env.GHL_API_KEY = 'test-ghl-key';
process.env.GHL_LOCATION_ID = 'test-location-id';

process.env.HUBSPOT_ACCESS_TOKEN = 'test-hubspot-token';

// Application configuration
process.env.NODE_ENV = 'test';
process.env.LOG_LEVEL = 'error'; // Reduce log noise in tests
process.env.LEAD_RESPONSE_SLA_SECONDS = '60'; // 60-second SLA for testing

// Performance thresholds for testing
process.env.MAX_RESPONSE_TIME_MS = '1000';
process.env.MAX_DATABASE_QUERY_TIME_MS = '500';
process.env.MAX_API_CALL_TIME_MS = '2000';

// Test-specific flags
process.env.ENABLE_TEST_METRICS = 'true';
process.env.MOCK_EXTERNAL_APIS = 'true';
process.env.ENABLE_PERFORMANCE_MONITORING = 'true';