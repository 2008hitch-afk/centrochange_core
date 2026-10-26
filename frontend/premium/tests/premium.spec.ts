import { expect, test, type Locator, type Page } from '@playwright/test'
import type { Appointment } from '../src/api'
import { configureDemoLabels, demoPatient, demoText, syntheticCode } from '../src/demo_labels'
import { auditActorName, economyName, practitionerNameFor } from '../src/display_names'
import { availableUnitLabel, sessionCountLabel } from '../src/patient_packages'
import { parseItalianDate } from '../src/ui'

async function chooseCombo(scope: Page | Locator, label: string | RegExp, value: string) {
  const field = scope.getByRole('combobox', { name: label })
  await field.click()
  await field.locator('..').locator('..').locator(`[role="option"][data-value="${value}"]`).click()
  await expect(field).not.toHaveAttribute('aria-expanded', 'true')
}

test('AUDIT-04 UX-04-04: quantità 0/1/2 leggibili nelle due select', () => {
  expect([0, 1, 2].map(sessionCountLabel)).toEqual(['0 sedute', '1 seduta', '2 sedute'])
  expect([0, 1, 2].map(availableUnitLabel)).toEqual(['0 unità disponibili', '1 unità disponibile', '2 unità disponibili'])
})

test('AUDIT-04 UX: pacchetto mostra il nome professionista senza codice fixture', () => {
  const id = 'CC-HTTP-AbCd123456 a'
  expect(practitionerNameFor(id, [{ name: id, practitioner_name: id }])).toBe('Professionista di prova A')
  expect(practitionerNameFor('PR-001', [{ name: 'PR-001', practitioner_name: 'Dott.ssa Rossi' }])).toBe('Dott.ssa Rossi')
})

test('AUDIT-05: identità sintetica resta leggibile dopo modifica autorizzata del cognome', () => {
  const id = 'CC-HTTP-a5f3ce4696 a Professionista'
  expect(syntheticCode(id)).toBe(true)
  expect(practitionerNameFor('PR-TEST', [{ name: 'PR-TEST', practitioner_name: id }])).toBe('Professionista di prova A')
})

test('AUDIT-03: historical state and owned synthetic audit actor stay readable', () => {
  expect(economyName('Pending')).toBe('Da definire')
  expect(auditActorName('cc-http-1234567890-m@example.invalid')).toBe('Manager di prova')
  expect(auditActorName('maria.rossi@example.invalid')).toBe('maria.rossi@example.invalid')
})

test('AUDIT-03: vista giorno usa la stessa etichetta servizio della settimana', async ({ page }) => {
  const service = 'CC-HTTP-AbCd123456 SESSION'
  await mockApi(page, [], true, {}, {}, [{ ...appointment, cc_service_label: service }])
  await page.goto('./#Agenda')
  await page.getByRole('button', { name: 'Giorno', exact: true }).click()
  await expect(page.locator('.rbc-event')).toContainText('Servizio di prova')
  await expect(page.locator('.rbc-event')).not.toContainText(service)
})

test('AUDIT-03: una seduta futura non offre chiusura anticipata', async ({ page }) => {
  const future = new Date(`${today}T12:00:00Z`)
  future.setUTCDate(future.getUTCDate() + 7)
  await mockApi(page, [], true, {}, {}, [{ ...appointment, appointment_date: future.toISOString().slice(0, 10) }])
  await page.goto('./#Agenda')
  await page.getByRole('button', { name: 'Periodo successivo' }).click()
  await page.locator('.week-event').first().click()
  const drawer = page.getByRole('dialog')
  await expect(drawer.getByRole('button', { name: 'Sposta', exact: true })).toBeVisible()
  await expect(drawer.getByRole('button', { name: 'Chiudi seduta' })).toHaveCount(0)
})

test('AUDIT-03: spostamento bloccato mostra due debiti e deroga contestuale autorizzata', async ({ page }, info) => {
  const future = new Date(`${today}T12:00:00Z`)
  future.setUTCDate(future.getUTCDate() + 7)
  const day = future.toISOString().slice(0, 10)
  const writes: { method: string; body: Record<string, unknown>; headers: Record<string, string> }[] = []
  await mockApi(page, writes, true, {}, {}, [{ ...appointment, appointment_date: day }])
  await page.route('**/api/method/centrochange_core.scheduling.booking.reschedule*', async route => {
    const method = new URL(route.request().url()).pathname
    if (method.endsWith('reschedule_payment_blockers')) {
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ message: { blocked: true, can_override: true, debts: [
        { center: 'CENTRO-A', reference_doctype: 'Sales Invoice', reference_name: 'INV-1', amount: 80, currency: 'EUR', due_date: today, original_due_date: today },
        { center: 'CENTRO-A', reference_doctype: 'Patient Appointment', reference_name: 'APP-OLD', amount: 40, currency: 'EUR', due_date: today, original_due_date: today }
      ] } }) })
    } else if (method.endsWith('reschedule_with_payment_override')) {
      writes.push({ method, body: route.request().postDataJSON(), headers: route.request().headers() })
      await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ message: { name: 'APP-001', replay: false } }) })
    } else {
      writes.push({ method, body: route.request().postDataJSON(), headers: route.request().headers() })
      await route.fulfill({ status: 417, contentType: 'application/json', body: JSON.stringify({ exc: 'ValidationError', _server_messages: JSON.stringify([JSON.stringify({ message: 'Serve una verifica dei pagamenti prima della prossima seduta: contatta la segreteria.' })]) }) })
    }
  })
  await page.goto('./#Agenda')
  await page.getByRole('button', { name: 'Periodo successivo' }).click()
  await page.locator('.week-event').first().click()
  const drawer = page.getByRole('dialog', { name: 'Paziente Sintetico' })
  await drawer.getByRole('button', { name: 'Sposta', exact: true }).click()
  await drawer.getByRole('textbox', { name: /Motivo/ }).fill('Spostamento di prova')
  await drawer.getByRole('button', { name: 'Conferma', exact: true }).click()
  const popup = page.getByRole('dialog', { name: 'Verifica pagamenti prima dello spostamento' })
  await expect(popup.getByText('Fattura 1')).toBeVisible()
  await expect(popup.getByText('Seduta non fatturata 2')).toBeVisible()
  await page.screenshot({ path: info.outputPath('payment-block-override.png') })
  await popup.getByRole('textbox', { name: 'Motivazione della deroga' }).fill('Deroga di prova')
  await popup.getByRole('button', { name: 'Autorizza e procedi' }).click()
  await expect(popup).toHaveCount(0)
  const action = writes.find(write => write.method.endsWith('reschedule_with_payment_override'))!
  expect(action.body.expected_references).toEqual([
    { reference_doctype: 'Sales Invoice', reference_name: 'INV-1' },
    { reference_doctype: 'Patient Appointment', reference_name: 'APP-OLD' }
  ])
  expect(action.body.override_reason).toBe('Deroga di prova')
  expect(action.headers['x-frappe-csrf-token']).toBe('synthetic-test-token')
})

test('AUDIT-03: utente senza permesso vede blocco ma non può derogare', async ({ page }) => {
  const future = new Date(`${today}T12:00:00Z`)
  future.setUTCDate(future.getUTCDate() + 7)
  await mockApi(page, [], true, {}, { roles: ['CC Professional'] }, [{ ...appointment, appointment_date: future.toISOString().slice(0, 10) }])
  await page.route('**/api/method/centrochange_core.scheduling.booking.reschedule*', async route => {
    if (route.request().method() === 'GET') await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ message: { blocked: true, can_override: false, debts: [] } }) })
    else await route.fulfill({ status: 417, contentType: 'application/json', body: JSON.stringify({ exc: 'ValidationError', _server_messages: JSON.stringify([JSON.stringify({ message: 'Serve una verifica dei pagamenti prima della prossima seduta: contatta la segreteria.' })]) }) })
  })
  await page.goto('./#Agenda')
  await page.getByRole('button', { name: 'Periodo successivo' }).click()
  await page.locator('.week-event').first().click()
  const drawer = page.getByRole('dialog', { name: 'Paziente Sintetico' })
  await drawer.getByRole('button', { name: 'Sposta', exact: true }).click()
  await drawer.getByRole('textbox', { name: /Motivo/ }).fill('Spostamento di prova')
  await drawer.getByRole('button', { name: 'Conferma', exact: true }).click()
  const popup = page.getByRole('dialog', { name: 'Verifica pagamenti prima dello spostamento' })
  await expect(popup.getByText('il tuo ruolo non può autorizzare una deroga')).toBeVisible()
  await expect(popup.getByRole('button', { name: 'Autorizza e procedi' })).toHaveCount(0)
})

test('AUDIT-03: owned synthetic Agenda records show readable labels without changing canonical IDs', () => {
  configureDemoLabels(null, null)
  const tag = 'CC-HTTP-AbCd123456'
  expect(demoPatient(`${tag} OWN`, `${tag} OWN`)).toMatch(/^Anagrafica da completare · scheda [A-Z0-9]+$/)
  expect(demoPatient(`${tag} CROSS`, `${tag} CROSS`)).not.toBe(demoPatient(`${tag} OWN`, `${tag} OWN`))
  expect(demoPatient('CC-MVP-POS-1', 'CC-MVP-POS-1', 'Giulia', 'Neri')).toBe('Giulia Neri')
  expect(demoPatient('CC-MVP-POS-1', 'CC-MVP-POS-1')).not.toContain('CC-MVP')
  expect(demoPatient('CC-MVP-POS-1', 'CC-MVP-POS-1', 'Giulia', '')).toMatch(/^Anagrafica da completare · scheda/)
  expect(demoPatient('CC-MVP-POS-2', 'CC-MVP-POS-2', 'Giulia', '')).not.toBe(demoPatient('CC-MVP-POS-1', 'CC-MVP-POS-1', 'Giulia', ''))
  expect(demoText(`${tag} Session`)).toBe('Servizio di prova')
  expect(demoText(`${tag} PACKAGE`)).toBe('Pacchetto di prova')
  expect(demoText('Servizio reale')).toBe('Servizio reale')
})

test('AUDIT-04 UX: Agenda usa il nome API anche oltre i 500 Patient del bootstrap', async ({ page }) => {
  const row = { ...appointment, patient: 'CC-MVP-POS-501', patient_name: 'CC-MVP-POS-501', patient_first_name: 'Elena', patient_last_name: 'Rossi' }
  await mockApi(page, [], true, {}, { patients: [] }, [row])
  await page.goto('./#Agenda')
  await expect(page.locator('.week-event').first()).toContainText('Elena Rossi')
  await expect(page.locator('.week-event').first()).not.toContainText(row.patient)
})

test('AUDIT-04 UX: nome Marley reale in Agenda e Pazienti, drawer senza duplicati, ricerca contestuale', async ({ page }, info) => {
  const patient = { name: 'CC-MVP-POS-TEST-1', patient_name: 'CC-MVP-POS-TEST-1', first_name: 'Giulia', last_name: 'Neri' }
  const row = { ...appointment, patient: patient.name, patient_name: patient.patient_name, patient_first_name: patient.first_name, patient_last_name: patient.last_name }
  await mockApi(page, [], true, {}, { patients: [patient] }, [row])
  await page.route('**/api/method/centrochange_core.operations.workspace.patient_search*', route =>
    route.fulfill({ contentType: 'application/json', body: JSON.stringify({ message: { patients: [patient], truncated: false } }) }))
  await page.route('**/api/method/centrochange_core.operations.profiles.patient_detail*', route =>
    route.fulfill({ contentType: 'application/json', body: JSON.stringify({ message: { ...patient, email: '', modified: '2026-10-23 12:00:00', active_assignment: true } }) }))
  await page.goto('./#Agenda')
  await expect(page.locator('.week-event').first()).toContainText('Giulia Neri')
  await expect(page.getByRole('combobox', { name: 'Ricerca globale pazienti' })).toHaveCount(0)
  await expect(page.getByRole('button', { name: 'Apri ricerca pazienti' })).toHaveCount(0)
  await page.screenshot({ path: info.outputPath(`audit-04-ux-agenda-${info.project.name}.png`), fullPage: true })
  await openSection(page, 'Pazienti')
  await page.getByRole('textbox', { name: 'Cerca pazienti' }).fill('Giulia')
  await expect(page.locator('tbody')).toContainText('Giulia Neri')
  await expect(page.locator('tbody')).not.toContainText(patient.name)
  await page.screenshot({ path: info.outputPath(`audit-04-ux-list-${info.project.name}.png`), fullPage: true })
  await page.locator('tbody tr').first().click()
  const drawer = page.getByRole('dialog', { name: 'Giulia Neri' })
  await expect(drawer.getByRole('heading', { name: 'Giulia Neri' })).toHaveCount(1)
  await expect(drawer.getByRole('heading', { name: 'Anagrafica' })).toBeVisible()
  await expect(drawer.getByText(patient.name)).toHaveCount(0)
  await page.screenshot({ path: info.outputPath(`audit-04-ux-patient-${info.project.name}.png`), fullPage: true })
  await page.reload()
  await expect(page.locator('tbody')).toContainText('Giulia Neri')
})

const today = new Intl.DateTimeFormat('en-CA', { timeZone: 'Europe/Rome', year: 'numeric', month: '2-digit', day: '2-digit' }).format(new Date())
const todayItalian = `${today.slice(8, 10)}/${today.slice(5, 7)}/${today.slice(0, 4)}`
const boot = { center: 'CENTRO-A', centers: [{ name: 'CENTRO-A', branch: 'Centro A' }], patients: [{ name: 'PAT-001', patient_name: 'Paziente Sintetico' }], practitioners: [{ name: 'PR-001', practitioner_name: 'Dott.ssa Rossi' }], services: [{ name: 'SERV-001', cc_service_label: 'Prima visita', cc_service_item: 'ITEM-001', cc_price_snapshot: 80, cc_currency_snapshot: 'EUR', duration: 60 }], packages: [], payment_methods: ['Contanti'], roles: ['CC Manager', 'CC Secretariat'] }
const financeBoot = { center: 'CENTRO-A', centers: boot.centers, can_write: true, is_manager: true, customers: [], suppliers: [], accounts: [{ name: 'EXP-001', root_type: 'Expense', is_group: 0, disabled: 0 }, { name: 'TAX-001', account_type: 'Tax', is_group: 0, disabled: 0 }], practitioners: boot.practitioners, items: [{ name: 'ITEM-001', item_name: 'Prima visita', is_purchase_item: 1, disabled: 0, is_stock_item: 0 }], assignees: [], simulation_only: true, fiscal_verified: false }
const appointment = { name: 'APP-001', patient: 'PAT-001', patient_name: 'Paziente Sintetico', practitioner: 'PR-001', practitioner_name: 'Dott.ssa Rossi', cc_center: 'CENTRO-A', appointment_date: today, appointment_time: '09:00:00', duration: 60, status: 'Open', cc_closure_state: 'Pending', cc_economic_state: 'Due', cc_paid: 0, cc_performed: 0, cc_service_label: 'Prima visita', cc_price_snapshot: 80, cc_currency_snapshot: 'EUR' }

test('AUDIT-04 scheda paziente: profilo autorizzato, note e storico', async ({ page }, info) => {
  const writes: { method: string; body: Record<string, unknown>; headers: Record<string, string> }[] = []
  await mockApi(page, writes)
  await page.route('**/api/method/centrochange_core.operations.profiles.patient_detail*', route => route.fulfill({ contentType: 'application/json', body: JSON.stringify({ message: { name: 'PAT-001', patient_name: 'Paziente Sintetico', first_name: 'Paziente', last_name: 'Sintetico', email: 'paziente@example.invalid', modified: '2026-10-23 12:00:00' } }) }))
  await page.goto('./#Pazienti')
  await page.locator('tbody tr').first().click()
  const drawer = page.getByRole('dialog', { name: 'Paziente Sintetico' })
  await expect(drawer.getByText('paziente@example.invalid')).toBeVisible()
  await expect(drawer.getByText(todayItalian, { exact: false }).first()).toBeVisible()
  await page.screenshot({ path: info.outputPath(`patients-detail-${info.project.name}.png`), fullPage: true })
  await drawer.getByRole('button', { name: 'Modifica scheda' }).click()
  const edit = page.getByRole('dialog', { name: 'Modifica paziente' })
  await edit.getByRole('textbox', { name: /^Nome \*/ }).fill('Persona')
  await edit.getByRole('textbox', { name: 'Motivo' }).fill('Correzione sintetica')
  await edit.getByRole('button', { name: 'Salva' }).click()
  await expect.poll(() => writes.some(write => write.method.endsWith('operations.profiles.patient_save'))).toBe(true)
  expect(writes.find(write => write.method.endsWith('operations.profiles.patient_save'))?.body).toMatchObject({ center: 'CENTRO-A', name: 'PAT-001', expected_version: '2026-10-23 12:00:00', first_name: 'Persona' })
  await drawer.getByRole('textbox', { name: 'Nuova nota organizzativa' }).fill('Osservazione di prova')
  await drawer.getByRole('button', { name: 'Aggiungi nota' }).click()
  await expect.poll(() => writes.some(write => write.method.endsWith('operations.notes.add_note'))).toBe(true)
  expect(writes.find(write => write.method.endsWith('operations.notes.add_note'))?.body).toMatchObject({ patient: 'PAT-001', center: 'CENTRO-A', private: 0 })
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(page.viewportSize()!.width)
})

test('AUDIT-04 UX-04-08: eventi della seduta nel medesimo drawer, ritorno e tastiera', async ({ page }, info) => {
  await mockApi(page)
  await page.goto('./#Pazienti')
  await page.locator('tbody tr').first().click()
  const drawer = page.locator('.drawer')
  const visit = drawer.getByRole('button', { name: /Apri eventi/ }).first()
  await visit.scrollIntoViewIfNeeded()
  const previous = await drawer.evaluate(element => element.scrollTop)
  await visit.press('Enter')
  await expect(drawer).toHaveAttribute('aria-label', 'Dettaglio seduta')
  await expect(drawer.getByRole('heading', { name: 'Anagrafica' })).toHaveCount(0)
  await expect(drawer.getByRole('heading', { name: 'Eventi della seduta' })).toBeVisible()
  await expect(drawer.getByRole('button', { name: 'Torna alla scheda paziente' })).toBeFocused()
  await expect(page.getByRole('dialog')).toHaveCount(1)
  await page.screenshot({ path: info.outputPath(`patient-appointment-drawer-${info.project.name}.png`), fullPage: true })
  await drawer.getByRole('button', { name: 'Torna alla scheda paziente' }).click()
  await expect(drawer).toHaveAttribute('aria-label', 'Paziente Sintetico')
  await expect(drawer.getByRole('heading', { name: 'Anagrafica' })).toBeVisible()
  await expect(visit).toBeFocused()
  expect(await drawer.evaluate(element => element.scrollTop)).toBeGreaterThanOrEqual(previous - 3)
})

test('AUDIT-04 UX-04-08: sedute A/B non mescolano timeline; vuoto ed errore restano nel drawer', async ({ page }) => {
  await mockApi(page)
  await page.route('**/api/method/centrochange_core.operations.workspace.patient_history*', route =>
    route.fulfill({ contentType: 'application/json', body: JSON.stringify({ message: { appointments: [appointment, { ...appointment, name: 'APP-002', cc_service_label: 'Seconda visita' }], packages: [], organizational_notes: [], private_notes: [], settlements: [] } }) }))
  let failSecond = false
  await page.route('**/api/method/centrochange_core.operations.workspace.appointment_events*', async route => {
    const id = new URL(route.request().url()).searchParams.get('appointment')
    if (id === 'APP-001') {
      await new Promise(resolve => setTimeout(resolve, 250))
      await route.fulfill({ contentType: 'application/json', body: JSON.stringify({ message: [{ event_type: 'APPOINTMENT_BOOKED', event_time: `${today} 11:00:00`, actor: 'manager@example.invalid', reason: 'Evento A' }] }) })
    } else if (failSecond) await route.fulfill({ status: 503, contentType: 'application/json', body: JSON.stringify({ exc: 'Unavailable' }) })
    else await route.fulfill({ contentType: 'application/json', body: JSON.stringify({ message: [] }) })
  })
  await page.goto('./#Pazienti')
  await page.locator('tbody tr').first().click()
  const drawer = page.locator('.drawer')
  await drawer.locator('[data-appointment="APP-001"]').click()
  await expect(drawer.getByRole('status', { name: '' }).filter({ hasText: 'Caricamento eventi' })).toBeVisible()
  await expect(drawer.getByText('Evento A')).toBeVisible()
  await drawer.getByRole('button', { name: 'Torna alla scheda paziente' }).click()
  await drawer.locator('[data-appointment="APP-002"]').click()
  await expect(drawer.getByText('Nessun evento registrato per questa seduta')).toBeVisible()
  await expect(drawer.getByText('Evento A')).toHaveCount(0)
  await drawer.getByRole('button', { name: 'Torna alla scheda paziente' }).click()
  failSecond = true
  await drawer.locator('[data-appointment="APP-002"]').click()
  await expect(drawer.getByRole('alert')).toBeVisible()
  await expect(drawer.getByText('Nessun evento registrato per questa seduta')).toHaveCount(0)
  await expect(page.getByRole('dialog')).toHaveCount(1)
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(page.viewportSize()!.width)
})

test('AUDIT-04 ricerca Pazienti segnala caricamento, troncamento ed errore senza risultati obsoleti', async ({ page }) => {
  await mockApi(page)
  await page.route('**/api/method/centrochange_core.operations.workspace.patient_search*', async route => {
    const query = new URL(route.request().url()).searchParams.get('query')
    if (query === 'lento') await new Promise(resolve => setTimeout(resolve, 500))
    await route.fulfill(query === 'errore'
      ? { status: 503, contentType: 'application/json', body: JSON.stringify({ exc: 'Unavailable' }) }
      : { contentType: 'application/json', body: JSON.stringify({ message: { patients: query === 'nessuno' ? [] : boot.patients, truncated: query === 'molti' } }) })
  })
  await page.goto('./#Pazienti')
  const search = page.getByRole('textbox', { name: 'Cerca pazienti' })
  await search.fill('lento')
  await expect(page.getByRole('status').filter({ hasText: 'Caricamento pazienti' })).toBeVisible()
  await search.fill('molti')
  await expect(page.getByText('Mostrati i primi 50 risultati. Affina la ricerca.')).toBeVisible()
  await search.fill('errore')
  await expect(page.getByRole('alert').filter({ hasText: 'Operazione non riuscita' })).toBeVisible()
  await expect(page.locator('tbody tr')).toHaveCount(0)
  await search.fill('nessuno')
  await expect(page.getByText('Nessun paziente trovato nel centro.')).toBeVisible()
})

test('AUDIT-04 due emissioni volontarie identiche usano chiavi diverse', async ({ page }) => {
  const writes: { method: string; body: Record<string, unknown>; headers: Record<string, string> }[] = []
  await mockApi(page, writes)
  await page.goto('./#Pazienti')
  await page.locator('tbody tr').first().click()
  const drawer = page.getByRole('dialog', { name: 'Paziente Sintetico' })
  await expect(drawer).toBeVisible()
  for (let count = 0; count < 2; count++) {
    await drawer.getByRole('button', { name: 'Emetti pacchetto' }).click()
    await chooseCombo(drawer, 'Modello', 'TEMPLATE-001')
    await drawer.getByRole('textbox', { name: 'Motivo' }).fill('Emissione sintetica')
    await drawer.getByRole('button', { name: 'Conferma' }).click()
    await expect.poll(() => writes.filter(write => write.method.endsWith('operations.packages.issue')).length).toBe(count + 1)
  }
  const keys = writes.filter(write => write.method.endsWith('operations.packages.issue')).map(write => write.body.request_key)
  expect(keys[0]).not.toBe(keys[1])
})

test('AUDIT-04 combobox facoltativo non invia un nome digitato senza selezione', async ({ page }) => {
  const writes: { method: string; body: Record<string, unknown>; headers: Record<string, string> }[] = []
  await mockApi(page, writes)
  await page.goto('./#Pazienti')
  await page.locator('tbody tr').first().click()
  const drawer = page.getByRole('dialog', { name: 'Paziente Sintetico' })
  await drawer.getByRole('button', { name: 'Emetti pacchetto' }).click()
  await chooseCombo(drawer, 'Modello', 'TEMPLATE-001')
  const professional = drawer.getByRole('combobox', { name: 'Professionista dedicato' })
  await professional.fill('Rossi')
  await drawer.getByRole('textbox', { name: 'Motivo' }).fill('Prova senza selezione')
  await expect(professional).toHaveValue('')
  await expect(professional).toHaveAttribute('aria-invalid', 'true')
  await expect(drawer.getByRole('alert', { name: '' })).toContainText('Nessuna voce selezionata')
  await drawer.getByRole('button', { name: 'Conferma' }).click()
  expect(writes.some(write => write.method.endsWith('operations.packages.issue'))).toBe(false)
  await chooseCombo(drawer, 'Professionista dedicato', 'PR-001')
  await expect(professional).toHaveValue('Dott.ssa Rossi')
  await drawer.getByRole('button', { name: 'Conferma' }).click()
  await expect.poll(() => writes.find(write => write.method.endsWith('operations.packages.issue'))?.body.practitioner).toBe('PR-001')
})

test('AUDIT-04 assegnazioni ricercabili e riassegnazione usa servizio scoped', async ({ page }) => {
  const writes: { method: string; body: Record<string, unknown>; headers: Record<string, string> }[] = []
  await mockApi(page, writes, true, {}, { practitioners: [boot.practitioners[0], { name: 'PR-002', practitioner_name: 'Dott. Verdi' }] })
  await page.goto('./#Pazienti')
  await page.locator('tbody tr').first().click()
  const drawer = page.getByRole('dialog', { name: 'Paziente Sintetico' })
  await drawer.getByRole('button', { name: 'Riassegna' }).click()
  await drawer.getByRole('combobox', { name: 'Professionista attuale' }).fill('Rossi')
  await drawer.getByRole('option', { name: 'Dott.ssa Rossi' }).click()
  await drawer.getByRole('combobox', { name: 'Nuovo professionista' }).fill('Verdi')
  await drawer.getByRole('option', { name: 'Dott. Verdi' }).click()
  await drawer.getByRole('textbox', { name: 'Motivo' }).fill('Riassegnazione sintetica')
  await drawer.getByRole('button', { name: 'Conferma' }).click()
  await expect.poll(() => writes.some(write => write.method.endsWith('security.lifecycle.reassign'))).toBe(true)
  expect(writes.find(write => write.method.endsWith('security.lifecycle.reassign'))?.body).toMatchObject({ patient: 'PAT-001', center: 'CENTRO-A', old_practitioner: 'PR-001', new_practitioner: 'PR-002' })
})

test('AUDIT-04 note private solo in vista professionista, edit paziente solo Manager', async ({ page }) => {
  await mockApi(page, [], false, {}, { roles: ['CC Professional'] })
  await page.route('**/api/method/centrochange_core.operations.workspace.patient_history*', route => route.fulfill({ contentType: 'application/json', body: JSON.stringify({ message: { appointments: [], packages: [], organizational_notes: [], private_notes: [{ name: 'PN-1', content: 'Segreto sintetico', authored_by: 'pro@example.invalid', creation: today + ' 12:00:00', corrects: null }], settlements: [] } }) }))
  await page.goto('./#Pazienti')
  await page.locator('tbody tr').first().click()
  const drawer = page.getByRole('dialog', { name: 'Paziente Sintetico' })
  await expect(drawer.getByText('Segreto sintetico')).toBeVisible()
  await expect(drawer.getByRole('button', { name: 'Modifica scheda' })).toHaveCount(0)
  await expect(drawer.getByRole('button', { name: 'Emetti pacchetto' })).toHaveCount(0)
  await expect(drawer.getByRole('button', { name: 'Gestisci assegnazione' })).toHaveCount(0)
})

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
  await page.route('**/api/method/centrochange_core.operations.profiles.patient_detail*', route => {
    const name = new URL(route.request().url()).searchParams.get('name')
    const row = name === patientB.name ? patientB : patientA
    return route.fulfill({ contentType: 'application/json', body: JSON.stringify({ message: {
      ...row, first_name: row.patient_name, last_name: '', email: 'paziente@example.invalid',
      modified: '2026-10-23 12:00:00', active_assignment: true,
    } }) })
  })
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

  await openSection(page, 'Pazienti')
  await page.getByRole('textbox', { name: 'Cerca pazienti' }).fill('Paziente di prova A')
  await page.locator('tbody tr').first().click()
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
  await expect(page.locator('tbody')).toContainText('Anagrafica da completare · scheda')
  await expect(page.locator('tbody')).not.toContainText(patientB.name)
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
    else if (method.endsWith('operations.profiles.practitioners')) {
      const search = (new URL(req.url()).searchParams.get('search') ?? '').toLocaleLowerCase('it-IT')
      message = { rows: (bootState.practitioners ?? boot.practitioners).filter(row => row.practitioner_name.toLocaleLowerCase('it-IT').includes(search)), has_more: false }
    }
    else if (method.endsWith('operations.profiles.practitioner_detail')) message = { name: 'PR-001', practitioner_name: 'Dott.ssa Rossi', status: 'Active' }
    else if (method.endsWith('operations.profiles.patient_detail')) message = { name: 'PAT-001', patient_name: 'Paziente Sintetico', first_name: 'Paziente', last_name: 'Sintetico', email: 'paziente@example.invalid', modified: '2026-10-23 12:00:00' }
    else if (method.endsWith('operations.workspace.patient_search')) message = { patients: boot.patients, truncated: false }
    else if (method.endsWith('operations.workspace.patient_history')) message = { appointments: [{ ...appointment, ...appointmentState }], packages: [], organizational_notes: [{ name: 'NOTE-002', content: 'Nota sintetica rettificata', creation: today + ' 12:00:00', authored_by: 'direzione@example.invalid', corrects: 'NOTE-001' }, { name: 'NOTE-001', content: 'Nota sintetica', creation: today + ' 11:00:00', authored_by: 'direzione@example.invalid', corrects: null }], private_notes: [], settlements: [] }
    else if (method.endsWith('operations.workspace.appointment_events')) message = [
      { event_type: 'APPOINTMENT_BOOKED', actor: 'direzione@example.invalid', event_time: today + ' 08:00:00', reason: 'Prenotazione sintetica', before: {}, after: { appointment_date: today, appointment_time: '09:00:00' } },
      { event_type: 'APPOINTMENT_RESCHEDULED', actor: 'direzione@example.invalid', event_time: today + ' 08:30:00', reason: 'Spostamento sintetico', before: { appointment_date: today, appointment_time: '09:00:00' }, after: { appointment_date: today, appointment_time: '10:00:00' } },
      { event_type: 'SESSION_AUTO_LOCKED', actor: 'scheduler@example.invalid', event_time: today + ' 09:00:00', reason: 'Scadenza sintetica', before: { closure: 'Pending' }, after: { closure: 'Auto Locked' } }
    ]
    else if (method.endsWith('operations.workspace.schedules')) message = [{ name: 'SCHED-001', practitioner: 'PR-001', time_slots: [{ day: 'Monday', from_time: '09:00:00', to_time: '18:00:00' }], absences: [] }]
    else if (method.endsWith('operations.reporting.summary')) message = { currencies: { EUR: { sessions: 1, performed: 0, due: 1, due_snapshot_amount: 80 } }, truncated: false }
    else if (method.endsWith('operations.reporting.sessions')) message = { appointments: [{ ...appointment, ...appointmentState, patient_first_name: 'Paziente', patient_last_name: 'Sintetico', practitioner_name: 'Dott.ssa Rossi', cc_service_label: 'Prima visita', mode_of_payment: 'POS' }], total: 1, truncated: false }
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
  await expect(page.getByRole('dialog', { name: 'Nuova prenotazione' }).getByRole('combobox', { name: 'Professionista' })).toHaveValue('Professionista 2')
  await page.getByRole('dialog').getByRole('button', { name: 'Chiudi' }).click()
  await page.getByLabel('Professionista', { exact: true }).selectOption('PR-002')
  await expect(page.locator('.week-row')).toHaveCount(1)
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(page.viewportSize()!.width)
})

test('AUDIT-03 storico seduta mostra evento, prima/dopo e motivo senza confondere le note', async ({ page }, info) => {
  await mockApi(page)
  await page.goto('./#Agenda')
  await page.locator('.week-event').first().click()
  const drawer = page.getByRole('dialog')
  await drawer.getByRole('tab', { name: 'Storico' }).click()
  await expect(drawer.getByText('Prenotazione spostata')).toBeVisible()
  await expect(drawer.getByText('Seduta bloccata automaticamente')).toBeVisible()
  await expect(drawer.getByText('Spostamento sintetico')).toBeVisible()
  await expect(drawer.getByText('09:00 → 10:00')).toBeVisible()
  await expect(drawer).toContainText(todayItalian)
  await expect(drawer.getByText('Le versioni delle note sono nella scheda Note.')).toBeVisible()
  await page.screenshot({ path: info.outputPath('agenda-storico.png'), fullPage: true })
})

test('AUDIT-03 blocchi settimanali seguono il tempo e conservano giorno e professionista', async ({ page }) => {
  const anchor = new Date(`${today}T12:00:00Z`)
  const monday = new Date(anchor.getTime() - ((anchor.getUTCDay() + 6) % 7) * 86_400_000).toISOString().slice(0, 10)
  await mockApi(page, [], true, {}, {}, [
    { ...appointment, appointment_date: monday, appointment_time: '09:00:00' },
    { ...appointment, name: 'APP-002', appointment_date: monday, appointment_time: '12:00:00' }
  ])
  await page.goto('./#Agenda')
  const cell = page.locator(`.week-cell[data-date="${monday}"][data-practitioner="PR-001"]`)
  await expect(cell.locator('.week-event')).toHaveCount(2)
  const positions = await cell.locator('.week-event').evaluateAll(elements => elements.map(element => ({
    time: element.getAttribute('data-time'), top: element.getBoundingClientRect().top
  })))
  expect(positions.map(item => item.time)).toEqual(['09:00', '12:00'])
  expect(positions[1].top - positions[0].top).toBeGreaterThanOrEqual(140)
  expect(positions[1].top - positions[0].top).toBeLessThanOrEqual(148)
  const labelAndAxis = await page.locator('.week-professional').first().evaluate(element => ({
    labelBottom: element.querySelector('strong')!.getBoundingClientRect().bottom,
    axisTop: element.querySelector('.week-hour-axis span')!.getBoundingClientRect().top
  }))
  expect(labelAndAxis.axisTop).toBeGreaterThan(labelAndAxis.labelBottom)
})

test('AUDIT-03 modifica un giorno senza cancellare le altre fasce e annulla assenza esatta', async ({ page }, info) => {
  const writes: { method: string; body: Record<string, unknown>; headers: Record<string, string> }[] = []
  await mockApi(page, writes)
  await page.route('**/api/method/centrochange_core.operations.workspace.schedules*', async route => {
    await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ message: [{
      name: 'SCHED-001', modified: '2026-10-22 10:00:00', practitioner: 'PR-001', time_slots: [
        { day: 'Monday', from_time: '09:00:00', to_time: '12:00:00' },
        { day: 'Tuesday', from_time: '14:00:00', to_time: '18:00:00' }
      ], absences: [{ name: 'ABS-001', start_date: today, end_date: today, start_time: '11:00:00', end_time: '12:00:00' }]
    }] }) })
  })
  await page.goto('./#Disponibilit%C3%A0')
  await expect(page.getByText('Martedì')).toBeVisible()
  await page.screenshot({ path: info.outputPath('agenda-disponibilita.png'), fullPage: true })
  await page.getByRole('button', { name: 'Modifica orario' }).click()
  const dialog = page.getByRole('dialog')
  await expect(dialog.getByLabel('Dalle (fascia 1)')).toHaveValue('09:00')
  await dialog.getByLabel('Dalle (fascia 1)').fill('10:00')
  await dialog.getByLabel(/^Alle/).fill('13:00')
  await dialog.getByLabel('Motivo').fill('Orario di prova')
  await expect(dialog.getByRole('button', { name: 'Conferma' })).toBeDisabled()
  await dialog.getByRole('checkbox', { name: /Ho verificato le fasce precedenti/ }).check()
  await dialog.getByRole('button', { name: 'Conferma' }).click()
  await expect.poll(() => writes.find(write => write.method.endsWith('availability.set_schedule'))).toBeTruthy()
  expect(writes.find(write => write.method.endsWith('availability.set_schedule'))?.body.time_slots).toEqual([
    { day: 'Monday', from_time: '10:00', to_time: '13:00' },
    { day: 'Tuesday', from_time: '14:00', to_time: '18:00' }
  ])
  expect(writes.find(write => write.method.endsWith('availability.set_schedule'))?.body.expected_modified).toBe('2026-10-22 10:00:00')
  await page.getByRole('button', { name: 'Annulla assenza' }).click()
  await dialog.getByLabel('Motivo').fill('Annullamento di prova')
  await dialog.getByRole('button', { name: 'Conferma' }).click()
  await expect.poll(() => writes.find(write => write.method.endsWith('availability.cancel_absence'))).toBeTruthy()
  expect(writes.find(write => write.method.endsWith('availability.cancel_absence'))?.body).toEqual({ availability: 'ABS-001', reason: 'Annullamento di prova' })
})

test('AUDIT-03 non offre spostamento della seduta storica rinviato da DECISION-059', async ({ page }) => {
  const yesterday = new Date(Date.parse(`${today}T12:00:00Z`) - 86_400_000).toISOString().slice(0, 10)
  await mockApi(page, [], true, { appointment_date: yesterday, cc_closure_state: 'Reopened' })
  await page.goto('./#Agenda')
  if (new Date(`${today}T12:00:00Z`).getUTCDay() === 1) await page.getByRole('button', { name: 'Periodo precedente' }).click()
  await page.locator('.week-event').first().click()
  await expect(page.getByRole('dialog').getByRole('button', { name: 'Sposta' })).toHaveCount(0)
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

test('AUDIT-05: ricerca server trova un professionista oltre il bootstrap e mostra stato e pagina vuota', async ({ page }, info) => {
  await mockApi(page, [], true, {}, { practitioners: [boot.practitioners[0]] })
  const searches: string[] = []
  await page.route('**/api/method/centrochange_core.operations.profiles.practitioners*', async route => {
    const query = new URL(route.request().url()).searchParams.get('search') ?? ''
    searches.push(query)
    await route.fulfill({ contentType: 'application/json', body: JSON.stringify({ message: {
      rows: query.toLowerCase().includes('bianchi') ? [{ name: 'PR-101', practitioner_name: 'Dott. Bianchi', first_name: 'Luca', last_name: 'Bianchi', status: 'Inactive' }] : [],
      has_more: false,
    } }) })
  })
  await page.route('**/api/method/centrochange_core.operations.profiles.practitioner_detail*', route => route.fulfill({ contentType: 'application/json', body: JSON.stringify({ message: {
    name: 'PR-101', practitioner_name: 'Dott. Bianchi', first_name: 'Luca', last_name: 'Bianchi', status: 'Inactive'
  } }) }))
  await page.goto('./#Professionisti')
  await page.getByRole('searchbox', { name: 'Cerca professionisti' }).fill('Bianchi')
  await expect(page.locator('tbody tr')).toHaveCount(1)
  await expect(page.locator('tbody tr')).toContainText('Dott. Bianchi')
  await expect(page.locator('tbody tr')).toContainText('Non attivo')
  await page.screenshot({ path: `../../docs/evidence/issue-171/professionisti-list-${info.project.name}.png` })
  await page.locator('tbody tr').click()
  const drawer = page.getByRole('dialog')
  await expect(drawer).toContainText('Dott. Bianchi')
  await expect(drawer).toContainText('Luca')
  await expect(drawer).toContainText('Non attivo')
  await page.screenshot({ path: `../../docs/evidence/issue-171/professionisti-${info.project.name}.png` })
  await page.getByRole('dialog').getByRole('button', { name: 'Chiudi' }).click()
  await page.getByRole('searchbox', { name: 'Cerca professionisti' }).fill('NessunNome')
  await expect(page.getByText('Nessun risultato per questa ricerca.')).toBeVisible()
  expect(searches).toContain('Bianchi')
})

test('AUDIT-05: pagina vecchia non mescola risultati dopo cambio ricerca', async ({ page }) => {
  await mockApi(page, [], true, {}, { practitioners: [boot.practitioners[0]] })
  let releasePage: (() => void) | undefined
  let oldPageCompleted = false
  await page.route('**/api/method/centrochange_core.operations.profiles.practitioners*', async route => {
    const params = new URL(route.request().url()).searchParams
    const search = params.get('search') ?? ''
    const offset = Number(params.get('offset') ?? 0)
    if (offset) await new Promise<void>(resolve => { releasePage = resolve })
    const rows = search === 'Bianchi' ? [{ name: 'PR-B', practitioner_name: 'Dott. Bianchi', status: 'Active' }]
      : offset ? [{ name: 'PR-A2', practitioner_name: 'Dott. Arancio', status: 'Active' }]
      : [{ name: 'PR-A1', practitioner_name: 'Dott. Alberti', status: 'Active' }]
    await route.fulfill({ contentType: 'application/json', body: JSON.stringify({ message: { rows, has_more: !search && !offset } }) })
    if (offset) oldPageCompleted = true
  })
  await page.goto('./#Professionisti')
  await expect(page.getByRole('button', { name: 'Carica altri' })).toBeVisible()
  await page.getByRole('button', { name: 'Carica altri' }).click()
  await expect.poll(() => Boolean(releasePage)).toBe(true)
  await page.getByRole('searchbox', { name: 'Cerca professionisti' }).fill('Bianchi')
  await expect(page.locator('tbody tr')).toContainText('Dott. Bianchi')
  releasePage?.()
  await expect.poll(() => oldPageCompleted).toBe(true)
  await expect(page.locator('tbody tr')).toHaveCount(1)
  await expect(page.locator('tbody tr')).not.toContainText('Dott. Arancio')
})

test('AUDIT-05: scheda sintetica non espone il codice tecnico come nome', async ({ page }) => {
  await mockApi(page, [], true)
  const row = { name: 'PR-SYNTH', practitioner_name: 'CC-HTTP-AbCd123456 a', first_name: 'CC-HTTP-AbCd123456 a', last_name: '', status: 'Active' }
  await page.route('**/api/method/centrochange_core.operations.profiles.practitioners*', route =>
    route.fulfill({ contentType: 'application/json', body: JSON.stringify({ message: { rows: [row], has_more: false } }) }))
  await page.route('**/api/method/centrochange_core.operations.profiles.practitioner_detail*', route =>
    route.fulfill({ contentType: 'application/json', body: JSON.stringify({ message: row }) }))
  await page.goto('./#Professionisti')
  await expect(page.locator('tbody tr')).toContainText('Professionista di prova A')
  await page.locator('tbody tr').click()
  const drawer = page.getByRole('dialog')
  await expect(drawer.getByRole('heading', { name: 'Scheda professionista' })).toBeVisible()
  await expect(drawer).toContainText('Professionista di prova A')
  await expect(drawer).not.toContainText('CC-HTTP-AbCd123456 a')
})

test('AUDIT-05: selettore Report professionisti usa la stessa identità leggibile', async ({ page }) => {
  const row = { name: 'PR-SYNTH', practitioner_name: 'CC-HTTP-AbCd123456 a', first_name: 'CC-HTTP-AbCd123456 a', status: 'Active' }
  await mockApi(page, [], true, {}, { practitioners: [row] })
  await page.goto('./#Report')
  await page.getByRole('button', { name: 'Report professionisti' }).click()
  const select = page.getByRole('combobox', { name: 'Professionista report' })
  await expect(select).toContainText('Professionista di prova A')
  await expect(select).not.toContainText('CC-HTTP-AbCd123456 a')
})

test('UAT Report professionisti: sedute disponibili, economia limitata al ruolo', async ({ page }, testInfo) => {
  await mockApi(page, [], false, { cc_performed: 1 }, { roles: ['CC Secretariat'] })
  await page.goto('./')
  await openSection(page, 'Report')
  await page.getByRole('button', { name: 'Report professionisti' }).click()
  await page.getByLabel('Professionista report').selectOption('PR-001')
  await expect(page.locator('.professional-report').getByText('Sedute svolte')).toBeVisible()
  await expect(page.getByRole('button', { name: 'Compensi e fatture autorizzati' })).toHaveCount(0)
  await page.screenshot({ path: `../../docs/evidence/issue-148/uat-report-professionisti-${testInfo.project.name}.png`, fullPage: true })
})

test('UAT Patient: nome reale prevale su alias demo, ID API invariati', async ({ page }, testInfo) => {
  const writes: { method: string; body: Record<string, unknown>; headers: Record<string, string> }[] = []
  const demo_labels = { 'PAT-001': 'Paziente Sintetico', 'Paziente Sintetico': 'Paziente Sintetico', 'PR-001': 'Professionista 1', 'Dott.ssa Rossi': 'Professionista 1', 'SERV-001': 'Servizio 1', 'Prima visita': 'Servizio 1', 'CENTRO-A': 'Centro A' }
  await mockApi(page, writes, true, {}, { demo_labels } as Partial<typeof boot>, null, { demo_labels: { 'PAT-001': 'Cliente 1', 'Paziente Sintetico': 'Cliente 1' } } as Partial<typeof financeBoot>)
  await page.goto('./')
  await expect(page.locator('.week-event').first()).toContainText('Paziente Sintetico')
  await expect(page.locator('.week-professional')).toContainText('Professionista 1')
  await openSection(page, 'Pazienti')
  await page.getByRole('textbox', { name: 'Cerca pazienti' }).last().fill('Paziente Sintetico')
  await expect(page.locator('tbody tr')).toHaveCount(1)
  await expect(page.locator('tbody')).toContainText('Paziente Sintetico')
  await page.reload()
  await expect(page.locator('tbody')).toContainText('Paziente Sintetico')
  await openSection(page, 'Professionisti')
  await expect(page.locator('tbody')).toContainText('Professionista 1')
  await openSection(page, 'Servizi')
  await expect(page.locator('tbody')).toContainText('Servizio 1')
  await openSection(page, 'Agenda')
  await page.getByRole('button', { name: 'Nuova prenotazione', exact: true }).click()
  await page.getByRole('dialog').getByRole('combobox', { name: 'Paziente' }).click()
  await expect(page.getByRole('dialog').getByRole('option', { name: 'Paziente Sintetico' })).toHaveCount(1)
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
  await expect(drawer.getByText('Paziente Sintetico')).toBeVisible()
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

test('AUDIT-05: account professionista apre notifiche personali native senza coda manager', async ({ page }) => {
  await mockApi(page, [], false, {}, { roles: ['CC Professional'] })
  const requested: string[] = []
  page.on('request', request => {
    if (request.url().includes('/api/method/frappe.client.get_list'))
      requested.push(new URL(request.url()).searchParams.get('doctype') ?? '')
  })
  await page.goto('./')
  await openSection(page, 'Notifiche')
  await expect(page.getByRole('heading', { name: 'Notifiche', exact: true })).toBeVisible()
  await expect(page.getByText('Nessuna notifica recente')).toBeVisible()
  expect(requested).toContain('Notification Log')
  expect(requested).not.toContain('CC Notification')
  await expect(page.getByRole('button', { name: 'Gestione accessi' })).toHaveCount(0)
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
  const select = dialog.getByRole('combobox', { name: 'Paziente' })
  await select.fill('Zeta')
  await expect(dialog.getByRole('option', { name: 'Zeta Sintetica' })).toBeVisible()
  await dialog.getByRole('option', { name: 'Zeta Sintetica' }).click()
  await dialog.getByRole('textbox', { name: 'Motivo' }).fill('Ricerca sintetica')
  await dialog.getByRole('button', { name: 'Conferma prenotazione' }).click()
  await expect.poll(() => writes.find(w => w.method.endsWith('scheduling.booking.book'))?.body.patient).toBe('PAT-ZETA')
})

test('AUDIT-04 UX-04-09: combobox unico supporta tastiera, filtro, clear e validazione', async ({ page }) => {
  const writes: { method: string; body: Record<string, unknown>; headers: Record<string, string> }[] = []
  await mockApi(page, writes, true, {}, { patients: [...boot.patients, { name: 'PAT-002', patient_name: 'Secondo Paziente' }] })
  await page.goto('./#Agenda')
  await page.getByRole('button', { name: 'Nuova prenotazione' }).click()
  const dialog = page.getByRole('dialog', { name: 'Nuova prenotazione' })
  const patient = dialog.getByRole('combobox', { name: 'Paziente' })
  await expect(dialog.locator('.searchable-select').first().locator('select')).toHaveCount(0)
  await patient.fill('Secondo')
  await expect(dialog.getByRole('option', { name: 'Secondo Paziente' })).toBeVisible()
  await patient.press('ArrowDown')
  await patient.press('Enter')
  await expect(patient).toHaveValue('Secondo Paziente')
  await dialog.getByRole('button', { name: 'Cancella paziente' }).click()
  await expect(patient).toHaveValue('')
  await patient.fill('Sconosciuto')
  await expect(dialog.getByText('Nessun risultato. Modifica la ricerca.')).toBeVisible()
  await patient.press('Escape')
  await expect(patient).toHaveValue('')
  await chooseCombo(dialog, 'Paziente', 'PAT-002')
  await dialog.getByRole('textbox', { name: 'Motivo' }).fill('Prenotazione sintetica')
  await dialog.getByRole('button', { name: 'Conferma prenotazione' }).click()
  await expect.poll(() => writes.find(write => write.method.endsWith('scheduling.booking.book'))?.body.patient).toBe('PAT-002')
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
  await chooseCombo(dialog, 'Professionista', 'PR-001')
  await chooseCombo(dialog, 'Servizio', 'ITEM-001')
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
  await chooseCombo(dialog, 'Fonte seduta', 'SOURCE-001')
  await chooseCombo(dialog, 'Regola esplicita', 'RULE-001')
  await dialog.getByRole('textbox', { name: 'Motivo' }).fill('Cattura sintetica')
  await dialog.getByRole('button', { name: 'Conferma' }).click()
  await expect.poll(() => writes.find(w => w.method.endsWith('professional_economics.capture'))).toBeTruthy()
  expect(writes.find(w => w.method.endsWith('professional_economics.capture'))!.body).toMatchObject({ source: 'SOURCE-001', rule: 'RULE-001' })
  await expect(dialog).toHaveCount(0)

  await page.getByRole('button', { name: 'Operazioni compensi' }).click()
  dialog = page.getByRole('dialog', { name: 'Economia professionisti' })
  await dialog.getByRole('combobox', { name: 'Operazione' }).selectOption('compare')
  await chooseCombo(dialog, 'Fattura fornitore contabilizzata', 'INV-001')
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
  await chooseCombo(drawer, 'Professionista', 'PR-001')
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
  await chooseCombo(drawer, 'Modello', 'TEMPLATE-001')
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
  await chooseCombo(drawer, /Voce 1/, 'ITEM-001')
  await chooseCombo(drawer, 'Conto costo', 'EXP-001')
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

test('AUDIT-04 ricerca locale trova il paziente nel centro e apre la scheda', async ({ page }, testInfo) => {
  await mockApi(page)
  const requests: string[] = []
  page.on('request', request => {
    if (request.url().includes('operations.workspace.patient_search')) requests.push(request.url())
  })
  await page.goto('./#Pazienti')
  await page.getByRole('textbox', { name: 'Cerca pazienti' }).fill('Paziente')
  await expect(page.locator('tbody')).toContainText('Paziente Sintetico')
  await page.screenshot({ path: `test-results/audit-02-search-${testInfo.project.name}.png`, fullPage: true })
  expect(requests.some(url => new URL(url).searchParams.get('center') === 'CENTRO-A')).toBeTruthy()
  await page.locator('tbody tr').first().click()
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
  await expect(page.getByRole('button', { name: 'Apri ricerca pazienti' })).toHaveCount(0)
  await openSection(page, 'Pazienti')
  await page.getByRole('textbox', { name: 'Cerca pazienti' }).fill('Paziente')
  await expect(page.locator('tbody')).toContainText('Paziente Sintetico')
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

test('AUDIT-04 cambio centro scarta risultati tardivi della ricerca locale', async ({ page }, testInfo) => {
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
  await page.goto('./#Pazienti')
  await page.getByRole('textbox', { name: 'Cerca pazienti' }).fill('Paziente')
  await expect.poll(() => started).toBe(true)
  await page.getByRole('combobox', { name: 'Centro' }).selectOption('CENTRO-B')
  await expect(page.getByRole('textbox', { name: 'Cerca pazienti' })).toHaveValue('')
  await page.waitForTimeout(700)
  await expect(page.getByText('Nessun paziente trovato nel centro.')).toBeVisible()
})

test('AUDIT-04 ricerca locale mostra errore ed esito vuoto senza dati di altri centri', async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== 'desktop')
  await mockApi(page)
  await page.route('**/api/method/centrochange_core.operations.workspace.patient_search*', async route => {
    const query = new URL(route.request().url()).searchParams.get('query')
    await route.fulfill(query === 'errore'
      ? { status: 503, contentType: 'application/json', body: JSON.stringify({ exc: 'Unavailable' }) }
      : { contentType: 'application/json', body: JSON.stringify({ message: { patients: [], truncated: false } }) })
  })
  await page.goto('./#Pazienti')
  const search = page.getByRole('textbox', { name: 'Cerca pazienti' })
  await search.fill('errore')
  await expect(page.getByRole('alert').filter({ hasText: 'Operazione non riuscita' })).toBeVisible()
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
  await expect(page.getByRole('button', { name: 'Apri ricerca pazienti' })).toHaveCount(0)
})

test('AUDIT-04 ricerca locale segnala risultati troncati', async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== 'desktop')
  await mockApi(page)
  await page.route('**/api/method/centrochange_core.operations.workspace.patient_search*', route =>
    route.fulfill({ contentType: 'application/json', body: JSON.stringify({ message: { patients: boot.patients, truncated: true } }) }))
  await page.goto('./#Pazienti')
  await page.getByRole('textbox', { name: 'Cerca pazienti' }).fill('Paziente')
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
  await chooseCombo(dialog, 'Seduta da fatturare', 'APP-001')
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
  await expect(dialog.getByRole('button', { name: 'Conferma modifica' })).toBeDisabled()
  await dialog.getByRole('combobox', { name: 'Nuovo stato' }).selectOption('0')
  await dialog.getByRole('textbox', { name: 'Motivo della modifica' }).fill('Revisione sintetica')
  await dialog.getByRole('button', { name: 'Conferma modifica' }).click()
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

test('AUDIT-05 MUST-FIX 1: Agenda con filtro professionisti multiplo e ricercabile', async ({ page }) => {
  const practitioners = [
    { name: 'PR-001', practitioner_name: 'Dott.ssa Rossi' },
    { name: 'PR-002', practitioner_name: 'Dott. Bianchi' },
    { name: 'PR-003', practitioner_name: 'Dott. Verdi' }
  ]
  await mockApi(page, [], true, {}, { practitioners })
  await page.goto('./#Agenda')
  await expect(page.getByRole('heading', { name: 'Agenda', exact: true })).toBeVisible()

  const trigger = page.getByRole('button', { name: 'Filtro professionisti' })
  await expect(trigger).toBeVisible()
  await expect(trigger).toContainText('Tutti i professionisti (3)')

  await trigger.click()
  const popover = page.locator('.practitioner-multi-popover')
  await expect(popover).toBeVisible()

  const searchInput = popover.getByRole('textbox', { name: 'Cerca professionista' })
  await searchInput.fill('Bianchi')
  await expect(popover.getByRole('checkbox', { name: 'Dott. Bianchi' })).toBeVisible()
  await expect(popover.getByRole('checkbox', { name: 'Dott. Verdi' })).toHaveCount(0)

  await searchInput.clear()
  await popover.locator('.multi-popover-item', { hasText: 'Dott.ssa Rossi' }).click()
  await expect(popover.locator('.multi-popover-chips')).toContainText('Dott.ssa Rossi')

  await popover.getByRole('button', { name: 'Tutti' }).click({ force: true })
  await expect(popover.locator('.multi-popover-chips')).toHaveCount(0)
})

test('AUDIT-05 MUST-FIX 1b: Account Professionista non vede filtro Tutti i professionisti', async ({ page }) => {
  const practitioner = { name: 'PR-001', practitioner_name: 'Dott.ssa Rossi' }
  await mockApi(page, [], false, {}, { roles: ['CC Professional'], practitioners: [practitioner] })
  await page.goto('./#Agenda')
  await expect(page.getByRole('heading', { name: 'Agenda', exact: true })).toBeVisible()

  await expect(page.getByRole('button', { name: 'Filtro professionisti' })).toHaveCount(0)
  await expect(page.locator('.agenda-practitioner-label')).toContainText('Dott.ssa Rossi')
})

test('AUDIT-05 MUST-FIX 2: Report fail-closed senza fallback silenzioso a workspace.agenda', async ({ page }) => {
  let agendaCalled = false
  await mockApi(page)
  await page.route('**/api/method/centrochange_core.operations.workspace.agenda*', route => {
    agendaCalled = true
    return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ message: { appointments: [{ name: 'LEAK-APP' }], truncated: false } }) })
  })
  await page.route('**/api/method/centrochange_core.operations.reporting.sessions*', route => {
    return route.fulfill({ status: 500, contentType: 'application/json', body: JSON.stringify({ exc: 'InternalServerError' }) })
  })

  await page.goto('./#Report')
  await expect(page.getByRole('heading', { name: 'Report', exact: true })).toBeVisible()

  await expect(page.locator('.inline-error').last()).toContainText("Operazione non riuscita")
  expect(agendaCalled).toBe(false)
  await expect(page.locator('.report-drilldown .button.secondary')).toHaveClass(/disabled/)
})

test('AUDIT-05 MUST-FIX 3 & 4: Report paginazione server-side e query isolata Professionisti', async ({ page }) => {
  const sessionCalls: string[] = []
  await mockApi(page)
  await page.route('**/api/method/centrochange_core.operations.reporting.sessions*', route => {
    const url = new URL(route.request().url())
    sessionCalls.push(url.search)
    const pageNum = Number(url.searchParams.get('page') || '1')
    return route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        message: {
          appointments: [
            {
              name: `APP-PAGE-${pageNum}`,
              appointment_date: today,
              appointment_time: '10:00:00',
              patient_name: `Paziente Pagina ${pageNum}`,
              practitioner_name: 'Dott.ssa Rossi',
              cc_service_label: 'Visita',
              status: 'Closed',
              cc_performed: 1,
              cc_paid: 1,
              cc_economic_state: 'Paid',
              mode_of_payment: 'POS',
              cc_price_snapshot: 80,
              cc_currency_snapshot: 'EUR'
            }
          ],
          total: 120,
          total_pages: 3,
          page: pageNum,
          page_length: 50,
          truncated: false
        }
      })
    })
  })

  await page.goto('./#Report')
  await expect(page.getByRole('heading', { name: 'Report', exact: true })).toBeVisible()

  const paginationBar = page.locator('.pagination-bar')
  await expect(paginationBar).toBeVisible()
  await expect(paginationBar).toContainText('Pagina 1 di 3 (120 sedute totali)')

  await paginationBar.getByRole('button', { name: 'Successiva' }).click()
  await expect(paginationBar).toContainText('Pagina 2 di 3 (120 sedute totali)')
  expect(sessionCalls.some(call => call.includes('page=2'))).toBe(true)

  await page.getByRole('button', { name: 'Report professionisti' }).click()
  await page.getByRole('combobox', { name: 'Professionista report' }).selectOption('PR-001')

  await expect.poll(() => sessionCalls.some(call => call.includes('practitioner=PR-001') && call.includes('kpi=all'))).toBe(true)
  await expect(page.locator('.professional-report')).toBeVisible()
})

test('AUDIT-05 MUST-FIX 5: Seduta futura non viene marcata come Non pagata', async ({ page }) => {
  await mockApi(page)
  await page.route('**/api/method/centrochange_core.operations.reporting.sessions*', route => {
    return route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        message: {
          appointments: [
            {
              name: 'APP-FUTURE',
              appointment_date: '2099-01-01',
              appointment_time: '15:00:00',
              patient_name: 'Paziente Futuro',
              practitioner_name: 'Dott.ssa Rossi',
              cc_service_label: 'Visita futura',
              status: 'Open',
              cc_performed: 0,
              cc_paid: 0,
              cc_economic_state: 'Due',
              cc_classified_future: true,
              cc_classified_to_close: false,
              cc_classified_unpaid: false,
              mode_of_payment: null,
              cc_price_snapshot: 80,
              cc_currency_snapshot: 'EUR'
            }
          ],
          total: 1,
          total_pages: 1,
          page: 1,
          page_length: 50,
          truncated: false
        }
      })
    })
  })

  await page.goto('./#Report')
  await expect(page.getByRole('heading', { name: 'Report', exact: true })).toBeVisible()

  const row = page.locator('.report-drilldown tbody tr').first()
  await expect(row).toContainText('In programma')
  await expect(row).not.toContainText('Non pagata')
})

test('AUDIT-05 UAT: Riconciliazione matematica KPI=6 <-> Header (6) <-> 6 righe <-> Esclusione cancellate', async ({ page }) => {
  await mockApi(page)
  // Summary with 8 sessions: 6 performed unpaid, 2 cancelled
  await page.route('**/api/method/centrochange_core.operations.reporting.summary*', route => {
    return route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        message: {
          currencies: {
            EUR: {
              sessions: 8,
              performed: 6,
              future: 0,
              to_close: 0,
              operational_paid: 0,
              operational_unpaid: 6,
              cancelled: 2,
              due: 6,
              due_snapshot_amount: 600
            }
          },
          total_appointments: 8,
          truncated: false
        }
      })
    })
  })

  let requestedKpi = ''
  await page.route('**/api/method/centrochange_core.operations.reporting.sessions*', route => {
    const url = new URL(route.request().url())
    requestedKpi = url.searchParams.get('kpi') || ''
    if (requestedKpi === 'operational_unpaid') {
      const unpaidRows = Array.from({ length: 6 }, (_, i) => ({
        name: `APP-UNPAID-${i + 1}`,
        appointment_date: '2026-09-10',
        appointment_time: '10:00:00',
        patient_name: `Paziente ${i + 1}`,
        practitioner_name: 'Dott. A',
        cc_service_label: 'Seduta psicologica',
        status: 'Closed',
        cc_performed: 1,
        cc_paid: 0,
        cc_economic_state: 'Due',
        cc_classified_future: false,
        cc_classified_to_close: false,
        cc_classified_unpaid: true,
        cc_classified_cancelled: false,
        mode_of_payment: null,
        cc_price_snapshot: 100,
        cc_currency_snapshot: 'EUR'
      }))
      return route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          message: {
            appointments: unpaidRows,
            total: 6,
            total_pages: 1,
            page: 1,
            page_length: 50,
            truncated: false
          }
        })
      })
    }
    return route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        message: {
          appointments: [],
          total: 0,
          total_pages: 1,
          page: 1,
          page_length: 50,
          truncated: false
        }
      })
    })
  })

  await page.goto('./#Report')
  await expect(page.getByRole('heading', { name: 'Report', exact: true })).toBeVisible()

  // Verify grouping titles
  await expect(page.getByText('Sedute e appuntamenti (EUR)')).toBeVisible()
  await expect(page.getByText('Stato pagamenti operativi')).toBeVisible()
  await expect(page.getByText(/Valore tariffe previste: importo teorico/)).toBeVisible()

  // Click on "Svolte senza pagamento" (value 6)
  const unpaidCard = page.locator('.metric-card').filter({ hasText: 'Svolte senza pagamento' })
  await expect(unpaidCard).toContainText('6')
  await unpaidCard.click()

  // Drilldown header must show exact count 6 and Italian label
  const header = page.locator('.report-drilldown-header h3')
  await expect(header).toHaveText('Dettaglio sedute — Svolte senza pagamento (6)')

  // Table must contain exactly 6 rows, all with 'Da incassare' and none with 'annullata'
  const rows = page.locator('.report-drilldown tbody tr')
  await expect(rows).toHaveCount(6)
  await expect(rows.first()).toContainText('Da incassare')
  await expect(rows.first()).not.toContainText('annullata')
  await expect(rows.first()).not.toContainText('Non pagata')
})

test('AUDIT-05 UAT: Visualizzazione neutra per seduta annullata e registrato per pagata', async ({ page }) => {
  await mockApi(page)
  await page.route('**/api/method/centrochange_core.operations.reporting.sessions*', route => {
    return route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        message: {
          appointments: [
            {
              name: 'APP-CANC',
              appointment_date: '2026-09-15',
              appointment_time: '11:00:00',
              patient_name: 'Paziente Annullato',
              practitioner_name: 'Dott. A',
              cc_service_label: 'Seduta',
              status: 'Cancelled',
              cc_performed: 0,
              cc_paid: 0,
              cc_economic_state: 'Non Due',
              cc_classified_future: false,
              cc_classified_to_close: false,
              cc_classified_unpaid: false,
              cc_classified_cancelled: true,
              mode_of_payment: null,
              cc_price_snapshot: 100,
              cc_currency_snapshot: 'EUR'
            },
            {
              name: 'APP-PAID',
              appointment_date: '2026-09-16',
              appointment_time: '12:00:00',
              patient_name: 'Paziente Pagato',
              practitioner_name: 'Dott. A',
              cc_service_label: 'Seduta',
              status: 'Closed',
              cc_performed: 1,
              cc_paid: 1,
              cc_economic_state: 'Due',
              cc_classified_future: false,
              cc_classified_to_close: false,
              cc_classified_unpaid: false,
              cc_classified_cancelled: false,
              mode_of_payment: 'POS',
              cc_price_snapshot: 100,
              cc_currency_snapshot: 'EUR'
            }
          ],
          total: 2,
          total_pages: 1,
          page: 1,
          page_length: 50,
          truncated: false
        }
      })
    })
  })

  await page.goto('./#Report')
  const rows = page.locator('.report-drilldown tbody tr')
  await expect(rows).toHaveCount(2)

  // Cancelled session row
  const cancRow = rows.first()
  await expect(cancRow).toContainText('Annullata')
  await expect(cancRow).toContainText('— (annullata)')
  await expect(cancRow).not.toContainText('Non pagata')

  // Paid session row
  const paidRow = rows.nth(1)
  await expect(paidRow).toContainText('Svolta')
  await expect(paidRow).toContainText('Registrato')
})

test('AUDIT-05 UAT: Metriche ribbon Agenda coerenti con filtro professionisti e stati temporali', async ({ page }) => {
  const p1 = { name: 'PR-001', practitioner_name: 'Dott.ssa Rossi' }
  const p2 = { name: 'PR-002', practitioner_name: 'Dott. Bianchi' }
  const today = '2026-10-24'
  const appointments = [
    // 2 appointments for PR-001: 1 performed, 1 cancelled
    { name: 'APP-1', practitioner: 'PR-001', appointment_date: today, appointment_time: '09:00:00', duration: 60, cc_performed: 1, status: 'Closed' },
    { name: 'APP-2', practitioner: 'PR-001', appointment_date: today, appointment_time: '10:00:00', duration: 60, cc_performed: 0, status: 'Cancelled' },
    // 2 appointments for PR-002: 1 future (scheduled tomorrow), 1 past to_close (08:00 today)
    { name: 'APP-3', practitioner: 'PR-002', appointment_date: '2026-10-25', appointment_time: '15:00:00', duration: 60, cc_performed: 0, status: 'Scheduled' },
    { name: 'APP-4', practitioner: 'PR-002', appointment_date: today, appointment_time: '08:00:00', duration: 60, cc_performed: 0, status: 'Scheduled' },
  ]
  await mockApi(page, [], false, {}, { practitioners: [p1, p2] })
  await page.route('**/api/method/centrochange_core.operations.workspace.agenda*', route => {
    return route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ message: { appointments, truncated: false } })
    })
  })

  await page.goto('./#Agenda')
  await expect(page.getByRole('heading', { name: 'Agenda', exact: true })).toBeVisible()

  // Initially "Tutti i professionisti" is active (both P1 and P2):
  // Total displayed = 4
  // Svolte = 1 (APP-1)
  // Sedute da chiudere = 1 (APP-4 only! APP-2 is cancelled, APP-3 is future tomorrow!)
  // Professionisti = 2
  const metricsRibbon = page.locator('.metrics-grid').first()
  await expect(metricsRibbon.locator('.metric-card').filter({ hasText: 'Sedute nel periodo' })).toContainText('4')
  await expect(metricsRibbon.locator('.metric-card').filter({ hasText: 'Sedute svolte' })).toContainText('1')
  await expect(metricsRibbon.locator('.metric-card').filter({ hasText: 'Sedute da chiudere' })).toContainText('1')
  await expect(metricsRibbon.locator('.metric-card').filter({ hasText: 'Professionisti' })).toContainText('2')

  // Now select only Dott.ssa Rossi (PR-001)
  await page.getByRole('button', { name: 'Filtro professionisti' }).click()
  await page.locator('.multi-popover-item', { hasText: 'Dott.ssa Rossi' }).locator('input[type="checkbox"]').click()
  await page.keyboard.press('Escape')

  // Ribbon should now update to PR-001 ONLY:
  // Total displayed = 2 (APP-1 and APP-2)
  // Svolte = 1
  // Sedute da chiudere = 0 (APP-1 is performed, APP-2 is cancelled)
  // Professionisti = 1
  await expect(metricsRibbon.locator('.metric-card').filter({ hasText: 'Sedute nel periodo' })).toContainText('2')
  await expect(metricsRibbon.locator('.metric-card').filter({ hasText: 'Sedute svolte' })).toContainText('1')
  await expect(metricsRibbon.locator('.metric-card').filter({ hasText: 'Sedute da chiudere' })).toContainText('0')
  await expect(metricsRibbon.locator('.metric-card').filter({ hasText: 'Professionisti' })).toContainText('1')
})

test('AUDIT-05 UAT: Cancellazione tardiva dovuta riconciliata in KPI, drilldown ed export', async ({ page }) => {
  await mockApi(page)
  const today = '2026-10-24'
  const summary = {
    currencies: {
      EUR: { sessions: 1, performed: 0, cancelled: 1, future: 0, to_close: 0, operational_paid: 0, operational_unpaid: 0, due: 1, due_snapshot_amount: 80.0 }
    },
    practitioner: null,
    total_appointments: 1,
    truncated: false
  }
  const lateCancelledApp: Appointment = {
    name: 'APP-LATE-1',
    patient: 'PAT-1',
    patient_name: 'Paziente Late',
    practitioner: 'PRO-1',
    practitioner_name: 'Dott.ssa Rossi',
    cc_center: 'CENTRO-A',
    appointment_date: today,
    appointment_time: '10:00:00',
    duration: 60,
    status: 'Cancelled',
    cc_closure_state: 'Closed',
    cc_economic_state: 'Due',
    cc_performed: 0,
    cc_paid: 0,
    cc_service_label: 'Consulenza Specialistica',
    cc_price_snapshot: 80.0,
    cc_currency_snapshot: 'EUR'
  }

  await page.route('**/api/method/centrochange_core.operations.reporting.summary*', route => {
    return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ message: summary }) })
  })
  await page.route('**/api/method/centrochange_core.operations.reporting.sessions*', route => {
    const url = new URL(route.request().url())
    const kpi = url.searchParams.get('kpi')
    if (kpi === 'due' || kpi === 'all') {
      return route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ message: { appointments: [lateCancelledApp], total: 1, total_pages: 1 } })
      })
    }
    return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ message: { appointments: [], total: 0, total_pages: 1 } }) })
  })

  await page.goto('./#Report')
  await expect(page.getByRole('heading', { name: 'Report', exact: true })).toBeVisible()

  // Verify KPI card "Con tariffa prevista" shows 1
  const dueCard = page.locator('.metric-card').filter({ hasText: 'Con tariffa prevista' })
  await expect(dueCard).toContainText('1')
  await dueCard.click()

  // Drilldown header must show 1 session for "Con tariffa prevista"
  await expect(page.locator('.report-drilldown-header h3')).toContainText('Dettaglio sedute — Con tariffa prevista')
  await expect(page.locator('.report-drilldown-header h3')).toContainText('(1)')

  // Table row must display the late cancelled session with neutral badge '— (annullata)' and tariff 80,00 €
  const row = page.locator('.report-drilldown tbody tr').first()
  await expect(row).toBeVisible()
  await expect(row).toContainText('Annullata')
  await expect(row).toContainText('— (annullata)')
  await expect(row).toContainText('80,00 €')
})

test('AUDIT-05 UAT: Report multi-valuta con filtro e drilldown separato per valuta', async ({ page }) => {
  await mockApi(page)
  const today = '2026-10-24'
  const summary = {
    currencies: {
      EUR: { sessions: 2, performed: 1, cancelled: 0, future: 0, to_close: 1, operational_paid: 1, operational_unpaid: 0, due: 1, due_snapshot_amount: 50.0 },
      USD: { sessions: 3, performed: 2, cancelled: 0, future: 0, to_close: 1, operational_paid: 1, operational_unpaid: 1, due: 2, due_snapshot_amount: 140.0 }
    },
    practitioner: null,
    total_appointments: 5,
    truncated: false
  }

  const eurApps: Appointment[] = [
    { name: 'APP-EUR-1', patient: 'PAT-1', patient_name: 'Paziente EUR', practitioner: 'PRO-1', practitioner_name: 'Dott.ssa Rossi', cc_center: 'CENTRO-A', appointment_date: today, appointment_time: '09:00:00', duration: 60, status: 'Closed', cc_performed: 1, cc_paid: 1, cc_price_snapshot: 50.0, cc_currency_snapshot: 'EUR' },
    { name: 'APP-EUR-2', patient: 'PAT-2', patient_name: 'Paziente EUR 2', practitioner: 'PRO-1', practitioner_name: 'Dott.ssa Rossi', cc_center: 'CENTRO-A', appointment_date: today, appointment_time: '10:00:00', duration: 60, status: 'Scheduled', cc_performed: 0, cc_paid: 0, cc_price_snapshot: 50.0, cc_currency_snapshot: 'EUR' }
  ]
  const usdApps: Appointment[] = [
    { name: 'APP-USD-1', patient: 'PAT-3', patient_name: 'Paziente USD 1', practitioner: 'PRO-1', practitioner_name: 'Dott.ssa Rossi', cc_center: 'CENTRO-A', appointment_date: today, appointment_time: '11:00:00', duration: 60, status: 'Closed', cc_performed: 1, cc_paid: 1, cc_price_snapshot: 70.0, cc_currency_snapshot: 'USD' },
    { name: 'APP-USD-2', patient: 'PAT-4', patient_name: 'Paziente USD 2', practitioner: 'PRO-1', practitioner_name: 'Dott.ssa Rossi', cc_center: 'CENTRO-A', appointment_date: today, appointment_time: '12:00:00', duration: 60, status: 'Closed', cc_performed: 1, cc_paid: 0, cc_price_snapshot: 70.0, cc_currency_snapshot: 'USD' },
    { name: 'APP-USD-3', patient: 'PAT-5', patient_name: 'Paziente USD 3', practitioner: 'PRO-1', practitioner_name: 'Dott.ssa Rossi', cc_center: 'CENTRO-A', appointment_date: today, appointment_time: '13:00:00', duration: 60, status: 'Scheduled', cc_performed: 0, cc_paid: 0, cc_price_snapshot: 0.0, cc_currency_snapshot: 'USD' }
  ]

  await page.route('**/api/method/centrochange_core.operations.reporting.summary*', route => {
    return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ message: summary }) })
  })
  await page.route('**/api/method/centrochange_core.operations.reporting.sessions*', route => {
    const url = new URL(route.request().url())
    const curr = url.searchParams.get('currency')
    if (curr === 'USD') {
      return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ message: { appointments: usdApps, total: 3, total_pages: 1 } }) })
    }
    if (curr === 'EUR') {
      return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ message: { appointments: eurApps, total: 2, total_pages: 1 } }) })
    }
    return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ message: { appointments: [...eurApps, ...usdApps], total: 5, total_pages: 1 } }) })
  })

  await page.goto('./#Report')
  await expect(page.getByRole('heading', { name: 'Report', exact: true })).toBeVisible()

  // Two currency sections should be visible
  await expect(page.getByText('Sedute e appuntamenti (EUR)')).toBeVisible()
  await expect(page.getByText('Sedute e appuntamenti (USD)')).toBeVisible()

  // Click on "Sedute totali" in USD section (card value 3)
  const usdSection = page.locator('.report-currency').filter({ hasText: 'Sedute e appuntamenti (USD)' })
  await usdSection.locator('.metric-card').filter({ hasText: 'Sedute totali' }).click()

  // Drilldown header should reflect USD and (3)
  await expect(page.locator('.report-drilldown-header h3')).toContainText('Dettaglio sedute — Tutte le sedute (USD) (3)')

  // Table should show exactly 3 rows
  await expect(page.locator('.report-drilldown tbody tr')).toHaveCount(3)

  // Export link should include currency=USD
  const exportBtn = page.locator('.report-drilldown-header a.button').filter({ hasText: 'Esporta CSV' })
  await expect(exportBtn).toHaveAttribute('href', /currency=USD/)
})




test('AUDIT-05: validazione date italiane, bisestili e canoniche senza timezone', () => {
  expect(parseItalianDate('29/02/2024')).toBe('2024-02-29')
  expect(parseItalianDate('29/02/2025')).toBeNull()
  expect(parseItalianDate('31/04/2026')).toBeNull()
  expect(parseItalianDate('26/10/2026')).toBe('2026-10-26')
  expect(parseItalianDate('2026-10-26')).toBeNull()
})

test('AUDIT-05: filtri report accettano data scritta e calendario e bloccano periodo inverso', async ({ page }) => {
  await mockApi(page)
  await page.goto('./#Report')
  const start = page.getByRole('textbox', { name: 'data iniziale (GG/MM/AAAA)' })
  const end = page.getByRole('textbox', { name: 'data finale (GG/MM/AAAA)' })
  await start.fill('29/02/2025')
  await expect(page.getByText(/Periodo non valido: inserisci due date/)).toBeVisible()
  await expect(page.getByRole('link', { name: 'Esporta CSV del centro' })).toHaveAttribute('aria-disabled', 'true')
  await start.fill('28/09/2026')
  await end.fill('04/10/2026')
  await expect.poll(() => page.locator('.report-drilldown').count()).toBe(1)
  await page.getByRole('button', { name: 'Apri calendario data iniziale' }).click()
  const picker = page.getByRole('dialog', { name: 'Calendario data iniziale' })
  await expect(picker).toBeVisible()
  await picker.getByRole('button', { name: '28/09/2026' }).click()
  await expect(start).toHaveValue('28/09/2026')
  await end.fill('27/09/2026')
  await expect(page.getByText(/Periodo non valido: inserisci due date/)).toBeVisible()
})

test('AUDIT-05: orari multipli non possono essere salvati senza revisione', async ({ page }) => {
  const writes: { method: string; body: Record<string, unknown>; headers: Record<string, string> }[] = []
  await mockApi(page, writes)
  await page.route('**/api/method/centrochange_core.operations.workspace.schedules*', route => route.fulfill({
    contentType: 'application/json', body: JSON.stringify({ message: [{ name: 'SCHED-MULTI', practitioner: 'PR-001', modified: '2026-10-26 10:00:00',
      time_slots: [
        { day: 'Monday', from_time: '09:00:00', to_time: '12:00:00' },
        { day: 'Monday', from_time: '14:00:00', to_time: '17:00:00' },
        { day: 'Tuesday', from_time: '09:00:00', to_time: '18:00:00' }
      ], absences: [] }] })
  }))
  await page.goto('./#Disponibilit%C3%A0')
  await page.getByRole('button', { name: 'Modifica orario' }).click()
  const dialog = page.getByRole('dialog', { name: 'Modifica disponibilità' })
  await expect(dialog.getByLabel('Dalle (fascia 1)')).toHaveValue('09:00')
  await expect(dialog.getByLabel('Dalle (fascia 2)')).toHaveValue('14:00')
  await expect(dialog.locator('input[type="time"]')).toHaveCount(0)
  await dialog.getByLabel('Dalle (fascia 1)').fill('10:00')
  await dialog.getByLabel('Motivo').fill('Rettifica prova')
  await expect(dialog.getByRole('button', { name: 'Conferma' })).toBeDisabled()
  expect(writes.find(write => write.method.endsWith('availability.set_schedule'))).toBeUndefined()
  await dialog.getByRole('checkbox', { name: /Ho verificato le fasce precedenti/ }).check()
  await dialog.getByRole('button', { name: 'Conferma' }).click()
  const sent = await expect.poll(() => writes.find(write => write.method.endsWith('availability.set_schedule'))).toBeTruthy()
  const payload = writes.find(write => write.method.endsWith('availability.set_schedule'))!.body
  expect(payload.time_slots).toEqual([
    { day: 'Monday', from_time: '10:00', to_time: '12:00' },
    { day: 'Monday', from_time: '14:00', to_time: '17:00' },
    { day: 'Tuesday', from_time: '09:00', to_time: '18:00' }
  ])
  expect(payload.expected_modified).toBe('2026-10-26 10:00:00')
})
