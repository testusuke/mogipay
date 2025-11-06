// API Error Classes

import type { ApiError } from './types';

/**
 * Base API Error Class
 */
export class ApiClientError extends Error {
  public readonly statusCode: number;
  public readonly errorCode: string;
  public readonly details?: unknown;
  public readonly requestId?: string;

  constructor(
    message: string,
    statusCode: number,
    errorCode: string,
    details?: unknown,
    requestId?: string
  ) {
    super(message);
    this.name = 'ApiClientError';
    this.statusCode = statusCode;
    this.errorCode = errorCode;
    this.details = details;
    this.requestId = requestId;

    // Maintains proper stack trace for where our error was thrown
    if (Error.captureStackTrace) {
      Error.captureStackTrace(this, ApiClientError);
    }
  }

  static fromApiError(error: ApiError, statusCode: number): ApiClientError {
    return new ApiClientError(
      error.message,
      statusCode,
      error.error_code,
      error.details,
      error.request_id
    );
  }
}

/**
 * Validation Error (400)
 */
export class ValidationError extends ApiClientError {
  constructor(message: string, details?: unknown) {
    super(message, 400, 'VALIDATION_ERROR', details);
    this.name = 'ValidationError';
  }
}

/**
 * Insufficient Stock Error (400)
 */
export class InsufficientStockError extends ApiClientError {
  constructor(message: string, details?: unknown) {
    super(message, 400, 'INSUFFICIENT_STOCK', details);
    this.name = 'InsufficientStockError';
  }
}

/**
 * Resource Not Found Error (404)
 */
export class ResourceNotFoundError extends ApiClientError {
  constructor(message: string, details?: unknown) {
    super(message, 404, 'RESOURCE_NOT_FOUND', details);
    this.name = 'ResourceNotFoundError';
  }
}

/**
 * Duplicate Resource Error (409)
 */
export class DuplicateResourceError extends ApiClientError {
  constructor(message: string, details?: unknown) {
    super(message, 409, 'DUPLICATE_RESOURCE', details);
    this.name = 'DuplicateResourceError';
  }
}

/**
 * Unprocessable Entity Error (422)
 */
export class UnprocessableEntityError extends ApiClientError {
  constructor(message: string, details?: unknown) {
    super(message, 422, 'UNPROCESSABLE_ENTITY', details);
    this.name = 'UnprocessableEntityError';
  }
}

/**
 * Internal Server Error (500)
 */
export class InternalServerError extends ApiClientError {
  constructor(message: string, requestId?: string) {
    super(message, 500, 'INTERNAL_SERVER_ERROR', undefined, requestId);
    this.name = 'InternalServerError';
  }
}

/**
 * Database Unavailable Error (503)
 */
export class DatabaseUnavailableError extends ApiClientError {
  constructor(message: string) {
    super(message, 503, 'DATABASE_UNAVAILABLE');
    this.name = 'DatabaseUnavailableError';
  }
}

/**
 * Network Error (timeout, connection refused, etc.)
 */
export class NetworkError extends ApiClientError {
  constructor(message: string) {
    super(message, 0, 'NETWORK_ERROR');
    this.name = 'NetworkError';
  }
}
