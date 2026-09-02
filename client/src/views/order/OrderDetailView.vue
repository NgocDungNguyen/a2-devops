<script setup>
import { storeToRefs } from 'pinia'
import { computed, ref, watch } from 'vue'
import { useRoute } from 'vue-router'

import AppIcon from '@/components/common/AppIcon.vue'
import LoadingIndicator from '@/components/common/LoadingIndicator.vue'
import { ORDER_ITEM_STATUS, ORDER_ITEM_STATUS_LABELS } from '@/config'
import { useAuthStore } from '@/stores/auth'
import { useOrdersStore } from '@/stores/orders'
import { useUiStore } from '@/stores/ui'
import { dateTime, errorMessage, imageOrPlaceholder, money } from '@/utils/format'

const route = useRoute()
const auth = useAuthStore()
const orders = useOrdersStore()
const ui = useUiStore()

const { order, loading } = storeToRefs(orders)
const notFound = ref(false)
const busyItem = ref(null)

const statusOptions = Object.entries(ORDER_ITEM_STATUS_LABELS)

const canCancelOrder = computed(() => {
  if (!order.value || order.value.status === 'cancelled') return false
  // Once anything has shipped or been delivered, the whole order can no
  // longer be pulled back in one go.
  return !order.value.items.some((item) =>
    ['shipped', 'delivered'].includes(item.status)
  )
})

function badgeClass(status) {
  return (
    {
      not_processed: 'text-bg-secondary',
      processing: 'text-bg-info',
      shipped: 'text-bg-primary',
      delivered: 'text-bg-success',
      cancelled: 'text-bg-dark'
    }[status] || 'text-bg-secondary'
  )
}

async function load(id) {
  notFound.value = false
  try {
    await orders.fetchOrder(id)
  } catch (error) {
    if (error?.response?.status === 404) notFound.value = true
    else ui.error(errorMessage(error))
  }
}

watch(() => route.params.id, load, { immediate: true })

async function setStatus(item, status) {
  busyItem.value = item.id
  try {
    await orders.setItemStatus(order.value.id, item.id, status)
    ui.success(`Item marked as ${ORDER_ITEM_STATUS_LABELS[status].toLowerCase()}.`)
  } catch (error) {
    ui.error(errorMessage(error))
  } finally {
    busyItem.value = null
  }
}

async function cancelWholeOrder() {
  try {
    await orders.cancel(order.value.id)
    ui.success('Your order has been cancelled and the stock returned.')
  } catch (error) {
    ui.error(errorMessage(error))
  }
}
</script>

<template>
  <div class="container py-4">
    <LoadingIndicator v-if="loading && !order" />

    <div v-else-if="notFound" class="text-center py-5">
      <h1 class="h4 page-title">We could not find that order</h1>
      <RouterLink class="btn btn-primary" to="/dashboard/orders">Your orders</RouterLink>
    </div>

    <template v-else-if="order">
      <RouterLink class="btn btn-sm btn-link px-0 mb-3" to="/dashboard/orders">
        <AppIcon name="arrowLeft" :size="14" /> Back to orders
      </RouterLink>

      <div class="subpage-header">
        <div>
          <h1 class="h4 page-title mb-1">Order #{{ order.id }}</h1>
          <p class="text-muted small mb-0">
            Placed {{ dateTime(order.created_at) }}
            <span v-if="auth.isAdmin && order.customer_email">
              · {{ order.customer_email }}
            </span>
          </p>
        </div>

        <div class="d-flex align-items-center gap-2">
          <span class="badge" :class="order.status === 'cancelled' ? 'text-bg-dark' : 'text-bg-success'">
            {{ order.status === 'cancelled' ? 'Cancelled' : 'Placed' }}
          </span>
          <button
            v-if="canCancelOrder"
            class="btn btn-sm btn-outline-danger"
            type="button"
            @click="cancelWholeOrder"
          >
            Cancel order
          </button>
        </div>
      </div>

      <div class="row g-4">
        <div class="col-12 col-lg-8">
          <ul class="list-unstyled d-grid gap-3 mb-0">
            <li v-for="item in order.items" :key="item.id" class="data-card">
              <div class="d-flex gap-3">
                <img
                  :src="imageOrPlaceholder(item.product_image)"
                  :alt="item.product_name"
                  width="72"
                  height="72"
                  class="rounded object-fit-cover flex-shrink-0"
                />

                <div class="flex-grow-1 min-w-0">
                  <RouterLink
                    v-if="item.product_slug"
                    class="fw-medium d-block"
                    :to="{ name: 'product', params: { slug: item.product_slug } }"
                  >
                    {{ item.product_name }}
                  </RouterLink>
                  <span v-else class="fw-medium d-block">{{ item.product_name }}</span>

                  <div class="small text-muted mb-2">
                    {{ item.brand_name }} · {{ item.quantity }} ×
                    {{ money(item.purchase_price) }}
                  </div>

                  <div class="d-flex flex-wrap align-items-center gap-2">
                    <span class="badge" :class="badgeClass(item.status)">
                      {{ ORDER_ITEM_STATUS_LABELS[item.status] }}
                    </span>

                    <!--
                      Only the store moves an item through fulfilment.

                      A cancelled line is finished: its stock has gone back on
                      the shelf and its money has been refunded, so the server
                      rejects any further status change. Disabling the select
                      says so up front instead of letting an administrator
                      pick a status and collect an error toast.
                    -->
                    <select
                      v-if="auth.isAdmin"
                      class="form-select form-select-sm"
                      style="width: auto"
                      :value="item.status"
                      :disabled="
                        busyItem === item.id ||
                        item.status === ORDER_ITEM_STATUS.CANCELLED
                      "
                      :title="
                        item.status === ORDER_ITEM_STATUS.CANCELLED
                          ? 'A cancelled item cannot be reinstated - the customer must order it again.'
                          : ''
                      "
                      :aria-label="`Status for ${item.product_name}`"
                      @change="setStatus(item, $event.target.value)"
                    >
                      <option v-for="[value, label] in statusOptions" :key="value" :value="value">
                        {{ label }}
                      </option>
                    </select>

                    <button
                      v-else-if="item.status !== ORDER_ITEM_STATUS.CANCELLED
                        && item.status !== ORDER_ITEM_STATUS.DELIVERED"
                      class="btn btn-sm btn-outline-danger"
                      type="button"
                      :disabled="busyItem === item.id"
                      @click="setStatus(item, ORDER_ITEM_STATUS.CANCELLED)"
                    >
                      Cancel item
                    </button>

                    <RouterLink
                      v-if="item.status === ORDER_ITEM_STATUS.DELIVERED && item.product_slug"
                      class="btn btn-sm btn-outline-primary"
                      :to="{ name: 'product', params: { slug: item.product_slug } }"
                    >
                      Review product
                    </RouterLink>

                    <span class="ms-auto fw-semibold">{{ money(item.price_with_tax) }}</span>
                  </div>
                </div>
              </div>
            </li>
          </ul>
        </div>

        <div class="col-12 col-lg-4">
          <div class="data-card">
            <h2 class="h6 mb-3">Summary</h2>
            <dl class="row mb-0 small">
              <dt class="col-7 fw-normal text-muted">Subtotal</dt>
              <dd class="col-5 text-end">{{ money(order.subtotal) }}</dd>

              <dt class="col-7 fw-normal text-muted">Estimated sales tax</dt>
              <dd class="col-5 text-end">{{ money(order.total_tax) }}</dd>

              <dt class="col-7 fw-normal text-muted">Shipping</dt>
              <dd class="col-5 text-end">Free</dd>
            </dl>
            <hr />
            <div class="d-flex justify-content-between fw-semibold">
              <span>Total</span>
              <span class="text-brand">{{ money(order.total) }}</span>
            </div>

            <!-- Brand and last four only. That is all the server keeps. -->
            <div v-if="order.card_last4" class="small text-muted mt-3">
              <div class="d-flex justify-content-between">
                <span class="text-capitalize">
                  {{ order.card_brand }} ending {{ order.card_last4 }}
                </span>
                <span
                  class="badge"
                  :class="order.payment_status === 'refunded' ? 'text-bg-dark' : 'text-bg-success'"
                >
                  {{ order.payment_status === 'refunded' ? 'Refunded' : 'Paid' }}
                </span>
              </div>
              <div v-if="order.payment_reference" class="font-monospace mt-1">
                {{ order.payment_reference }}
              </div>
            </div>

            <p v-if="order.status === 'cancelled'" class="small text-muted mt-3 mb-0">
              Every item on this order was cancelled and the stock returned.
              The order is kept here for your records.
            </p>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>
