/**
 * Every API URL in the application lives in this file.
 *
 * Stores call these functions; nothing else calls axios directly. The day the
 * API is versioned or a path changes, it is one edit here rather than forty
 * across the component tree.
 */

import http from './http'

// --- auth ------------------------------------------------------------------

export const authApi = {
  register: (payload) => http.post('/auth/register/', payload),
  login: (payload) => http.post('/auth/login/', payload),
  logout: (refresh) => http.post('/auth/logout/', { refresh }),
  forgotPassword: (email) => http.post('/auth/password/forgot/', { email }),
  resetPassword: (payload) => http.post('/auth/password/reset/', payload),
  changePassword: (payload) => http.post('/auth/password/change/', payload)
}

// --- account ---------------------------------------------------------------

export const accountApi = {
  me: () => http.get('/users/me/'),
  updateMe: (payload) => http.patch('/users/me/', payload)
}

export const usersApi = {
  list: (params) => http.get('/users/', { params })
}

export const addressApi = {
  list: () => http.get('/addresses/'),
  get: (id) => http.get(`/addresses/${id}/`),
  create: (payload) => http.post('/addresses/', payload),
  update: (id, payload) => http.patch(`/addresses/${id}/`, payload),
  remove: (id) => http.delete(`/addresses/${id}/`)
}

// --- storefront ------------------------------------------------------------

export const productApi = {
  list: (params) => http.get('/products/', { params }),
  get: (slug) => http.get(`/products/${slug}/`),
  search: (q) => http.get('/products/search/', { params: { q } }),
  reviews: (slug, params) => http.get(`/products/${slug}/reviews/`, { params })
}

export const categoryApi = {
  list: () => http.get('/categories/')
}

export const brandApi = {
  list: () => http.get('/brands/')
}

// --- management ------------------------------------------------------------

function toFormData(payload) {
  const form = new FormData()
  Object.entries(payload).forEach(([key, value]) => {
    if (value === undefined || value === null) return
    if (Array.isArray(value)) {
      value.forEach((entry) => form.append(key, entry))
    } else {
      form.append(key, value)
    }
  })
  return form
}

export const manageProductApi = {
  list: (params) => http.get('/manage/products/', { params }),
  get: (id) => http.get(`/manage/products/${id}/`),
  select: () => http.get('/manage/products/select/'),
  // Deliberately not setting Content-Type: axios needs to generate the
  // multipart boundary itself, and overriding the header breaks the upload.
  create: (payload) => http.post('/manage/products/', toFormData(payload)),
  update: (id, payload) => http.patch(`/manage/products/${id}/`, toFormData(payload)),
  remove: (id) => http.delete(`/manage/products/${id}/`)
}

export const manageCategoryApi = {
  list: (params) => http.get('/manage/categories/', { params }),
  get: (id) => http.get(`/manage/categories/${id}/`),
  create: (payload) => http.post('/manage/categories/', payload),
  update: (id, payload) => http.patch(`/manage/categories/${id}/`, payload),
  remove: (id) => http.delete(`/manage/categories/${id}/`)
}

export const manageBrandApi = {
  list: (params) => http.get('/manage/brands/', { params }),
  get: (id) => http.get(`/manage/brands/${id}/`),
  select: () => http.get('/manage/brands/select/'),
  create: (payload) => http.post('/manage/brands/', payload),
  update: (id, payload) => http.patch(`/manage/brands/${id}/`, payload),
  remove: (id) => http.delete(`/manage/brands/${id}/`)
}

export const manageMerchantApi = {
  list: (params) => http.get('/manage/merchants/', { params }),
  update: (id, payload) => http.patch(`/manage/merchants/${id}/`, payload),
  approve: (id) => http.post(`/manage/merchants/${id}/approve/`),
  reject: (id) => http.post(`/manage/merchants/${id}/reject/`),
  remove: (id) => http.delete(`/manage/merchants/${id}/`)
}

export const manageReviewApi = {
  list: (params) => http.get('/manage/reviews/', { params }),
  approve: (id) => http.post(`/manage/reviews/${id}/approve/`),
  reject: (id) => http.post(`/manage/reviews/${id}/reject/`)
}

// --- merchants (public) ----------------------------------------------------

export const merchantApi = {
  apply: (payload) => http.post('/merchants/apply/', payload),
  signup: (payload) => http.post('/merchants/signup/', payload)
}

// --- orders, reviews, wishlist --------------------------------------------

export const orderApi = {
  list: (params) => http.get('/orders/', { params }),
  get: (id) => http.get(`/orders/${id}/`),
  // The card travels with the order and is never stored client-side.
  create: (items, payment) => http.post('/orders/', { items, payment }),
  cancel: (id) => http.post(`/orders/${id}/cancel/`),
  setItemStatus: (orderId, itemId, status) =>
    http.patch(`/orders/${orderId}/items/${itemId}/`, { status })
}

export const reviewApi = {
  create: (payload) => http.post('/reviews/', payload),
  update: (id, payload) => http.patch(`/reviews/${id}/`, payload),
  remove: (id) => http.delete(`/reviews/${id}/`)
}

export const wishlistApi = {
  list: () => http.get('/wishlist/'),
  toggle: (product, isLiked) =>
    http.post('/wishlist/', { product, is_liked: isLiked })
}

// --- misc ------------------------------------------------------------------

export const siteApi = {
  config: () => http.get('/config/'),
  contact: (payload) => http.post('/contact/', payload),
  subscribe: (email) => http.post('/newsletter/subscribe/', { email })
}
