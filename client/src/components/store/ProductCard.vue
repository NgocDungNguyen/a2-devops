<script setup>
/**
 * One product in a grid - on the shop page, the home page and the wishlist.
 *
 * A good first component to read. `<script setup>` is Vue's shorthand: every
 * top-level binding is available in the template below, with no `return` and
 * no `data()`.
 *
 * The card takes a whole `product` object and renders it. It deliberately does
 * not fetch anything - whichever page owns the grid loads the list, and this
 * component is handed one row of it. That is what lets the same card appear in
 * three places that get their data three different ways.
 */
import AppIcon from '@/components/common/AppIcon.vue'
import StarRating from '@/components/common/StarRating.vue'
import { useAuthStore } from '@/stores/auth'
import { useUiStore } from '@/stores/ui'
import { useWishlistStore } from '@/stores/wishlist'
import { errorMessage, imageOrPlaceholder, money } from '@/utils/format'

// `product` is the shape the storefront API returns for a list row - see
// ProductListSerializer on the server for the authoritative field list.
const props = defineProps({
  product: { type: Object, required: true }
})

const auth = useAuthStore()
const wishlist = useWishlistStore()
const ui = useUiStore()

async function toggleWishlist() {
  // Checked here only to give a signed-out visitor a useful nudge instead of
  // a 401 they cannot act on. This is not the security boundary - the API
  // rejects the request regardless, and that is what actually protects the
  // wishlist. Never rely on a check in the browser for anything but manners.
  if (!auth.isAuthenticated) {
    ui.info('Sign in to save items to your wishlist.')
    return
  }
  try {
    await wishlist.toggle(props.product.id, !props.product.is_liked)
  } catch (error) {
    // `errorMessage` digs the server's sentence out of the axios error, so
    // the user sees "That product is unavailable" rather than "Request
    // failed with status code 400".
    ui.error(errorMessage(error))
  }
}
</script>

<template>
  <article class="product-card">
    <button
      type="button"
      class="wishlist-button"
      :class="{ 'is-liked': product.is_liked }"
      :aria-label="product.is_liked ? 'Remove from wishlist' : 'Add to wishlist'"
      :aria-pressed="product.is_liked"
      @click="toggleWishlist"
    >
      <AppIcon name="heart" :size="17" :filled="product.is_liked" />
    </button>

    <RouterLink :to="{ name: 'product', params: { slug: product.slug } }">
      <!--
        `loading="lazy"` matters more than it looks: the shop grid is 12 cards,
        and without it every image is fetched before the page settles. The
        placeholder covers products with no photograph, so a broken image icon
        never reaches the page.
      -->
      <img
        class="product-card__image"
        :src="imageOrPlaceholder(product.image_url)"
        :alt="product.name"
        loading="lazy"
      />
    </RouterLink>

    <div class="product-card__body">
      <div v-if="product.brand_name" class="product-card__brand mb-1">
        {{ product.brand_name }}
      </div>

      <RouterLink
        class="product-card__name"
        :to="{ name: 'product', params: { slug: product.slug } }"
      >
        {{ product.name }}
      </RouterLink>

      <div class="d-flex align-items-center gap-1 mt-2 mb-2">
        <StarRating :model-value="product.rating_avg" :size="14" />
        <small class="text-muted">
          {{ product.rating_count ? `(${product.rating_count})` : 'No reviews yet' }}
        </small>
      </div>

      <div class="d-flex align-items-center justify-content-between">
        <span class="product-card__price">{{ money(product.price) }}</span>
        <span v-if="!product.in_stock" class="badge text-bg-secondary">Out of stock</span>
      </div>
    </div>
  </article>
</template>
