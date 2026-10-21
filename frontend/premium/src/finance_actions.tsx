import { useEffect, useRef, useState } from 'react'
import { type Row, finance, requestKey, romeToday, money } from './api'
import { type Feedback, Button, DateInput, Field, FormError, useAction } from './ui'

type Props = { row: Row; tab: string; center: string; canWrite: boolean; accounts: Row[]; suppliers: Row[]; feedback: Feedback; onChange: () => void }
const err = (e: unknown) => e instanceof Error ? e.message : 'Operazione non riuscita.'

export function FinanceActions({ row, tab, center, canWrite, accounts, suppliers, feedback, onChange }: Props) {
  const [choice, setChoice] = useState('')
  const [reason, setReason] = useState('')
  const [date, setDate] = useState(romeToday())
  const [due, setDue] = useState(romeToday())
  const [amount, setAmount] = useState(String(row.outstanding_amount ?? ''))
  const [invoice, setInvoice] = useState('')
  const [outcome, setOutcome] = useState('Accepted')
  const [expenseAccount, setExpenseAccount] = useState('')
  const [supplier, setSupplier] = useState('')
  const [candidates, setCandidates] = useState<Row[]>([])
  const [detail, setDetail] = useState<Row | null>(null)
  const [loadError, setLoadError] = useState('')
  const keys = useRef<Record<string, string>>({})
  const { busy, error, run } = useAction(feedback, onChange)

  useEffect(() => {
    let live = true
    const name = String(row.name ?? '')
    const task = tab === 'Banca' ? finance<Row>('banking.candidates', { name }) : ['SdI', 'TS'].includes(tab) ? finance<Row>('fiscal.status', { name }) : null
    if (task) task.then(r => { if (!live) return; setDetail(r); setCandidates(Array.isArray(r.invoices) ? r.invoices as Row[] : []) }).catch(e => { if (live) setLoadError(err(e)) })
    return () => { live = false }
  }, [row, tab])

  if (!canWrite) return null
  const docstatus = Number(row.docstatus)
  const invoiceDomain = tab === 'Fatture pazienti' ? 'receivables' : tab === 'Fatture fornitori' ? 'incoming' : ''
  const actions = invoiceDomain ? docstatus === 0 ? [['submit', 'Approva e contabilizza']] : docstatus === 1 ? [['pay', 'Registra pagamento'], ['cancel', 'Annulla documento'], ...(invoiceDomain === 'receivables' ? [['credit', 'Nota di credito']] : [])] : docstatus === 2 ? [['amend', 'Rettifica e riemetti']] : []
    : tab === 'Banca' && Number(row.docstatus) === 1 ? [['reconcile', 'Riconcilia con fattura'], ['cancel', 'Annulla movimento']] : tab === 'XML ricevuti' && !row.purchase_invoice ? [['bind_supplier', 'Collega fornitore']] : ['SdI', 'TS'].includes(tab) && row.direction === 'OUTBOUND' && (tab === 'TS' ? ['READY', 'RETRY_REQUIRED'] : ['PREPARED', 'FAILED_RETRYABLE']).includes(String(detail?.status ?? row.status)) ? [['queue', 'Simula tentativo']] : []
  const submit = async () => {
    if (!choice) return
    const name = String(row.name)
    let method = ''
    let args: Row = { name, reason }
    if (invoiceDomain) {
      method = `${invoiceDomain}.${choice}`
      if (choice === 'pay') args = { ...args, amount, posting_date: date }
      if (choice === 'credit') args = { ...args, posting_date: date }
      if (choice === 'amend') args = { ...args, posting_date: date, due_date: due, ...(invoiceDomain === 'incoming' ? { expense_account: expenseAccount } : {}) }
    } else if (tab === 'Banca') {
      method = `banking.${choice}`
      if (choice === 'reconcile') args.invoice = invoice
    } else if (tab === 'XML ricevuti') {
      method = 'incoming.bind_supplier'
      args.supplier = supplier
    } else {
      method = `${tab === 'SdI' ? 'sdi' : 'ts'}.queue`
      args = { ...args, outcome }
    }
    const key = `${method}:${JSON.stringify(args)}`
    if (['pay', 'credit', 'amend'].includes(choice)) args.request_key = keys.current[key] ??= requestKey()
    if (choice === 'queue') args.attempt_key = keys.current[key] ??= requestKey()
    await run(() => finance(method, args, true), 'Operazione finanziaria registrata.')
  }
  return <section className="finance-actions"><h3>Azioni autorizzate</h3>{loadError && <p className="inline-error">{loadError}</p>}{Boolean(detail?.state) && tab === 'Banca' && <p>Stato confronto: {String(detail?.state)}</p>}{Boolean(detail?.attempts) && ['SdI', 'TS'].includes(tab) && <p>Tentativi precedenti: {(detail?.attempts as Row[]).length}. Solo simulazione, nessun invio reale.</p>}{!actions.length ? <p>Nessuna azione disponibile nello stato attuale.</p> : <><div className="action-grid">{actions.map(([id, label]) => <Button type="button" key={id} variant={choice === id ? 'primary' : 'secondary'} onClick={() => setChoice(id)}>{label}</Button>)}</div>{choice && <form onSubmit={e => { e.preventDefault(); void submit() }}>
    {choice === 'pay' && <Field label="Importo" required><input type="number" step="0.01" min="0.01" value={amount} onChange={e => setAmount(e.target.value)} required /></Field>}
    {['pay', 'credit', 'amend'].includes(choice) && <Field label="Data registrazione" required><DateInput value={date} onChange={setDate} required /></Field>}
    {choice === 'amend' && <Field label="Scadenza" required><DateInput value={due} onChange={setDue} required /></Field>}
    {choice === 'amend' && invoiceDomain === 'incoming' && <Field label="Conto costo" required><select value={expenseAccount} onChange={e => setExpenseAccount(e.target.value)} required><option value="">Seleziona</option>{accounts.filter(a => a.root_type === 'Expense' && !a.is_group && !a.disabled).map(a => <option key={String(a.name)} value={String(a.name)}>{String(a.name)}</option>)}</select></Field>}
    {choice === 'reconcile' && <Field label="Fattura compatibile" required><select value={invoice} onChange={e => setInvoice(e.target.value)} required><option value="">Seleziona</option>{candidates.map(c => <option key={String(c.name)} value={String(c.name)}>{String(c.name)} · residuo {money(c.outstanding_amount)}</option>)}</select></Field>}
    {choice === 'bind_supplier' && <Field label="Fornitore" required><select value={supplier} onChange={e => setSupplier(e.target.value)} required><option value="">Seleziona</option>{suppliers.map(s => <option key={String(s.name)} value={String(s.name)}>{String(s.supplier_name ?? s.name)}</option>)}</select></Field>}
    {choice === 'queue' && <Field label="Esito simulato" required><select value={outcome} onChange={e => setOutcome(e.target.value)}><option>Accepted</option><option>Rejected</option><option>Retryable Failure</option><option>Terminal Failure</option>{tab === 'TS' && <option>Correction Required</option>}</select></Field>}
    <Field label="Motivo" required><textarea value={reason} onChange={e => setReason(e.target.value)} required maxLength={2000} /></Field><FormError error={error} /><Button disabled={busy || (choice === 'reconcile' && !invoice)} type="submit">{busy ? 'Salvataggio…' : 'Conferma operazione'}</Button>
  </form>}</>}</section>
}
