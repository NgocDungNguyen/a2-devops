// RMIT University Vietnam
// Course: COSC2767 | COSC2805 Systems Deployment and Operations
// Assessment: Assignment 2 — CI/CD Pipeline
//
// Web UI / end-to-end test — README "Verifying a deployment", Journey C
// (Fulfilment), converted as the README itself invites: "the acceptance
// journeys in the next section are a ready-made backlog — each one converts
// into an end-to-end test."
//
//   As an administrator, mark an item Shipped -> the customer sees it. As
//   the customer, cancel the other item -> its stock comes back and the
//   order total drops. Cancel the last item -> the order becomes Cancelled
//   but is still there, and the payment reads Refunded. Now try to move a
//   cancelled item back to Processing as an administrator -> the dropdown
//   is disabled.
//
// This exercises the one part of the order lifecycle the checkout journey
// (purchase-journey.spec.js) never reaches: what happens *after* an order
// is placed, from both the customer's and the administrator's side of the
// same order, in the same browser.

import { expect, test } from '@playwright/test'
import { ADMIN, CARDS, loginAs, logout, realCatalogueCards, TEST_PASSWORD, uniqueEmail } from './helpers.js'

test('an administrator ships one item while the customer cancels the rest, and a cancelled line cannot be reinstated', async ({
  page
}) => {
  const email = uniqueEmail('fulfilment')
  let orderId
  let firstItemName

  await test.step('Register, buy two different products in one order', async () => {
    await page.goto('/register')
    await page.locator('#first-name').fill('Fulfilment')
    await page.locator('#last-name').fill('Tester')
    await page.locator('#email').fill(email)
    await page.locator('#password').fill(TEST_PASSWORD)
    await page.getByRole('button', { name: 'Create account' }).click()
    await expect(page).toHaveURL(/\/dashboard/)

    await page.goto('/shop')
    const cards = realCatalogueCards(page)
    await expect(cards.first()).toBeVisible({ timeout: 15_000 })

    firstItemName = await cards.nth(0).locator('.product-card__name').innerText()
    await cards.nth(0).locator('.product-card__name').click()
    await page.getByRole('button', { name: 'Add to bag' }).click()
    await page.getByRole('button', { name: 'Close' }).click() // back to the shop grid

    await page.goto('/shop')
    await expect(cards.first()).toBeVisible({ timeout: 15_000 })
    await cards.nth(1).locator('.product-card__name').click()
    await page.getByRole('button', { name: 'Add to bag' }).click()

    const drawer = page.getByRole('dialog', { name: 'Your bag' })
    await expect(drawer.locator('li')).toHaveCount(2)

    await drawer.getByText('No real cards - use a test number').click()
    await drawer.getByRole('button', { name: new RegExp(`${CARDS.approved} - succeeds`) }).click()
    await drawer.getByRole('button', { name: /Pay and place order/ }).click()

    await page.waitForURL(/\/order\/success\/\d+/, { timeout: 15_000 })
    orderId = page.url().match(/\/order\/success\/(\d+)/)[1]
  })

  // The summary's <dl> lists Subtotal, then estimated sales tax, then
  // shipping, in that fixed order (see OrderDetailView.vue) — the first
  // <dd> is always the subtotal.
  const subtotalText = async () => (await page.locator('dl.row dd').first().innerText()).trim()

  await test.step('Sign out, sign in as the administrator, and ship the first item', async () => {
    await logout(page)
    await loginAs(page, ADMIN.email, ADMIN.password)

    await page.goto(`/order/${orderId}`)
    await expect(page.getByRole('heading', { name: `Order #${orderId}` })).toBeVisible()

    // The admin-only per-line <select> lets fulfilment move independently
    // of the customer's own "cancel" control (see OrderDetailView.vue).
    const shippedSelect = page.getByRole('combobox', { name: `Status for ${firstItemName}` })
    await shippedSelect.selectOption('shipped')
    await expect(page.getByRole('alert')).toContainText(/marked as shipped/i)
  })

  await test.step('The customer sees the shipped status', async () => {
    await logout(page)
    await loginAs(page, email, TEST_PASSWORD)

    await page.goto(`/order/${orderId}`)
    const shippedBadge = page.locator('li', { hasText: firstItemName }).getByText('Shipped')
    await expect(shippedBadge).toBeVisible()
  })

  await test.step('The customer cancels the other item — stock returns, the total drops', async () => {
    const before = await subtotalText()

    const otherLine = page.locator('li').filter({ hasNotText: firstItemName }).first()
    await otherLine.getByRole('button', { name: 'Cancel item' }).click()

    await expect(page.getByRole('alert')).toContainText(/cancelled/i)
    await expect(otherLine.getByText('Cancelled')).toBeVisible()

    const after = await subtotalText()
    expect(after).not.toBe(before)
  })

  await test.step('The customer cancels the last (already shipped) item — the whole order becomes Cancelled and Refunded', async () => {
    const lastLine = page.locator('li', { hasText: firstItemName })
    await lastLine.getByRole('button', { name: 'Cancel item' }).click()

    // The order is still there — not deleted — just marked cancelled, with
    // the payment showing refunded rather than paid. Scoped to the header
    // badge specifically, since by now every line item also reads
    // "Cancelled" and an unscoped match would be ambiguous about which one
    // it found.
    await expect(page.locator('.subpage-header').getByText('Cancelled', { exact: true })).toBeVisible()
    await expect(page.getByText('Refunded')).toBeVisible()
  })

  await test.step('An administrator cannot move a cancelled line back into fulfilment', async () => {
    await logout(page)
    await loginAs(page, ADMIN.email, ADMIN.password)
    await page.goto(`/order/${orderId}`)

    const cancelledSelect = page.getByRole('combobox', { name: `Status for ${firstItemName}` })
    await expect(cancelledSelect).toBeDisabled()
  })
})
