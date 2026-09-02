import { PLACEHOLDER_IMAGE } from '@/config'

const currency = new Intl.NumberFormat('en-AU', {
  style: 'currency',
  currency: 'USD',
  currencyDisplay: 'narrowSymbol'
})

export function money(value) {
  const number = Number(value ?? 0)
  return Number.isFinite(number) ? currency.format(number) : currency.format(0)
}

export function shortDate(value) {
  if (!value) return ''
  return new Date(value).toLocaleDateString('en-AU', {
    day: 'numeric',
    month: 'short',
    year: 'numeric'
  })
}

export function dateTime(value) {
  if (!value) return ''
  return new Date(value).toLocaleString('en-AU', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

/** Falls back to the placeholder for products with no photograph. */
export function imageOrPlaceholder(url) {
  return url || PLACEHOLDER_IMAGE
}

export function initial(text) {
  return (text || '?').trim().charAt(0).toUpperCase()
}

/**
 * Pulls a usable message out of an axios error.
 *
 * The API's exception handler guarantees a `detail` string on every 4xx, and
 * the response interceptor copies it onto `friendlyMessage`, so this is
 * mostly a safety net for anything that slips past both.
 */
export function errorMessage(error, fallback = 'Something went wrong.') {
  return (
    error?.friendlyMessage || error?.response?.data?.detail || error?.message || fallback
  )
}

/**
 * Field-level errors, for highlighting the offending input in a form.
 *
 * Pass `scope` to reach into a nested serializer. Checkout posts the card
 * under `payment`, so DRF returns `{payment: {number: [...]}}` and the card
 * form asks for fieldErrors(error, 'payment') to get `{number: '...'}`.
 */
export function fieldErrors(error, scope) {
  let data = error?.response?.data
  if (scope && data && typeof data === 'object') data = data[scope]
  if (!data || typeof data !== 'object') return {}

  return Object.fromEntries(
    Object.entries(data)
      .filter(([key]) => key !== 'detail')
      .map(([key, value]) => [key, Array.isArray(value) ? value[0] : String(value)])
  )
}
