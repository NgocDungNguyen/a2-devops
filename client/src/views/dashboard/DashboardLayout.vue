<script setup>
import { computed } from 'vue'

import { DASHBOARD_LINKS } from '@/router'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()

/**
 * One link list, filtered by role.
 *
 * The same array drives the route metadata, so a visible link and the guard
 * protecting it cannot drift apart. The original kept three separate route
 * trees plus a JSON file of menu items and they did drift.
 */
const links = computed(() =>
  DASHBOARD_LINKS.filter((link) => !link.roles || link.roles.includes(auth.role))
)

const roleLabel = computed(
  () => ({ admin: 'Admin', merchant: 'Seller', member: 'Member' })[auth.role] || ''
)
</script>

<template>
  <div class="container py-4">
    <!--
      A seller whose account has been switched off keeps their role but loses
      access. Showing this instead of the dashboard matches what the server
      does, which is return 403 for everything under /api/manage/.
    -->
    <div v-if="auth.isDisabledMerchant" class="data-card text-center py-5">
      <h1 class="h5 page-title mb-3">Your seller account is not active</h1>
      <p class="text-muted mb-4">
        An administrator has deactivated your account, so your products are no
        longer listed in the store. Get in touch and we will sort it out.
      </p>
      <RouterLink class="btn btn-primary" to="/contact">Contact the store</RouterLink>
    </div>

    <div v-else class="row g-4">
      <aside class="col-12 col-lg-3">
        <div class="dashboard-sidebar">
          <div class="p-3 bg-light border-bottom">
            <p class="fw-medium mb-0 text-truncate">
              {{ auth.user?.full_name || auth.user?.email }}
            </p>
            <span class="badge text-bg-secondary mt-1">{{ roleLabel }}</span>
          </div>

          <nav class="list-group list-group-flush">
            <RouterLink
              v-for="link in links"
              :key="link.to"
              class="list-group-item list-group-item-action"
              :to="link.to"
              :exact-active-class="link.exact ? 'router-link-active' : undefined"
              :active-class="link.exact ? '' : 'router-link-active'"
            >
              {{ link.label }}
            </RouterLink>
          </nav>
        </div>
      </aside>

      <div class="col-12 col-lg-9">
        <RouterView />
      </div>
    </div>
  </div>
</template>
