<script setup>
/**
 * Dashboard > Brands. **The list half of the dashboard CRUD pattern.**
 *
 * CategoryList, UserList, AddressList and the product list are all this file
 * with the nouns changed, so it is worth reading once properly. The shape is:
 *
 *   1. pull the collection and its pagination out of the manage store
 *   2. `load(page)` on mount, and again whenever PaginationBar asks
 *   3. mutate through the store, then re-read the current page
 *   4. every failure becomes a toast; nothing is swallowed
 *
 * Step 3 is the part worth copying deliberately. Deleting a row re-fetches
 * instead of splicing it out of the local array, because removing a row shifts
 * every later row up a page - after a delete the local list is a page of
 * eleven items, and the twelfth is one the user has not seen. Re-reading is a
 * cheap way to stay honest about server-side state.
 *
 * What is *not* here: any check of what this user may do beyond hiding a
 * button. `auth.isAdmin` decides whether "Add brand" is rendered; the API
 * decides whether the request is allowed. The first is a courtesy, the second
 * is the rule - see apps/core/permissions.py.
 */
import { storeToRefs } from 'pinia'
import { onMounted } from 'vue'

import LoadingIndicator from '@/components/common/LoadingIndicator.vue'
import PaginationBar from '@/components/common/PaginationBar.vue'
import SubPage from '@/components/dashboard/SubPage.vue'
import { useAuthStore } from '@/stores/auth'
import { useManageStore } from '@/stores/manage'
import { useUiStore } from '@/stores/ui'
import { errorMessage } from '@/utils/format'

const auth = useAuthStore()
const store = useManageStore()
const ui = useUiStore()
const { brands, loading, pagination } = storeToRefs(store)

function load(page = 1) {
  return store.fetchBrands({ page })
}

onMounted(() => load())

async function remove(brand) {
  try {
    await store.deleteBrand(brand.id)
    ui.success(`${brand.name} deleted.`)
    load(pagination.value.current_page)
  } catch (error) {
    ui.error(errorMessage(error))
  }
}
</script>

<template>
  <SubPage
    title="Brands"
    :description="auth.isMerchant ? 'Your brand.' : 'Every brand in the store.'"
  >
    <template v-if="auth.isAdmin" #action>
      <RouterLink class="btn btn-sm btn-primary" to="/dashboard/brand/add">
        Add brand
      </RouterLink>
    </template>
  </SubPage>

  <LoadingIndicator v-if="loading && !brands.length" />

  <p v-else-if="!brands.length" class="text-muted">No brands yet.</p>

  <template v-else>
    <div class="table-responsive">
      <table class="table align-middle">
        <thead>
          <tr>
            <th scope="col">Name</th>
            <th scope="col">Seller</th>
            <th scope="col">Status</th>
            <th scope="col"><span class="visually-hidden">Actions</span></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="brand in brands" :key="brand.id">
            <td class="fw-medium">
              {{ brand.name }}
              <div class="small text-muted">{{ brand.description }}</div>
            </td>
            <td class="small text-muted">{{ brand.merchant_name || '—' }}</td>
            <td>
              <span class="badge" :class="brand.is_active ? 'text-bg-success' : 'text-bg-secondary'">
                {{ brand.is_active ? 'Active' : 'Inactive' }}
              </span>
            </td>
            <td class="text-end text-nowrap">
              <RouterLink
                class="btn btn-sm btn-outline-secondary me-1"
                :to="`/dashboard/brand/${brand.id}`"
              >
                Edit
              </RouterLink>
              <button
                v-if="auth.isAdmin"
                class="btn btn-sm btn-outline-danger"
                type="button"
                @click="remove(brand)"
              >
                Delete
              </button>
            </td>
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
