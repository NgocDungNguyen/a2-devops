<script setup>
import { storeToRefs } from 'pinia'
import { onMounted, ref } from 'vue'

import LoadingIndicator from '@/components/common/LoadingIndicator.vue'
import PaginationBar from '@/components/common/PaginationBar.vue'
import SubPage from '@/components/dashboard/SubPage.vue'
import { useManageStore } from '@/stores/manage'
import { shortDate } from '@/utils/format'

const store = useManageStore()
const { users, loading, pagination } = storeToRefs(store)

const search = ref('')

function load(page = 1) {
  return store.fetchUsers({ page, search: search.value || undefined })
}

onMounted(() => load())

const roleBadge = {
  admin: 'text-bg-danger',
  merchant: 'text-bg-primary',
  member: 'text-bg-secondary'
}
</script>

<template>
  <SubPage title="Users" description="Everyone with an account on the store." />

  <form class="d-flex gap-2 mb-3" style="max-width: 360px" @submit.prevent="load()">
    <input
      v-model="search"
      type="search"
      class="form-control form-control-sm"
      placeholder="Search by name or email"
      aria-label="Search users"
    />
    <button class="btn btn-sm btn-outline-secondary flex-shrink-0" type="submit">
      Search
    </button>
  </form>

  <LoadingIndicator v-if="loading && !users.length" />

  <p v-else-if="!users.length" class="text-muted">No users match that search.</p>

  <template v-else>
    <div class="table-responsive">
      <table class="table align-middle">
        <thead>
          <tr>
            <th scope="col">Name</th>
            <th scope="col">Email</th>
            <th scope="col">Role</th>
            <th scope="col">Seller</th>
            <th scope="col">Joined</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="user in users" :key="user.id">
            <td class="fw-medium">{{ user.full_name || '—' }}</td>
            <td class="small text-muted">{{ user.email }}</td>
            <td>
              <span class="badge" :class="roleBadge[user.role]">{{ user.role }}</span>
            </td>
            <td class="small text-muted">{{ user.merchant_name || '—' }}</td>
            <td class="small text-muted">{{ shortDate(user.created_at) }}</td>
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
