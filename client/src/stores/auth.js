import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

import { accountApi, authApi, merchantApi } from '@/api'
import { ROLES, STORAGE_KEYS } from '@/config'

export const useAuthStore = defineStore('auth', () => {
  const accessToken = ref(localStorage.getItem(STORAGE_KEYS.access) || '')
  const refreshToken = ref(localStorage.getItem(STORAGE_KEYS.refresh) || '')
  const user = ref(null)
  const loading = ref(false)

  const isAuthenticated = computed(() => Boolean(accessToken.value))
  const role = computed(() => user.value?.role || null)
  const isAdmin = computed(() => role.value === ROLES.ADMIN)
  const isMerchant = computed(() => role.value === ROLES.MERCHANT)
  // Drives the "your seller account has been disabled" screen.
  const isDisabledMerchant = computed(
    () => isMerchant.value && user.value?.merchant?.is_active === false
  )

  function applyTokens(access, refresh) {
    accessToken.value = access || ''
    if (access) localStorage.setItem(STORAGE_KEYS.access, access)
    if (refresh) {
      refreshToken.value = refresh
      localStorage.setItem(STORAGE_KEYS.refresh, refresh)
    }
  }

  function clearSession() {
    accessToken.value = ''
    refreshToken.value = ''
    user.value = null
    localStorage.removeItem(STORAGE_KEYS.access)
    localStorage.removeItem(STORAGE_KEYS.refresh)
  }

  async function fetchProfile() {
    if (!accessToken.value) return null
    try {
      const { data } = await accountApi.me()
      user.value = data
      return data
    } catch {
      // An unusable token is the same as no session at all.
      clearSession()
      return null
    }
  }

  async function login(credentials) {
    loading.value = true
    try {
      const { data } = await authApi.login(credentials)
      applyTokens(data.access, data.refresh)
      user.value = data.user
      return data.user
    } finally {
      loading.value = false
    }
  }

  async function register(payload) {
    loading.value = true
    try {
      const { data } = await authApi.register(payload)
      applyTokens(data.access, data.refresh)
      user.value = data.user
      return data.user
    } finally {
      loading.value = false
    }
  }

  async function completeMerchantSignup(payload) {
    loading.value = true
    try {
      const { data } = await merchantApi.signup(payload)
      applyTokens(data.access, data.refresh)
      user.value = data.user
      return data.user
    } finally {
      loading.value = false
    }
  }

  async function logout() {
    // Tell the server to blacklist the refresh token so it cannot be replayed;
    // clear the session either way.
    try {
      if (refreshToken.value) await authApi.logout(refreshToken.value)
    } catch {
      /* already expired or revoked — nothing to do */
    } finally {
      clearSession()
    }
  }

  function setUser(next) {
    user.value = next
  }

  return {
    accessToken,
    refreshToken,
    user,
    loading,
    isAuthenticated,
    role,
    isAdmin,
    isMerchant,
    isDisabledMerchant,
    applyTokens,
    clearSession,
    fetchProfile,
    login,
    register,
    completeMerchantSignup,
    logout,
    setUser
  }
})
