import React, { useEffect, useMemo, useRef, useState } from 'react'
import { ArrowRight, Printer, Search } from 'lucide-react'
import { displayDate, money, recentPaymentStart, requestKey, romeToday, type Boot, type FinanceBoot, type Practitioner, type Row } from './api'
import { archiveDetail, createArchive, creatableKinds, documentPreview, editableKinds, financeKinds, listArchive, saveArchive, type ArchiveKind, type ArchiveRecord, type PrintPreview } from './scoped_api'
import { Button, DataTable, DateInput, Drawer, Empty, Field, FormError, Heading, Modal, SearchableSelect } from './ui'
import { financeFieldValue } from './finance_locale'
import { demoPatient, demoText, syntheticCode } from './demo_labels'
import { centerNameFor, practitionerName } from './display_names'

type FieldSpec = { key: string; label: string; edit?: boolean; required?: boolean; kind?: 'text' | 'number' | 'email' | 'select'; values?: { value: string; label: string }[] }
type Spec = { kind: ArchiveKind; label: string; group: string; fields: FieldSpec[] }
const status: FieldSpec = { key: 'enabled', label: 'Stato', edit: true, kind: 'select', values: [{ value: '1', label: 'Attivo' }, { value: '0', label: 'Disattivato' }] }
const specs: Spec[] = [
  { kind: 'Patient', label: 'Pazienti', group: 'Anagrafiche', fields: [{ key: 'patient_name', label: 'Paziente' }, { key: 'first_name', label: 'Nome', edit: true, required: true }, { key: 'last_name', label: 'Cognome', edit: true }, { key: 'email', label: 'Email', edit: true, kind: 'email' }] },
  { kind: 'Healthcare Practitioner', label: 'Professionisti', group: 'Anagrafiche', fields: [{ key: 'practitioner_name', label: 'Professionista' }, { key: 'first_name', label: 'Nome', edit: true, required: true }, { key: 'last_name', label: 'Cognome', edit: true }, { key: 'status', label: 'Stato' }] },
  { kind: 'Item', label: 'Articoli', group: 'Catalogo', fields: [{ key: 'item_name', label: 'Articolo', edit: true, required: true }, { key: 'item_group', label: 'Gruppo' }, { key: 'stock_uom', label: 'Unità' }, { key: 'disabled', label: 'Disabilitato' }] },
  { kind: 'Item Price', label: 'Tariffe', group: 'Catalogo', fields: [{ key: 'item_code', label: 'Articolo' }, { key: 'price_list', label: 'Listino' }, { key: 'price_list_rate', label: 'Tariffa', edit: true, required: true, kind: 'number' }, { key: 'currency', label: 'Valuta' }, { key: 'valid_from', label: 'Valida dal' }] },
  { kind: 'Appointment Type', label: 'Tipi seduta', group: 'Catalogo', fields: [{ key: 'appointment_type', label: 'Tipo seduta' }, { key: 'default_duration', label: 'Durata (min)', edit: true, required: true, kind: 'number' }, { key: 'cc_service_item', label: 'Articolo' }] },
  { kind: 'CC Center Service', label: 'Servizi del centro', group: 'Catalogo', fields: [{ key: 'appointment_type', label: 'Tipo seduta' }, { key: 'center', label: 'Centro' }, status] },
  { kind: 'CC Package Template', label: 'Modelli pacchetto', group: 'Catalogo', fields: [{ key: 'title', label: 'Modello', edit: true, required: true }, { key: 'service_item', label: 'Articolo' }, { key: 'units', label: 'Numero di sedute incluse', edit: true, required: true, kind: 'number' }, status] },
  { kind: 'Sales Invoice', label: 'Fatture pazienti', group: 'Finanza', fields: [{ key: 'name', label: 'Fattura' }, { key: 'customer', label: 'Cliente' }, { key: 'posting_date', label: 'Data' }, { key: 'grand_total', label: 'Totale' }, { key: 'outstanding_amount', label: 'Residuo' }] },
  { kind: 'Purchase Invoice', label: 'Fatture professionisti', group: 'Finanza', fields: [{ key: 'name', label: 'Fattura' }, { key: 'supplier', label: 'Fornitore' }, { key: 'posting_date', label: 'Data' }, { key: 'grand_total', label: 'Totale' }, { key: 'outstanding_amount', label: 'Residuo' }] },
  { kind: 'Payment Entry', label: 'Pagamenti', group: 'Finanza', fields: [{ key: 'name', label: 'Pagamento' }, { key: 'party', label: 'Soggetto' }, { key: 'posting_date', label: 'Data' }, { key: 'payment_type', label: 'Tipo' }, { key: 'paid_amount', label: 'Importo' }, { key: 'unallocated_amount', label: 'Non allocato' }] },
  { kind: 'Bank Transaction', label: 'Movimenti bancari', group: 'Finanza', fields: [{ key: 'name', label: 'Movimento' }, { key: 'date', label: 'Data' }, { key: 'reference_number', label: 'Riferimento' }, { key: 'deposit', label: 'Entrata' }, { key: 'withdrawal', label: 'Uscita' }] }
]
const view = (field: FieldSpec, value: unknown) => {
  if (value == null || value === '') return '—'
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

/** Live candidate: reads only approved projections; writes only manager-scoped existing records. */
export function ScopedArchive({ boot, financeBoot, center }: { boot: Boot | null; financeBoot: FinanceBoot | null; center: string }) {
  const manager = !!boot?.roles.includes('CC Manager') || !!financeBoot?.is_manager
  const visible = specs.filter(spec => spec.group === 'Catalogo' ? manager && !!boot : financeKinds.includes(spec.kind) ? !!financeBoot : spec.kind === 'Healthcare Practitioner' ? !!boot && (manager || boot.roles.includes('CC Professional')) : !!boot)
  const [kind, setKind] = useState<ArchiveKind>(boot ? 'Patient' : 'Sales Invoice')
  const [rows, setRows] = useState<ArchiveRecord[]>([])
  const [hasMore, setHasMore] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [search, setSearch] = useState('')
  const [paymentStart, setPaymentStart] = useState(recentPaymentStart)
  const [paymentEnd, setPaymentEnd] = useState(romeToday())
  const [selected, setSelected] = useState<ArchiveRecord | null>(null)
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

  async function refresh(activeKind = spec.kind) {
    setLoading(true); setError('')
    try { const result = await listArchive(center, activeKind, 0, { start: paymentStart, end: paymentEnd }); setRows(result.rows); setHasMore(result.has_more) }
    catch (cause) { setRows([]); setError(cause instanceof Error ? cause.message : 'Caricamento non riuscito.') }
    finally { setLoading(false) }
  }
  useEffect(() => { setSelected(null); setDraft(null); setSearch(''); void refresh(spec.kind) }, [center, spec.kind])
  const more = async () => {
    setLoading(true); setError('')
    try { const result = await listArchive(center, spec.kind, rows.length, { start: paymentStart, end: paymentEnd }); setRows(old => [...old, ...result.rows]); setHasMore(result.has_more) }
    catch (cause) { setError(cause instanceof Error ? cause.message : 'Caricamento non riuscito.') }
    finally { setLoading(false) }
  }
  const filtered = useMemo(() => rows.filter(row => Object.entries(row).map(([field, value]) => `${String(value ?? '')} ${kind === 'Patient' && ['name', 'patient_name'].includes(field) ? demoPatient(row.name, row.patient_name, row.first_name, row.last_name) : demoText(value)}`).join(' ').toLocaleLowerCase('it-IT').includes(search.toLocaleLowerCase('it-IT').trim())), [rows, search, kind])
  const change = (next: ArchiveKind) => { setKind(next); setNotice(''); setError('') }
  const open = async (row: ArchiveRecord) => {
    setLoading(true); setError('')
    try { setSelected(financeKinds.includes(kind) && kind !== 'Payment Entry' ? row : await archiveDetail(center, kind, row.name)) }
    catch (cause) { setError(cause instanceof Error ? cause.message : 'Dettaglio non disponibile.') }
    finally { setLoading(false) }
  }
  const edit = () => { if (!selected) return; setCreating(false); setDraft({ ...selected }); setReason(''); key.current = requestKey(); setConfirm(false); setError('') }
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
      setSelected(current); setDraft(null); setCreating(false); setNotice('Scheda salvata con successo.'); await refresh()
    } catch (cause) { setError(cause instanceof Error ? cause.message : 'Salvataggio non riuscito.') }
    finally { setLoading(false) }
  }
  const print = async () => {
    if (!selected || !['Sales Invoice', 'Purchase Invoice', 'Payment Entry'].includes(kind)) return
    setLoading(true); setError('')
    try { setPreview(await documentPreview(center, kind as 'Sales Invoice' | 'Purchase Invoice' | 'Payment Entry', selected.name)) }
    catch (cause) { setError(cause instanceof Error ? cause.message : 'Anteprima non disponibile.') }
    finally { setLoading(false) }
  }
  const formFields: FieldSpec[] = creating ? spec.fields.filter(field => field.edit || (kind === 'Item Price' && ['item_code', 'valid_from'].includes(field.key)) || (kind === 'Appointment Type' && ['appointment_type', 'cc_service_item'].includes(field.key)) || (kind === 'CC Center Service' && field.key === 'appointment_type') || (kind === 'CC Package Template' && field.key === 'service_item')).map(field => ({ ...field, required: true })) : spec.fields.filter(field => field.edit)
  const columns: { key: string; label: string; render: (value: unknown, row: Row) => React.ReactNode }[] = kind === 'Healthcare Practitioner'
    ? [{ key: 'practitioner_name', label: 'Professionista', render: (_value, row) => practitionerName(row as Practitioner) },
      { key: 'status', label: 'Stato', render: value => value === 'Active' ? 'Attivo' : 'Non attivo' }]
    : [spec.fields[0], ...spec.fields.slice(1, 3)].map(field => ({ key: field.key, label: field.label, render: (value: unknown, row: Row) => kind === 'Patient' && field.key === 'patient_name' ? demoPatient(row.name, value, row.first_name, row.last_name) : view(field, value) }))
  columns.push({ key: 'name', label: 'Scheda', render: () => <ArrowRight size={16} aria-hidden="true" /> })
  const selectedTitle = selected ? kind === 'Patient' ? demoPatient(selected.name, selected.patient_name, selected.first_name, selected.last_name) : kind === 'Healthcare Practitioner' ? practitionerName(selected as Practitioner) : demoText(selected[spec.fields[0].key] || selected.name) : ''
  const detailFields = kind === 'Healthcare Practitioner' && selected && syntheticCode(selected.first_name)
    ? [{ key: 'practitioner_name', label: 'Identità' }, { key: 'status', label: 'Stato' }] : spec.fields
  const groups = ['Anagrafiche', 'Catalogo', 'Finanza'].filter(group => visible.some(s => s.group === group))
  return <>
    <Heading eyebrow="ARCHIVI OPERATIVI" title="Archivi" subtitle="Dati del centro, con autorizzazioni verificate dal server." />
    <div className="archive-layout"><nav className="archive-menu" aria-label="Tipi di archivio">{groups.map(group => <div key={group}><h2>{group}</h2>{visible.filter(s => s.group === group).map(s => <button key={s.kind} aria-label={s.label} className={spec.kind === s.kind ? 'active' : ''} aria-current={spec.kind === s.kind ? 'page' : undefined} onClick={() => change(s.kind)}>{s.label}</button>)}</div>)}</nav>
      <section className="panel archive-panel"><div className="panel-toolbar"><div className="panel-title"><h2>{spec.label}</h2><p>{rows.length} {rows.length === 1 ? 'scheda' : 'schede'} · {centerNameFor(center, boot?.centers?.length ? boot.centers : financeBoot?.centers ?? [])}{hasMore ? ' · altri risultati disponibili nella ricerca dedicata' : ''}</p></div><div className="form-actions">{manager && creatableKinds.includes(kind) && <Button onClick={beginCreate}>Nuova scheda</Button>}<Button variant="secondary" onClick={() => void refresh()} disabled={loading}>Ricarica</Button></div></div>
        <div className="archive-filters"><label className="search-inline"><Search size={17} /><input type="search" aria-label={`Cerca in ${spec.label.toLocaleLowerCase('it-IT')}`} placeholder="Filtra le schede caricate" value={search} onChange={e => setSearch(e.target.value)} /></label>{kind === 'Payment Entry' && <div className="archive-dates"><Field label="Dal"><input type="date" value={paymentStart} onChange={event => setPaymentStart(event.target.value)} /></Field><Field label="Al"><input type="date" value={paymentEnd} onChange={event => setPaymentEnd(event.target.value)} /></Field><Button variant="secondary" onClick={() => void refresh()}>Applica</Button></div>}</div>
        {loading && <p className="panel-loading" role="status">Caricamento…</p>}{error && <p className="alert error" role="alert">{error}</p>}
        {!loading && (filtered.length ? <DataTable rows={filtered} columns={columns} onRow={row => void open(row as ArchiveRecord)} /> : <Empty title="Nessuna scheda trovata" detail="Modifica il filtro o ricarica la lista." />)}
        {hasMore && <div className="archive-more"><Button variant="secondary" onClick={() => void more()} disabled={loading}>Carica altri</Button></div>}
        <p className="scope-note">Nuove schede e campi non approvati richiedono una configurazione autorizzata. Nessuna scrittura generica è disponibile.</p>
      </section></div>
    {notice && <div className="alert success archive-notice" role="status">{notice}<button onClick={() => setNotice('')} aria-label="Chiudi avviso">×</button></div>}
    {selected && <Drawer title={selectedTitle} onClose={() => { setSelected(null); setDraft(null) }}>{kind !== 'Patient' && kind !== 'Healthcare Practitioner' && <div className="detail-summary"><p>Codice identificativo: {demoText(selected.name)}</p></div>}<div className="detail-section"><h3>{kind === 'Patient' ? 'Anagrafica' : 'Dettaglio'}</h3><dl className="property-list">{detailFields.map(field => <div key={field.key}><dt>{field.label}</dt><dd>{kind === 'Patient' && field.key === 'patient_name' ? demoPatient(selected.name, selected[field.key], selected.first_name, selected.last_name) : kind === 'Healthcare Practitioner' && field.key === 'practitioner_name' ? practitionerName(selected as Practitioner) : kind === 'Healthcare Practitioner' && field.key === 'status' ? selected.status === 'Active' ? 'Attivo' : 'Non attivo' : view(field, selected[field.key])}</dd></div>)}</dl>{kind === 'Payment Entry' && Array.isArray(selected.references) && <p>{selected.references.length} documenti collegati autorizzati.</p>}<div className="form-actions">{manager && editableKinds.includes(kind) && <Button onClick={edit}>Modifica scheda</Button>}{['Sales Invoice', 'Purchase Invoice', 'Payment Entry'].includes(kind) && <Button variant="secondary" onClick={() => void print()}><Printer size={16} /> Anteprima e stampa</Button>}</div></div></Drawer>}
    {draft && !confirm && <Modal title={`${creating ? 'Nuova scheda' : 'Modifica'} · ${spec.label}`} onClose={() => setDraft(null)}><form onSubmit={event => { event.preventDefault(); const issue = validate(); if (issue) setError(issue); else { setError(''); setConfirm(true) } }}><p>Solo i campi approvati sono modificabili. Ogni modifica viene tracciata nel registro di audit interno.</p><div className="form-grid">{formFields.map(field => {
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
      return <Field key={field.key} label={field.label} required={field.required}><input type={field.kind ?? 'text'} required={field.required} min={field.kind === 'number' ? 0 : undefined} step={field.kind === 'number' ? 'any' : undefined} value={String(draft[field.key] ?? '')} onChange={event => update(field.key, event.target.value)} /></Field>
    })}</div><Field label="Motivo" required><input value={reason} maxLength={500} onChange={event => { setReason(event.target.value); key.current = requestKey() }} /></Field><FormError error={error} /><div className="form-actions"><Button type="button" variant="secondary" onClick={() => setDraft(null)}>Annulla</Button><Button type="submit">{creating ? 'Rivedi dati' : 'Rivedi modifica'}</Button></div></form></Modal>}
    {confirm && <Modal title={creating ? `Conferma creazione · ${spec.label}` : `Conferma modifica · ${spec.label}`} onClose={() => setConfirm(false)}>
      <div className="review-diff-container">
        <p style={{ margin: '0 0 10px 0', fontSize: 13, color: '#475569' }}>
          {creating ? 'Verifica i dati della nuova scheda prima di salvare nel sistema:' : 'Verifica le variazioni apportate alla scheda prima di salvare:'}
        </p>
        <div style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: 8, padding: '10px 14px', marginBottom: 12, fontSize: 13 }}>
          <div><strong>Entità:</strong> {spec.label}</div>
          <div><strong>Sede:</strong> {centerNameFor(center, boot?.centers?.length ? boot.centers : financeBoot?.centers ?? [])}</div>
          {!creating && selected && <div><strong>Scheda:</strong> {demoText(selected[spec.fields[0].key] || selected.name)} ({demoText(selected.name)})</div>}
          <div style={{ marginTop: 4 }}><strong>Motivo:</strong> {reason}</div>
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
                {!creating && <td>{view(f, selected?.[f.key])}</td>}
                <td style={{ color: !creating ? '#15803d' : undefined, fontWeight: 600 }}>{view(f, draft?.[f.key])}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {kind === 'Item Price' && (
          <div style={{ background: '#eff6ff', border: '1px solid #bfdbfe', borderRadius: 6, padding: '8px 12px', margin: '12px 0', fontSize: 12, color: '#1e40af' }}>
            <strong>Nota economica (DECISION-053):</strong> la tariffa modificata sarà valida per le future prenotazioni a partire dalla data indicata. Le sedute già fissate nel calendario mantengono il loro prezzo snapshot originario.
          </div>
        )}
        <div className="form-actions" style={{ marginTop: 16 }}>
          <Button variant="secondary" onClick={() => setConfirm(false)}>Torna al form</Button>
          <Button onClick={() => void save()} disabled={loading}>{loading ? 'Salvataggio…' : 'Conferma salvataggio'}</Button>
        </div>
      </div>
    </Modal>}
    {preview && <Modal title={`Anteprima · ${demoText(preview.name)}`} onClose={() => setPreview(null)}><iframe ref={frame} title={`Documento ${demoText(preview.name)}`} srcDoc={preview.html} sandbox="allow-same-origin allow-modals" referrerPolicy="no-referrer" className="document-preview" /><div className="form-actions"><Button variant="secondary" onClick={() => setPreview(null)}>Chiudi</Button><Button onClick={() => frame.current?.contentWindow?.print()}><Printer size={16} /> Stampa</Button></div></Modal>}
  </>
}
