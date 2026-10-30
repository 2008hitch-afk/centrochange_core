import React, { useEffect, useRef, useState } from 'react'
import { ArrowRight, Printer, Search } from 'lucide-react'
import { displayDate, money, recentPaymentStart, requestKey, romeToday, type Boot, type FinanceBoot, type Practitioner, type Row } from './api'
import { archiveDetail, createArchive, creatableKinds, documentDetail, documentPreview, editableKinds, financeKinds, listArchive, saveArchive, type ArchiveKind, type ArchiveRecord, type FinanceDocument, type PrintPreview } from './scoped_api'
import { Button, DataTable, DateInput, Drawer, Empty, Field, FormError, Heading, Modal, SearchableSelect } from './ui'
import { financeFieldValue } from './finance_locale'
import { demoPatient, demoText, syntheticCode, syntheticLetter } from './demo_labels'
import { centerNameFor, practitionerName } from './display_names'

type FieldSpec = { key: string; label: string; edit?: boolean; required?: boolean; kind?: 'text' | 'number' | 'email' | 'select'; values?: { value: string; label: string }[] }
type Spec = { kind: ArchiveKind; label: string; group: string; fields: FieldSpec[] }
const status: FieldSpec = { key: 'enabled', label: 'Stato', edit: true, kind: 'select', values: [{ value: '1', label: 'Attivo' }, { value: '0', label: 'Disattivato' }] }
const specs: Spec[] = [
  { kind: 'Patient', label: 'Pazienti', group: 'Anagrafiche', fields: [{ key: 'patient_name', label: 'Paziente' }, { key: 'first_name', label: 'Nome', edit: true, required: true }, { key: 'last_name', label: 'Cognome', edit: true }, { key: 'email', label: 'Email', edit: true, kind: 'email' }] },
  { kind: 'Healthcare Practitioner', label: 'Professionisti', group: 'Anagrafiche', fields: [{ key: 'practitioner_name', label: 'Professionista' }, { key: 'first_name', label: 'Nome', edit: true, required: true }, { key: 'last_name', label: 'Cognome', edit: true }, { key: 'status', label: 'Stato' }] },
  { kind: 'Item', label: 'Articoli', group: 'Catalogo', fields: [{ key: 'item_name', label: 'Articolo', edit: true, required: true }, { key: 'item_group', label: 'Gruppo' }, { key: 'stock_uom', label: 'Unità' }, { key: 'disabled', label: 'Stato' }] },
  { kind: 'Item Price', label: 'Tariffe', group: 'Catalogo', fields: [{ key: 'item_code', label: 'Articolo' }, { key: 'price_list', label: 'Listino' }, { key: 'price_list_rate', label: 'Tariffa', edit: true, required: true, kind: 'number' }, { key: 'currency', label: 'Valuta' }, { key: 'valid_from', label: 'Valida dal' }] },
  { kind: 'Appointment Type', label: 'Tipi seduta', group: 'Catalogo', fields: [{ key: 'appointment_type', label: 'Tipo seduta' }, { key: 'default_duration', label: 'Durata (min)', edit: true, required: true, kind: 'number' }, { key: 'cc_service_item', label: 'Articolo' }] },
  { kind: 'CC Center Service', label: 'Servizi del centro', group: 'Catalogo', fields: [{ key: 'appointment_type', label: 'Tipo seduta' }, { key: 'center', label: 'Centro' }, status] },
  { kind: 'CC Package Template', label: 'Modelli pacchetto', group: 'Catalogo', fields: [{ key: 'title', label: 'Modello', edit: true, required: true }, { key: 'service_item', label: 'Articolo' }, { key: 'units', label: 'Numero di sedute incluse', edit: true, required: true, kind: 'number' }, status] },
  { kind: 'Sales Invoice', label: 'Fatture pazienti', group: 'Finanza', fields: [{ key: 'name', label: 'Fattura' }, { key: 'customer', label: 'Cliente' }, { key: 'posting_date', label: 'Data' }, { key: 'grand_total', label: 'Totale' }, { key: 'outstanding_amount', label: 'Residuo' }, { key: 'docstatus', label: 'Stato documento' }] },
  { kind: 'Purchase Invoice', label: 'Fatture professionisti', group: 'Finanza', fields: [{ key: 'name', label: 'Fattura' }, { key: 'supplier', label: 'Fornitore' }, { key: 'posting_date', label: 'Data' }, { key: 'grand_total', label: 'Totale' }, { key: 'outstanding_amount', label: 'Residuo' }, { key: 'docstatus', label: 'Stato documento' }] },
  { kind: 'Payment Entry', label: 'Pagamenti', group: 'Finanza', fields: [{ key: 'name', label: 'Pagamento' }, { key: 'party', label: 'Soggetto' }, { key: 'posting_date', label: 'Data' }, { key: 'payment_type', label: 'Tipo' }, { key: 'paid_amount', label: 'Importo' }, { key: 'unallocated_amount', label: 'Importo non attribuito' }, { key: 'docstatus', label: 'Stato documento' }] },
  { kind: 'Bank Transaction', label: 'Movimenti bancari', group: 'Finanza', fields: [{ key: 'name', label: 'Movimento' }, { key: 'date', label: 'Data' }, { key: 'reference_number', label: 'Riferimento' }, { key: 'deposit', label: 'Entrata' }, { key: 'withdrawal', label: 'Uscita' }, { key: 'unallocated_amount', label: 'Importo non attribuito' }, { key: 'docstatus', label: 'Stato documento' }] }
]
const view = (field: FieldSpec, value: unknown) => {
  if (value == null || value === '') return '—'
  if (field.key === 'docstatus') {
    const v = Number(value)
    if (v === 0) return 'Bozza'
    if (v === 1) return 'Confermata'
    if (v === 2) return 'Annullata'
    return String(value)
  }
  if (/date|valid_from/.test(field.key)) return displayDate(value)
  if (/amount|total|rate|deposit|withdrawal/.test(field.key)) return money(value)
  if (field.key === 'enabled' || field.key === 'disabled') {
    if (field.key === 'disabled') return Number(value) ? 'Disattivato' : 'Attivo'
    return Number(value) ? 'Attivo' : 'Disattivato'
  }
  if (field.key === 'stock_uom') {
    const s = String(value)
    if (s === 'Nos') return 'Sedute'
    if (s === 'Services') return 'Servizi'
    return s
  }
  if (field.key === 'payment_type') return financeFieldValue(field.key, value)
  return demoText(value)
}

// Only the archive editor reconciles an exact UAT alias with the saved Frappe
// fields. Other surfaces retain their existing presentation contract.
const archivePatientName = (row: Row) => {
  const first = String(row.first_name ?? '').trim(), last = String(row.last_name ?? '').trim()
  if (first && !syntheticCode(first)) return [first, last].filter(Boolean).join(' ')
  if (syntheticCode(first)) return `Paziente di prova ${syntheticLetter(first) ?? ''}`.trim()
  return demoPatient(row.name, row.patient_name, row.first_name, row.last_name)
}
const archivePractitionerName = (row: Practitioner) => {
  const first = String(row.first_name ?? '').trim(), last = String(row.last_name ?? '').trim()
  if (first && !syntheticCode(first)) return [first, last].filter(Boolean).join(' ')
  if (syntheticCode(first)) return `Professionista di prova ${syntheticLetter(first) ?? ''}`.trim()
  return practitionerName(row)
}
const archiveCatalogName = (kind: ArchiveKind, row: Row) => {
  const field = kind === 'Item' ? 'item_name' : kind === 'CC Package Template' ? 'title' : ''
  const value = String(row[field] ?? row.name ?? '')
  if (field && syntheticCode(value)) return `${kind === 'Item' ? 'Articolo' : 'Pacchetto'} di prova ${syntheticLetter(value) ?? ''}`.trim()
  return field ? value : demoText(value)
}

/** Live candidate: reads only approved projections; writes only manager-scoped existing records. */
export function ScopedArchive({ boot, financeBoot, center }: { boot: Boot | null; financeBoot: FinanceBoot | null; center: string }) {
  const manager = !!boot?.roles.includes('CC Manager') || !!financeBoot?.is_manager
  const visible = specs.filter(spec => spec.group === 'Catalogo' ? manager && !!boot : financeKinds.includes(spec.kind) ? !!financeBoot : spec.kind === 'Healthcare Practitioner' ? !!boot && (manager || boot.roles.includes('CC Professional')) : !!boot)
  const [kind, setKind] = useState<ArchiveKind>(boot ? 'Patient' : 'Sales Invoice')
  const [rows, setRows] = useState<ArchiveRecord[]>([])
  const [loadedKey, setLoadedKey] = useState('')
  const [hasMore, setHasMore] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [search, setSearch] = useState('')
  const [debouncedSearch, setDebouncedSearch] = useState('')
  const searchGen = useRef(0)
  const detailGen = useRef(0)
  const [paymentStart, setPaymentStart] = useState(recentPaymentStart)
  const [paymentEnd, setPaymentEnd] = useState(romeToday())
  const [selected, setSelected] = useState<ArchiveRecord | null>(null)
  const [document, setDocument] = useState<FinanceDocument | null>(null)
  const [draft, setDraft] = useState<Row | null>(null)
  const [creating, setCreating] = useState(false)
  const [reason, setReason] = useState('')
  const [confirm, setConfirm] = useState(false)
  const [preview, setPreview] = useState<PrintPreview | null>(null)
  const [availableItems, setAvailableItems] = useState<{ value: string; label: string }[]>([])
  const [availableTypes, setAvailableTypes] = useState<{ value: string; label: string }[]>([])
  const key = useRef(requestKey())
  const frame = useRef<HTMLIFrameElement>(null)
  const spec = visible.find(s => s.kind === kind) ?? visible[0]
  const queryKey = `${center}\u0000${spec.kind}\u0000${debouncedSearch}\u0000${paymentStart}\u0000${paymentEnd}`

  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(search)
    }, 200)
    return () => clearTimeout(timer)
  }, [search])

  useEffect(() => {
    if (!creating || !center) return
    let live = true
    listArchive(center, 'Item', 0).then(result => {
      if (live) setAvailableItems(result.rows.map(r => ({ value: String(r.name), label: `${demoText(r.item_name || r.name)} (${demoText(r.name)})` })))
    }).catch(() => {})
    listArchive(center, 'Appointment Type', 0).then(result => {
      if (live) setAvailableTypes(result.rows.map(r => ({ value: String(r.name), label: `${demoText(r.appointment_type || r.name)} (${demoText(r.name)})` })))
    }).catch(() => {})
    return () => { live = false }
  }, [creating, center])

  async function refresh(activeKind = spec.kind, query = debouncedSearch) {
    const gen = ++searchGen.current
    setLoading(true); setError('')
    try {
      const result = await listArchive(center, activeKind, 0, { start: paymentStart, end: paymentEnd }, query)
      if (gen === searchGen.current) {
        setRows(result.rows)
        setHasMore(result.has_more)
        setLoadedKey(`${center}\u0000${activeKind}\u0000${query}\u0000${paymentStart}\u0000${paymentEnd}`)
      }
    } catch (cause) {
      if (gen === searchGen.current) {
        setRows([])
        setHasMore(false)
        setLoadedKey(`${center}\u0000${activeKind}\u0000${query}\u0000${paymentStart}\u0000${paymentEnd}`)
        setError(cause instanceof Error ? cause.message : 'Caricamento non riuscito.')
      }
    } finally {
      if (gen === searchGen.current) setLoading(false)
    }
  }

  useEffect(() => {
    detailGen.current++
    setSelected(null)
    setDocument(null)
    setPreview(null)
    setDraft(null)
    void refresh(spec.kind, debouncedSearch)
  }, [center, spec.kind, debouncedSearch, paymentStart, paymentEnd])

  const more = async () => {
    const gen = searchGen.current
    setLoading(true); setError('')
    try {
      const result = await listArchive(center, spec.kind, rows.length, { start: paymentStart, end: paymentEnd }, debouncedSearch)
      if (gen === searchGen.current) {
        setRows(old => [...old, ...result.rows])
        setHasMore(result.has_more)
      }
    } catch (cause) {
      if (gen === searchGen.current) setError(cause instanceof Error ? cause.message : 'Caricamento non riuscito.')
    } finally {
      if (gen === searchGen.current) setLoading(false)
    }
  }

  // The server already applies center/role scoped search before pagination.
  // Filtering a loaded page again would hide valid matches by code or alias.
  const pendingQuery = loadedKey !== queryKey || search !== debouncedSearch
  const filtered = pendingQuery ? [] : rows

  const change = (next: ArchiveKind) => {
    setKind(next)
    setNotice('')
    setError('')
    setSearch('')
    setDebouncedSearch('')
  }
  const open = async (row: ArchiveRecord) => {
    const gen = ++detailGen.current
    setLoading(true); setError('')
    try {
      if (kind === 'Sales Invoice' || kind === 'Purchase Invoice' || kind === 'Payment Entry') {
        const result = await documentDetail(center, kind, row.name)
        if (gen !== detailGen.current) return
        setDocument(result)
        setSelected({ ...row, ...result })
      } else { const result = financeKinds.includes(kind) ? row : await archiveDetail(center, kind, row.name); if (gen !== detailGen.current) return; setDocument(null); setSelected(result) }
    }
    catch (cause) { if (gen === detailGen.current) setError(cause instanceof Error ? cause.message : 'Dettaglio non disponibile.') }
    finally { if (gen === detailGen.current) setLoading(false) }
  }
  const edit = () => { if (!selected) return; setCreating(false); const nameField = kind === 'Patient' || kind === 'Healthcare Practitioner' ? 'first_name' : kind === 'Item' ? 'item_name' : kind === 'CC Package Template' ? 'title' : ''; setDraft({ ...selected, ...(nameField && syntheticCode(selected[nameField]) ? { [nameField]: '' } : {}) }); setReason(''); key.current = requestKey(); setConfirm(false); setError('') }
  const beginCreate = () => { setCreating(true); setSelected(null); setDraft({ enabled: 1, valid_from: romeToday() }); setReason(''); key.current = requestKey(); setError('') }
  const update = (field: string, value: string) => { setDraft(old => ({ ...old, [field]: value })); key.current = requestKey() }
  const validate = () => {
    if (!draft) return 'Scheda non disponibile.'
    for (const field of formFields) {
      const value = String(draft[field.key] ?? '').trim()
      if (field.required && !value) return `Compila ${field.label.toLocaleLowerCase('it-IT')}.`
      if (field.kind === 'number' && (!Number.isFinite(Number(value)) || Number(value) < 0)) return `Verifica ${field.label.toLocaleLowerCase('it-IT')}.`
      if (field.kind === 'email' && value && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) return 'Email non valida.'
    }
    if (!reason.trim()) return 'Indica il motivo della modifica.'
    return ''
  }
  const save = async () => {
    const issue = validate(); if (issue) { setError(issue); setConfirm(false); return }
    if (!draft || (!selected && !creating)) return
    setLoading(true); setError(''); setConfirm(false)
    try {
      const result = creating ? await createArchive(center, kind, draft, reason.trim(), key.current) : await saveArchive(center, kind, selected!, draft, reason.trim(), key.current)
      const current = await archiveDetail(center, kind, result.name)
      setSelected(current); setDraft(null); setCreating(false); setNotice('Scheda salvata con successo.'); await refresh(kind, debouncedSearch)
    } catch (cause) { setError(cause instanceof Error ? cause.message : 'Salvataggio non riuscito.') }
    finally { setLoading(false) }
  }
  const print = async () => {
    if (!selected || !['Sales Invoice', 'Purchase Invoice', 'Payment Entry'].includes(kind)) return
    const gen = detailGen.current
    setLoading(true); setError('')
    try { const result = await documentPreview(center, kind as 'Sales Invoice' | 'Purchase Invoice' | 'Payment Entry', selected.name); if (gen === detailGen.current) setPreview(result) }
    catch (cause) { if (gen === detailGen.current) setError(cause instanceof Error ? cause.message : 'Anteprima non disponibile.') }
    finally { if (gen === detailGen.current) setLoading(false) }
  }
  const formFields: FieldSpec[] = creating ? spec.fields.filter(field => field.edit || (kind === 'Item Price' && ['item_code', 'valid_from'].includes(field.key)) || (kind === 'Appointment Type' && ['appointment_type', 'cc_service_item'].includes(field.key)) || (kind === 'CC Center Service' && field.key === 'appointment_type') || (kind === 'CC Package Template' && field.key === 'service_item')).map(field => ({ ...field, required: true })) : spec.fields.filter(field => field.edit)
  const columns: { key: string; label: string; render: (value: unknown, row: Row) => React.ReactNode }[] = kind === 'Healthcare Practitioner'
    ? [{ key: 'practitioner_name', label: 'Professionista', render: (_value, row) => archivePractitionerName(row as Practitioner) },
      { key: 'status', label: 'Stato', render: value => value === 'Active' ? 'Attivo' : 'Non attivo' }]
    : [spec.fields[0], ...spec.fields.slice(1, 3)].map(field => ({ key: field.key, label: field.label, render: (value: unknown, row: Row) => kind === 'Patient' && field.key === 'patient_name' ? archivePatientName(row) : kind === 'Patient' && field.key === 'first_name' && syntheticCode(value) ? `Dato di prova ${syntheticLetter(value) ?? ''}` : kind === 'Patient' && ['first_name', 'last_name'].includes(field.key) ? String(value || '—') : (kind === 'Item' && field.key === 'item_name') || (kind === 'CC Package Template' && field.key === 'title') ? archiveCatalogName(kind, row) : view(field, value) }))
  columns.push({ key: 'name', label: 'Scheda', render: () => <ArrowRight size={16} aria-hidden="true" /> })
  const selectedTitle = selected ? kind === 'Patient' ? archivePatientName(selected) : kind === 'Healthcare Practitioner' ? archivePractitionerName(selected as Practitioner) : kind === 'Item' || kind === 'CC Package Template' ? archiveCatalogName(kind, selected) : demoText(selected[spec.fields[0].key] || selected.name) : ''
  const editableNameKey = kind === 'Patient' || kind === 'Healthcare Practitioner' ? 'first_name' : kind === 'Item' ? 'item_name' : kind === 'CC Package Template' ? 'title' : ''
  const displayDiffersFromStored = !!selected && !!editableNameKey && !!draft && !creating && selectedTitle !== String(selected[editableNameKey] ?? '').trim()
  const canPrint = !!document?.can_print
  const documentMoney = (value: unknown, unit?: string) => value == null ? '—' : unit ? money(value, unit) : `${new Intl.NumberFormat('it-IT', { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(Number(value))} (valuta non indicata)`
  const documentNumber = (value: unknown) => value == null ? '—' : new Intl.NumberFormat('it-IT', { maximumFractionDigits: 6 }).format(Number(value))
  const detailFields = kind === 'Healthcare Practitioner' && selected && syntheticCode(selected.first_name)
    ? [{ key: 'practitioner_name', label: 'Identità' }, { key: 'status', label: 'Stato' }] : spec.fields
  const groups = ['Anagrafiche', 'Catalogo', 'Finanza'].filter(group => visible.some(s => s.group === group))
  return <>
    <Heading eyebrow="ARCHIVI OPERATIVI" title="Archivi" subtitle="Dati del centro, con autorizzazioni verificate dal server." />
    <div className="archive-layout"><nav className="archive-menu" aria-label="Tipi di archivio">{groups.map(group => <div key={group}><h2>{group}</h2>{visible.filter(s => s.group === group).map(s => <button key={s.kind} aria-label={s.label} className={spec.kind === s.kind ? 'active' : ''} aria-current={spec.kind === s.kind ? 'page' : undefined} onClick={() => change(s.kind)}>{s.label}</button>)}</div>)}</nav>
      <section className="panel archive-panel"><div className="panel-toolbar"><div className="panel-title"><h2>{spec.label}</h2><p>{rows.length} {rows.length === 1 ? 'scheda' : 'schede'} · {centerNameFor(center, boot?.centers?.length ? boot.centers : financeBoot?.centers ?? [])}{hasMore ? ' · altri risultati disponibili nella ricerca dedicata' : ''}</p></div><div className="form-actions">{manager && creatableKinds.includes(kind) && <Button onClick={beginCreate}>Nuova scheda</Button>}<Button variant="secondary" onClick={() => void refresh(spec.kind, debouncedSearch)} disabled={loading}>Ricarica</Button></div></div>
        <div className="archive-filters"><label className="search-inline"><Search size={17} /><input type="search" aria-label={`Cerca in ${spec.label.toLocaleLowerCase('it-IT')}`} placeholder={`Cerca in ${spec.label.toLocaleLowerCase('it-IT')}…`} value={search} onChange={e => setSearch(e.target.value)} /></label>{kind === 'Payment Entry' && <div className="archive-dates"><Field label="Dal"><DateInput value={paymentStart} onChange={setPaymentStart} calendarLabel="data iniziale pagamenti" /></Field><Field label="Al"><DateInput value={paymentEnd} onChange={setPaymentEnd} calendarLabel="data finale pagamenti" /></Field><Button variant="secondary" onClick={() => void refresh(spec.kind, debouncedSearch)}>Applica</Button></div>}</div>
        {(loading || pendingQuery) && <p className="panel-loading" role="status">Caricamento…</p>}{error && <p className="alert error" role="alert">{error}</p>}
        {!loading && !pendingQuery && (filtered.length ? <DataTable rows={filtered} columns={columns} onRow={row => void open(row as ArchiveRecord)} /> : <Empty title="Nessuna scheda trovata" detail="Modifica il filtro o ricarica la lista." />)}
        {!pendingQuery && hasMore && <div className="archive-more"><Button variant="secondary" onClick={() => void more()} disabled={loading}>Carica altri</Button></div>}
        <p className="scope-note">Seleziona una scheda per consultarne i dettagli.</p>
      </section></div>
    {notice && <div className="alert success archive-notice" role="status">{notice}<button onClick={() => setNotice('')} aria-label="Chiudi avviso">×</button></div>}
    {selected && <Drawer title={selectedTitle} compact onClose={() => { detailGen.current++; setSelected(null); setDocument(null); setDraft(null) }}>
      <div className="detail-section"><h3>{kind === 'Patient' ? 'Anagrafica' : 'Dettaglio'}</h3>
        <dl className="property-list">{detailFields.map(field => <div key={field.key}><dt>{field.label}</dt><dd>{document && ['grand_total', 'outstanding_amount', 'paid_amount', 'unallocated_amount'].includes(field.key) ? documentMoney(selected[field.key], field.key === 'outstanding_amount' || field.key === 'unallocated_amount' ? document.party_currency : field.key === 'paid_amount' ? document.paid_currency : document.currency) : kind === 'Patient' && field.key === 'patient_name' ? archivePatientName(selected) : kind === 'Patient' && field.key === 'first_name' && syntheticCode(selected.first_name) ? `Dato di prova ${syntheticLetter(selected.first_name) ?? ''}` : kind === 'Healthcare Practitioner' && field.key === 'practitioner_name' ? archivePractitionerName(selected as Practitioner) : kind === 'Healthcare Practitioner' && field.key === 'status' ? selected.status === 'Active' ? 'Attivo' : 'Non attivo' : ((kind === 'Item' && field.key === 'item_name') || (kind === 'CC Package Template' && field.key === 'title')) ? archiveCatalogName(kind, selected) : view(field, selected[field.key])}</dd></div>)}</dl>
        {document && <section className="detail-section"><h3>Documento completo</h3><dl className="property-list"><div><dt>Numero documento</dt><dd>{document.name}</dd></div><div><dt>Soggetto</dt><dd>{document.party || "—"}</dd></div><div><dt>Sede</dt><dd>{centerNameFor(center, boot?.centers?.length ? boot.centers : financeBoot?.centers ?? [])}</dd></div>{document.status && <div><dt>Stato contabile</dt><dd>{financeFieldValue('status', document.status)}</dd></div>}{document.address && <div><dt>Indirizzo</dt><dd>{document.address}</dd></div>}{document.tax_id && <div><dt>Identificativo fiscale</dt><dd>{document.tax_id}</dd></div>}{document.company_address && <div><dt>Indirizzo azienda</dt><dd>{document.company_address}</dd></div>}{document.company_tax_id && <div><dt>Identificativo fiscale azienda</dt><dd>{document.company_tax_id}</dd></div>}{document.due_date && <div><dt>Scadenza</dt><dd>{displayDate(document.due_date)}</dd></div>}{document.mode_of_payment && <div><dt>Metodo</dt><dd>{document.mode_of_payment}</dd></div>}{document.reference_no && <div><dt>Riferimento</dt><dd>{document.reference_no}</dd></div>}{document.reference_date && <div><dt>Data riferimento</dt><dd>{displayDate(document.reference_date)}</dd></div>}{document.payment_type && <div><dt>Operazione</dt><dd>{financeFieldValue('payment_type', document.payment_type)}</dd></div>}{(['net_total', 'discount_amount', 'total_taxes_and_charges', 'grand_total', 'outstanding_amount', 'paid_amount', 'received_amount', 'unallocated_amount'] as const).map(key => document[key] != null && <div key={key}><dt>{({ net_total: 'Imponibile', discount_amount: 'Sconto', total_taxes_and_charges: 'Imposte e oneri', grand_total: 'Totale', outstanding_amount: 'Residuo', paid_amount: 'Importo pagato', received_amount: 'Importo ricevuto', unallocated_amount: 'Non attribuito' })[key]}</dt><dd>{documentMoney(document[key], key === 'paid_amount' ? document.paid_currency : key === 'received_amount' ? document.received_currency : key === 'unallocated_amount' || key === 'outstanding_amount' ? document.party_currency : document.currency)}</dd></div>)}</dl>{document.items && <><h3>Servizi e articoli</h3>{document.items.length ? document.items.map((item, i) => <div className="archive-display-context" key={i}><strong>{item.item_name || item.description}</strong><p>{item.description}</p><p>Quantità: {documentNumber(item.qty)} {item.uom} · Prezzo: {documentMoney(item.rate, document.currency)} · Importo: {documentMoney(item.amount, document.currency)}</p>{!!item.discount_percentage && <p>Sconto: {documentNumber(item.discount_percentage)}%</p>}{!!item.discount_amount && <p>Sconto per unità: {documentMoney(item.discount_amount, document.currency)}</p>}</div>) : <p>Nessuna riga presente.</p>}</>}{document.taxes?.map((tax, i) => <p key={i}>{tax.description || 'Imposta'}: {documentMoney(tax.tax_amount, document.currency)}</p>)}{document.references?.map((ref, i) => <p key={i}>Documento collegato: {ref.name} · {documentMoney(ref.allocated_amount, document.party_currency)}</p>)}{document.links?.map((link, i) => <p key={i}>Documento collegato: {link.name}</p>)}</section>}
        {kind === 'Payment Entry' && Array.isArray(selected.references) && <p>{selected.references.length} {selected.references.length === 1 ? 'documento collegato' : 'documenti collegati'}.</p>}
        {kind === 'Sales Invoice' && Number(selected.docstatus) === 2 && <p className="scope-note">Il residuo mostrato appartiene al documento annullato: non è un importo da incassare.</p>}
        {kind === 'Purchase Invoice' && Number(selected.docstatus) === 2 && <p className="scope-note">Il residuo mostrato appartiene al documento annullato: non è un importo da pagare.</p>}
        {['Sales Invoice', 'Purchase Invoice', 'Payment Entry'].includes(kind) && !canPrint && <p className="scope-note">{Number(selected.docstatus) === 2 ? 'Questo documento è annullato e non è disponibile per la stampa.' : Number(selected.docstatus) === 0 ? 'Questo documento è in bozza e non è disponibile per la stampa.' : 'Non hai il permesso di stampare questo documento.'}</p>}
        <div className="form-actions">{manager && editableKinds.includes(kind) && <Button onClick={edit}>Modifica scheda</Button>}{['Sales Invoice', 'Purchase Invoice', 'Payment Entry'].includes(kind) && canPrint && <Button variant="secondary" onClick={() => void print()}><Printer size={16} /> Anteprima e stampa</Button>}</div>
      </div>
    </Drawer>}
    {draft && !confirm && <Modal title={`${creating ? 'Nuova scheda' : 'Modifica'} · ${spec.label}`} onClose={() => setDraft(null)}><form onSubmit={event => { event.preventDefault(); const issue = validate(); if (issue) setError(issue); else { setError(''); setConfirm(true) } }}><p>Modifica i dati della scheda e indica il motivo: l’operazione sarà registrata.</p>{displayDiffersFromStored && <p className="archive-display-context">Scheda selezionata: <strong>{selectedTitle}</strong>. Le modifiche riguardano solo questa scheda.</p>}{selected && <details><summary>Identificativo della scheda</summary><p>{selected.name}</p></details>}<div className="form-grid">{formFields.map(field => {
      if (field.key === 'valid_from') {
        return <Field key={field.key} label={field.label} required={field.required}><DateInput value={String(draft[field.key] ?? '')} onChange={value => update(field.key, value)} required={field.required} /></Field>
      }
      if (field.key === 'item_code' || field.key === 'cc_service_item' || field.key === 'service_item') {
        return <SearchableSelect key={field.key} label={field.label} options={availableItems} value={String(draft[field.key] ?? '')} onChange={value => update(field.key, value)} required={field.required} empty="Nessun articolo disponibile" />
      }
      if (field.key === 'appointment_type' && kind === 'CC Center Service') {
        return <SearchableSelect key={field.key} label={field.label} options={availableTypes} value={String(draft[field.key] ?? '')} onChange={value => update(field.key, value)} required={field.required} empty="Nessun tipo seduta disponibile" />
      }
      if (field.kind === 'select') {
        return <Field key={field.key} label={field.label} required={field.required}><select value={String(draft[field.key] ?? '')} onChange={event => update(field.key, event.target.value)}>{field.values?.map(choice => <option key={choice.value} value={choice.value}>{choice.label}</option>)}</select></Field>
      }
      return <Field key={field.key} label={field.label} required={field.required}>{field.key === editableNameKey && selected && syntheticCode(selected[field.key]) && <span>Il nome registrato è un codice di prova. Inserisci il nome leggibile da salvare per questa scheda.</span>}<input type={field.kind ?? 'text'} required={field.required} min={field.kind === 'number' ? 0 : undefined} step={field.kind === 'number' ? 'any' : undefined} value={String(draft[field.key] ?? '')} onChange={event => update(field.key, event.target.value)} /></Field>
    })}</div><Field label="Motivo della modifica" required><input value={reason} maxLength={500} onChange={event => { setReason(event.target.value); key.current = requestKey() }} /></Field><FormError error={error} /><div className="form-actions"><Button type="button" variant="secondary" onClick={() => setDraft(null)}>Annulla</Button><Button type="submit">{creating ? 'Rivedi dati' : 'Rivedi modifica'}</Button></div></form></Modal>}
    {confirm && <Modal title={creating ? `Conferma creazione · ${spec.label}` : `Conferma modifica · ${spec.label}`} onClose={() => setConfirm(false)}>
      <div className="review-diff-container">
        <p style={{ margin: '0 0 10px 0', fontSize: 13, color: '#475569' }}>
          {creating ? 'Verifica i dati della nuova scheda prima di salvare nel sistema:' : 'Verifica le variazioni apportate alla scheda prima di salvare:'}
        </p>
        <div style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: 8, padding: '10px 14px', marginBottom: 12, fontSize: 13 }}>
          <div><strong>Entità:</strong> {spec.label}</div>
          <div><strong>Sede:</strong> {centerNameFor(center, boot?.centers?.length ? boot.centers : financeBoot?.centers ?? [])}</div>
          {!creating && selected && <div><strong>Scheda:</strong> {selectedTitle}</div>}
          <div style={{ marginTop: 4 }}><strong>Motivo della modifica:</strong> {reason}</div>
        </div>
        <table className="review-diff-table">
          <thead>
            <tr>
              <th>Campo</th>
              {!creating && <th>Valore attuale</th>}
              <th>{creating ? 'Valore impostato' : 'Nuovo valore'}</th>
            </tr>
          </thead>
          <tbody>
            {formFields.filter(f => creating || String(draft?.[f.key] ?? '') !== String(selected?.[f.key] ?? '')).map(f => (
              <tr key={f.key}>
                <td><strong>{f.label}</strong></td>
                {!creating && <td>{syntheticCode(selected?.[f.key]) ? 'Dato di prova registrato' : view(f, selected?.[f.key])}</td>}
                <td style={{ color: !creating ? '#15803d' : undefined, fontWeight: 600 }}>{view(f, draft?.[f.key])}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {kind === 'Item Price' && (
          <div style={{ background: '#eff6ff', border: '1px solid #bfdbfe', borderRadius: 6, padding: '8px 12px', margin: '12px 0', fontSize: 12, color: '#1e40af' }}>
            La nuova tariffa vale per le future prenotazioni dalla data indicata. Le sedute già fissate mantengono il prezzo registrato al momento della prenotazione.
          </div>
        )}
        <div className="form-actions" style={{ marginTop: 16 }}>
          <Button variant="secondary" onClick={() => setConfirm(false)}>Torna al form</Button>
          <Button onClick={() => void save()} disabled={loading}>{loading ? 'Salvataggio…' : 'Conferma salvataggio'}</Button>
        </div>
      </div>
    </Modal>}
    {preview && <Modal title={`Anteprima · ${demoText(preview.name)}`} onClose={() => setPreview(null)}><p className="scope-note">Per escludere data e indirizzo del browser, disattiva intestazioni e piè di pagina nelle opzioni di stampa.</p><iframe ref={frame} title={`Documento ${demoText(preview.name)}`} srcDoc={preview.html} sandbox="allow-same-origin allow-modals" referrerPolicy="no-referrer" className="document-preview" /><div className="form-actions"><Button variant="secondary" onClick={() => setPreview(null)}>Chiudi</Button><Button onClick={() => frame.current?.contentWindow?.print()}><Printer size={16} /> Stampa</Button></div></Modal>}
  </>
}
