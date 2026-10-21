import { defineConfig, devices } from '@playwright/test'

const baseURL = process.env.CC_PREMIUM_LIVE_URL
if (!baseURL || !/^http:\/\/127\.0\.0\.1:\d+$/.test(baseURL)) throw new Error('CC_PREMIUM_LIVE_URL must be a local forwarded DEV URL')

export default defineConfig({
  testDir: './tests', testMatch: 'live.spec.ts', timeout: 60_000, workers: 1,
  expect: { timeout: 10_000 },
  use: { baseURL, browserName: 'chromium', trace: 'retain-on-failure', screenshot: 'only-on-failure' },
  projects: [
    { name: 'desktop', use: { ...devices['Desktop Chrome'], viewport: { width: 1440, height: 900 } } },
    { name: 'mobile', use: { ...devices['iPhone 13'], browserName: 'chromium', viewport: { width: 390, height: 844 } } }
  ]
})
