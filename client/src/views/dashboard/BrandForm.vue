<script setup>
/**
 * Dashboard > Brands > add / edit. **The form half of the dashboard CRUD
 * pattern**, shared in outline with CategoryForm, AddressForm and ProductForm.
 *
 * One component serves both "add" and "edit": `isEdit` is decided by whether
 * the route carries an :id, and the only differences that follow are whether
 * the existing record is loaded on mount and which store method is called on
 * submit. Two nearly identical components would drift apart within a semester.
 *
 * Note the two kinds of error, because this pairing recurs everywhere in the
 * SPA and the server is built to support it:
 *
 *   errors.value = fieldErrors(error)   -> {name: "This field is required."}
 *                                          rendered against the input
 *   ui.error(errorMessage(error))       -> one sentence, in a toast
 *
 * A 400 from DRF carries per-field messages *and* the flattened `detail`
 * sentence that apps/core/exceptions.py adds, so both lines read from the same
 * response and neither has to guess.
 *
 * `reactive({...})` rather than a `ref` per input: one object that v-model can
 * write into, and one `{ ...form }` to send. There is no client-side
 * validation at all here - the server owns the rules, and duplicating them in
 * the browser means maintaining them twice and being wrong in one of the two.
 */
import { onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import SubPage from '@/components/dashboard/SubPage.vue'
import { useManageStore } from '@/stores/manage'
import { useUiStore } from '@/stores/ui'
import { errorMessage, fieldErrors } from '@/utils/format'

const route = useRoute()
const router = useRouter()
const store = useManageStore()
const ui = useUiStore()

const isEdit = Boolean(route.params.id)
const form = reactive({ name: '', description: '', is_active: true })
const errors = ref({})
const saving = ref(false)

onMounted(async () => {
  if (!isEdit) return
  try {
    const brand = await store.fetchBrand(route.params.id)
    Object.assign(form, {
      name: brand.name,
      description: brand.description,
      is_active: brand.is_active
    })
  } catch (error) {
    ui.error(errorMessage(error))
    router.push('/dashboard/brand')
  }
})

async function submit() {
  errors.value = {}
  saving.value = true
  try {
    if (isEdit) {
      await store.updateBrand(route.params.id, { ...form })
      ui.success('Brand updated.')
    } else {
      await store.createBrand({ ...form })
      ui.success('Brand created.')
    }
    router.push('/dashboard/brand')
  } catch (error) {
    errors.value = fieldErrors(error)
    ui.error(errorMessage(error))
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <SubPage :title="isEdit ? 'Edit brand' : 'Add brand'">
    <template #action>
      <RouterLink class="btn btn-sm btn-outline-secondary" to="/dashboard/brand">
        Back
      </RouterLink>
    </template>
  </SubPage>

  <form class="data-card" style="max-width: 560px" @submit.prevent="submit">
    <div class="mb-3">
      <label class="form-label" for="name">Name</label>
      <input
        id="name"
        v-model="form.name"
        type="text"
        class="form-control"
        :class="{ 'is-invalid': errors.name }"
        required
      />
      <div v-if="errors.name" class="invalid-feedback">{{ errors.name }}</div>
    </div>

    <div class="mb-3">
      <label class="form-label" for="description">Description</label>
      <textarea
        id="description"
        v-model="form.description"
        class="form-control"
        :class="{ 'is-invalid': errors.description }"
        rows="3"
      />
      <div v-if="errors.description" class="invalid-feedback">{{ errors.description }}</div>
    </div>

    <div class="form-check form-switch mb-2">
      <input id="active" v-model="form.is_active" class="form-check-input" type="checkbox" />
      <label class="form-check-label" for="active">Active</label>
    </div>
    <p class="form-text mb-4">
      Switching a brand off also hides every product belonging to it.
    </p>

    <button class="btn btn-primary" type="submit" :disabled="saving">
      {{ saving ? 'Saving…' : isEdit ? 'Save changes' : 'Create brand' }}
    </button>
  </form>
</template>
