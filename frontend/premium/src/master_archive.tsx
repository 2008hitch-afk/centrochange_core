import React, { useEffect, useMemo, useState } from 'react'
import { ArrowRight, Plus, Search } from 'lucide-react'
import { type Boot, type FinanceBoot, type Row, displayDate, money, romeToday } from './api'
import { Button, Chip, DataTable, DateInput, Drawer, Empty, Field, FormError, Heading, Modal } from './ui'

type FieldType = 'text' | 'number' | 'date' | 'email' | 'select'
type ArchiveField = { key: string; label: string; type?: FieldType; required?: boolean; options?: string[]; min?: number }
type ArchiveKind = 'Sales Invoice' | 'Purchase Invoice' | 'Payment Entry' | 'Bank Transaction' | 'Patient' | 'Healthcare Practitioner' | 'Item' | 'Item Price' | 'Appointment Type' | 'CC Center Service' | 'CC Package Template'
type Definition = { kind: ArchiveKind; label: string; group: string; id: string; fields: ArchiveField[] }

const definitions: Definition[] = [
  { kind: 'Patient', label: 'Pazienti', group: 'Anagrafiche', id: 'PAT', fields: [{ key: 'patient_name', label: 'Nome e cognome', required: true }, { key: 'email', label: 'Email', type: 'email' }, { key: 'phone', label: 'Telefono' }] },
  { kind: 'Healthcare Practitioner', label: 'Professionisti', group: 'Anagrafiche', id: 'PR', fields: [{ key: 'practitioner_name', label: 'Nome professionista', required: true }, { key: 'specialty', label: 'Specializzazione' }, { key: 'email', label: 'Email', type: 'email' }] },
  { kind: 'Item', label: 'Articoli', group: 'Catalogo', id: 'ITEM', fields: [{ key: 'item_name', label: 'Nome articolo', required: true }, { key: 'item_group', label: 'Categoria', required: true }, { key: 'disabled', label: 'Stato', type: 'select', options: ['Attivo', 'Disattivato'] }] },
  { kind: 'Item Price', label: 'Tariffe', group: 'Catalogo', id: 'PRICE', fields: [{ key: 'item_code', label: 'Articolo', required: true }, { key: 'price_list', label: 'Listino', required: true }, { key: 'price_list_rate', label: 'Importo EUR', type: 'number', required: true, min: 0 }, { key: 'valid_from', label: 'Valida dal', type: 'date', required: true }] },
  { kind: 'Appointment Type', label: 'Tipi seduta', group: 'Catalogo', id: 'TYPE', fields: [{ key: 'appointment_type', label: 'Tipo seduta', required: true }, { key: 'duration', label: 'Durata in minuti', type: 'number', required: true, min: 1 }] },
  { kind: 'CC Center Service', label: 'Servizi del centro', group: 'Catalogo', id: 'SERV', fields: [{ key: 'cc_service_label', label: 'Nome servizio', required: true }, { key: 'cc_service_item', label: 'Articolo collegato', required: true }, { key: 'duration', label: 'Durata in minuti', type: 'number', required: true, min: 1 }, { key: 'cc_price_snapshot', label: 'Tariffa EUR', type: 'number', required: true, min: 0 }] },
  { kind: 'CC Package Template', label: 'Modelli pacchetto', group: 'Catalogo', id: 'PACK', fields: [{ key: 'title', label: 'Nome modello', required: true }, { key: 'service_item', label: 'Articolo servizio', required: true }, { key: 'units', label: 'Numero di sedute incluse', type: 'number', required: true, min: 1 }] },
  { kind: 'Sales Invoice', label: 'Fatture pazienti', group: 'Finanza', id: 'SINV', fields: [{ key: 'customer', label: 'Cliente', required: true }, { key: 'posting_date', label: 'Data documento', type: 'date', required: true }, { key: 'grand_total', label: 'Totale EUR', type: 'number', required: true, min: 0 }, { key: 'outstanding_amount', label: 'Residuo EUR', type: 'number', required: true, min: 0 }] },
  { kind: 'Purchase Invoice', label: 'Fatture professionisti', group: 'Finanza', id: 'PINV', fields: [{ key: 'supplier', label: 'Fornitore', required: true }, { key: 'posting_date', label: 'Data documento', type: 'date', required: true }, { key: 'grand_total', label: 'Totale EUR', type: 'number', required: true, min: 0 }, { key: 'outstanding_amount', label: 'Residuo EUR', type: 'number', required: true, min: 0 }] },
  { kind: 'Payment Entry', label: 'Pagamenti', group: 'Finanza', id: 'PAY', fields: [{ key: 'party', label: 'Soggetto', required: true }, { key: 'posting_date', label: 'Data pagamento', type: 'date', required: true }, { key: 'payment_type', label: 'Tipo', type: 'select', options: ['Receive', 'Pay'], required: true }, { key: 'paid_amount', label: 'Importo EUR', type: 'number', required: true, min: 0 }] },
  { kind: 'Bank Transaction', label: 'Movimenti bancari', group: 'Finanza', id: 'BANK', fields: [{ key: 'date', label: 'Data movimento', type: 'date', required: true }, { key: 'reference_number', label: 'Riferimento', required: true }, { key: 'deposit', label: 'Entrata EUR', type: 'number', min: 0 }, { key: 'withdrawal', label: 'Uscita EUR', type: 'number', min: 0 }] }
]

export const syntheticArchive = import.meta.env.DEV && import.meta.env.VITE_CC_SYNTHETIC_UI === '1'
const seed = (): Record<ArchiveKind, Row[]> => {
  const today = romeToday()
  return {
    Patient: [{ name: 'PAT-DEMO-1', patient_name: 'Paziente di prova', email: 'paziente@example.invalid', phone: '000 000 0000' }],
    'Healthcare Practitioner': [{ name: 'PR-DEMO-1', practitioner_name: 'Professionista di prova', specialty: 'Psicologia', email: 'professionista@example.invalid' }],
    Item: [{ name: 'ITEM-DEMO-1', item_name: 'Prima visita di prova', item_group: 'Servizi', disabled: 'Attivo' }],
    'Item Price': [{ name: 'PRICE-DEMO-1', item_code: 'ITEM-DEMO-1', price_list: 'Listino di prova', price_list_rate: 80, valid_from: today }],
    'Appointment Type': [{ name: 'TYPE-DEMO-1', appointment_type: 'Prima visita di prova', duration: 60 }],
    'CC Center Service': [{ name: 'SERV-DEMO-1', cc_service_label: 'Prima visita di prova', cc_service_item: 'ITEM-DEMO-1', duration: 60, cc_price_snapshot: 80 }],
    'CC Package Template': [{ name: 'PACK-DEMO-1', title: 'Percorso di quattro sedute', service_item: 'ITEM-DEMO-1', units: 4 }],
    'Sales Invoice': [{ name: 'SINV-DEMO-1', customer: 'Cliente di prova', posting_date: today, grand_total: 80, outstanding_amount: 20 }],
    'Purchase Invoice': [{ name: 'PINV-DEMO-1', supplier: 'Professionista di prova', posting_date: today, grand_total: 40, outstanding_amount: 10 }],
    'Payment Entry': [{ name: 'PAY-DEMO-1', party: 'Cliente di prova', posting_date: today, payment_type: 'Receive', paid_amount: 60 }],
    'Bank Transaction': [{ name: 'BANK-DEMO-1', date: today, reference_number: 'PROVA-001', deposit: 60, withdrawal: 0 }]
  }
}
const labelValue = (field: ArchiveField, value: unknown) => field.type === 'date' ? displayDate(value) : field.type === 'number' && /amount|total|rate|deposit|withdrawal|snapshot/.test(field.key) ? money(value) : String(value ?? '—')
const labelFor = (definition: Definition, row: Row) => String(row[definition.fields[0].key] || row.name || 'Scheda')

/** Only active in Vite development with VITE_CC_SYNTHETIC_UI=1. Never calls Frappe or persists. */
export function MasterArchive({ boot, financeBoot, center }: { boot: Boot; financeBoot: FinanceBoot | null; center: string }) {
  const [kind, setKind] = useState<ArchiveKind>('Patient')
  const [records, setRecords] = useState(seed)
  const [search, setSearch] = useState('')
  const [selected, setSelected] = useState<Row | null>(null)
  const [editor, setEditor] = useState<Row | null>(null)
  const [draft, setDraft] = useState<Row>({})
  const [confirm, setConfirm] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  useEffect(() => { setRecords(seed()); setSelected(null); setEditor(null); setSearch('') }, [boot, financeBoot, center])
  const definition = definitions.find(d => d.kind === kind)!
  const financeArea = definition.group === 'Finanza'
  const allowed = financeArea ? !!financeBoot : !!boot
  const rows = useMemo(() => (records[kind] ?? []).filter(r => `${Object.values(r).join(' ')}`.toLocaleLowerCase('it-IT').includes(search.toLocaleLowerCase('it-IT').trim())), [records, kind, search])
  const changeKind = (next: ArchiveKind) => { setKind(next); setSearch(''); setSelected(null); setEditor(null); setError(''); setNotice('') }
  const edit = (row: Row) => { setEditor(row); setDraft({ ...row }); setSelected(null); setError(''); setConfirm(false) }
  const checkDraft = () => {
    for (const field of definition.fields) {
      const value = String(draft[field.key] ?? '').trim()
      if (field.required && !value) return `Compila ${field.label.toLocaleLowerCase('it-IT')}.`
      if (field.type === 'number' && value && (!Number.isFinite(Number(value)) || Number(value) < (field.min ?? 0))) return `Verifica ${field.label.toLocaleLowerCase('it-IT')}.`
      if (field.type === 'email' && value && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) return 'Inserisci un indirizzo email valido.'
    }
    if (kind === 'Bank Transaction' && Number(draft.deposit || 0) > 0 && Number(draft.withdrawal || 0) > 0) return 'Indica un’entrata oppure un’uscita.'
    return ''
  }
  const save = () => {
    const issue = checkDraft(); if (issue) { setError(issue); setConfirm(false); return }
    setConfirm(false); setLoading(true); setError('')
    window.setTimeout(() => {
      if (sessionStorage.getItem('cc-synthetic-fail') === '1') { setError('Simulazione non riuscita. Riprova.'); setLoading(false); return }
      const name = String(editor?.name ?? `${definition.id}-DEMO-${Date.now()}`)
      const next = { ...draft, name }
      setRecords(old => ({ ...old, [kind]: editor?.name ? old[kind].map(r => r.name === editor.name ? next : r) : [...old[kind], next] }))
      setEditor(null); setSelected(next); setLoading(false)
      setNotice('Bozza di prova aggiornata nel browser. Nessun dato salvato su Frappe.')
    }, 240)
  }
  const columns = [{ key: definition.fields[0].key, label: definition.fields[0].label, render: (v: unknown) => <strong>{String(v ?? '—')}</strong> }, ...definition.fields.slice(1, 3).map(f => ({ key: f.key, label: f.label, render: (v: unknown) => labelValue(f, v) })), { key: 'name', label: 'Scheda', render: () => <ArrowRight size={16} aria-hidden="true" /> }]
  const groups = ['Anagrafiche', 'Catalogo', 'Finanza'].filter(group => definitions.some(d => d.group === group))
  return <>
    <Heading eyebrow="ARCHIVI OPERATIVI" title="Archivi" subtitle="Schede e liste del perimetro MVP, raggruppate per attività." />
    {syntheticArchive && <div className="synthetic-banner" role="status"><strong>Anteprima sintetica</strong><span>Modifiche solo in memoria nel browser. Nessun salvataggio Frappe.</span></div>}
    <div className="archive-layout"><nav className="archive-menu" aria-label="Tipi di archivio">{groups.map(group => <div key={group}><h2>{group}</h2>{definitions.filter(d => d.group === group).map(d => <button key={d.kind} aria-label={d.label} className={kind === d.kind ? 'active' : ''} aria-current={kind === d.kind ? 'page' : undefined} onClick={() => changeKind(d.kind)} disabled={d.group === 'Finanza' && !financeBoot}>{d.label}<span>{records[d.kind]?.length ?? 0}</span></button>)}</div>)}</nav>
    <section className="panel archive-panel"><div className="panel-toolbar"><div className="panel-title"><h2>{definition.label}</h2><p>{rows.length} {rows.length === 1 ? 'scheda' : 'schede'} · {center}</p></div>{syntheticArchive && allowed && <Button onClick={() => edit({})}><Plus size={16} /> Nuova scheda</Button>}</div><div className="archive-filters"><label className="search-inline"><Search size={17} /><input type="search" aria-label={`Cerca in ${definition.label.toLocaleLowerCase('it-IT')}`} placeholder="Cerca per nome, codice o riferimento" value={search} onChange={e => setSearch(e.target.value)} /></label></div>{loading ? <p className="panel-loading" role="status">Aggiornamento bozza di prova…</p> : rows.length ? <DataTable rows={rows} columns={columns} onRow={setSelected} /> : <Empty title="Nessuna scheda trovata" detail="Modifica la ricerca o crea una scheda di prova." />}{!syntheticArchive && <p className="scope-note">Gli editor di questi archivi richiedono API di dominio e permessi approvati. I dati non vengono modificati da questa vista.</p>}</section></div>
    {notice && <div className="alert success archive-notice" role="status">{notice}<button onClick={() => setNotice('')} aria-label="Chiudi avviso">×</button></div>}
    {selected && <Drawer title={labelFor(definition, selected)} onClose={() => setSelected(null)}><div className="detail-summary"><Chip tone="blue">{definition.label}</Chip><p>Codice: {String(selected.name ?? '—')}</p></div><div className="detail-section"><h3>Dettaglio</h3><dl className="property-list">{definition.fields.map(f => <div key={f.key}><dt>{f.label}</dt><dd>{labelValue(f, selected[f.key])}</dd></div>)}</dl>{syntheticArchive && <Button onClick={() => edit(selected)}>Modifica bozza di prova</Button>}</div></Drawer>}
    {editor && !confirm && <Modal title={`${editor.name ? 'Modifica' : 'Nuova scheda'} · ${definition.label}`} onClose={() => { setEditor(null); setConfirm(false) }}><form onSubmit={e => { e.preventDefault(); const issue = checkDraft(); if (issue) setError(issue); else { setError(''); setConfirm(true) } }}><p className="synthetic-form-note">Anteprima sintetica: questa scheda non sarà salvata su Frappe.</p><div className="form-grid">{definition.fields.map(f => <Field key={f.key} label={f.label} required={f.required}>{f.type === 'select' ? <select required={f.required} value={String(draft[f.key] ?? '')} onChange={e => setDraft(d => ({ ...d, [f.key]: e.target.value }))}><option value="">Seleziona</option>{f.options?.map(o => <option key={o} value={o}>{o === 'Receive' ? 'Incasso' : o === 'Pay' ? 'Pagamento' : o}</option>)}</select> : f.type === 'date' ? <DateInput value={String(draft[f.key] ?? '')} onChange={value => setDraft(d => ({ ...d, [f.key]: value }))} required={f.required} /> : <input type={f.type ?? 'text'} required={f.required} min={f.type === 'number' ? f.min : undefined} step={f.type === 'number' ? 'any' : undefined} autoComplete="off" name={f.key} spellCheck={f.type === 'email' ? false : undefined} value={String(draft[f.key] ?? '')} onChange={e => setDraft(d => ({ ...d, [f.key]: e.target.value }))} />}</Field>)}</div><FormError error={error} /><div className="form-actions"><Button type="button" variant="secondary" onClick={() => setEditor(null)}>Annulla</Button><Button type="submit">Rivedi modifica di prova</Button></div></form></Modal>}
    {confirm && <Modal title="Conferma modifica di prova" onClose={() => setConfirm(false)}><p>La scheda sarà aggiornata solo nella memoria di questa pagina. Frappe e il database non cambieranno.</p><div className="form-actions"><Button variant="secondary" onClick={() => setConfirm(false)}>Torna al form</Button><Button onClick={save}>Conferma nella preview</Button></div></Modal>}
  </>
}
