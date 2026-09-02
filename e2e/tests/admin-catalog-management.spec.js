import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { expect, test } from '@playwright/test'
import { ADMIN, findRowAcrossPages, loginAs, uniqueSuffix } from './helpers.js'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const SAMPLE_IMAGE = path.resolve(__dirname, '../../server/seed_assets/products/p-1.jpg')

test.describe.configure({ mode: 'serial' })

async function openEditFormAndWaitForLoad(page, listPath, rowName) {
  await page.goto(listPath)
  const row = await findRowAcrossPages(page, rowName)
  // Ép click xuyên qua alert của thao tác trước
  await row.getByRole('link', { name: 'Edit' }).click({ force: true })
  await expect(page.locator('#name')).toHaveValue(rowName)
}

test('an administrator creates, edits, deactivates and deletes a category, a brand and a product; and searches the user list', async ({ page }) => {
  const categoryName = `Category ${uniqueSuffix()}`
  const brandName = `Brand ${uniqueSuffix()}`
  const productName = `Product ${uniqueSuffix()}`
  const productSku = `E2E-${Date.now()}`

  await test.step('Sign in as the administrator', async () => {
    await loginAs(page, ADMIN.email, ADMIN.password)
  })

  await test.step('Create a category', async () => {
    await page.goto('/dashboard/category')
    await page.getByRole('link', { name: 'Add category' }).click()
    await page.locator('#name').fill(categoryName)
    await page.locator('#description').fill('Created by the E2E administration journey.')
    await page.getByRole('button', { name: 'Create category' }).click()
    await expect(page.getByRole('alert')).toContainText(/created/i)
    await expect(await findRowAcrossPages(page, categoryName)).toBeVisible()
  })

  await test.step('Create a product to exercise the category multi-select', async () => {
    await page.goto('/dashboard/product')
    await page.getByRole('link', { name: 'Add product' }).click()

    await page.locator('#sku').fill(productSku)
    await page.locator('#name').fill(productName)
    await page.locator('#quantity').fill('10')
    await page.locator('#price').fill('25.00')
    await page.locator('#image').setInputFiles(SAMPLE_IMAGE)
    await page.getByRole('button', { name: 'Create product' }).click()

    await expect(page.getByRole('alert')).toContainText(/created/i)
    await expect(page).toHaveURL(/\/dashboard\/product$/)
    await expect(await findRowAcrossPages(page, productName)).toBeVisible()
  })

  await test.step('Edit the category: select the product in the multi-select, save, and confirm it round-trips', async () => {
    await openEditFormAndWaitForLoad(page, '/dashboard/category', categoryName)

    await page.locator('#products').selectOption({ label: productName })
    await page.getByRole('button', { name: 'Save changes' }).click()
    await expect(page.getByRole('alert')).toContainText(/updated/i)

    await openEditFormAndWaitForLoad(page, '/dashboard/category', categoryName)
    const selected = await page.locator('#products').evaluate((select) =>
      Array.from(select.selectedOptions).map((option) => option.textContent.trim())
    )
    expect(selected).toContain(productName)
  })

  await test.step('The product renders its uploaded image', async () => {
    await page.goto('/dashboard/product')
    const row = await findRowAcrossPages(page, productName)
    const thumbnail = row.locator('img')
    await expect(thumbnail).toBeVisible()
    await expect(thumbnail).toHaveAttribute('src', /\/media\/products\//)
  })

  await test.step('The product also appears on the public storefront', async () => {
    await page.goto(`/shop?search=${encodeURIComponent(productName)}`)
    await expect(page.locator('.product-card', { hasText: productName })).toBeVisible({ timeout: 10_000 })
  })

  await test.step('Create a brand, then edit it', async () => {
    await page.goto('/dashboard/brand')
    await page.getByRole('link', { name: 'Add brand' }).click()
    await page.locator('#name').fill(brandName)
    await page.locator('#description').fill('Created by the E2E administration journey.')
    await page.getByRole('button', { name: 'Create brand' }).click()
    await expect(page.getByRole('alert')).toContainText(/created/i)
    await expect(await findRowAcrossPages(page, brandName)).toBeVisible()

    await openEditFormAndWaitForLoad(page, '/dashboard/brand', brandName)
    await page.locator('#description').fill('Updated description from the E2E journey.')
    await page.getByRole('button', { name: 'Save changes' }).click()
    await expect(page.getByRole('alert')).toContainText(/updated/i)
  })

  await test.step('Deactivate the category, the brand and the product', async () => {
    for (const [listPath, name] of [
      ['/dashboard/category', categoryName],
      ['/dashboard/brand', brandName],
      ['/dashboard/product', productName]
    ]) {
      await openEditFormAndWaitForLoad(page, listPath, name)
      const activeSwitch = page.locator('#active')
      if (await activeSwitch.isChecked()) await activeSwitch.uncheck()
      await page.getByRole('button', { name: /Save changes/ }).click()
      await expect(page.getByRole('alert')).toContainText(/updated/i)
    }

    await page.goto('/dashboard/product')
    const productRow = await findRowAcrossPages(page, productName)
    await expect(productRow.getByText('Inactive')).toBeVisible()
  })

  await test.step('Delete the category, the brand and the product', async () => {
    for (const [listPath, name] of [
      ['/dashboard/product', productName],
      ['/dashboard/category', categoryName],
      ['/dashboard/brand', brandName]
    ]) {
      await page.goto(listPath)
      const row = await findRowAcrossPages(page, name)
      await row.getByRole('button', { name: 'Delete' }).click()
      await expect(page.getByRole('alert')).toContainText(/deleted/i)
      await expect(page.locator('tr', { hasText: name })).toHaveCount(0)
    }
  })

  await test.step('Search the user list', async () => {
    await page.goto('/dashboard/users')
    const searchBox = page.getByRole('searchbox', { name: 'Search users' })
    await searchBox.fill('rmit.edu.au')
    await searchBox.press('Enter')
    await expect(page.locator('tbody tr').first()).toBeVisible()
    const rowCountForRealSearch = await page.locator('tbody tr').count()
    expect(rowCountForRealSearch).toBeGreaterThan(0)

    await searchBox.fill('no-such-person-xyz')
    await searchBox.press('Enter')
    await expect(page.getByText('No users match that search.')).toBeVisible()
  })
})
