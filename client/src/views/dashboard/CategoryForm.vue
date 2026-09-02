<script setup>
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
const form = reactive({
  name: '',
  description: '',
  is_active: true,
  products: []
})
const errors = ref({})
const saving = ref(false)

onMounted(async () => {
  await store.fetchProductOptions()

  if (!isEdit) return
  try {
    const category = await store.fetchCategory(route.params.id)
    Object.assign(form, {
      name: category.name,
      description: category.description,
      is_active: category.is_active,
      products: category.products || []
    })
  } catch (error) {
    ui.error(errorMessage(error))
    router.push('/dashboard/category')
  }
})

async function submit() {
  errors.value = {}
  saving.value = true
  try {
    if (isEdit) {
      await store.updateCategory(route.params.id, { ...form })
      ui.success('Category updated.')
    } else {
      await store.createCategory({ ...form })
      ui.success('Category created.')
    }
    router.push('/dashboard/category')
  } catch (error) {
    errors.value = fieldErrors(error)
    ui.error(errorMessage(error))
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <SubPage :title="isEdit ? 'Edit category' : 'Add category'">
    <template #action>
      <RouterLink class="btn btn-sm btn-outline-secondary" to="/dashboard/category">
        Back
      </RouterLink>
    </template>
  </SubPage>

  <form class="data-card" @submit.prevent="submit">
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
        rows="3"
      />
    </div>

    <div class="mb-3">
      <label class="form-label" for="products">Products in this category</label>
      <select id="products" v-model="form.products" class="form-select" multiple size="10">
        <option v-for="option in store.productOptions" :key="option.id" :value="option.id">
          {{ option.name }}
        </option>
      </select>
      <div class="form-text">
        Hold Command or Control to select more than one. A product can belong to
        several categories.
      </div>
    </div>

    <div class="form-check form-switch mb-2">
      <input id="active" v-model="form.is_active" class="form-check-input" type="checkbox" />
      <label class="form-check-label" for="active">Active</label>
    </div>
    <p class="form-text mb-4">
      Switching a category off also hides every product in it, including
      products that also belong to another category.
    </p>

    <button class="btn btn-primary" type="submit" :disabled="saving">
      {{ saving ? 'Saving…' : isEdit ? 'Save changes' : 'Create category' }}
    </button>
  </form>
</template>
