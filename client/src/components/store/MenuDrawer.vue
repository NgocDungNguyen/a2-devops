<script setup>
import { storeToRefs } from 'pinia'

import BaseDrawer from '@/components/common/BaseDrawer.vue'
import { useCatalogStore } from '@/stores/catalog'
import { useUiStore } from '@/stores/ui'

const catalog = useCatalogStore()
const ui = useUiStore()

const { categories } = storeToRefs(catalog)
const { isMenuOpen } = storeToRefs(ui)
</script>

<template>
  <BaseDrawer :open="isMenuOpen" title="Browse" side="left" @close="ui.closeMenu()">
    <nav>
      <ul class="list-unstyled d-grid gap-1 mb-4">
        <li>
          <RouterLink class="d-block py-2 fw-medium" to="/shop" @click="ui.closeMenu()">
            All merchandise
          </RouterLink>
        </li>
        <li>
          <RouterLink class="d-block py-2 fw-medium" to="/brands" @click="ui.closeMenu()">
            Brands
          </RouterLink>
        </li>
      </ul>

      <h3 class="h6 text-uppercase text-muted small mb-2">Categories</h3>
      <ul class="list-unstyled d-grid gap-1 mb-0">
        <li v-for="category in categories" :key="category.id">
          <RouterLink
            class="d-flex justify-content-between align-items-center py-2"
            :to="{ name: 'shop-category', params: { slug: category.slug } }"
            @click="ui.closeMenu()"
          >
            <span>{{ category.name }}</span>
            <span class="badge text-bg-light">{{ category.product_count }}</span>
          </RouterLink>
        </li>
      </ul>
    </nav>
  </BaseDrawer>
</template>
