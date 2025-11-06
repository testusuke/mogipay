// MogiPay API Client

import type {
  // Product
  Product,
  CreateProductRequest,
  UpdateProductRequest,
  UpdatePriceRequest,
  ProductResponse,
  DeleteResponse,
  ProductQueryParams,
  // Sales
  CheckoutRequest,
  CheckoutResponse,
  SalesHistory,
  SalesSummary,
  SalesHistoryQueryParams,
  // Inventory
  InventoryStatus,
  // Financial
  FinancialSummary,
  // Error
  ApiError,
} from './types';

/**
 * API Client Configuration
 */
export interface ApiClientConfig {
  baseURL: string;
  timeout?: number;
  retries?: number;
}

/**
 * API Client Class
 */
export class ApiClient {
  private baseURL: string;
  private timeout: number;
  private retries: number;

  constructor(config: ApiClientConfig) {
    this.baseURL = config.baseURL;
    this.timeout = config.timeout || 10000;
    this.retries = config.retries || 3;
  }

  /**
   * Generic request method with retry logic
   */
  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.timeout);

    let lastError: Error | null = null;

    for (let attempt = 0; attempt < this.retries; attempt++) {
      try {
        const response = await fetch(url, {
          ...options,
          signal: controller.signal,
          headers: {
            'Content-Type': 'application/json',
            ...options.headers,
          },
        });

        clearTimeout(timeoutId);

        // Handle HTTP error responses
        if (!response.ok) {
          await this.handleErrorResponse(response);
        }

        // Parse JSON response
        const data = await response.json();
        return data as T;
      } catch (error) {
        lastError = error as Error;

        // If this is the last attempt, throw the error
        if (attempt === this.retries - 1) {
          throw await this.handleNetworkError(lastError);
        }

        // Wait before retrying (exponential backoff)
        await this.sleep(Math.pow(2, attempt) * 1000);
      }
    }

    throw lastError || new Error('Unknown error');
  }

  /**
   * Handle HTTP error responses
   */
  private async handleErrorResponse(response: Response): Promise<never> {
    const { ApiClientError } = await import('./errors');

    try {
      const errorData: ApiError = await response.json();
      throw ApiClientError.fromApiError(errorData, response.status);
    } catch (error) {
      // If JSON parsing fails, throw generic error
      if (error instanceof ApiClientError) {
        throw error;
      }
      throw new ApiClientError(
        response.statusText || 'Unknown error',
        response.status,
        'UNKNOWN_ERROR'
      );
    }
  }

  /**
   * Handle network errors
   */
  private async handleNetworkError(error: Error): Promise<Error> {
    if (error.name === 'AbortError') {
      const { NetworkError } = await import('./errors');
      return new NetworkError('Request timeout');
    }
    return error;
  }

  /**
   * Sleep utility for retry backoff
   */
  private sleep(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }

  /**
   * GET request
   */
  private async get<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: 'GET' });
  }

  /**
   * POST request
   */
  private async post<T>(endpoint: string, body: unknown): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: JSON.stringify(body),
    });
  }

  /**
   * PUT request
   */
  private async put<T>(endpoint: string, body: unknown): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'PUT',
      body: JSON.stringify(body),
    });
  }

  /**
   * DELETE request
   */
  private async delete<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: 'DELETE' });
  }

  // =========================================
  // Product API Methods
  // =========================================

  /**
   * Create a new product
   */
  async createProduct(data: CreateProductRequest): Promise<ProductResponse> {
    return this.post<ProductResponse>('/api/products', data);
  }

  /**
   * Get all products
   */
  async getProducts(params?: ProductQueryParams): Promise<Product[]> {
    const queryString = params?.product_type
      ? `?product_type=${params.product_type}`
      : '';
    return this.get<Product[]>(`/api/products${queryString}`);
  }

  /**
   * Get a product by ID
   */
  async getProduct(productId: string): Promise<Product> {
    return this.get<Product>(`/api/products/${productId}`);
  }

  /**
   * Update a product
   */
  async updateProduct(
    productId: string,
    data: UpdateProductRequest
  ): Promise<ProductResponse> {
    return this.put<ProductResponse>(`/api/products/${productId}`, data);
  }

  /**
   * Update product price
   */
  async updateProductPrice(
    productId: string,
    data: UpdatePriceRequest
  ): Promise<ProductResponse> {
    return this.put<ProductResponse>(
      `/api/products/${productId}/price`,
      data
    );
  }

  /**
   * Delete a product
   */
  async deleteProduct(productId: string): Promise<DeleteResponse> {
    return this.delete<DeleteResponse>(`/api/products/${productId}`);
  }

  // =========================================
  // Sales API Methods
  // =========================================

  /**
   * Process checkout
   */
  async checkout(data: CheckoutRequest): Promise<CheckoutResponse> {
    return this.post<CheckoutResponse>('/api/sales/checkout', data);
  }

  /**
   * Get sales history
   */
  async getSalesHistory(
    params?: SalesHistoryQueryParams
  ): Promise<SalesHistory[]> {
    const queryString = [];
    if (params?.date_from) {
      queryString.push(`date_from=${params.date_from}`);
    }
    if (params?.date_to) {
      queryString.push(`date_to=${params.date_to}`);
    }
    const query = queryString.length > 0 ? `?${queryString.join('&')}` : '';
    return this.get<SalesHistory[]>(`/api/sales/history${query}`);
  }

  /**
   * Get sales summary
   */
  async getSalesSummary(): Promise<SalesSummary> {
    return this.get<SalesSummary>('/api/sales/summary');
  }

  // =========================================
  // Inventory API Methods
  // =========================================

  /**
   * Get inventory status
   */
  async getInventoryStatus(): Promise<InventoryStatus> {
    return this.get<InventoryStatus>('/api/inventory/status');
  }

  // =========================================
  // Financial API Methods
  // =========================================

  /**
   * Get financial summary
   */
  async getFinancialSummary(): Promise<FinancialSummary> {
    return this.get<FinancialSummary>('/api/financial/summary');
  }
}

/**
 * Default API Client Instance
 */
export const apiClient = new ApiClient({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
});
