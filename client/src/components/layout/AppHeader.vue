<script setup>
import { storeToRefs } from 'pinia'
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import AppIcon from '@/components/common/AppIcon.vue'
import SearchAutosuggest from '@/components/common/SearchAutosuggest.vue'
import { useAuthStore } from '@/stores/auth'
import { useCartStore } from '@/stores/cart'
import { useCatalogStore } from '@/stores/catalog'
import { useUiStore } from '@/stores/ui'

const auth = useAuthStore()
const cart = useCartStore()
const catalog = useCatalogStore()
const ui = useUiStore()
const router = useRouter()
const route = useRoute()

const { count } = storeToRefs(cart)
const { brands } = storeToRefs(catalog)

// Only one dropdown open at a time; null means none.
const openMenu = ref(null)

function toggle(name) {
  openMenu.value = openMenu.value === name ? null : name
}

function closeMenus() {
  openMenu.value = null
}

/**
 * Close an open dropdown when the next click lands outside it.
 *
 * Done with a document listener rather than a transparent full-screen
 * backdrop: a backdrop has to sit above the page to catch the click, which
 * also puts it above the dropdown's own menu items and makes them
 * unclickable. Clicks inside `.dropdown` are ignored here — the toggle button
 * and the menu items handle themselves.
 */
function onDocumentClick(event) {
  if (!openMenu.value) return
  if (event.target.closest?.('.dropdown')) return
  closeMenus()
}

onMounted(() => document.addEventListener('click', onDocumentClick))
onBeforeUnmount(() => document.removeEventListener('click', onDocumentClick))

// Navigating away should not leave a menu hanging open.
watch(() => route.fullPath, closeMenus)

async function signOut() {
  closeMenus()
  await auth.logout()
  ui.info('You have been signed out.')
  router.push({ name: 'home' })
}
</script>

<template>
  <header>
    <div class="info-bar">
      <div
        class="container d-flex flex-wrap justify-content-center justify-content-md-between gap-2 py-1"
      >
        <span>Free shipping on every order</span>
        <span class="d-none d-md-inline">Pay by card, PayPal or campus credit</span>
        <span class="d-none d-md-inline">Support 24 / 7</span>
      </div>
    </div>

    <div class="store-header sticky-top">
      <div class="container">
        <nav class="navbar navbar-expand-lg py-2 gap-2 flex-nowrap">
          <button
            type="button"
            class="icon-button flex-shrink-0"
            aria-label="Browse categories"
            @click="ui.toggleMenu()"
          >
            <AppIcon name="menu" />
          </button>

          <RouterLink class="navbar-brand me-2 flex-shrink-0" to="/">
            <img src="/images/rmit-store-logo.png" alt="RMIT Store" />
          </RouterLink>

          <!-- Brands -->
          <div class="dropdown d-none d-lg-block flex-shrink-0">
            <button
              class="btn btn-sm btn-link text-decoration-none text-dark d-flex align-items-center gap-1"
              type="button"
              :aria-expanded="openMenu === 'brands'"
              @click="toggle('brands')"
            >
              Brands
              <AppIcon name="chevronDown" :size="14" />
            </button>

            <ul v-if="openMenu === 'brands'" class="dropdown-menu show mt-1">
              <li v-for="brand in brands.slice(0, 8)" :key="brand.id">
                <RouterLink
                  class="dropdown-item"
                  :to="{ name: 'shop-brand', params: { slug: brand.slug } }"
                  @click="closeMenus"
                >
                  {{ brand.name }}
                </RouterLink>
              </li>
              <li v-if="brands.length"><hr class="dropdown-divider" /></li>
              <li>
                <RouterLink class="dropdown-item fw-medium" to="/brands" @click="closeMenus">
                  See all brands
                </RouterLink>
              </li>
            </ul>
          </div>

          <SearchAutosuggest class="mx-lg-3" />

          <div class="d-flex align-items-center ms-auto flex-shrink-0">
            <!-- Account -->
            <div class="dropdown">
              <button
                type="button"
                class="icon-button"
                aria-label="Account"
                :aria-expanded="openMenu === 'user'"
                @click="toggle('user')"
              >
                <AppIcon name="user" />
              </button>

              <ul v-if="openMenu === 'user'" class="dropdown-menu dropdown-menu-end show mt-1">
                <template v-if="auth.isAuthenticated">
                  <li class="dropdown-header text-truncate">
                    {{ auth.user?.full_name || auth.user?.email }}
                  </li>
                  <li>
                    <RouterLink class="dropdown-item" to="/dashboard" @click="closeMenus">
                      Dashboard
                    </RouterLink>
                  </li>
                  <li><hr class="dropdown-divider" /></li>
                  <li>
                    <button class="dropdown-item" type="button" @click="signOut">
                      Sign out
                    </button>
                  </li>
                </template>
                <template v-else>
                  <li>
                    <RouterLink class="dropdown-item" to="/login" @click="closeMenus">
                      Sign in
                    </RouterLink>
                  </li>
                  <li>
                    <RouterLink class="dropdown-item" to="/register" @click="closeMenus">
                      Create an account
                    </RouterLink>
                  </li>
                </template>
              </ul>
            </div>

            <!-- Bag -->
            <button
              type="button"
              class="icon-button position-relative"
              :aria-label="`Shopping bag, ${count} item${count === 1 ? '' : 's'}`"
              @click="ui.toggleCart()"
            >
              <AppIcon name="bag" />
              <span v-if="count" class="cart-badge">{{ count > 99 ? '99+' : count }}</span>
            </button>
          </div>
        </nav>
      </div>
    </div>

  </header>
</template>
