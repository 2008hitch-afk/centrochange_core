import { defineConfig, devices } from '@playwright/test'
import { resolve } from 'node:path'
import { statSync } from 'node:fs'

const baseURL = process.env.CC_LOGIN_LIVE_URL
const outputDir = process.env.CC_LOGIN_OUTPUT_DIR
if (!baseURL || !/^http:\/\/127\.0\.0\.1:\d+$/.test(baseURL) || !outputDir ||
    resolve(outputDir).startsWith(resolve(process.cwd(), '../..') + '/') || (statSync(outputDir).mode & 0o077)) {
  throw new Error('Login QA requires loopback DEV and private output outside Git')
}

export default defineConfig({
  testDir: './tests', testMatch: 'login.candidate.spec.ts', timeout: 120_000,
  workers: 1, outputDir,
  expect: { timeout: 12_000 },
  use: { baseURL, browserName: 'chromium', trace: 'retain-on-failure', screenshot: 'only-on-failure' },
  projects: [
    { name: 'desktop', use: { ...devices['Desktop Chrome'], viewport: { width: 1440, height: 900 } } },
    { name: 'mobile', use: { ...devices['iPhone 13'], browserName: 'chromium', viewport: { width: 390, height: 844 } } }
  ]
})
