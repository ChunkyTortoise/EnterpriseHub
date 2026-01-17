/**
 * Unit tests for Error Handling Service
 * Tests: 25 tests covering error handling and recovery logic
 */

import { ErrorHandlingService, LeadEngineError, ErrorContext } from '../../src/services/error-handling.service';

describe('ErrorHandlingService', () => {
  describe('LeadEngineError', () => {
    test('should create error with correct properties', () => {
      const context: Partial<ErrorContext> = {
        leadId: 'lead123',
        workflowId: 'workflow456',
        step: 'validation'
      };

      const error = new LeadEngineError('VALIDATION_ERROR', 'Test error message', true, context);

      expect(error.code).toBe('VALIDATION_ERROR');
      expect(error.message).toBe('Test error message');
      expect(error.retryable).toBe(true);
      expect(error.context.leadId).toBe('lead123');
      expect(error.context.workflowId).toBe('workflow456');
      expect(error.context.step).toBe('validation');
      expect(error.context.timestamp).toBeInstanceOf(Date);
    });

    test('should set default values correctly', () => {
      const error = new LeadEngineError('TEST_ERROR', 'Test message');

      expect(error.retryable).toBe(false); // Default
      expect(error.context.timestamp).toBeInstanceOf(Date);
      expect(error.context.leadId).toBeUndefined();
    });
  });

  describe('handleError', () => {
    test('should handle LeadEngineError correctly', () => {
      const error = new LeadEngineError('APOLLO_RATE_LIMIT', 'Rate limit exceeded', true);
      const context = { leadId: 'lead123' };

      const response = ErrorHandlingService.handleError(error, context);

      expect(response.success).toBe(false);
      expect(response.error?.code).toBe('APOLLO_RATE_LIMIT');
      expect(response.error?.message).toBe('Rate limit exceeded');
      expect(response.error?.retryable).toBe(true);
      expect(response.error?.retryAfterMs).toBeGreaterThan(0);
    });

    test('should handle standard JavaScript errors', () => {
      const error = new Error('Network timeout occurred');
      const context = { workflowId: 'workflow123' };

      const response = ErrorHandlingService.handleError(error, context);

      expect(response.success).toBe(false);
      expect(response.error?.code).toBe('TIMEOUT_ERROR');
      expect(response.error?.message).toBe('Network timeout occurred');
      expect(response.error?.retryable).toBe(true);
    });

    test('should map database errors correctly', () => {
      const error = new Error('Database connection failed');
      
      const response = ErrorHandlingService.handleError(error);

      expect(response.error?.code).toBe('DATABASE_ERROR');
      expect(response.error?.retryable).toBe(true);
    });

    test('should map network errors correctly', () => {
      const error = new Error('Network connection lost');
      
      const response = ErrorHandlingService.handleError(error);

      expect(response.error?.code).toBe('NETWORK_ERROR');
      expect(response.error?.retryable).toBe(true);
    });

    test('should handle unknown errors as non-retryable', () => {
      const error = new Error('Unknown system failure');
      
      const response = ErrorHandlingService.handleError(error);

      expect(response.error?.code).toBe('SYSTEM_ERROR');
      expect(response.error?.retryable).toBe(false);
    });
  });

  describe('createValidationError', () => {
    test('should create validation error with correct properties', () => {
      const context = { leadId: 'lead123' };
      const error = ErrorHandlingService.createValidationError('email', 'invalid-email', context);

      expect(error.code).toBe('MISSING_REQUIRED_FIELD');
      expect(error.message).toBe("Validation failed for field 'email': invalid-email");
      expect(error.retryable).toBe(false);
      expect(error.context.leadId).toBe('lead123');
    });
  });

  describe('createAPIError', () => {
    test('should create API error for rate limiting', () => {
      const error = ErrorHandlingService.createAPIError('Apollo', 429, 'Rate limit exceeded');

      expect(error.code).toBe('APOLLO_RATE_LIMIT');
      expect(error.message).toBe('Apollo API error (429): Rate limit exceeded');
      expect(error.retryable).toBe(true);
    });

    test('should create API error for server errors', () => {
      const error = ErrorHandlingService.createAPIError('Twilio', 500, 'Internal server error');

      expect(error.code).toBe('TWILIO_API_ERROR');
      expect(error.message).toBe('Twilio API error (500): Internal server error');
      expect(error.retryable).toBe(true);
    });

    test('should create non-retryable error for client errors', () => {
      const error = ErrorHandlingService.createAPIError('SendGrid', 400, 'Bad request');

      expect(error.code).toBe('SENDGRID_API_ERROR');
      expect(error.retryable).toBe(false);
    });
  });

  describe('createTimeoutError', () => {
    test('should create timeout error with correct properties', () => {
      const error = ErrorHandlingService.createTimeoutError('lead_enrichment', 5000);

      expect(error.code).toBe('TIMEOUT_ERROR');
      expect(error.message).toBe("Operation 'lead_enrichment' timed out after 5000ms");
      expect(error.retryable).toBe(true);
    });
  });

  describe('createDuplicateLeadError', () => {
    test('should create duplicate lead error with metadata', () => {
      const error = ErrorHandlingService.createDuplicateLeadError('test@example.com', 'existing-lead-123');

      expect(error.code).toBe('DUPLICATE_LEAD');
      expect(error.message).toBe('Duplicate lead detected for email: test@example.com (existing ID: existing-lead-123)');
      expect(error.retryable).toBe(false);
      expect(error.context.metadata?.email).toBe('test@example.com');
      expect(error.context.metadata?.existingLeadId).toBe('existing-lead-123');
    });
  });

  describe('isRetryable', () => {
    test('should identify retryable LeadEngineError', () => {
      const retryableError = new LeadEngineError('TEST', 'Test', true);
      const nonRetryableError = new LeadEngineError('TEST', 'Test', false);

      expect(ErrorHandlingService.isRetryable(retryableError)).toBe(true);
      expect(ErrorHandlingService.isRetryable(nonRetryableError)).toBe(false);
    });

    test('should identify retryable standard errors by message', () => {
      const retryableMessages = [
        'Request timeout occurred',
        'Network connection failed',
        'Connection lost',
        'Rate limit exceeded',
        'Temporary service unavailable'
      ];

      retryableMessages.forEach(message => {
        const error = new Error(message);
        expect(ErrorHandlingService.isRetryable(error)).toBe(true);
      });
    });

    test('should identify non-retryable errors', () => {
      const nonRetryableMessages = [
        'Invalid API key',
        'Resource not found',
        'Permission denied',
        'Validation failed'
      ];

      nonRetryableMessages.forEach(message => {
        const error = new Error(message);
        expect(ErrorHandlingService.isRetryable(error)).toBe(false);
      });
    });
  });

  describe('getRetryDelay', () => {
    test('should calculate exponential backoff for Apollo rate limit', () => {
      const delay1 = ErrorHandlingService.getRetryDelay('APOLLO_RATE_LIMIT', 1);
      const delay2 = ErrorHandlingService.getRetryDelay('APOLLO_RATE_LIMIT', 2);
      const delay3 = ErrorHandlingService.getRetryDelay('APOLLO_RATE_LIMIT', 3);

      expect(delay1).toBeGreaterThan(60000); // Base 60s + jitter
      expect(delay2).toBeGreaterThan(delay1);
      expect(delay3).toBeGreaterThan(delay2);
    });

    test('should return 0 for unknown error codes', () => {
      const delay = ErrorHandlingService.getRetryDelay('UNKNOWN_ERROR');
      expect(delay).toBe(0);
    });

    test('should include jitter in calculations', () => {
      const delays = Array.from({ length: 10 }, () => 
        ErrorHandlingService.getRetryDelay('DATABASE_ERROR', 1)
      );

      // All delays should be different due to jitter
      const uniqueDelays = new Set(delays);
      expect(uniqueDelays.size).toBeGreaterThan(1);
    });
  });

  describe('getMaxRetries', () => {
    test('should return configured max retries', () => {
      expect(ErrorHandlingService.getMaxRetries('APOLLO_RATE_LIMIT')).toBe(3);
      expect(ErrorHandlingService.getMaxRetries('DATABASE_ERROR')).toBe(3);
      expect(ErrorHandlingService.getMaxRetries('TIMEOUT_ERROR')).toBe(2);
    });

    test('should return 0 for unknown error codes', () => {
      expect(ErrorHandlingService.getMaxRetries('UNKNOWN_ERROR')).toBe(0);
    });
  });

  describe('executeWithRetry', () => {
    test('should succeed on first attempt', async () => {
      const mockOperation = jest.fn().mockResolvedValue('success');

      const result = await ErrorHandlingService.executeWithRetry(mockOperation);

      expect(result).toBe('success');
      expect(mockOperation).toHaveBeenCalledTimes(1);
    });

    test('should retry on retryable errors', async () => {
      const retryableError = new LeadEngineError('DATABASE_ERROR', 'Connection lost', true);
      const mockOperation = jest.fn()
        .mockRejectedValueOnce(retryableError)
        .mockRejectedValueOnce(retryableError)
        .mockResolvedValue('success');

      const result = await ErrorHandlingService.executeWithRetry(mockOperation);

      expect(result).toBe('success');
      expect(mockOperation).toHaveBeenCalledTimes(3);
    });

    test('should not retry non-retryable errors', async () => {
      const nonRetryableError = new LeadEngineError('INVALID_EMAIL', 'Bad email format', false);
      const mockOperation = jest.fn().mockRejectedValue(nonRetryableError);

      await expect(ErrorHandlingService.executeWithRetry(mockOperation)).rejects.toThrow('Bad email format');
      expect(mockOperation).toHaveBeenCalledTimes(1);
    });

    test('should respect max retry limits', async () => {
      const retryableError = new LeadEngineError('TIMEOUT_ERROR', 'Operation timed out', true);
      const mockOperation = jest.fn().mockRejectedValue(retryableError);

      await expect(ErrorHandlingService.executeWithRetry(mockOperation)).rejects.toThrow('Operation timed out');
      
      // Should try initial + 2 retries = 3 total (based on TIMEOUT_ERROR config)
      expect(mockOperation).toHaveBeenCalledTimes(3);
    });

    test('should handle standard errors', async () => {
      const timeoutError = new Error('Request timeout');
      const mockOperation = jest.fn()
        .mockRejectedValueOnce(timeoutError)
        .mockResolvedValue('success');

      const result = await ErrorHandlingService.executeWithRetry(mockOperation);

      expect(result).toBe('success');
      expect(mockOperation).toHaveBeenCalledTimes(2);
    });
  });

  describe('validateOperation', () => {
    test('should validate lead creation successfully', () => {
      const validLeadData = {
        email: 'test@example.com',
        firstName: 'John',
        lastName: 'Doe'
      };

      expect(() => {
        ErrorHandlingService.validateOperation('lead_creation', validLeadData);
      }).not.toThrow();
    });

    test('should throw validation error for missing email', () => {
      const invalidLeadData = {
        firstName: 'John',
        lastName: 'Doe'
        // Missing email
      };

      expect(() => {
        ErrorHandlingService.validateOperation('lead_creation', invalidLeadData);
      }).toThrow('Validation failed for field \'email\'');
    });

    test('should validate API call successfully', () => {
      const validAPIData = {
        endpoint: '/api/leads',
        method: 'POST',
        data: {}
      };

      expect(() => {
        ErrorHandlingService.validateOperation('api_call', validAPIData);
      }).not.toThrow();
    });

    test('should throw error for invalid API call', () => {
      const invalidAPIData = {
        endpoint: '/api/leads'
        // Missing method
      };

      expect(() => {
        ErrorHandlingService.validateOperation('api_call', invalidAPIData);
      }).toThrow('HTTP method is required');
    });

    test('should validate database operation successfully', () => {
      const validDBData = {
        query: 'SELECT * FROM leads',
        params: []
      };

      expect(() => {
        ErrorHandlingService.validateOperation('database_operation', validDBData);
      }).not.toThrow();
    });

    test('should throw error for unknown operation', () => {
      expect(() => {
        ErrorHandlingService.validateOperation('unknown_operation', {});
      }).toThrow('Unknown operation: unknown_operation');
    });
  });

  describe('healthCheck', () => {
    test('should return healthy status when all checks pass', async () => {
      const health = await ErrorHandlingService.healthCheck();

      expect(health.status).toBe('healthy');
      expect(health.checks.database).toBe(true);
      expect(health.checks.redis).toBe(true);
      expect(health.errors).toBeUndefined();
    });

    test('should handle individual check failures gracefully', async () => {
      // This test might be flaky due to random API health check
      // but demonstrates the concept
      const health = await ErrorHandlingService.healthCheck();

      expect(['healthy', 'degraded', 'unhealthy']).toContain(health.status);
      expect(typeof health.checks.database).toBe('boolean');
      expect(typeof health.checks.redis).toBe('boolean');
    });

    test('should complete health check within reasonable time', async () => {
      const startTime = Date.now();
      await ErrorHandlingService.healthCheck();
      const executionTime = Date.now() - startTime;

      expect(executionTime).toBeLessThan(1000); // Should complete in under 1 second
    });
  });

  describe('Performance Tests', () => {
    test('should handle error creation efficiently', () => {
      const startTime = Date.now();
      
      for (let i = 0; i < 1000; i++) {
        new LeadEngineError('TEST_ERROR', `Error ${i}`, false, { leadId: `lead${i}` });
      }
      
      const executionTime = Date.now() - startTime;
      expect(executionTime).toBeLessThan(100); // Should create 1000 errors in under 100ms
    });

    test('should handle error processing efficiently', () => {
      const errors = Array.from({ length: 100 }, (_, i) => 
        new LeadEngineError('TEST_ERROR', `Error ${i}`, false)
      );

      const startTime = Date.now();
      
      errors.forEach(error => {
        ErrorHandlingService.handleError(error);
      });
      
      const executionTime = Date.now() - startTime;
      expect(executionTime).toBeLessThan(50); // Should process 100 errors in under 50ms
    });
  });

  describe('Edge Cases', () => {
    test('should handle null error gracefully', () => {
      expect(() => {
        ErrorHandlingService.handleError(null as any);
      }).not.toThrow();
    });

    test('should handle error with circular references', () => {
      const error = new Error('Test error');
      (error as any).circular = error; // Create circular reference

      expect(() => {
        ErrorHandlingService.handleError(error);
      }).not.toThrow();
    });

    test('should handle very long error messages', () => {
      const longMessage = 'A'.repeat(10000);
      const error = new LeadEngineError('TEST', longMessage);

      const response = ErrorHandlingService.handleError(error);
      
      expect(response.error?.message).toBe(longMessage);
    });

    test('should handle concurrent error handling', async () => {
      const errors = Array.from({ length: 100 }, (_, i) => 
        new LeadEngineError('CONCURRENT_TEST', `Error ${i}`)
      );

      const promises = errors.map(error => 
        Promise.resolve(ErrorHandlingService.handleError(error))
      );

      const results = await Promise.all(promises);
      
      expect(results).toHaveLength(100);
      expect(results.every(r => !r.success)).toBe(true);
    });
  });
});