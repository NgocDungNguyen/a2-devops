import { createRouter, createWebHistory } from 'vue-router'

import { ROLES } from '@/config'
import { useAuthStore } from '@/stores/auth'
import { useUiStore } from '@/stores/ui'

/**
 * Dashboard navigation.
 *
 * One array drives both the sidebar menu and the route metadata, so a link
 * and the guard protecting it can never drift apart. In the original these
 * were three separate route trees plus a JSON file of links.
 */
export const DASHBOARD_LINKS = [
  { to: '/dashboard', label: 'Account Details', exact: true, roles: null },
  { to: '/dashboard/security', label: 'Account Security', roles: null },
  { to: '/dashboard/address', label: 'Addresses', roles: null },
  { to: '/dashboard/orders', label: 'Orders', roles: null },
  { to: '/dashboard/wishlist', label: 'Wishlist', roles: null },
  { to: '/dashboard/product', label: 'Products', roles: [ROLES.ADMIN, ROLES.MERCHANT] },
  { to: '/dashboard/brand', label: 'Brands', roles: [ROLES.ADMIN, ROLES.MERCHANT] },
  { to: '/dashboard/category', label: 'Categories', roles: [ROLES.ADMIN] },
  { to: '/dashboard/users', label: 'Users', roles: [ROLES.ADMIN] },
  { to: '/dashboard/merchant', label: 'Sellers', roles: [ROLES.ADMIN] },
  { to: '/dashboard/review', label: 'Reviews', roles: [ROLES.ADMIN] }
]

const ADMIN_ONLY = [ROLES.ADMIN]
const ADMIN_OR_MERCHANT = [ROLES.ADMIN, ROLES.MERCHANT]

const routes = [
  { path: '/', name: 'home', component: () => import('@/views/HomeView.vue') },

  // --- storefront ---------------------------------------------------------
  { path: '/shop', name: 'shop', component: () => import('@/views/shop/ShopView.vue') },
  {
    path: '/shop/category/:slug',
    name: 'shop-category',
    component: () => import('@/views/shop/ShopView.vue'),
    props: (route) => ({ categorySlug: route.params.slug })
  },
  {
    path: '/shop/brand/:slug',
    name: 'shop-brand',
    component: () => import('@/views/shop/ShopView.vue'),
    props: (route) => ({ brandSlug: route.params.slug })
  },
  { path: '/brands', name: 'brands', component: () => import('@/views/BrandsView.vue') },
  {
    path: '/product/:slug',
    name: 'product',
    component: () => import('@/views/ProductView.vue')
  },
  { path: '/sell', name: 'sell', component: () => import('@/views/SellView.vue') },
  { path: '/contact', name: 'contact', component: () => import('@/views/ContactView.vue') },

  // --- authentication -----------------------------------------------------
  {
    path: '/login',
    name: 'login',
    component: () => import('@/views/auth/LoginView.vue'),
    meta: { guestOnly: true }
  },
  {
    path: '/register',
    name: 'register',
    component: () => import('@/views/auth/RegisterView.vue'),
    meta: { guestOnly: true }
  },
  {
    path: '/forgot-password',
    name: 'forgot-password',
    component: () => import('@/views/auth/ForgotPasswordView.vue'),
    meta: { guestOnly: true }
  },
  {
    // Django's reset link carries a base64 user id as well as the token.
    path: '/reset-password/:uid/:token',
    name: 'reset-password',
    component: () => import('@/views/auth/ResetPasswordView.vue'),
    meta: { guestOnly: true }
  },
  {
    path: '/merchant-signup/:token',
    name: 'merchant-signup',
    component: () => import('@/views/auth/MerchantSignupView.vue')
  },

  // --- orders -------------------------------------------------------------
  {
    path: '/order/success/:id',
    name: 'order-success',
    component: () => import('@/views/order/OrderSuccessView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/order/:id',
    name: 'order-detail',
    component: () => import('@/views/order/OrderDetailView.vue'),
    meta: { requiresAuth: true }
  },

  // --- dashboard ----------------------------------------------------------
  {
    path: '/dashboard',
    component: () => import('@/views/dashboard/DashboardLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      { path: '', name: 'dashboard', component: () => import('@/views/dashboard/AccountDetails.vue') },
      { path: 'security', name: 'dashboard-security', component: () => import('@/views/dashboard/AccountSecurity.vue') },

      { path: 'address', name: 'dashboard-addresses', component: () => import('@/views/dashboard/AddressList.vue') },
      { path: 'address/add', name: 'dashboard-address-add', component: () => import('@/views/dashboard/AddressForm.vue') },
      { path: 'address/:id', name: 'dashboard-address-edit', component: () => import('@/views/dashboard/AddressForm.vue') },

      { path: 'orders', name: 'dashboard-orders', component: () => import('@/views/dashboard/OrderList.vue') },
      { path: 'wishlist', name: 'dashboard-wishlist', component: () => import('@/views/dashboard/WishlistPanel.vue') },

      {
        path: 'product',
        name: 'dashboard-products',
        component: () => import('@/views/dashboard/ProductList.vue'),
        meta: { roles: ADMIN_OR_MERCHANT }
      },
      {
        path: 'product/add',
        name: 'dashboard-product-add',
        component: () => import('@/views/dashboard/ProductForm.vue'),
        meta: { roles: ADMIN_OR_MERCHANT }
      },
      {
        path: 'product/:id',
        name: 'dashboard-product-edit',
        component: () => import('@/views/dashboard/ProductForm.vue'),
        meta: { roles: ADMIN_OR_MERCHANT }
      },

      {
        path: 'brand',
        name: 'dashboard-brands',
        component: () => import('@/views/dashboard/BrandList.vue'),
        meta: { roles: ADMIN_OR_MERCHANT }
      },
      {
        path: 'brand/add',
        name: 'dashboard-brand-add',
        component: () => import('@/views/dashboard/BrandForm.vue'),
        meta: { roles: ADMIN_ONLY }
      },
      {
        path: 'brand/:id',
        name: 'dashboard-brand-edit',
        component: () => import('@/views/dashboard/BrandForm.vue'),
        meta: { roles: ADMIN_OR_MERCHANT }
      },

      {
        path: 'category',
        name: 'dashboard-categories',
        component: () => import('@/views/dashboard/CategoryList.vue'),
        meta: { roles: ADMIN_ONLY }
      },
      {
        path: 'category/add',
        name: 'dashboard-category-add',
        component: () => import('@/views/dashboard/CategoryForm.vue'),
        meta: { roles: ADMIN_ONLY }
      },
      {
        path: 'category/:id',
        name: 'dashboard-category-edit',
        component: () => import('@/views/dashboard/CategoryForm.vue'),
        meta: { roles: ADMIN_ONLY }
      },

      {
        path: 'users',
        name: 'dashboard-users',
        component: () => import('@/views/dashboard/UserList.vue'),
        meta: { roles: ADMIN_ONLY }
      },
      {
        path: 'merchant',
        name: 'dashboard-merchants',
        component: () => import('@/views/dashboard/MerchantList.vue'),
        meta: { roles: ADMIN_ONLY }
      },
      {
        path: 'review',
        name: 'dashboard-reviews',
        component: () => import('@/views/dashboard/ReviewList.vue'),
        meta: { roles: ADMIN_ONLY }
      }
    ]
  },

  {
    path: '/:pathMatch(.*)*',
    name: 'not-found',
    component: () => import('@/views/NotFoundView.vue')
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior(to, from, savedPosition) {
    if (savedPosition) return savedPosition
    if (to.hash) return { el: to.hash, behavior: 'smooth' }
    return { top: 0 }
  }
})

/**
 * One guard for the whole application.
 *
 * Note this is a convenience, not a security boundary — it decides what to
 * render, and the server decides what data anyone is allowed to see. Every
 * endpoint enforces its own permissions, so hand-editing the URL gets you a
 * page shell and a 403, not somebody else's data.
 */
router.beforeEach(async (to) => {
  const auth = useAuthStore()
  useUiStore().closeAll()

  // A page reload leaves a token in storage but no profile in memory.
  if (auth.isAuthenticated && !auth.user) {
    await auth.fetchProfile()
  }

  if (to.meta.requiresAuth && !auth.isAuthenticated) {
    return { name: 'login', query: { next: to.fullPath } }
  }

  if (to.meta.guestOnly && auth.isAuthenticated) {
    return { name: 'dashboard' }
  }

  if (to.meta.roles && !to.meta.roles.includes(auth.role)) {
    return { name: 'dashboard' }
  }

  return true
})

export default router
