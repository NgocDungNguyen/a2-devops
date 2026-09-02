<script setup>
import { storeToRefs } from 'pinia'
import { onMounted } from 'vue'

import LoadingIndicator from '@/components/common/LoadingIndicator.vue'
import SubPage from '@/components/dashboard/SubPage.vue'
import { useAddressStore } from '@/stores/addresses'
import { useUiStore } from '@/stores/ui'
import { errorMessage } from '@/utils/format'

const store = useAddressStore()
const ui = useUiStore()
const { addresses, loading } = storeToRefs(store)

onMounted(() => store.fetchAll())

async function remove(address) {
  try {
    await store.remove(address.id)
    ui.success('Address removed.')
  } catch (error) {
    ui.error(errorMessage(error))
  }
}
</script>

<template>
  <SubPage title="Addresses" description="Where we send your orders.">
    <template #action>
      <RouterLink class="btn btn-sm btn-primary" to="/dashboard/address/add">
        Add address
      </RouterLink>
    </template>
  </SubPage>

  <LoadingIndicator v-if="loading && !addresses.length" />

  <p v-else-if="!addresses.length" class="text-muted">
    You have not saved an address yet.
  </p>

  <ul v-else class="list-unstyled d-grid gap-3 mb-0">
    <li v-for="address in addresses" :key="address.id" class="data-card">
      <div class="d-flex flex-wrap justify-content-between gap-2">
        <div>
          <p class="mb-1 fw-medium">
            {{ address.address }}
            <span v-if="address.is_default" class="badge text-bg-primary ms-1">Default</span>
          </p>
          <p class="small text-muted mb-0">
            {{ address.city }}, {{ address.state }} {{ address.zip_code }},
            {{ address.country }}
          </p>
        </div>

        <div class="d-flex gap-2 align-items-start">
          <RouterLink
            class="btn btn-sm btn-outline-secondary"
            :to="`/dashboard/address/${address.id}`"
          >
            Edit
          </RouterLink>
          <button class="btn btn-sm btn-outline-danger" type="button" @click="remove(address)">
            Remove
          </button>
        </div>
      </div>
    </li>
  </ul>
</template>
