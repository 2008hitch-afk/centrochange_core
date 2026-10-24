/** AUDIT-05: real Frappe/MariaDB against an owned disposable clone. No mocks. */
import { expect, test, type Browser, type BrowserContext } from '@playwright/test'
import { readFileSync, statSync } from 'node:fs'
import { resolve } from 'node:path'

type Role = 'manager' | 'secretariat' | 'professional_a' | 'professional_b' | 'professional_c' | 'finance' | 'accountant'
type Fixture = { synthetic_only: true; tag: string; center_a: string; center_b: string;
  practitioner_a: string; practitioner_b: string; patient_a: string; roles: Record<Role, string>;
  daily_appointments: [string, string]; daily_date: string; future_appointment: string; reminder_log: string;
  availability_patient: string; appointment_type: string }
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
    !fixture.practitioner_a || !fixture.practitioner_b || !fixture.patient_a || roles.some(role => !fixture.roles[role]) ||
    !fixture.daily_date || fixture.daily_appointments?.length !== 2 || !fixture.future_appointment || !fixture.reminder_log ||
    !fixture.availability_patient || !fixture.appointment_type)
  throw new Error('AUDIT-05 fixture inventory incomplete')
for (const role of roles) privateFile(fixture.roles[role])
const method = (name: string) => '/api/method/centrochange_core.' + name
const ctxFor = (browser: Browser, role: Role) => browser.newContext({ storageState: fixture.roles[role] })
async function api(ctx: BrowserContext, name: string, args: Record<string, string>) {
  const response = await ctx.request.get(name.startsWith('frappe.') ? '/api/method/' + name : method(name), { params: args })
  return { response, body: await response.json().catch(() => ({})) }
}
async function post(ctx: BrowserContext, name: string, args: Record<string, unknown>, csrf: string) {
  const response = await ctx.request.post(method(name), { data: args, headers: { 'X-Frappe-CSRF-Token': csrf } })
  return { response, body: await response.json().catch(() => ({})) }
}

test('Account professionista: agenda propria, chiusura pagata/non pagata, replay e report', async ({ browser }, info) => {
  test.skip(info.project.name !== 'desktop')
  const ctx = await ctxFor(browser, 'professional_a')
  const other = await ctxFor(browser, 'professional_b')
  try {
    const page = await ctx.newPage()
    const otherPage = await other.newPage()
    await otherPage.goto('/premium/')
    const otherCsrf = await otherPage.locator('meta[name="csrf-token"]').getAttribute('content')
    expect(otherCsrf).toBeTruthy()
    await page.goto('/premium/#Agenda')
    await page.getByRole('combobox', { name: 'Centro' }).selectOption(fixture.center_a)
    const csrf = await page.locator('meta[name="csrf-token"]').getAttribute('content')
    expect(csrf).toBeTruthy()
    const agenda = await api(ctx, 'operations.workspace.agenda', { center: fixture.center_a, start: fixture.daily_date, end: fixture.daily_date })
    expect(agenda.response.ok()).toBeTruthy()
    expect((agenda.body.message?.appointments ?? []).map((row: { name: string }) => row.name)).toEqual(expect.arrayContaining(fixture.daily_appointments))
    const foreign = await api(other, 'operations.workspace.agenda', { center: fixture.center_a, start: fixture.daily_date, end: fixture.daily_date })
    expect((foreign.body.message?.appointments ?? []).map((row: { name: string }) => row.name)).not.toContain(fixture.daily_appointments[0])
    const unauthorized = await post(other, 'operations.lifecycle.close', { appointment: fixture.daily_appointments[0], paid: 0, reason: 'Tentativo negato' }, otherCsrf!)
    expect(unauthorized.response.ok()).toBeFalsy()
    const future = await post(ctx, 'operations.lifecycle.close', { appointment: fixture.future_appointment, paid: 0, reason: 'Seduta futura' }, csrf!)
    expect(future.response.ok()).toBeFalsy()
    const cancelledBooking = await post(ctx, 'scheduling.booking.book', { patient: fixture.availability_patient,
      practitioner: fixture.practitioner_a, center: fixture.center_a, appointment_type: fixture.appointment_type,
      appointment_date: '2099-03-02', appointment_time: '10:00:00',
      request_key: `${fixture.tag}-cancelled-closure`, reason: 'Seduta sintetica da cancellare' }, csrf!)
    expect(cancelledBooking.response.ok()).toBeTruthy()
    const cancelledName = cancelledBooking.body.message.name
    const cancelled = await post(ctx, 'operations.lifecycle.cancel', { appointment: cancelledName, reason: 'Verifica chiusura negata' }, csrf!)
    expect(cancelled.response.ok()).toBeTruthy()
    const cancelledClose = await post(ctx, 'operations.lifecycle.close', { appointment: cancelledName, paid: 0, reason: 'Seduta annullata' }, csrf!)
    expect(cancelledClose.response.ok()).toBeFalsy()

    let paymentMethod = ''
    if (!agenda.body.message.appointments.find((row: { name: string }) => row.name === fixture.daily_appointments[0])?.cc_performed) {
      await expect(page.locator('.week-event[data-time="07:00"]')).toBeVisible()
      await page.locator('.week-event[data-time="07:00"]').click()
      await page.getByRole('button', { name: 'Chiudi seduta' }).click()
      await page.getByRole('checkbox', { name: 'Pagata' }).check()
      paymentMethod = await page.getByRole('combobox', { name: 'Metodo di pagamento' }).inputValue()
      expect(paymentMethod).toBeTruthy()
      await page.getByRole('textbox', { name: 'Motivo' }).fill('Seduta sintetica svolta e pagata')
      await page.getByRole('button', { name: 'Conferma', exact: true }).click()
      await expect(page.getByText('Sedute svolte')).toBeVisible()
    }
    await expect.poll(async () => { const result = await api(ctx, 'operations.workspace.agenda', { center: fixture.center_a, start: fixture.daily_date, end: fixture.daily_date });
      return Number(result.body.message?.appointments?.find((row: { name: string }) => row.name === fixture.daily_appointments[0])?.cc_performed) }).toBe(1)
    const closedPaid = await api(ctx, 'operations.workspace.agenda', { center: fixture.center_a, start: fixture.daily_date, end: fixture.daily_date })
    const paidRow = closedPaid.body.message.appointments.find((row: { name: string }) => row.name === fixture.daily_appointments[0])
    expect(Number(paidRow.cc_performed)).toBe(1)
    expect(Number(paidRow.cc_paid)).toBe(1)
    const history = await api(ctx, 'operations.workspace.patient_history', { patient: fixture.patient_a, center: fixture.center_a })
    const persistedMethod = String(history.body.message.settlements.find((row: { appointment: string }) => row.appointment === fixture.daily_appointments[0])?.mode_of_payment ?? '')
    if (!paymentMethod) paymentMethod = persistedMethod
    expect(paymentMethod).toBeTruthy()
    expect(persistedMethod).toBe(paymentMethod)
    const replay = await post(ctx, 'operations.lifecycle.close', { appointment: fixture.daily_appointments[0], paid: 1,
      mode_of_payment: paymentMethod, reason: 'Seduta sintetica svolta e pagata' }, csrf!)
    expect(replay.response.ok()).toBeTruthy()
    expect(replay.body.message.replay).toBe(true)
    await page.screenshot({ path: info.outputPath('professional-closed-paid-desktop.png') })

    await page.reload()
    if (!closedPaid.body.message.appointments.find((row: { name: string }) => row.name === fixture.daily_appointments[1])?.cc_performed) {
      await page.locator('.week-event[data-time="08:00"]').click()
      await page.getByRole('button', { name: 'Chiudi seduta' }).click()
      await page.getByRole('textbox', { name: 'Motivo' }).fill('Seduta sintetica svolta non pagata')
      await page.getByRole('button', { name: 'Conferma', exact: true }).click()
      await expect(page.getByText('Sedute svolte')).toBeVisible()
    }
    await expect.poll(async () => { const result = await api(ctx, 'operations.workspace.agenda', { center: fixture.center_a, start: fixture.daily_date, end: fixture.daily_date });
      return Number(result.body.message?.appointments?.find((row: { name: string }) => row.name === fixture.daily_appointments[1])?.cc_performed) }).toBe(1)
    const closedUnpaid = await api(ctx, 'operations.workspace.agenda', { center: fixture.center_a, start: fixture.daily_date, end: fixture.daily_date })
    const unpaidRow = closedUnpaid.body.message.appointments.find((row: { name: string }) => row.name === fixture.daily_appointments[1])
    expect(Number(unpaidRow.cc_performed)).toBe(1)
    expect(Number(unpaidRow.cc_paid)).toBe(0)
    const unauthorizedCorrection = await post(ctx, 'operations.lifecycle.record_settlement', { appointment: fixture.daily_appointments[1], paid: 1,
      mode_of_payment: paymentMethod, reason: 'Tentativo post chiusura' }, csrf!)
    expect(unauthorizedCorrection.response.ok()).toBeFalsy()
    await page.goto('/premium/#Report')
    await page.getByRole('button', { name: 'Report professionisti' }).click()
    await page.getByRole('combobox', { name: 'Professionista report' }).selectOption(fixture.practitioner_a)
    await expect(page.locator('.professional-report')).toContainText('Sedute svolte')
    await expect(page.locator('.professional-report')).toContainText('2')
    await expect(page.locator('.professional-report')).not.toContainText(fixture.practitioner_b)
    const exported = page.waitForEvent('download')
    await page.getByRole('button', { name: 'Esporta CSV' }).click()
    const download = await exported
    expect(download.suggestedFilename()).toBe('centrochange-report-professionista.csv')
    const csv = readFileSync(await download.path(), 'utf8')
    expect(csv).toContain('"Data";"Ora";"Paziente";"Servizio";"Stato"')
    expect(csv).not.toContain(fixture.practitioner_b)
    expect(csv).not.toContain('Compenso')
    await page.screenshot({ path: info.outputPath('professional-report-desktop.png') })
  } finally { await ctx.close(); await other.close() }
})

test('Account professionista: disponibilità propria, assenza e rifiuto del collega', async ({ browser }, info) => {
  test.skip(info.project.name !== 'desktop')
  const ctx = await ctxFor(browser, 'professional_a')
  const manager = await ctxFor(browser, 'manager')
  try {
    const page = await ctx.newPage()
    await page.goto('/premium/#Disponibilit%C3%A0')
    await page.getByRole('combobox', { name: 'Centro' }).selectOption(fixture.center_a)
    await expect(page.getByRole('heading', { name: 'Disponibilità' })).toBeVisible()
    const csrf = await page.locator('meta[name="csrf-token"]').getAttribute('content')
    expect(csrf).toBeTruthy()
    let initial = await api(ctx, 'operations.workspace.schedules', { center: fixture.center_a })
    let initialRow = initial.body.message.find((row: { practitioner: string }) => row.practitioner === fixture.practitioner_a)
    if (!/^12:00/.test(String(initialRow?.time_slots.find((slot: { day: string }) => slot.day === 'Monday')?.to_time))) {
      const reset = await post(ctx, 'scheduling.availability.set_schedule', { practitioner: fixture.practitioner_a,
        center: fixture.center_a, time_slots: [...initialRow.time_slots.filter((slot: { day: string }) => slot.day !== 'Monday'),
          { day: 'Monday', from_time: '09:00:00', to_time: '12:00:00' }], reason: 'Ripristino orario sintetico di prova',
        expected_modified: initialRow.modified }, csrf!)
      expect(reset.response.ok(), 'restore owned schedule fixture').toBeTruthy()
      initial = await api(ctx, 'operations.workspace.schedules', { center: fixture.center_a })
      initialRow = initial.body.message.find((row: { practitioner: string }) => row.practitioner === fixture.practitioner_a)
      await page.getByRole('button', { name: 'Aggiorna', exact: true }).click()
      await expect(page.locator('.schedule-grid')).toContainText('09:00 – 12:00')
    }
    expect(initialRow?.time_slots.find((slot: { day: string }) => slot.day === 'Monday')?.to_time).toMatch(/^12:00/)
    const early = await post(ctx, 'scheduling.booking.book', { patient: fixture.availability_patient,
      practitioner: fixture.practitioner_a, center: fixture.center_a, appointment_type: fixture.appointment_type,
      appointment_date: '2099-02-02', appointment_time: '11:00:00',
      request_key: `${fixture.tag}-availability-before`, reason: 'Verifica disponibilità prima della modifica' }, csrf!)
    expect(early.response.ok(), 'booking before schedule change').toBeTruthy()
    await page.getByRole('button', { name: 'Modifica orario' }).click()
    const dialog = page.getByRole('dialog', { name: 'Modifica disponibilità' })
    await expect(dialog.getByRole('combobox', { name: 'Professionista' })).toHaveCount(1)
    await expect(dialog.getByRole('combobox', { name: 'Professionista' }).locator('option')).toHaveCount(1)
    await dialog.locator('input[type="time"]').nth(1).fill('11:00')
    await dialog.getByRole('textbox', { name: 'Motivo' }).fill('Aggiornamento orario sintetico proprio')
    await dialog.getByRole('button', { name: 'Conferma' }).click()
    await expect(page.getByText('Orario aggiornato.')).toBeVisible()
    const own = await api(ctx, 'operations.workspace.schedules', { center: fixture.center_a })
    expect(own.response.ok()).toBeTruthy()
    expect((own.body.message ?? []).every((row: { practitioner: string }) => row.practitioner === fixture.practitioner_a)).toBe(true)
    expect(own.body.message.find((row: { practitioner: string }) => row.practitioner === fixture.practitioner_a)
      ?.time_slots.find((slot: { day: string }) => slot.day === 'Monday')?.to_time).toMatch(/^11:00/)
    const today = new Intl.DateTimeFormat('en-CA', { timeZone: 'Europe/Rome', year: 'numeric', month: '2-digit', day: '2-digit' }).format(new Date())
    const audit = await api(manager, 'security.audit_view.events', { start: today, end: today, event_type: 'SCHEDULE_CHANGED',
      reference: String(initialRow.name) })
    expect(audit.response.ok()).toBeTruthy()
    expect(audit.body.message.events.some((event: { reason: string }) => event.reason === 'Aggiornamento orario sintetico proprio')).toBe(true)
    const late = await post(ctx, 'scheduling.booking.book', { patient: fixture.availability_patient,
      practitioner: fixture.practitioner_a, center: fixture.center_a, appointment_type: fixture.appointment_type,
      appointment_date: '2099-02-09', appointment_time: '11:00:00',
      request_key: `${fixture.tag}-availability-after`, reason: 'Verifica disponibilità dopo la modifica' }, csrf!)
    expect(late.response.ok(), 'booking rejected after schedule change').toBeFalsy()
    const forbidden = await post(ctx, 'scheduling.availability.set_schedule', {
      practitioner: fixture.practitioner_b, center: fixture.center_a,
      time_slots: [{ day: 'Monday', from_time: '09:00:00', to_time: '11:00:00' }], reason: 'Tentativo altrui'
    }, csrf!)
    expect(forbidden.response.ok()).toBeFalsy()
    const absence = await post(ctx, 'scheduling.availability.create_absence', {
      practitioner: fixture.practitioner_a, center: fixture.center_a, start_date: '2099-01-26', end_date: '2099-01-26',
      start_time: '09:00:00', end_time: '10:00:00', reason: 'Assenza sintetica propria'
    }, csrf!)
    expect(absence.response.ok()).toBeTruthy()
    await page.reload()
    await expect(page.getByRole('button', { name: 'Annulla assenza' })).toBeVisible()
    await page.screenshot({ path: info.outputPath('professional-availability-desktop.png') })
    await page.getByRole('button', { name: 'Annulla assenza' }).click()
    await page.getByRole('dialog', { name: 'Annulla assenza' }).getByRole('textbox', { name: 'Motivo' }).fill('Fine assenza sintetica')
    await page.getByRole('dialog', { name: 'Annulla assenza' }).getByRole('button', { name: 'Conferma' }).click()
    await expect(page.getByText('Assenza annullata.')).toBeVisible()
  } finally { await ctx.close(); await manager.close() }
})

test('Account professionista: nota privata append-only e notifica personale senza leak', async ({ browser }, info) => {
  test.skip(info.project.name !== 'desktop')
  const professional = await ctxFor(browser, 'professional_a')
  const manager = await ctxFor(browser, 'manager')
  const other = await ctxFor(browser, 'professional_b')
  try {
    const page = await professional.newPage()
    await page.goto('/premium/#Pazienti')
    await page.getByRole('combobox', { name: 'Centro' }).selectOption(fixture.center_a)
    await expect(page.locator('tbody tr')).not.toHaveCount(0)
    await page.getByRole('textbox', { name: 'Cerca pazienti' }).fill(fixture.patient_a)
    await expect(page.locator('tbody tr')).toHaveCount(1)
    await page.locator('tbody tr').first().click()
    const drawer = page.getByRole('dialog')
    await expect(drawer.getByText('Note professionali riservate')).toBeVisible()
    const text = `${fixture.tag} nota privata nuova ${Date.now()}`
    await drawer.getByRole('textbox', { name: 'Nuova nota organizzativa' }).fill(text)
    await drawer.getByRole('checkbox', { name: 'Nota professionale riservata' }).check()
    await drawer.getByRole('button', { name: 'Aggiungi nota' }).click()
    await expect(drawer.getByText(text)).toBeVisible()
    let note: { name: string } | undefined
    await expect.poll(async () => { const history = await api(professional, 'operations.workspace.patient_history', { patient: fixture.patient_a, center: fixture.center_a })
      expect(history.response.ok()).toBeTruthy()
      note = history.body.message.private_notes.find((row: { content: string }) => row.content === text)
      return !!note?.name }).toBe(true)
    const csrf = await page.locator('meta[name="csrf-token"]').getAttribute('content')
    const revision = await post(professional, 'operations.notes.add_note', { patient: fixture.patient_a, center: fixture.center_a,
      content: text + ' rettificata', private: 1, corrects: note!.name }, csrf!)
    expect(revision.response.ok()).toBeTruthy()
    const after = await api(professional, 'operations.workspace.patient_history', { patient: fixture.patient_a, center: fixture.center_a })
    expect(after.body.message.private_notes.some((row: { name: string; corrects: string }) => row.name === revision.body.message.name && row.corrects === note!.name)).toBe(true)
    for (const ctx of [manager, other]) {
      const denied = await api(ctx, 'frappe.client.get', { doctype: 'CC Private Note', name: note!.name })
      expect(denied.response.ok()).toBeFalsy()
    }
    await page.goto('/premium/#Notifiche')
    await expect(page.getByRole('heading', { name: 'Notifiche', exact: true })).toBeVisible()
    await expect(page.locator('tbody')).toContainText('Hai sedute da chiudere oggi.')
    const personal = await api(professional, 'frappe.client.get_list', { doctype: 'Notification Log', fields: '["name","subject"]' })
    expect(personal.body.message.map((row: { name: string }) => row.name)).toContain(fixture.reminder_log)
    const foreign = await api(other, 'frappe.client.get_list', { doctype: 'Notification Log', fields: '["name","subject"]' })
    expect(foreign.body.message.map((row: { name: string }) => row.name)).not.toContain(fixture.reminder_log)
    const direct = await api(other, 'frappe.client.get', { doctype: 'Notification Log', name: fixture.reminder_log })
    expect(direct.response.ok()).toBeFalsy()
    await page.screenshot({ path: info.outputPath('professional-private-notification-desktop.png') })
  } finally { await professional.close(); await manager.close(); await other.close() }
})

test('Account professionista mobile: Agenda, disponibilità, note, report e notifiche leggibili', async ({ browser }, info) => {
  test.skip(info.project.name !== 'mobile')
  const ctx = await ctxFor(browser, 'professional_a')
  try {
    const page = await ctx.newPage()
    for (const [route, heading, shot] of [
      ['Agenda', 'Agenda', 'agenda'], ['Disponibilità', 'Disponibilità', 'disponibilita'],
      ['Pazienti', 'Pazienti', 'pazienti'], ['Report', 'Report', 'report'],
      ['Notifiche', 'Notifiche', 'notifiche']
    ]) {
      await page.goto('/premium/#' + encodeURIComponent(route))
      await expect(page.getByRole('heading', { name: heading, exact: true }).first()).toBeVisible()
      expect(await page.evaluate(() => document.documentElement.scrollWidth), route).toBeLessThanOrEqual(390)
      if (route === 'Notifiche') await expect(page.locator('tbody')).toContainText('Hai sedute da chiudere oggi.')
      await page.screenshot({ path: info.outputPath(`professional-${shot}-mobile.png`) })
    }
  } finally { await ctx.close() }
})

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
    const testKey = `${fixture.tag}-edit-${Date.now()}`
    const payload = { center: fixture.center_a, name: fixture.practitioner_a, first_name: source.first_name,
      last_name: source.last_name === 'Professionista' ? 'Verifica' : 'Professionista',
      expected_version: source.modified, request_key: testKey, reason: `AUDIT-05 fixture isolata ${testKey}` }
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
    const edits = (audit.body.message?.events ?? []).filter((event: { reason: string }) => event.reason === payload.reason)
    expect(edits).toHaveLength(1)
    expect(edits[0].actor).toBeTruthy()
    const stale = await post({ ...payload, request_key: testKey + '-stale' })
    expect(stale.response.ok()).toBeFalsy()
    const after = await api(manager, 'operations.profiles.practitioner_detail', { center: fixture.center_a, name: fixture.practitioner_a })
    expect(after.body.message.last_name).toBe(payload.last_name)
    expect(after.body.message.user_id).toBe(source.user_id)
    const forbidden = await post({ ...payload, request_key: testKey + '-extra', supplier: 'NO' })
    expect(forbidden.response.ok()).toBeFalsy()
    for (const role of ['secretariat', 'professional_a', 'finance', 'accountant'] as Role[]) {
      const ctx = await ctxFor(browser, role)
      try {
        const rolePage = await ctx.newPage()
        await rolePage.goto('/premium/')
        const roleCsrf = await rolePage.locator('meta[name="csrf-token"]').getAttribute('content')
        expect(roleCsrf).toBeTruthy()
        const attempt = await ctx.request.post(method('operations.profiles.practitioner_save'), { data: { ...payload, request_key: testKey + '-' + role }, headers: { 'X-Frappe-CSRF-Token': roleCsrf! } })
        expect(attempt.ok(), `${role} write denied`).toBeFalsy()
      } finally { await ctx.close() }
    }
  } finally { await manager.close() }
})
