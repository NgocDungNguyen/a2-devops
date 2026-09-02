<script setup>
/**
 * Where checkout lands: /order-success/:id.
 *
 * Deliberately the dumbest view in the project. It fetches nothing - the order
 * number comes from the URL, so this page cannot fail, cannot show a spinner,
 * and cannot tell a shopper whose card has just been charged that something
 * went wrong. If they want the detail, the link takes them to the page whose
 * job that is.
 *
 * The order is safely on the server before the router gets here, so a reload,
 * a bookmark or a shared link all still work.
 */
import AppIcon from '@/components/common/AppIcon.vue'
import { useRoute } from 'vue-router'

const route = useRoute()
</script>

<template>
  <div class="container py-5 text-center" style="max-width: 560px">
    <span class="d-inline-flex align-items-center justify-content-center rounded-circle bg-success text-white mb-3" style="width: 64px; height: 64px">
      <AppIcon name="check" :size="30" />
    </span>

    <h1 class="h4 page-title mb-2">Thank you for your order</h1>
    <p class="text-muted mb-4">
      Your order
      <RouterLink :to="{ name: 'order-detail', params: { id: route.params.id } }">
        #{{ route.params.id }}
      </RouterLink>
      has been placed. We have emailed you a confirmation.
    </p>

    <div class="d-flex gap-2 justify-content-center">
      <RouterLink class="btn btn-primary" :to="{ name: 'order-detail', params: { id: route.params.id } }">
        View order
      </RouterLink>
      <RouterLink class="btn btn-outline-secondary" to="/shop">
        Continue shopping
      </RouterLink>
    </div>
  </div>
</template>
