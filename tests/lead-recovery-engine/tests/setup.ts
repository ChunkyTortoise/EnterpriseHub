/**
 * Global test setup and configuration
 * Sets up testing environment and global utilities
 */

import { jest } from '@jest/globals';

// Set test timeout globally
jest.setTimeout(30000);

// Mock environment variables
process.env.NODE_ENV = 'test';
process.env.DATABASE_URL = 'postgresql://test:test@localhost:5433/test_lead_recovery';
process.env.REDIS_URL = 'redis://localhost:6380';
process.env.N8N_WEBHOOK_URL = 'http://localhost:5678/webhook';

// Global test utilities
global.testUtils = {
  // Async delay utility
  delay: (ms: number) => new Promise(resolve => setTimeout(resolve, ms)),
  
  // Random test data generators
  generateRandomEmail: () => `test-${Date.now()}-${Math.random().toString(36).substring(7)}@example.com`,
  generateRandomPhone: () => `+1${Math.floor(1000000000 + Math.random() * 9000000000)}`,
  generateRandomUUID: () => require('crypto').randomUUID(),
  
  // Test performance measurement
  measureExecutionTime: async (fn: () => Promise<any>) => {
    const start = Date.now();
    await fn();
    return Date.now() - start;
  }
};

// Global error handler for unhandled promises
process.on('unhandledRejection', (reason, promise) => {
  console.error('Unhandled Rejection at:', promise, 'reason:', reason);
});

// Increase Node.js memory limit for tests
if (process.env.NODE_OPTIONS && !process.env.NODE_OPTIONS.includes('--max-old-space-size')) {
  process.env.NODE_OPTIONS = `${process.env.NODE_OPTIONS} --max-old-space-size=4096`;
}

// Configure console for test environment
const originalConsoleError = console.error;
console.error = (...args: any[]) => {
  if (typeof args[0] === 'string' && args[0].includes('Warning: ')) {
    return; // Suppress React warnings in tests
  }
  originalConsoleError.apply(console, args);
};

// Global beforeEach and afterEach for all tests
beforeEach(async () => {
  // Clear all timers
  jest.clearAllTimers();
  jest.clearAllMocks();
});

afterEach(async () => {
  // Cleanup after each test
  jest.restoreAllMocks();
});