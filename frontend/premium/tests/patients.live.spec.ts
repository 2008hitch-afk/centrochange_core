/** AUDIT-04: real Frappe/MariaDB on an identified disposable clone. No mocks. */
import { expect, test, type Browser, type BrowserContext } from '@playwright/test'
import { readFileSync, statSync } from 'node:fs'
import { resolve } from 'node:path'

type Role = 'manager' | 'secretariat' | 'professional_a' | 'professional_b' | 'professional_c' | 'finance' | 'accountant'
type Fixture = { synthetic_only: true; tag: string; center_a: string; center_b: string;
  patient_a: string; patient_b: string; patient_mvp: string; patient_real: string; practitioner_a: string; practitioner_b: string;
  template: string; package: string; appointment_type: string; manager_second: string; roles: Record<Role, string> }
const path = process.env.CC_PATIENTS_ISOLATED_FIXTURE
if (!path || process.env.CC_PATIENTS_ISOLATED !== 'YES') throw new Error('Private AUDIT-04 clone fixture required')
const repo = resolve(process.cwd(), '../..')
function privateFile(value: string) {
  const file = resolve(value)
  if (file === repo || file.startsWith(repo + '/') || statSync(file).mode & 0o077)
    throw new Error('Fixture/session must be private and outside Git')
  return file
}
const fixture = JSON.parse(readFileSync(privateFile(path), 'utf8')) as Fixture
const roles: Role[] = ['manager', 'secretariat', 'professional_a', 'professional_b', 'professional_c', 'finance', 'accountant']
if (fixture.synthetic_only !== true || !/^CC-HTTP-[A-Za-z0-9]{10}$/.test(fixture.tag) ||
    !fixture.center_a || !fixture.center_b || fixture.center_a === fixture.center_b ||
    !fixture.patient_a || !fixture.patient_b || !/^CC-MVP-POS-/.test(fixture.patient_mvp) || !/^CC-MVP-POS-/.test(fixture.patient_real) || !fixture.template || !fixture.package ||
    !fixture.appointment_type || !fixture.manager_second || roles.some(role => !fixture.roles[role]))
  throw new Error('AUDIT-04 fixture inventory incomplete')
for (const role of roles) privateFile(fixture.roles[role])
privateFile(fixture.manager_second)
const method = (name: string) => '/api/method/centrochange_core.' + name
async function context(browser: Browser, role: Role) { return browser.newContext({ storageState: fixture.roles[role] }) }
async function csrf(page: { locator: (selector: string) => { getAttribute: (name: string) => Promise<string | null> } }) {
  const token = await page.locator('meta[name="csrf-token"]').getAttribute('content')
  expect(token).toBeTruthy()
  return token!
}
async function get(ctx: BrowserContext, name: string, args: Record<string, string>) {
  const response = await ctx.request.get(name.startsWith('frappe.') ? '/api/method/' + name : method(name), { params: args })
  return { response, body: await response.json().catch(() => ({})) }
}
async function post(ctx: BrowserContext, token: string, name: string, args: Record<string, unknown>) {
  const response = await ctx.request.post(method(name), { data: args, headers: { 'X-Frappe-CSRF-Token': token } })
  return { response, body: await response.json().catch(() => ({})) }
}

test('UX-04 live isolato: nome Patient reale, fallback onesto, ricerca contestuale e centro A/B', async ({ browser }, info) => {
  const ctx = await context(browser, 'manager')
  try {
    const detail = await get(ctx, 'operations.profiles.patient_detail', { center: fixture.center_a, name: fixture.patient_real })
    expect(detail.response.ok()).toBeTruthy()
    const displayName = `${detail.body.message.first_name} ${detail.body.message.last_name}`.trim()
    expect(displayName).not.toMatch(/^CC-/i)
    const firstName = String(detail.body.message.first_name)
    const boot = await get(ctx, 'operations.workspace.bootstrap', { center: fixture.center_a })
    expect(boot.response.ok()).toBeTruthy()
    const own = (boot.body.message?.patients ?? []).find((row: { name: string }) => row.name === fixture.patient_real)
    expect(own).toMatchObject({ first_name: detail.body.message.first_name, last_name: detail.body.message.last_name })
    const searched = await get(ctx, 'operations.workspace.patient_search', { center: fixture.center_a, query: firstName })
    expect(searched.response.ok()).toBeTruthy()
    expect((searched.body.message?.patients ?? []).map((row: { name: string }) => row.name)).toContain(fixture.patient_real)
    const foreign = await get(ctx, 'operations.workspace.patient_search', { center: fixture.center_b, query: firstName })
    expect(foreign.response.ok()).toBeTruthy()
    expect((foreign.body.message?.patients ?? []).map((row: { name: string }) => row.name)).not.toContain(fixture.patient_real)

    const page = await ctx.newPage()
    await page.goto('/premium/#Pazienti')
    await page.getByRole('combobox', { name: 'Centro' }).selectOption(fixture.center_a)
    await expect(page.getByRole('combobox', { name: 'Ricerca globale pazienti' })).toHaveCount(0)
    await page.getByRole('textbox', { name: 'Cerca pazienti' }).fill(firstName)
    await expect(page.locator('tbody')).toContainText(displayName)
    await expect(page.locator('tbody')).not.toContainText(fixture.patient_real)
    await page.locator('tbody tr').first().click()
    const drawer = page.getByRole('dialog', { name: displayName })
    await expect(drawer.getByRole('heading', { name: displayName })).toHaveCount(1)
    await expect(drawer.getByRole('heading', { name: 'Anagrafica' })).toBeVisible()
    await expect(drawer).not.toContainText(fixture.patient_real)
    await page.screenshot({ path: info.outputPath(`ux-04-live-patient-${info.project.name}.png`), fullPage: true })
    await drawer.getByRole('button', { name: 'Chiudi' }).click()
    await page.getByRole('combobox', { name: 'Centro' }).selectOption(fixture.center_b)
    await page.getByRole('textbox', { name: 'Cerca pazienti' }).fill(fixture.tag)
    await expect(page.locator('tbody')).toContainText('Anagrafica da completare · scheda')
    await expect(page.locator('tbody')).not.toContainText(fixture.patient_b)
    await page.screenshot({ path: info.outputPath(`ux-04-live-fallback-${info.project.name}.png`), fullPage: true })
    expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(page.viewportSize()!.width)
  } finally { await ctx.close() }
})

test('UX-04 live isolato: nuova proiezione Patient non allarga ruoli o accesso diretto', async ({ browser }, info) => {
  test.skip(info.project.name !== 'desktop')
  for (const role of roles) {
    const ctx = await context(browser, role)
    try {
      const list = await get(ctx, 'operations.workspace.patient_search', { center: fixture.center_a, query: fixture.patient_a })
      if (list.response.ok()) {
        const rows = list.body.message?.patients ?? []
        expect(rows.every((row: { name: string }) => row.name === fixture.patient_a)).toBeTruthy()
      }
      const idor = await get(ctx, 'operations.profiles.patient_detail', { center: fixture.center_b, name: fixture.patient_a })
      expect(idor.response.ok(), `${role} must not access A Patient in B`).toBeFalsy()
      expect(JSON.stringify(idor.body)).not.toContain(fixture.patient_a)
    } finally { await ctx.close() }
  }
  const guest = await browser.newContext()
  try {
    const list = await get(guest, 'operations.workspace.patient_search', { center: fixture.center_a, query: fixture.patient_a })
    expect(list.response.ok()).toBeFalsy()
  } finally { await guest.close() }
})

test('UX-04 live isolato: CC-MVP-POS incompleto resta distinguibile dopo refresh; Agenda proietta solo sedute autorizzate', async ({ browser }, info) => {
  test.skip(info.project.name !== 'desktop')
  const manager = await context(browser, 'manager')
  try {
    const page = await manager.newPage()
    await page.goto('/premium/#Pazienti')
    const token = await csrf(page)
    await page.getByRole('combobox', { name: 'Centro' }).selectOption(fixture.center_a)
    await page.getByRole('textbox', { name: 'Cerca pazienti' }).fill(fixture.patient_mvp)
    await expect(page.locator('tbody')).toContainText('Anagrafica da completare · scheda')
    await expect(page.locator('tbody')).not.toContainText(fixture.patient_mvp)
    const before = await page.locator('tbody tr').first().innerText()
    await page.reload()
    await page.getByRole('combobox', { name: 'Centro' }).selectOption(fixture.center_a)
    await page.getByRole('textbox', { name: 'Cerca pazienti' }).fill(fixture.patient_mvp)
    await expect(page.locator('tbody tr').first()).toHaveText(before)
    await page.screenshot({ path: info.outputPath('ux-04-live-mvp-fallback-desktop.png'), fullPage: true })
    const foreign = await get(manager, 'operations.workspace.patient_search', { center: fixture.center_b, query: fixture.patient_mvp })
    expect(foreign.response.ok()).toBeTruthy()
    expect((foreign.body.message?.patients ?? []).map((row: { name: string }) => row.name)).not.toContain(fixture.patient_mvp)
    const booked = await post(manager, token, 'scheduling.booking.book', {
      patient: fixture.patient_mvp, practitioner: fixture.practitioner_a, center: fixture.center_a,
      appointment_type: fixture.appointment_type, appointment_date: '2099-01-12', appointment_time: '09:00:00',
      request_key: fixture.tag + '-ux04-mvp-agenda', reason: 'Seduta sintetica per proiezione Agenda' })
    expect(booked.response.ok()).toBeTruthy()
    for (const role of ['manager', 'secretariat', 'professional_a'] as Role[]) {
      const ctx = await context(browser, role)
      try {
        const agenda = await get(ctx, 'operations.workspace.agenda', { center: fixture.center_a, start: '2099-01-12', end: '2099-01-18' })
        expect(agenda.response.ok(), `${role} Agenda HTTP`).toBeTruthy()
        const row = (agenda.body.message?.appointments ?? []).find((item: { patient: string }) => item.patient === fixture.patient_mvp)
        expect(row, `${role} sees only assigned synthetic appointment`).toBeTruthy()
        expect(row.patient_first_name).toMatch(/^CC-MVP-POS-/)
        expect(row.patient_last_name).toBeFalsy()
        const denied = await get(ctx, 'operations.workspace.agenda', { center: fixture.center_b, start: '2099-01-12', end: '2099-01-18' })
        if (denied.response.ok()) expect((denied.body.message?.appointments ?? []).some((item: { patient: string }) => item.patient === fixture.patient_mvp)).toBeFalsy()
      } finally { await ctx.close() }
    }
  } finally { await manager.close() }
})

test('scheda Pazienti reale: ricerca, profilo, note, pacchetto e responsive', async ({ browser }, info) => {
  const ctx = await context(browser, 'manager')
  try {
    const page = await ctx.newPage()
    const shell = await page.goto('/premium/#Pazienti')
    expect(shell?.ok()).toBeTruthy()
    await expect(page.getByRole('heading', { name: 'Pazienti', exact: true })).toBeVisible()
    await page.getByRole('combobox', { name: 'Centro' }).selectOption(fixture.center_a)
    await page.getByRole('textbox', { name: 'Cerca pazienti' }).fill(fixture.tag + '-inesistente')
    await expect(page.getByText('Nessun paziente trovato')).toBeVisible()
    await page.getByRole('textbox', { name: 'Cerca pazienti' }).fill(fixture.patient_a)
    await expect(page.locator('tbody tr')).toHaveCount(1)
    await page.locator('tbody tr').first().click()
    const drawer = page.getByRole('dialog')
    await expect(drawer.getByRole('heading', { level: 2 })).toHaveCount(1)
    await expect(drawer.getByRole('heading', { name: 'Anagrafica' })).toBeVisible()
    await expect(drawer.getByRole('heading', { name: 'Note organizzative' })).toBeVisible()
    await expect(drawer.getByRole('heading', { name: 'Pacchetti' })).toBeVisible()
    await expect(drawer.getByRole('heading', { name: 'Professionisti assegnati' })).toBeVisible()
    await page.screenshot({ path: info.outputPath(`patients-live-${info.project.name}.png`), fullPage: true })
    expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(page.viewportSize()!.width)
  } finally { await ctx.close() }
})

test('sette ruoli più Guest: endpoint, IDOR e centro A/B reali', async ({ browser }, info) => {
  test.skip(info.project.name !== 'desktop')
  const results: Record<string, { own: number; foreign: number }> = {}
  for (const role of roles) {
    const ctx = await context(browser, role)
    try {
      const own = await get(ctx, 'operations.profiles.patient_detail', { center: fixture.center_a, name: fixture.patient_a })
      const foreign = await get(ctx, 'operations.profiles.patient_detail', { center: fixture.center_b, name: fixture.patient_a })
      results[role] = { own: own.response.status(), foreign: foreign.response.status() }
      expect(foreign.response.ok(), `${role} must not read A patient in B context`).toBeFalsy()
      expect(JSON.stringify(foreign.body)).not.toContain('SYNTHETIC PRIVATE BODY')
      expect(own.response.ok()).toBe(['manager', 'secretariat', 'professional_a'].includes(role))
      const search = await get(ctx, 'operations.workspace.patient_search', { center: fixture.center_b, query: fixture.tag })
      if (role === 'manager') {
        expect(search.response.ok()).toBeTruthy()
        expect((search.body.message?.patients ?? []).map((row: { name: string }) => row.name)).not.toContain(fixture.patient_a)
      }
    } finally { await ctx.close() }
  }
  const guest = await browser.newContext()
  try {
    const response = await get(guest, 'operations.profiles.patient_detail', { center: fixture.center_a, name: fixture.patient_a })
    expect(response.response.ok()).toBeFalsy()
  } finally { await guest.close() }
  expect(Object.keys(results)).toHaveLength(7)
})

test('Manager: salvataggio versionato, CSRF e riassegnazione stale fail closed', async ({ browser }, info) => {
  test.skip(info.project.name !== 'desktop')
  const ctx = await context(browser, 'manager')
  try {
    const page = await ctx.newPage()
    await page.goto('/premium/#Pazienti')
    const token = await csrf(page)
    const detail = await get(ctx, 'operations.profiles.patient_detail', { center: fixture.center_a, name: fixture.patient_a })
    expect(detail.response.ok()).toBeTruthy()
    const record = detail.body.message
    const noCsrf = await ctx.request.post(method('operations.profiles.patient_save'), { data: { center: fixture.center_a, name: fixture.patient_a, first_name: record.first_name, last_name: record.last_name, email: record.email, expected_version: record.modified, request_key: fixture.tag + '-no-csrf', reason: 'Prova sintetica' } })
    expect(noCsrf.ok()).toBeFalsy()
    const unique = Date.now().toString(36) + Math.random().toString(36).slice(2, 6)
    const key = fixture.tag + '-profile-' + unique
    const email = `paziente-${unique}@example.invalid`
    const args = { center: fixture.center_a, name: fixture.patient_a, first_name: 'Paziente prova', last_name: 'Sintetico', email, expected_version: record.modified, request_key: key, reason: 'Correzione anagrafica sintetica' }
    const saved = await post(ctx, token, 'operations.profiles.patient_save', args)
    expect(saved.response.ok()).toBeTruthy()
    const replay = await post(ctx, token, 'operations.profiles.patient_save', args)
    expect(replay.response.ok()).toBeTruthy()
    expect(replay.body.message.modified).toBe(saved.body.message.modified)
    const stale = await post(ctx, token, 'operations.profiles.patient_save', { ...args, request_key: key + '-stale' })
    expect(stale.response.ok()).toBeFalsy()
    const after = await get(ctx, 'operations.profiles.patient_detail', { center: fixture.center_a, name: fixture.patient_a })
    expect(after.body.message.email).toBe(email)
    const old = fixture.practitioner_b
    const next = fixture.practitioner_a
    const wrong = await post(ctx, token, 'security.lifecycle.reassign', { patient: fixture.patient_a, center: fixture.center_a, old_practitioner: old, new_practitioner: next, reason: 'Old non attivo' })
    expect(wrong.response.ok()).toBeFalsy()
    const stillAssigned = await get(ctx, 'operations.workspace.patient_history', { patient: fixture.patient_a, center: fixture.center_a })
    expect(stillAssigned.response.ok()).toBeTruthy()
  } finally { await ctx.close() }
})

test('note private: solo professionista assegnato, versioni append-only e revoca', async ({ browser }, info) => {
  test.skip(info.project.name !== 'desktop')
  const pro = await context(browser, 'professional_a')
  const manager = await context(browser, 'manager')
  try {
    const page = await pro.newPage()
    await page.goto('/premium/#Pazienti')
    const token = await csrf(page)
    const note = await post(pro, token, 'operations.notes.add_note', { patient: fixture.patient_a, center: fixture.center_a, content: fixture.tag + ' PRIVATE NOTE', private: 1 })
    expect(note.response.ok()).toBeTruthy()
    const correction = await post(pro, token, 'operations.notes.add_note', { patient: fixture.patient_a, center: fixture.center_a, content: fixture.tag + ' PRIVATE CORRECTION', private: 1, corrects: note.body.message.name })
    expect(correction.response.ok()).toBeTruthy()
    const own = await get(pro, 'operations.workspace.patient_history', { patient: fixture.patient_a, center: fixture.center_a })
    expect(own.response.ok()).toBeTruthy()
    expect(own.body.message.private_notes.some((row: { name: string }) => row.name === correction.body.message.name)).toBeTruthy()
    const managed = await get(manager, 'operations.workspace.patient_history', { patient: fixture.patient_a, center: fixture.center_a })
    expect(managed.response.ok()).toBeTruthy()
    expect(JSON.stringify(managed.body)).not.toContain('PRIVATE CORRECTION')
    const direct = await get(manager, 'frappe.client.get_list', { doctype: 'CC Private Note', fields: '["name","content"]' })
    expect(direct.response.ok()).toBeFalsy()
    const record = await get(manager, 'frappe.client.get', { doctype: 'CC Private Note', name: note.body.message.name })
    expect(record.response.ok()).toBeFalsy()
    expect(JSON.stringify(record.body)).not.toContain('PRIVATE CORRECTION')
    const exportAttempt = await manager.request.get('/api/method/frappe.desk.reportview.export_query', {
      params: { doctype: 'CC Private Note', file_format_type: 'CSV',
        fields: '["CC Private Note","name"],["CC Private Note","content"]', filters: '[]' } })
    expect(exportAttempt.ok()).toBeFalsy()
    expect(await exportAttempt.text()).not.toContain('PRIVATE CORRECTION')
  } finally { await pro.close(); await manager.close() }
})

test('pacchetti: chiave replay, nuova emissione, rettifica e saldo reale', async ({ browser }, info) => {
  test.skip(info.project.name !== 'desktop')
  const ctx = await context(browser, 'manager')
  const secondManager = await browser.newContext({ storageState: fixture.manager_second })
  try {
    const page = await ctx.newPage()
    await page.goto('/premium/#Pazienti')
    const token = await csrf(page)
    const secondPage = await secondManager.newPage()
    await secondPage.goto('/premium/#Pazienti')
    const secondToken = await csrf(secondPage)
    const issueArgs = { template: fixture.template, patient: fixture.patient_a, centers: [fixture.center_a], practitioner: fixture.practitioner_a, reason: 'Emissione sintetica', request_key: fixture.tag + '-issue-a' }
    const first = await post(ctx, token, 'operations.packages.issue', issueArgs)
    expect(first.response.ok()).toBeTruthy()
    const replay = await post(ctx, token, 'operations.packages.issue', issueArgs)
    expect(replay.response.ok()).toBeTruthy()
    expect(replay.body.message.name).toBe(first.body.message.name)
    const second = await post(ctx, token, 'operations.packages.issue', { ...issueArgs, request_key: fixture.tag + '-issue-b' })
    expect(second.response.ok()).toBeTruthy()
    expect(second.body.message.name).not.toBe(first.body.message.name)
    const packageFilter = JSON.stringify({ patient: fixture.patient_a, template: fixture.template })
    const beforeConcurrent = await get(ctx, 'frappe.client.get_list', {
      doctype: 'CC Patient Package', fields: '["name"]', filters: packageFilter, limit_page_length: '1000' })
    expect(beforeConcurrent.response.ok()).toBeTruthy()
    const beforeNames = new Set((beforeConcurrent.body.message as { name: string }[]).map(row => row.name))
    const concurrentArgs = { ...issueArgs, request_key: fixture.tag + '-concurrent-' + Date.now().toString(36) }
    const [parallelA, parallelB] = await Promise.all([
      post(ctx, token, 'operations.packages.issue', concurrentArgs),
      post(secondManager, secondToken, 'operations.packages.issue', concurrentArgs),
    ])
    expect(parallelA.response.ok() && parallelB.response.ok(),
      `concurrent HTTP ${parallelA.response.status()}/${parallelB.response.status()} types ${parallelA.body.exc_type ?? '-'} / ${parallelB.body.exc_type ?? '-'}`).toBeTruthy()
    expect(parallelA.body.message.name).toBe(parallelB.body.message.name)
    const concurrentPackage = parallelA.body.message.name as string
    const afterConcurrent = await get(ctx, 'frappe.client.get_list', {
      doctype: 'CC Patient Package', fields: '["name"]', filters: packageFilter, limit_page_length: '1000' })
    expect(afterConcurrent.response.ok()).toBeTruthy()
    expect((afterConcurrent.body.message as { name: string }[]).map(row => row.name).filter(name => !beforeNames.has(name))).toEqual([concurrentPackage])
    const grant = await get(ctx, 'frappe.client.get_list', {
      doctype: 'CC Package Ledger', fields: '["name"]',
      filters: JSON.stringify({ package: concurrentPackage, event_type: 'GRANT' }) })
    const audit = await get(ctx, 'frappe.client.get_list', {
      doctype: 'CC Audit Event', fields: '["name"]',
      filters: JSON.stringify({ reference_doctype: 'CC Patient Package', reference_name: concurrentPackage, event_type: 'PACKAGE_ISSUED' }) })
    expect(grant.response.ok() && audit.response.ok()).toBeTruthy()
    expect(grant.body.message).toHaveLength(1)
    expect(audit.body.message).toHaveLength(1)
    const packageName = first.body.message.name
    const adjustArgs = { package: packageName, units: 1, reason: 'Rettifica sintetica', request_key: fixture.tag + '-adjust' }
    const adjust = await post(ctx, token, 'operations.packages.adjust', adjustArgs)
    expect(adjust.response.ok()).toBeTruthy()
    const again = await post(ctx, token, 'operations.packages.adjust', adjustArgs)
    expect(again.body.message.event).toBe(adjust.body.message.event)
    const balance = await get(ctx, 'operations.packages.balance', { package: packageName, center: fixture.center_a })
    expect(balance.response.ok()).toBeTruthy()
    expect(balance.body.message.remaining).toBe(adjust.body.message.remaining)
    const overdraw = await post(ctx, token, 'operations.packages.adjust', { ...adjustArgs, units: -9999, request_key: fixture.tag + '-overdraw' })
    expect(overdraw.response.ok()).toBeFalsy()
  } finally { await ctx.close(); await secondManager.close() }
})

test('browser reale: form paziente, validazione, nota e persistenza', async ({ browser }, info) => {
  test.skip(info.project.name !== 'desktop')
  const ctx = await context(browser, 'manager')
  try {
    const page = await ctx.newPage()
    await page.goto('/premium/#Pazienti')
    await page.getByRole('combobox', { name: 'Centro' }).selectOption(fixture.center_a)
    await page.getByRole('textbox', { name: 'Cerca pazienti' }).fill(fixture.patient_a)
    await expect(page.locator('tbody tr')).toHaveCount(1)
    await page.locator('tbody tr').click()
    const drawer = page.getByRole('dialog')
    await drawer.getByRole('button', { name: 'Modifica scheda' }).click()
    const edit = page.getByRole('dialog', { name: 'Modifica paziente' })
    await edit.getByRole('button', { name: 'Salva' }).click()
    await expect(edit.getByRole('textbox', { name: 'Motivo' })).toBeFocused()
    await edit.locator('input').first().fill('Paziente prova interfaccia')
    await edit.getByRole('textbox', { name: 'Motivo' }).fill('Correzione UAT sintetica')
    await edit.getByRole('button', { name: 'Salva' }).click()
    await expect(edit).toBeHidden()
    await expect(drawer.getByRole('heading', { name: /Paziente prova interfaccia/ }).first()).toBeVisible()
    await page.reload()
    await page.getByRole('combobox', { name: 'Centro' }).selectOption(fixture.center_a)
    await page.getByRole('textbox', { name: 'Cerca pazienti' }).fill(fixture.patient_a)
    await page.locator('tbody tr').click()
    await expect(page.getByRole('dialog').getByText('Paziente prova interfaccia').first()).toBeVisible()
    const note = page.getByRole('dialog').getByRole('textbox', { name: 'Nuova nota organizzativa' })
    await note.fill(fixture.tag + ' NOTA UI')
    await page.getByRole('dialog').getByRole('button', { name: 'Aggiungi nota' }).click()
    await expect(page.getByRole('dialog').locator('.note p').filter({ hasText: fixture.tag + ' NOTA UI' }).first()).toBeVisible()
    await page.getByRole('dialog').locator('.note').filter({ hasText: fixture.tag + ' NOTA UI' }).first().getByRole('button', { name: 'Rettifica' }).click()
    await page.getByRole('dialog').getByRole('textbox', { name: 'Rettifica nota' }).fill(fixture.tag + ' NOTA UI RETTIFICATA')
    await page.getByRole('dialog').getByRole('button', { name: 'Registra rettifica' }).click()
    await expect(page.getByRole('dialog').locator('.note p').filter({ hasText: fixture.tag + ' NOTA UI RETTIFICATA' }).first()).toBeVisible()
    await page.screenshot({ path: info.outputPath('patients-live-edit-note.png'), fullPage: true })
  } finally { await ctx.close() }
})

test('revoca e ripristino: accesso professionista e audit effettivi', async ({ browser }, info) => {
  test.skip(info.project.name !== 'desktop')
  const manager = await context(browser, 'manager')
  const pro = await context(browser, 'professional_a')
  try {
    const page = await manager.newPage()
    await page.goto('/premium/#Pazienti')
    const token = await csrf(page)
    const args = { patient: fixture.patient_a, center: fixture.center_a,
      practitioner: fixture.practitioner_a, reason: 'AUDIT-04 revoca e ripristino sintetico' }
    const before = await get(pro, 'operations.profiles.patient_detail', { center: fixture.center_a, name: fixture.patient_a })
    expect(before.response.ok()).toBeTruthy()
    const revoke = await post(manager, token, 'security.lifecycle.set_assignment', { ...args, active: 0 })
    expect(revoke.response.ok()).toBeTruthy()
    const denied = await get(pro, 'operations.profiles.patient_detail', { center: fixture.center_a, name: fixture.patient_a })
    expect(denied.response.ok()).toBeFalsy()
    const privateDenied = await get(pro, 'operations.workspace.patient_history', { center: fixture.center_a, patient: fixture.patient_a })
    expect(privateDenied.response.ok()).toBeFalsy()
    const restore = await post(manager, token, 'security.lifecycle.set_assignment', { ...args, active: 1 })
    expect(restore.response.ok()).toBeTruthy()
    const after = await get(pro, 'operations.profiles.patient_detail', { center: fixture.center_a, name: fixture.patient_a })
    expect(after.response.ok()).toBeTruthy()
    const history = await get(manager, 'operations.workspace.patient_history', { center: fixture.center_a, patient: fixture.patient_a })
    expect(history.response.ok()).toBeTruthy()
    const events = history.body.message.assignment_events as { active: number; reason: string }[]
    expect(events.some(row => row.active === 0 && row.reason === args.reason)).toBeTruthy()
    expect(events.some(row => row.active === 1 && row.reason === args.reason)).toBeTruthy()
  } finally { await manager.close(); await pro.close() }
})

test('pacchetti e note: richieste dirette fuori contesto negate', async ({ browser }, info) => {
  test.skip(info.project.name !== 'desktop')
  const manager = await context(browser, 'manager')
  const accountant = await context(browser, 'accountant')
  const pro = await context(browser, 'professional_b')
  try {
    const page = await manager.newPage()
    await page.goto('/premium/#Pazienti')
    const token = await csrf(page)
    const invalidCenter = await post(manager, token, 'operations.packages.issue', {
      template: fixture.template, patient: fixture.patient_a, centers: [fixture.center_b],
      reason: 'Test contesto negato', request_key: fixture.tag + '-invalid-center' })
    expect(invalidCenter.response.ok()).toBeFalsy()
    const invalidPractitioner = await post(manager, token, 'operations.packages.issue', {
      template: fixture.template, patient: fixture.patient_a, centers: [fixture.center_a],
      practitioner: 'CC-MISSING-PRACTITIONER', reason: 'Test professionista invalido',
      request_key: fixture.tag + '-invalid-practitioner' })
    expect(invalidPractitioner.response.ok()).toBeFalsy()
    const unauthorized = await get(accountant, 'operations.workspace.patient_history', {
      center: fixture.center_a, patient: fixture.patient_a })
    expect(unauthorized.response.ok()).toBeFalsy()
    const crossNote = await get(pro, 'operations.workspace.patient_history', {
      center: fixture.center_b, patient: fixture.patient_a })
    expect(crossNote.response.ok()).toBeFalsy()
    expect(JSON.stringify(crossNote.body)).not.toContain('PRIVATE CORRECTION')
  } finally { await manager.close(); await accountant.close(); await pro.close() }
})

test('scritture dirette negate per ruolo e paziente non assegnato', async ({ browser }, info) => {
  test.skip(info.project.name !== 'desktop')
  for (const role of ['secretariat', 'professional_b', 'finance'] as const) {
    const ctx = await context(browser, role)
    try {
      const page = await ctx.newPage()
      await page.goto('/premium/#Pazienti')
      const token = await csrf(page)
      if (role === 'secretariat') {
        const detail = await get(ctx, 'operations.profiles.patient_detail', { center: fixture.center_a, name: fixture.patient_a })
        expect(detail.response.ok()).toBeTruthy()
        const denied = await post(ctx, token, 'operations.profiles.patient_save', {
          center: fixture.center_a, name: fixture.patient_a, first_name: 'Non autorizzato',
          last_name: 'Sintetico', email: '', expected_version: detail.body.message.modified,
          request_key: fixture.tag + '-secretariat-write', reason: 'Verifica permesso' })
        expect(denied.response.ok()).toBeFalsy()
      } else if (role === 'professional_b') {
        const denied = await post(ctx, token, 'operations.notes.add_note', {
          patient: fixture.patient_a, center: fixture.center_a, private: 1,
          content: fixture.tag + ' DEVE ESSERE NEGATO' })
        expect(denied.response.ok()).toBeFalsy()
      } else {
        const denied = await post(ctx, token, 'operations.packages.issue', {
          template: fixture.template, patient: fixture.patient_a, centers: [fixture.center_a],
          reason: 'Verifica permesso', request_key: fixture.tag + '-finance-denied' })
        expect(denied.response.ok()).toBeFalsy()
      }
    } finally { await ctx.close() }
  }
})

test('pacchetto dedicato: professionista privo di membership nel centro negato', async ({ browser }, info) => {
  test.skip(info.project.name !== 'desktop')
  const manager = await context(browser, 'manager')
  const userB = fixture.tag.toLowerCase() + '-b@example.invalid'
  let restoreMembership = false
  let token = ''
  const membership = { user: userB, center: fixture.center_a, reason: 'Verifica sintetica centro pacchetto' }
  try {
    const page = await manager.newPage()
    await page.goto('/premium/#Pazienti')
    token = await csrf(page)
    const revoke = await post(manager, token, 'security.lifecycle.set_membership', { ...membership, active: 0 })
    expect(revoke.response.ok()).toBeTruthy()
    restoreMembership = true
    const issue = await post(manager, token, 'operations.packages.issue', {
      template: fixture.template, patient: fixture.patient_a, centers: [fixture.center_a],
      practitioner: fixture.practitioner_b, reason: 'Test professionista fuori centro',
      request_key: fixture.tag + '-wrong-practitioner-center' })
    expect(issue.response.ok()).toBeFalsy()
  } finally {
    try {
      if (restoreMembership) {
        const restore = await post(manager, token, 'security.lifecycle.set_membership', { ...membership, active: 1 })
        expect(restore.response.ok(), 'Ripristino membership sintetica obbligatorio').toBeTruthy()
      }
    } finally { await manager.close() }
  }
})

test('storico seduta reale: prenotazione, riserva, cancellazione e rilascio pacchetto', async ({ browser }, info) => {
  test.skip(info.project.name !== 'desktop')
  const manager = await context(browser, 'manager')
  try {
    const page = await manager.newPage()
    await page.goto('/premium/#Pazienti')
    const token = await csrf(page)
    const schedule = await post(manager, token, 'scheduling.availability.set_schedule', {
      practitioner: fixture.practitioner_a, center: fixture.center_a,
      time_slots: [{ day: 'Monday', from_time: '09:00:00', to_time: '12:00:00' }],
      reason: 'Fascia UAT sintetica per storico' })
    expect(schedule.response.ok()).toBeTruthy()
    const key = fixture.tag + '-history-' + Date.now().toString(36)
    const issued = await post(manager, token, 'operations.packages.issue', {
      template: fixture.template, patient: fixture.patient_a, centers: [fixture.center_a],
      practitioner: fixture.practitioner_a, reason: 'Pacchetto sintetico per storico', request_key: key + '-package' })
    expect(issued.response.ok()).toBeTruthy()
    const packageName = issued.body.message.name as string
    const todayRome = new Intl.DateTimeFormat('en-CA', { timeZone: 'Europe/Rome', year: 'numeric', month: '2-digit', day: '2-digit' }).format(new Date())
    const [year, month, day] = todayRome.split('-').map(Number)
    let dateMs = Date.UTC(year, month - 1, day) + 14 * 86_400_000
    while (new Date(dateMs).getUTCDay() !== 1) dateMs += 86_400_000
    const appointmentDate = new Date(dateMs).toISOString().slice(0, 10)
    const booked = await post(manager, token, 'scheduling.booking.book', {
      patient: fixture.patient_a, practitioner: fixture.practitioner_a, center: fixture.center_a,
      appointment_type: fixture.appointment_type, appointment_date: appointmentDate,
      appointment_time: '10:30:00', patient_package: packageName,
      request_key: key, reason: 'Prenotazione UAT sintetica' })
    const bookingError = booked.body._server_messages ? JSON.parse(booked.body._server_messages).map((entry: string) => JSON.parse(entry).message).join('; ') : ''
    expect(booked.response.ok(), `prenotazione sintetica: HTTP ${booked.response.status()} ${bookingError}`).toBeTruthy()
    const name = booked.body.message.name as string
    let cancelCompleted = false
    try {
    const reserved = await get(manager, 'operations.packages.balance', { package: packageName, center: fixture.center_a })
    expect(reserved.body.message.reserved).toBe(1)
    const history = await get(manager, 'operations.workspace.patient_history', { patient: fixture.patient_a, center: fixture.center_a })
    expect(history.response.ok()).toBeTruthy()
    const inVisibleHistory = history.body.message.appointments.some((row: { name: string }) => row.name === name)
    if (!history.body.message.truncated) expect(inVisibleHistory).toBeTruthy()
    const events = await get(manager, 'operations.workspace.appointment_events', { appointment: name })
    expect(events.response.ok()).toBeTruthy()
    expect(events.body.message.some((row: { event_type: string }) => row.event_type === 'APPOINTMENT_BOOKED')).toBeTruthy()
    const canceled = await post(manager, token, 'operations.lifecycle.cancel', {
      appointment: name, reason: 'Cancellazione UAT sintetica' })
    expect(canceled.response.ok()).toBeTruthy()
    cancelCompleted = true
    expect(canceled.body.message.late).toBe(false)
    const released = await get(manager, 'operations.packages.balance', { package: packageName, center: fixture.center_a })
    expect(released.body.message.reserved).toBe(0)
    expect(released.body.message.remaining).toBe(1)
    const after = await get(manager, 'operations.workspace.appointment_events', { appointment: name })
    expect(after.body.message.some((row: { event_type: string }) => row.event_type === 'SESSION_CANCELLED')).toBeTruthy()
    await page.getByRole('combobox', { name: 'Centro' }).selectOption(fixture.center_a)
    await page.getByRole('textbox', { name: 'Cerca pazienti' }).fill(fixture.patient_a)
    await page.locator('tbody tr').first().click()
    const drawer = page.getByRole('dialog')
    if (inVisibleHistory) {
      await drawer.locator('button.patient-history-item').filter({ hasText: appointmentDate.split('-').reverse().join('/') }).first().click()
      await expect(drawer.getByText('Prenotazione creata').first()).toBeVisible()
      await expect(drawer.getByText('Seduta cancellata').first()).toBeVisible()
    } else {
      expect(history.body.message.truncated).toBe(true)
      await expect(drawer.getByText('Mostrate le ultime 100 sedute.')).toBeVisible()
    }
    await page.screenshot({ path: info.outputPath('patients-live-history.png'), fullPage: true })
    } finally {
      if (!cancelCompleted) await post(manager, token, 'operations.lifecycle.cancel', {
        appointment: name, reason: 'Pulizia prenotazione UAT sintetica dopo errore' }).catch(() => undefined)
    }
  } finally { await manager.close() }
})

test('cancellazione tardiva sintetica: unità pacchetto consumata una sola volta', async ({ browser }, info) => {
  test.skip(info.project.name !== 'desktop')
  const manager = await context(browser, 'manager')
  try {
    const page = await manager.newPage()
    await page.goto('/premium/#Pazienti')
    const token = await csrf(page)
    const local = new Intl.DateTimeFormat('en-CA', { timeZone: 'Europe/Rome', year: 'numeric', month: '2-digit', day: '2-digit' }).format(new Date())
    const [year, month, day] = local.split('-').map(Number)
    const target = new Date(Date.UTC(year, month - 1, day) + 86_400_000)
    const date = target.toISOString().slice(0, 10)
    const weekday = new Intl.DateTimeFormat('en-US', { weekday: 'long', timeZone: 'UTC' }).format(target)
    const schedule = await post(manager, token, 'scheduling.availability.set_schedule', {
      practitioner: fixture.practitioner_a, center: fixture.center_a,
      time_slots: [{ day: weekday, from_time: '09:00:00', to_time: '12:00:00' }],
      reason: 'Fascia UAT sintetica temporanea' })
    expect(schedule.response.ok()).toBeTruthy()
    const key = fixture.tag + '-late-' + Date.now().toString(36)
    const issued = await post(manager, token, 'operations.packages.issue', {
      template: fixture.template, patient: fixture.patient_a, centers: [fixture.center_a],
      practitioner: fixture.practitioner_a, reason: 'Pacchetto tardivo sintetico', request_key: key })
    expect(issued.response.ok()).toBeTruthy()
    const packageName = issued.body.message.name as string
    const booked = await post(manager, token, 'scheduling.booking.book', {
      patient: fixture.patient_a, practitioner: fixture.practitioner_a, center: fixture.center_a,
      appointment_type: fixture.appointment_type, appointment_date: date,
      appointment_time: '09:00:00', patient_package: packageName,
      request_key: key + '-book', reason: 'Prenotazione tardiva sintetica' })
    expect(booked.response.ok()).toBeTruthy()
    const appointment = booked.body.message.name as string
    const canceled = await post(manager, token, 'operations.lifecycle.cancel', { appointment, reason: 'Cancellazione tardiva sintetica' })
    expect(canceled.response.ok()).toBeTruthy()
    expect(canceled.body.message.late).toBe(true)
    const replay = await post(manager, token, 'operations.lifecycle.cancel', { appointment, reason: 'Retry sintetico' })
    expect(replay.response.ok()).toBeTruthy()
    expect(replay.body.message.replay).toBe(true)
    const balance = await get(manager, 'operations.packages.balance', { package: packageName, center: fixture.center_a })
    expect(balance.response.ok()).toBeTruthy()
    expect(balance.body.message.remaining).toBe(0)
    expect(balance.body.message.reserved).toBe(0)
  } finally { await manager.close() }
})

test('ultima revoca: Direzione legge storico, scritture bloccate e riattivazione', async ({ browser }, info) => {
  test.skip(info.project.name !== 'desktop')
  const manager = await context(browser, 'manager')
  const professional = await context(browser, 'professional_a')
  const secretariat = await context(browser, 'secretariat')
  const revoked: string[] = []
  try {
    const page = await manager.newPage()
    await page.goto('/premium/#Pazienti')
    const token = await csrf(page)
    const assignments = await get(manager, 'frappe.client.get_list', {
      doctype: 'CC Patient Assignment', fields: '["name","patient","center","practitioner","active"]',
      filters: JSON.stringify({ patient: fixture.patient_a, center: fixture.center_a, active: 1 }) })
    expect(assignments.response.ok()).toBeTruthy()
    expect(assignments.body.message.length).toBeGreaterThan(0)
    for (const row of assignments.body.message as { practitioner: string }[]) {
      expect([fixture.practitioner_a, fixture.practitioner_b]).toContain(row.practitioner)
      const result = await post(manager, token, 'security.lifecycle.set_assignment', {
        patient: fixture.patient_a, center: fixture.center_a, practitioner: row.practitioner,
        active: 0, reason: 'Revoca UAT sintetica e reversibile' })
      expect(result.response.ok()).toBeTruthy()
      revoked.push(row.practitioner)
    }
    const search = await get(manager, 'operations.workspace.patient_search', { center: fixture.center_a, query: fixture.tag })
    expect(search.response.ok()).toBeTruthy()
    expect(search.body.message.patients.find((row: { name: string }) => row.name === fixture.patient_a)?.active_assignment).toBe(false)
    const profile = await get(manager, 'operations.profiles.patient_detail', { center: fixture.center_a, name: fixture.patient_a })
    expect(profile.response.ok()).toBeTruthy()
    expect(profile.body.message.active_assignment).toBe(false)
    const history = await get(manager, 'operations.workspace.patient_history', { center: fixture.center_a, patient: fixture.patient_a })
    expect(history.response.ok()).toBeTruthy()
    expect(history.body.message.assignment_events.some((row: { active: number }) => row.active === 0)).toBeTruthy()
    const deniedNote = await post(manager, token, 'operations.notes.add_note', {
      center: fixture.center_a, patient: fixture.patient_a, content: 'NON SALVARE', private: 0 })
    expect(deniedNote.response.ok()).toBeFalsy()
    const deniedAdjustment = await post(manager, token, 'operations.packages.adjust', {
      package: fixture.package, units: 1, request_key: fixture.tag + '-historical-adjust', reason: 'NON SALVARE' })
    expect(deniedAdjustment.response.ok()).toBeFalsy()
    for (const actor of [professional, secretariat]) {
      const hidden = await get(actor, 'operations.workspace.patient_search', { center: fixture.center_a, query: fixture.tag })
      expect(hidden.response.ok()).toBeTruthy()
      expect(hidden.body.message.patients.some((row: { name: string }) => row.name === fixture.patient_a)).toBeFalsy()
      const direct = await get(actor, 'operations.profiles.patient_detail', { center: fixture.center_a, name: fixture.patient_a })
      expect(direct.response.ok()).toBeFalsy()
    }
    await page.getByRole('combobox', { name: 'Centro' }).selectOption(fixture.center_a)
    await page.getByRole('textbox', { name: 'Cerca pazienti' }).fill(fixture.patient_a)
    await expect(page.locator('tbody tr').filter({ hasText: 'Storico' }).first()).toBeVisible()
    await page.locator('tbody tr').filter({ hasText: 'Storico' }).first().click()
    const drawer = page.getByRole('dialog')
    await expect(drawer.getByText('Nessuna assegnazione attiva in questo centro.')).toBeVisible()
    await expect(drawer.getByText('Assegnazione revocata').first()).toBeVisible()
    await expect(drawer.getByRole('button', { name: 'Modifica scheda' })).toHaveCount(0)
    await expect(drawer.getByRole('button', { name: 'Emetti pacchetto' })).toHaveCount(0)
    await page.screenshot({ path: info.outputPath('patients-live-historical.png'), fullPage: true })
  } finally {
    if (revoked.length) {
      const recoveryPage = await manager.newPage()
      await recoveryPage.goto('/premium/#Pazienti')
      const token = await csrf(recoveryPage)
      for (const practitioner of revoked) {
        const restored = await post(manager, token, 'security.lifecycle.set_assignment', {
          patient: fixture.patient_a, center: fixture.center_a, practitioner, active: 1,
          reason: 'Ripristino fixture UAT sintetica' })
        expect(restored.response.ok()).toBeTruthy()
      }
    }
    await manager.close(); await professional.close(); await secretariat.close()
  }
})

test('Segreteria: note organizzative, assegnazione e pacchetto nei limiti autorizzati', async ({ browser }, info) => {
  test.skip(info.project.name !== 'desktop')
  const secretary = await context(browser, 'secretariat')
  const manager = await context(browser, 'manager')
  let extraAssignment = false
  try {
    const page = await secretary.newPage()
    await page.goto('/premium/#Pazienti')
    const token = await csrf(page)
    const note = await post(secretary, token, 'operations.notes.add_note', {
      patient: fixture.patient_a, center: fixture.center_a, private: 0,
      content: fixture.tag + ' SEGRETERIA ORGANIZZATIVA' })
    expect(note.response.ok()).toBeTruthy()
    const corrected = await post(secretary, token, 'operations.notes.add_note', {
      patient: fixture.patient_a, center: fixture.center_a, private: 0,
      content: fixture.tag + ' SEGRETERIA RETTIFICA', corrects: note.body.message.name })
    expect(corrected.response.ok()).toBeTruthy()
    const view = await get(secretary, 'operations.workspace.patient_history', {
      patient: fixture.patient_a, center: fixture.center_a })
    expect(view.response.ok()).toBeTruthy()
    expect(view.body.message.organizational_notes.some((row: { name: string }) => row.name === corrected.body.message.name)).toBeTruthy()
    const suffix = Date.now().toString(36)
    const issue = await post(secretary, token, 'operations.packages.issue', {
      template: fixture.template, patient: fixture.patient_a, centers: [fixture.center_a],
      practitioner: fixture.practitioner_a, valid_until: '2099-12-31',
      reason: 'Pacchetto Segreteria sintetico', request_key: fixture.tag + '-secretary-issue-' + suffix })
    expect(issue.response.ok()).toBeTruthy()
    const adjustment = await post(secretary, token, 'operations.packages.adjust', {
      package: issue.body.message.name, units: 1, reason: 'Rettifica Segreteria sintetica',
      request_key: fixture.tag + '-secretary-adjust-' + suffix })
    expect(adjustment.response.ok()).toBeTruthy()
    const expired = await post(secretary, token, 'operations.packages.issue', {
      template: fixture.template, patient: fixture.patient_a, centers: [fixture.center_a],
      valid_until: '2020-01-01', reason: 'DEVE FALLIRE',
      request_key: fixture.tag + '-secretary-expired-' + suffix })
    expect(expired.response.ok()).toBeFalsy()
    const assigned = await post(secretary, token, 'security.lifecycle.set_assignment', {
      patient: fixture.patient_a, center: fixture.center_a, practitioner: fixture.practitioner_b,
      active: 1, reason: 'Assegnazione Segreteria sintetica' })
    expect(assigned.response.ok()).toBeTruthy()
    extraAssignment = true
    const history = await get(manager, 'operations.workspace.patient_history', {
      patient: fixture.patient_a, center: fixture.center_a })
    expect(history.response.ok()).toBeTruthy()
    expect(history.body.message.assignment_events.some((row: { practitioner: string; active: number }) =>
      row.practitioner === fixture.practitioner_b && row.active === 1)).toBeTruthy()
  } finally {
    if (extraAssignment) {
      const page = await secretary.newPage()
      await page.goto('/premium/#Pazienti')
      const token = await csrf(page)
      const revoked = await post(secretary, token, 'security.lifecycle.set_assignment', {
        patient: fixture.patient_a, center: fixture.center_a, practitioner: fixture.practitioner_b,
        active: 0, reason: 'Ripristino fixture Segreteria sintetica' })
      expect(revoked.response.ok()).toBeTruthy()
    }
    await secretary.close(); await manager.close()
  }
})

test('riassegnazione reale: grant nuovo, revoca precedente e ritorno allo stato fixture', async ({ browser }, info) => {
  test.skip(info.project.name !== 'desktop')
  const manager = await context(browser, 'manager')
  const previous = await context(browser, 'professional_a')
  const next = await context(browser, 'professional_b')
  let moved = false
  try {
    const page = await manager.newPage()
    await page.goto('/premium/#Pazienti')
    const token = await csrf(page)
    const change = await post(manager, token, 'security.lifecycle.reassign', {
      patient: fixture.patient_a, center: fixture.center_a,
      old_practitioner: fixture.practitioner_a, new_practitioner: fixture.practitioner_b,
      reason: 'Riassegnazione UAT sintetica' })
    expect(change.response.ok()).toBeTruthy()
    moved = true
    const priorDenied = await get(previous, 'operations.profiles.patient_detail', {
      center: fixture.center_a, name: fixture.patient_a })
    const newGranted = await get(next, 'operations.profiles.patient_detail', {
      center: fixture.center_a, name: fixture.patient_a })
    expect(priorDenied.response.ok()).toBeFalsy()
    expect(newGranted.response.ok()).toBeTruthy()
    const audit = await get(manager, 'operations.workspace.patient_history', {
      patient: fixture.patient_a, center: fixture.center_a })
    expect(audit.response.ok()).toBeTruthy()
    expect(audit.body.message.assignment_events.some((row: { practitioner: string; active: number }) =>
      row.practitioner === fixture.practitioner_b && row.active === 1)).toBeTruthy()
  } finally {
    if (moved) {
      const page = await manager.newPage()
      await page.goto('/premium/#Pazienti')
      const token = await csrf(page)
      const restored = await post(manager, token, 'security.lifecycle.reassign', {
        patient: fixture.patient_a, center: fixture.center_a,
        old_practitioner: fixture.practitioner_b, new_practitioner: fixture.practitioner_a,
        reason: 'Ripristino riassegnazione UAT sintetica' })
      expect(restored.response.ok()).toBeTruthy()
    }
    await manager.close(); await previous.close(); await next.close()
  }
})

test('storico oltre cento sedute: limite e avviso espliciti', async ({ browser }, info) => {
  test.skip(info.project.name !== 'desktop')
  test.setTimeout(180_000)
  const manager = await context(browser, 'manager')
  try {
    const page = await manager.newPage()
    await page.goto('/premium/#Pazienti')
    const token = await csrf(page)
    const schedule = await post(manager, token, 'scheduling.availability.set_schedule', {
      practitioner: fixture.practitioner_a, center: fixture.center_a,
      time_slots: [{ day: 'Monday', from_time: '09:00:00', to_time: '12:00:00' }],
      reason: 'Fascia sintetica per limite storico' })
    expect(schedule.response.ok()).toBeTruthy()
    let firstMonday = Date.UTC(2100, 0, 1)
    while (new Date(firstMonday).getUTCDay() !== 1) firstMonday += 86_400_000
    for (let index = 0; index < 101; index++) {
      const appointmentDate = new Date(firstMonday + index * 7 * 86_400_000).toISOString().slice(0, 10)
      const booked = await post(manager, token, 'scheduling.booking.book', {
        patient: fixture.patient_a, practitioner: fixture.practitioner_a, center: fixture.center_a,
        appointment_type: fixture.appointment_type, appointment_date: appointmentDate,
        appointment_time: '09:00:00', request_key: fixture.tag + '-history-limit-' + index,
        reason: 'Seduta sintetica per limite storico' })
      expect(booked.response.ok(), `prenotazione sintetica ${index + 1}: HTTP ${booked.response.status()}`).toBeTruthy()
    }
    const history = await get(manager, 'operations.workspace.patient_history', {
      patient: fixture.patient_a, center: fixture.center_a })
    expect(history.response.ok()).toBeTruthy()
    expect(history.body.message.truncated).toBe(true)
    expect(history.body.message.appointments).toHaveLength(100)
    await page.getByRole('combobox', { name: 'Centro' }).selectOption(fixture.center_a)
    await page.getByRole('textbox', { name: 'Cerca pazienti' }).fill(fixture.patient_a)
    await page.locator('tbody tr').first().click()
    await expect(page.getByRole('dialog').getByText('Mostrate le ultime 100 sedute.')).toBeVisible()
  } finally { await manager.close() }
})
