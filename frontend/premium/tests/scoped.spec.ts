import { expect, test, type Page } from '@playwright/test'

const center = 'CENTRO-A'
const today = new Intl.DateTimeFormat('en-CA', { timeZone: 'Europe/Rome', year: 'numeric', month: '2-digit', day: '2-digit' }).format(new Date())
const boot = { center, centers: [{ name: center, branch: 'Centro A' }], patients: [{ name: 'PAT-001', patient_name: 'Paziente Sintetico' }], practitioners: [{ name: 'PR-001', practitioner_name: 'Professionista Sintetico' }], services: [], packages: [], payment_methods: [], roles: ['CC Manager'] }
const financeBoot = { center, centers: boot.centers, can_write: true, is_manager: true, customers: [], suppliers: [], accounts: [], practitioners: [], items: [], assignees: [], simulation_only: true, fiscal_verified: false }
type Write = { method: string; body: Record<string, unknown>; csrf: string | undefined }

async function mock(page: Page, writes: Write[], role = 'CC Manager') {
  const rows: Record<string, Record<string, unknown>[]> = {
    Patient: [{ name: 'PAT-001', patient_name: 'Paziente Sintetico', first_name: 'Paziente', last_name: 'Sintetico', email: 'paziente@example.invalid', modified: 'v1' }],
    'Healthcare Practitioner': [{ name: 'PR-001', practitioner_name: 'Professionista Sintetico', first_name: 'Professionista', last_name: 'Sintetico', status: 'Active', modified: 'v1' }],
    Item: [{ name: 'ITEM-001', item_name: 'Visita sintetica', item_group: 'Services', stock_uom: 'Nos', modified: 'v1' }],
    'Item Price': [{ name: 'PRICE-001', item_code: 'ITEM-001', price_list: 'Centro A', currency: 'EUR', price_list_rate: 80, valid_from: today, modified: 'v1' }],
    'Appointment Type': [{ name: 'TYPE-001', appointment_type: 'Visita sintetica', default_duration: 60, cc_service_item: 'ITEM-001', modified: 'v1' }],
    'CC Center Service': [{ name: 'SERV-001', appointment_type: 'TYPE-001', center, enabled: 1, modified: 'v1' }],
    'CC Package Template': [{ name: 'PACK-001', title: 'Percorso sintetico', service_item: 'ITEM-001', units: 4, enabled: 1, modified: 'v1' }],
    'Sales Invoice': [{ name: 'SINV-001', customer: 'CUS-001', party_label: 'Soggetto sintetico', posting_date: today, grand_total: 80, outstanding_amount: 20, docstatus: 1 }],
    'Purchase Invoice': [{ name: 'PINV-001', supplier: 'SUP-001', party_label: 'Soggetto sintetico', posting_date: today, grand_total: 40, outstanding_amount: 10, docstatus: 1 }],
    'Payment Entry': [{ name: 'PAY-001', party: 'CUS-001', party_label: 'Soggetto sintetico', posting_date: today, payment_type: 'Receive', paid_amount: 60, unallocated_amount: 0, docstatus: 1, modified: 'v1', references: [], reference_no: 'CC-HTTP-UAT0000001-ref' }],
    'Bank Transaction': [{ name: 'BANK-001', date: today, reference_number: 'SYN-001', deposit: 60, withdrawal: 0 }]
  }
  await page.route('**/api/method/**', async route => {
    const request = route.request(), method = new URL(request.url()).pathname.split('/api/method/')[1]
    const args = request.method() === 'POST' ? request.postDataJSON() as Record<string, unknown> : Object.fromEntries(new URL(request.url()).searchParams)
    if (request.method() === 'POST') writes.push({ method, body: args, csrf: request.headers()['x-frappe-csrf-token'] })
    let message: unknown = null, status = 200
    if (method.endsWith('operations.workspace.bootstrap')) { if (role === 'CC Finance') status = 403; else message = { ...boot, roles: [role] } }
    else if (method.endsWith('finance.reporting.bootstrap')) { if (role === 'CC Manager' || role === 'CC Finance') message = { ...financeBoot, is_manager: role === 'CC Manager' }; else status = 403 }
    else if (method.endsWith('catalog.records') || method.endsWith('operations.profiles.patients') || method.endsWith('operations.profiles.practitioners') || method.endsWith('finance.payments.records')) {
      const kind = method.endsWith('patients') ? 'Patient' : method.endsWith('practitioners') ? 'Healthcare Practitioner' : method.endsWith('payments.records') ? 'Payment Entry' : String(args.kind)
      message = { rows: rows[kind] ?? [], has_more: false }
    } else if (method.endsWith('finance.reporting.records')) {
      const list = rows[String(args.doctype)] ?? []
      message = args.limit !== undefined ? { rows: list, has_more: false } : list
    }
    else if (method.endsWith('catalog.detail') || method.endsWith('operations.profiles.patient_detail') || method.endsWith('operations.profiles.practitioner_detail') || method.endsWith('finance.payments.detail')) {
      const kind = method.endsWith('patient_detail') ? 'Patient' : method.endsWith('practitioner_detail') ? 'Healthcare Practitioner' : method.endsWith('payments.detail') ? 'Payment Entry' : String(args.kind)
      message = rows[kind]?.find(row => row.name === args.name) ?? null
      if (!message) status = 404
    } else if (method.endsWith('finance.documents.detail')) {
      const row = rows[String(args.doctype)]?.find(entry => entry.name === args.name)
      message = row ? { ...row, doctype: args.doctype, party: 'Soggetto sintetico', currency: 'EUR', can_print: row.docstatus === 1, items: [], taxes: [], references: [] } : null
      if (!message) status = 404
    } else if (method.endsWith('finance.documents.preview')) message = { doctype: args.doctype, name: args.name, format: 'Centro Change', html: '<html lang="it"><body><h1>Documento sintetico</h1></body></html>' }
    else if (request.method() === 'POST' && /catalog\.(service|item|appointment_type|price|package_template)_(save|create)|operations\.profiles\.(patient|practitioner)_save/.test(method)) {
      if (role !== 'CC Manager') status = 403
      else {
        const kind = method.includes('item_save') ? 'Item' : method.includes('price_') ? 'Item Price' : method.includes('service_') ? 'CC Center Service' : method.includes('appointment_type_') ? 'Appointment Type' : method.includes('package_template_') ? 'CC Package Template' : method.includes('patient_') ? 'Patient' : 'Healthcare Practitioner'
        const existing = rows[kind].find(row => row.name === args.name)
        if (existing) { Object.assign(existing, args, { modified: 'v2' }); message = { name: existing.name, modified: 'v2' } }
        else { const created = { ...args, name: `NEW-${kind.replaceAll(' ', '-')}`, modified: 'v1' }; rows[kind].push(created); message = { name: created.name, modified: 'v1' } }
      }
    } else if (method.endsWith('operations.workspace.agenda')) message = { appointments: [], truncated: false }
    else if (method.endsWith('operations.workspace.patient_search')) message = { patients: boot.patients, truncated: false }
    else if (method.endsWith('operations.workspace.patient_history')) message = { appointments: [], truncated: false, settlements: [], organizational_notes: [{ name: 'ORG-001', content: 'Nota organizzativa di prova', creation: '2026-10-31 10:00:00' }], private_notes: role === 'CC Professional' ? [{ name: 'PRIV-001', content: 'Nota riservata di prova', creation: '2026-10-31 10:01:00' }] : [], packages: [], assignment_events: [] }
    else if (method.endsWith('operations.workspace.management_context')) message = { users: [{ name: 'manager@example.invalid', full_name: 'Direzione di prova', roles: ['CC Manager'] }], practitioners: boot.practitioners, memberships: [{ name: 'MEM-001', user: 'manager@example.invalid', active: 1 }] }
    else if (method.endsWith('security.audit_view.events')) message = { events: [{ name: 'AUD-001', event_type: 'SESSION_AUTO_LOCKED', event_time: '2026-10-27 07:00:04', actor: 'cc-automation-service@example.invalid', reference_name: 'APP-001', reason: '07:00 local cutoff catch-up', before_state: '{}', after_state: '{}' }], has_more: false }
    else if (method.endsWith('operations.notes.add_note') && request.method() === 'POST') message = { name: 'NOTE-NEW' }
    else if (method.endsWith('operations.workspace.schedules')) message = []
    else status = 404
    await route.fulfill({ status, contentType: 'application/json', body: JSON.stringify(status === 200 ? { message } : { exc: 'PermissionError' }) })
  })
}

async function openArchives(page: Page) {
  await page.goto('./')
  if ((page.viewportSize()?.width ?? 1440) < 760) await page.getByRole('button', { name: 'Apri menu' }).click()
  await page.getByRole('button', { name: 'Archivi', exact: true }).click()
  await expect(page.getByRole('heading', { name: 'Archivi' })).toBeVisible()
}

test('Archivi mantiene catalogo e finanza senza duplicare le anagrafiche operative', async ({ page }) => {
  await mock(page, [])
  await openArchives(page)
  const nav = page.getByRole('navigation', { name: 'Tipi di archivio' })
  await expect(nav.getByRole('button', { name: 'Pazienti', exact: true })).toHaveCount(0)
  await expect(nav.getByRole('button', { name: 'Professionisti', exact: true })).toHaveCount(0)
  await expect(nav.getByRole('button', { name: 'Articoli', exact: true })).toBeVisible()
  await expect(nav.getByRole('button', { name: 'Fatture pazienti', exact: true })).toBeVisible()
})

test('regressioni DECISION-064: Agenda unica e intervallo pagamenti ammesso', async ({ page }) => {
  await mock(page, [])
  await page.goto('./')
  if ((page.viewportSize()?.width ?? 1440) < 760) await page.getByRole('button', { name: 'Apri menu' }).click()
  const agenda = page.locator('.sidebar nav').first().getByRole('button', { name: 'Agenda', exact: true })
  await expect(agenda).toHaveCount(1)
  await expect(agenda).toBeVisible()
  await openArchives(page)
  const paymentRequest = page.waitForRequest(request => request.url().includes('finance.payments.records'))
  await page.getByRole('navigation', { name: 'Tipi di archivio' }).getByRole('button', { name: 'Pagamenti', exact: true }).click()
  const url = new URL((await paymentRequest).url())
  const start = url.searchParams.get('start') ?? ''
  const end = url.searchParams.get('end') ?? ''
  expect(start).toMatch(/^\d{4}-\d{2}-\d{2}$/)
  expect(end).toMatch(/^\d{4}-\d{2}-\d{2}$/)
  const days = (Date.parse(end + 'T00:00:00Z') - Date.parse(start + 'T00:00:00Z')) / 86_400_000
  expect(days).toBe(90)
  await expect(page.locator('.archive-dates input').first()).toHaveValue(/^\d{2}\/\d{2}\/\d{4}$/)
  await expect(page.locator('.archive-panel tbody tr')).toHaveCount(1)
})

test('AUDIT-09: fattura annullata mostra il limite di stampa senza richiedere anteprima', async ({ page }) => {
  const writes: Write[] = []
  await mock(page, writes)
  await page.route('**/api/method/centrochange_core.finance.reporting.records*', route => {
    const url = new URL(route.request().url())
    if (url.searchParams.get('doctype') !== 'Sales Invoice') return route.fallback()
    // List is stale: the authoritative detail has since been cancelled.
    return route.fulfill({ contentType: 'application/json', body: JSON.stringify({ message: { rows: [{ name: 'SINV-CANCELLED', customer: 'CC-MVP-POS-TEST', party_label: 'Cliente precedente', posting_date: today, grand_total: 100, outstanding_amount: 100, docstatus: 1 }], has_more: false } }) })
  })
  await page.route('**/api/method/centrochange_core.finance.documents.detail*', route => route.fulfill({ contentType: 'application/json', body: JSON.stringify({ message: { doctype: 'Sales Invoice', name: 'SINV-CANCELLED', party: 'Cliente sintetico', docstatus: 2, currency: 'EUR', can_print: false, items: [{ item_name: 'Visita', description: 'Visita', qty: 1, rate: 100, amount: 100 }], taxes: [] } }) }))
  await openArchives(page)
  await page.getByRole('navigation', { name: 'Tipi di archivio' }).getByRole('button', { name: 'Fatture pazienti' }).click()
  await expect(page.locator('.archive-panel tbody tr').first()).toContainText('Cliente precedente')
  await expect(page.locator('.archive-panel tbody tr').first()).not.toContainText('CC-MVP-POS-TEST')
  await page.locator('.archive-panel tbody tr').first().click()
  const drawer = page.locator('.archive-detail-page')
  await expect(drawer).toContainText('Questo documento è annullato')
  await expect(drawer).toContainText('Numero documento')
  await expect(drawer).toContainText('SINV-CANCELLED')
  await expect(drawer).not.toContainText('Cliente precedente')
  await expect(drawer).not.toContainText('CC-MVP-POS-TEST')
  await expect(drawer.getByText('Cliente sintetico', { exact: true })).toHaveCount(2)
  await expect(drawer).toContainText('non è un importo da incassare')
  await expect(drawer.getByRole('button', { name: 'Anteprima e stampa' })).toHaveCount(0)
  expect(writes).toHaveLength(0)
})

test('anteprima scorrevole e riferimento operazione integro', async ({ page }) => {
  await mock(page, [])
  await openArchives(page)
  await page.getByRole('navigation', { name: 'Tipi di archivio' }).getByRole('button', { name: 'Fatture pazienti' }).click()
  await page.locator('.archive-panel tbody tr').first().click()
  await page.getByRole('button', { name: 'Anteprima e stampa' }).click()
  const region = page.getByRole('region', { name: 'Anteprima documento scorrevole' })
  await expect(region).toBeVisible()
  await expect(region.locator('iframe')).toHaveJSProperty('clientWidth', 794)
  if ((page.viewportSize()?.width ?? 1440) < 760) {
    await region.evaluate(el => { el.scrollLeft = el.scrollWidth })
    expect(await region.evaluate(el => el.scrollLeft)).toBeGreaterThan(0)
  }
  await page.getByRole('dialog', { name: /Anteprima/ }).getByRole('button', { name: 'Chiudi' }).first().click()
  await page.getByRole('button', { name: 'Torna agli archivi' }).click()
  await page.getByRole('navigation', { name: 'Tipi di archivio' }).getByRole('button', { name: 'Pagamenti' }).click()
  await page.locator('.archive-panel tbody tr').first().click()
  await expect(page.locator('.archive-detail-page')).toContainText('Riferimento operazione')
  await expect(page.locator('.archive-detail-page')).toContainText('CC-HTTP-UAT0000001-ref')
})

test('API catalogo: 9 liste, dettaglio, salvataggio con CSRF e anteprima stampa', async ({ page }, testInfo) => {
  const writes: Write[] = []
  await mock(page, writes)
  await openArchives(page)
  for (const name of ['Articoli', 'Tariffe', 'Tipi seduta', 'Servizi del centro', 'Modelli pacchetto', 'Fatture pazienti', 'Fatture professionisti', 'Pagamenti', 'Movimenti bancari']) {
    await page.getByRole('navigation', { name: 'Tipi di archivio' }).getByRole('button', { name, exact: true }).click()
    await expect(page.locator('.archive-panel tbody tr')).toHaveCount(1)
    await page.locator('.archive-panel tbody tr').first().click()
    await expect(page.locator('.archive-detail-page')).toBeVisible()
    await expect(page.getByRole('dialog')).toHaveCount(0)
    if (name === 'Pagamenti') {
      await page.getByRole('button', { name: 'Anteprima e stampa' }).click()
      await expect(page.getByTitle('Documento PAY-001')).toBeVisible()
      await expect(page.getByTitle('Documento PAY-001')).toHaveAttribute('sandbox', 'allow-same-origin allow-modals')
      await page.getByTitle('Documento PAY-001').evaluate(element => { const frame = element as HTMLIFrameElement; frame.contentWindow!.print = () => frame.setAttribute('data-printed', 'yes') })
      await page.getByRole('dialog', { name: /Anteprima/ }).getByRole('button', { name: 'Stampa' }).click()
      await expect(page.getByTitle('Documento PAY-001')).toHaveAttribute('data-printed', 'yes')
      await page.getByRole('dialog', { name: /Anteprima/ }).getByRole('button', { name: 'Chiudi' }).first().click()
    }
    await page.screenshot({ path: testInfo.outputPath(`scoped-${name.toLowerCase().replaceAll(' ', '-')}-${testInfo.project.name}.png`), fullPage: true })
    await page.getByRole('button', { name: 'Torna agli archivi' }).click()
  }
  await page.getByRole('navigation', { name: 'Tipi di archivio' }).getByRole('button', { name: 'Articoli' }).click()
  await page.locator('.archive-panel tbody tr').first().click()
  await page.getByRole('button', { name: 'Modifica scheda' }).click()
  await page.locator('.archive-edit').getByLabel('Articolo').fill('Visita sintetica aggiornata')
  await page.locator('.archive-edit').getByLabel('Motivo').fill('Aggiornamento prova')
  await page.getByRole('button', { name: 'Rivedi modifica' }).click()
  await page.getByRole('button', { name: 'Conferma salvataggio' }).click()
  await expect(page.getByText(/Scheda salvata/)).toBeVisible()
  expect(writes).toHaveLength(1)
  expect(writes[0].method).toContain('catalog.item_save')
  expect(writes[0].body).toMatchObject({ center, name: 'ITEM-001', expected_version: 'v1', item_name: 'Visita sintetica aggiornata' })
  expect(writes[0].csrf).toBe('synthetic-test-token')
  expect(writes.some(write => write.method.includes('payments.'))).toBe(false)
})

test('API scoped: creazione autorizzata e diniego ruolo', async ({ page }) => {
  const writes: Write[] = []
  await mock(page, writes)
  await openArchives(page)
  await page.getByRole('navigation', { name: 'Tipi di archivio' }).getByRole('button', { name: 'Modelli pacchetto' }).click()
  await page.getByRole('button', { name: 'Nuova scheda' }).click()
  const form = page.locator('.archive-edit')
  await form.getByLabel('Modello').fill('Percorso nuovo')
  await form.getByLabel('Articolo').fill('ITEM-001')
  await form.getByLabel(/Numero di sedute incluse|Unità/).fill('4')
  await form.getByLabel('Motivo').fill('Prova sintetica')
  await form.getByRole('button', { name: /Rivedi (dati|modifica)/ }).click()
  await page.getByRole('button', { name: 'Conferma salvataggio' }).click()
  await expect(page.getByText(/Scheda salvata/)).toBeVisible()
  expect(writes[0].method).toContain('catalog.package_template_create')
  expect(writes[0].body).not.toHaveProperty('customer')
})

for (const task of [
  { section: 'Tariffe', method: 'catalog.price_create', fields: { Articolo: 'ITEM-001', Tariffa: '95', 'Valida dal': today } },
  { section: 'Tipi seduta', method: 'catalog.appointment_type_create', fields: { 'Tipo seduta': 'Nuova visita sintetica', 'Durata (min)': '45', Articolo: 'ITEM-001' } },
  { section: 'Servizi del centro', method: 'catalog.service_create', fields: { 'Tipo seduta': 'TYPE-001' } }
]) test(`API scoped: crea ${task.section} con contratto ristretto`, async ({ page }) => {
  const writes: Write[] = []
  await mock(page, writes)
  await openArchives(page)
  await page.getByRole('navigation', { name: 'Tipi di archivio' }).getByRole('button', { name: task.section, exact: true }).click()
  await page.getByRole('button', { name: 'Nuova scheda' }).click()
  const form = page.locator('.archive-edit')
  for (const [label, value] of Object.entries(task.fields)) await form.getByLabel(label).first().fill(value)
  await form.getByLabel('Motivo').fill('Creazione sintetica')
  await form.getByRole('button', { name: /Rivedi (dati|modifica)/ }).click()
  await page.getByRole('button', { name: 'Conferma salvataggio' }).click()
  await expect(page.getByText(/Scheda salvata/)).toBeVisible()
  expect(writes).toHaveLength(1)
  expect(writes[0].method).toContain(task.method)
})

test('API scoped: professionista non ha accesso agli archivi amministrativi', async ({ page }) => {
  const writes: Write[] = []
  await mock(page, writes, 'CC Professional')
  await page.goto('./#Archivi')
  await expect(page.getByRole('button', { name: 'Archivi', exact: true })).toHaveCount(0)
  expect(writes).toEqual([])
})

test('API scoped: ruolo Finanza senza workspace operativo consulta i pagamenti', async ({ page }) => {
  const writes: Write[] = []
  await mock(page, writes, 'CC Finance')
  await openArchives(page)
  const nav = page.getByRole('navigation', { name: 'Tipi di archivio' })
  await expect(nav.getByRole('button', { name: 'Pazienti', exact: true })).toHaveCount(0)
  await nav.getByRole('button', { name: 'Pagamenti' }).click()
  await expect(page.locator('.archive-panel tbody tr')).toHaveCount(1)
  await page.locator('.archive-panel tbody tr').first().click()
  await expect(page.getByRole('button', { name: 'Modifica scheda' })).toHaveCount(0)
  await expect(page.getByRole('button', { name: 'Anteprima e stampa' })).toBeVisible()
  expect(writes).toEqual([])
})

test('API scoped: validazione e 403 non confermano una modifica', async ({ page }) => {
  const writes: Write[] = []
  await mock(page, writes)
  await page.route('**/api/method/centrochange_core.catalog.item_save', route => route.fulfill({ status: 403, contentType: 'application/json', body: JSON.stringify({ exc: 'PermissionError' }) }))
  await openArchives(page)
  await page.getByRole('navigation', { name: 'Tipi di archivio' }).getByRole('button', { name: 'Articoli' }).click()
  await page.locator('.archive-panel tbody tr').first().click()
  await page.getByRole('button', { name: 'Modifica scheda' }).click()
  const form = page.locator('.archive-edit')
  await form.getByLabel('Articolo').fill('Nome aggiornato')
  await form.getByRole('button', { name: 'Rivedi modifica' }).click()
  await expect(form.getByRole('alert')).toContainText('motivo')
  expect(writes).toEqual([])
  await form.getByLabel('Motivo').fill('Prova diniego')
  await form.getByRole('button', { name: 'Rivedi modifica' }).click()
  await page.getByRole('button', { name: 'Conferma salvataggio' }).click()
  await expect(page.locator('.archive-edit')).toBeVisible()
  await expect(page.getByRole('alert').first()).toContainText('Accesso negato')
  await expect(page.getByText(/Scheda salvata/)).toHaveCount(0)
})

for (const task of [
  { section: 'Tariffe', field: 'Tariffa', value: '92', method: 'catalog.price_save' },
  { section: 'Tipi seduta', field: 'Durata (min)', value: '50', method: 'catalog.appointment_type_save' },
  { section: 'Servizi del centro', field: 'Stato', value: '0', method: 'catalog.service_save' },
  { section: 'Modelli pacchetto', field: 'Modello', value: 'Percorso aggiornato', method: 'catalog.package_template_save' }
]) test(`API scoped: ${task.section} salva solo i campi consentiti`, async ({ page }) => {
  const writes: Write[] = []
  await mock(page, writes)
  await openArchives(page)
  await page.getByRole('navigation', { name: 'Tipi di archivio' }).getByRole('button', { name: task.section, exact: true }).click()
  await page.locator('.archive-panel tbody tr').first().click()
  await page.getByRole('button', { name: 'Modifica scheda' }).click()
  const form = page.locator('.archive-edit')
  if (task.field === 'Stato') await form.getByLabel(task.field).first().selectOption(task.value)
  else await form.getByLabel(task.field).first().fill(task.value)
  await form.getByLabel('Motivo').fill('Revisione sintetica')
  await form.getByRole('button', { name: /Rivedi (dati|modifica)/ }).click()
  await page.getByRole('button', { name: 'Conferma salvataggio' }).click()
  await expect(page.getByText(/Scheda salvata/)).toBeVisible()
  expect(writes).toHaveLength(1)
  expect(writes[0].method).toContain(task.method)
  expect(writes[0].body).not.toHaveProperty('customer')
  if (['Pazienti', 'Professionisti', 'Modelli pacchetto'].includes(task.section)) {
    await expect(page.locator('.archive-detail-page')).toContainText(task.value)
    await page.getByRole('button', { name: 'Modifica scheda' }).click()
    await expect(page.locator('.archive-edit').getByLabel(task.field).first()).toHaveValue(task.value)
  }
})

test('API scoped: archivi finanziari paginazione server-side oltre 500 record e ricerca', async ({ page }) => {
  const writes: Write[] = []
  await mock(page, writes)
  const queries: Record<string, string>[] = []
  await page.route('**/api/method/centrochange_core.finance.reporting.records*', async route => {
    const params = Object.fromEntries(new URL(route.request().url()).searchParams)
    queries.push(params)
    const offset = Number(params.offset ?? 0)
    const search = params.search ?? ''
    const dt = params.doctype ?? 'Sales Invoice'
    if (search === '520') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          message: {
            rows: [{ name: `${dt}-0520`, docstatus: 1, customer: 'CUS-520', supplier: 'SUP-520', reference_number: 'REF-520', posting_date: today, date: today, grand_total: 120, outstanding_amount: 0, deposit: 120, withdrawal: 0, unallocated_amount: 0 }],
            has_more: false
          }
        })
      })
      return
    }
    const row = { name: `${dt}-PAGE-${offset}`, docstatus: 1, customer: 'CUS-001', supplier: 'SUP-001', reference_number: 'REF-001', posting_date: today, date: today, grand_total: 80, outstanding_amount: 0, deposit: 80, withdrawal: 0, unallocated_amount: 0 }
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ message: { rows: [row], has_more: offset < 500 } })
    })
  })
  await openArchives(page)
  const nav = page.getByRole('navigation', { name: 'Tipi di archivio' })
  for (const label of ['Fatture pazienti', 'Fatture professionisti', 'Movimenti bancari']) {
    await nav.getByRole('button', { name: label, exact: true }).click()
    await expect(page.getByRole('button', { name: 'Carica altri' })).toBeVisible()
    await page.getByRole('button', { name: 'Carica altri' }).click()
    await expect(page.locator('.archive-panel tbody tr')).toHaveCount(2)
    await page.getByLabel(`Cerca in ${label.toLocaleLowerCase('it-IT')}`).fill('520')
    await expect(page.locator('.archive-panel tbody tr')).toHaveCount(1)
    await expect(page.locator('.archive-panel tbody tr').first()).toContainText('520')
  }
  expect(queries.some(q => q.doctype === 'Sales Invoice' && q.limit === '100' && Number(q.offset) > 0)).toBe(true)
  expect(queries.some(q => q.doctype === 'Purchase Invoice' && q.limit === '100' && q.search === '520')).toBe(true)
  expect(queries.some(q => q.doctype === 'Bank Transaction' && q.limit === '100' && q.search === '520')).toBe(true)
})

test('ricerca server-side mantiene un risultato trovato per codice anche se il nome visibile è diverso', async ({ page }) => {
  await mock(page, [])
  await page.route('**/api/method/centrochange_core.operations.workspace.patient_search*', async route => {
    const query = new URL(route.request().url()).searchParams.get('query') ?? ''
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ message: {
        patients: query === 'PAT-REMOTE-520' ? [{ name: 'PAT-REMOTE-520', patient_name: 'Mario Rossi', first_name: 'Mario', last_name: 'Rossi', modified: 'v1' }] : [],
        truncated: false
      } })
    })
  })
  await page.goto('./#Pazienti')
  await page.getByLabel('Cerca pazienti').fill('PAT-REMOTE-520')
  await expect(page.locator('tbody tr')).toHaveCount(1)
  await expect(page.locator('tbody tr').first()).toContainText('Mario Rossi')
})

test('GOAL-75: scheda Paziente usa pagina e schede, conserva il collegamento e ritorna alla ricerca', async ({ page }, info) => {
  await mock(page, [])
  await page.goto('./')
  if ((page.viewportSize()?.width ?? 1440) < 760) await page.getByRole('button', { name: 'Apri menu' }).click()
  await page.getByRole('button', { name: 'Pazienti', exact: true }).click()
  await page.getByRole('textbox', { name: 'Cerca pazienti' }).fill('Paziente')
  await page.locator('tbody tr').first().click()
  await expect(page.locator('.patient-detail-page')).toBeVisible()
  await expect(page).toHaveURL(/patient=PAT-001/)
  await expect(page.getByRole('navigation', { name: 'Sezioni della scheda paziente' })).toBeVisible()
  await page.getByRole('button', { name: 'Riepilogo', exact: true }).click()
  await expect(page.locator('.patient-tab-notes')).toBeVisible()
  await page.screenshot({ path: info.outputPath(`paziente-scheda-${info.project.name}.png`), fullPage: true })
  await page.reload()
  await expect(page.locator('.patient-detail-page')).toBeVisible()
  await page.getByRole('button', { name: 'Torna ai pazienti' }).click()
  await expect(page.getByRole('textbox', { name: 'Cerca pazienti' })).toBeVisible()
  await expect(page).not.toHaveURL(/patient=/)
})

test('GOAL-75: accessi usa ricerca e conferma esplicita della disattivazione globale', async ({ page }, info) => {
  await mock(page, [])
  await page.goto('./')
  if ((page.viewportSize()?.width ?? 1440) < 760) await page.getByRole('button', { name: 'Apri menu' }).click()
  await page.getByRole('button', { name: 'Gestione accessi', exact: true }).click()
  const statusCell = page.locator('.access-memberships tbody tr').first().locator('td').last()
  await statusCell.scrollIntoViewIfNeeded()
  await expect(statusCell).toBeInViewport({ ratio: 1 })
  expect(await page.locator('.access-memberships .table-scroll').evaluate(el => el.scrollWidth <= el.clientWidth)).toBe(true)
  await page.getByRole('button', { name: 'Stato professionista' }).click()
  const dialog = page.getByRole('dialog', { name: 'Stato professionista' })
  await dialog.getByRole('combobox', { name: 'Professionista' }).fill('Sintetico')
  await dialog.getByRole('option', { name: 'Professionista Sintetico' }).click()
  await dialog.getByLabel('Nuovo stato').selectOption('0')
  await expect(dialog.getByRole('alert')).toContainText('tutte le sedi')
  await dialog.getByLabel('Motivo della modifica').fill('Test sintetico')
  await dialog.getByRole('button', { name: 'Rivedi modifica' }).click()
  await expect(dialog.getByRole('alert')).toContainText('tutte le sedi')
  await page.screenshot({ path: info.outputPath(`accessi-disattivazione-${info.project.name}.png`), fullPage: true })
})

test('GOAL-75: registro rende leggibile il motivo di sistema e conserva l’originale', async ({ page }, info) => {
  await mock(page, [])
  await page.goto('./')
  if ((page.viewportSize()?.width ?? 1440) < 760) await page.getByRole('button', { name: 'Apri menu' }).click()
  await page.getByRole('button', { name: 'Registro modifiche', exact: true }).click()
  await expect(page.locator('tbody')).toContainText('Chiusura automatica alla scadenza')
  await page.locator('tbody tr').first().click()
  const drawer = page.getByRole('dialog')
  await drawer.getByText('Motivo originale registrato').click()
  await expect(drawer).toContainText('07:00 local cutoff catch-up')
  await page.screenshot({ path: info.outputPath(`registro-motivo-${info.project.name}.png`), fullPage: true })
})

test('GOAL-75: un deep link paziente negato non monta note o azioni di assegnazione', async ({ page }) => {
  await mock(page, [])
  await page.route('**/api/method/centrochange_core.operations.profiles.patient_detail*', route =>
    route.fulfill({ status: 403, contentType: 'application/json', body: JSON.stringify({ exc: 'PermissionError' }) }))
  await page.goto('./?patient=PAT-FOREIGN#Pazienti')
  await expect(page.locator('.patient-detail-page')).toBeVisible()
  await expect(page.locator('.patient-detail-page').getByRole('alert')).toBeVisible()
  await expect(page.locator('.patient-tab-notes')).toHaveCount(0)
  await expect(page.getByRole('button', { name: 'Gestisci assegnazione' })).toHaveCount(0)
})

test('GOAL-75: rettifica nota riservata conserva il tipo e il riferimento originale', async ({ page }) => {
  const writes: Write[] = []
  await mock(page, writes, 'CC Professional')
  await page.goto('./')
  if ((page.viewportSize()?.width ?? 1440) < 760) await page.getByRole('button', { name: 'Apri menu' }).click()
  await page.getByRole('button', { name: 'Pazienti', exact: true }).click()
  await page.locator('tbody tr').first().click()
  await page.getByRole('button', { name: 'Riepilogo', exact: true }).click()
  await expect(page.locator('.patient-tab-notes')).toContainText('Nota riservata di prova')
  await page.locator('.note.private').getByRole('button', { name: 'Rettifica' }).click()
  await expect(page.locator('.patient-tab-notes')).toContainText('Rettifica di una nota professionale riservata')
  await expect(page.locator('.note-kind')).toHaveCount(0)
  await page.getByRole('textbox', { name: 'Testo della rettifica' }).fill('Rettifica riservata sintetica')
  await page.getByRole('button', { name: 'Registra rettifica' }).click()
  await expect.poll(() => writes.find(write => write.method.endsWith('operations.notes.add_note'))?.body).toMatchObject({ private: 1, corrects: 'PRIV-001' })
})

test('GOAL75: registro distingue note e motivi automatici preservando il testo libero', async ({ page }) => {
  await mock(page, [])
  const base = { event_time: '2026-10-27 07:00:00', reference_name: 'SYN-1', before_state: '{}', after_state: '{}', actor: 'manager@example.invalid' }
  const events = [
    { ...base, event_type: 'ORGANIZATIONAL_NOTE_CREATED', reason: 'Protected note entry' },
    { ...base, event_type: 'ORGANIZATIONAL_NOTE_CREATED', reason: 'Protected note revision' },
    { ...base, event_type: 'PRIVATE_NOTE_CREATED', reason: 'Protected note entry' },
    { ...base, event_type: 'PRIVATE_NOTE_CREATED', reason: 'Protected note revision' },
    { ...base, event_type: 'ADMIN_EXCEPTION_DETECTED', actor: 'cc-automation-service@example.invalid', reason: 'Scheduled administrative condition reconciliation' },
    { ...base, event_type: 'PAYMENT_BLOCK_NOTIFIED', actor: 'cc-automation-service@example.invalid', reason: 'Scheduled payment-rule catch-up' },
    { ...base, event_type: 'ADMIN_EXCEPTION_MANAGED', reason: 'Scheduled payment-rule catch-up' }
  ]
  await page.route('**/api/method/centrochange_core.security.audit_view.events*', route => route.fulfill({ contentType: 'application/json', body: JSON.stringify({ message: { events, has_more: false } }) }))
  await page.goto('./#Registro%20modifiche')
  const rows = page.locator('tbody tr')
  await expect(rows).toHaveCount(7)
  await expect(rows.nth(0)).toContainText('Registrazione di nota organizzativa')
  await expect(rows.nth(1)).toContainText('Rettifica di nota organizzativa')
  await expect(rows.nth(2)).toContainText('Registrazione di nota professionale riservata')
  await expect(rows.nth(3)).toContainText('Rettifica di nota professionale riservata')
  await expect(rows.nth(4)).toContainText('Servizio automatico')
  await expect(rows.nth(4)).toContainText('Verifica automatica delle condizioni amministrative')
  await expect(rows.nth(5)).toContainText('Verifica automatica delle regole di pagamento')
  await expect(rows.nth(6)).toContainText('Scheduled payment-rule catch-up')
  await rows.nth(0).click()
  const detail = page.getByRole('dialog')
  await detail.getByText('Motivo originale registrato').click()
  await expect(detail).toContainText('Protected note entry')
  await detail.getByText('Dettagli tecnici').click()
  await expect(detail).toContainText('ORGANIZATIONAL_NOTE_CREATED')
})

test('Professionista: modifica operativa senza passare da Archivi', async ({ page }) => {
  await mock(page, [])
  await page.goto('./?practitioner=PR-001#Professionisti')
  await expect(page.getByRole('link', { name: 'Modifica professionista negli Archivi' })).toHaveCount(0)
  await page.getByRole('button', { name: 'Modifica professionista' }).click()
  await expect(page.getByRole('textbox', { name: /^Nome/ })).toHaveValue('Professionista')
  await expect(page.getByRole('textbox', { name: 'Cognome', exact: true })).toHaveValue('Sintetico')
  await expect(page.getByLabel('Motivo della modifica')).toBeVisible()
})

test('GOAL75: movimento bancario deep link usa la proiezione autorizzata anche oltre la prima pagina', async ({ page }) => {
  await mock(page, [])
  let searchedPages = 0
  await page.route('**/api/method/centrochange_core.finance.reporting.records*', route => {
    const params = new URL(route.request().url()).searchParams
    if (params.get('doctype') !== 'Bank Transaction') return route.fallback()
    const search = params.get('search') || '', offset = Number(params.get('offset') || 0)
    if (!search) return route.fulfill({ contentType: 'application/json', body: JSON.stringify({ message: { rows: [{ name: 'BANK-001', date: today, reference_number: 'SYN-001', deposit: 60, withdrawal: 0 }], has_more: false } }) })
    searchedPages++
    const data = search === 'BANK-001' ? offset === 0 ? { rows: Array.from({ length: 100 }, (_, i) => ({ name: `OTHER-${i}` })), has_more: true } : { rows: [{ name: 'BANK-001', date: today, reference_number: 'SYN-001', deposit: 60, withdrawal: 0 }], has_more: false } : { rows: [], has_more: false }
    return route.fulfill({ contentType: 'application/json', body: JSON.stringify({ message: data }) })
  })
  await openArchives(page)
  await page.getByRole('navigation', { name: 'Tipi di archivio' }).getByRole('button', { name: 'Movimenti bancari' }).click()
  await page.locator('.archive-panel tbody tr').first().click()
  await expect(page.locator('.archive-detail-page')).toContainText('SYN-001')
  await page.reload()
  await expect(page.locator('.archive-detail-page')).toContainText('SYN-001')
  expect(searchedPages).toBeGreaterThanOrEqual(2)
  await page.goto('./?archive_kind=Bank+Transaction&archive_record=OTHER-CENTER#Archivi')
  await expect(page.getByRole('alert')).toContainText('Scheda non disponibile')
  await expect(page.locator('.archive-detail-page')).toHaveCount(0)
})

test('GOAL75: focus torna al comando dopo annullamento creazione e conferma', async ({ page }) => {
  await mock(page, [])
  await openArchives(page)
  await page.getByRole('navigation', { name: 'Tipi di archivio' }).getByRole('button', { name: 'Modelli pacchetto' }).click()
  const create = page.getByRole('button', { name: 'Nuova scheda' })
  await create.click()
  await expect(page.locator('.archive-edit h2')).toBeFocused()
  await page.keyboard.press('Escape')
  await expect(create).toBeFocused()
  await page.locator('.archive-panel tbody tr').first().click()
  await page.getByRole('button', { name: 'Modifica scheda' }).click()
  await page.locator('.archive-edit').getByLabel('Modello').fill('Modificato')
  await page.locator('.archive-edit').getByLabel('Motivo').fill('Prova')
  await page.getByRole('button', { name: 'Rivedi modifica' }).click()
  await expect(page.locator('.archive-review h2')).toBeFocused()
  await page.keyboard.press('Escape')
  await expect(page.locator('.archive-edit h2')).toBeFocused()
})

test('GOAL75: collegamento anagrafico conserva la sede scelta', async ({ page }) => {
  await mock(page, [])
  const centers = [boot.centers[0], { name: 'CENTRO-B', branch: 'Centro B' }]
  const detailCenters: string[] = []
  await page.route('**/api/method/centrochange_core.operations.workspace.bootstrap*', route => {
    const selected = new URL(route.request().url()).searchParams.get('center') || center
    return route.fulfill({ contentType: 'application/json', body: JSON.stringify({ message: { ...boot, centers, center: selected } }) })
  })
  await page.route('**/api/method/centrochange_core.operations.profiles.practitioner_detail*', route => {
    detailCenters.push(new URL(route.request().url()).searchParams.get('center') || '')
    return route.fulfill({ contentType: 'application/json', body: JSON.stringify({ message: { name: 'PR-001', practitioner_name: 'Professionista Sintetico', first_name: 'Professionista', last_name: 'Sintetico', status: 'Active', modified: 'v1' } }) })
  })
  await page.goto('./?center=CENTRO-B&practitioner=PR-001#Professionisti')
  await page.getByRole('button', { name: 'Modifica professionista' }).click()
  await expect(page.locator('.professional-detail-page')).toContainText('Professionista Sintetico')
  expect(new URL(page.url()).searchParams.get('center')).toBe('CENTRO-B')
  expect(detailCenters.length).toBeGreaterThanOrEqual(1)
  expect(detailCenters.every(value => value === 'CENTRO-B')).toBe(true)
  await page.reload()
  await expect(page.locator('.professional-detail-page')).toContainText('Professionista Sintetico')
  expect(detailCenters.every(value => value === 'CENTRO-B')).toBe(true)
})

test('GOAL75: cronologia mantiene sincronizzata la sede con la URL', async ({ page }) => {
  await mock(page, [])
  const centers = [boot.centers[0], { name: 'CENTRO-B', branch: 'Centro B' }]
  await page.route('**/api/method/centrochange_core.operations.workspace.bootstrap*', route => {
    const selected = new URL(route.request().url()).searchParams.get('center') || center
    return route.fulfill({ contentType: 'application/json', body: JSON.stringify({ message: { ...boot, centers, center: selected } }) })
  })
  await page.goto('./?center=CENTRO-A#Archivi')
  await page.locator('.archive-panel tbody tr').first().click()
  await expect(page.locator('.archive-detail-page')).toBeVisible()
  const selector = page.locator('.center-selector select')
  await selector.selectOption('CENTRO-B')
  await expect(selector).toHaveValue('CENTRO-B')
  await page.goBack()
  await expect.poll(() => new URL(page.url()).searchParams.get('center')).toBe('CENTRO-A')
  await expect(selector).toHaveValue('CENTRO-A')
})

test('Nuovo professionista: creazione con account personale autorizzato', async ({ page }) => {
  await mock(page, [])
  let payload: Record<string, unknown> | undefined
  await page.route('**/api/method/centrochange_core.operations.profiles.practitioner_access_candidates*', route => route.fulfill({ contentType: 'application/json', body: JSON.stringify({ message: [{name:'professionista@example.invalid', label:'Professionista Prova'}] }) }))
  await page.route('**/api/method/centrochange_core.operations.profiles.practitioner_create', route => {
    payload = route.request().postDataJSON()
    return route.fulfill({ contentType: 'application/json', body: JSON.stringify({ message: { name: 'PR-NEW', modified: 'v1' } }) })
  })
  await page.route('**/api/method/centrochange_core.operations.profiles.practitioner_detail*', route => route.fulfill({ contentType: 'application/json', body: JSON.stringify({ message: { name: 'PR-NEW', practitioner_name: 'Professionista Prova', first_name: 'Professionista', last_name: 'Prova', status: 'Active', user_id: 'professionista@example.invalid', email_id: 'professionista@example.invalid', modified: 'v1' } }) }))
  await page.goto('./#Professionisti')
  await page.getByRole('button', { name: 'Nuovo professionista' }).click()
  const form = page.getByRole('dialog', { name: 'Nuovo professionista' })
  await form.getByLabel(/^Nome/).fill('Professionista')
  await form.getByLabel('Cognome').fill('Prova')
  await form.getByLabel('Email').fill('professionista@example.invalid')
  await form.getByLabel('Account personale').selectOption('professionista@example.invalid')
  await form.getByLabel('Cellulare').fill('000123')
  await form.getByLabel('Motivo').fill('Prova sintetica')
  await form.getByRole('button', { name: 'Crea professionista' }).click()
  await expect(page.getByText('Accesso personale collegato')).toBeVisible()
  expect(payload).toMatchObject({ center, first_name:'Professionista', last_name:'Prova', email:'professionista@example.invalid', mobile_phone:'000123' })
  expect(payload).toHaveProperty('user', 'professionista@example.invalid')
})

test('Professionista: modifica precompilata e auditata dal profilo', async ({ page }) => {
  const writes: Write[] = []
  await mock(page, writes)
  await page.goto('./?practitioner=PR-001#Professionisti')
  await page.getByRole('button', { name: 'Modifica professionista', exact: true }).click()
  const form = page.locator('.professional-detail-page form')
  await expect(form.getByLabel(/^Nome/)).toHaveValue('Professionista')
  await expect(form.getByLabel('Cognome', { exact: true })).toHaveValue('Sintetico')
  await form.getByLabel(/^Nome/).fill('Nome sintetico')
  await form.getByLabel('Email', { exact: true }).fill('professionista@example.invalid')
  await form.getByLabel('Motivo della modifica').fill('Correzione sintetica')
  await form.getByRole('button', { name: 'Salva modifiche' }).click()
  await expect.poll(() => writes.find(w => w.method.endsWith('profiles.practitioner_save'))).toBeTruthy()
  const payload = writes.find(w => w.method.endsWith('profiles.practitioner_save'))!.body
  expect(payload).toMatchObject({ center, name:'PR-001', first_name:'Nome sintetico', email:'professionista@example.invalid', expected_version:'v1', reason:'Correzione sintetica' })
})
