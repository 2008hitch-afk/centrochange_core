import { expect, test, type Page } from '@playwright/test'

const today = new Intl.DateTimeFormat('en-CA', { timeZone: 'Europe/Rome', year: 'numeric', month: '2-digit', day: '2-digit' }).format(new Date())
const todayItalian = `${today.slice(8, 10)}/${today.slice(5, 7)}/${today.slice(0, 4)}`
const boot = { center: 'CENTRO-A', centers: [{ name: 'CENTRO-A', branch: 'Centro A' }], patients: [{ name: 'PAT-001', patient_name: 'Paziente Sintetico' }], practitioners: [{ name: 'PR-001', practitioner_name: 'Dott.ssa Rossi' }], services: [{ name: 'SERV-001', cc_service_label: 'Prima visita', cc_service_item: 'ITEM-001', cc_price_snapshot: 80, cc_currency_snapshot: 'EUR', duration: 60 }], packages: [], payment_methods: ['Contanti'], roles: ['CC Manager', 'CC Secretariat'] }
const financeBoot = { center: 'CENTRO-A', centers: boot.centers, can_write: true, is_manager: true, customers: [], suppliers: [], accounts: [{ name: 'EXP-001', root_type: 'Expense', is_group: 0, disabled: 0 }, { name: 'TAX-001', account_type: 'Tax', is_group: 0, disabled: 0 }], practitioners: boot.practitioners, items: [{ name: 'ITEM-001', item_name: 'Prima visita', is_purchase_item: 1, disabled: 0, is_stock_item: 0 }], assignees: [], simulation_only: true, fiscal_verified: false }
const appointment = { name: 'APP-001', patient: 'PAT-001', patient_name: 'Paziente Sintetico', practitioner: 'PR-001', practitioner_name: 'Dott.ssa Rossi', cc_center: 'CENTRO-A', appointment_date: today, appointment_time: '09:00:00', duration: 60, status: 'Open', cc_closure_state: 'Pending', cc_economic_state: 'Due', cc_paid: 0, cc_performed: 0, cc_service_label: 'Prima visita', cc_price_snapshot: 80, cc_currency_snapshot: 'EUR' }

test('AUDIT-02 polish: nomi disponibili, fallback trasparenti e ricerca A/B senza cambiare ID', async ({ page }, info) => {
  const pageErrors: string[] = []
  page.on('pageerror', error => pageErrors.push(error.message))
  const centers = [
    { name: 'CC-HTTP-UAT0000001 A', branch: 'CC-HTTP-UAT0000001 A' },
    { name: 'CC-HTTP-G2NAV161AA B', branch: 'CC-HTTP-G2NAV161AA B' }
  ]
  const patientA = { name: 'CC-HTTP-UAT0000001 PA', patient_name: 'Paziente di prova A' }
  const patientB = { name: 'CC-HTTP-G2NAV161AA PB', patient_name: 'CC-HTTP-G2NAV161AA B' }
  const professionalA = { name: 'CC-HTTP-UAT0000001 PR', practitioner_name: 'Dott.ssa Maria Rossi' }
  const professionalB = { name: 'CC-HTTP-G2NAV161AA PR', practitioner_name: 'CC-HTTP-G2NAV161AA b' }
  const professionalC = { name: 'CC-HTTP-G2NAV161AA PC', practitioner_name: 'CC-HTTP-G2NAV161AA c' }
  const sessionA = { ...appointment, name: 'CC-HTTP-UAT0000001 APP', patient: patientA.name,
    patient_name: patientA.patient_name, practitioner: professionalA.name, practitioner_name: professionalA.practitioner_name,
    cc_center: centers[0].name, cc_service_label: 'CC-HTTP-UAT0000001 Visita' }
  await mockApi(page, [], false)
  await page.route('**/api/method/centrochange_core.operations.workspace.*', async route => {
    const request = route.request()
    const url = new URL(request.url())
    const center = url.searchParams.get('center') || centers[0].name
    const inB = center === centers[1].name
    let message: unknown
    if (url.pathname.endsWith('workspace.bootstrap')) message = {
      ...boot, center, centers, patients: [inB ? patientB : patientA],
      practitioners: inB ? [professionalB, professionalC] : [professionalA],
      demo_labels: inB ? {} : { [centers[0].name]: 'Centro A', [sessionA.cc_service_label]: 'Servizio 1' }
    }
    else if (url.pathname.endsWith('workspace.agenda')) message = { appointments: inB ? [] : [sessionA], truncated: false }
    else if (url.pathname.endsWith('workspace.patient_search')) message = {
      patients: [inB ? patientB : patientA], truncated: false
    }
    else if (url.pathname.endsWith('workspace.patient_history')) message = {
      appointments: inB ? [] : [sessionA], packages: [], private_notes: [], settlements: [],
      organizational_notes: inB ? [] : [{ name: 'NOTE-A', content: 'Riferimento CC-HTTP-UAT0000001 A',
        creation: today + ' 11:00:00', authored_by: 'cc-uat@example.invalid', corrects: null }]
    }
    else return route.fallback()
    await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ message }) })
  })
  await page.goto('./')
  await expect(page).toHaveTitle(/Centro Change/)
  const selector = page.locator('.center-selector select')
  await expect(selector.locator('option').first()).toHaveText('Centro A')
  await expect(selector.locator('option').last()).toHaveText('Centro di prova B')
  await expect(page.locator('.week-professional strong')).toHaveText('Dott.ssa Maria Rossi')
  await expect(page.locator('.week-row')).toHaveAttribute('data-practitioner', professionalA.name)
  await page.screenshot({ path: info.outputPath('polish-agenda-a.png'), fullPage: true })

  if (info.project.name === 'mobile') await page.getByRole('button', { name: 'Apri ricerca pazienti' }).click()
  await page.getByRole('combobox', { name: 'Ricerca globale pazienti' }).fill('Paziente di prova A')
  await page.getByRole('option', { name: 'Paziente di prova A' }).click()
  const drawer = page.getByRole('dialog')
  await expect(drawer).toContainText('Paziente di prova A')
  await expect(drawer.getByText('Servizio 1')).toBeVisible()
  await expect(drawer).toContainText('Da chiudere')
  await expect(drawer).not.toContainText('Pending')
  await expect(drawer.getByText('Codice demo:')).toHaveCount(0)
  // This is literal test note content, not a presentation mapping to rewrite.
  await expect(drawer).toContainText('Riferimento CC-HTTP-UAT0000001 A')
  await page.screenshot({ path: info.outputPath('polish-patient-a.png'), fullPage: true })
  await drawer.getByRole('button', { name: 'Chiudi' }).click()

  await selector.selectOption(centers[1].name)
  await expect(selector).toHaveValue(centers[1].name)
  await openSection(page, 'Agenda')
  await expect(page.locator('.week-professional strong')).toHaveText(['Professionista di prova B', 'Professionista di prova C'])
  await expect(page.locator('.week-row')).toHaveCount(2)
  await expect(page.locator('.week-row').first()).toHaveAttribute('data-practitioner', professionalB.name)
  await page.screenshot({ path: info.outputPath('polish-agenda-b.png'), fullPage: true })
  await openSection(page, 'Pazienti')
  await expect(page.locator('tbody')).toContainText('Paziente di prova B')
  await expect(page.locator('tbody')).not.toContainText('Paziente di prova A')
  await page.screenshot({ path: info.outputPath('polish-center-b.png'), fullPage: true })
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(page.viewportSize()!.width)
  expect(pageErrors).toEqual([])
})

async function mockApi(page: Page, writes: { method: string; body: Record<string, unknown>; headers: Record<string, string> }[] = [], financeAllowed = true, appointmentState: Partial<typeof appointment> = {}, bootState: Partial<typeof boot> = {}, agendaRows: typeof appointment[] | null = null, financeState: Partial<typeof financeBoot> = {}, opsAllowed = true) {
  await page.route('**/api/method/**', async route => {
    const req = route.request()
    const method = new URL(req.url()).pathname.split('/api/method/')[1]
    const body = req.method() === 'POST' ? req.postDataJSON() : {}
    if (req.method() === 'POST') writes.push({ method, body, headers: req.headers() })
    let message: unknown = null
    let status = 200
    if (method.endsWith('operations.workspace.bootstrap')) { if (opsAllowed) message = { ...boot, ...bootState }; else status = 403 }
    else if (method.endsWith('finance.reporting.bootstrap')) { if (financeAllowed) message = { ...financeBoot, ...financeState }; else status = 403 }
    else if (method.endsWith('operations.workspace.agenda')) message = { appointments: agendaRows ?? [{ ...appointment, ...appointmentState }], truncated: false }
    else if (method.endsWith('operations.profiles.practitioner_detail')) message = { name: 'PR-001', practitioner_name: 'Dott.ssa Rossi', status: 'Active' }
    else if (method.endsWith('operations.workspace.patient_search')) message = { patients: boot.patients, truncated: false }
    else if (method.endsWith('operations.workspace.patient_history')) message = { appointments: [{ ...appointment, ...appointmentState }], packages: [], organizational_notes: [{ name: 'NOTE-002', content: 'Nota sintetica rettificata', creation: today + ' 12:00:00', authored_by: 'direzione@example.invalid', corrects: 'NOTE-001' }, { name: 'NOTE-001', content: 'Nota sintetica', creation: today + ' 11:00:00', authored_by: 'direzione@example.invalid', corrects: null }], private_notes: [], settlements: [] }
    else if (method.endsWith('operations.workspace.schedules')) message = [{ name: 'SCHED-001', practitioner: 'PR-001', time_slots: [{ day: 'Monday', from_time: '09:00:00', to_time: '18:00:00' }], absences: [] }]
    else if (method.endsWith('operations.reporting.summary')) message = { currencies: { EUR: { sessions: 1, performed: 0, due: 1, due_snapshot_amount: 80 } }, truncated: false }
    else if (method.endsWith('finance.reporting.summary')) message = { totals: { revenue_net: 600, collected: 400, receivable_outstanding: 200, purchase_net: 250, payable_outstanding: 80, expected_compensation: 120, unresolved_expectations: 0, sessions: 4 }, sales_invoices: [], purchase_invoices: [], scope_note: 'Dati sintetici.' }
    else if (method.endsWith('finance.patient_reporting.patient_view')) message = new URL(req.url()).searchParams.has('key')
      ? { key: 'CUS-001', customer_label: 'Soggetto sintetico', state: 'Scaduto', counts: { sessions: 1, performed: 1 }, totals: { invoiced: 80, collected: 60, outstanding: 20, overdue: 20, open_invoices: 1 }, next_due_date: today, blocked: false, deferred: true, sessions: [{ name: 'APP-001', appointment_date: today, patient_label: 'Paziente Sintetico', cc_service_label: 'Prima visita', category: 'performed' }], invoices: [{ name: 'INV-001', posting_date: today, grand_total: 80 }], payments: [{ name: 'PAY-001', posting_date: today, collected_amount: 60 }], open_invoices: [{ name: 'INV-001', outstanding_amount: 20, original_due_date: today, effective_due_date: today, overdue: true }], scope_note: 'Dati sintetici.' }
      : { rows: [{ key: 'CUS-001', customer_label: 'Soggetto sintetico', state: 'Scaduto', totals: { outstanding: 20, overdue: 20 }, next_due_date: today }] }
    else if (method.endsWith('finance.reporting.professional_view')) message = { practitioner_name: 'Dott.ssa Rossi', counts: { sessions: 1, performed: 1 }, sessions: [{ name: 'APP-001', appointment_date: today, patient_label: 'Paziente Sintetico', cc_service_label: 'Prima visita', category: 'performed' }], economics: { expected: 40, suspended: 0, review: 0, supplier_paid: 10, supplier_invoices: [{ name: 'PUR-001', posting_date: today, grand_total: 40 }], expectations: [{ name: 'EXPECT-001', appointment: 'APP-001', state: 'OK', amount: 40 }], missing_expectation_sessions: [], comparisons: [] }, scope_note: 'Dati sintetici.' }
    else if (method.endsWith('finance.reporting.records')) {
      const doctype = new URL(req.url()).searchParams.get('doctype')
      message = doctype === 'CC Economic Source Link' ? [{ name: 'SOURCE-001', appointment: 'APP-001', session_date: today, practitioner: 'PR-001', price: 80 }]
        : doctype === 'CC Professional Expectation' ? [{ name: 'EXPECT-001', appointment: 'APP-001', appointment_label: 'Seduta sintetica', practitioner: 'PR-001', state: 'SUSPENDED', amount: null, problem: 'Unpaid Threshold Exceeded' }]
        : doctype === 'CC Incoming Invoice' ? [{ name: 'XML-001', invoice_number: 'SYN-001', state: 'Needs Classification', supplier: 'SUP-001', total: 80, purchase_invoice: null }]
        : [{ name: 'INV-001', posting_date: today, customer: 'Cliente Sintetico', supplier: 'SUP-001', grand_total: 80, outstanding_amount: 20, docstatus: 1 }]
    }
    else if (method.endsWith('finance.receivables.position')) message = { name: 'INV-001', docstatus: 1, total: 80, outstanding: 20, currency: 'EUR' }
    else if (method.endsWith('finance.receivables.candidates')) message = { candidates: [{ name: 'APP-001', patient: 'PAT-001' }], period: [today, today] }
    else if (method.endsWith('finance.banking.candidates')) message = { state: 'Candidate', invoices: [{ name: 'INV-001', outstanding_amount: 20 }] }
    else if (method.endsWith('finance.admin_queue.list_items') || method.endsWith('finance.fiscal.records')) message = []
    else if (method.endsWith('operations.workspace.management_context')) message = { memberships: [{ user: 'synthetic@example.invalid', active: 1 }], users: [{ name: 'synthetic@example.invalid', full_name: 'Utente Sintetico' }], practitioners: boot.practitioners }
    else if (method.endsWith('security.audit_view.events')) message = { events: [{ name: 'AUDIT-001', event_type: 'APPOINTMENT_RESCHEDULED', actor: 'direzione@example.invalid', event_time: today + ' 12:00:00', reference_doctype: 'Patient Appointment', reference_name: 'APP-001', reason: 'Riprogrammazione sintetica', before_state: JSON.stringify({ appointment_time: '09:00:00' }), after_state: JSON.stringify({ appointment_time: '10:00:00' }) }], has_more: false, offset: 0 }
    else if (method.endsWith('scheduling.public_booking.available_slots')) message = { route: 'Marco', service: 'Primo incontro', duration: 60, price: 80, currency: 'EUR', slots: [{ date: today, time: '10:00:00' }] }
    else if (method.endsWith('scheduling.public_booking.first_meeting')) message = { name: 'APP-PUBLIC-001', confirmation: { state: 'Simulated Sent' } }
    else if (method.endsWith('frappe.client.get_list')) {
      const doctype = new URL(req.url()).searchParams.get('doctype')
      message = doctype === 'CC Compensation Rule' ? [{ name: 'RULE-001', practitioner: 'PR-001', service_item: 'ITEM-001' }]
        : doctype === 'CC Package Template' ? [{ name: 'TEMPLATE-001', title: 'Pacchetto sintetico', service_item: 'ITEM-001', units: 4, enabled: 1 }]
        : doctype === 'CC Patient Assignment' ? [{ name: 'ASSIGN-001', patient: 'PAT-001', center: 'CENTRO-A', practitioner: 'PR-001', active: 1 }] : []
    }
    else if (method.endsWith('frappe.client.get')) message = { name: 'XML-001', lines_json: JSON.stringify([{ description: 'Visita sintetica', qty: 1, rate: 80 }]), tax_total: 0 }
    else if (req.method() === 'POST') message = { name: 'SYNTHETIC-NEW' }
    else status = 404
    await route.fulfill({ status, contentType: 'application/json', body: JSON.stringify(status === 200 ? { message } : { exc: 'PermissionError' }) })
  })
}

async function openSection(page: Page, name: string) {
  const mobile = (page.viewportSize()?.width ?? 1440) < 760
  if (mobile) await page.getByRole('button', { name: 'Apri menu' }).click()
  await page.getByRole('button', { name, exact: true }).click()
  if (mobile) await expect.poll(() => page.locator('.sidebar').evaluate(el => Math.round(new DOMMatrixReadOnly(getComputedStyle(el).transform).m41))).toBe(-260)
}

const archiveCases = [
  { group: 'Anagrafiche', label: 'Pazienti', first: 'Nome e cognome', sample: 'Persona di prova', fields: { 'Email': 'persona@example.invalid' } },
  { group: 'Anagrafiche', label: 'Professionisti', first: 'Nome professionista', sample: 'Dott. Verdi', fields: { 'Specializzazione': 'Psicologia' } },
  { group: 'Catalogo', label: 'Articoli', first: 'Nome articolo', sample: 'Colloquio di prova', fields: { 'Categoria': 'Servizi' } },
  { group: 'Catalogo', label: 'Tariffe', first: 'Articolo', sample: 'ITEM-001', fields: { 'Listino': 'Listino Centro', 'Importo EUR': '90', 'Valida dal': today } },
  { group: 'Catalogo', label: 'Tipi seduta', first: 'Tipo seduta', sample: 'Colloquio di prova', fields: { 'Durata in minuti': '50' } },
  { group: 'Catalogo', label: 'Servizi del centro', first: 'Nome servizio', sample: 'Servizio di prova', fields: { 'Articolo collegato': 'ITEM-001', 'Durata in minuti': '50', 'Tariffa EUR': '90' } },
  { group: 'Catalogo', label: 'Modelli pacchetto', first: 'Nome modello', sample: 'Percorso di prova', fields: { 'Articolo servizio': 'ITEM-001', 'Sedute incluse': '4' } },
  { group: 'Finanza', label: 'Fatture pazienti', first: 'Cliente', sample: 'Cliente di prova due', fields: { 'Data documento': today, 'Totale EUR': '90', 'Residuo EUR': '20' } },
  { group: 'Finanza', label: 'Fatture professionisti', first: 'Fornitore', sample: 'Fornitore di prova due', fields: { 'Data documento': today, 'Totale EUR': '45', 'Residuo EUR': '10' } },
  { group: 'Finanza', label: 'Pagamenti', first: 'Soggetto', sample: 'Cliente di prova due', fields: { 'Data pagamento': today, 'Importo EUR': '90' }, select: { 'Tipo': 'Receive' } },
  { group: 'Finanza', label: 'Movimenti bancari', first: 'Data movimento', sample: today, fields: { 'Riferimento': 'PROVA-002', 'Entrata EUR': '90' } }
] as const

for (const entry of archiveCases) test(`archivio ${entry.label}: lista, dettaglio e form sintetico`, async ({ page }, testInfo) => {
  const writes: { method: string; body: Record<string, unknown>; headers: Record<string, string> }[] = []
  await mockApi(page, writes)
  await page.goto('./')
  await openSection(page, 'Archivi')
  const nav = page.getByRole('navigation', { name: 'Tipi di archivio' })
  await nav.getByRole('button', { name: entry.label, exact: true }).click()
  await expect(page.getByRole('heading', { name: entry.label, exact: true })).toBeVisible()
  await expect(page.getByText('Nessun salvataggio Frappe.')).toBeVisible()
  await page.screenshot({ path: `../../docs/evidence/issue-148/archive-${entry.label.toLowerCase().replaceAll(' ', '-')}-${testInfo.project.name}.png`, fullPage: true })
  const rows = page.locator('.archive-panel tbody tr')
  if (await rows.count()) { await rows.first().click(); await expect(page.getByRole('dialog')).toBeVisible(); await page.getByRole('dialog').getByRole('button', { name: 'Chiudi' }).click() }
  await page.getByRole('button', { name: 'Nuova scheda' }).click()
  let form = page.getByRole('dialog')
  await form.getByLabel(entry.first).fill(entry.first.startsWith('Data ') ? todayItalian : entry.sample)
  for (const [label, value] of Object.entries(entry.fields)) await form.getByLabel(label).fill(label.startsWith('Data ') || label === 'Valida dal' ? todayItalian : value)
  if ('select' in entry) for (const [label, value] of Object.entries(entry.select)) await form.getByLabel(label).selectOption(value)
  await page.screenshot({ path: `../../docs/evidence/issue-148/archive-form-${entry.label.toLowerCase().replaceAll(' ', '-')}-${testInfo.project.name}.png`, fullPage: true })
  await form.getByRole('button', { name: 'Rivedi modifica di prova' }).click()
  await expect(page.getByRole('dialog', { name: 'Conferma modifica di prova' })).toBeVisible()
  await page.getByRole('button', { name: 'Conferma nella preview' }).click()
  await expect(page.getByText('Bozza di prova aggiornata nel browser. Nessun dato salvato su Frappe.')).toBeVisible()
  await expect(page.getByRole('dialog')).toContainText(entry.sample)
  expect(writes).toEqual([])
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(page.viewportSize()!.width)
})

test('archivio: ricerca, validazione, errore e accesso per ruolo', async ({ page }) => {
  await mockApi(page)
  await page.goto('./')
  await openSection(page, 'Archivi')
  await page.getByRole('searchbox', { name: 'Cerca in pazienti' }).fill('nessun risultato')
  await expect(page.getByText('Nessuna scheda trovata')).toBeVisible()
  await page.getByRole('searchbox', { name: 'Cerca in pazienti' }).fill('')
  await page.getByRole('button', { name: 'Nuova scheda' }).click()
  await expect(page.getByRole('dialog').getByRole('button', { name: 'Chiudi' })).toBeFocused()
  await page.keyboard.press('Shift+Tab')
  await expect(page.getByRole('dialog').getByRole('button', { name: 'Rivedi modifica di prova' })).toBeFocused()
  await page.keyboard.press('Tab')
  await expect(page.getByRole('dialog').getByRole('button', { name: 'Chiudi' })).toBeFocused()
  await page.getByRole('dialog').getByLabel('Email').fill('non-valida')
  await page.getByRole('dialog').getByRole('button', { name: 'Rivedi modifica di prova' }).click()
  await expect(page.getByRole('dialog', { name: 'Conferma modifica di prova' })).toHaveCount(0)
  await page.getByRole('dialog').getByLabel('Nome e cognome').fill('Persona errore')
  await page.getByRole('dialog').getByLabel('Email').fill('ok@example.invalid')
  await page.evaluate(() => sessionStorage.setItem('cc-synthetic-fail', '1'))
  await page.getByRole('dialog').getByRole('button', { name: 'Rivedi modifica di prova' }).click()
  await page.getByRole('button', { name: 'Conferma nella preview' }).click()
  await expect(page.getByRole('alert', { name: '' }).filter({ hasText: 'Simulazione non riuscita' })).toBeVisible()
  await page.keyboard.press('Escape')
  await expect(page.getByRole('dialog')).toHaveCount(0)
})

test('archivio nascosto a ruolo senza facoltà amministrativa', async ({ page }) => {
  await mockApi(page, [], false, {}, { roles: ['CC Secretariat'] })
  await page.goto('./#Archivi')
  await expect(page.getByRole('heading', { name: 'Agenda' })).toBeVisible()
  await expect(page.getByRole('button', { name: 'Archivi', exact: true })).toHaveCount(0)
})

test('UAT Agenda: sette colonne uguali, professionisti per riga e prenotazione contestuale', async ({ page }, testInfo) => {
  const anchor = new Date(`${today}T12:00:00Z`)
  const monday = new Date(anchor.getTime() - ((anchor.getUTCDay() + 6) % 7) * 86_400_000).toISOString().slice(0, 10)
  const tuesday = new Date(`${monday}T12:00:00Z`)
  tuesday.setUTCDate(tuesday.getUTCDate() + 1)
  const next = tuesday.toISOString().slice(0, 10)
  const second = { ...appointment, name: 'APP-002', practitioner: 'PR-002', practitioner_name: 'Dott. Bianchi', appointment_date: next }
  await mockApi(page, [], true, {}, { practitioners: [...boot.practitioners, { name: 'PR-002', practitioner_name: 'Dott. Bianchi' }], demo_labels: { 'Dott.ssa Rossi': 'Professionista 1', 'Dott. Bianchi': 'Professionista 2' } } as Partial<typeof boot>, [{ ...appointment, appointment_date: monday }, second])
  await page.goto('./')
  await expect(page.locator('.segmented button.selected')).toHaveText('Settimana')
  await expect(page.locator('.week-day')).toHaveCount(7)
  await expect(page.locator('.week-row')).toHaveCount(2)
  await expect(page.locator(`.week-cell[data-date="${monday}"][data-practitioner="PR-001"] .week-event`)).toHaveCount(1)
  await expect(page.locator(`.week-cell[data-date="${next}"][data-practitioner="PR-002"] .week-event`)).toHaveCount(1)
  const geometry = await page.locator('.week-grid').evaluate(grid => {
    const header = [...grid.querySelectorAll('.week-day')].map(element => element.getBoundingClientRect())
    const cells = [...grid.querySelector('.week-row')!.querySelectorAll('.week-cell')].map(element => element.getBoundingClientRect())
    return { widths: header.map(rect => rect.width), delta: header.map((rect, index) => Math.abs(rect.left - cells[index].left)) }
  })
  expect(Math.max(...geometry.widths) - Math.min(...geometry.widths)).toBeLessThanOrEqual(0.75)
  expect(Math.max(...geometry.delta)).toBeLessThanOrEqual(0.75)
  const practitionerFit = await page.locator('.week-professional strong').first().evaluate(element => {
    const style = getComputedStyle(element)
    const canvas = document.createElement('canvas')
    const context = canvas.getContext('2d')!
    context.font = `${style.fontWeight} ${style.fontSize} ${style.fontFamily}`
    return { available: element.getBoundingClientRect().width, word: context.measureText('Professionista').width }
  })
  expect(practitionerFit.available).toBeGreaterThanOrEqual(practitionerFit.word)
  await page.screenshot({ path: `../../docs/evidence/issue-148/uat-agenda-week-${testInfo.project.name}.png`, fullPage: true })
  await page.locator(`.week-cell[data-date="${next}"][data-practitioner="PR-002"] .week-add`).click()
  await expect(page.getByRole('dialog', { name: 'Nuova prenotazione' }).getByLabel('Professionista')).toHaveValue('PR-002')
  await page.getByRole('dialog').getByRole('button', { name: 'Chiudi' }).click()
  await page.getByLabel('Professionista', { exact: true }).selectOption('PR-002')
  await expect(page.locator('.week-row')).toHaveCount(1)
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(page.viewportSize()!.width)
})

test('UAT Professionisti: navigazione, ricerca e scheda autorizzata', async ({ page }, testInfo) => {
  await mockApi(page, [], true, {}, { practitioners: [...boot.practitioners, { name: 'PR-002', practitioner_name: 'Dott. Bianchi' }] })
  await page.goto('./')
  await openSection(page, 'Professionisti')
  await page.getByRole('searchbox', { name: 'Cerca professionisti' }).fill('Bianchi')
  await expect(page.locator('tbody tr')).toHaveCount(1)
  await page.locator('tbody tr').click()
  await expect(page.getByRole('dialog')).toContainText('Dott. Bianchi')
  await page.screenshot({ path: `../../docs/evidence/issue-148/uat-professionisti-${testInfo.project.name}.png`, fullPage: true })
})

test('UAT Report professionisti: sedute disponibili, economia limitata al ruolo', async ({ page }, testInfo) => {
  await mockApi(page, [], false, { cc_performed: 1 }, { roles: ['CC Secretariat'] })
  await page.goto('./')
  await openSection(page, 'Report')
  await page.getByRole('button', { name: 'Report professionisti' }).click()
  await page.getByLabel('Professionista report').selectOption('PR-001')
  await expect(page.getByText('Sedute svolte')).toBeVisible()
  await expect(page.getByRole('button', { name: 'Compensi e fatture autorizzati' })).toHaveCount(0)
  await page.screenshot({ path: `../../docs/evidence/issue-148/uat-report-professionisti-${testInfo.project.name}.png`, fullPage: true })
})

test('UAT alias demo: record esatti in Agenda, ricerca e schede, ID API invariati', async ({ page }, testInfo) => {
  const writes: { method: string; body: Record<string, unknown>; headers: Record<string, string> }[] = []
  const demo_labels = { 'PAT-001': 'Paziente 1', 'Paziente Sintetico': 'Paziente 1', 'PR-001': 'Professionista 1', 'Dott.ssa Rossi': 'Professionista 1', 'SERV-001': 'Servizio 1', 'Prima visita': 'Servizio 1', 'CENTRO-A': 'Centro A' }
  await mockApi(page, writes, true, {}, { demo_labels } as Partial<typeof boot>, null, { demo_labels: { 'PAT-001': 'Cliente 1', 'Paziente Sintetico': 'Cliente 1' } } as Partial<typeof financeBoot>)
  await page.goto('./')
  await expect(page.locator('.week-event').first()).toContainText('Paziente 1')
  await expect(page.locator('.week-professional')).toContainText('Professionista 1')
  await openSection(page, 'Pazienti')
  await page.getByRole('textbox', { name: 'Cerca pazienti' }).last().fill('Paziente 1')
  await expect(page.locator('tbody tr')).toHaveCount(1)
  await expect(page.locator('tbody')).toContainText('Paziente 1')
  await page.reload()
  await expect(page.locator('tbody')).toContainText('Paziente 1')
  await openSection(page, 'Professionisti')
  await expect(page.locator('tbody')).toContainText('Professionista 1')
  await openSection(page, 'Servizi')
  await expect(page.locator('tbody')).toContainText('Servizio 1')
  await openSection(page, 'Agenda')
  await page.getByRole('button', { name: 'Nuova prenotazione', exact: true }).click()
  await expect(page.getByRole('dialog').getByRole('option', { name: 'Paziente 1' })).toHaveCount(1)
  await page.getByRole('dialog').getByRole('textbox', { name: 'Motivo' }).fill('Verifica alias UAT')
  await page.getByRole('button', { name: 'Conferma prenotazione' }).click()
  expect(writes.at(-1)?.body.patient).toBe('PAT-001')
  expect(writes.at(-1)?.body.practitioner).toBe('PR-001')
  await page.screenshot({ path: `../../docs/evidence/issue-148/uat-alias-demo-${testInfo.project.name}.png`, fullPage: true })
})

test('UAT alias demo: fattura e soggetto leggibili in Finanza, valore non censito invariato', async ({ page }) => {
  await mockApi(page, [], true, {}, { demo_labels: { 'INV-001': 'Fattura paziente 1', 'Cliente Sintetico': 'Cliente 1', 'SUP-001': 'Fornitore 1' } } as Partial<typeof boot>)
  await page.goto('./')
  await openSection(page, 'Finanza')
  await page.getByRole('tab', { name: 'Fatture pazienti' }).click()
  await expect(page.locator('.finance-panel tbody')).toContainText('Fattura paziente 1')
  await expect(page.locator('.finance-panel tbody')).toContainText('Cliente 1')
  await expect(page.locator('.finance-panel tbody')).toContainText('80,00')
})

test('UAT alias demo: Finanza sola distingue Patient e Customer con nome coincidente', async ({ page }) => {
  const demo_labels = { 'CUS-001': 'Cliente 1', 'Paziente Sintetico': 'Cliente 1', 'Patient::PAT-001': 'Paziente 1', 'PatientDisplay::Paziente Sintetico': 'Paziente 1' }
  await mockApi(page, [], true, {}, {}, null, { demo_labels } as Partial<typeof financeBoot>, false)
  await page.goto('./')
  await expect(page.getByRole('button', { name: 'Pazienti', exact: true })).toHaveCount(0)
  await page.getByRole('button', { name: 'Report dettagliati' }).click()
  const drawer = page.getByRole('dialog', { name: 'Report dettagliati' })
  await expect(drawer.locator('tbody')).toContainText('Cliente 1')
  await drawer.locator('tbody tr').first().click()
  await expect(drawer.getByText('Paziente 1')).toBeVisible()
})

test('schermate principali renderizzate e fotografate', async ({ page }, testInfo) => {
  await mockApi(page)
  await page.goto('./')
  for (const section of ['Agenda', 'Pazienti', 'Servizi', 'Disponibilità', 'Report', 'Finanza', 'Gestione accessi', 'Registro modifiche', 'Notifiche']) {
    if (section !== 'Agenda') await openSection(page, section)
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible()
    if (section === 'Notifiche') await expect(page.getByText('Nessuna notifica recente')).toBeVisible()
    await page.screenshot({ path: `../../docs/evidence/issue-148/area-${section.toLocaleLowerCase('it-IT').replaceAll(' ', '-')}-${testInfo.project.name}.png`, fullPage: true })
    expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(page.viewportSize()!.width)
  }
})

test('notifiche: caricamento, errore e riprova con stato vuoto corretto', async ({ page }) => {
  await mockApi(page)
  let fail = true
  let release = () => {}
  const gate = new Promise<void>(resolve => { release = resolve })
  await page.route('**/api/method/frappe.client.get_list*', async route => {
    await gate
    if (fail) await route.fulfill({ status: 503, contentType: 'application/json', body: JSON.stringify({ exc: 'SyntheticUnavailable' }) })
    else await route.fulfill({ contentType: 'application/json', body: JSON.stringify({ message: [] }) })
  })
  await page.goto('./')
  await openSection(page, 'Notifiche')
  await expect(page.getByRole('status', { name: '' }).filter({ hasText: 'Caricamento notifiche' })).toBeVisible()
  release()
  await expect(page.getByRole('alert').filter({ hasText: 'Operazione non riuscita' })).toBeVisible()
  fail = false
  await page.getByRole('button', { name: 'Riprova' }).click()
  await expect(page.getByText('Nessuna notifica recente')).toBeVisible()
  await expect(page.getByText('Le comunicazioni del centro appariranno qui.')).toBeVisible()
})

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
  await page.getByRole('button', { name: 'Nuova prenotazione', exact: true }).click()
  await expect(page.getByRole('dialog', { name: 'Nuova prenotazione' })).toBeVisible()
  await page.getByRole('dialog', { name: 'Nuova prenotazione' }).getByRole('textbox', { name: 'Motivo' }).fill('Test sintetico')
  await page.getByRole('button', { name: 'Conferma prenotazione' }).click()
  await expect.poll(() => writes.some(w => w.method.endsWith('scheduling.booking.book'))).toBe(true)
  const booking = writes.find(w => w.method.endsWith('scheduling.booking.book'))!
  expect(booking.body.center).toBe('CENTRO-A')
  expect(booking.headers['x-frappe-csrf-token']).toBe('synthetic-test-token')
  expect(errors).toEqual([])
})

test('seduta cancellata mostra solo azioni coerenti con lo stato server', async ({ page }) => {
  await mockApi(page, [], true, { status: 'Cancelled', cc_closure_state: 'Closed', cc_economic_state: 'Due' })
  await page.goto('./')
  await page.getByText('Paziente Sintetico').first().click()
  const drawer = page.getByRole('dialog', { name: 'Paziente Sintetico' })
  await expect(drawer.getByRole('button', { name: 'Chiudi seduta' })).toHaveCount(0)
  await expect(drawer.getByRole('button', { name: 'Sposta' })).toHaveCount(0)
  await expect(drawer.getByRole('button', { name: 'Cancella' })).toHaveCount(0)
  await expect(drawer.getByRole('button', { name: 'Riapri' })).toBeVisible()
  await expect(drawer.getByRole('button', { name: 'Rinuncia economica' })).toBeVisible()
})

test('selettore pazienti lungo filtra senza perdere scelta e invia ID canonico', async ({ page }) => {
  const writes: { method: string; body: Record<string, unknown>; headers: Record<string, string> }[] = []
  const patients = [...boot.patients, ...Array.from({ length: 10 }, (_, i) => ({ name: `PAT-${String(i + 2).padStart(3, '0')}`, patient_name: `Paziente Demo ${i + 2}` })), { name: 'PAT-ZETA', patient_name: 'Zeta Sintetica' }]
  await mockApi(page, writes, true, {}, { patients })
  await page.goto('./')
  await page.getByRole('button', { name: 'Nuova prenotazione' }).click()
  const dialog = page.getByRole('dialog', { name: 'Nuova prenotazione' })
  await dialog.getByRole('searchbox', { name: 'Filtra paziente' }).fill('Zeta')
  const select = dialog.getByRole('combobox', { name: 'Paziente' })
  await expect(select.locator('option')).toHaveCount(3)
  await select.selectOption('PAT-ZETA')
  await dialog.getByRole('textbox', { name: 'Motivo' }).fill('Ricerca sintetica')
  await dialog.getByRole('button', { name: 'Conferma prenotazione' }).click()
  await expect.poll(() => writes.find(w => w.method.endsWith('scheduling.booking.book'))?.body.patient).toBe('PAT-ZETA')
})

test('catalogo consultivo mostra servizi e professionisti dal centro autorizzato', async ({ page }, testInfo) => {
  await mockApi(page)
  await page.goto('./')
  await openSection(page, 'Servizi')
  await expect(page.getByRole('heading', { name: 'Servizi e professionisti' })).toBeVisible()
  await expect(page.getByRole('row', { name: /Prima visita/ })).toContainText('60 min')
  await expect(page.getByRole('row', { name: /Prima visita/ })).toContainText('80,00')
  await expect(page.getByText('Dott.ssa Rossi')).toBeVisible()
  await page.getByRole('row', { name: /Prima visita/ }).click()
  const detail = page.getByRole('dialog', { name: 'Prima visita' })
  await expect(detail.getByText('ITEM-001')).toBeVisible()
  await expect(detail.getByText('80,00')).toBeVisible()
  await detail.getByRole('button', { name: 'Chiudi' }).click()
  if (testInfo.project.name === 'mobile') expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(390)
  await page.screenshot({ path: `test-results/${testInfo.project.name}-services.png`, fullPage: true })
  await page.getByRole('searchbox', { name: 'Cerca servizi' }).fill('inesistente')
  await expect(page.getByRole('row', { name: /Prima visita/ })).toHaveCount(0)
})

test('cambio centro svuota immediatamente i dati del centro precedente', async ({ page }) => {
  await mockApi(page)
  await page.route('**/api/method/centrochange_core.operations.workspace.bootstrap*', async route => {
    const selected = new URL(route.request().url()).searchParams.get('center')
    const data = selected === 'CENTRO-B'
      ? { ...boot, center: 'CENTRO-B', centers: [{ name: 'CENTRO-A', branch: 'Centro A' }, { name: 'CENTRO-B', branch: 'Centro B' }], patients: [], practitioners: [], services: [] }
      : { ...boot, centers: [{ name: 'CENTRO-A', branch: 'Centro A' }, { name: 'CENTRO-B', branch: 'Centro B' }] }
    await route.fulfill({ contentType: 'application/json', body: JSON.stringify({ message: data }) })
  })
  await page.goto('./')
  await openSection(page, 'Servizi')
  await expect(page.getByRole('row', { name: /Prima visita/ })).toBeVisible()
  await page.getByRole('combobox', { name: 'Centro' }).selectOption('CENTRO-B')
  await expect(page.getByRole('row', { name: /Prima visita/ })).toHaveCount(0)
  await expect(page.getByText('Nessun elemento')).toBeVisible()
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

test('compensi: regola, cattura e confronto usano i contratti auditati', async ({ page }) => {
  const writes: { method: string; body: Record<string, unknown>; headers: Record<string, string> }[] = []
  await mockApi(page, writes, true, {}, {}, null, { demo_labels: { 'ITEM-001': 'Servizio 1', 'RULE-001': 'Regola 1', 'INV-001': 'Fattura professionista 1', 'EXPECT-001': 'Atteso 1' } } as Partial<typeof financeBoot>)
  await page.goto('./')
  await openSection(page, 'Finanza')
  await page.getByRole('tab', { name: 'Professionisti' }).click()
  await page.getByRole('button', { name: 'Operazioni compensi' }).click()
  let dialog = page.getByRole('dialog', { name: 'Economia professionisti' })
  await dialog.getByRole('combobox', { name: 'Professionista' }).selectOption('PR-001')
  await dialog.getByRole('combobox', { name: 'Servizio' }).selectOption('ITEM-001')
  await dialog.getByRole('spinbutton', { name: 'Importo EUR' }).fill('40')
  await dialog.getByRole('textbox', { name: 'Motivo' }).fill('Regola sintetica')
  await dialog.getByRole('button', { name: 'Conferma' }).click()
  await expect.poll(() => writes.find(w => w.method.endsWith('professional_economics.configure_rule'))).toBeTruthy()
  const rule = writes.find(w => w.method.endsWith('professional_economics.configure_rule'))!
  expect(rule.body).toMatchObject({ center: 'CENTRO-A', practitioner: 'PR-001', service_item: 'ITEM-001', basis: 'Fixed Amount', value: '40', currency: 'EUR' })
  expect(rule.body.request_key).toMatch(/^[0-9a-f]{32}$/)
  await expect(dialog).toHaveCount(0)

  await page.getByRole('button', { name: 'Operazioni compensi' }).click()
  dialog = page.getByRole('dialog', { name: 'Economia professionisti' })
  await dialog.getByRole('combobox', { name: 'Operazione' }).selectOption('capture')
  await dialog.getByRole('combobox', { name: 'Fonte seduta' }).selectOption('SOURCE-001')
  await dialog.getByRole('combobox', { name: 'Regola esplicita' }).selectOption('RULE-001')
  await dialog.getByRole('textbox', { name: 'Motivo' }).fill('Cattura sintetica')
  await dialog.getByRole('button', { name: 'Conferma' }).click()
  await expect.poll(() => writes.find(w => w.method.endsWith('professional_economics.capture'))).toBeTruthy()
  expect(writes.find(w => w.method.endsWith('professional_economics.capture'))!.body).toMatchObject({ source: 'SOURCE-001', rule: 'RULE-001' })
  await expect(dialog).toHaveCount(0)

  await page.getByRole('button', { name: 'Operazioni compensi' }).click()
  dialog = page.getByRole('dialog', { name: 'Economia professionisti' })
  await dialog.getByRole('combobox', { name: 'Operazione' }).selectOption('compare')
  await dialog.getByRole('combobox', { name: 'Fattura fornitore contabilizzata' }).selectOption('INV-001')
  await dialog.getByRole('listbox', { name: 'Snapshot distinti delle sedute' }).selectOption('EXPECT-001')
  await dialog.getByRole('textbox', { name: 'Motivo' }).fill('Confronto sintetico')
  await dialog.getByRole('button', { name: 'Conferma' }).click()
  await expect.poll(() => writes.find(w => w.method.endsWith('professional_economics.compare'))).toBeTruthy()
  expect(writes.find(w => w.method.endsWith('professional_economics.compare'))!.body).toMatchObject({ purchase_invoice: 'INV-001', expectations: ['EXPECT-001'] })
})

test('assegnazione paziente usa il servizio di sicurezza con motivo e CSRF', async ({ page }) => {
  const writes: { method: string; body: Record<string, unknown>; headers: Record<string, string> }[] = []
  await mockApi(page, writes)
  await page.goto('./')
  await openSection(page, 'Pazienti')
  await page.getByRole('row', { name: /Paziente Sintetico/ }).click()
  const drawer = page.getByRole('dialog', { name: 'Paziente Sintetico' })
  await expect(drawer.getByText('Professionisti assegnati')).toBeVisible()
  await drawer.getByRole('button', { name: 'Gestisci assegnazione' }).click()
  await drawer.getByRole('combobox', { name: 'Professionista' }).selectOption('PR-001')
  await drawer.getByRole('combobox', { name: 'Stato' }).selectOption('0')
  await drawer.getByRole('textbox', { name: 'Motivo' }).fill('Revoca sintetica')
  await drawer.getByRole('button', { name: 'Conferma' }).click()
  await expect.poll(() => writes.find(w => w.method.endsWith('security.lifecycle.set_assignment'))).toBeTruthy()
  const write = writes.find(w => w.method.endsWith('security.lifecycle.set_assignment'))!
  expect(write.body).toMatchObject({ patient: 'PAT-001', center: 'CENTRO-A', practitioner: 'PR-001', active: '0', reason: 'Revoca sintetica' })
  expect(write.headers['x-frappe-csrf-token']).toBe('synthetic-test-token')
})

test('emissione pacchetto usa modello autorizzato e centro corrente', async ({ page }) => {
  const writes: { method: string; body: Record<string, unknown>; headers: Record<string, string> }[] = []
  await mockApi(page, writes)
  await page.goto('./')
  await openSection(page, 'Pazienti')
  await page.getByRole('row', { name: /Paziente Sintetico/ }).click()
  const drawer = page.getByRole('dialog', { name: 'Paziente Sintetico' })
  await drawer.getByRole('button', { name: 'Emetti pacchetto' }).click()
  await drawer.getByRole('combobox', { name: 'Modello' }).selectOption('TEMPLATE-001')
  await drawer.getByRole('textbox', { name: 'Motivo' }).fill('Emissione sintetica')
  await drawer.getByRole('button', { name: 'Conferma' }).click()
  await expect.poll(() => writes.find(w => w.method.endsWith('operations.packages.issue'))).toBeTruthy()
  const write = writes.find(w => w.method.endsWith('operations.packages.issue'))!
  expect(write.body).toMatchObject({ template: 'TEMPLATE-001', patient: 'PAT-001', centers: ['CENTRO-A'], reason: 'Emissione sintetica' })
  expect(write.body.request_key).toMatch(/^[0-9a-f]{32}$/)
  expect(write.headers['x-frappe-csrf-token']).toBe('synthetic-test-token')
})

test('XML ricevuto: classificazione esplicita prepara bozza tramite servizio di dominio', async ({ page }, testInfo) => {
  const writes: { method: string; body: Record<string, unknown>; headers: Record<string, string> }[] = []
  await mockApi(page, writes)
  await page.goto('./')
  await openSection(page, 'Finanza')
  await page.getByRole('tab', { name: 'XML ricevuti' }).click()
  await page.getByRole('row', { name: /SYN-001/ }).click()
  const drawer = page.getByRole('dialog', { name: 'SYN-001' })
  await drawer.getByRole('button', { name: 'Classifica e prepara' }).click()
  await drawer.getByRole('combobox', { name: /Voce 1/ }).selectOption('ITEM-001')
  await drawer.getByRole('combobox', { name: 'Conto costo' }).selectOption('EXP-001')
  await drawer.screenshot({ path: `test-results/${testInfo.project.name}-xml-classification.png` })
  await drawer.getByRole('textbox', { name: 'Motivo' }).fill('Classificazione sintetica')
  await drawer.getByRole('button', { name: 'Conferma operazione' }).click()
  await expect.poll(() => writes.find(w => w.method.endsWith('finance.incoming.draft'))).toBeTruthy()
  const write = writes.find(w => w.method.endsWith('finance.incoming.draft'))!
  expect(write.body).toMatchObject({ name: 'XML-001', items: ['ITEM-001'], expense_account: 'EXP-001', tax_account: null, reason: 'Classificazione sintetica' })
  expect(write.body.request_key).toMatch(/^[0-9a-f]{32}$/)
  expect(write.headers['x-frappe-csrf-token']).toBe('synthetic-test-token')
})

test('report dettagliati separa soggetto fiscale e professionista', async ({ page }, testInfo) => {
  await mockApi(page)
  await page.goto('./')
  await openSection(page, 'Finanza')
  await page.getByRole('button', { name: 'Report dettagliati' }).click()
  const drawer = page.getByRole('dialog', { name: 'Report dettagliati' })
  await expect(drawer.getByText('Soggetto sintetico')).toBeVisible()
  await drawer.getByRole('row', { name: /Soggetto sintetico/ }).click()
  await expect(drawer.getByText('Fatturato')).toBeVisible()
  await expect(drawer.getByText('PAY-001')).toBeVisible()
  await expect(drawer.getByRole('heading', { name: 'Fatture aperte, posizione corrente' })).toBeVisible()
  await expect(drawer.getByText('Scadenza differita')).toBeVisible()
  await drawer.screenshot({ path: `test-results/${testInfo.project.name}-finance-report.png` })
  await drawer.getByRole('button', { name: 'Professionisti' }).click()
  await drawer.getByRole('combobox', { name: 'Professionista' }).selectOption('PR-001')
  await expect(drawer.getByText('Confronti atteso e ricevuto')).toBeVisible()
  await expect(drawer.getByRole('heading', { name: 'Compensi attesi' })).toBeVisible()
  await expect(drawer.getByText('PUR-001')).toBeVisible()
  await expect(drawer.getByText('40,00').first()).toBeVisible()
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

test('AUDIT-02 ricerca globale trova il paziente nel centro e apre la scheda', async ({ page }, testInfo) => {
  await mockApi(page)
  const requests: string[] = []
  page.on('request', request => {
    if (request.url().includes('operations.workspace.patient_search')) requests.push(request.url())
  })
  await page.goto('./')
  if (testInfo.project.name === 'mobile') await page.getByRole('button', { name: 'Apri ricerca pazienti' }).click()
  await page.getByRole('combobox', { name: 'Ricerca globale pazienti' }).fill('Paziente')
  await expect(page.getByRole('option', { name: 'Paziente Sintetico' })).toBeVisible()
  await page.screenshot({ path: `test-results/audit-02-search-${testInfo.project.name}.png`, fullPage: true })
  expect(requests.some(url => new URL(url).searchParams.get('center') === 'CENTRO-A')).toBeTruthy()
  await page.getByRole('option', { name: 'Paziente Sintetico' }).click()
  await expect(page.getByRole('heading', { name: 'Pazienti', exact: true })).toBeVisible()
  await expect(page.getByRole('dialog', { name: 'Paziente Sintetico' })).toBeVisible()
})

test('AUDIT-02 hash sconosciuto e non autorizzato convergono su route lecita', async ({ page }, testInfo) => {
  await mockApi(page, [], false)
  await page.goto('./#Finanza')
  await expect(page.locator('.breadcrumbs strong')).toHaveText('Agenda')
  await expect.poll(() => decodeURIComponent(new URL(page.url()).hash.slice(1))).toBe('Agenda')
  await page.evaluate(() => { location.hash = '%ZZ' })
  await expect(page.locator('.breadcrumbs strong')).toHaveText('Agenda')
  await expect.poll(() => decodeURIComponent(new URL(page.url()).hash.slice(1))).toBe('Agenda')
  if (testInfo.project.name === 'mobile') await page.getByRole('button', { name: 'Apri menu' }).click()
  await page.getByRole('button', { name: 'Pazienti', exact: true }).click()
  await page.reload()
  await expect(page.locator('.breadcrumbs strong')).toHaveText('Pazienti')
  await page.goBack()
  await expect(page.locator('.breadcrumbs strong')).toHaveText('Agenda')
})

test('AUDIT-02 menu e ricerca mobile restano usabili con tastiera', async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== 'mobile')
  await mockApi(page)
  await page.goto('./')
  await page.getByRole('button', { name: 'Apri menu' }).click()
  await expect(page.getByRole('complementary', { name: 'Navigazione principale' }).getByRole('button', { name: 'Chiudi menu' })).toBeFocused()
  await expect.poll(() => page.locator('.sidebar').evaluate(element => Math.round(new DOMMatrixReadOnly(getComputedStyle(element).transform).m41))).toBe(0)
  expect(await page.locator('.sidebar').evaluate(element => Number(getComputedStyle(element).zIndex))).toBeGreaterThan(
    await page.locator('.topbar').evaluate(element => Number(getComputedStyle(element).zIndex)))
  const closeIsOnTop = await page.getByRole('complementary', { name: 'Navigazione principale' }).getByRole('button', { name: 'Chiudi menu' }).evaluate(element => {
    const rect = element.getBoundingClientRect()
    return element.contains(document.elementFromPoint(rect.left + rect.width / 2, rect.top + rect.height / 2))
  })
  expect(closeIsOnTop).toBe(true)
  await page.screenshot({ path: 'test-results/audit-02-mobile-menu.png', fullPage: true })
  await page.keyboard.press('Escape')
  await expect(page.getByRole('button', { name: 'Apri menu' })).toBeFocused()
  await page.getByRole('button', { name: 'Apri ricerca pazienti' }).click()
  await expect(page.getByRole('combobox', { name: 'Ricerca globale pazienti' })).toBeFocused()
  await page.getByRole('combobox', { name: 'Ricerca globale pazienti' }).fill('Paziente')
  await expect(page.getByRole('option', { name: 'Paziente Sintetico' })).toBeVisible()
  await page.keyboard.press('Escape')
  await expect(page.getByRole('option', { name: 'Paziente Sintetico' })).toHaveCount(0)
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(390)
})

test('AUDIT-02 sidebar mobile chiusa non cattura Tab', async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== 'mobile')
  await mockApi(page)
  await page.goto('./')
  await page.keyboard.press('Tab')
  await expect(page.getByRole('link', { name: 'Vai al contenuto' })).toBeFocused()
  await page.keyboard.press('Tab')
  await expect(page.getByRole('button', { name: 'Apri menu' })).toBeFocused()
})

test('AUDIT-02 cambio centro scarta risultati tardivi della ricerca precedente', async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== 'desktop')
  await mockApi(page, [], true, {}, { centers: [{ name: 'CENTRO-A', branch: 'Centro A' }, { name: 'CENTRO-B', branch: 'Centro B' }] })
  let started = false
  await page.route('**/api/method/centrochange_core.operations.workspace.patient_search*', async route => {
    const selected = new URL(route.request().url()).searchParams.get('center')
    if (selected === 'CENTRO-A') { started = true; await new Promise(resolve => setTimeout(resolve, 600)) }
    await route.fulfill({ contentType: 'application/json', body: JSON.stringify({ message: { patients: selected === 'CENTRO-A' ? boot.patients : [], truncated: false } }) })
  })
  await page.route('**/api/method/centrochange_core.operations.workspace.bootstrap*', async route => {
    const selected = new URL(route.request().url()).searchParams.get('center')
    await route.fulfill({ contentType: 'application/json', body: JSON.stringify({ message: { ...boot, center: selected || 'CENTRO-A', centers: [{ name: 'CENTRO-A', branch: 'Centro A' }, { name: 'CENTRO-B', branch: 'Centro B' }], patients: selected === 'CENTRO-B' ? [] : boot.patients } }) })
  })
  await page.goto('./')
  await page.getByRole('combobox', { name: 'Ricerca globale pazienti' }).fill('Paziente')
  await expect.poll(() => started).toBe(true)
  await page.getByRole('combobox', { name: 'Centro' }).selectOption('CENTRO-B')
  await expect(page.getByRole('combobox', { name: 'Ricerca globale pazienti' })).toHaveValue('')
  await page.waitForTimeout(700)
  await expect(page.getByRole('option', { name: 'Paziente Sintetico' })).toHaveCount(0)
})

test('AUDIT-02 ricerca globale mostra errore ed esito vuoto senza dati di altri centri', async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== 'desktop')
  await mockApi(page)
  await page.route('**/api/method/centrochange_core.operations.workspace.patient_search*', async route => {
    const query = new URL(route.request().url()).searchParams.get('query')
    await route.fulfill(query === 'errore'
      ? { status: 503, contentType: 'application/json', body: JSON.stringify({ exc: 'Unavailable' }) }
      : { contentType: 'application/json', body: JSON.stringify({ message: { patients: [], truncated: false } }) })
  })
  await page.goto('./')
  const search = page.getByRole('combobox', { name: 'Ricerca globale pazienti' })
  await search.fill('errore')
  await expect(page.getByRole('alert', { name: '' }).filter({ hasText: 'Ricerca non disponibile' })).toBeVisible()
  await search.fill('nessuno')
  await expect(page.getByText('Nessun paziente trovato nel centro.')).toBeVisible()
})

test('AUDIT-02 menu utente usa logout Frappe e footer coerente', async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== 'desktop')
  const writes: { method: string; body: Record<string, unknown>; headers: Record<string, string> }[] = []
  await mockApi(page, writes)
  await page.goto('./')
  await expect(page.locator('.app-footer')).toHaveText('Centro Change · Area riservata')
  await page.getByRole('button', { name: 'Menu utente' }).click()
  await page.getByRole('button', { name: 'Esci', exact: true }).last().click()
  await expect(page).toHaveURL(/\/login\?redirect-to=\/premium/)
  const logout = writes.find(write => write.method === 'logout')
  expect(logout?.headers['x-frappe-csrf-token']).toBe('synthetic-test-token')
})

test('AUDIT-02 utente solo Finanza riceve landing e URL consentiti', async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== 'desktop')
  await mockApi(page, [], true, {}, {}, null, { can_write: false, is_manager: false }, false)
  await page.goto('./#Agenda')
  await expect(page.locator('.breadcrumbs strong')).toHaveText('Finanza')
  await expect.poll(() => decodeURIComponent(new URL(page.url()).hash.slice(1))).toBe('Finanza')
  await expect(page.getByRole('button', { name: 'Pazienti', exact: true })).toHaveCount(0)
  await expect(page.getByRole('combobox', { name: 'Ricerca globale pazienti' })).toBeDisabled()
})

test('AUDIT-02 ricerca globale segnala risultati troncati', async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== 'desktop')
  await mockApi(page)
  await page.route('**/api/method/centrochange_core.operations.workspace.patient_search*', route =>
    route.fulfill({ contentType: 'application/json', body: JSON.stringify({ message: { patients: boot.patients, truncated: true } }) }))
  await page.goto('./')
  await page.getByRole('combobox', { name: 'Ricerca globale pazienti' }).fill('Paziente')
  await expect(page.getByText('Mostrati i primi 50 risultati. Affina la ricerca.')).toBeVisible()
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
  await expect(drawer.getByText('Ultima rettifica registrata')).toBeVisible()
  await expect(drawer.getByText('Cronologia precedenti (1)')).toBeVisible()
  await drawer.getByText('Cronologia precedenti (1)').click()
  await expect(drawer.getByText('Nota sintetica', { exact: true })).toBeVisible()
  await drawer.getByRole('button', { name: 'Rettifica' }).click()
  await drawer.getByRole('textbox', { name: 'Rettifica nota' }).fill('Nota sintetica rettificata')
  await drawer.getByRole('button', { name: 'Registra rettifica' }).click()
  await expect.poll(() => writes.some(w => w.method.endsWith('operations.notes.add_note'))).toBe(true)
  const note = writes.find(w => w.method.endsWith('operations.notes.add_note'))!
  expect(note.body.corrects).toBe('NOTE-002')
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

test('registro modifiche mostra autore, motivo e prima/dopo senza mutazioni', async ({ page }, testInfo) => {
  const writes: { method: string; body: Record<string, unknown>; headers: Record<string, string> }[] = []
  await mockApi(page, writes)
  await page.goto('./')
  await openSection(page, 'Registro modifiche')
  await expect(page.getByRole('heading', { name: 'Registro modifiche' })).toBeVisible()
  await page.getByRole('row', { name: /Prenotazione spostata/ }).click()
  const drawer = page.getByRole('dialog', { name: 'Prenotazione spostata' })
  await expect(drawer.getByText('Riprogrammazione sintetica')).toBeVisible()
  await expect(drawer.getByText('ora seduta')).toBeVisible()
  await expect(drawer.getByText('09:00')).toBeVisible()
  await expect(drawer.getByText('10:00')).toBeVisible()
  await drawer.screenshot({ path: `test-results/${testInfo.project.name}-audit-detail.png` })
  expect(writes).toEqual([])
})

test('sweep grafico delle sezioni operative e amministrative', async ({ page }, testInfo) => {
  await mockApi(page)
  const consoleErrors: string[] = []
  page.on('console', message => { if (message.type() === 'error') consoleErrors.push(message.text()) })
  page.on('pageerror', error => consoleErrors.push(error.message))
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
  expect(consoleErrors).toEqual([])
})
