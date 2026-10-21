import { useEffect, useRef, useState } from 'react'
import { type Boot, type Row, call, ops, requestKey } from './api'
import { demoText } from './demo_labels'
import { type Feedback, Button, DateInput, Field, FormError, SearchableSelect, useAction } from './ui'

export function PatientPackages({ boot, patient, center, packages, feedback, onSuccess }: { boot: Boot; patient: string; center: string; packages: Row[]; feedback: Feedback; onSuccess: () => void }) {
  const [templates, setTemplates] = useState<Row[]>([])
  const [loadError, setLoadError] = useState('')
  const [mode, setMode] = useState<'issue' | 'adjust' | null>(null)
  const [template, setTemplate] = useState('')
  const [practitioner, setPractitioner] = useState('')
  const [validUntil, setValidUntil] = useState('')
  const [packageName, setPackageName] = useState('')
  const [units, setUnits] = useState('')
  const [reason, setReason] = useState('')
  const keys = useRef<Record<string, string>>({})
  const canManage = boot.roles.some(r => r === 'CC Manager' || r === 'CC Secretariat')
  const { busy, error, run } = useAction(feedback, () => { setMode(null); onSuccess() })
  useEffect(() => {
    if (!mode || !canManage) return
    let live = true
    call<Row[]>('frappe.client.get_list', { doctype: 'CC Package Template', fields: ['name', 'title', 'service_item', 'units', 'enabled'], filters: { enabled: 1 }, limit_page_length: 100 })
      .then(rows => { if (live) { setTemplates(rows); setLoadError('') } })
      .catch(e => { if (live) setLoadError(e instanceof Error ? e.message : 'Catalogo pacchetti non disponibile.') })
    return () => { live = false }
  }, [mode, canManage])
  const submit = () => {
    const payload: Row = mode === 'issue'
      ? { template, patient, centers: [center], practitioner: practitioner || null, valid_until: validUntil || null, reason }
      : { package: packageName, units, reason }
    const id = JSON.stringify(payload)
    payload.request_key = keys.current[id] ??= requestKey()
    return run(() => ops(mode === 'issue' ? 'packages.issue' : 'packages.adjust', payload, true), mode === 'issue' ? 'Pacchetto emesso.' : 'Saldo pacchetto rettificato.')
  }
  return <section className="detail-section"><h3>Pacchetti</h3>
    {packages.length ? packages.map(p => <article className="note" key={String(p.name)}><strong>{demoText(p.label ?? p.name)}</strong><small>Disponibili: {String(p.available ?? '—')} · Riservate: {String(p.reserved ?? '—')} · Residue: {String(p.remaining ?? '—')}</small></article>) : <p>Nessun pacchetto nel centro selezionato.</p>}
    {canManage && <div className="action-grid"><Button type="button" variant="secondary" onClick={() => { setMode('issue'); setLoadError('') }}>Emetti pacchetto</Button>{packages.length > 0 && <Button type="button" variant="secondary" onClick={() => { setMode('adjust'); setLoadError('') }}>Rettifica saldo</Button>}</div>}
    {mode && <form className="action-form" onSubmit={e => { e.preventDefault(); void submit() }}><h3>{mode === 'issue' ? 'Emetti pacchetto' : 'Rettifica saldo'}</h3>
      {mode === 'issue' ? <><SearchableSelect label="Modello" options={templates.map(t => ({ value: String(t.name), label: `${demoText(t.title)} · ${String(t.units)} sedute` }))} value={template} onChange={setTemplate} required /><SearchableSelect label="Professionista dedicato" options={boot.practitioners.map(p => ({ value: p.name, label: demoText(p.practitioner_name) }))} value={practitioner} onChange={setPractitioner} empty="Nessuno" /><Field label="Valido fino al"><DateInput value={validUntil} onChange={setValidUntil} /></Field><p className="scope-note">Il pacchetto vale nel centro selezionato. Le unità provengono dal modello autorizzato.</p></>
        : <><Field label="Pacchetto" required><select value={packageName} onChange={e => setPackageName(e.target.value)} required><option value="">Seleziona</option>{packages.map(p => <option key={String(p.name)} value={String(p.name)}>{demoText(p.label ?? p.name)} · {String(p.available)} disponibili</option>)}</select></Field><Field label="Variazione unità (+/−)" required><input type="number" step="1" min="-9999" max="9999" value={units} onChange={e => setUnits(e.target.value)} required /></Field></>}
      <Field label="Motivo" required><textarea value={reason} onChange={e => setReason(e.target.value)} maxLength={2000} required /></Field>{loadError && <p className="inline-error" role="alert">{loadError}</p>}<FormError error={error} /><div className="form-actions"><Button variant="secondary" type="button" onClick={() => setMode(null)}>Annulla</Button><Button type="submit" disabled={busy || !!loadError || (mode === 'adjust' && Number(units) === 0)}>{busy ? 'Salvataggio…' : 'Conferma'}</Button></div>
    </form>}
  </section>
}
