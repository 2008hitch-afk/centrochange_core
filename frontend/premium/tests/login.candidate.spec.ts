/** #158: real synthetic Frappe sessions, candidate assets served by Playwright only. No DEV install. */
import { expect, test, type Browser, type Page } from '@playwright/test'
import { readFileSync, statSync } from 'node:fs'
import { resolve } from 'node:path'

type Role = 'm' | 's' | 'a' | 'b' | 'c' | 'f' | 't'
type Credentials = { tag: string; centers: string[]; users: Record<Role, { name: string; password: string }> }
const root = resolve(process.cwd(), '../..')
const privatePath = process.env.CC_LOGIN_UAT_CREDENTIALS
if (!privatePath || resolve(privatePath).startsWith(root + '/') || (statSync(privatePath).mode & 0o077)) {
  throw new Error('Private synthetic login fixture with mode 0600 required outside Git')
}
const fixture = JSON.parse(readFileSync(privatePath, 'utf8')) as Credentials
const roles: Role[] = ['m', 's', 'a', 'b', 'c', 'f', 't']
if (!/^CC-HTTP-[A-Za-z0-9]{10}$/.test(fixture.tag) || fixture.centers?.length !== 2 ||
    roles.some(role => !fixture.users?.[role]?.name.endsWith('.invalid') || !fixture.users[role].password)) {
  throw new Error('Only complete synthetic UAT identities are allowed')
}
const publicRoot = resolve(root, 'app/centrochange_core/centrochange_core/public')
const candidateAssets = new Set(['app.js', 'app.css'])
const chunk = /style-[A-Za-z0-9_-]+\.js$/

async function useCandidate(page: Page) {
  await page.route('**/assets/centrochange_core/premium/*', route => {
    const name = new URL(route.request().url()).pathname.split('/').at(-1) ?? ''
    if (!candidateAssets.has(name) && !chunk.test(name)) return route.continue()
    const path = resolve(publicRoot, 'premium', name)
    return route.fulfill({ body: readFileSync(path, 'utf8'), contentType: name.endsWith('.css') ? 'text/css' : 'text/javascript' })
  })
}
async function login(page: Page, role: Role) {
  await page.goto('/login?redirect-to=/premium')
  await page.locator('#login_email').fill(fixture.users[role].name)
  await page.locator('#login_password').fill(fixture.users[role].password)
  await page.locator('.form-login button[type=submit]').click()
  await expect(page).toHaveURL(/\/premium$/)
  await expect(page.locator('main#main')).toBeVisible()
  await expect(page.locator('.loading-state')).toBeHidden()
  await expect(page.locator('.breadcrumbs strong')).toContainText(/Agenda|Finanza/)
}
async function newCandidateContext(browser: Browser, role: Role, mobile: boolean) {
  const context = await browser.newContext({ viewport: mobile ? { width: 390, height: 844 } : { width: 1440, height: 900 } })
  const page = await context.newPage()
  await useCandidate(page)
  await login(page, role)
  return { context, page }
}
async function menuAction(page: Page, name: string) {
  if ((page.viewportSize()?.width ?? 1440) < 760) await page.getByRole('button', { name: 'Apri menu' }).click()
  await page.getByRole('button', { name, exact: true }).click()
}

test('native login: Guest, invalid credentials, seven roles and direct protected route', async ({ browser }, info) => {
  const guest = await browser.newContext()
  const guestPage = await guest.newPage()
  await guestPage.goto('/premium#Finanza')
  await expect(guestPage).toHaveURL(/\/login\?redirect-to=\/premium/)
  await expect(guestPage.locator('#login_email')).toBeVisible()
  const guestApi = await guest.request.get('/api/method/centrochange_core.operations.workspace.bootstrap')
  expect(guestApi.ok()).toBe(false)
  await guest.close()

  const invalid = await browser.newContext()
  const invalidPage = await invalid.newPage()
  await invalidPage.goto('/login?redirect-to=/premium')
  await invalidPage.locator('#login_email').fill('cc158.invalid@example.invalid')
  await invalidPage.locator('#login_password').fill('invalid')
  await invalidPage.locator('.form-login button[type=submit]').click()
  await expect(invalidPage).toHaveURL(/\/login/)
  await expect(invalidPage.locator('.form-login .login-error-banner .es-alert__title')).not.toBeEmpty()
  await invalid.close()

  for (const role of roles) {
    const context = await browser.newContext({ viewport: info.project.name === 'mobile' ? { width: 390, height: 844 } : { width: 1440, height: 900 } })
    try {
      const page = await context.newPage()
      await useCandidate(page)
      await login(page, role)
      const expected = role === 'f' || role === 't' ? 'Finanza' : 'Agenda'
      await expect(page.locator('.breadcrumbs strong')).toHaveText(expected)
      const csrf = await page.locator('meta[name="csrf-token"]').getAttribute('content')
      expect(csrf).toBeTruthy()
      const direct = await context.request.get('/premium#Gestione%20accessi', { maxRedirects: 0 })
      expect(direct.status()).toBe(200)
      await page.reload()
      await expect(page.locator('.breadcrumbs strong')).toHaveText(expected)
      if (role === 'a') {
        await page.goto('/premium#Finanza')
        await expect(page.locator('.breadcrumbs strong')).toHaveText('Agenda')
      }
      if (role === 'f' || role === 't') {
        await page.goto('/premium#Gestione%20accessi')
        await expect(page.locator('.breadcrumbs strong')).toHaveText('Finanza')
      }
      const catalog = await context.request.get('/api/method/centrochange_core.catalog.records', {
        params: { center: fixture.centers[0], kind: 'Item', limit: 1 }
      })
      expect(catalog.ok()).toBe(role === 'm')
      expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true)
    } finally { await context.close() }
  }
})

test('native login presentation candidate: brand, Italian error, keyboard, responsive', async ({ page }, info) => {
  await page.goto('/login?redirect-to=/premium')
  await page.addStyleTag({ path: resolve(publicRoot, 'css/login_v1.css') })
  await page.evaluate(() => document.querySelectorAll<HTMLImageElement>('.page-card-head .app-logo')
    .forEach(image => { image.src = '/assets/centrochange_core/premium/logo.webp' }))
  await page.addScriptTag({ path: resolve(publicRoot, 'js/login_v1.js') })
  await expect(page.getByRole('heading', { name: 'Accedi', level: 1 })).toBeVisible()
  await expect(page.locator('.form-login .login-error-banner')).toBeHidden()
  await expect(page.locator('.page-card-head .app-logo').first()).toHaveAttribute('alt', 'Centro Change')
  await expect(page.getByRole('button', { name: 'Mostra password' })).toBeVisible()
  await page.getByRole('button', { name: 'Mostra password' }).focus()
  await page.keyboard.press('Space')
  await expect(page.locator('#login_password')).toHaveAttribute('type', 'text')
  await page.getByRole('button', { name: 'Nascondi password' }).press('Enter')
  await expect(page.locator('#login_password')).toHaveAttribute('type', 'password')
  await page.locator('#login_email').fill('cc158.invalid@example.invalid')
  await page.locator('#login_password').fill('invalid')
  await page.locator('.form-login button[type=submit]').click()
  await expect(page.locator('.form-login .login-error-banner')).toContainText('Credenziali non valide')
  await expect(page.locator('.form-login .login-error-banner')).not.toContainText('Invalid credentials')
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true)
  await page.screenshot({ path: info.outputPath(`login-candidate-${info.project.name}.png`), fullPage: true })
  await page.getByRole('link', { name: 'Password dimenticata?' }).click()
  await expect(page.getByRole('heading', { name: 'Password dimenticata?', level: 1 })).toBeVisible()
  await page.getByRole('link', { name: 'Torna all’accesso' }).click()
  await page.getByRole('link', { name: 'Accedi con link email' }).click()
  await expect(page.getByRole('button', { name: 'Invia link di accesso' })).toBeVisible()
})

test('candidate logout failure does not falsely confirm exit; retry succeeds', async ({ browser }, info) => {
  const { context, page } = await newCandidateContext(browser, 'm', info.project.name === 'mobile')
  try {
    let failed = false
    await page.route('**/api/method/logout', route => {
      if (!failed) { failed = true; return route.fulfill({ status: 503, contentType: 'application/json', body: '{"exc":"Synthetic failure"}' }) }
      return route.continue()
    })
    await menuAction(page, 'Esci')
    await expect(page.getByRole('alert')).toContainText('Uscita non riuscita. Riprova.')
    await expect(page).toHaveURL(/\/premium$/)
    expect((await context.request.get('/premium', { maxRedirects: 0 })).status()).toBe(200)
    if (info.project.name === 'mobile') await page.getByRole('button', { name: 'Esci' }).click()
    else await menuAction(page, 'Esci')
    await expect(page).toHaveURL(/\/login\?redirect-to=\/premium/)
    const protectedPage = await context.request.get('/premium', { maxRedirects: 0 })
    expect(protectedPage.status()).toBe(301)
  } finally { await context.close() }
})

test('candidate detects expired cookie on an existing React page', async ({ browser }, info) => {
  const { context, page } = await newCandidateContext(browser, 'm', info.project.name === 'mobile')
  try {
    await context.clearCookies()
    await menuAction(page, 'Report')
    const from = page.locator('.panel-toolbar').filter({ hasText: 'Riepilogo operativo' }).locator('input.date-input').first()
    await page.waitForURL(/\/login\?redirect-to=\/premium/, { timeout: 2_000 }).catch(async () => {
      if (await from.isVisible()) {
        await from.fill('02/10/2026', { timeout: 2_000 }).catch(() => { /* redirect already in progress */ })
        await from.blur({ timeout: 2_000 }).catch(() => { /* redirect already in progress */ })
      }
    })
    await expect(page).toHaveURL(/\/login\?redirect-to=\/premium/)
    await expect(page.locator('#login_email')).toBeVisible()
  } finally { await context.close() }
})
