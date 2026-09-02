import fs from 'node:fs'
import path from 'node:path'
import { expect } from '@playwright/test'

export function uniqueEmail(prefix = 'e2e') {
  const stamp = Date.now()
  const random = Math.floor(Math.random() * 100000)
  return `${prefix}.${stamp}.${random}@example.com`
}

export function uniqueSuffix() {
  return `E2E ${Date.now()}-${Math.floor(Math.random() * 10000)}`
}

export const TEST_PASSWORD = 'RmitStore-E2E-2026!'

export const CARDS = {
  approved: '4242 4242 4242 4242',
  declinedCardDeclined: '4000 0000 0000 0002',
  declinedInsufficientFunds: '4000 0000 0000 9995'
}

export const ADMIN = {
  email: process.env.E2E_ADMIN_EMAIL || 'admin@rmit.edu.au',
  password: process.env.E2E_ADMIN_PASSWORD || 'RmitStore2767!'
}

export function realCatalogueCards(page) {
  return page
    .locator('.product-card')
    .filter({ hasNotText: 'E2E' })
    .filter({ hasNotText: 'Out of stock' })
}

export async function findRowAcrossPages(page, name, { maxPages = 15 } = {}) {
  for (let attempt = 0; attempt < maxPages; attempt++) {
    const row = page.locator('tr', { hasText: name })
    const foundOnThisPage = await row
      .first()
      .waitFor({ state: 'visible', timeout: 2_000 })
      .then(() => true)
      .catch(() => false)
    if (foundOnThisPage) return row.first()

    const nextButton = page.getByRole('button', { name: 'Next' })
    if ((await nextButton.count()) === 0) break

    const nextListItem = page.locator('li.page-item', { has: nextButton })
    const onLastPage = await nextListItem.evaluate((el) => el.classList.contains('disabled'))
    if (onLastPage) break

    await nextButton.click()
  }
  return page.locator('tr', { hasText: name })
}

export async function loginAs(page, email, password) {
  await page.goto('/login')
  await page.locator('#email').fill(email)
  await page.locator('#password').fill(password)
  await page.getByRole('button', { name: 'Sign in' }).click()
  await expect(page).toHaveURL(/\/dashboard/)
}

export async function logout(page) {
  await page.goto('/shop')
  await page.getByRole('button', { name: 'Account' }).click()
  await page.getByRole('button', { name: 'Sign out' }).click()
  await expect(page).toHaveURL('/')
}

export async function readLatestSignupLink(merchantEmail, { timeoutMs = 10_000 } = {}) {
  const emailDir = process.env.E2E_EMAIL_DIR
  if (!emailDir) {
    throw new Error('E2E_EMAIL_DIR is not set.')
  }

  const deadline = Date.now() + timeoutMs
  let lastSeenFile = null
  while (Date.now() < deadline) {
    if (fs.existsSync(emailDir)) {
      const files = fs
        .readdirSync(emailDir)
        .map((name) => ({ name, mtime: fs.statSync(path.join(emailDir, name)).mtimeMs }))
        .sort((a, b) => b.mtime - a.mtime)

      for (const file of files) {
        const content = fs.readFileSync(path.join(emailDir, file.name), 'utf-8')
        lastSeenFile = file.name
        if (!content.includes(merchantEmail)) continue
        const match = content.match(/https?:\/\/\S*\/merchant-signup\/([\w:-]+)/)
        if (match) return match[0].trim()
      }
    }
    await new Promise((resolve) => setTimeout(resolve, 250))
  }

  throw new Error(`No link found for ${merchantEmail}`)
}
