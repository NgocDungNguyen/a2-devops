<script setup>
import { storeToRefs } from 'pinia'
import { onMounted, ref } from 'vue'

import LoadingIndicator from '@/components/common/LoadingIndicator.vue'
import PaginationBar from '@/components/common/PaginationBar.vue'
import SubPage from '@/components/dashboard/SubPage.vue'
import { MERCHANT_STATUS_LABELS } from '@/config'
import { useManageStore } from '@/stores/manage'
import { useUiStore } from '@/stores/ui'
import { errorMessage, shortDate } from '@/utils/format'

const store = useManageStore()
const ui = useUiStore()
const { merchants, loading, pagination } = storeToRefs(store)

const search = ref('')
const busy = ref(null)

function load(page = 1) {
  return store.fetchMerchants({ page, search: search.value || undefined })
}

onMounted(() => load())

const statusBadge = {
  waiting: 'text-bg-warning',
  approved: 'text-bg-success',
  rejected: 'text-bg-dark'
}

async function act(merchant, action) {
  busy.value = merchant.id
  try {
    if (action === 'approve') {
      await store.approveMerchant(merchant.id)
      // The invitation email carries a signup link. With the console email
      // backend it appears in the API server's log.
      ui.success(`${merchant.name} approved — an invitation email has been sent.`)
    } else if (action === 'reject') {
      await store.rejectMerchant(merchant.id)
      ui.info(`${merchant.name} rejected.`)
    } else if (action === 'toggle') {
      await store.setMerchantActive(merchant.id, !merchant.is_active)
      ui.success(
        merchant.is_active
          ? `${merchant.name} deactivated — their products are no longer listed.`
          : `${merchant.name} reactivated.`
      )
    } else if (action === 'delete') {
      await store.deleteMerchant(merchant.id)
      ui.success(`${merchant.name} deleted.`)
    }
    load(pagination.value.current_page)
  } catch (error) {
    ui.error(errorMessage(error))
  } finally {
    busy.value = null
  }
}
</script>

<template>
  <SubPage title="Sellers" description="Applications and active seller accounts." />

  <form class="d-flex gap-2 mb-3" style="max-width: 360px" @submit.prevent="load()">
    <input
      v-model="search"
      type="search"
      class="form-control form-control-sm"
      placeholder="Search by name, email, brand or status"
      aria-label="Search sellers"
    />
    <button class="btn btn-sm btn-outline-secondary flex-shrink-0" type="submit">
      Search
    </button>
  </form>

  <LoadingIndicator v-if="loading && !merchants.length" />

  <p v-else-if="!merchants.length" class="text-muted">No seller applications yet.</p>

  <ul v-else class="list-unstyled d-grid gap-3 mb-0">
    <li v-for="merchant in merchants" :key="merchant.id" class="data-card">
      <div class="d-flex flex-wrap justify-content-between gap-3">
        <div class="min-w-0">
          <div class="d-flex flex-wrap align-items-center gap-2 mb-1">
            <strong>{{ merchant.brand_name || merchant.name }}</strong>
            <span class="badge" :class="statusBadge[merchant.status]">
              {{ MERCHANT_STATUS_LABELS[merchant.status] }}
            </span>
            <span
              v-if="merchant.status === 'approved'"
              class="badge"
              :class="merchant.is_active ? 'text-bg-success' : 'text-bg-secondary'"
            >
              {{ merchant.is_active ? 'Active' : 'Disabled' }}
            </span>
            <span
              v-if="merchant.brand_name_actual && !merchant.brand_is_active"
              class="badge text-bg-warning"
            >
              Brand not activated
            </span>
          </div>

          <p class="small text-muted mb-1">{{ merchant.business }}</p>
          <p class="small text-muted mb-0">
            {{ merchant.name }} · {{ merchant.email }}
            <span v-if="merchant.phone_number">· {{ merchant.phone_number }}</span>
            · applied {{ shortDate(merchant.created_at) }}
          </p>
        </div>

        <div class="d-flex flex-wrap gap-2 align-items-start">
          <template v-if="merchant.status === 'waiting'">
            <button
              class="btn btn-sm btn-primary"
              type="button"
              :disabled="busy === merchant.id"
              @click="act(merchant, 'approve')"
            >
              Approve
            </button>
            <button
              class="btn btn-sm btn-outline-secondary"
              type="button"
              :disabled="busy === merchant.id"
              @click="act(merchant, 'reject')"
            >
              Reject
            </button>
          </template>

          <template v-else-if="merchant.status === 'approved'">
            <button
              class="btn btn-sm"
              :class="merchant.is_active ? 'btn-outline-warning' : 'btn-outline-success'"
              type="button"
              :disabled="busy === merchant.id"
              @click="act(merchant, 'toggle')"
            >
              {{ merchant.is_active ? 'Deactivate' : 'Reactivate' }}
            </button>
          </template>

          <template v-else>
            <button
              class="btn btn-sm btn-outline-primary"
              type="button"
              :disabled="busy === merchant.id"
              @click="act(merchant, 'approve')"
            >
              Approve after all
            </button>
          </template>

          <button
            class="btn btn-sm btn-outline-danger"
            type="button"
            :disabled="busy === merchant.id"
            @click="act(merchant, 'delete')"
          >
            Delete
          </button>
        </div>
      </div>
    </li>
  </ul>

  <div class="mt-4">
    <PaginationBar
      :current-page="pagination.current_page"
      :total-pages="pagination.total_pages"
      @change="load"
    />
  </div>
</template>
