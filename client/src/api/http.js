/**
 * The one axios instance the whole application uses.
 *
 * Two interceptors do all the work:
 *
 *   Request  — attaches "Bearer <access token>". The scheme prefix lives here
 *              and nowhere else, so nothing downstream has to remember it.
 *
 *   Response — on a 401, refreshes the access token once and replays the
 *              original request. Ten requests failing at the same moment
 *              share a single refresh call rather than firing ten of them.
 */

import axios from 'axios'

import { API_BASE_URL, STORAGE_KEYS } from '@/config'

const http = axios.create({
  baseURL: API_BASE_URL,
  timeout: 20000,
  headers: { Accept: 'application/json' }
})

// Set by the auth store at start-up. Injecting it avoids a circular import
// between this module and the store, which imports this module.
let authStore = null
let router = null

export function registerAuthStore(store) {
  authStore = store
}

export function registerRouter(instance) {
  router = instance
}

function readAccessToken() {
  if (authStore?.accessToken) return authStore.accessToken
  return localStorage.getItem(STORAGE_KEYS.access)
}

http.interceptors.request.use((config) => {
  const token = readAccessToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// A single in-flight refresh, shared by every request that got a 401 while it
// was running.
let refreshPromise = null

async function refreshAccessToken() {
  const refresh = localStorage.getItem(STORAGE_KEYS.refresh)
  if (!refresh) throw new Error('No refresh token')

  // A bare axios call, not `http` — going through the instance would attach
  // the expired access token and recurse through this interceptor.
  const { data } = await axios.post(
    `${API_BASE_URL}/auth/refresh/`,
    { refresh },
    { headers: { 'Content-Type': 'application/json' } }
  )

  localStorage.setItem(STORAGE_KEYS.access, data.access)
  if (data.refresh) {
    // Refresh tokens rotate, so the response carries a new one.
    localStorage.setItem(STORAGE_KEYS.refresh, data.refresh)
  }
  if (authStore) authStore.applyTokens(data.access, data.refresh)
  return data.access
}

http.interceptors.response.use(
  (response) => response,
  async (error) => {
    const { response, config } = error

    if (!response) {
      // Network failure, DNS, CORS rejection or a timeout.
      return Promise.reject(
        Object.assign(error, {
          friendlyMessage:
            'Could not reach the store. Check your connection and try again.'
        })
      )
    }

    const isRefreshCall = config?.url?.includes('/auth/refresh/')

    if (response.status === 401 && !config._retried && !isRefreshCall) {
      config._retried = true
      try {
        refreshPromise = refreshPromise || refreshAccessToken()
        const token = await refreshPromise
        refreshPromise = null
        config.headers.Authorization = `Bearer ${token}`
        return http(config)
      } catch {
        refreshPromise = null
        authStore?.clearSession()
        if (router && router.currentRoute.value.meta?.requiresAuth) {
          router.push({
            name: 'login',
            query: { next: router.currentRoute.value.fullPath }
          })
        }
      }
    }

    error.friendlyMessage =
      response.data?.detail ||
      (response.status === 403
        ? 'You are not allowed to do that.'
        : response.status === 404
          ? 'We could not find what you were looking for.'
          : response.status >= 500
            ? 'Something went wrong at our end. Please try again.'
            : 'That request could not be completed.')

    return Promise.reject(error)
  }
)

export default http
