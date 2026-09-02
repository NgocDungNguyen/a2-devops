// RMIT University Vietnam
// Course: COSC2767 | COSC2805 Systems Deployment and Operations
// Assessment: Assignment 2 — CI/CD Pipeline
//
// Web UI / end-to-end test — README "Verifying a deployment", Journey D
// (Reviews and wishlist):
//
//   Post a review -> it appears immediately and the star rating updates ->
//   an administrator rejects it -> it disappears from the product page and
//   the average recomputes -> heart a product -> it shows in your wishlist
//   and the heart stays filled on the shop grid -> sign out and confirm the
//   hearts are empty with no errors in the console.
//
// The "no errors in the console" line is not a figure of speech — this
// spec actually listens for uncaught page errors for its whole duration and
// fails if one fires, which none of the other specs do. It is the right
// place for that check: signing out clears a lot of client-side state
// (Pinia stores, the wishlist cache) in one go, which is exactly the kind
// of moment a stale reference throws in production and nowhere else.

import { expect, test } from '@playwright/test'
import {
  ADMIN,
  loginAs,
  logout,
  realCatalogueCards,
  TEST_PASSWORD,
  uniqueEmail,
  uniqueSuffix
} from './helpers.js'

test('a review appears, is moderated away, and a wishlist heart clears cleanly on sign-out', async ({
  page
}) => {
  const email = uniqueEmail('reviewer')
  const reviewTitle = `Great product ${uniqueSuffix()}`
  const pageErrors = []
  page.on('pageerror', (error) => pageErrors.push(error))

  let productSlug
  let productName

  await test.step('Register and open a product page', async () => {
    await page.goto('/register')
    await page.locator('#first-name').fill('Reviewer')
    await page.locator('#last-name').fill('Tester')
    await page.locator('#email').fill(email)
    await page.locator('#password').fill(TEST_PASSWORD)
    await page.getByRole('button', { name: 'Create account' }).click()
    await expect(page).toHaveURL(/\/dashboard/)

    await page.goto('/shop')
    const firstCard = realCatalogueCards(page).first()
    await expect(firstCard).toBeVisible({ timeout: 15_000 })
    productName = await firstCard.locator('.product-card__name').innerText()
    await firstCard.locator('.product-card__name').click()
    productSlug = new URL(page.url()).pathname.split('/product/')[1]
  })

  await test.step('Post a review — it appears immediately', async () => {
    await page.locator('#review-title').fill(reviewTitle)
    await page.locator('#review-body').fill('Exactly as described, would buy again.')
    await page.getByRole('button', { name: 'Publish review' }).click()

    await expect(page.getByRole('alert')).toContainText(/published/i)
    await expect(page.getByText(reviewTitle)).toBeVisible()
  })

  await test.step('Heart the product — it shows in the wishlist and stays filled on the shop grid', async () => {
    const saveButton = page.getByRole('button', { name: /^Save$/ })
    await saveButton.click()
    await expect(page.getByRole('button', { name: 'Saved' })).toBeVisible()

    await page.goto('/dashboard/wishlist')
    await expect(page.getByText(productName)).toBeVisible()

    await page.goto('/shop')
    const heartedCard = page.locator('.product-card', { hasText: productName }).first()
    await expect(heartedCard.getByRole('button', { name: 'Remove from wishlist' })).toBeVisible()
  })

  await test.step('An administrator rejects the review — it disappears from the product page', async () => {
    await logout(page)
    await loginAs(page, ADMIN.email, ADMIN.password)

    await page.goto('/dashboard/review')
    const row = page.locator('li', { hasText: reviewTitle })
    await expect(row).toBeVisible({ timeout: 10_000 })
    await row.getByRole('button', { name: 'Reject' }).click()
    await expect(page.getByRole('alert')).toContainText(/rejected/i)

    await page.goto(`/product/${productSlug}`)
    await expect(page.getByText(reviewTitle)).not.toBeVisible()
  })

  await test.step('Sign out — the wishlist heart is empty everywhere, with no console errors', async () => {
    await logout(page)

    await page.goto('/shop')
    const card = page.locator('.product-card', { hasText: productName }).first()
    await expect(card.getByRole('button', { name: 'Add to wishlist' })).toBeVisible()
    await expect(card.getByRole('button', { name: 'Remove from wishlist' })).not.toBeVisible()

    expect(pageErrors, `Uncaught page errors: ${pageErrors.map(String).join('; ')}`).toHaveLength(0)
  })
})
