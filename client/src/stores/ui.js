import { defineStore } from 'pinia'
import { ref } from 'vue'

let nextToastId = 1

/**
 * Everything that is chrome rather than data: the two slide-out drawers and
 * the toast queue. Replaces four separate reducers in the original.
 */
export const useUiStore = defineStore('ui', () => {
  const isCartOpen = ref(false)
  const isMenuOpen = ref(false)
  const toasts = ref([])

  function openCart() {
    isCartOpen.value = true
    isMenuOpen.value = false // the two drawers are mutually exclusive
  }

  function closeCart() {
    isCartOpen.value = false
  }

  function toggleCart() {
    isCartOpen.value ? closeCart() : openCart()
  }

  function openMenu() {
    isMenuOpen.value = true
    isCartOpen.value = false
  }

  function closeMenu() {
    isMenuOpen.value = false
  }

  function toggleMenu() {
    isMenuOpen.value ? closeMenu() : openMenu()
  }

  function closeAll() {
    isCartOpen.value = false
    isMenuOpen.value = false
  }

  function notify(message, variant = 'success', timeout = 4000) {
    const id = nextToastId++
    toasts.value.push({ id, message, variant })
    if (timeout) {
      setTimeout(() => dismiss(id), timeout)
    }
    return id
  }

  const success = (message) => notify(message, 'success')
  const error = (message) => notify(message, 'danger', 6000)
  const info = (message) => notify(message, 'info')

  function dismiss(id) {
    toasts.value = toasts.value.filter((toast) => toast.id !== id)
  }

  return {
    isCartOpen,
    isMenuOpen,
    toasts,
    openCart,
    closeCart,
    toggleCart,
    openMenu,
    closeMenu,
    toggleMenu,
    closeAll,
    notify,
    success,
    error,
    info,
    dismiss
  }
})
