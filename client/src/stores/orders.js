/**
 * Order history and the single order being viewed.
 *
 * A Pinia store is shared state plus the functions that change it. This one is
 * written in the "setup" style — the body is just a function, `ref()` makes a
 * reactive value, and whatever the function returns is the store's public
 * surface. Components read `orders.loading` and call `orders.fetchOrder(id)`;
 * they never touch axios themselves.
 *
 * Why a store at all, when a component could fetch its own data? Because two
 * components show the same order: the detail page and the fulfilment controls
 * inside it. Keeping the order in one place means an update from either lands
 * in both, with no events to wire up.
 *
 * Note that nothing here is cached between visits — every view calls fetch on
 * mount. Order status changes behind the user's back (the store ships things),
 * so stale order data is worse than an extra request.
 *
 * Unlike the cart store, nothing here is persisted to localStorage. This is
 * all server state; the server is the copy that counts.
 */
import { defineStore } from 'pinia'
import { ref } from 'vue'

import { orderApi } from '@/api'

export const useOrdersStore = defineStore('orders', () => {
  // The list, for the history page.
  const orders = ref([])
  // The one being looked at, for the detail page. Null while it loads.
  const order = ref(null)
  const loading = ref(false)
  // Mirrors the API's pagination envelope so PaginationBar can render itself.
  const pagination = ref({ count: 0, total_pages: 1, current_page: 1 })

  async function fetchOrders(params = {}) {
    loading.value = true
    try {
      const { data } = await orderApi.list(params)
      orders.value = data.results
      pagination.value = {
        count: data.count,
        total_pages: data.total_pages,
        current_page: data.current_page
      }
      return data
    } finally {
      loading.value = false
    }
  }

  async function fetchOrder(id) {
    loading.value = true
    // Cleared first so the page cannot show the *previous* order's lines
    // while the new one is in flight.
    order.value = null
    try {
      const { data } = await orderApi.get(id)
      order.value = data
      return data
    } finally {
      // `finally`, so a failed request still turns the spinner off. The error
      // itself is deliberately left to propagate: the view knows whether it
      // means "not found" or "show a toast", and this store does not.
      loading.value = false
    }
  }

  // Both of these below replace the whole order with what the server returns
  // rather than patching the local copy. Cancelling a line changes its status,
  // the order's status, its totals and possibly its payment status, and
  // re-deriving all of that in the browser would be the server's arithmetic
  // written a second time — in a second language, where it can disagree.

  async function setItemStatus(orderId, itemId, status) {
    const { data } = await orderApi.setItemStatus(orderId, itemId, status)
    order.value = data
    return data
  }

  async function cancel(orderId) {
    const { data } = await orderApi.cancel(orderId)
    order.value = data
    return data
  }

  return {
    orders,
    order,
    loading,
    pagination,
    fetchOrders,
    fetchOrder,
    setItemStatus,
    cancel
  }
})
