import { useEffect, useRef, useState } from 'react'
import { type Row, finance, requestKey, romeToday } from './api'
import { type Feedback, Button, DateInput, Field, FormError, Modal, SearchableSelect, useAction } from './ui'

type Props = { tab: string; center: string; feedback: Feedback; onClose: () => void; onSuccess: () => void; start: string; end: string }
const asError = (e: unknown) => e instanceof Error ? e.message : 'Caricamento non riuscito.'

export function FinanceCreate({ tab, center, feedback, onClose, onSuccess, start, end }: Props) {
  const [choices, setChoices] = useState<Row[]>([])
  const [secondary, setSecondary] = useState<Row[]>([])
  const [selected, setSelected] = useState('')
  const [second, setSecond] = useState('')
  const [date, setDate] = useState(romeToday())
  const [due, setDue] = useState(romeToday())
  const [reason, setReason] = useState('')
  const [file, setFile] = useState<File | null>(null)
  const [externalId, setExternalId] = useState('')
  const [deposit, setDeposit] = useState('0')
  const [withdrawal, setWithdrawal] = useState('0')
  const [reference, setReference] = useState('')
  const [description, setDescription] = useState('')
  const [loadError, setLoadError] = useState('')
  const keys = useRef<Record<string, string>>({})
  const { busy, error, run } = useAction(feedback, onSuccess)
  const keyFor = (payload: Row) => { const k = `${tab}:${JSON.stringify(payload)}`; return keys.current[k] ??= requestKey() }

  useEffect(() => {
    let live = true
    let task: Promise<unknown> = Promise.resolve([])
    if (tab === 'Fatture pazienti') task = finance<{ candidates: Row[] }>('receivables.candidates', { center, from_date: start, to_date: end }).then(x => x.candidates)
    if (tab === 'SdI' || tab === 'TS') task = finance<Row[]>('reporting.records', { center, doctype: tab === 'SdI' ? 'Sales Invoice' : 'CC Economic Source Link' })
    task.then(x => { if (live) setChoices(Array.isArray(x) ? x : []) }).catch(e => { if (live) setLoadError(asError(e)) })
    if (tab === 'TS') finance<Row[]>('reporting.records', { center, doctype: 'Sales Invoice' }).then(x => { if (live) setSecondary(x.filter(r => Number(r.docstatus) === 1)) }).catch(e => { if (live) setLoadError(asError(e)) })
    return () => { live = false }
  }, [tab, center, start, end])

  const submit = () => {
    if (tab === 'Fatture pazienti') {
      const base = { appointment: selected, reason }
      void run(async () => {
        const source = await finance<{ name: string }>('bridge.capture', base, true)
        const payload = { sources: [source.name], posting_date: date, due_date: due, reason }
        return finance('receivables.draft', { ...payload, request_key: keyFor(payload) }, true)
      }, 'Bozza fattura creata.')
    } else if (tab === 'XML ricevuti') {
      void run(async () => {
        if (!file || file.size > 1048576) throw new Error('Seleziona un XML sintetico entro 1 MB.')
        return finance('incoming.intake', { center, xml: await file.text(), reason }, true)
      }, 'XML sintetico registrato.')
    } else if (tab === 'Banca') {
      void run(() => finance('banking.import_movements', { center, movements: [{ external_id: externalId, date, deposit, withdrawal, reference, description }], reason }, true), 'Movimento sintetico importato.')
    } else if (tab === 'SdI') {
      const payload = { invoice: selected, reason }
      void run(() => finance('sdi.prepare', { ...payload, request_key: keyFor(payload) }, true), 'Bozza SdI simulata preparata.')
    } else if (tab === 'TS') {
      const payload = { source: selected, invoice: second, reason }
      void run(() => finance('ts.prepare', { ...payload, request_key: keyFor(payload) }, true), 'Bozza TS simulata preparata.')
    } else if (tab === 'Coda amministrativa') {
      void run(() => finance('admin_queue.refresh', { center, reason }, true), 'Condizioni amministrative aggiornate.')
    }
  }
  const title = ({ 'Fatture pazienti': 'Crea fattura paziente', 'XML ricevuti': 'Importa XML sintetico', Banca: 'Importa movimento', SdI: 'Prepara SdI simulato', TS: 'Prepara TS simulato', 'Coda amministrativa': 'Rileva condizioni' } as Record<string, string>)[tab] ?? 'Nuova operazione'
  return <Modal title={title} onClose={onClose}><form onSubmit={e => { e.preventDefault(); submit() }}>
    {loadError && <p className="inline-error">{loadError}</p>}
    {['Fatture pazienti', 'SdI', 'TS'].includes(tab) && <SearchableSelect label={tab === 'Fatture pazienti' ? 'Seduta da fatturare' : tab === 'SdI' ? 'Fattura contabilizzata' : 'Fonte economica'} options={choices.filter(r => tab !== 'SdI' || Number(r.docstatus) === 1).map(r => ({ value: String(r.name), label: String(r.name) }))} value={selected} onChange={setSelected} required />}
    {tab === 'TS' && <SearchableSelect label="Fattura della fonte" options={secondary.map(r => ({ value: String(r.name), label: String(r.name) }))} value={second} onChange={setSecond} required />}
    {tab === 'XML ricevuti' && <Field label="File XML sintetico" required><input type="file" accept=".xml,text/xml,application/xml" onChange={e => setFile(e.target.files?.[0] ?? null)} required /></Field>}
    {tab === 'Banca' && <><Field label="Identificativo estratto" required><input value={externalId} onChange={e => setExternalId(e.target.value)} maxLength={160} required /></Field><div className="form-grid"><Field label="Entrata EUR"><input type="number" step="0.01" min="0" value={deposit} onChange={e => setDeposit(e.target.value)} /></Field><Field label="Uscita EUR"><input type="number" step="0.01" min="0" value={withdrawal} onChange={e => setWithdrawal(e.target.value)} /></Field></div><Field label="Riferimento"><input value={reference} onChange={e => setReference(e.target.value)} /></Field><Field label="Descrizione" required><input value={description} onChange={e => setDescription(e.target.value)} required /></Field></>}
    {['Fatture pazienti', 'Banca'].includes(tab) && <Field label="Data" required><DateInput value={date} onChange={setDate} required /></Field>}
    {tab === 'Fatture pazienti' && <Field label="Scadenza" required><DateInput value={due} onChange={setDue} required /></Field>}
    {['SdI', 'TS'].includes(tab) && <p className="scope-note">Solo processo sintetico. Nessun invio a provider reali.</p>}
    <Field label="Motivo" required><textarea value={reason} onChange={e => setReason(e.target.value)} required maxLength={2000} /></Field><FormError error={error} /><div className="form-actions"><Button type="button" variant="secondary" onClick={onClose}>Annulla</Button><Button disabled={busy || !!loadError} type="submit">{busy ? 'Salvataggio…' : 'Conferma'}</Button></div>
  </form></Modal>
}
