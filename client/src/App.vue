<script setup>
import { onMounted } from 'vue'

import AppFooter from '@/components/layout/AppFooter.vue'
import AppHeader from '@/components/layout/AppHeader.vue'
import CartDrawer from '@/components/store/CartDrawer.vue'
import MenuDrawer from '@/components/store/MenuDrawer.vue'
import ToastHost from '@/components/common/ToastHost.vue'
import { useCatalogStore } from '@/stores/catalog'

const catalog = useCatalogStore()

onMounted(() => {
  // The nav drawer and the brands dropdown both need these, so fetch once at
  // start-up rather than on every route that happens to show them.
  catalog.fetchCategories()
  catalog.fetchBrands()
})
</script>

<template>
  <AppHeader />

  <main>
    <RouterView v-slot="{ Component }">
      <component :is="Component" />
    </RouterView>
  </main>

  <AppFooter />

  <CartDrawer />
  <MenuDrawer />
  <ToastHost />
</template>
