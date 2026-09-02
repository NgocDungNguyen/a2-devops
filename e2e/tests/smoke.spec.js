// RMIT University Vietnam
// Course: COSC2767 | COSC2805 Systems Deployment and Operations
// Assessment: Assignment 2 — CI/CD Pipeline
//
// Web UI smoke test — the browser-driven equivalent of scripts/smoke_test.py.
//
// Deliberately the cheapest, least specific test in the whole E2E suite: it
// asks only "does the SPA render, and does it manage to show at least one
// product from the real API and the real database?" That single assertion
// is what the assignment brief means by "that the shop page renders
// products, proving frontend -> backend -> database is connected end to
// end" — every deeper journey (register, sign in, checkout) is only worth
// running if this one already passes, which is why it runs first and fails
// fast if it does not.

import { expect, test } from '@playwright/test'

test.describe('Smoke: the storefront is alive end to end', () => {
  test('the home page loads with the RMIT Store shell', async ({ page }) => {
    await page.goto('/')
    await expect(page).toHaveTitle(/RMIT Store/)
    // The header renders on every page — its presence means Vue mounted,
    // the router resolved a route, and no unhandled error blanked the page.
    await expect(page.getByRole('link', { name: 'RMIT Store' })).toBeVisible()
  })

  test('the shop page renders products served by the real API', async ({ page }) => {
    await page.goto('/shop')

    // A product card only exists once ShopView has called the catalog store,
    // which called GET /api/products/, which the Django view answered from
    // PostgreSQL/SQLite. A grey placeholder page (API down) or an empty grid
    // (seed data missing) both fail this line — see the README's
    // "The frontend loads but every request fails" troubleshooting entry.
    const firstCard = page.locator('.product-card').first()
    await expect(firstCard).toBeVisible({ timeout: 15_000 })

    const cardCount = await page.locator('.product-card').count()
    expect(cardCount).toBeGreaterThan(0)
  })

  test('a product card links through to a working product detail page', async ({ page }) => {
    await page.goto('/shop')
    const firstCard = page.locator('.product-card').first()
    await expect(firstCard).toBeVisible({ timeout: 15_000 })

    await firstCard.locator('.product-card__name').click()
    await expect(page).toHaveURL(/\/product\//)

    // Price, stock badge and the "Add to bag" affordance are the three
    // things the README calls out as proof the product page is wired up:
    // "the image, price, stock and star summary."
    await expect(page.locator('.product-card__price, .h4.text-brand')).toBeVisible()
  })

  test('anonymous visitors can reach the register and login pages', async ({ page }) => {
    await page.goto('/register')
    await expect(page.getByRole('heading', { name: 'Create an account' })).toBeVisible()

    await page.goto('/login')
    await expect(page.getByRole('heading', { name: 'Sign in' })).toBeVisible()
  })
})
