// RMIT University Vietnam
// Course: COSC2767 | COSC2805 Systems Deployment and Operations
// Assessment: Assignment 2 — CI/CD Pipeline
//
// Web UI / end-to-end test — the full acceptance journey the assignment
// brief asks for by name: "simulate the full user journey (Register -> Sign
// In -> Add to Cart -> Checkout)". It is also, almost verbatim, Journey B
// from the README's "Verifying a deployment" section, which the README
// itself describes as "written to be converted directly into automated
// end-to-end tests" — this file is that conversion.
//
// One long journey rather than several short, independent tests on purpose:
// splitting "register" and "sign in" and "checkout" into isolated tests
// would need each one to fabricate the state the last one produced (an
// authenticated session, an item in the bag), which tests nothing that the
// real user journey does not already prove in sequence. A failure partway
// through still tells you exactly which step broke, because each step has
// its own `test.step()` block and its own assertion.

import { expect, test } from '@playwright/test'
import { CARDS, realCatalogueCards, TEST_PASSWORD, uniqueEmail } from './helpers.js'

test.describe.configure({ mode: 'serial' })

test('register, sign in, add to cart, and complete checkout with an approved card', async ({
  page
}) => {
  const email = uniqueEmail('journey')
  let orderId

  await test.step('Register a new account', async () => {
    await page.goto('/register')
    await page.locator('#first-name').fill('Journey')
    await page.locator('#last-name').fill('Tester')
    await page.locator('#email').fill(email)
    await page.locator('#password').fill(TEST_PASSWORD)
    await page.getByRole('button', { name: 'Create account' }).click()

    // RegisterView signs the new account straight in and redirects to the
    // dashboard — confirms the register call succeeded end to end.
    await expect(page).toHaveURL(/\/dashboard/)
    await expect(page.getByRole('alert')).toContainText(/Welcome to the RMIT Store/i)
  })

  await test.step('Sign out', async () => {
    await page.getByRole('button', { name: 'Account' }).click()
    await page.getByRole('button', { name: 'Sign out' }).click()
    await expect(page).toHaveURL('/')
    await expect(page.getByRole('alert')).toContainText(/signed out/i)

    // The account menu now offers "Sign in" instead of "Dashboard" /
    // "Sign out" — confirms the client-side session was actually cleared,
    // not just that the toast fired.
    await page.getByRole('button', { name: 'Account' }).click()
    await expect(page).toHaveURL('/')
  })

  await test.step('Sign in with the account just created', async () => {
    await page.goto('/login')
    await page.locator('#email').fill(email)
    await page.locator('#password').fill(TEST_PASSWORD)
    await page.getByRole('button', { name: 'Sign in' }).click()

    await expect(page).toHaveURL(/\/dashboard/)
    await expect(page.getByRole('alert')).toContainText(/Welcome back/i)
  })

  await test.step('Add a product to the bag', async () => {
    await page.goto('/shop')
    const firstCard = realCatalogueCards(page).first()
    await expect(firstCard).toBeVisible({ timeout: 15_000 })
    await firstCard.locator('.product-card__name').click()

    await expect(page).toHaveURL(/\/product\//)
    await page.getByRole('button', { name: 'Add to bag' }).click()

    // Adding to bag opens the drawer automatically (ProductView.addToBag()).
    const drawer = page.getByRole('dialog', { name: 'Your bag' })
    await expect(drawer).toBeVisible()
    await expect(drawer.getByRole('button', { name: /Pay and place order/ })).toBeVisible()
  })

  await test.step('Pay with an approved test card', async () => {
    const drawer = page.getByRole('dialog', { name: 'Your bag' })

    // The card form ships with buttons that fill in a whole documented test
    // card (number, a future expiry, and a correctly-sized CVC) in one
    // click — see PaymentForm.vue's `useTestCard()`. Using it here is not a
    // shortcut around the form; it is the same control a human demoing the
    // store clicks, and it still drives every input the checkout submits.
    await drawer.getByText('No real cards - use a test number').click()
    await drawer
      .getByRole('button', { name: new RegExp(`${CARDS.approved} - succeeds`) })
      .click()

    const payButton = drawer.getByRole('button', { name: /Pay and place order/ })
    await expect(payButton).toBeEnabled()
    await payButton.click()

    // A successful checkout redirects to /order/success/:id.
    await page.waitForURL(/\/order\/success\/\d+/, { timeout: 15_000 })
    orderId = page.url().match(/\/order\/success\/(\d+)/)[1]
    await expect(page.getByRole('heading', { name: 'Thank you for your order' })).toBeVisible()
    await expect(page.getByText(`#${orderId}`)).toBeVisible()
  })

  await test.step('The order detail page shows a paid order with correct totals', async () => {
    await page.getByRole('link', { name: 'View order' }).click()
    await expect(page).toHaveURL(new RegExp(`/order/${orderId}$`))

    // "Paid", a card brand and the last four digits are exactly what the
    // README's screenshot of a real checkout shows — proof the payment
    // gateway's response reached the order row, not just the success page.
    await expect(page.getByText(/Paid/i).first()).toBeVisible()
    await expect(page.getByText(/Visa ending 4242/i)).toBeVisible()
  })
})
