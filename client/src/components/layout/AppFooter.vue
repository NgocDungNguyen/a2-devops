<script setup>
import { ref } from 'vue'

import { siteApi } from '@/api'
import { useUiStore } from '@/stores/ui'
import { errorMessage } from '@/utils/format'

const ui = useUiStore()
const email = ref('')
const submitting = ref(false)

async function subscribe() {
  if (!email.value.trim()) return
  submitting.value = true
  try {
    const { data } = await siteApi.subscribe(email.value.trim())
    ui.success(data.detail || 'You are subscribed.')
    email.value = ''
  } catch (error) {
    ui.error(errorMessage(error, 'We could not subscribe that address.'))
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <footer class="store-footer mt-5 pt-5 pb-4">
    <div class="container">
      <div class="row g-4">
        <div class="col-6 col-lg-3">
          <h6 class="mb-3">Support</h6>
          <ul class="list-unstyled d-grid gap-2 mb-0">
            <li><RouterLink to="/contact">Get in touch</RouterLink></li>
            <li><RouterLink to="/sell">Partner with us</RouterLink></li>
            <li><RouterLink to="/brands">Our brands</RouterLink></li>
          </ul>
        </div>

        <div class="col-6 col-lg-3">
          <h6 class="mb-3">Shop</h6>
          <ul class="list-unstyled d-grid gap-2 mb-0">
            <li><RouterLink to="/shop">All merchandise</RouterLink></li>
            <li><RouterLink to="/dashboard/orders">Track an order</RouterLink></li>
            <li><RouterLink to="/dashboard/wishlist">Your wishlist</RouterLink></li>
          </ul>
        </div>

        <div class="col-12 col-lg-6">
          <h6 class="mb-3">Newsletter</h6>
          <p class="mb-3">
            New merchandise and sales, and not much else. Unsubscribe whenever
            you like.
          </p>
          <form class="d-flex gap-2" @submit.prevent="subscribe">
            <input
              v-model="email"
              type="email"
              class="form-control form-control-sm"
              placeholder="you@student.rmit.edu.au"
              aria-label="Email address"
              required
            />
            <button class="btn btn-sm btn-primary flex-shrink-0" :disabled="submitting">
              {{ submitting ? 'Subscribing…' : 'Subscribe' }}
            </button>
          </form>
        </div>
      </div>

      <hr class="my-4 border-light opacity-25" />

      <p class="text-center mb-0 small">
        &copy; {{ new Date().getFullYear() }} RMIT Store. Built for COSC2767
        Systems Deployment and Operations.
      </p>
    </div>
  </footer>
</template>
