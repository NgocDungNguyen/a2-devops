<script setup>
import { storeToRefs } from 'pinia'
import { computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'

import LoadingIndicator from '@/components/common/LoadingIndicator.vue'
import PaginationBar from '@/components/common/PaginationBar.vue'
import ProductCard from '@/components/store/ProductCard.vue'
import ProductFilter from '@/components/store/ProductFilter.vue'
import { SORT_OPTIONS } from '@/config'
import { useCatalogStore } from '@/stores/catalog'

/**
 * One view backs /shop, /shop/category/:slug and /shop/brand/:slug — the three
 * differ only by which filter is pre-applied.
 */
const props = defineProps({
  categorySlug: { type: String, default: '' },
  brandSlug: { type: String, default: '' }
})

const route = useRoute()
const catalog = useCatalogStore()
const { products, loading, filters, pagination, showingFrom, showingTo } =
  storeToRefs(catalog)

const heading = computed(() => {
  if (props.categorySlug) {
    const match = catalog.categories.find((c) => c.slug === props.categorySlug)
    return match?.name || 'Category'
  }
  if (props.brandSlug) {
    const match = catalog.brands.find((b) => b.slug === props.brandSlug)
    return match?.name || 'Brand'
  }
  if (filters.value.search) return `Results for “${filters.value.search}”`
  return 'All merchandise'
})

function load() {
  catalog.resetFilters({
    category: props.categorySlug || '',
    brand: props.brandSlug || '',
    search: route.query.search || ''
  })
  return catalog.fetchProducts()
}

onMounted(load)

// Navigating between /shop/category/a and /shop/category/b reuses this
// component, so the params have to be watched rather than read once.
watch(() => [props.categorySlug, props.brandSlug, route.query.search], load)

function applyFilters(patch) {
  catalog.setFilters(patch)
}

function resetFilters() {
  catalog.resetFilters({
    category: props.categorySlug || '',
    brand: props.brandSlug || ''
  })
  catalog.fetchProducts()
}
</script>

<template>
  <div class="container py-4">
    <h1 class="h3 page-title mb-4">{{ heading }}</h1>

    <div class="row g-4">
      <div class="col-12 col-lg-3">
        <ProductFilter
          :min-price="filters.min_price"
          :max-price="filters.max_price"
          :min-rating="filters.min_rating"
          @apply="applyFilters"
          @reset="resetFilters"
        />
      </div>

      <div class="col-12 col-lg-9">
        <div
          class="d-flex flex-wrap gap-2 align-items-center justify-content-between mb-3"
        >
          <p class="text-muted small mb-0">
            <template v-if="pagination.count">
              Showing {{ showingFrom }}–{{ showingTo }} of
              {{ pagination.count }} products
            </template>
            <template v-else>No products match these filters</template>
          </p>

          <div class="d-flex align-items-center gap-2">
            <label class="form-label mb-0 small text-muted" for="sort">Sort by</label>
            <select
              id="sort"
              class="form-select form-select-sm"
              style="width: auto"
              :value="filters.ordering"
              @change="applyFilters({ ordering: $event.target.value })"
            >
              <option v-for="option in SORT_OPTIONS" :key="option.value" :value="option.value">
                {{ option.label }}
              </option>
            </select>
          </div>
        </div>

        <LoadingIndicator v-if="loading" />

        <template v-else>
          <div v-if="products.length" class="row row-cols-2 row-cols-md-3 g-3">
            <div v-for="product in products" :key="product.id" class="col">
              <ProductCard :product="product" />
            </div>
          </div>

          <div v-else class="text-center text-muted py-5">
            <p class="mb-3">Nothing here matches what you are looking for.</p>
            <button class="btn btn-sm btn-outline-primary" type="button" @click="resetFilters">
              Clear filters
            </button>
          </div>

          <div class="mt-4">
            <PaginationBar
              :current-page="pagination.current_page"
              :total-pages="pagination.total_pages"
              @change="catalog.setPage($event)"
            />
          </div>
        </template>
      </div>
    </div>
  </div>
</template>
