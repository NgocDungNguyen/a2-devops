<script setup>
import { storeToRefs } from 'pinia'
import { ref } from 'vue'
import { useRouter } from 'vue-router'

import AppIcon from '@/components/common/AppIcon.vue'
import BaseDrawer from '@/components/common/BaseDrawer.vue'
import PaymentForm from '@/components/store/PaymentForm.vue'
import { useAuthStore } from '@/stores/auth'
import { useCartStore } from '@/stores/cart'
import { useUiStore } from '@/stores/ui'
import { errorMessage, fieldErrors, imageOrPlaceholder, money } from '@/utils/format'

const auth = useAuthStore()
const cart = useCartStore()
const ui = useUiStore()
const router = useRouter()

const { items, subtotal, isEmpty } = storeToRefs(cart)
const { isCartOpen } = storeToRefs(ui)

const placing = ref(false)
// Held for the life of the drawer and never persisted - see the comment on
// cart.checkout() for why this is not store state.
const card = ref({})
// A template ref on the PaymentForm component, used only to read whether the
// card is filled in far enough to submit. Null until the drawer has rendered.
const cardForm = ref(null)
// Server-reported problems with the card, keyed by field name, handed to the
// form so it can mark the offending input.
const cardErrors = ref({})

// Which input a gateway decline points at. A declined card is not a typo, so
// most of these have nowhere useful to point and only get a toast; these two
// name a specific box, and marking it saves the shopper re-reading all four.
const DECLINE_FIELD = {
  incorrect_cvc: 'cvc',
  expired_card: 'exp_year'
}

function goToLogin() {
  ui.closeCart()
  ui.info('Please sign in to complete your order.')
  router.push({ name: 'login', query: { next: '/shop' } })
}

async function placeOrder() {
  placing.value = true
  cardErrors.value = {}
  try {
    const order = await cart.checkout(card.value)
    // The bag is cleared by the store, and the card is dropped here. Nothing
    // that could be used to charge somebody again survives this line.
    card.value = {}
    ui.closeCart()
    router.push({ name: 'order-success', params: { id: order.id } })
  } catch (error) {
    // Three shapes of failure arrive here:
    //   400 - the details are malformed. The server returns per-field errors
    //         nested under `payment`, which the form renders next to the box.
    //   402 - the details were fine and the gateway said no. One sentence,
    //         plus a `decline_code` that sometimes names a field.
    //   anything else - usually a stock shortfall; the server names the
    //         product, and the toast is the whole story.
    // In every case the bag is left alone, so nothing is lost by trying again.
    const declineField = DECLINE_FIELD[error?.response?.data?.decline_code]
    cardErrors.value = declineField
      ? { [declineField]: errorMessage(error) }
      : fieldErrors(error, 'payment')
    ui.error(errorMessage(error, 'We could not place your order.'))
  } finally {
    placing.value = false
  }
}
</script>

<template>
  <BaseDrawer :open="isCartOpen" title="Your bag" side="right" @close="ui.closeCart()">
    <div v-if="isEmpty" class="text-center text-muted py-5">
      <AppIcon name="bag" :size="42" class="mb-3 opacity-50" />
      <p class="mb-3">Your bag is empty.</p>
      <RouterLink class="btn btn-sm btn-primary" to="/shop" @click="ui.closeCart()">
        Start shopping
      </RouterLink>
    </div>

    <ul v-else class="list-unstyled d-grid gap-3 mb-0">
      <li v-for="item in items" :key="item.id" class="d-flex gap-3">
        <img
          :src="imageOrPlaceholder(item.image_url)"
          :alt="item.name"
          width="64"
          height="64"
          class="rounded object-fit-cover flex-shrink-0"
        />

        <div class="flex-grow-1 min-w-0">
          <RouterLink
            :to="{ name: 'product', params: { slug: item.slug } }"
            class="d-block text-truncate fw-medium"
            @click="ui.closeCart()"
          >
            {{ item.name }}
          </RouterLink>
          <div class="small text-muted">{{ item.brand_name }}</div>

          <div class="d-flex align-items-center gap-2 mt-2">
            <div class="input-group input-group-sm" style="width: 108px">
              <button
                class="btn btn-outline-secondary"
                type="button"
                aria-label="Decrease quantity"
                :disabled="item.quantity <= 1"
                @click="cart.setQuantity(item.id, item.quantity - 1)"
              >
                <AppIcon name="minus" :size="12" />
              </button>
              <span class="form-control text-center">{{ item.quantity }}</span>
              <button
                class="btn btn-outline-secondary"
                type="button"
                aria-label="Increase quantity"
                :disabled="item.quantity >= Math.min(cart.maxPurchaseQuantity(item.inventory), item.inventory)"
                @click="cart.setQuantity(item.id, item.quantity + 1)"
              >
                <AppIcon name="plus" :size="12" />
              </button>
            </div>

            <span class="ms-auto fw-semibold text-brand">
              {{ money(Number(item.price) * item.quantity) }}
            </span>

            <button
              type="button"
              class="btn btn-link btn-sm p-0 text-muted"
              :aria-label="`Remove ${item.name}`"
              @click="cart.remove(item.id)"
            >
              <AppIcon name="trash" :size="16" />
            </button>
          </div>
        </div>
      </li>
    </ul>

    <template v-if="!isEmpty" #footer>
      <div class="d-flex justify-content-between small text-muted mb-1">
        <span>Shipping</span>
        <span>Free</span>
      </div>
      <div class="d-flex justify-content-between fw-semibold mb-1">
        <span>Subtotal</span>
        <span>{{ money(subtotal) }}</span>
      </div>
      <!--
        Sales tax is added by the server at checkout, which is also where the
        final total is decided. Showing an estimate here and letting the
        server be authoritative is the point.
      -->
      <p class="small text-muted mb-3">
        Sales tax is calculated at checkout.
      </p>

      <PaymentForm
        v-if="auth.isAuthenticated"
        ref="cardForm"
        v-model="card"
        :errors="cardErrors"
        :disabled="placing"
        class="mb-3"
      />

      <div class="d-grid gap-2">
        <button
          v-if="auth.isAuthenticated"
          class="btn btn-primary"
          type="button"
          :disabled="placing || !cardForm?.complete"
          @click="placeOrder"
        >
          <!-- Not "Pay $X": the total is not known until the server has added
               tax, and quoting the pre-tax subtotal on the button would be a
               lie by one line of arithmetic. -->
          {{ placing ? 'Paying…' : 'Pay and place order' }}
        </button>
        <button v-else class="btn btn-primary" type="button" @click="goToLogin">
          Sign in to check out
        </button>

        <RouterLink class="btn btn-outline-secondary" to="/shop" @click="ui.closeCart()">
          Continue shopping
        </RouterLink>
      </div>
    </template>
  </BaseDrawer>
</template>
