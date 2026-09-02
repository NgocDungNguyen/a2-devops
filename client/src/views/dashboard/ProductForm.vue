<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import SubPage from '@/components/dashboard/SubPage.vue'
import { useAuthStore } from '@/stores/auth'
import { useCatalogStore } from '@/stores/catalog'
import { useManageStore } from '@/stores/manage'
import { useUiStore } from '@/stores/ui'
import { errorMessage, fieldErrors, imageOrPlaceholder } from '@/utils/format'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const catalog = useCatalogStore()
const store = useManageStore()
const ui = useUiStore()

const isEdit = Boolean(route.params.id)
const form = reactive({
  sku: '',
  name: '',
  description: '',
  quantity: 0,
  price: '',
  taxable: false,
  is_active: true,
  brand: '',
  categories: []
})
const imageFile = ref(null)
const currentImage = ref('')
const errors = ref({})
const saving = ref(false)

onMounted(async () => {
  // A merchant never picks a brand — theirs is implied, and the server
  // rejects any attempt to file a product under someone else's.
  if (auth.isAdmin) await store.fetchBrandOptions()
  await catalog.fetchCategories()

  if (!isEdit) return
  try {
    const product = await store.fetchProduct(route.params.id)
    Object.assign(form, {
      sku: product.sku,
      name: product.name,
      description: product.description,
      quantity: product.quantity,
      price: product.price,
      taxable: product.taxable,
      is_active: product.is_active,
      brand: product.brand || '',
      categories: product.categories || []
    })
    currentImage.value = product.image_url || ''
  } catch (error) {
    ui.error(errorMessage(error))
    router.push('/dashboard/product')
  }
})

function onFileChange(event) {
  imageFile.value = event.target.files?.[0] || null
}

async function submit() {
  errors.value = {}
  saving.value = true

  const payload = { ...form }
  if (!auth.isAdmin) delete payload.brand
  if (imageFile.value) payload.image = imageFile.value

  try {
    if (isEdit) {
      await store.updateProduct(route.params.id, payload)
      ui.success('Product updated.')
    } else {
      await store.createProduct(payload)
      ui.success('Product created.')
    }
    router.push('/dashboard/product')
  } catch (error) {
    errors.value = fieldErrors(error)
    ui.error(errorMessage(error))
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <SubPage :title="isEdit ? 'Edit product' : 'Add product'">
    <template #action>
      <RouterLink class="btn btn-sm btn-outline-secondary" to="/dashboard/product">
        Back
      </RouterLink>
    </template>
  </SubPage>

  <form class="data-card" @submit.prevent="submit">
    <div class="row g-3 mb-3">
      <div class="col-12 col-sm-6">
        <label class="form-label" for="sku">SKU</label>
        <input
          id="sku"
          v-model="form.sku"
          type="text"
          class="form-control"
          :class="{ 'is-invalid': errors.sku }"
          required
        />
        <div v-if="errors.sku" class="invalid-feedback">{{ errors.sku }}</div>
      </div>

      <div class="col-12 col-sm-6">
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
    </div>

    <div class="mb-3">
      <label class="form-label" for="description">Description</label>
      <textarea
        id="description"
        v-model="form.description"
        class="form-control"
        :class="{ 'is-invalid': errors.description }"
        rows="4"
      />
      <div v-if="errors.description" class="invalid-feedback">{{ errors.description }}</div>
    </div>

    <div class="row g-3 mb-3">
      <div class="col-12 col-sm-4">
        <label class="form-label" for="quantity">Stock quantity</label>
        <input
          id="quantity"
          v-model.number="form.quantity"
          type="number"
          min="0"
          class="form-control"
          :class="{ 'is-invalid': errors.quantity }"
          required
        />
        <div v-if="errors.quantity" class="invalid-feedback">{{ errors.quantity }}</div>
      </div>

      <div class="col-12 col-sm-4">
        <label class="form-label" for="price">Price</label>
        <input
          id="price"
          v-model="form.price"
          type="number"
          min="0"
          step="0.01"
          class="form-control"
          :class="{ 'is-invalid': errors.price }"
          required
        />
        <div v-if="errors.price" class="invalid-feedback">{{ errors.price }}</div>
      </div>

      <div class="col-12 col-sm-4">
        <label class="form-label" for="taxable">Sales tax</label>
        <select id="taxable" v-model="form.taxable" class="form-select">
          <option :value="false">Not taxable</option>
          <option :value="true">Taxable</option>
        </select>
      </div>
    </div>

    <div v-if="auth.isAdmin" class="mb-3">
      <label class="form-label" for="brand">Brand</label>
      <select
        id="brand"
        v-model="form.brand"
        class="form-select"
        :class="{ 'is-invalid': errors.brand }"
      >
        <option value="">No brand</option>
        <option v-for="option in store.brandOptions" :key="option.id" :value="option.id">
          {{ option.name }}
        </option>
      </select>
      <div v-if="errors.brand" class="invalid-feedback">{{ errors.brand }}</div>
    </div>

    <div v-else class="mb-3">
      <label class="form-label">Brand</label>
      <input class="form-control" :value="auth.user?.merchant?.brand_name" disabled />
      <div class="form-text">Products you add are listed under your own brand.</div>
    </div>

    <div class="mb-3">
      <label class="form-label" for="categories">Categories</label>
      <select
        id="categories"
        v-model="form.categories"
        class="form-select"
        multiple
        size="6"
      >
        <option v-for="category in catalog.categories" :key="category.id" :value="category.id">
          {{ category.name }}
        </option>
      </select>
      <div class="form-text">Hold Command or Control to select more than one.</div>
    </div>

    <div class="mb-3">
      <label class="form-label" for="image">Product image</label>
      <input
        id="image"
        type="file"
        class="form-control"
        accept="image/*"
        @change="onFileChange"
      />
      <img
        v-if="currentImage"
        :src="imageOrPlaceholder(currentImage)"
        alt="Current product image"
        width="96"
        height="96"
        class="rounded object-fit-cover mt-2"
      />
    </div>

    <div class="form-check form-switch mb-4">
      <input id="active" v-model="form.is_active" class="form-check-input" type="checkbox" />
      <label class="form-check-label" for="active">
        Active — visible in the store
      </label>
    </div>

    <button class="btn btn-primary" type="submit" :disabled="saving">
      {{ saving ? 'Saving…' : isEdit ? 'Save changes' : 'Create product' }}
    </button>
  </form>
</template>
