import { createPinia } from 'pinia'
import { createApp } from 'vue'

import App from './App.vue'
import { registerAuthStore, registerRouter } from './api/http'
import router from './router'
import { useAuthStore } from './stores/auth'
import { useCartStore } from './stores/cart'
import { STORAGE_KEYS } from './config'

import './styles/main.scss'

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.use(router)

// Hand the axios interceptors their dependencies. Doing it here rather than
// importing the store inside http.js avoids a circular import, since every
// store imports the api layer.
const auth = useAuthStore()
registerAuthStore(auth)
registerRouter(router)

// Keep the bag in step when the store is open in more than one tab.
window.addEventListener('storage', (event) => {
  if (event.key === STORAGE_KEYS.cart) {
    useCartStore().syncFromStorage()
  }
})

// Show focus rings for keyboard users only.
window.addEventListener('keydown', (event) => {
  if (event.key === 'Tab') document.body.classList.add('user-is-tabbing')
})
window.addEventListener('mousedown', () => {
  document.body.classList.remove('user-is-tabbing')
})

app.mount('#app')
