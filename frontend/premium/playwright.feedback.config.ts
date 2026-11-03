import { defineConfig } from '@playwright/test'
import defaultConfig from './playwright.config'

// EMPV synthetic feedback: own 5183 test server while the human preview uses 5182.
// Never connect this test configuration to shared Frappe DEV/STAGING.
const url = 'http://127.0.0.1:5183/assets/centrochange_core/premium/'

export default defineConfig({
  ...defaultConfig,
  use: { ...defaultConfig.use, baseURL: url },
  webServer: {
    command: 'VITE_CC_SYNTHETIC_UI=1 npm run dev -- --port 5183',
    url,
    reuseExistingServer: false,
    timeout: 30_000
  }
})
