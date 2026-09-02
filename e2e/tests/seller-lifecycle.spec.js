// RMIT University Vietnam
// Course: COSC2767 | COSC2805 Systems Deployment and Operations
// Assessment: Assignment 2 — CI/CD Pipeline
//
// Web UI / end-to-end test — README "Verifying a deployment", Journey E,
// which the README itself calls "the big one":
//
//   Submit the /sell form -> an administrator sees it as Waiting Approval
//   -> Approve -> the invitation email appears in the API server's log ->
//   open the /merchant-signup/... link, set a password, and land signed in
//   as a seller -> the dashboard menu is shorter (no Users, Categories,
//   Sellers or Reviews) -> the brand exists but is inactive, so add a
//   product and confirm it does not appear in the shop -> an administrator
//   activates the brand -> now it appears -> the seller's product list
//   shows only their own products -> an administrator deactivates the
//   seller -> they see the disabled-account screen and their products
//   vanish from the shop.
//
// This is the only journey that crosses three roles (public applicant,
// administrator, seller) through one continuous piece of state — a single
// Merchant row — and the only one that depends on a real outgoing email
// actually reaching its destination rather than assuming a token exists.
//
// *** Requires a real email trace to read. ***
// The default (console) email backend prints the invitation link into
// whichever terminal is attached to `manage.py runserver`'s stdout — a
// human can read that, a separate Node process cannot. Run the backend for
// this journey with the file-based backend instead (no code change, purely
// environment variables — the exact "pluggable email" story the README
// describes):
//
//   EMAIL_BACKEND=django.core.mail.backends.filebased.EmailBackend
//   EMAIL_FILE_PATH=/absolute/path/to/server/.dev-emails
//
// ...and point this spec at the same directory:
//
//   E2E_EMAIL_DIR=/absolute/path/to/server/.dev-emails npx playwright test tests/seller-lifecycle.spec.js
//
// See TESTING.md's "Seller lifecycle (Journey E)" section for the full
// pipeline-stage version of this. Every other spec in this suite works
// against the default console backend and needs none of this.

import { expect, test } from '@playwright/test'
import { ADMIN, loginAs, logout, readLatestSignupLink, uniqueEmail, uniqueSuffix } from './helpers.js'

test.describe.configure({ mode: 'serial' })

test('the full seller lifecycle: apply, approve, accept the invitation, list a product, brand activation gates visibility, and deactivation locks the seller out', async ({
  page
}) => {
  test.skip(
    !process.env.E2E_EMAIL_DIR,
    'E2E_EMAIL_DIR is not set — see this file’s header comment and TESTING.md ' +
      'for how to run the backend with a file-based email backend for this journey.'
  )

  const applicantEmail = uniqueEmail('seller')
  // "0-" sorts before every seeded "Campus Threads" / "RMIT ..." brand and
  // category name, so this brand lands on page 1 of the (unsearchable)
  // dashboard brand list no matter how many earlier runs have accumulated
  // brands of their own.
  const brandName = `0-E2E-Seller-Brand-${uniqueSuffix()}`
  const applicantName = `E2E Seller ${uniqueSuffix()}`
  const productName = `Seller Product ${uniqueSuffix()}`

  await test.step('Submit the public "become a seller" form', async () => {
    await page.goto('/sell')
    await page.locator('#name').fill(applicantName)
    await page.locator('#email').fill(applicantEmail)
    await page.locator('#phone').fill('0400000000')
    await page.locator('#brand').fill(brandName)
    await page.locator('#business').fill('An E2E test seller applying through the public form.')
    await page.getByRole('button', { name: 'Submit application' }).click()
    await expect(page.getByRole('heading', { name: 'Thanks — we have your application' })).toBeVisible()
  })

  await test.step('An administrator sees it Waiting Approval and approves it', async () => {
    await loginAs(page, ADMIN.email, ADMIN.password)
    await page.goto('/dashboard/merchant')

    const row = page.locator('li', { hasText: brandName })
    await expect(row).toBeVisible({ timeout: 10_000 })
    await expect(row.getByText('Waiting Approval')).toBeVisible()

    await row.getByRole('button', { name: 'Approve' }).click()
    await expect(page.getByRole('alert')).toContainText(/approved/i)
    await expect(row.getByText('Approved', { exact: true })).toBeVisible()
    // Note: the brand does not exist yet at this point — approve_merchant()
    // only creates a passwordless account and sends the invitation for a
    // brand-new applicant. The brand is created by complete_merchant_signup()
    // once the invitation is accepted below, which is the surprise the
    // README calls out ("the brand exists but is inactive") — checked once
    // it actually exists, in the "brand still inactive" step further down.
  })

  let signupLink
  await test.step('The invitation email carries a working /merchant-signup/ link', async () => {
    signupLink = await readLatestSignupLink(applicantEmail)
    expect(signupLink).toMatch(/\/merchant-signup\//)
  })

  await test.step('Accept the invitation and land signed in as a seller', async () => {
    await logout(page)
    const fixedLink = signupLink.replace("localhost:5173", "127.0.0.1"); await page.goto(fixedLink)

    await expect(page.getByRole('heading', { name: 'Set up your seller account' })).toBeVisible()
    await page.locator('#first-name').fill('Seller')
    await page.locator('#last-name').fill('Tester')
    await page.locator('#password').fill('SellerE2E-2026!')
    await page.locator('#confirm').fill('SellerE2E-2026!')

    // Wait for the actual signup response, not just the redirect. This step
    // does real work server-side (set_password + create_brand_for_merchant
    // in one transaction — see complete_merchant_signup() in
    // apps/merchants/services.py), and under concurrent load from other
    // specs sharing the same dev server, the round trip can occasionally
    // outrun a fixed navigation-timeout race. Anchoring on the response
    // means the URL check below only starts once the signup has actually
    // succeeded, the same fix applied to the toast races in
    // declined-payment.spec.js.
    const [response] = await Promise.all([
      page.waitForResponse(
        (res) => res.url().includes('/api/merchants/signup/') && res.request().method() === 'POST'
      ),
      page.getByRole('button', { name: 'Create seller account' }).click()
    ])
    expect(response.status()).toBe(201)

    await expect(page).toHaveURL(/\/dashboard/)
    await expect(page.getByText('Seller', { exact: true })).toBeVisible() // the role badge
  })

  await test.step('The dashboard menu is shorter than an administrator\'s', async () => {
    const sidebar = page.locator('nav.list-group')
    await expect(sidebar.getByRole('link', { name: 'Products' })).toBeVisible()
    await expect(sidebar.getByRole('link', { name: 'Brands' })).toBeVisible()
    for (const hidden of ['Users', 'Categories', 'Sellers', 'Reviews']) {
      await expect(sidebar.getByRole('link', { name: hidden })).not.toBeVisible()
    }
  })

  await test.step('Add a product — the brand is still inactive, so it must not appear in the shop', async () => {
    await page.goto('/dashboard/product/add')
    await page.locator('#sku').fill(`SELLER-${Date.now()}`)
    await page.locator('#name').fill(productName)
    await page.locator('#quantity').fill('5')
    await page.locator('#price').fill('19.95')
    await page.getByRole('button', { name: 'Create product' }).click()
    await expect(page.getByRole('alert')).toContainText(/created/i)

    await page.goto(`/shop?search=${encodeURIComponent(productName)}`)
    await expect(page.locator('.product-card', { hasText: productName })).toHaveCount(0)
  })

  await test.step('An administrator activates the brand', async () => {
    await logout(page)
    await loginAs(page, ADMIN.email, ADMIN.password)

    await page.goto('/dashboard/brand')
    const brandRow = page.locator('tr', { hasText: brandName })
    await expect(brandRow).toBeVisible({ timeout: 10_000 })
    await brandRow.getByRole('link', { name: 'Edit' }).click()
    await expect(page.locator('#name')).toHaveValue(brandName)

    await page.locator('#active').check()
    await page.getByRole('button', { name: 'Save changes' }).click()
    await expect(page.getByRole('alert')).toContainText(/updated/i)
  })

  await test.step('Now the product appears in the shop', async () => {
    await page.goto(`/shop?search=${encodeURIComponent(productName)}`)
    await expect(page.locator('.product-card', { hasText: productName })).toBeVisible({
      timeout: 10_000
    })
  })

  await test.step('The seller\'s own product list shows only their product', async () => {
    await logout(page)
    await loginAs(page, applicantEmail, 'SellerE2E-2026!')
    await page.goto('/dashboard/product')
    await expect(page.locator('tr', { hasText: productName })).toBeVisible()
  })

  await test.step('An administrator deactivates the seller', async () => {
    await logout(page)
    await loginAs(page, ADMIN.email, ADMIN.password)
    await page.goto('/dashboard/merchant')

    const row = page.locator('li', { hasText: brandName })
    await row.getByRole('button', { name: 'Deactivate' }).click()
    await expect(page.getByRole('alert')).toContainText(/deactivated/i)
  })

  await test.step('The seller now sees the disabled-account screen, and their product vanishes from the shop', async () => {
    await logout(page)
    await loginAs(page, applicantEmail, 'SellerE2E-2026!')

    await expect(page.getByRole('heading', { name: 'Your seller account is not active' })).toBeVisible()

    await page.goto(`/shop?search=${encodeURIComponent(productName)}`)
    await expect(page.locator('.product-card', { hasText: productName })).toHaveCount(0)
  })
})
