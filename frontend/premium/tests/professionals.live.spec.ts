/** AUDIT-05: real Frappe/MariaDB against an owned disposable clone. No mocks. */
import { expect, test, type Browser, type BrowserContext } from '@playwright/test'
import { readFileSync, statSync } from 'node:fs'
import { resolve } from 'node:path'

type Role = 'manager' | 'secretariat' | 'professional_a' | 'professional_b' | 'professional_c' | 'finance' | 'accountant'
type Fixture = { synthetic_only: true; tag: string; center_a: string; center_b: string;
  practitioner_a: string; practitioner_b: string; patient_a: string; roles: Record<Role, string> }
const fixturePath = process.env.CC_PROFESSIONALS_ISOLATED_FIXTURE
if (!fixturePath || process.env.CC_PROFESSIONALS_ISOLATED !== 'YES') throw new Error('Private AUDIT-05 clone fixture required')
const repo = resolve(process.cwd(), '../..')
function privateFile(value: string) {
  const file = resolve(value)
  if (file === repo || file.startsWith(repo + '/') || statSync(file).mode & 0o077)
    throw new Error('Fixture/session must be private and outside Git')
  return file
}
const fixture = JSON.parse(readFileSync(privateFile(fixturePath), 'utf8')) as Fixture
const roles: Role[] = ['manager', 'secretariat', 'professional_a', 'professional_b', 'professional_c', 'finance', 'accountant']
if (fixture.synthetic_only !== true || !/^CC-HTTP-[A-Za-z0-9]{10}$/.test(fixture.tag) ||
    !fixture.center_a || !fixture.center_b || fixture.center_a === fixture.center_b ||
    !fixture.practitioner_a || !fixture.practitioner_b || !fixture.patient_a || roles.some(role => !fixture.roles[role]))
  throw new Error('AUDIT-05 fixture inventory incomplete')
for (const role of roles) privateFile(fixture.roles[role])
const method = (name: string) => '/api/method/centrochange_core.' + name
const ctxFor = (browser: Browser, role: Role) => browser.newContext({ storageState: fixture.roles[role] })
async function api(ctx: BrowserContext, name: string, args: Record<string, string>) {
  const response = await ctx.request.get(name.startsWith('frappe.') ? '/api/method/' + name : method(name), { params: args })
  return { response, body: await response.json().catch(() => ({})) }
}

test('Professionisti: ricerca reale, scheda, refresh e resa responsive', async ({ browser }, info) => {
  const ctx = await ctxFor(browser, 'manager')
  try {
    const detail = await api(ctx, 'operations.profiles.practitioner_detail', { center: fixture.center_a, name: fixture.practitioner_a })
    expect(detail.response.ok()).toBeTruthy()
    const canonicalName = String(detail.body.message?.practitioner_name ?? '')
    expect(canonicalName).toBeTruthy()
    const page = await ctx.newPage()
    await page.goto('/premium/#Professionisti')
    await page.getByRole('combobox', { name: 'Centro' }).selectOption(fixture.center_a)
    await page.getByRole('searchbox', { name: 'Cerca professionisti' }).fill(String(detail.body.message.first_name))
    await expect(page.locator('tbody')).toContainText('Professionista di prova A')
    await expect(page.locator('tbody')).not.toContainText(canonicalName)
    await page.screenshot({ path: info.outputPath(`professionisti-live-list-${info.project.name}.png`) })
    const row = page.locator('tbody tr').filter({ hasText: 'Professionista di prova A' }).first()
    await row.click()
    const drawer = page.getByRole('dialog')
    await expect(drawer).toContainText('Professionista di prova A')
    await expect(drawer.getByRole('heading', { name: 'Scheda professionista' })).toBeVisible()
    await expect(drawer).not.toContainText(String(detail.body.message.first_name))
    await expect(drawer).toContainText('Centro:')
    await page.screenshot({ path: info.outputPath(`professionisti-live-detail-${info.project.name}.png`) })
    await page.reload()
    await expect(page.getByRole('heading', { name: 'Professionisti', exact: true })).toBeVisible()
    expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(page.viewportSize()!.width)
  } finally { await ctx.close() }
})

test('Sette ruoli più Guest: ricerca, dettaglio proprio, IDOR, centro A/B', async ({ browser }, info) => {
  test.skip(info.project.name !== 'desktop')
  for (const role of roles) {
    const ctx = await ctxFor(browser, role)
    try {
      const list = await api(ctx, 'operations.profiles.practitioners', { center: fixture.center_a, search: fixture.tag })
      if (['manager', 'professional_a', 'professional_b', 'professional_c'].includes(role)) {
        expect(list.response.ok(), `${role} list`).toBeTruthy()
        const names = (list.body.message?.rows ?? []).map((row: { name: string }) => row.name)
        if (role === 'manager') expect(names).toContain(fixture.practitioner_a)
        else expect(names.every((name: string) => name === fixture.practitioner_a || name === fixture.practitioner_b)).toBeTruthy()
      } else expect(list.response.ok(), `${role} scoped list denied`).toBeFalsy()
      const own = await api(ctx, 'operations.profiles.practitioner_detail', { center: fixture.center_a, name: fixture.practitioner_a })
      const foreign = await api(ctx, 'operations.profiles.practitioner_detail', { center: fixture.center_b, name: fixture.practitioner_a })
      expect(foreign.response.ok(), `${role} cross-center detail`).toBeFalsy()
      expect(own.response.ok(), `${role} own detail`).toBe(role === 'manager' || role === 'professional_a')
      const direct = await api(ctx, 'frappe.client.get', { doctype: 'Healthcare Practitioner', name: fixture.practitioner_b })
      if (role !== 'manager' && role !== 'professional_b') expect(direct.response.ok(), `${role} direct practitioner IDOR`).toBeFalsy()
    } finally { await ctx.close() }
  }
  const guest = await browser.newContext()
  try {
    const result = await api(guest, 'operations.profiles.practitioners', { center: fixture.center_a })
    expect(result.response.ok()).toBeFalsy()
  } finally { await guest.close() }
})

test('Browser multiruolo: directory propria e nessun accesso ai ruoli finanziari', async ({ browser }, info) => {
  test.skip(info.project.name !== 'desktop')
  for (const role of roles) {
    const ctx = await ctxFor(browser, role)
    try {
      const page = await ctx.newPage()
      await page.goto('/premium/#Professionisti')
      if (role === 'finance' || role === 'accountant') {
        await expect(page.getByRole('heading', { name: 'Professionisti', exact: true })).toHaveCount(0)
        continue
      }
      await expect(page.getByRole('heading', { name: 'Professionisti', exact: true })).toBeVisible()
      await page.getByRole('combobox', { name: 'Centro' }).selectOption(fixture.center_a)
      if (role === 'professional_c') {
        await expect(page.getByText('Nessun professionista trovato nel centro.')).toBeVisible()
        continue
      }
      const expected = role === 'professional_b' ? 'Professionista di prova B' : 'Professionista di prova A'
      await expect(page.locator('tbody')).toContainText(expected)
      if (role === 'professional_a' || role === 'professional_b')
        await expect(page.locator('tbody')).not.toContainText(role === 'professional_a' ? 'Professionista di prova B' : 'Professionista di prova A')
    } finally { await ctx.close() }
  }
})

test('Archivio professionisti: elenco, dettaglio ed editor manager senza codici in lettura', async ({ browser }, info) => {
  test.skip(info.project.name !== 'desktop')
  const ctx = await ctxFor(browser, 'manager')
  try {
    const page = await ctx.newPage()
    await page.goto('/premium/#Archivi')
    await page.getByRole('combobox', { name: 'Centro' }).selectOption(fixture.center_a)
    await page.getByRole('navigation', { name: 'Tipi di archivio' }).getByRole('button', { name: 'Professionisti', exact: true }).click()
    await expect(page.locator('tbody')).toContainText('Professionista di prova A')
    await expect(page.locator('tbody')).not.toContainText(fixture.tag)
    await page.locator('tbody tr').filter({ hasText: 'Professionista di prova A' }).first().click()
    const drawer = page.getByRole('dialog')
    await expect(drawer.getByRole('heading', { name: 'Dettaglio' })).toBeVisible()
    await expect(drawer).not.toContainText(fixture.tag)
    await drawer.getByRole('button', { name: 'Modifica scheda' }).click()
    await expect(page.getByRole('dialog', { name: 'Modifica · Professionisti' })).toBeVisible()
    await expect(page.getByRole('textbox', { name: 'Motivo' })).toBeVisible()
  } finally { await ctx.close() }
})

test('Manager: archivio edit con motivo, versione, replay/stale e CSRF; altri negati', async ({ browser }, info) => {
  test.skip(info.project.name !== 'desktop')
  const manager = await ctxFor(browser, 'manager')
  try {
    const page = await manager.newPage()
    await page.goto('/premium/#Archivi')
    const csrf = await page.locator('meta[name="csrf-token"]').getAttribute('content')
    expect(csrf).toBeTruthy()
    const before = await api(manager, 'operations.profiles.practitioner_detail', { center: fixture.center_a, name: fixture.practitioner_a })
    expect(before.response.ok()).toBeTruthy()
    const source = before.body.message
    const payload = { center: fixture.center_a, name: fixture.practitioner_a, first_name: source.first_name,
      last_name: 'Professionista', expected_version: source.modified, request_key: fixture.tag + '-edit-1', reason: 'AUDIT-05 fixture isolata' }
    const post = async (data: Record<string, unknown>, token = csrf!) => {
      const response = await manager.request.post(method('operations.profiles.practitioner_save'), { data, headers: token ? { 'X-Frappe-CSRF-Token': token } : {} })
      return { response, body: await response.json().catch(() => ({})) }
    }
    const noCsrf = await post(payload, '')
    expect(noCsrf.response.ok()).toBeFalsy()
    const saved = await post(payload)
    expect(saved.response.ok()).toBeTruthy()
    expect(saved.body.message.replay).toBe(false)
    const repeated = await post(payload)
    expect(repeated.response.ok()).toBeTruthy()
    expect(repeated.body.message.replay).toBe(true)
    const day = new Intl.DateTimeFormat('en-CA', { timeZone: 'Europe/Rome', year: 'numeric', month: '2-digit', day: '2-digit' }).format(new Date())
    const audit = await api(manager, 'security.audit_view.events', { start: day, end: day, event_type: 'PREMIUM_MASTER_UPDATED', reference: fixture.practitioner_a })
    expect(audit.response.ok()).toBeTruthy()
    const edits = (audit.body.message?.events ?? []).filter((event: { reason: string }) => event.reason === 'AUDIT-05 fixture isolata')
    expect(edits).toHaveLength(1)
    expect(edits[0].actor).toBeTruthy()
    const stale = await post({ ...payload, request_key: fixture.tag + '-edit-stale' })
    expect(stale.response.ok()).toBeFalsy()
    const after = await api(manager, 'operations.profiles.practitioner_detail', { center: fixture.center_a, name: fixture.practitioner_a })
    expect(after.body.message.last_name).toBe(payload.last_name)
    expect(after.body.message.user_id).toBe(source.user_id)
    const forbidden = await post({ ...payload, request_key: fixture.tag + '-extra', supplier: 'NO' })
    expect(forbidden.response.ok()).toBeFalsy()
    for (const role of ['secretariat', 'professional_a', 'finance', 'accountant'] as Role[]) {
      const ctx = await ctxFor(browser, role)
      try {
        const rolePage = await ctx.newPage()
        await rolePage.goto('/premium/')
        const roleCsrf = await rolePage.locator('meta[name="csrf-token"]').getAttribute('content')
        expect(roleCsrf).toBeTruthy()
        const attempt = await ctx.request.post(method('operations.profiles.practitioner_save'), { data: { ...payload, request_key: fixture.tag + '-' + role }, headers: { 'X-Frappe-CSRF-Token': roleCsrf! } })
        expect(attempt.ok(), `${role} write denied`).toBeFalsy()
      } finally { await ctx.close() }
    }
  } finally { await manager.close() }
})
