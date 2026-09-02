/**
 * Saved delivery addresses.
 *
 * The smallest store in the project, and a good one to read first if Pinia is
 * new to you: some state, some async functions that call the API layer, and an
 * object listing what the rest of the app is allowed to use.
 */
import { defineStore } from 'pinia'
import { ref } from 'vue'

import { addressApi } from '@/api'

export const useAddressStore = defineStore('addresses', () => {
  const addresses = ref([])
  const loading = ref(false)

  async function fetchAll() {
    loading.value = true
    try {
      const { data } = await addressApi.list()
      addresses.value = data
      return data
    } finally {
      loading.value = false
    }
  }

  async function fetchOne(id) {
    const { data } = await addressApi.get(id)
    return data
  }

  // Saving an address can change a *different* one: marking this the default
  // clears the flag on whichever address held it (Address.save() enforces
  // that server-side). Pushing the response onto the local list would leave
  // two addresses both showing the "Default" badge, so re-read the lot. One
  // extra request is a fair price for not having to mirror a server-side rule
  // in the browser.
  async function create(payload) {
    const { data } = await addressApi.create(payload)
    await fetchAll()
    return data
  }

  async function update(id, payload) {
    const { data } = await addressApi.update(id, payload)
    await fetchAll()
    return data
  }

  // Deleting cannot change any other row, so the local list is filtered
  // instead — no round trip needed.
  async function remove(id) {
    await addressApi.remove(id)
    addresses.value = addresses.value.filter((a) => a.id !== id)
  }

  return { addresses, loading, fetchAll, fetchOne, create, update, remove }
})
