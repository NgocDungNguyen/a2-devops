<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import SubPage from '@/components/dashboard/SubPage.vue'
import { useAddressStore } from '@/stores/addresses'
import { useUiStore } from '@/stores/ui'
import { errorMessage, fieldErrors } from '@/utils/format'

const route = useRoute()
const router = useRouter()
const store = useAddressStore()
const ui = useUiStore()

const isEdit = Boolean(route.params.id)
const form = reactive({
  address: '',
  city: '',
  state: '',
  country: 'Australia',
  zip_code: '',
  is_default: false
})
const errors = ref({})
const saving = ref(false)

onMounted(async () => {
  if (!isEdit) return
  try {
    Object.assign(form, await store.fetchOne(route.params.id))
  } catch (error) {
    ui.error(errorMessage(error))
    router.push('/dashboard/address')
  }
})

async function submit() {
  errors.value = {}
  saving.value = true
  try {
    if (isEdit) {
      await store.update(route.params.id, { ...form })
      ui.success('Address updated.')
    } else {
      await store.create({ ...form })
      ui.success('Address added.')
    }
    router.push('/dashboard/address')
  } catch (error) {
    errors.value = fieldErrors(error)
    ui.error(errorMessage(error))
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <SubPage :title="isEdit ? 'Edit address' : 'Add address'">
    <template #action>
      <RouterLink class="btn btn-sm btn-outline-secondary" to="/dashboard/address">
        Back
      </RouterLink>
    </template>
  </SubPage>

  <form class="data-card" style="max-width: 560px" @submit.prevent="submit">
    <div class="mb-3">
      <label class="form-label" for="street">Street address</label>
      <input
        id="street"
        v-model="form.address"
        type="text"
        class="form-control"
        :class="{ 'is-invalid': errors.address }"
        required
      />
      <div v-if="errors.address" class="invalid-feedback">{{ errors.address }}</div>
    </div>

    <div class="row g-3 mb-3">
      <div class="col-12 col-sm-6">
        <label class="form-label" for="city">City</label>
        <input
          id="city"
          v-model="form.city"
          type="text"
          class="form-control"
          :class="{ 'is-invalid': errors.city }"
          required
        />
        <div v-if="errors.city" class="invalid-feedback">{{ errors.city }}</div>
      </div>

      <div class="col-12 col-sm-6">
        <label class="form-label" for="state">State</label>
        <input
          id="state"
          v-model="form.state"
          type="text"
          class="form-control"
          :class="{ 'is-invalid': errors.state }"
          required
        />
        <div v-if="errors.state" class="invalid-feedback">{{ errors.state }}</div>
      </div>
    </div>

    <div class="row g-3 mb-3">
      <div class="col-12 col-sm-6">
        <label class="form-label" for="zip">Postcode</label>
        <input
          id="zip"
          v-model="form.zip_code"
          type="text"
          class="form-control"
          :class="{ 'is-invalid': errors.zip_code }"
          required
        />
        <div v-if="errors.zip_code" class="invalid-feedback">{{ errors.zip_code }}</div>
      </div>

      <div class="col-12 col-sm-6">
        <label class="form-label" for="country">Country</label>
        <input
          id="country"
          v-model="form.country"
          type="text"
          class="form-control"
          :class="{ 'is-invalid': errors.country }"
          required
        />
        <div v-if="errors.country" class="invalid-feedback">{{ errors.country }}</div>
      </div>
    </div>

    <div class="form-check mb-4">
      <input id="default" v-model="form.is_default" class="form-check-input" type="checkbox" />
      <label class="form-check-label" for="default">
        Use this as my default delivery address
      </label>
    </div>

    <button class="btn btn-primary" type="submit" :disabled="saving">
      {{ saving ? 'Saving…' : isEdit ? 'Save changes' : 'Add address' }}
    </button>
  </form>
</template>
