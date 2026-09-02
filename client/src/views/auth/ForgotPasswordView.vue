<script setup>
import { ref } from 'vue'

import { authApi } from '@/api'
import { useUiStore } from '@/stores/ui'
import { errorMessage } from '@/utils/format'

const ui = useUiStore()
const email = ref('')
const submitting = ref(false)
const sent = ref(false)

async function submit() {
  submitting.value = true
  try {
    await authApi.forgotPassword(email.value.trim())
    // The server answers the same way whether or not the address is
    // registered, so this message is deliberately non-committal.
    sent.value = true
  } catch (error) {
    ui.error(errorMessage(error))
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="container py-5" style="max-width: 420px">
    <h1 class="h4 page-title mb-4">Reset your password</h1>

    <div v-if="sent" class="alert alert-info">
      If an account exists for <strong>{{ email }}</strong>, a reset link is on
      its way. The link is valid for one hour.
      <div class="mt-3">
        <RouterLink class="btn btn-sm btn-primary" to="/login">Back to sign in</RouterLink>
      </div>
    </div>

    <form v-else class="data-card" @submit.prevent="submit">
      <p class="text-muted small">
        Enter the email address on your account and we will send you a link to
        choose a new password.
      </p>

      <div class="mb-3">
        <label class="form-label" for="email">Email</label>
        <input
          id="email"
          v-model="email"
          type="email"
          class="form-control"
          autocomplete="email"
          required
        />
      </div>

      <button class="btn btn-primary w-100 mb-3" type="submit" :disabled="submitting">
        {{ submitting ? 'Sending…' : 'Send reset link' }}
      </button>

      <p class="small text-center mb-0">
        <RouterLink to="/login">Back to sign in</RouterLink>
      </p>
    </form>
  </div>
</template>
