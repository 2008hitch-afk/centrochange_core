/** Real Frappe acceptance. No routes are mocked. Run only after the Owner gate. */
import { expect, test, type Browser } from '@playwright/test'
import { readFileSync, statSync } from 'node:fs'
import { resolve } from 'node:path'

type Role = 'manager' | 'secretariat' | 'professional_a' | 'professional_b' | 'professional_c' | 'finance' | 'accountant'
type Fixture = { synthetic_only: true; site: 'centrochange.local'; center_a: string; center_b: string;
  item_a: string; payment_a: string; invoice_a: string; roles: Record<Role, string>;
  owned_write: { tag: string; center: string; item: string } }
const fixturePath = process.env.CC_PREMIUM_LIVE_FIXTURE
if (!fixturePath || !process.env.CC_PREMIUM_LIVE_SYNTHETIC || process.env.CC_PREMIUM_LIVE_SYNTHETIC !== 'YES')
  throw new Error('Gated synthetic fixture and explicit CC_PREMIUM_LIVE_SYNTHETIC=YES required')
const repoRoot = resolve(process.cwd(), '../..')
const privateFile = (path: string) => {
  const absolute = resolve(path)
  if (absolute === repoRoot || absolute.startsWith(repoRoot + '/') || (statSync(absolute).mode & 0o077))
    throw new Error('Live fixture/session must be outside Git with mode 0600')
  return absolute
}
const fixture = JSON.parse(readFileSync(privateFile(fixturePath), 'utf8')) as Fixture
const names: Role[] = ['manager', 'secretariat', 'professional_a', 'professional_b', 'professional_c', 'finance', 'accountant']
if (fixture.synthetic_only !== true || fixture.site !== 'centrochange.local' ||
    !fixture.center_a || !fixture.center_b || fixture.center_a === fixture.center_b ||
    !fixture.item_a || !fixture.payment_a || !fixture.invoice_a ||
    !/^CC-HTTP-[A-Za-z0-9]{10}$/.test(fixture.owned_write?.tag || '') ||
    !fixture.owned_write.center ||
    fixture.owned_write.center === fixture.center_a || fixture.owned_write.center === fixture.center_b ||
    fixture.owned_write.item !== fixture.owned_write.tag + ' SESSION' ||
    names.some(name => !fixture.roles?.[name])) throw new Error('Incomplete synthetic single-Site fixture')
for (const role of names) privateFile(fixture.roles[role])

const endpoint = (name: string) => '/api/method/centrochange_core.' + name
const denied = (response: { ok(): boolean }) => expect(response.ok()).toBeFalsy()
async function roleContext(browser: Browser, role: Role) {
  return browser.newContext({ storageState: privateFile(fixture.roles[role]) })
}

test('same Site shell, compiled assets and responsive archive navigation', async ({ browser }, info) => {
  const context = await roleContext(browser, 'manager')
  try {
    const page = await context.newPage()
    const shell = await page.goto('/premium')
    expect(shell?.ok()).toBeTruthy()
    await page.keyboard.press('Tab')
    await expect(page.locator('.skip-link')).toBeFocused()
    await page.keyboard.press('Enter')
    await expect(page.locator('main#main')).toBeFocused()
    await expect(page.locator('.breadcrumbs strong')).toHaveText('Agenda')
    await expect(page.locator('meta[name="csrf-token"]')).toHaveAttribute('content', /.+/)
    await expect(page.locator('.sidebar nav').first().getByRole('button', { name: 'Agenda', exact: true })).toBeVisible()
    if (info.project.name === 'mobile') await page.getByRole('button', { name: 'Apri menu' }).click()
    await page.getByRole('button', { name: 'Archivi', exact: true }).click()
    await expect(page.getByRole('heading', { name: 'Archivi' })).toBeVisible()
    await page.getByRole('navigation', { name: 'Tipi di archivio' }).getByRole('button', { name: 'Articoli' }).click()
    await expect(page.locator('.archive-panel')).toBeVisible()
    const js = await context.request.get('/assets/centrochange_core/premium/app.js')
    const css = await context.request.get('/assets/centrochange_core/premium/app.css')
    expect(js.ok() && css.ok()).toBeTruthy()
    await page.screenshot({ path: info.outputPath('premium-live-archive.png'), fullPage: true })
  } finally { await context.close() }
})

test('UAT priority: live weekly grid, Professionals, report and manifest-owned demo labels', async ({ browser }, info) => {
  const context = await roleContext(browser, 'manager')
  try {
    const page = await context.newPage()
    await page.goto('/premium#Agenda')
    await expect(page.locator('.center-selector select')).toBeVisible()
    await page.locator('.center-selector select').selectOption(fixture.center_a)
    await expect(page.locator('.segmented button.selected')).toHaveText('Settimana')
    await expect(page.locator('.week-day')).toHaveCount(7)
    const alignment = await page.locator('.week-grid').evaluate(grid => {
      const header = [...grid.querySelectorAll('.week-day')].map(node => node.getBoundingClientRect())
      const cells = [...grid.querySelector('.week-row')!.querySelectorAll('.week-cell')].map(node => node.getBoundingClientRect())
      return { widths: header.map(rect => rect.width), drift: header.map((rect, i) => Math.abs(rect.left - cells[i].left)) }
    })
    expect(Math.max(...alignment.widths) - Math.min(...alignment.widths)).toBeLessThanOrEqual(0.75)
    expect(Math.max(...alignment.drift)).toBeLessThanOrEqual(0.75)
    await page.screenshot({ path: info.outputPath('uat-live-week.png'), fullPage: true })
    const nav = page.locator('.sidebar nav').first()
    const labels = await nav.locator('.nav-item span:first-of-type').allTextContents()
    expect(labels.indexOf('Professionisti')).toBe(labels.indexOf('Pazienti') + 1)
    await page.goto('/premium#Professionisti')
    await expect(page.getByRole('heading', { name: 'Professionisti', exact: true })).toBeVisible()
    await expect(page.locator('tbody')).toContainText('Professionista 1')
    await page.getByRole('searchbox', { name: 'Cerca professionisti' }).fill('Professionista 1')
    await expect(page.locator('tbody tr')).toHaveCount(1)
    await page.locator('tbody tr').first().click()
    await expect(page.getByRole('dialog')).toContainText('Professionista 1')
    await page.screenshot({ path: info.outputPath('uat-live-professionals.png'), fullPage: true })
    await page.goto('/premium#Pazienti')
    await expect(page.locator('tbody')).toContainText('Paziente 1')
    await page.getByRole('textbox', { name: 'Cerca pazienti' }).last().fill('Paziente 1')
    await expect(page.locator('tbody tr')).toHaveCount(1)
    await page.goto('/premium#Report')
    await page.getByRole('button', { name: 'Report professionisti' }).click()
    await page.getByLabel('Professionista report').selectOption({ label: 'Professionista 1' })
    await expect(page.getByRole('button', { name: 'Compensi e fatture autorizzati' })).toBeVisible()
    await page.screenshot({ path: info.outputPath('uat-live-professional-report.png'), fullPage: true })
  } finally { await context.close() }
})

test('UAT priority: secretariat professional report has no financial details', async ({ browser }) => {
  const context = await roleContext(browser, 'secretariat')
  try {
    const page = await context.newPage()
    await page.goto('/premium#Report')
    await expect(page.getByRole('heading', { name: 'Report' })).toBeVisible()
    await page.getByRole('button', { name: 'Report professionisti' }).click()
    await expect(page.getByRole('button', { name: 'Compensi e fatture autorizzati' })).toHaveCount(0)
    await expect(page.getByRole('button', { name: 'Finanza', exact: true })).toHaveCount(0)
  } finally { await context.close() }
})

test('all eleven live archives render a list or a genuine empty state', async ({ browser }, info) => {
  const context = await roleContext(browser, 'manager')
  try {
    const page = await context.newPage()
    await page.goto('/premium#Archivi')
    const selector = page.locator('.center-selector select')
    await expect(selector).toBeVisible()
    if (await selector.inputValue() !== fixture.center_a) await selector.selectOption(fixture.center_a)
    await expect(page.getByRole('navigation', { name: 'Tipi di archivio' })).toBeVisible()
    await selector.selectOption(fixture.center_a)
    await expect(page.getByRole('navigation', { name: 'Tipi di archivio' })).toBeVisible()
    await expect(page.getByRole('heading', { name: 'Archivi' })).toBeVisible()
    for (const label of ['Pazienti', 'Professionisti', 'Articoli', 'Tariffe', 'Tipi seduta',
      'Servizi del centro', 'Modelli pacchetto', 'Fatture pazienti', 'Fatture professionisti',
      'Pagamenti', 'Movimenti bancari']) {
      await page.getByRole('navigation', { name: 'Tipi di archivio' }).getByRole('button', { name: label, exact: true }).click()
      await expect(page.locator('.archive-panel h2')).toHaveText(label)
      await expect(page.locator('.archive-panel .panel-loading')).toHaveCount(0)
      await expect(page.locator('.archive-panel [role="alert"]')).toHaveCount(0)
      await expect(page.locator('.archive-panel tbody, .archive-panel .empty-state')).toBeVisible()
    }
    await page.screenshot({ path: info.outputPath('premium-live-eleven-archives.png'), fullPage: true })
  } finally { await context.close() }
})

test('eleven live detail cards open with authorized records', async ({ browser }, info) => {
  const context = await roleContext(browser, 'manager')
  try {
    const page = await context.newPage()
    await page.goto('/premium#Archivi')
    const selector = page.locator('.center-selector select')
    await expect(selector).toBeVisible()
    if (await selector.inputValue() !== fixture.center_a) await selector.selectOption(fixture.center_a)
    await expect(page.getByRole('navigation', { name: 'Tipi di archivio' })).toBeVisible()
    const labels = ['Pazienti', 'Professionisti', 'Articoli', 'Tariffe', 'Tipi seduta',
      'Servizi del centro', 'Modelli pacchetto', 'Fatture pazienti', 'Fatture professionisti',
      'Pagamenti', 'Movimenti bancari']
    for (const [index, label] of labels.entries()) {
      await page.getByRole('navigation', { name: 'Tipi di archivio' }).getByRole('button', { name: label, exact: true }).click()
      await expect(page.locator('.archive-panel h2')).toHaveText(label)
      const row = page.locator('.archive-panel tbody tr.clickable').first()
      await expect(row, `${label} must have a synthetic UAT record`).toBeVisible({ timeout: 15_000 })
      await row.click()
      const detail = page.getByRole('dialog')
      await expect(detail).toBeVisible()
      await expect(detail.getByRole('heading', { name: 'Dettaglio' })).toBeVisible()
      if (label === 'Pagamenti') {
        await expect(detail.getByText(/Incasso|Pagamento|Giroconto/).first()).toBeVisible()
        await expect(detail.getByText('Receive', { exact: true })).toHaveCount(0)
      }
      await page.screenshot({ path: info.outputPath(`detail-${String(index + 1).padStart(2, '0')}.png`), fullPage: true })
      await detail.getByRole('button', { name: 'Chiudi' }).click()
    }
  } finally { await context.close() }
})

test('principal live sections render without page overflow', async ({ browser }, info) => {
  const context = await roleContext(browser, 'manager')
  try {
    const page = await context.newPage()
    await page.goto('/premium#Agenda')
    const selector = page.locator('.center-selector select')
    await expect(selector).toBeVisible()
    if (await selector.inputValue() !== fixture.center_a) await selector.selectOption(fixture.center_a)
    const views = ['Agenda', 'Pazienti', 'Servizi', 'Disponibilità', 'Report',
      'Finanza', 'Archivi', 'Gestione accessi', 'Registro modifiche', 'Notifiche']
    for (const [index, view] of views.entries()) {
      const response = await page.goto('/premium#' + encodeURIComponent(view))
      if (response) expect(response.ok(), `${view} route`).toBeTruthy()
      await expect(page.locator('.breadcrumbs strong')).toHaveText(view)
      await expect(page.locator('main')).toBeVisible()
      await expect(page.locator('main [role="alert"].error')).toHaveCount(0)
      if (view === 'Finanza') {
        await expect(page.locator('.scope-note')).toContainText('date di registrazione')
        await expect(page.locator('.scope-note')).not.toContainText('Posting')
      }
      const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth)
      expect(overflow, `${view} horizontal overflow`).toBeLessThanOrEqual(2)
      await page.screenshot({ path: info.outputPath(`section-${String(index + 1).padStart(2, '0')}.png`), fullPage: true })
    }
  } finally { await context.close() }
})

test('financial drill-down keeps labels and status in Italian', async ({ browser }, info) => {
  const context = await roleContext(browser, 'manager')
  try {
    const page = await context.newPage()
    await page.goto('/premium#Finanza')
    const selector = page.locator('.center-selector select')
    await expect(selector).toBeVisible()
    if (await selector.inputValue() !== fixture.center_a) await selector.selectOption(fixture.center_a)
    await page.getByRole('tab', { name: 'Fatture pazienti', exact: true }).click()
    const row = page.locator('.finance-panel tbody tr.clickable').first()
    await expect(row).toBeVisible()
    await row.click()
    const detail = page.getByRole('dialog')
    await expect(detail).toBeVisible()
    await expect(detail.locator('dt').filter({ hasText: 'Data registrazione' })).toBeVisible()
    await expect(detail.locator('dt').filter({ hasText: 'Codice' })).toBeVisible()
    await expect(detail.locator('dt').filter({ hasText: 'posting date' })).toHaveCount(0)
    await expect(page.getByText('Workspace', { exact: true })).toHaveCount(0)
    await page.screenshot({ path: info.outputPath('finance-detail-it.png'), fullPage: true })
  } finally { await context.close() }
})

test('seven identities and Guest: scoped API, cross-center, native access', async ({ browser }) => {
  for (const role of names) {
    const context = await roleContext(browser, role)
    try {
      const response = await context.request.get(endpoint('catalog.records'), {
        params: { center: fixture.center_a, kind: 'Item', limit: 1 } })
      if (role === 'manager') expect(response.ok(), `catalog ${role}`).toBeTruthy()
      else denied(response)
      const cross = await context.request.get(endpoint('catalog.records'), {
        params: { center: fixture.center_b, kind: 'Item', limit: 1 } })
      // A user may belong to both centers; record-level denial is checked below.
      if (role !== 'manager') denied(cross)
      const profile = await context.request.get(endpoint('operations.profiles.patients'), {
        params: { center: fixture.center_a, limit: 1 } })
      if (role === 'manager' || role === 'secretariat' || role.startsWith('professional_'))
        expect(profile.ok(), `profiles ${role}`).toBeTruthy()
      else {
        expect(profile.ok(), `profiles ${role}`).toBeTruthy()
        expect((await profile.json()).message.rows).toEqual([])
      }
      const finance = await context.request.get(endpoint('finance.payments.detail'), {
        params: { center: fixture.center_a, name: fixture.payment_a } })
      if (['manager', 'secretariat', 'finance', 'accountant'].includes(role))
        expect(finance.ok(), `payments ${role}`).toBeTruthy()
      else denied(finance)
    } finally { await context.close() }
  }
  const guest = await browser.newContext()
  try {
    denied(await guest.request.get(endpoint('catalog.records'), { params: { center: fixture.center_a, kind: 'Item' } }))
    denied(await guest.request.get(endpoint('finance.payments.detail'), { params: { center: fixture.center_a, name: fixture.payment_a } }))
  } finally { await guest.close() }
})

test('manager write: CSRF, field whitelist, replay, audit and center boundary', async ({ browser }) => {
  const context = await roleContext(browser, 'manager')
  try {
    const page = await context.newPage()
    await page.goto('/premium')
    const csrf = await page.locator('meta[name="csrf-token"]').getAttribute('content')
    expect(csrf).toBeTruthy()
    const detail = await context.request.get(endpoint('catalog.detail'), {
      params: { center: fixture.owned_write.center, kind: 'Item', name: fixture.owned_write.item } })
    expect(detail.ok()).toBeTruthy()
    const item = (await detail.json()).message
    expect(item.modified && item.item_name).toBeTruthy()
    const key = `live-cc148-${crypto.randomUUID()}`
    const body = { center: fixture.owned_write.center, name: fixture.owned_write.item, item_name: item.item_name,
      expected_version: item.modified, request_key: key, reason: 'Collaudo sintetico #148' }
    denied(await context.request.post(endpoint('catalog.item_save'), { data: body }))
    denied(await context.request.post(endpoint('catalog.item_save'), {
      data: { ...body, disabled: 0 }, headers: { 'X-Frappe-CSRF-Token': csrf! } }))
    const write = await context.request.post(endpoint('catalog.item_save'), {
      data: body, headers: { 'X-Frappe-CSRF-Token': csrf! } })
    expect(write.ok()).toBeTruthy()
    expect((await write.json()).message.replay).toBe(false)
    const replay = await context.request.post(endpoint('catalog.item_save'), {
      data: body, headers: { 'X-Frappe-CSRF-Token': csrf! } })
    expect(replay.ok()).toBeTruthy()
    expect((await replay.json()).message.replay).toBe(true)
    denied(await context.request.post(endpoint('catalog.item_save'), {
      data: { ...body, item_name: item.item_name + ' alterato' }, headers: { 'X-Frappe-CSRF-Token': csrf! } }))
    denied(await context.request.get(endpoint('catalog.detail'), {
      params: { center: fixture.center_b, kind: 'Item', name: fixture.owned_write.item } }))
    // Frappe audit filters are local calendar days; UTC can already be yesterday in Rome.
    const today = new Intl.DateTimeFormat('sv-SE', { timeZone: 'Europe/Rome', year: 'numeric',
      month: '2-digit', day: '2-digit' }).format(new Date())
    const audit = await context.request.get(endpoint('security.audit_view.events'), {
      params: { start: today, end: today, event_type: 'PREMIUM_MASTER_UPDATED', reference: fixture.owned_write.item } })
    expect(audit.ok()).toBeTruthy()
    expect(JSON.stringify((await audit.json()).message)).toContain(fixture.owned_write.item)
  } finally { await context.close() }
})

test('print is scoped; Payment Entry stays read-only', async ({ browser }) => {
  const context = await roleContext(browser, 'finance')
  try {
    const good = await context.request.get(endpoint('finance.documents.preview'), {
      params: { center: fixture.center_a, doctype: 'Sales Invoice', name: fixture.invoice_a } })
    expect(good.ok()).toBeTruthy()
    expect((await good.json()).message.html).toContain('<')
    denied(await context.request.get(endpoint('finance.documents.preview'), {
      params: { center: fixture.center_b, doctype: 'Sales Invoice', name: fixture.invoice_a } }))
    denied(await context.request.get(endpoint('finance.documents.preview'), {
      params: { center: fixture.center_a, doctype: 'Sales Invoice', name: fixture.invoice_a, print_format: 'NotApproved' } }))
    denied(await context.request.post(endpoint('finance.payments.records'), {
      data: { center: fixture.center_a } }))
  } finally { await context.close() }
})

test('invalid parameters fail and catalog latency is recorded', async ({ browser }) => {
  const context = await roleContext(browser, 'manager')
  try {
    denied(await context.request.get(endpoint('catalog.records'), {
      params: { center: fixture.center_a, kind: 'Item', limit: 101 } }))
    denied(await context.request.get(endpoint('catalog.records'), {
      params: { center: fixture.center_a, kind: 'User' } }))
    denied(await context.request.get(endpoint('finance.payments.records'), {
      params: { center: fixture.center_a, start: '2020-01-01', end: '2026-12-31' } }))
    const times: number[] = []
    for (let i = 0; i < 10; i++) {
      const start = performance.now()
      const response = await context.request.get(endpoint('catalog.records'), {
        params: { center: fixture.center_a, kind: 'Item', limit: 10 } })
      expect(response.ok()).toBeTruthy()
      times.push(performance.now() - start)
    }
    times.sort((a, b) => a - b)
    console.log(JSON.stringify({ metric: 'catalog.records', samples: times.length,
      p50_ms: Math.round(times[4]), p95_ms: Math.round(times[9]) }))
  } finally { await context.close() }
})
