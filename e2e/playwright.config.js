// RMIT University Vietnam
// Course: COSC2767 | COSC2805 Systems Deployment and Operations
// Assessment: Assignment 2 — CI/CD Pipeline
//
// Web UI / end-to-end test configuration.
//
// These tests exercise the whole stack over real HTTP: a browser drives the
// built (or dev-served) Vue SPA, which calls the real Django REST API, which
// reads and writes the real database. Nothing here is mocked — that is the
// point. A green run is proof that the frontend, the backend and the
// database are wired together correctly in whichever environment E2E_BASE_URL
// points at, which is exactly what a post-deploy pipeline gate needs to know.
//
// E2E_BASE_URL selects the target:
//   http://localhost:5173   Plan A, `npm run dev` (the default)
//   http://localhost:4173   Plan A, `vite preview` against the production build
//   http://<staging-host>   the pipeline's staging gate, before promoting to prod
//   http://<prod-host>      a post-deploy verification pass on production itself
//
// See ../TESTING.md for the exact commands each pipeline stage runs.

import { defineConfig, devices } from '@playwright/test'

const BASE_URL = process.env.E2E_BASE_URL || 'http://localhost:5173'

export default defineConfig({
  testDir: './tests',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  // Retry once in CI — a flaky network hiccup against a real staging
  // deployment should not fail the pipeline; the same failure on every retry
  // means it is a real regression.
  retries: process.env.CI ? 1 : 0,
  workers: process.env.CI ? 2 : undefined,
  timeout: 30_000,
  expect: { timeout: 8_000 },

  // JUnit is what Jenkins' junit step reads to publish a pass/fail table per
  // test; HTML is for a human to open after a failed build; list keeps the
  // console readable while it runs.
  reporter: process.env.CI
    ? [
        ['list'],
        ['junit', { outputFile: 'results/junit.xml' }],
        ['html', { outputFolder: 'results/html', open: 'never' }]
      ]
    : [['list'], ['html', { outputFolder: 'results/html', open: 'never' }]],

  use: {
    baseURL: BASE_URL,
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure'
  },

  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } }
  ]
})
