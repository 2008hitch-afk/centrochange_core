import { defineConfig, devices } from '@playwright/test'

export default defineConfig({
  testDir: './tests', testMatch: 'scoped.spec.ts', timeout: 30_000,
  expect: { timeout: 7_000 },
  use: { baseURL: 'http://127.0.0.1:5183/assets/centrochange_core/premium/', browserName: 'chromium', trace: 'retain-on-failure', screenshot: 'only-on-failure' },
  projects: [
    { name: 'desktop', use: { ...devices['Desktop Chrome'], viewport: { width: 1440, height: 900 } } },
    { name: 'mobile', use: { ...devices['iPhone 13'], browserName: 'chromium', viewport: { width: 390, height: 844 } } }
  ],
  webServer: { command: 'npm run dev -- --port 5183', url: 'http://127.0.0.1:5183/assets/centrochange_core/premium/', reuseExistingServer: false, timeout: 30_000 }
})
