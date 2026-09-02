<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'

import { authApi } from '@/api'
import SubPage from '@/components/dashboard/SubPage.vue'
import { useAuthStore } from '@/stores/auth'
import { useUiStore } from '@/stores/ui'
import { errorMessage, fieldErrors } from '@/utils/format'

const auth = useAuthStore()
const ui = useUiStore()
const router = useRouter()

const form = reactive({
  current_password: '',
  new_password: '',
  confirm_password: ''
})
const errors = ref({})
const saving = ref(false)

async function submit() {
  errors.value = {}
  saving.value = true
  try {
    await authApi.changePassword({ ...form })
    ui.success('Your password has been changed. Please sign in again.')
    // Force a fresh sign-in so any other session with the old password is
    // clearly finished as far as the user is concerned.
    await auth.logout()
    router.push({ name: 'login' })
  } catch (error) {
    errors.value = fieldErrors(error)
    ui.error(errorMessage(error))
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <SubPage title="Account security" description="Change the password you sign in with." />

  <form class="data-card" style="max-width: 460px" @submit.prevent="submit">
    <div class="mb-3">
      <label class="form-label" for="current">Current password</label>
      <input
        id="current"
        v-model="form.current_password"
        type="password"
        class="form-control"
        :class="{ 'is-invalid': errors.current_password }"
        autocomplete="current-password"
        required
      />
      <div v-if="errors.current_password" class="invalid-feedback">
        {{ errors.current_password }}
      </div>
    </div>

    <div class="mb-3">
      <label class="form-label" for="new">New password</label>
      <input
        id="new"
        v-model="form.new_password"
        type="password"
        class="form-control"
        :class="{ 'is-invalid': errors.new_password }"
        autocomplete="new-password"
        minlength="8"
        required
      />
      <div v-if="errors.new_password" class="invalid-feedback">{{ errors.new_password }}</div>
    </div>

    <div class="mb-4">
      <label class="form-label" for="confirm">Confirm new password</label>
      <input
        id="confirm"
        v-model="form.confirm_password"
        type="password"
        class="form-control"
        :class="{ 'is-invalid': errors.confirm_password }"
        autocomplete="new-password"
        required
      />
      <div v-if="errors.confirm_password" class="invalid-feedback">
        {{ errors.confirm_password }}
      </div>
    </div>

    <button class="btn btn-primary" type="submit" :disabled="saving">
      {{ saving ? 'Saving…' : 'Change password' }}
    </button>
  </form>
</template>
