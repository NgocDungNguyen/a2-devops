import { defineStore } from 'pinia'
import { computed, ref, watch } from 'vue'

import { orderApi } from '@/api'
import { STORAGE_KEYS } from '@/config'

/**
 * The shopping bag.
 *
 * Held in the browser, exactly as in the application this replaces — nothing
 * touches the server until checkout. What is different is that checkout sends
 * only product ids and quantities; the server works out the prices, the tax
 * and the total. The old API accepted a total from the browser and stored it.
 */
export const useCartStore = defineStore('cart', () => {
  const items = ref(loadFromStorage())

  function loadFromStorage() {
    try {
      const raw = localStorage.getItem(STORAGE_KEYS.cart)
      return raw ? JSON.parse(raw) : []
    } catch {
      return []
    }
  }

  function persist() {
    localStorage.setItem(STORAGE_KEYS.cart, JSON.stringify(items.value))
  }

  watch(items, persist, { deep: true })

  const count = computed(() =>
    items.value.reduce((total, item) => total + item.quantity, 0)
  )

  // Displayed as an estimate. The authoritative figure comes back from the
  // server when the order is placed.
  const subtotal = computed(() =>
    items.value.reduce(
      (total, item) => total + Number(item.price) * item.quantity,
      0
    )
  )

  const isEmpty = computed(() => items.value.length === 0)

  function find(productId) {
    return items.value.find((item) => item.id === productId)
  }

  /**
   * How many of one product may go in a single order.
   *
   * Ported from the original's calculatePurchaseQuantity: scarce stock is
   * rationed so one shopper cannot clear the shelf.
   */
  function maxPurchaseQuantity(inventory) {
    if (inventory <= 25) return 1
    if (inventory <= 100) return 5
    if (inventory < 500) return 25
    return 50
  }

  function add(product, quantity = 1) {
    const cap = Math.min(maxPurchaseQuantity(product.quantity), product.quantity)
    const existing = find(product.id)

    if (existing) {
      existing.quantity = Math.min(existing.quantity + quantity, cap)
    } else {
      items.value.push({
        id: product.id,
        name: product.name,
        slug: product.slug,
        price: product.price,
        image_url: product.image_url,
        brand_name: product.brand_name,
        inventory: product.quantity,
        quantity: Math.min(quantity, cap)
      })
    }
    persist()
  }

  function setQuantity(productId, quantity) {
    const item = find(productId)
    if (!item) return
    const cap = Math.min(maxPurchaseQuantity(item.inventory), item.inventory)
    item.quantity = Math.max(1, Math.min(quantity, cap))
    persist()
  }

  function remove(productId) {
    items.value = items.value.filter((item) => item.id !== productId)
    persist()
  }

  function clear() {
    items.value = []
    persist()
  }

  /**
   * Place the order.
   *
   * `payment` is the card, passed straight through to the request. It is
   * deliberately a parameter rather than store state: the bag is persisted to
   * localStorage on every change, and a card must never end up there.
   *
   * The bag is only cleared once the server has accepted the order, so a
   * declined card leaves the shopper's items exactly where they were.
   */
  async function checkout(payment) {
    const payload = items.value.map((item) => ({
      product: item.id,
      quantity: item.quantity
    }))
    const { data } = await orderApi.create(payload, payment)
    clear()
    return data
  }

  /** Keeps the bag in step when the same store is open in another tab. */
  function syncFromStorage() {
    items.value = loadFromStorage()
  }

  return {
    items,
    count,
    subtotal,
    isEmpty,
    find,
    add,
    setQuantity,
    remove,
    clear,
    checkout,
    syncFromStorage,
    maxPurchaseQuantity
  }
})
