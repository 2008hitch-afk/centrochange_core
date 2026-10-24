import { useEffect, useState } from 'react'
import { type Boot, type Row, call } from './api'
import { practitionerName, practitionerNameFor } from './display_names'
import { type Feedback, Button, Chip, Field, FormError, SearchableSelect, useAction } from './ui'

export function PatientAssignments({ boot, patient, center, feedback, onSuccess }: { boot: Boot; patient: string; center: string; feedback: Feedback; onSuccess: () => void }) {
  const [rows, setRows] = useState<Row[]>([])
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState('')
  const [reload, setReload] = useState(0)
  const [mode, setMode] = useState<'assign' | 'reassign' | null>(null)
  const [practitioner, setPractitioner] = useState('')
  const [next, setNext] = useState('')
  const [active, setActive] = useState('1')
  const [reason, setReason] = useState('')
  const canManage = boot.roles.some(r => r === 'CC Manager' || r === 'CC Secretariat')
  const { busy, error, run } = useAction(feedback, () => { setMode(null); setReload(n => n + 1); onSuccess() })
  useEffect(() => {
    let live = true
    setLoading(true); setLoadError('')
    call<Row[]>('frappe.client.get_list', { doctype: 'CC Patient Assignment', fields: ['name', 'patient', 'center', 'practitioner', 'active'], filters: { patient, center }, limit_page_length: 100 })
      .then(data => { if (live) { setRows(data); setLoading(false) } })
      .catch(e => { if (live) { setLoadError(e instanceof Error ? e.message : 'Assegnazioni non disponibili.'); setLoading(false) } })
    return () => { live = false }
  }, [patient, center, reload])
  const assigned = rows.filter(r => Boolean(r.active) && Boolean(r.practitioner))
  const inactive = rows.filter(r => !Boolean(r.active) && Boolean(r.practitioner))
  const choices = mode === 'reassign' ? assigned.map(r => String(r.practitioner)) : boot.practitioners.map(p => p.name)
  const submit = () => {
    if (!practitioner || !reason.trim()) return
    if (mode === 'reassign' && (!next || next === practitioner)) return
    if (mode === 'reassign') return run(() => call('security.lifecycle.reassign', { patient, center, old_practitioner: practitioner, new_practitioner: next, reason }, true), 'Assegnazione aggiornata.')
    return run(() => call('security.lifecycle.set_assignment', { patient, center, practitioner, active, reason }, true), 'Assegnazione registrata.')
  }
  return <section className="detail-section"><h3>Professionisti assegnati</h3>
    {loadError && <p className="inline-error" role="alert">{loadError}</p>}
    {loading ? <p>Caricamento assegnazioni…</p> : assigned.length ? assigned.map(r => <p key={String(r.name)}><Chip tone="good">Attivo</Chip> {practitionerNameFor(String(r.practitioner), boot.practitioners)}</p>) : <p>Nessun professionista assegnato visibile.</p>}
    {!loading && inactive.length > 0 && <details><summary>Assegnazioni non attive ({inactive.length})</summary>{inactive.map(row => <p key={String(row.name)}><Chip tone="warn">Non attivo</Chip> {practitionerNameFor(String(row.practitioner), boot.practitioners)}</p>)}</details>}
    {canManage && <div className="action-grid"><Button variant="secondary" type="button" onClick={() => { setMode('assign'); setPractitioner(''); setActive('1') }}>Gestisci assegnazione</Button>{assigned.length > 0 && <Button variant="secondary" type="button" onClick={() => { setMode('reassign'); setPractitioner(''); setNext('') }}>Riassegna</Button>}</div>}
    {mode && <form className="action-form" onSubmit={e => { e.preventDefault(); void submit() }}><h3>{mode === 'reassign' ? 'Riassegna professionista' : 'Gestisci assegnazione'}</h3>
      <SearchableSelect label={mode === 'reassign' ? 'Professionista attuale' : 'Professionista'} options={choices.map(name => ({ value: name, label: practitionerNameFor(name, boot.practitioners) }))} value={practitioner} onChange={value => { setPractitioner(value); setNext('') }} required />
      {mode === 'reassign' ? <SearchableSelect label="Nuovo professionista" options={boot.practitioners.filter(p => p.name !== practitioner).map(p => ({ value: p.name, label: practitionerName(p) }))} value={next} onChange={setNext} required /> : <Field label="Stato" required><select value={active} onChange={e => setActive(e.target.value)}><option value="1">Attivo</option><option value="0">Disattivo</option></select></Field>}
      <Field label="Motivo" required><textarea value={reason} onChange={e => setReason(e.target.value)} maxLength={2000} required /></Field><FormError error={error} /><div className="form-actions"><Button variant="secondary" type="button" onClick={() => setMode(null)}>Annulla</Button><Button type="submit" disabled={busy || !practitioner || (mode === 'reassign' && (!next || practitioner === next))}>{busy ? 'Salvataggio…' : 'Conferma'}</Button></div>
    </form>}
  </section>
}
