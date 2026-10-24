import { defineConfig, devices } from '@playwright/test'

if (process.env.CC_PROFESSIONALS_ISOLATED !== 'YES' || process.env.CC_PROFESSIONALS_ISOLATED_URL !== 'http://127.0.0.1:18071')
  throw new Error('AUDIT-05 live tests require the identified isolated localhost:18071 clone')

export default defineConfig({
  testDir: './tests', testMatch: 'professionals.live.spec.ts',
  workers: 1, timeout: 60_000, expect: { timeout: 10_000 },
  use: { baseURL: process.env.CC_PROFESSIONALS_ISOLATED_URL, browserName: 'chromium', screenshot: 'only-on-failure' },
  projects: [
    { name: 'desktop', use: { ...devices['Desktop Chrome'], viewport: { width: 1440, height: 900 } } },
    { name: 'mobile', use: { ...devices['iPhone 13'], browserName: 'chromium', viewport: { width: 390, height: 844 } } },
  ],
})
