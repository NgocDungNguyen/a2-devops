<script setup>
import { storeToRefs } from 'pinia'
import { onMounted, ref } from 'vue'

import LoadingIndicator from '@/components/common/LoadingIndicator.vue'
import PaginationBar from '@/components/common/PaginationBar.vue'
import SubPage from '@/components/dashboard/SubPage.vue'
import { useAuthStore } from '@/stores/auth'
import { useOrdersStore } from '@/stores/orders'
import { dateTime, money } from '@/utils/format'

const auth = useAuthStore()
const store = useOrdersStore()
const { orders, loading, pagination } = storeToRefs(store)

const search = ref('')

function load(page = 1) {
  // Order numbers are integers, so searching means "jump to this number".
  return store.fetchOrders({ page, search: search.value || undefined })
}

onMounted(() => load())
</script>

<template>
  <SubPage
    title="Orders"
    :description="auth.isAdmin ? 'Every order placed in the store.' : 'Your order history.'"
  />

  <form class="d-flex gap-2 mb-3" style="max-width: 320px" @submit.prevent="load()">
    <input
      v-model="search"
      type="search"
      class="form-control form-control-sm"
      placeholder="Order number"
      aria-label="Search by order number"
    />
    <button class="btn btn-sm btn-outline-secondary flex-shrink-0" type="submit">
      Search
    </button>
  </form>

  <LoadingIndicator v-if="loading && !orders.length" />

  <p v-else-if="!orders.length" class="text-muted">
    No orders yet.
    <RouterLink to="/shop">Start shopping</RouterLink>.
  </p>

  <template v-else>
    <div class="table-responsive">
      <table class="table align-middle">
        <thead>
          <tr>
            <th scope="col">Order</th>
            <th v-if="auth.isAdmin" scope="col">Customer</th>
            <th scope="col">Placed</th>
            <th scope="col" class="text-center">Items</th>
            <th scope="col">Status</th>
            <th scope="col" class="text-end">Total</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="order in orders" :key="order.id">
            <th scope="row" class="fw-normal">
              <RouterLink :to="{ name: 'order-detail', params: { id: order.id } }">
                #{{ order.id }}
              </RouterLink>
            </th>
            <td v-if="auth.isAdmin" class="small text-muted">{{ order.customer_email }}</td>
            <td class="small text-muted">{{ dateTime(order.created_at) }}</td>
            <td class="text-center">{{ order.item_count ?? '—' }}</td>
            <td>
              <span
                class="badge"
                :class="order.status === 'cancelled' ? 'text-bg-dark' : 'text-bg-success'"
              >
                {{ order.status === 'cancelled' ? 'Cancelled' : 'Placed' }}
              </span>
            </td>
            <td class="text-end fw-semibold">{{ money(order.total) }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <PaginationBar
      :current-page="pagination.current_page"
      :total-pages="pagination.total_pages"
      @change="load"
    />
  </template>
</template>
