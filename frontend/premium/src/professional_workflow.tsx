import { useEffect, useRef, useState } from 'react'
import { type FinanceBoot, type Row, call, finance, requestKey, romeToday } from './api'
import { type Feedback, Button, DateInput, Field, FormError, Modal, useAction } from './ui'

type Operation = 'rule' | 'threshold' | 'capture' | 'compare' | 'override' | 'reevaluate'
type Props = { boot: FinanceBoot; center: string; feedback: Feedback; onSuccess: () => void }
const labels: Record<Operation, string> = {
  rule: 'Configura regola', threshold: 'Configura soglia', capture: 'Registra atteso',
  compare: 'Confronta fattura', override: 'Riconosci sospeso', reevaluate: 'Rivaluta attesi'
}
const getError = (e: unknown) => e instanceof Error ? e.message : 'Caricamento non riuscito.'

export function ProfessionalWorkflow({ boot, center, feedback, onSuccess }: Props) {
  const [open, setOpen] = useState(false)
  const [operation, setOperation] = useState<Operation>(boot.is_manager ? 'rule' : 'capture')
  const [sources, setSources] = useState<Row[]>([])
  const [expectations, setExpectations] = useState<Row[]>([])
  const [invoices, setInvoices] = useState<Row[]>([])
  const [rules, setRules] = useState<Row[]>([])
  const [loadError, setLoadError] = useState('')
  const [practitioner, setPractitioner] = useState('')
  const [item, setItem] = useState('')
  const [from, setFrom] = useState(romeToday())
  const [to, setTo] = useState('')
  const [basis, setBasis] = useState('Fixed Amount')
  const [value, setValue] = useState('')
  const [threshold, setThreshold] = useState('')
  const [source, setSource] = useState('')
  const [rule, setRule] = useState('')
  const [invoice, setInvoice] = useState('')
  const [selected, setSelected] = useState<string[]>([])
  const [expectation, setExpectation] = useState('')
  const [reason, setReason] = useState('')
  const keys = useRef<Record<string, string>>({})
  const { busy, error, run } = useAction(feedback, () => { setOpen(false); onSuccess() })

  useEffect(() => {
    if (!open) return
    let live = true
    setLoadError('')
    Promise.all([
      finance<Row[]>('reporting.records', { center, doctype: 'CC Economic Source Link' }),
      finance<Row[]>('reporting.records', { center, doctype: 'CC Professional Expectation' }),
      finance<Row[]>('reporting.records', { center, doctype: 'Purchase Invoice' }),
      call<Row[]>('frappe.client.get_list', { doctype: 'CC Compensation Rule', fields: ['name', 'practitioner', 'service_item'], filters: { center }, limit_page_length: 500 })
    ]).then(([s, e, i, r]) => { if (live) { setSources(s); setExpectations(e); setInvoices(i); setRules(r) } })
      .catch(e => { if (live) setLoadError(getError(e)) })
    return () => { live = false }
  }, [open, center])

  const keyFor = (payload: Row) => {
    const id = JSON.stringify(payload)
    return keys.current[id] ??= requestKey()
  }
  const submit = () => {
    let method: string
    let payload: Row
    switch (operation) {
      case 'rule':
        method = 'configure_rule'
        payload = { center, practitioner, service_item: item, valid_from: from, valid_to: to || null, basis, value, currency: 'EUR', reason }
        payload.request_key = keyFor(payload)
        break
      case 'threshold':
        method = 'configure_threshold'
        payload = { center, practitioner, max_unpaid_sessions_compensated: threshold, reason }
        payload.request_key = keyFor(payload)
        break
      case 'capture': method = 'capture'; payload = { source, rule: rule || null, reason }; break
      case 'compare': method = 'compare'; payload = { purchase_invoice: invoice, expectations: selected, reason }; break
      case 'override': method = 'override'; payload = { expectation, reason }; break
      case 'reevaluate': method = 'reevaluate'; payload = { center, reason }; break
    }
    void run(() => finance(`professional_economics.${method}`, payload, true), `${labels[operation]}: operazione registrata.`)
  }
  const available = (Object.keys(labels) as Operation[]).filter(id => boot.is_manager || !['rule', 'threshold', 'override'].includes(id))
  return <><Button onClick={() => setOpen(true)}>Operazioni compensi</Button>{open && <Modal title="Economia professionisti" onClose={() => setOpen(false)}><form onSubmit={e => { e.preventDefault(); submit() }}>
    <Field label="Operazione" required><select value={operation} onChange={e => setOperation(e.target.value as Operation)}>{available.map(id => <option key={id} value={id}>{labels[id]}</option>)}</select></Field>
    {operation === 'rule' && <><Field label="Professionista" required><select value={practitioner} onChange={e => setPractitioner(e.target.value)} required><option value="">Seleziona</option>{boot.practitioners.map(p => <option key={p.name} value={p.name}>{p.practitioner_name}</option>)}</select></Field><Field label="Servizio" required><select value={item} onChange={e => setItem(e.target.value)} required><option value="">Seleziona</option>{boot.items.filter(i => !i.is_group && !i.disabled).map(i => <option key={String(i.name)} value={String(i.name)}>{String(i.item_name ?? i.name)}</option>)}</select></Field><div className="form-grid"><Field label="Valida dal" required><DateInput value={from} onChange={setFrom} required /></Field><Field label="Valida fino al"><DateInput value={to} onChange={setTo} /></Field></div><Field label="Base" required><select value={basis} onChange={e => setBasis(e.target.value)}><option value="Fixed Amount">Importo fisso</option><option value="Percentage">Percentuale</option></select></Field><Field label={basis === 'Percentage' ? 'Percentuale' : 'Importo EUR'} required><input type="number" min="0" max={basis === 'Percentage' ? '100' : '1000000000'} step="0.01" value={value} onChange={e => setValue(e.target.value)} required /></Field></>}
    {operation === 'threshold' && <><Field label="Professionista" required><select value={practitioner} onChange={e => setPractitioner(e.target.value)} required><option value="">Seleziona</option>{boot.practitioners.map(p => <option key={p.name} value={p.name}>{p.practitioner_name}</option>)}</select></Field><Field label="Massimo sedute non incassate" required><input type="number" min="0" max="2147483647" step="1" value={threshold} onChange={e => setThreshold(e.target.value)} required /></Field><p className="scope-note">Soglia esplicita per professionista. Il conteggio resta separato per paziente.</p></>}
    {operation === 'capture' && <><Field label="Fonte seduta" required><select value={source} onChange={e => setSource(e.target.value)} required><option value="">Seleziona</option>{sources.map(s => <option key={String(s.name)} value={String(s.name)}>{String(s.session_date)} · {String(s.practitioner)} · {String(s.appointment)}</option>)}</select></Field><Field label="Regola esplicita"><select value={rule} onChange={e => setRule(e.target.value)}><option value="">Nessuna: atteso da verificare</option>{rules.map(r => <option key={String(r.name)} value={String(r.name)}>{String(r.name)} · {String(r.practitioner)} · {String(r.service_item)}</option>)}</select></Field></>}
    {operation === 'compare' && <><Field label="Fattura fornitore contabilizzata" required><select value={invoice} onChange={e => setInvoice(e.target.value)} required><option value="">Seleziona</option>{invoices.filter(i => Number(i.docstatus) === 1).map(i => <option key={String(i.name)} value={String(i.name)}>{String(i.name)} · {String(i.supplier)}</option>)}</select></Field><Field label="Snapshot distinti delle sedute" required><select multiple size={Math.min(7, Math.max(3, expectations.length))} value={selected} onChange={e => setSelected(Array.from(e.target.selectedOptions, o => o.value))} required>{expectations.map(x => <option key={String(x.name)} value={String(x.name)}>{String(x.appointment_label ?? x.appointment)} · {String(x.practitioner)} · {String(x.state)}</option>)}</select></Field><p className="scope-note">Seleziona uno o più snapshot con Ctrl o ⌘. Il server verifica contesto e importi.</p></>}
    {operation === 'override' && <><Field label="Atteso sospeso corrente" required><select value={expectation} onChange={e => setExpectation(e.target.value)} required><option value="">Seleziona</option>{expectations.filter(x => x.state === 'SUSPENDED').map(x => <option key={String(x.name)} value={String(x.name)}>{String(x.appointment_label ?? x.appointment)} · {String(x.name)}</option>)}</select></Field><p className="scope-note">I fatti originari restano conservati nell'audit.</p></>}
    {operation === 'reevaluate' && <p className="scope-note">Rivaluta gli attesi del centro secondo le regole e i pagamenti correnti.</p>}
    <Field label="Motivo" required><textarea value={reason} onChange={e => setReason(e.target.value)} required maxLength={2000} /></Field><FormError error={loadError || error} /><div className="form-actions"><Button type="button" variant="secondary" onClick={() => setOpen(false)}>Annulla</Button><Button type="submit" disabled={busy || !!loadError || (operation === 'compare' && selected.length === 0)}>{busy ? 'Salvataggio…' : 'Conferma'}</Button></div>
  </form></Modal>}</>
}
