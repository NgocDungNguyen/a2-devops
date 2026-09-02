import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

import { brandApi, categoryApi, productApi } from '@/api'

const DEFAULT_FILTERS = {
  category: '',
  brand: '',
  search: '',
  min_price: null,
  max_price: null,
  min_rating: 0,
  ordering: 'newest',
  page: 1,
  page_size: 12
}

export const useCatalogStore = defineStore('catalog', () => {
  const products = ref([])
  const product = ref(null)
  const categories = ref([])
  const brands = ref([])
  const loading = ref(false)
  const filters = ref({ ...DEFAULT_FILTERS })
  const pagination = ref({
    count: 0,
    total_pages: 1,
    current_page: 1,
    page_size: 12
  })

  const showingFrom = computed(() =>
    pagination.value.count === 0
      ? 0
      : (pagination.value.current_page - 1) * pagination.value.page_size + 1
  )
  const showingTo = computed(() =>
    Math.min(
      pagination.value.current_page * pagination.value.page_size,
      pagination.value.count
    )
  )

  /** Drop empty values so the query string stays readable. */
  function activeParams() {
    const params = {}
    Object.entries(filters.value).forEach(([key, value]) => {
      if (value === null || value === '' || value === undefined) return
      if (key === 'min_rating' && !value) return
      params[key] = value
    })
    return params
  }

  async function fetchProducts() {
    loading.value = true
    try {
      const { data } = await productApi.list(activeParams())
      products.value = data.results
      pagination.value = {
        count: data.count,
        total_pages: data.total_pages,
        current_page: data.current_page,
        page_size: data.page_size
      }
    } finally {
      loading.value = false
    }
  }

  async function fetchProduct(slug) {
    loading.value = true
    product.value = null
    try {
      const { data } = await productApi.get(slug)
      product.value = data
      return data
    } finally {
      loading.value = false
    }
  }

  async function fetchCategories() {
    if (categories.value.length) return categories.value
    const { data } = await categoryApi.list()
    categories.value = data
    return data
  }

  async function fetchBrands() {
    if (brands.value.length) return brands.value
    const { data } = await brandApi.list()
    brands.value = data
    return data
  }

  /** Any filter change resets to page one, or you land on an empty page. */
  function setFilters(patch, { resetPage = true } = {}) {
    filters.value = {
      ...filters.value,
      ...patch,
      ...(resetPage ? { page: 1 } : {})
    }
    return fetchProducts()
  }

  function setPage(page) {
    filters.value.page = page
    return fetchProducts()
  }

  function resetFilters(overrides = {}) {
    filters.value = { ...DEFAULT_FILTERS, ...overrides }
  }

  /** Keeps the heart on a shop card in step with the wishlist store. */
  function applyLiked(productId, isLiked) {
    const found = products.value.find((item) => item.id === productId)
    if (found) found.is_liked = isLiked
    if (product.value?.id === productId) product.value.is_liked = isLiked
  }

  return {
    products,
    product,
    categories,
    brands,
    loading,
    filters,
    pagination,
    showingFrom,
    showingTo,
    fetchProducts,
    fetchProduct,
    fetchCategories,
    fetchBrands,
    setFilters,
    setPage,
    resetFilters,
    applyLiked
  }
})
