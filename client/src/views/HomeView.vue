<script setup>
import { onMounted, onUnmounted, ref } from 'vue'

import LoadingIndicator from '@/components/common/LoadingIndicator.vue'
import ProductCard from '@/components/store/ProductCard.vue'
import { productApi } from '@/api'

const BANNERS = [
  {
    image: '/images/banners/banner-1.jpg',
    title: 'Holiday specials',
    text: 'Hoodies, tees and lanyards, ready for the break.',
    to: '/shop'
  },
  {
    image: '/images/banners/banner-2.png',
    title: 'Sustainable living',
    text: 'Reusable cups and bottles from student-run labels.',
    to: '/brands'
  },
  {
    image: '/images/banners/banner-3.jpg',
    title: 'Tech deals',
    text: 'Accessories to keep you going through assessment week.',
    to: '/shop'
  }
]

const slide = ref(0)
const featured = ref([])
const loading = ref(true)
let timer = null

onMounted(async () => {
  timer = setInterval(() => {
    slide.value = (slide.value + 1) % BANNERS.length
  }, 6000)

  try {
    // The original homepage showed banners and nothing else. A row of
    // top-rated products gives a first-time visitor something to click.
    const { data } = await productApi.list({ ordering: 'rating', page_size: 8 })
    featured.value = data.results
  } finally {
    loading.value = false
  }
})

onUnmounted(() => clearInterval(timer))
</script>

<template>
  <div class="container py-4">
    <section class="hero mb-5">
      <img
        :src="BANNERS[slide].image"
        :alt="BANNERS[slide].title"
        class="hero__image"
      />
      <div class="hero__content">
        <h1 class="display-6 fw-semibold mb-3">{{ BANNERS[slide].title }}</h1>
        <p class="lead mb-4">{{ BANNERS[slide].text }}</p>
        <RouterLink class="btn btn-primary btn-lg" :to="BANNERS[slide].to">
          Shop now
        </RouterLink>

        <div class="d-flex gap-2 mt-4" role="tablist" aria-label="Banner">
          <button
            v-for="(banner, index) in BANNERS"
            :key="banner.title"
            type="button"
            class="btn btn-sm rounded-pill px-3"
            :class="index === slide ? 'btn-light' : 'btn-outline-light'"
            :aria-selected="index === slide"
            role="tab"
            @click="slide = index"
          >
            {{ index + 1 }}
          </button>
        </div>
      </div>
    </section>

    <section>
      <div class="d-flex align-items-center justify-content-between mb-3">
        <h2 class="h4 page-title mb-0">Top rated</h2>
        <RouterLink class="btn btn-sm btn-outline-secondary" to="/shop">
          View all merchandise
        </RouterLink>
      </div>

      <LoadingIndicator v-if="loading" />

      <div v-else class="row row-cols-2 row-cols-md-3 row-cols-lg-4 g-3">
        <div v-for="product in featured" :key="product.id" class="col">
          <ProductCard :product="product" />
        </div>
      </div>
    </section>

    <section class="row g-4 text-center mt-5 pt-4 border-top">
      <div class="col-12 col-md-4">
        <h3 class="h6 text-uppercase text-muted">Official merchandise</h3>
        <p class="mb-0">Apparel and accessories licensed by the university.</p>
      </div>
      <div class="col-12 col-md-4">
        <h3 class="h6 text-uppercase text-muted">Student sellers</h3>
        <p class="mb-0">
          Labels run by students.
          <RouterLink to="/sell">Start selling</RouterLink>.
        </p>
      </div>
      <div class="col-12 col-md-4">
        <h3 class="h6 text-uppercase text-muted">Free delivery</h3>
        <p class="mb-0">On every order, to any campus.</p>
      </div>
    </section>
  </div>
</template>
