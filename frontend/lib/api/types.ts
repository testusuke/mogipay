// API Type Definitions for MogiPay Frontend

// =========================================
// Product Types
// =========================================

export type ProductType = 'single' | 'set';

export interface SetItemRequest {
  product_id: string;
  quantity: number;
}

export interface CreateProductRequest {
  name: string;
  unit_cost: number;
  sale_price: number;
  initial_stock: number;
  product_type: ProductType;
  set_items?: SetItemRequest[];
}

export interface UpdateProductRequest {
  name?: string;
  unit_cost?: number;
  sale_price?: number;
  initial_stock?: number;
  product_type?: ProductType;
  set_items?: SetItemRequest[];
}

export interface UpdatePriceRequest {
  sale_price: number;
}

export interface SetItem {
  product_id: string;
  quantity: number;
}

export interface Product {
  id: string;
  name: string;
  unit_cost: number;
  sale_price: number;
  current_stock: number;
  initial_stock: number;
  product_type: ProductType;
  set_items?: SetItem[];
  created_at: string;
  updated_at: string;
}

export interface ProductResponse {
  product_id: string;
}

export interface DeleteResponse {
  message: string;
}

// =========================================
// Sales Types
// =========================================

export interface CheckoutItem {
  product_id: string;
  quantity: number;
}

export interface CheckoutRequest {
  items: CheckoutItem[];
}

export interface CheckoutResponse {
  sale_id: string;
  total_amount: number;
  timestamp: string;
}

export interface SaleItem {
  product_id: string;
  product_name: string;
  quantity: number;
  unit_cost: number;
  sale_price: number;
  subtotal: number;
}

export interface SalesHistory {
  sale_id: string;
  timestamp: string;
  items: SaleItem[];
  total_amount: number;
}

export interface SalesSummary {
  total_revenue: number;
  daily_revenue: number[];
  completion_rate: number;
}

// =========================================
// Inventory Types
// =========================================

export interface ProductInventory {
  id: string;
  name: string;
  product_type: ProductType;
  current_stock: number;
  initial_stock: number;
  stock_rate: number;
  is_out_of_stock: boolean;
}

export interface InventoryStatus {
  products: ProductInventory[];
}

// =========================================
// Financial Types
// =========================================

export interface FinancialSummary {
  total_cost: number;
  total_revenue: number;
  profit: number;
  profit_rate: number;
  break_even_achieved: boolean;
}

// =========================================
// Error Types
// =========================================

export interface ErrorDetail {
  field?: string;
  error?: string;
  value?: string | number;
  reason?: string;
  product_name?: string;
  requested?: number;
  available?: number;
  resource_type?: string;
  resource_id?: string;
}

export interface ApiError {
  error_code: string;
  message: string;
  details?: ErrorDetail;
  request_id?: string;
}

// =========================================
// Authentication Types
// =========================================

export interface LoginRequest {
  password: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface AuthStatusResponse {
  authenticated: boolean;
  message: string;
}

// =========================================
// Query Parameters
// =========================================

export interface SalesHistoryQueryParams {
  date_from?: string;
  date_to?: string;
}

export interface ProductQueryParams {
  product_type?: ProductType;
}
