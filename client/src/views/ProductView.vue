<script setup>
/**
 * A single product page: /product/:slug.
 *
 * The busiest view in the store, and a fair illustration of how the pieces fit
 * together. It owns no data of its own - the product comes from the catalog
 * store, the reviews from the reviews store, the bag from the cart store - and
 * its job is to arrange them and to translate clicks into store calls.
 *
 * Addressed by *slug* rather than id, so the URL reads /product/rmit-hoodie.
 * The slug is generated from the name when a product is saved and is treated
 * as permanent afterwards, which is why the admin cannot edit it: changing one
 * would break every link anybody has bookmarked or shared.
 */
import { storeToRefs } from 'pinia'
import { computed, ref, watch } from 'vue'
import { useRoute } from 'vue-router'

import AppIcon from '@/components/common/AppIcon.vue'
import LoadingIndicator from '@/components/common/LoadingIndicator.vue'
import PaginationBar from '@/components/common/PaginationBar.vue'
import StarRating from '@/components/common/StarRating.vue'
import ReviewForm from '@/components/store/ReviewForm.vue'
import ReviewList from '@/components/store/ReviewList.vue'
import ReviewSummary from '@/components/store/ReviewSummary.vue'
import { useAuthStore } from '@/stores/auth'
import { useCartStore } from '@/stores/cart'
import { useCatalogStore } from '@/stores/catalog'
import { useReviewsStore } from '@/stores/reviews'
import { useUiStore } from '@/stores/ui'
import { useWishlistStore } from '@/stores/wishlist'
import { errorMessage, imageOrPlaceholder, money } from '@/utils/format'

const route = useRoute()
const auth = useAuthStore()
const cart = useCartStore()
const catalog = useCatalogStore()
const reviewsStore = useReviewsStore()
const ui = useUiStore()
const wishlist = useWishlistStore()

const { product, loading } = storeToRefs(catalog)
const { reviews, summary, pagination } = storeToRefs(reviewsStore)

const quantity = ref(1)
const notFound = ref(false)

const inCart = computed(() => Boolean(product.value && cart.find(product.value.id)))

/**
 * The ceiling on the quantity selector: whichever is smaller of the per-order
 * purchase cap and what is actually in stock, and never below 1 so the input
 * stays usable while the product is still loading.
 *
 * This is a courtesy, not an enforcement. The stock check that counts happens
 * inside the checkout transaction on the server, with the product row locked -
 * anything decided here is already out of date by the time the request lands,
 * because another shopper may have bought the last one in between.
 */
const maxQuantity = computed(() => {
  if (!product.value) return 1
  return Math.max(
    1,
    Math.min(cart.maxPurchaseQuantity(product.value.quantity), product.value.quantity)
  )
})

async function load(slug) {
  notFound.value = false
  quantity.value = 1
  try {
    await catalog.fetchProduct(slug)
    await reviewsStore.fetchForProduct(slug)
  } catch (error) {
    // A 404 is a page state ("no such product"), not an error worth shouting
    // about - someone followed a stale link. Anything else is unexpected and
    // gets a toast.
    if (error?.response?.status === 404) notFound.value = true
    else ui.error(errorMessage(error))
  }
}

// Watching the route parameter rather than loading once on mount. Vue Router
// reuses the component when only the parameter changes, so navigating from one
// product straight to another - via a "related products" link - does not
// remount anything, and a plain onMounted() would leave the old product on
// screen. `immediate: true` covers the first load.
watch(() => route.params.slug, load, { immediate: true })

function addToBag() {
  cart.add(product.value, quantity.value)
  ui.success(`${product.value.name} added to your bag.`)
  ui.openCart()
}

function removeFromBag() {
  cart.remove(product.value.id)
  ui.info('Removed from your bag.')
}

async function toggleWishlist() {
  if (!auth.isAuthenticated) {
    ui.info('Sign in to save items to your wishlist.')
    return
  }
  try {
    await wishlist.toggle(product.value.id, !product.value.is_liked)
  } catch (error) {
    ui.error(errorMessage(error))
  }
}

function changeReviewPage(page) {
  reviewsStore.fetchForProduct(route.params.slug, { page })
}

const shareUrl = computed(() =>
  typeof window !== 'undefined' ? window.location.href : ''
)
</script>

<template>
  <div class="container py-4">
    <LoadingIndicator v-if="loading && !product" />

    <div v-else-if="notFound" class="text-center py-5">
      <h1 class="h4 page-title">We could not find that product</h1>
      <p class="text-muted">It may have been removed or is no longer on sale.</p>
      <RouterLink class="btn btn-primary" to="/shop">Back to the shop</RouterLink>
    </div>

    <template v-else-if="product">
      <RouterLink class="btn btn-sm btn-link px-0 mb-3" to="/shop">
        <AppIcon name="arrowLeft" :size="14" /> Back to the shop
      </RouterLink>

      <div class="row g-4 mb-5">
        <div class="col-12 col-md-6">
          <img
            class="img-fluid rounded border w-100 object-fit-cover"
            style="aspect-ratio: 1"
            :src="imageOrPlaceholder(product.image_url)"
            :alt="product.name"
          />
        </div>

        <div class="col-12 col-md-6">
          <p v-if="product.brand_name" class="text-muted small text-uppercase mb-1">
            <RouterLink :to="{ name: 'shop-brand', params: { slug: product.brand_slug } }">
              {{ product.brand_name }}
            </RouterLink>
          </p>

          <h1 class="h3 page-title mb-2">{{ product.name }}</h1>

          <div class="d-flex align-items-center gap-2 mb-3">
            <StarRating :model-value="product.rating_avg" :size="16" />
            <small class="text-muted">
              {{ product.rating_count }} review{{ product.rating_count === 1 ? '' : 's' }}
            </small>
          </div>

          <p class="h4 text-brand mb-3">{{ money(product.price) }}</p>

          <p class="mb-3">
            <span v-if="product.in_stock" class="badge text-bg-success">In stock</span>
            <span v-else class="badge text-bg-secondary">Out of stock</span>
            <span class="text-muted small ms-2">SKU {{ product.sku }}</span>
          </p>

          <p class="mb-4">{{ product.description }}</p>

          <div v-if="product.categories?.length" class="mb-4">
            <span class="text-muted small me-2">Categories:</span>
            <RouterLink
              v-for="category in product.categories"
              :key="category.id"
              class="badge text-bg-light me-1"
              :to="{ name: 'shop-category', params: { slug: category.slug } }"
            >
              {{ category.name }}
            </RouterLink>
          </div>

          <div class="d-flex flex-wrap align-items-end gap-3">
            <div v-if="product.in_stock" style="width: 110px">
              <label class="form-label small" for="quantity">Quantity</label>
              <input
                id="quantity"
                v-model.number="quantity"
                type="number"
                class="form-control"
                min="1"
                :max="maxQuantity"
              />
            </div>

            <button
              v-if="!inCart"
              class="btn btn-primary"
              type="button"
              :disabled="!product.in_stock"
              @click="addToBag"
            >
              Add to bag
            </button>
            <button v-else class="btn btn-outline-danger" type="button" @click="removeFromBag">
              Remove from bag
            </button>

            <button
              class="btn btn-outline-secondary d-flex align-items-center gap-2"
              type="button"
              :aria-pressed="product.is_liked"
              @click="toggleWishlist"
            >
              <AppIcon name="heart" :size="16" :filled="product.is_liked" />
              {{ product.is_liked ? 'Saved' : 'Save' }}
            </button>
          </div>

          <p v-if="product.in_stock && maxQuantity < product.quantity" class="small text-muted mt-2">
            Limited to {{ maxQuantity }} per order.
          </p>

          <div class="mt-4 pt-3 border-top small">
            <span class="text-muted me-2">Share:</span>
            <a
              class="me-2"
              :href="`https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(shareUrl)}`"
              target="_blank"
              rel="noopener"
              >Facebook</a
            >
            <a
              class="me-2"
              :href="`https://twitter.com/intent/tweet?url=${encodeURIComponent(shareUrl)}&text=${encodeURIComponent(product.name)}`"
              target="_blank"
              rel="noopener"
              >X</a
            >
            <a
              :href="`mailto:?subject=${encodeURIComponent(product.name)}&body=${encodeURIComponent(shareUrl)}`"
              >Email</a
            >
          </div>
        </div>
      </div>

      <section class="mb-4">
        <h2 class="h5 page-title mb-3">Customer reviews</h2>
        <div class="data-card mb-4">
          <ReviewSummary :summary="summary" />
        </div>

        <div class="row g-4">
          <div class="col-12 col-lg-7">
            <ReviewList :reviews="reviews" />
            <div class="mt-4">
              <PaginationBar
                :current-page="pagination.current_page"
                :total-pages="pagination.total_pages"
                @change="changeReviewPage"
              />
            </div>
          </div>

          <div class="col-12 col-lg-5">
            <ReviewForm
              :product-id="product.id"
              @created="load(route.params.slug)"
            />
          </div>
        </div>
      </section>
    </template>
  </div>
</template>
