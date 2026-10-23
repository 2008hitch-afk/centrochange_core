/** AUDIT-04: real Frappe/MariaDB on an identified disposable clone. No mocks. */
import { expect, test, type Browser, type BrowserContext } from '@playwright/test'
import { readFileSync, statSync } from 'node:fs'
import { resolve } from 'node:path'

type Role = 'manager' | 'secretariat' | 'professional_a' | 'professional_b' | 'professional_c' | 'finance' | 'accountant'
type Fixture = { synthetic_only: true; tag: string; center_a: string; center_b: string;
  patient_a: string; patient_b: string; practitioner_a: string; practitioner_b: string;
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
    !fixture.patient_a || !fixture.patient_b || !fixture.template || !fixture.package ||
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
    await page.getByRole('textbox', { name: 'Cerca pazienti' }).fill(fixture.tag)
    await expect(page.locator('tbody tr')).toHaveCount(1)
    await page.locator('tbody tr').first().click()
    const drawer = page.getByRole('dialog')
    await expect(drawer.getByRole('heading', { name: /Paziente/ }).first()).toBeVisible()
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
    const concurrentArgs = { ...issueArgs, request_key: fixture.tag + '-concurrent-' + Date.now().toString(36) }
    const [parallelA, parallelB] = await Promise.all([
      post(ctx, token, 'operations.packages.issue', concurrentArgs),
      post(secondManager, secondToken, 'operations.packages.issue', concurrentArgs),
    ])
    expect(parallelA.response.ok() && parallelB.response.ok(),
      `concurrent HTTP ${parallelA.response.status()}/${parallelB.response.status()} types ${parallelA.body.exc_type ?? '-'} / ${parallelB.body.exc_type ?? '-'}`).toBeTruthy()
    expect(parallelA.body.message.name).toBe(parallelB.body.message.name)
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
    await page.getByRole('textbox', { name: 'Cerca pazienti' }).fill(fixture.tag)
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
    await page.getByRole('textbox', { name: 'Cerca pazienti' }).fill(fixture.tag)
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
  try {
    const page = await manager.newPage()
    await page.goto('/premium/#Pazienti')
    const token = await csrf(page)
    const membership = { user: userB, center: fixture.center_a, reason: 'Verifica sintetica centro pacchetto' }
    const revoke = await post(manager, token, 'security.lifecycle.set_membership', { ...membership, active: 0 })
    expect(revoke.response.ok()).toBeTruthy()
    const issue = await post(manager, token, 'operations.packages.issue', {
      template: fixture.template, patient: fixture.patient_a, centers: [fixture.center_a],
      practitioner: fixture.practitioner_b, reason: 'Test professionista fuori centro',
      request_key: fixture.tag + '-wrong-practitioner-center' })
    expect(issue.response.ok()).toBeFalsy()
    const restore = await post(manager, token, 'security.lifecycle.set_membership', { ...membership, active: 1 })
    expect(restore.response.ok()).toBeTruthy()
  } finally { await manager.close() }
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
    const booked = await post(manager, token, 'scheduling.booking.book', {
      patient: fixture.patient_a, practitioner: fixture.practitioner_a, center: fixture.center_a,
      appointment_type: fixture.appointment_type, appointment_date: '2099-01-12',
      appointment_time: '09:00:00', patient_package: fixture.package,
      request_key: key, reason: 'Prenotazione UAT sintetica' })
    expect(booked.response.ok()).toBeTruthy()
    const name = booked.body.message.name as string
    const reserved = await get(manager, 'operations.packages.balance', { package: fixture.package, center: fixture.center_a })
    expect(reserved.body.message.reserved).toBe(1)
    const history = await get(manager, 'operations.workspace.patient_history', { patient: fixture.patient_a, center: fixture.center_a })
    expect(history.response.ok()).toBeTruthy()
    expect(history.body.message.appointments.some((row: { name: string }) => row.name === name)).toBeTruthy()
    const events = await get(manager, 'operations.workspace.appointment_events', { appointment: name })
    expect(events.response.ok()).toBeTruthy()
    expect(events.body.message.some((row: { event_type: string }) => row.event_type === 'APPOINTMENT_BOOKED')).toBeTruthy()
    const canceled = await post(manager, token, 'operations.lifecycle.cancel', {
      appointment: name, reason: 'Cancellazione UAT sintetica' })
    expect(canceled.response.ok()).toBeTruthy()
    expect(canceled.body.message.late).toBe(false)
    const released = await get(manager, 'operations.packages.balance', { package: fixture.package, center: fixture.center_a })
    expect(released.body.message.reserved).toBe(0)
    expect(released.body.message.remaining).toBe(1)
    const after = await get(manager, 'operations.workspace.appointment_events', { appointment: name })
    expect(after.body.message.some((row: { event_type: string }) => row.event_type === 'SESSION_CANCELLED')).toBeTruthy()
    await page.getByRole('combobox', { name: 'Centro' }).selectOption(fixture.center_a)
    await page.getByRole('textbox', { name: 'Cerca pazienti' }).fill(fixture.tag)
    await page.locator('tbody tr').first().click()
    const drawer = page.getByRole('dialog')
    await drawer.locator('button.patient-history-item').filter({ hasText: '12/01/2099' }).first().click()
    await expect(drawer.getByText('Prenotazione creata').first()).toBeVisible()
    await expect(drawer.getByText('Seduta cancellata').first()).toBeVisible()
    await page.screenshot({ path: info.outputPath('patients-live-history.png'), fullPage: true })
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
