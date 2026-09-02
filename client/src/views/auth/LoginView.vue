<script setup>
import { reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { useAuthStore } from '@/stores/auth'
import { useUiStore } from '@/stores/ui'
import { useWishlistStore } from '@/stores/wishlist'
import { errorMessage, fieldErrors } from '@/utils/format'

const auth = useAuthStore()
const ui = useUiStore()
const wishlist = useWishlistStore()
const route = useRoute()
const router = useRouter()

const form = reactive({ email: '', password: '' })
const errors = ref({})
const submitting = ref(false)

async function submit() {
  errors.value = {}
  submitting.value = true
  try {
    const user = await auth.login({ ...form })
    // Prime the wishlist so hearts render correctly straight away.
    wishlist.fetch().catch(() => {})
    ui.success(`Welcome back, ${user.first_name || user.email}.`)
    router.push(route.query.next || { name: 'dashboard' })
  } catch (error) {
    errors.value = fieldErrors(error)
    ui.error(errorMessage(error, 'That email and password did not match.'))
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="container py-5" style="max-width: 420px">
    <h1 class="h4 page-title mb-4">Sign in</h1>

    <form class="data-card" @submit.prevent="submit">
      <div class="mb-3">
        <label class="form-label" for="email">Email</label>
        <input
          id="email"
          v-model="form.email"
          type="email"
          class="form-control"
          :class="{ 'is-invalid': errors.email }"
          autocomplete="email"
          required
        />
        <div v-if="errors.email" class="invalid-feedback">{{ errors.email }}</div>
      </div>

      <div class="mb-3">
        <label class="form-label" for="password">Password</label>
        <input
          id="password"
          v-model="form.password"
          type="password"
          class="form-control"
          :class="{ 'is-invalid': errors.password }"
          autocomplete="current-password"
          required
        />
        <div v-if="errors.password" class="invalid-feedback">{{ errors.password }}</div>
      </div>

      <button class="btn btn-primary w-100 mb-3" type="submit" :disabled="submitting">
        {{ submitting ? 'Signing in…' : 'Sign in' }}
      </button>

      <div class="d-flex justify-content-between small">
        <RouterLink to="/register">Create an account</RouterLink>
        <RouterLink to="/forgot-password">Forgot your password?</RouterLink>
      </div>
    </form>
  </div>
</template>
