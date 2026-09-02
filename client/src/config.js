/**
 * Reads the runtime configuration injected by public/config.js.
 *
 * Order of precedence:
 *   1. window.__APP_CONFIG__      set by dist/config.js at page load
 *   2. import.meta.env.VITE_*     build-time fallback, development only
 *   3. a sensible default
 *
 * Nothing in the application imports import.meta.env directly — keeping that
 * in one place is what makes it possible to retarget a built bundle without
 * rebuilding it.
 */

const runtime = (typeof window !== 'undefined' && window.__APP_CONFIG__) || {}

export const API_BASE_URL =
  runtime.API_BASE_URL || import.meta.env?.VITE_API_BASE_URL || '/api'

export const STORE_NAME = runtime.STORE_NAME || 'RMIT Store'

// Where the token pair is kept between page loads.
export const STORAGE_KEYS = {
  access: 'rmit_access_token',
  refresh: 'rmit_refresh_token',
  cart: 'rmit_cart_items'
}

export const ROLES = {
  ADMIN: 'admin',
  MEMBER: 'member',
  MERCHANT: 'merchant'
}

export const ORDER_ITEM_STATUS = {
  NOT_PROCESSED: 'not_processed',
  PROCESSING: 'processing',
  SHIPPED: 'shipped',
  DELIVERED: 'delivered',
  CANCELLED: 'cancelled'
}

export const ORDER_ITEM_STATUS_LABELS = {
  not_processed: 'Not processed',
  processing: 'Processing',
  shipped: 'Shipped',
  delivered: 'Delivered',
  cancelled: 'Cancelled'
}

export const MERCHANT_STATUS_LABELS = {
  waiting: 'Waiting Approval',
  approved: 'Approved',
  rejected: 'Rejected'
}

export const REVIEW_STATUS_LABELS = {
  waiting: 'Waiting Approval',
  approved: 'Approved',
  rejected: 'Rejected'
}

export const SORT_OPTIONS = [
  { value: 'newest', label: 'Newest First' },
  { value: 'price_desc', label: 'Price: High to Low' },
  { value: 'price_asc', label: 'Price: Low to High' },
  { value: 'rating', label: 'Highest Rated' },
  { value: 'name', label: 'Name (A–Z)' }
]

export const PLACEHOLDER_IMAGE = '/images/placeholder-image.png'
