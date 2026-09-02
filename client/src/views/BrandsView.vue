<script setup>
import { storeToRefs } from 'pinia'
import { onMounted } from 'vue'

import LoadingIndicator from '@/components/common/LoadingIndicator.vue'
import { useCatalogStore } from '@/stores/catalog'

const catalog = useCatalogStore()
const { brands, loading } = storeToRefs(catalog)

onMounted(() => catalog.fetchBrands())
</script>

<template>
  <div class="container py-4">
    <h1 class="h3 page-title mb-4">Brands</h1>

    <LoadingIndicator v-if="loading && !brands.length" />

    <div v-else class="row row-cols-2 row-cols-md-3 row-cols-lg-4 g-3">
      <div v-for="brand in brands" :key="brand.id" class="col">
        <RouterLink
          class="data-card h-100 d-flex flex-column justify-content-between text-decoration-none"
          :to="{ name: 'shop-brand', params: { slug: brand.slug } }"
        >
          <div>
            <h2 class="h6 mb-1">{{ brand.name }}</h2>
            <p class="small text-muted mb-3">{{ brand.description }}</p>
          </div>
          <span class="badge text-bg-light align-self-start">
            {{ brand.product_count }} product{{ brand.product_count === 1 ? '' : 's' }}
          </span>
        </RouterLink>
      </div>
    </div>
  </div>
</template>
