<script setup>
/**
 * The card form at checkout.
 *
 * Everything here is presentation and typo-catching: grouping the digits,
 * reading MM/YY, recognising the brand, and refusing to submit something that
 * is obviously incomplete. Nothing here decides whether the card pays - that
 * is the server's call, and this component only reports what it says.
 *
 * The card details go straight into the checkout request and are never put in
 * the Pinia store or localStorage, so they are gone the moment the request
 * finishes. The bag persists across reloads; the card must not.
 */
import { computed, ref, watch } from 'vue'

const props = defineProps({
  errors: { type: Object, default: () => ({}) },
  disabled: { type: Boolean, default: false }
})

// The payload the API expects, kept in sync with the raw inputs below.
const model = defineModel({ type: Object, required: true })

const number = ref('')
const expiry = ref('')
const cvc = ref('')
const name = ref('')

const digits = computed(() => number.value.replace(/\D/g, ''))

const brand = computed(() => {
  const d = digits.value
  if (d.startsWith('4')) return 'Visa'
  if (/^3[47]/.test(d)) return 'American Express'
  if (/^5[1-5]/.test(d) || /^2(2[2-9]|[3-6]|7[01]|720)/.test(d)) return 'Mastercard'
  if (/^35/.test(d)) return 'JCB'
  if (/^6011|^65/.test(d)) return 'Discover'
  return ''
})

/** True for a number starting 34 or 37, whether or not it is in `number` yet. */
function looksAmex(value) {
  return /^3[47]/.test(String(value).replace(/\D/g, ''))
}

const isAmex = computed(() => looksAmex(digits.value))
const cvcLength = computed(() => (isAmex.value ? 4 : 3))

/**
 * Amex groups 4-6-5 (15 digits); everyone else in fours (16).
 *
 * Note that this reads the brand out of `value` — the text that has just been
 * typed — and not from the `isAmex` computed. `isAmex` is derived from
 * `number`, which is still the *previous* value while this runs, so using it
 * here formatted a pasted amex as "3782 8224 6310 005" until the next
 * keystroke nudged it. Anything that formats an input as you type has this
 * trap in it somewhere.
 */
function groupDigits(value) {
  const amex = looksAmex(value)
  const d = value.replace(/\D/g, '').slice(0, amex ? 15 : 16)
  const groups = amex ? [4, 6, 5] : [4, 4, 4, 4]
  const parts = []
  let index = 0
  for (const size of groups) {
    if (index >= d.length) break
    parts.push(d.slice(index, index + size))
    index += size
  }
  return parts.join(' ')
}

function onNumberInput(event) {
  number.value = groupDigits(event.target.value)
}

function onExpiryInput(event) {
  const d = event.target.value.replace(/\D/g, '').slice(0, 4)
  // Type "1" and you probably mean January; type "2" and you mean February,
  // so pad a leading zero rather than waiting for a second digit.
  if (d.length === 1 && Number(d) > 1) {
    expiry.value = `0${d}/`
  } else if (d.length >= 3) {
    expiry.value = `${d.slice(0, 2)}/${d.slice(2)}`
  } else {
    expiry.value = d
  }
}

function onCvcInput(event) {
  cvc.value = event.target.value.replace(/\D/g, '').slice(0, cvcLength.value)
}

/** "12/30" -> {month: 12, year: 2030}, or null while it is still half-typed. */
const expiryParts = computed(() => {
  const [month, year] = expiry.value.split('/')
  if (!month || !year || year.length < 2) return null
  return { month: Number(month), year: 2000 + Number(year) }
})

/**
 * Enough to submit. Deliberately weaker than "valid": it only asks whether
 * every box has been filled in plausibly, because a form that argues with you
 * about the check digit while you are still typing is infuriating. The Luhn
 * digit and the real expiry are the server's job, and its answer comes back
 * as field errors on `errors`.
 */
const complete = computed(
  () =>
    digits.value.length >= 13 &&
    cvc.value.length === cvcLength.value &&
    expiryParts.value !== null &&
    expiryParts.value.month >= 1 &&
    expiryParts.value.month <= 12
)

// Exposed so the parent can disable its own submit button - see CartDrawer.
// `defineExpose` unwraps the ref, so the parent reads `cardForm.complete` as
// a plain boolean, and it stays reactive.
defineExpose({ complete })

// Keep the outgoing payload in step with the boxes. The API wants bare digits
// and a numeric month and year, so the grouping spaces and the "MM/YY" shape
// are stripped here rather than anywhere else - the display format never
// leaves this component.
watch(
  [digits, expiryParts, cvc, name],
  () => {
    model.value = {
      number: digits.value,
      exp_month: expiryParts.value?.month ?? null,
      exp_year: expiryParts.value?.year ?? null,
      cvc: cvc.value,
      name_on_card: name.value
    }
  },
  { immediate: true }
)

/** Fills the form so the demo can be walked through without typing. */
function useTestCard(value) {
  number.value = groupDigits(value)
  const now = new Date()
  expiry.value = `12/${String((now.getFullYear() + 2) % 100).padStart(2, '0')}`
  cvc.value = looksAmex(value) ? '1234' : '123'
  name.value = name.value || 'Demo Member'
}
</script>

<template>
  <div class="d-grid gap-2">
    <div>
      <label class="form-label small mb-1" for="card-number">
        Card number
        <span v-if="brand" class="badge text-bg-light ms-1 fw-normal">{{ brand }}</span>
      </label>
      <input
        id="card-number"
        :value="number"
        type="text"
        inputmode="numeric"
        autocomplete="cc-number"
        class="form-control form-control-sm"
        :class="{ 'is-invalid': errors.number }"
        placeholder="4242 4242 4242 4242"
        :disabled="disabled"
        @input="onNumberInput"
      />
      <div v-if="errors.number" class="invalid-feedback">{{ errors.number }}</div>
    </div>

    <div class="row g-2">
      <div class="col-6">
        <label class="form-label small mb-1" for="card-expiry">Expiry</label>
        <input
          id="card-expiry"
          :value="expiry"
          type="text"
          inputmode="numeric"
          autocomplete="cc-exp"
          class="form-control form-control-sm"
          :class="{ 'is-invalid': errors.exp_year || errors.exp_month }"
          placeholder="MM/YY"
          :disabled="disabled"
          @input="onExpiryInput"
        />
        <div v-if="errors.exp_year" class="invalid-feedback">{{ errors.exp_year }}</div>
      </div>

      <div class="col-6">
        <label class="form-label small mb-1" for="card-cvc">
          Security code
        </label>
        <input
          id="card-cvc"
          :value="cvc"
          type="text"
          inputmode="numeric"
          autocomplete="cc-csc"
          class="form-control form-control-sm"
          :class="{ 'is-invalid': errors.cvc }"
          :placeholder="isAmex ? '1234' : '123'"
          :disabled="disabled"
          @input="onCvcInput"
        />
        <div v-if="errors.cvc" class="invalid-feedback">{{ errors.cvc }}</div>
      </div>
    </div>

    <div>
      <label class="form-label small mb-1" for="card-name">Name on card</label>
      <input
        id="card-name"
        v-model="name"
        type="text"
        autocomplete="cc-name"
        class="form-control form-control-sm"
        :disabled="disabled"
      />
    </div>

    <!--
      This is a teaching store with a simulated gateway, so the test numbers
      belong on screen rather than buried in the README. A real storefront
      would obviously not do this.
    -->
    <details class="small text-muted mt-1">
      <summary class="cursor-pointer">No real cards - use a test number</summary>
      <div class="d-grid gap-1 mt-2">
        <button
          type="button"
          class="btn btn-sm btn-outline-secondary text-start"
          :disabled="disabled"
          @click="useTestCard('4242424242424242')"
        >
          <code>4242 4242 4242 4242</code> - succeeds
        </button>
        <button
          type="button"
          class="btn btn-sm btn-outline-secondary text-start"
          :disabled="disabled"
          @click="useTestCard('4000000000000002')"
        >
          <code>4000 0000 0000 0002</code> - declined
        </button>
        <button
          type="button"
          class="btn btn-sm btn-outline-secondary text-start"
          :disabled="disabled"
          @click="useTestCard('4000000000009995')"
        >
          <code>4000 0000 0000 9995</code> - insufficient funds
        </button>
      </div>
      <p class="mt-2 mb-0">
        Any expiry in the future and any security code will do.
      </p>
    </details>
  </div>
</template>
