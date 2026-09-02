import { defineStore } from 'pinia'
import { ref } from 'vue'

import {
  manageBrandApi,
  manageCategoryApi,
  manageMerchantApi,
  manageProductApi,
  usersApi
} from '@/api'

/**
 * Dashboard CRUD for products, categories, brands, merchants and users.
 *
 * These five resources share one store because every screen that uses them is
 * the same shape — a paginated list, a form, and a delete — and because the
 * lists cross-reference each other (the product form needs the brand select,
 * the category form needs the product select).
 */
export const useManageStore = defineStore('manage', () => {
  const products = ref([])
  const categories = ref([])
  const brands = ref([])
  const merchants = ref([])
  const users = ref([])

  const brandOptions = ref([])
  const productOptions = ref([])

  const loading = ref(false)
  const pagination = ref({ count: 0, total_pages: 1, current_page: 1 })

  function capture(data, target) {
    target.value = data.results ?? data
    if (data.results) {
      pagination.value = {
        count: data.count,
        total_pages: data.total_pages,
        current_page: data.current_page
      }
    }
    return data
  }

  async function run(fn) {
    loading.value = true
    try {
      return await fn()
    } finally {
      loading.value = false
    }
  }

  // --- products ------------------------------------------------------------

  const fetchProducts = (params) =>
    run(async () => capture((await manageProductApi.list(params)).data, products))
  const fetchProduct = async (id) => (await manageProductApi.get(id)).data
  const createProduct = async (payload) => (await manageProductApi.create(payload)).data
  const updateProduct = async (id, payload) =>
    (await manageProductApi.update(id, payload)).data
  const deleteProduct = (id) => manageProductApi.remove(id)

  // --- categories ----------------------------------------------------------

  const fetchCategories = (params) =>
    run(async () => capture((await manageCategoryApi.list(params)).data, categories))
  const fetchCategory = async (id) => (await manageCategoryApi.get(id)).data
  const createCategory = async (payload) => (await manageCategoryApi.create(payload)).data
  const updateCategory = async (id, payload) =>
    (await manageCategoryApi.update(id, payload)).data
  const deleteCategory = (id) => manageCategoryApi.remove(id)

  // --- brands --------------------------------------------------------------

  const fetchBrands = (params) =>
    run(async () => capture((await manageBrandApi.list(params)).data, brands))
  const fetchBrand = async (id) => (await manageBrandApi.get(id)).data
  const createBrand = async (payload) => (await manageBrandApi.create(payload)).data
  const updateBrand = async (id, payload) => (await manageBrandApi.update(id, payload)).data
  const deleteBrand = (id) => manageBrandApi.remove(id)

  // --- merchants -----------------------------------------------------------

  const fetchMerchants = (params) =>
    run(async () => capture((await manageMerchantApi.list(params)).data, merchants))
  const approveMerchant = async (id) => (await manageMerchantApi.approve(id)).data
  const rejectMerchant = async (id) => (await manageMerchantApi.reject(id)).data
  const setMerchantActive = async (id, isActive) =>
    (await manageMerchantApi.update(id, { is_active: isActive })).data
  const deleteMerchant = (id) => manageMerchantApi.remove(id)

  // --- users ---------------------------------------------------------------

  const fetchUsers = (params) =>
    run(async () => capture((await usersApi.list(params)).data, users))

  // --- select options ------------------------------------------------------

  async function fetchBrandOptions() {
    const { data } = await manageBrandApi.select()
    brandOptions.value = data
    return data
  }

  async function fetchProductOptions() {
    const { data } = await manageProductApi.select()
    productOptions.value = data
    return data
  }

  return {
    products,
    categories,
    brands,
    merchants,
    users,
    brandOptions,
    productOptions,
    loading,
    pagination,
    fetchProducts,
    fetchProduct,
    createProduct,
    updateProduct,
    deleteProduct,
    fetchCategories,
    fetchCategory,
    createCategory,
    updateCategory,
    deleteCategory,
    fetchBrands,
    fetchBrand,
    createBrand,
    updateBrand,
    deleteBrand,
    fetchMerchants,
    approveMerchant,
    rejectMerchant,
    setMerchantActive,
    deleteMerchant,
    fetchUsers,
    fetchBrandOptions,
    fetchProductOptions
  }
})
