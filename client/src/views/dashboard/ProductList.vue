<script setup>
import { storeToRefs } from 'pinia'
import { onMounted } from 'vue'

import LoadingIndicator from '@/components/common/LoadingIndicator.vue'
import PaginationBar from '@/components/common/PaginationBar.vue'
import SubPage from '@/components/dashboard/SubPage.vue'
import { useAuthStore } from '@/stores/auth'
import { useManageStore } from '@/stores/manage'
import { useUiStore } from '@/stores/ui'
import { errorMessage, imageOrPlaceholder, money } from '@/utils/format'

const auth = useAuthStore()
const store = useManageStore()
const ui = useUiStore()
const { products, loading, pagination } = storeToRefs(store)

function load(page = 1) {
  return store.fetchProducts({ page })
}

onMounted(() => load())

async function remove(product) {
  try {
    await store.deleteProduct(product.id)
    ui.success(`${product.name} deleted.`)
    load(pagination.value.current_page)
  } catch (error) {
    // A product that appears on a historical order is protected from
    // deletion, so the server returns 409 with an explanation.
    ui.error(errorMessage(error))
  }
}
</script>

<template>
  <SubPage
    title="Products"
    :description="auth.isMerchant ? 'Products under your brand.' : 'Every product in the store.'"
  >
    <template #action>
      <RouterLink class="btn btn-sm btn-primary" to="/dashboard/product/add">
        Add product
      </RouterLink>
    </template>
  </SubPage>

  <LoadingIndicator v-if="loading && !products.length" />

  <p v-else-if="!products.length" class="text-muted">No products yet.</p>

  <template v-else>
    <div class="table-responsive">
      <table class="table align-middle">
        <thead>
          <tr>
            <th scope="col" style="width: 60px"><span class="visually-hidden">Image</span></th>
            <th scope="col">Name</th>
            <th scope="col">SKU</th>
            <th scope="col">Brand</th>
            <th scope="col" class="text-end">Price</th>
            <th scope="col" class="text-center">Stock</th>
            <th scope="col">Status</th>
            <th scope="col"><span class="visually-hidden">Actions</span></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="product in products" :key="product.id">
            <td>
              <img
                :src="imageOrPlaceholder(product.image_url)"
                :alt="product.name"
                width="44"
                height="44"
                class="rounded object-fit-cover"
              />
            </td>
            <td class="fw-medium">{{ product.name }}</td>
            <td class="small text-muted">{{ product.sku }}</td>
            <td class="small text-muted">{{ product.brand_name || '—' }}</td>
            <td class="text-end">{{ money(product.price) }}</td>
            <td class="text-center">{{ product.quantity }}</td>
            <td>
              <span class="badge" :class="product.is_active ? 'text-bg-success' : 'text-bg-secondary'">
                {{ product.is_active ? 'Active' : 'Inactive' }}
              </span>
            </td>
            <td class="text-end text-nowrap">
              <RouterLink
                class="btn btn-sm btn-outline-secondary me-1"
                :to="`/dashboard/product/${product.id}`"
              >
                Edit
              </RouterLink>
              <button class="btn btn-sm btn-outline-danger" type="button" @click="remove(product)">
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
