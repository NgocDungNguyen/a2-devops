import { onBeforeUnmount } from 'vue'

/**
 * Debounce a function call.
 *
 * Used by the navbar search so typing "hoodie" issues one request rather than
 * six. The previous application instead fired a request on every third
 * character, which meant "hood" searched for "hoo".
 */
export function useDebounce(fn, delay = 300) {
  let timer = null

  function debounced(...args) {
    clearTimeout(timer)
    timer = setTimeout(() => fn(...args), delay)
  }

  debounced.cancel = () => clearTimeout(timer)

  onBeforeUnmount(() => clearTimeout(timer))

  return debounced
}
