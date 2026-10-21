import { expect, test, type Page } from '@playwright/test'

const today = new Intl.DateTimeFormat('en-CA', { timeZone: 'Europe/Rome', year: 'numeric', month: '2-digit', day: '2-digit' }).format(new Date())
const boot = { center: 'CENTRO-A', centers: [{ name: 'CENTRO-A', branch: 'Centro A' }], patients: [{ name: 'PAT-001', patient_name: 'Paziente Sintetico' }], practitioners: [{ name: 'PR-001', practitioner_name: 'Dott.ssa Rossi' }], services: [{ name: 'SERV-001', cc_service_label: 'Prima visita', cc_service_item: 'ITEM-001' }], packages: [], payment_methods: ['Contanti'], roles: ['CC Manager', 'CC Secretariat'] }
const financeBoot = { center: 'CENTRO-A', centers: boot.centers, can_write: true, is_manager: true, customers: [], suppliers: [], accounts: [], practitioners: boot.practitioners, items: [], assignees: [], simulation_only: true, fiscal_verified: false }
const appointment = { name: 'APP-001', patient: 'PAT-001', patient_name: 'Paziente Sintetico', practitioner: 'PR-001', practitioner_name: 'Dott.ssa Rossi', cc_center: 'CENTRO-A', appointment_date: today, appointment_time: '09:00:00', duration: 60, status: 'Open', cc_closure_state: 'Pending', cc_economic_state: 'Due', cc_paid: 0, cc_performed: 0, cc_service_label: 'Prima visita', cc_price_snapshot: 80, cc_currency_snapshot: 'EUR' }

async function mockApi(page: Page, writes: { method: string; body: Record<string, unknown>; headers: Record<string, string> }[] = [], financeAllowed = true) {
  await page.route('**/api/method/**', async route => {
    const req = route.request()
    const method = new URL(req.url()).pathname.split('/api/method/')[1]
    const body = req.method() === 'POST' ? req.postDataJSON() : {}
    if (req.method() === 'POST') writes.push({ method, body, headers: req.headers() })
    let message: unknown = null
    let status = 200
    if (method.endsWith('operations.workspace.bootstrap')) message = boot
    else if (method.endsWith('finance.reporting.bootstrap')) { if (financeAllowed) message = financeBoot; else status = 403 }
    else if (method.endsWith('operations.workspace.agenda')) message = { appointments: [appointment], truncated: false }
    else if (method.endsWith('operations.workspace.patient_search')) message = { patients: boot.patients, truncated: false }
    else if (method.endsWith('operations.workspace.patient_history')) message = { appointments: [appointment], packages: [], organizational_notes: [{ name: 'NOTE-001', content: 'Nota sintetica', creation: today }], private_notes: [], settlements: [] }
    else if (method.endsWith('operations.workspace.schedules')) message = [{ name: 'SCHED-001', practitioner: 'PR-001', time_slots: [{ day: 'Monday', from_time: '09:00:00', to_time: '18:00:00' }], absences: [] }]
    else if (method.endsWith('operations.reporting.summary')) message = { currencies: { EUR: { sessions: 1, performed: 0, due: 1, due_snapshot_amount: 80 } }, truncated: false }
    else if (method.endsWith('finance.reporting.summary')) message = { totals: { revenue_net: 600, collected: 400, receivable_outstanding: 200, purchase_net: 250, payable_outstanding: 80, expected_compensation: 120, unresolved_expectations: 0, sessions: 4 }, sales_invoices: [], purchase_invoices: [], scope_note: 'Dati sintetici.' }
    else if (method.endsWith('finance.reporting.records')) message = [{ name: 'INV-001', posting_date: today, customer: 'Cliente Sintetico', grand_total: 80, outstanding_amount: 20, docstatus: 1 }]
    else if (method.endsWith('finance.receivables.position')) message = { name: 'INV-001', docstatus: 1, total: 80, outstanding: 20, currency: 'EUR' }
    else if (method.endsWith('finance.receivables.candidates')) message = { candidates: [{ name: 'APP-001', patient: 'PAT-001' }], period: [today, today] }
    else if (method.endsWith('finance.banking.candidates')) message = { state: 'Candidate', invoices: [{ name: 'INV-001', outstanding_amount: 20 }] }
    else if (method.endsWith('finance.admin_queue.list_items') || method.endsWith('finance.fiscal.records')) message = []
    else if (method.endsWith('operations.workspace.management_context')) message = { memberships: [{ user: 'synthetic@example.invalid', active: 1 }], users: [{ name: 'synthetic@example.invalid', full_name: 'Utente Sintetico' }], practitioners: boot.practitioners }
    else if (method.endsWith('scheduling.public_booking.available_slots')) message = { route: 'Marco', service: 'Primo incontro', duration: 60, price: 80, currency: 'EUR', slots: [{ date: today, time: '10:00:00' }] }
    else if (method.endsWith('scheduling.public_booking.first_meeting')) message = { name: 'APP-PUBLIC-001', confirmation: { state: 'Simulated Sent' } }
    else if (method.endsWith('frappe.client.get_list')) message = []
    else if (req.method() === 'POST') message = { name: 'SYNTHETIC-NEW' }
    else status = 404
    await route.fulfill({ status, contentType: 'application/json', body: JSON.stringify(status === 200 ? { message } : { exc: 'PermissionError' }) })
  })
}

test('agenda desktop: shell, calendario, dettaglio e prenotazione con CSRF', async ({ page }, testInfo) => {
  const writes: { method: string; body: Record<string, unknown>; headers: Record<string, string> }[] = []
  await mockApi(page, writes)
  const errors: string[] = []
  page.on('pageerror', error => errors.push(error.message))
  await page.goto('./')
  await expect(page.getByRole('heading', { name: 'Agenda' })).toBeVisible()
  await expect(page.getByText('Paziente Sintetico').first()).toBeVisible()
  await page.screenshot({ path: `test-results/${testInfo.project.name}-agenda.png`, fullPage: true })
  await page.getByText('Paziente Sintetico').first().click()
  await expect(page.getByRole('dialog', { name: 'Paziente Sintetico' })).toBeVisible()
  await page.getByRole('button', { name: 'Chiudi', exact: true }).first().click()
  await page.getByRole('button', { name: 'Nuova prenotazione' }).click()
  await expect(page.getByRole('dialog', { name: 'Nuova prenotazione' })).toBeVisible()
  await page.getByRole('dialog', { name: 'Nuova prenotazione' }).getByRole('textbox', { name: 'Motivo' }).fill('Test sintetico')
  await page.getByRole('button', { name: 'Conferma prenotazione' }).click()
  await expect.poll(() => writes.some(w => w.method.endsWith('scheduling.booking.book'))).toBe(true)
  const booking = writes.find(w => w.method.endsWith('scheduling.booking.book'))!
  expect(booking.body.center).toBe('CENTRO-A')
  expect(booking.headers['x-frappe-csrf-token']).toBe('synthetic-test-token')
  expect(errors).toEqual([])
})

test('navigazione finanza, pazienti e report usa endpoint di dominio', async ({ page }, testInfo) => {
  await mockApi(page)
  await page.goto('./')
  if (page.viewportSize()?.width && page.viewportSize()!.width < 760) await page.getByRole('button', { name: 'Apri menu' }).click()
  await page.getByRole('button', { name: 'Finanza', exact: true }).click()
  await expect(page.getByRole('heading', { name: 'Finanza' })).toBeVisible()
  await expect(page.getByText('600,00 €')).toBeVisible()
  await expect(page.locator('.finance-panel .date-input').first()).toHaveValue(/\d{2}\/\d{2}\/\d{4}/)
  if (testInfo.project.name === 'desktop') await page.screenshot({ path: 'test-results/finance-desktop.png', fullPage: true })
  await page.getByRole('tab', { name: 'Fatture pazienti' }).click()
  await expect(page.getByText('INV-001')).toBeVisible()
  if (page.viewportSize()?.width && page.viewportSize()!.width < 760) await page.getByRole('button', { name: 'Apri menu' }).click()
  await page.getByRole('button', { name: 'Pazienti', exact: true }).click()
  await expect(page.getByRole('heading', { name: 'Pazienti', exact: true })).toBeVisible()
  if (page.viewportSize()?.width && page.viewportSize()!.width < 760) await page.getByRole('button', { name: 'Apri menu' }).click()
  await page.getByRole('button', { name: 'Report', exact: true }).click()
  await expect(page.getByRole('heading', { name: 'Report' })).toBeVisible()
})

test('mobile: menu, Agenda e Finanza senza overflow orizzontale', async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== 'mobile')
  await mockApi(page)
  await page.goto('./')
  await expect(page.getByRole('heading', { name: 'Agenda' })).toBeVisible()
  await page.screenshot({ path: 'test-results/mobile-agenda.png', fullPage: true })
  await page.getByRole('button', { name: 'Apri menu' }).click()
  await page.getByRole('button', { name: 'Finanza', exact: true }).click()
  await expect(page.getByRole('heading', { name: 'Finanza' })).toBeVisible()
  await page.waitForTimeout(250)
  await page.screenshot({ path: 'test-results/mobile-finanza.png', fullPage: true })
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(390)
})

test('ruolo senza accesso finanza non vede la sezione', async ({ page }) => {
  await mockApi(page, [], false)
  await page.goto('./')
  await expect(page.getByRole('heading', { name: 'Agenda' })).toBeVisible()
  await expect(page.getByRole('button', { name: 'Finanza', exact: true })).toHaveCount(0)
})

test('hash diretto non apre finanza senza ruolo; errore API visibile', async ({ page }) => {
  await mockApi(page, [], false)
  await page.goto('./#Finanza')
  await expect(page.getByRole('heading', { name: 'Agenda' })).toBeVisible()
  await expect(page.getByRole('heading', { name: 'Finanza' })).toHaveCount(0)
})

test('date umane e cambio ora Europe/Rome conservano giorno canonico', async ({ page }) => {
  await mockApi(page)
  await page.goto('./')
  const result = await page.evaluate(async () => {
    const modulePath = new URL('src/api.ts', location.href).href
    const api = await import(modulePath)
    return [api.displayDate('2026-03-29'), api.displayDate('2026-10-25'), api.romeDateAt(new Date('2026-03-29T00:30:00Z')), api.romeDateAt(new Date('2026-03-29T01:30:00Z')), api.romeDateAt(new Date('2026-10-25T00:30:00Z'))]
  })
  expect(result).toEqual(['29/03/2026', '25/10/2026', '2026-03-29', '2026-03-29', '2026-10-25'])
})

test('navigazione non chiama CRUD generico né domini terzi', async ({ page }) => {
  await mockApi(page)
  const urls: string[] = []
  page.on('request', request => urls.push(request.url()))
  await page.goto('./')
  await expect(page.getByRole('heading', { name: 'Agenda' })).toBeVisible()
  expect(urls.filter(url => url.includes('/api/resource/'))).toEqual([])
  expect(urls.filter(url => !url.startsWith('http://127.0.0.1:5182/'))).toEqual([])
})

test('data italiana non valida blocca prenotazione e ISO valido raggiunge API', async ({ page }) => {
  const writes: { method: string; body: Record<string, unknown>; headers: Record<string, string> }[] = []
  await mockApi(page, writes)
  await page.goto('./')
  await page.getByRole('button', { name: 'Nuova prenotazione' }).click()
  const dialog = page.getByRole('dialog', { name: 'Nuova prenotazione' })
  await dialog.getByRole('textbox', { name: 'Motivo' }).fill('Controllo data sintetica')
  await dialog.locator('.date-input').fill('31/02/2026')
  await dialog.getByRole('button', { name: 'Conferma prenotazione' }).click()
  expect(writes.filter(w => w.method.endsWith('scheduling.booking.book'))).toHaveLength(0)
  await dialog.locator('.date-input').fill('29/03/2026')
  await dialog.getByRole('button', { name: 'Conferma prenotazione' }).click()
  await expect.poll(() => writes.filter(w => w.method.endsWith('scheduling.booking.book')).length).toBe(1)
  expect(writes.at(-1)?.body.appointment_date).toBe('2026-03-29')
})

test('pagamento fattura invoca servizio ERPNext con CSRF e chiave idempotente', async ({ page }) => {
  const writes: { method: string; body: Record<string, unknown>; headers: Record<string, string> }[] = []
  await mockApi(page, writes)
  await page.goto('./#Finanza')
  await expect(page.getByRole('heading', { name: 'Finanza' })).toBeVisible()
  await page.getByRole('tab', { name: 'Fatture pazienti' }).click()
  await page.getByText('INV-001').click()
  const drawer = page.getByRole('dialog', { name: 'INV-001' })
  await drawer.getByRole('button', { name: 'Registra pagamento' }).click()
  await drawer.getByRole('textbox', { name: 'Motivo' }).fill('Pagamento sintetico')
  await drawer.getByRole('button', { name: 'Conferma operazione' }).click()
  await expect.poll(() => writes.some(w => w.method.endsWith('finance.receivables.pay'))).toBe(true)
  const payment = writes.find(w => w.method.endsWith('finance.receivables.pay'))!
  expect(payment.body.name).toBe('INV-001')
  expect(payment.body.request_key).toMatch(/^[a-f0-9]{32}$/)
  expect(payment.headers['x-frappe-csrf-token']).toBe('synthetic-test-token')
})

test('nuova fattura usa bridge economico e bozza ERPNext con date canoniche', async ({ page }) => {
  const writes: { method: string; body: Record<string, unknown>; headers: Record<string, string> }[] = []
  await mockApi(page, writes)
  await page.goto('./#Finanza')
  await expect(page.getByRole('heading', { name: 'Finanza' })).toBeVisible()
  await page.getByRole('tab', { name: 'Fatture pazienti' }).click()
  await page.getByRole('button', { name: 'Nuova operazione' }).click()
  const dialog = page.getByRole('dialog', { name: 'Crea fattura paziente' })
  await dialog.getByRole('combobox', { name: 'Seduta da fatturare' }).selectOption('APP-001')
  await dialog.getByRole('textbox', { name: 'Motivo' }).fill('Fattura sintetica')
  await dialog.getByRole('button', { name: 'Conferma', exact: true }).click()
  await expect.poll(() => writes.filter(w => w.method.endsWith('finance.receivables.draft')).length).toBe(1)
  expect(writes.map(w => w.method).filter(x => x.endsWith('finance.bridge.capture') || x.endsWith('finance.receivables.draft'))).toEqual(['centrochange_core.finance.bridge.capture', 'centrochange_core.finance.receivables.draft'])
  const draft = writes.find(w => w.method.endsWith('finance.receivables.draft'))!
  expect(draft.body.sources).toEqual(['SYNTHETIC-NEW'])
  expect(draft.body.posting_date).toMatch(/^\d{4}-\d{2}-\d{2}$/)
  expect(draft.body.request_key).toMatch(/^[a-f0-9]{32}$/)
})

test('primo incontro pubblico usa solo slot e servizio guest', async ({ page }, testInfo) => {
  const writes: { method: string; body: Record<string, unknown>; headers: Record<string, string> }[] = []
  await mockApi(page, writes)
  await page.goto('./public.html')
  await expect(page.getByRole('heading', { name: 'Iniziamo da qui, insieme.' })).toBeVisible()
  await page.getByRole('button', { name: 'Cerca disponibilità' }).click()
  await expect(page.getByRole('radio', { name: new RegExp('10:00') })).toBeVisible()
  await page.screenshot({ path: `test-results/${testInfo.project.name}-first-meeting.png`, fullPage: true })
  await page.getByRole('radio', { name: new RegExp('10:00') }).click()
  await page.getByRole('textbox', { name: /^Nome/ }).fill('SYNTHETIC Ada')
  await page.getByRole('textbox', { name: 'Cognome' }).fill('Test')
  await page.getByRole('textbox', { name: 'Email' }).fill('ada@example.invalid')
  await page.getByRole('combobox', { name: 'Sesso' }).selectOption('Female')
  await page.getByRole('button', { name: 'Conferma primo incontro' }).click()
  await expect(page.getByRole('heading', { name: 'Prenotazione registrata' })).toBeVisible()
  const booking = writes.find(w => w.method.endsWith('scheduling.public_booking.first_meeting'))!
  expect(booking.body).not.toHaveProperty('patient')
  expect(booking.body.appointment_date).toBe(today)
  expect(booking.headers['x-frappe-csrf-token']).toBe('synthetic-test-token')
})

test('rettifica nota conserva riferimento alla versione precedente', async ({ page }) => {
  const writes: { method: string; body: Record<string, unknown>; headers: Record<string, string> }[] = []
  await mockApi(page, writes)
  await page.goto('./')
  await page.getByText('Paziente Sintetico').first().click()
  const drawer = page.getByRole('dialog', { name: 'Paziente Sintetico' })
  await drawer.getByRole('tab', { name: 'Note' }).click()
  await drawer.getByRole('button', { name: 'Rettifica' }).click()
  await drawer.getByRole('textbox', { name: 'Rettifica nota' }).fill('Nota sintetica rettificata')
  await drawer.getByRole('button', { name: 'Registra rettifica' }).click()
  await expect.poll(() => writes.some(w => w.method.endsWith('operations.notes.add_note'))).toBe(true)
  const note = writes.find(w => w.method.endsWith('operations.notes.add_note'))!
  expect(note.body.corrects).toBe('NOTE-001')
  expect(note.body.private).toBe(0)
})

test('gestione accessi invoca servizio membership auditato', async ({ page }) => {
  const writes: { method: string; body: Record<string, unknown>; headers: Record<string, string> }[] = []
  await mockApi(page, writes)
  await page.goto('./#Gestione%20accessi')
  await expect(page.getByRole('heading', { name: 'Gestione accessi' })).toBeVisible()
  await page.getByRole('button', { name: 'Appartenenza', exact: true }).click()
  const dialog = page.getByRole('dialog', { name: 'Appartenenza al centro' })
  await dialog.getByRole('combobox', { name: 'Utente' }).selectOption('synthetic@example.invalid')
  await dialog.getByRole('textbox', { name: 'Motivo' }).fill('Revisione sintetica')
  await dialog.getByRole('button', { name: 'Conferma' }).click()
  await expect.poll(() => writes.some(w => w.method.endsWith('security.lifecycle.set_membership'))).toBe(true)
  expect(writes.at(-1)?.body.center).toBe('CENTRO-A')
})

test('sweep grafico delle sezioni operative e amministrative', async ({ page }, testInfo) => {
  await mockApi(page)
  const sections = ['Pazienti', 'Disponibilità', 'Report', 'Finanza', 'Gestione accessi', 'Notifiche']
  await page.goto('./')
  await expect(page.getByRole('heading', { name: 'Agenda', exact: true })).toBeVisible()
  for (const section of sections) {
    await page.evaluate(value => { location.hash = encodeURIComponent(value) }, section)
    await expect(page.getByRole('heading', { name: section, exact: true })).toBeVisible()
    await expect(page.locator('.panel-loading')).toHaveCount(0)
    const slug = section.toLowerCase().replaceAll(' ', '-')
    await page.screenshot({ path: `test-results/${testInfo.project.name}-${slug}.png`, fullPage: true })
  }
})
