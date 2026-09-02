<script setup>
import { reactive, ref, watch } from 'vue'

import { accountApi } from '@/api'
import SubPage from '@/components/dashboard/SubPage.vue'
import { useAuthStore } from '@/stores/auth'
import { useUiStore } from '@/stores/ui'
import { errorMessage, fieldErrors } from '@/utils/format'

const auth = useAuthStore()
const ui = useUiStore()

const form = reactive({ first_name: '', last_name: '', phone_number: '' })
const errors = ref({})
const saving = ref(false)

watch(
  () => auth.user,
  (user) => {
    if (!user) return
    form.first_name = user.first_name || ''
    form.last_name = user.last_name || ''
    form.phone_number = user.phone_number || ''
  },
  { immediate: true }
)

async function save() {
  errors.value = {}
  saving.value = true
  try {
    // Only these three fields are writable, on the server as well as here.
    const { data } = await accountApi.updateMe({ ...form })
    auth.setUser(data)
    ui.success('Your details have been saved.')
  } catch (error) {
    errors.value = fieldErrors(error)
    ui.error(errorMessage(error))
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <SubPage title="Account details" description="Your name and contact number." />

  <form class="data-card" @submit.prevent="save">
    <div class="row g-3 mb-3">
      <div class="col-12 col-sm-6">
        <label class="form-label" for="first-name">First name</label>
        <input
          id="first-name"
          v-model="form.first_name"
          type="text"
          class="form-control"
          :class="{ 'is-invalid': errors.first_name }"
        />
        <div v-if="errors.first_name" class="invalid-feedback">{{ errors.first_name }}</div>
      </div>

      <div class="col-12 col-sm-6">
        <label class="form-label" for="last-name">Last name</label>
        <input
          id="last-name"
          v-model="form.last_name"
          type="text"
          class="form-control"
          :class="{ 'is-invalid': errors.last_name }"
        />
        <div v-if="errors.last_name" class="invalid-feedback">{{ errors.last_name }}</div>
      </div>
    </div>

    <div class="mb-3">
      <label class="form-label" for="phone">Phone number</label>
      <input
        id="phone"
        v-model="form.phone_number"
        type="tel"
        class="form-control"
        :class="{ 'is-invalid': errors.phone_number }"
      />
      <div v-if="errors.phone_number" class="invalid-feedback">
        {{ errors.phone_number }}
      </div>
    </div>

    <div class="mb-4">
      <label class="form-label" for="email">Email</label>
      <input id="email" :value="auth.user?.email" type="email" class="form-control" disabled />
      <div class="form-text">
        Your email address is your sign-in name and cannot be changed here.
      </div>
    </div>

    <button class="btn btn-primary" type="submit" :disabled="saving">
      {{ saving ? 'Saving…' : 'Save changes' }}
    </button>
  </form>
</template>
