/**
 * Error handling service for the Lead Recovery Engine
 * Provides centralized error handling, logging, and recovery mechanisms
 */

export interface ErrorContext {
  leadId?: string;
  workflowId?: string;
  step?: string;
  timestamp: Date;
  userId?: string;
  metadata?: Record<string, any>;
}

export interface ErrorResponse {
  success: boolean;
  error?: {
    code: string;
    message: string;
    details?: any;
    retryable: boolean;
    retryAfterMs?: number;
  };
}

export class LeadEngineError extends Error {
  public readonly code: string;
  public readonly retryable: boolean;
  public readonly context: ErrorContext;

  constructor(code: string, message: string, retryable = false, context: Partial<ErrorContext> = {}) {
    super(message);
    this.name = 'LeadEngineError';
    this.code = code;
    this.retryable = retryable;
    this.context = {
      timestamp: new Date(),
      ...context
    };
  }
}

export class ErrorHandlingService {
  private static readonly ERROR_CODES = {
    // Validation errors (non-retryable)
    INVALID_EMAIL: 'INVALID_EMAIL',
    INVALID_PHONE: 'INVALID_PHONE',
    MISSING_REQUIRED_FIELD: 'MISSING_REQUIRED_FIELD',
    DUPLICATE_LEAD: 'DUPLICATE_LEAD',
    
    // External API errors (retryable)
    APOLLO_RATE_LIMIT: 'APOLLO_RATE_LIMIT',
    APOLLO_API_ERROR: 'APOLLO_API_ERROR',
    TWILIO_ERROR: 'TWILIO_ERROR',
    SENDGRID_ERROR: 'SENDGRID_ERROR',
    GHL_ERROR: 'GHL_ERROR',
    HUBSPOT_ERROR: 'HUBSPOT_ERROR',
    
    // System errors (some retryable)
    DATABASE_ERROR: 'DATABASE_ERROR',
    REDIS_ERROR: 'REDIS_ERROR',
    NETWORK_ERROR: 'NETWORK_ERROR',
    TIMEOUT_ERROR: 'TIMEOUT_ERROR',
    
    // Workflow errors
    WORKFLOW_EXECUTION_ERROR: 'WORKFLOW_EXECUTION_ERROR',
    N8N_WEBHOOK_ERROR: 'N8N_WEBHOOK_ERROR',
    
    // Business logic errors
    LEAD_SCORING_ERROR: 'LEAD_SCORING_ERROR',
    ENRICHMENT_ERROR: 'ENRICHMENT_ERROR',
    COMMUNICATION_ERROR: 'COMMUNICATION_ERROR'
  };

  private static readonly RETRY_CONFIGS = {
    [this.ERROR_CODES.APOLLO_RATE_LIMIT]: { maxRetries: 3, backoffMs: 60000 },
    [this.ERROR_CODES.APOLLO_API_ERROR]: { maxRetries: 2, backoffMs: 5000 },
    [this.ERROR_CODES.DATABASE_ERROR]: { maxRetries: 3, backoffMs: 1000 },
    [this.ERROR_CODES.NETWORK_ERROR]: { maxRetries: 3, backoffMs: 2000 },
    [this.ERROR_CODES.TIMEOUT_ERROR]: { maxRetries: 2, backoffMs: 5000 }
  };

  /**
   * Handles errors with appropriate logging and response formatting
   */
  static handleError(error: Error | LeadEngineError, context: Partial<ErrorContext> = {}): ErrorResponse {
    const timestamp = new Date();
    const errorContext: ErrorContext = {
      timestamp,
      ...context
    };

    if (error instanceof LeadEngineError) {
      this.logError(error, errorContext);
      
      return {
        success: false,
        error: {
          code: error.code,
          message: error.message,
          retryable: error.retryable,
          retryAfterMs: this.getRetryDelay(error.code)
        }
      };
    }

    // Handle standard JavaScript errors
    const mappedError = this.mapStandardError(error, errorContext);
    this.logError(mappedError, errorContext);

    return {
      success: false,
      error: {
        code: mappedError.code,
        message: mappedError.message,
        retryable: mappedError.retryable,
        retryAfterMs: this.getRetryDelay(mappedError.code)
      }
    };
  }

  /**
   * Creates specific error types for common scenarios
   */
  static createValidationError(field: string, value: any, context: Partial<ErrorContext> = {}): LeadEngineError {
    return new LeadEngineError(
      this.ERROR_CODES.MISSING_REQUIRED_FIELD,
      `Validation failed for field '${field}': ${value}`,
      false,
      context
    );
  }

  static createAPIError(service: string, statusCode: number, message: string, context: Partial<ErrorContext> = {}): LeadEngineError {
    const code = this.mapAPIErrorCode(service, statusCode);
    const retryable = this.isRetryableStatusCode(statusCode);
    
    return new LeadEngineError(
      code,
      `${service} API error (${statusCode}): ${message}`,
      retryable,
      context
    );
  }

  static createTimeoutError(operation: string, timeoutMs: number, context: Partial<ErrorContext> = {}): LeadEngineError {
    return new LeadEngineError(
      this.ERROR_CODES.TIMEOUT_ERROR,
      `Operation '${operation}' timed out after ${timeoutMs}ms`,
      true,
      context
    );
  }

  static createDuplicateLeadError(email: string, existingLeadId: string, context: Partial<ErrorContext> = {}): LeadEngineError {
    return new LeadEngineError(
      this.ERROR_CODES.DUPLICATE_LEAD,
      `Duplicate lead detected for email: ${email} (existing ID: ${existingLeadId})`,
      false,
      { ...context, metadata: { email, existingLeadId } }
    );
  }

  /**
   * Determines if an error is retryable and calculates retry delay
   */
  static isRetryable(error: Error | LeadEngineError): boolean {
    if (error instanceof LeadEngineError) {
      return error.retryable;
    }

    // Check for common retryable error patterns
    const message = error.message.toLowerCase();
    return (
      message.includes('timeout') ||
      message.includes('network') ||
      message.includes('connection') ||
      message.includes('rate limit') ||
      message.includes('temporary')
    );
  }

  static getRetryDelay(errorCode: string, attempt = 1): number {
    const config = this.RETRY_CONFIGS[errorCode];
    if (!config) return 0;

    // Exponential backoff with jitter
    const baseDelay = config.backoffMs;
    const exponentialDelay = baseDelay * Math.pow(2, attempt - 1);
    const jitter = Math.random() * 1000; // Up to 1 second jitter
    
    return exponentialDelay + jitter;
  }

  static getMaxRetries(errorCode: string): number {
    const config = this.RETRY_CONFIGS[errorCode];
    return config?.maxRetries || 0;
  }

  /**
   * Executes operation with automatic retry logic
   */
  static async executeWithRetry<T>(
    operation: () => Promise<T>,
    context: Partial<ErrorContext> = {}
  ): Promise<T> {
    let lastError: Error | LeadEngineError;
    let attempt = 1;

    while (attempt <= 3) { // Default max attempts
      try {
        return await operation();
      } catch (error) {
        lastError = error as Error;
        
        if (!this.isRetryable(lastError)) {
          throw lastError;
        }

        const errorCode = error instanceof LeadEngineError 
          ? error.code 
          : 'UNKNOWN_ERROR';
          
        const maxRetries = this.getMaxRetries(errorCode);
        
        if (attempt >= maxRetries + 1) {
          throw lastError;
        }

        const delay = this.getRetryDelay(errorCode, attempt);
        await this.sleep(delay);
        
        attempt++;
      }
    }

    throw lastError!;
  }

  /**
   * Validates operation safety and throws appropriate errors
   */
  static validateOperation(operation: string, data: any, context: Partial<ErrorContext> = {}): void {
    switch (operation) {
      case 'lead_creation':
        this.validateLeadCreation(data, context);
        break;
      case 'api_call':
        this.validateAPICall(data, context);
        break;
      case 'database_operation':
        this.validateDatabaseOperation(data, context);
        break;
      default:
        throw new LeadEngineError(
          'INVALID_OPERATION',
          `Unknown operation: ${operation}`,
          false,
          context
        );
    }
  }

  /**
   * Monitors system health and preemptively handles issues
   */
  static async healthCheck(): Promise<{
    status: 'healthy' | 'degraded' | 'unhealthy';
    checks: Record<string, boolean>;
    errors?: string[];
  }> {
    const checks: Record<string, boolean> = {};
    const errors: string[] = [];

    try {
      // Database connectivity check
      checks.database = await this.checkDatabaseHealth();
    } catch (error) {
      checks.database = false;
      errors.push(`Database health check failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }

    try {
      // Redis connectivity check
      checks.redis = await this.checkRedisHealth();
    } catch (error) {
      checks.redis = false;
      errors.push(`Redis health check failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }

    try {
      // External API health checks
      checks.apollo = await this.checkExternalAPIHealth('apollo');
      checks.twilio = await this.checkExternalAPIHealth('twilio');
      checks.sendgrid = await this.checkExternalAPIHealth('sendgrid');
    } catch (error) {
      checks.apollo = false;
      checks.twilio = false;
      checks.sendgrid = false;
      errors.push(`External API health check failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }

    const healthyChecks = Object.values(checks).filter(Boolean).length;
    const totalChecks = Object.keys(checks).length;
    
    let status: 'healthy' | 'degraded' | 'unhealthy';
    if (healthyChecks === totalChecks) {
      status = 'healthy';
    } else if (healthyChecks >= totalChecks * 0.6) {
      status = 'degraded';
    } else {
      status = 'unhealthy';
    }

    return { status, checks, errors: errors.length > 0 ? errors : undefined };
  }

  // Private helper methods

  private static logError(error: LeadEngineError, context: ErrorContext): void {
    const logData = {
      timestamp: context.timestamp.toISOString(),
      level: 'error',
      code: error.code,
      message: error.message,
      retryable: error.retryable,
      context: {
        leadId: context.leadId,
        workflowId: context.workflowId,
        step: context.step,
        userId: context.userId,
        metadata: context.metadata
      },
      stack: error.stack
    };

    // In production, this would send to logging service
    console.error('Lead Engine Error:', JSON.stringify(logData, null, 2));
  }

  private static mapStandardError(error: Error, context: ErrorContext): LeadEngineError {
    const message = error.message.toLowerCase();

    if (message.includes('timeout')) {
      return new LeadEngineError(this.ERROR_CODES.TIMEOUT_ERROR, error.message, true, context);
    }

    if (message.includes('network') || message.includes('connection')) {
      return new LeadEngineError(this.ERROR_CODES.NETWORK_ERROR, error.message, true, context);
    }

    if (message.includes('database') || message.includes('sql')) {
      return new LeadEngineError(this.ERROR_CODES.DATABASE_ERROR, error.message, true, context);
    }

    // Default to non-retryable system error
    return new LeadEngineError('SYSTEM_ERROR', error.message, false, context);
  }

  private static mapAPIErrorCode(service: string, statusCode: number): string {
    const servicePrefix = service.toUpperCase();
    
    if (statusCode === 429) {
      return `${servicePrefix}_RATE_LIMIT`;
    }
    
    return `${servicePrefix}_API_ERROR`;
  }

  private static isRetryableStatusCode(statusCode: number): boolean {
    // Retryable HTTP status codes
    return [408, 429, 500, 502, 503, 504].includes(statusCode);
  }

  private static validateLeadCreation(data: any, context: Partial<ErrorContext>): void {
    if (!data.email) {
      throw this.createValidationError('email', data.email, context);
    }
    
    if (!data.firstName) {
      throw this.createValidationError('firstName', data.firstName, context);
    }
    
    if (!data.lastName) {
      throw this.createValidationError('lastName', data.lastName, context);
    }
  }

  private static validateAPICall(data: any, context: Partial<ErrorContext>): void {
    if (!data.endpoint) {
      throw new LeadEngineError('INVALID_API_CALL', 'API endpoint is required', false, context);
    }
    
    if (!data.method) {
      throw new LeadEngineError('INVALID_API_CALL', 'HTTP method is required', false, context);
    }
  }

  private static validateDatabaseOperation(data: any, context: Partial<ErrorContext>): void {
    if (!data.query && !data.operation) {
      throw new LeadEngineError('INVALID_DATABASE_OPERATION', 'Query or operation type is required', false, context);
    }
  }

  private static async sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  private static async checkDatabaseHealth(): Promise<boolean> {
    // Mock database health check
    return new Promise(resolve => {
      setTimeout(() => resolve(true), 10);
    });
  }

  private static async checkRedisHealth(): Promise<boolean> {
    // Mock Redis health check
    return new Promise(resolve => {
      setTimeout(() => resolve(true), 10);
    });
  }

  private static async checkExternalAPIHealth(service: string): Promise<boolean> {
    // Mock external API health check
    return new Promise(resolve => {
      setTimeout(() => resolve(Math.random() > 0.1), 10); // 90% success rate
    });
  }
}