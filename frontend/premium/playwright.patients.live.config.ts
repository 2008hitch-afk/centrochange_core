import { defineConfig, devices } from '@playwright/test'

const url = process.env.CC_PATIENTS_ISOLATED_URL
if (process.env.CC_PATIENTS_ISOLATED !== 'YES' || url !== 'http://127.0.0.1:18067')
  throw new Error('AUDIT-04 live tests require the isolated localhost:18067 clone')

export default defineConfig({
  testDir: './tests', testMatch: 'patients.live.spec.ts',
  workers: 1,
  timeout: 60_000, expect: { timeout: 10_000 },
  use: { baseURL: url, browserName: 'chromium', trace: 'off', screenshot: 'only-on-failure' },
  projects: [
    { name: 'desktop', use: { ...devices['Desktop Chrome'], viewport: { width: 1440, height: 900 } } },
    { name: 'mobile', use: { ...devices['iPhone 13'], browserName: 'chromium', viewport: { width: 390, height: 844 } } },
  ],
})
