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
    'Sales Invoice': [{ name: 'SINV-001', customer: 'CUS-001', posting_date: today, grand_total: 80, outstanding_amount: 20 }],
    'Purchase Invoice': [{ name: 'PINV-001', supplier: 'SUP-001', posting_date: today, grand_total: 40, outstanding_amount: 10 }],
    'Payment Entry': [{ name: 'PAY-001', party: 'CUS-001', posting_date: today, payment_type: 'Receive', paid_amount: 60, unallocated_amount: 0, modified: 'v1', references: [] }],
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
    } else if (method.endsWith('finance.documents.preview')) message = { doctype: args.doctype, name: args.name, format: 'Standard', html: '<html><body><h1>Documento sintetico</h1></body></html>' }
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

test('AUDIT-05: archivio professionisti usa alias solo in lettura, editor mantiene il dato canonico', async ({ page }, info) => {
  await mock(page, [])
  const row = { name: 'PR-SYNTH', practitioner_name: 'CC-HTTP-AbCd123456 a', first_name: 'CC-HTTP-AbCd123456 a', last_name: '', status: 'Active' }
  await page.route('**/api/method/centrochange_core.operations.profiles.practitioners*', route =>
    route.fulfill({ contentType: 'application/json', body: JSON.stringify({ message: { rows: [row], has_more: false } }) }))
  await page.route('**/api/method/centrochange_core.operations.profiles.practitioner_detail*', route =>
    route.fulfill({ contentType: 'application/json', body: JSON.stringify({ message: row }) }))
  await openArchives(page)
  await page.getByRole('navigation', { name: 'Tipi di archivio' }).getByRole('button', { name: 'Professionisti', exact: true }).click()
  await expect(page.locator('tbody')).toContainText('Professionista di prova A')
  await expect(page.locator('tbody')).not.toContainText('CC-HTTP-AbCd123456 a')
  await page.locator('tbody tr').click()
  const drawer = page.getByRole('dialog')
  await expect(drawer.getByRole('heading', { name: 'Dettaglio' })).toBeVisible()
  await expect(drawer.getByRole('heading', { name: 'Professionista di prova A' })).toHaveCount(1)
  await expect(drawer).not.toContainText('CC-HTTP-AbCd123456 a')
  await page.screenshot({ path: `../../docs/evidence/issue-171/professionisti-archivio-${info.project.name}.png`, fullPage: true })
  await drawer.getByRole('button', { name: 'Modifica scheda' }).click()
  await expect(page.getByRole('dialog', { name: 'Modifica · Professionisti' }).getByRole('textbox', { name: 'Nome *', exact: true })).toHaveValue(row.first_name)
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
  await expect(page.locator('.archive-panel tbody tr')).toHaveCount(1)
})

test('API catalogo: 11 liste, dettaglio, salvataggio con CSRF e anteprima stampa', async ({ page }, testInfo) => {
  const writes: Write[] = []
  await mock(page, writes)
  await openArchives(page)
  for (const name of ['Pazienti', 'Professionisti', 'Articoli', 'Tariffe', 'Tipi seduta', 'Servizi del centro', 'Modelli pacchetto', 'Fatture pazienti', 'Fatture professionisti', 'Pagamenti', 'Movimenti bancari']) {
    await page.getByRole('navigation', { name: 'Tipi di archivio' }).getByRole('button', { name, exact: true }).click()
    await expect(page.locator('.archive-panel tbody tr')).toHaveCount(1)
    await page.locator('.archive-panel tbody tr').first().click()
    await expect(page.getByRole('dialog')).toBeVisible()
    if (name === 'Pagamenti') {
      await page.getByRole('button', { name: 'Anteprima e stampa' }).click()
      await expect(page.getByTitle('Documento PAY-001')).toBeVisible()
      await expect(page.getByTitle('Documento PAY-001')).toHaveAttribute('sandbox', 'allow-same-origin allow-modals')
      await page.getByTitle('Documento PAY-001').evaluate(element => { const frame = element as HTMLIFrameElement; frame.contentWindow!.print = () => frame.setAttribute('data-printed', 'yes') })
      await page.getByRole('dialog', { name: /Anteprima/ }).getByRole('button', { name: 'Stampa' }).click()
      await expect(page.getByTitle('Documento PAY-001')).toHaveAttribute('data-printed', 'yes')
      await page.getByRole('dialog', { name: /Anteprima/ }).getByRole('button', { name: 'Chiudi' }).first().click()
    }
    await page.screenshot({ path: `../../docs/evidence/issue-148/scoped-${name.toLowerCase().replaceAll(' ', '-')}-${testInfo.project.name}.png`, fullPage: true })
    await page.getByRole('dialog').getByRole('button', { name: 'Chiudi' }).click()
  }
  await page.getByRole('navigation', { name: 'Tipi di archivio' }).getByRole('button', { name: 'Articoli' }).click()
  await page.locator('.archive-panel tbody tr').first().click()
  await page.getByRole('button', { name: 'Modifica scheda' }).click()
  await page.getByRole('dialog', { name: /Modifica/ }).getByLabel('Articolo').fill('Visita sintetica aggiornata')
  await page.getByRole('dialog', { name: /Modifica/ }).getByLabel('Motivo').fill('Aggiornamento prova')
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
  const form = page.getByRole('dialog', { name: /Nuova scheda/ })
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
  const form = page.getByRole('dialog', { name: /Nuova scheda/ })
  for (const [label, value] of Object.entries(task.fields)) await form.getByLabel(label).first().fill(value)
  await form.getByLabel('Motivo').fill('Creazione sintetica')
  await form.getByRole('button', { name: /Rivedi (dati|modifica)/ }).click()
  await page.getByRole('button', { name: 'Conferma salvataggio' }).click()
  await expect(page.getByText(/Scheda salvata/)).toBeVisible()
  expect(writes).toHaveLength(1)
  expect(writes[0].method).toContain(task.method)
})

test('API scoped: professionista vede solo profilo, nessuna scrittura o finanza', async ({ page }) => {
  const writes: Write[] = []
  await mock(page, writes, 'CC Professional')
  await openArchives(page)
  const nav = page.getByRole('navigation', { name: 'Tipi di archivio' })
  await expect(nav.getByRole('button', { name: 'Articoli' })).toHaveCount(0)
  await expect(nav.getByRole('button', { name: 'Pagamenti' })).toHaveCount(0)
  await nav.getByRole('button', { name: 'Professionisti' }).click()
  await page.locator('.archive-panel tbody tr').first().click()
  await expect(page.getByRole('button', { name: 'Modifica scheda' })).toHaveCount(0)
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
  const form = page.getByRole('dialog', { name: /Modifica/ })
  await form.getByLabel('Articolo').fill('Nome aggiornato')
  await form.getByRole('button', { name: 'Rivedi modifica' }).click()
  await expect(form.getByRole('alert')).toContainText('motivo')
  expect(writes).toEqual([])
  await form.getByLabel('Motivo').fill('Prova diniego')
  await form.getByRole('button', { name: 'Rivedi modifica' }).click()
  await page.getByRole('button', { name: 'Conferma salvataggio' }).click()
  await expect(page.getByRole('dialog', { name: /Modifica/ })).toBeVisible()
  await expect(page.getByRole('alert').first()).toContainText('Accesso negato')
  await expect(page.getByText(/Scheda salvata/)).toHaveCount(0)
})

for (const task of [
  { section: 'Pazienti', field: 'Nome', value: 'Persona aggiornata', method: 'operations.profiles.patient_save' },
  { section: 'Professionisti', field: 'Nome', value: 'Professionista aggiornata', method: 'operations.profiles.practitioner_save' },
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
  const form = page.getByRole('dialog', { name: /Modifica/ })
  if (task.field === 'Stato') await form.getByLabel(task.field).first().selectOption(task.value)
  else await form.getByLabel(task.field).first().fill(task.value)
  await form.getByLabel('Motivo').fill('Revisione sintetica')
  await form.getByRole('button', { name: /Rivedi (dati|modifica)/ }).click()
  await page.getByRole('button', { name: 'Conferma salvataggio' }).click()
  await expect(page.getByText(/Scheda salvata/)).toBeVisible()
  expect(writes).toHaveLength(1)
  expect(writes[0].method).toContain(task.method)
  expect(writes[0].body).not.toHaveProperty('customer')
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
  await page.route('**/api/method/centrochange_core.operations.profiles.patients*', async route => {
    const query = new URL(route.request().url()).searchParams.get('search') ?? ''
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ message: {
        rows: query === 'PAT-REMOTE-520' ? [{ name: 'PAT-REMOTE-520', patient_name: 'Mario Rossi', first_name: 'Mario', last_name: 'Rossi', modified: 'v1' }] : [],
        has_more: false
      } })
    })
  })
  await openArchives(page)
  await page.getByLabel('Cerca in pazienti').fill('PAT-REMOTE-520')
  await expect(page.locator('.archive-panel tbody tr')).toHaveCount(1)
  await expect(page.locator('.archive-panel tbody tr').first()).toContainText('Mario Rossi')
})
