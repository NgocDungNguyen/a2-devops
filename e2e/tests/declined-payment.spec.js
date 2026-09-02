// RMIT University Vietnam
// Course: COSC2767 | COSC2805 Systems Deployment and Operations
// Assessment: Assignment 2 — CI/CD Pipeline
//
// Web UI / end-to-end test — the other half of Journey B in the README:
//
//   "pay with the declined test card 4000 0000 0000 0002 and confirm you
//    get a decline, the bag still has your items in it, and no stock has
//    moved."
//
// server/apps/orders/tests/test_checkout_integration.py already proves this
// at the API layer (no order row, no stock decrement). What that suite
// cannot see is what the *shopper* experiences: does the SPA surface the
// decline as a readable message, and does it leave the bag exactly as it
// found it so a shopper whose card failed can simply try a different one
// without re-adding everything? That is a frontend behaviour, not a backend
// one, which is why it belongs here rather than in the Python suite.

import { expect, test } from '@playwright/test'
import { CARDS, realCatalogueCards, TEST_PASSWORD, uniqueEmail } from './helpers.js'

test('a declined card shows an error and leaves the bag untouched', async ({ page }) => {
  const email = uniqueEmail('decline')

  await test.step('Register and land signed in', async () => {
    await page.goto('/register')
    await page.locator('#first-name').fill('Decline')
    await page.locator('#last-name').fill('Tester')
    await page.locator('#email').fill(email)
    await page.locator('#password').fill(TEST_PASSWORD)
    await page.getByRole('button', { name: 'Create account' }).click()
    await expect(page).toHaveURL(/\/dashboard/)
  })

  await test.step('Add a product to the bag', async () => {
    await page.goto('/shop')
    const firstCard = realCatalogueCards(page).first()
    await expect(firstCard).toBeVisible({ timeout: 15_000 })
    await firstCard.locator('.product-card__name').click()
    await page.getByRole('button', { name: 'Add to bag' }).click()
    await expect(page.getByRole('dialog', { name: 'Your bag' })).toBeVisible()
  })

  await test.step('Attempt to pay with a declined test card', async () => {
    const drawer = page.getByRole('dialog', { name: 'Your bag' })
    await drawer.getByText('No real cards - use a test number').click()
    await drawer
      .getByRole('button', { name: new RegExp(`${CARDS.declinedCardDeclined} - declined`) })
      .click()

    const payButton = drawer.getByRole('button', { name: /Pay and place order/ })
    await expect(payButton).toBeEnabled()

    // Wait for the actual checkout response, not just the click. The error
    // toast auto-dismisses after 6s (see stores/ui.js: error() uses a 6000ms
    // timeout) while the default assertion timeout is 8s — under CI/agent
    // load, the round trip (submit -> server decline -> toast render) can
    // eat enough of that gap to race the toast's own disappearance. Anchoring
    // on the network response first means the toast assertion below only
    // ever starts polling once the decline has already happened server-side,
    // which removes the race instead of just widening it.
    const [response] = await Promise.all([
      page.waitForResponse(
        (res) => res.url().includes('/api/orders/') && res.request().method() === 'POST'
      ),
      payButton.click()
    ])
    expect(response.status()).toBe(402)

    // apps/orders/payments.py:DECLINE_CARDS maps this number to
    // "Your card was declined." — the exact sentence the shopper should see.
    // Scoped past the earlier "added to your bag" success toast, which is
    // still fading out and would otherwise make getByRole('alert') ambiguous.
    await expect(
      page.getByRole('alert').filter({ hasText: 'card was declined' })
    ).toBeVisible()
  })

  await test.step('The bag still has the item, and the page never navigated away', async () => {
    // A successful checkout would have redirected to /order/success/:id.
    // Staying on the same page is itself part of the assertion.
    await expect(page).not.toHaveURL(/\/order\/success/)

    const drawer = page.getByRole('dialog', { name: 'Your bag' })
    await expect(drawer).toBeVisible()
    await expect(drawer.locator('li')).toHaveCount(1)
    await expect(drawer.getByRole('button', { name: /Pay and place order/ })).toBeVisible()
  })
})

test('a second decline reason (insufficient funds) also leaves the bag alone after a reload', async ({
  page
}) => {
  const email = uniqueEmail('decline-2')

  await page.goto('/register')
  await page.locator('#first-name').fill('Retry')
  await page.locator('#last-name').fill('Shopper')
  await page.locator('#email').fill(email)
  await page.locator('#password').fill(TEST_PASSWORD)
  await page.getByRole('button', { name: 'Create account' }).click()
  await expect(page).toHaveURL(/\/dashboard/)

  await page.goto('/shop')
  const firstCard = realCatalogueCards(page).first()
  await expect(firstCard).toBeVisible({ timeout: 15_000 })
  await firstCard.locator('.product-card__name').click()
  await page.getByRole('button', { name: 'Add to bag' }).click()

  const drawer = page.getByRole('dialog', { name: 'Your bag' })
  await drawer.getByText('No real cards - use a test number').click()
  await drawer
    .getByRole('button', { name: new RegExp(`${CARDS.declinedInsufficientFunds} - insufficient funds`) })
    .click()
  const payButton = drawer.getByRole('button', { name: /Pay and place order/ })
  const [response] = await Promise.all([
    page.waitForResponse(
      (res) => res.url().includes('/api/orders/') && res.request().method() === 'POST'
    ),
    payButton.click()
  ])
  expect(response.status()).toBe(402)

  await expect(
    page.getByRole('alert').filter({ hasText: 'insufficient funds' })
  ).toBeVisible()

  // The bag is client-side state (see stores/cart.js), so it survives even
  // a full page reload — confirming the item was never cleared by the
  // failed request, only by a successful one.
  await page.reload()
  await expect(
    page.getByRole('button', { name: /Shopping bag, 1 item/ })
  ).toBeVisible()
})
