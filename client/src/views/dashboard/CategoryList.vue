<script setup>
import { storeToRefs } from 'pinia'
import { onMounted } from 'vue'

import LoadingIndicator from '@/components/common/LoadingIndicator.vue'
import PaginationBar from '@/components/common/PaginationBar.vue'
import SubPage from '@/components/dashboard/SubPage.vue'
import { useManageStore } from '@/stores/manage'
import { useUiStore } from '@/stores/ui'
import { errorMessage } from '@/utils/format'

const store = useManageStore()
const ui = useUiStore()
const { categories, loading, pagination } = storeToRefs(store)

function load(page = 1) {
  return store.fetchCategories({ page })
}

onMounted(() => load())

async function remove(category) {
  try {
    await store.deleteCategory(category.id)
    ui.success(`${category.name} deleted.`)
    load(pagination.value.current_page)
  } catch (error) {
    ui.error(errorMessage(error))
  }
}
</script>

<template>
  <SubPage title="Categories" description="How products are grouped in the shop.">
    <template #action>
      <RouterLink class="btn btn-sm btn-primary" to="/dashboard/category/add">
        Add category
      </RouterLink>
    </template>
  </SubPage>

  <LoadingIndicator v-if="loading && !categories.length" />

  <p v-else-if="!categories.length" class="text-muted">No categories yet.</p>

  <template v-else>
    <div class="table-responsive">
      <table class="table align-middle">
        <thead>
          <tr>
            <th scope="col">Name</th>
            <th scope="col" class="text-center">Products</th>
            <th scope="col">Status</th>
            <th scope="col"><span class="visually-hidden">Actions</span></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="category in categories" :key="category.id">
            <td class="fw-medium">
              {{ category.name }}
              <div class="small text-muted">{{ category.description }}</div>
            </td>
            <td class="text-center">{{ category.products?.length ?? 0 }}</td>
            <td>
              <span
                class="badge"
                :class="category.is_active ? 'text-bg-success' : 'text-bg-secondary'"
              >
                {{ category.is_active ? 'Active' : 'Inactive' }}
              </span>
            </td>
            <td class="text-end text-nowrap">
              <RouterLink
                class="btn btn-sm btn-outline-secondary me-1"
                :to="`/dashboard/category/${category.id}`"
              >
                Edit
              </RouterLink>
              <button class="btn btn-sm btn-outline-danger" type="button" @click="remove(category)">
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
