import { useEffect, useRef, useState } from 'react'
import { type Row, call, finance, requestKey, romeToday, money } from './api'
import { type Feedback, Button, DateInput, Field, FormError, SearchableSelect, useAction } from './ui'

type Props = { row: Row; tab: string; center: string; canWrite: boolean; accounts: Row[]; suppliers: Row[]; items: Row[]; feedback: Feedback; onChange: () => void }
const err = (e: unknown) => e instanceof Error ? e.message : 'Operazione non riuscita.'

export function FinanceActions({ row, tab, center, canWrite, accounts, suppliers, items, feedback, onChange }: Props) {
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
  const [incoming, setIncoming] = useState<Row | null>(null)
  const [lines, setLines] = useState<Row[]>([])
  const [classified, setClassified] = useState<string[]>([])
  const [taxAccount, setTaxAccount] = useState('')
  const [loadError, setLoadError] = useState('')
  const keys = useRef<Record<string, string>>({})
  const { busy, error, run } = useAction(feedback, onChange)

  useEffect(() => {
    let live = true
    const name = String(row.name ?? '')
    const task = tab === 'Banca' ? finance<Row>('banking.candidates', { name }) : ['SdI', 'TS'].includes(tab) ? finance<Row>('fiscal.status', { name }) : null
    if (task) task.then(r => { if (!live) return; setDetail(r); setCandidates(Array.isArray(r.invoices) ? r.invoices as Row[] : []) }).catch(e => { if (live) setLoadError(err(e)) })
    if (tab === 'XML ricevuti' && row.state === 'Needs Classification') {
      call<Row>('frappe.client.get', { doctype: 'CC Incoming Invoice', name }).then(doc => {
        if (!live) return
        const parsed = JSON.parse(String(doc.lines_json ?? '[]'))
        if (!Array.isArray(parsed) || !parsed.length || parsed.some(line => !line || typeof line !== 'object')) throw new Error('Righe XML non disponibili per la classificazione.')
        setIncoming(doc); setLines(parsed); setClassified(parsed.map(() => ''))
      }).catch(e => { if (live) setLoadError(err(e)) })
    }
    return () => { live = false }
  }, [row, tab])

  if (!canWrite) return null
  const docstatus = Number(row.docstatus)
  const invoiceDomain = tab === 'Fatture pazienti' ? 'receivables' : tab === 'Fatture fornitori' ? 'incoming' : ''
  const actions = invoiceDomain ? docstatus === 0 ? [['submit', 'Approva e contabilizza']] : docstatus === 1 ? [['pay', 'Registra pagamento'], ['cancel', 'Annulla documento'], ...(invoiceDomain === 'receivables' ? [['credit', 'Nota di credito']] : [])] : docstatus === 2 ? [['amend', 'Rettifica e riemetti']] : []
    : tab === 'Banca' && Number(row.docstatus) === 1 ? [['reconcile', 'Riconcilia con fattura'], ['cancel', 'Annulla movimento']] : tab === 'XML ricevuti' && !row.purchase_invoice ? [...(row.state !== 'Needs Classification' ? [['bind_supplier', 'Collega fornitore']] : []), ...(row.state === 'Needs Classification' ? [['draft', 'Classifica e prepara']] : [])] : ['SdI', 'TS'].includes(tab) && row.direction === 'OUTBOUND' && (tab === 'TS' ? ['READY', 'RETRY_REQUIRED'] : ['PREPARED', 'FAILED_RETRYABLE']).includes(String(detail?.status ?? row.status)) ? [['queue', 'Simula tentativo']] : []
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
      method = choice === 'draft' ? 'incoming.draft' : 'incoming.bind_supplier'
      if (choice === 'draft') args = { ...args, items: classified, expense_account: expenseAccount, tax_account: taxAccount || null, posting_date: date, due_date: due }
      else args.supplier = supplier
    } else {
      method = `${tab === 'SdI' ? 'sdi' : 'ts'}.queue`
      args = { ...args, outcome }
    }
    const key = `${method}:${JSON.stringify(args)}`
    if (['pay', 'credit', 'amend', 'draft'].includes(choice)) args.request_key = keys.current[key] ??= requestKey()
    if (choice === 'queue') args.attempt_key = keys.current[key] ??= requestKey()
    await run(() => finance(method, args, true), 'Operazione finanziaria registrata.')
  }
  return <section className="finance-actions"><h3>Azioni autorizzate</h3>{loadError && <p className="inline-error">{loadError}</p>}{Boolean(detail?.state) && tab === 'Banca' && <p>Stato confronto: {String(detail?.state)}</p>}{Boolean(detail?.attempts) && ['SdI', 'TS'].includes(tab) && <p>Tentativi precedenti: {(detail?.attempts as Row[]).length}. Solo simulazione, nessun invio reale.</p>}{!actions.length ? <p>Nessuna azione disponibile nello stato attuale.</p> : <><div className="action-grid">{actions.map(([id, label]) => <Button type="button" key={id} variant={choice === id ? 'primary' : 'secondary'} onClick={() => setChoice(id)}>{label}</Button>)}</div>{choice && <form onSubmit={e => { e.preventDefault(); void submit() }}>
    {choice === 'pay' && <Field label="Importo" required><input type="number" step="0.01" min="0.01" value={amount} onChange={e => setAmount(e.target.value)} required /></Field>}
    {['pay', 'credit', 'amend'].includes(choice) && <Field label="Data registrazione" required><DateInput value={date} onChange={setDate} required /></Field>}
    {choice === 'amend' && <Field label="Scadenza" required><DateInput value={due} onChange={setDue} required /></Field>}
    {choice === 'amend' && invoiceDomain === 'incoming' && <SearchableSelect label="Conto costo" options={accounts.filter(a => a.root_type === 'Expense' && !a.is_group && !a.disabled).map(a => ({ value: String(a.name), label: String(a.name) }))} value={expenseAccount} onChange={setExpenseAccount} required />}
    {choice === 'reconcile' && <SearchableSelect label="Fattura compatibile" options={candidates.map(c => ({ value: String(c.name), label: `${String(c.name)} · residuo ${money(c.outstanding_amount)}` }))} value={invoice} onChange={setInvoice} required />}
    {choice === 'bind_supplier' && <SearchableSelect label="Fornitore" options={suppliers.map(s => ({ value: String(s.name), label: String(s.supplier_name ?? s.name) }))} value={supplier} onChange={setSupplier} required />}
    {choice === 'draft' && <><p className="scope-note">Classifica ogni riga dell'XML conservato. La bozza resta soggetta ai controlli del server.</p>{lines.map((line, index) => <SearchableSelect key={index} label={`Voce ${index + 1}: ${String(line.description ?? 'senza descrizione').slice(0, 90)} · ${String(line.qty ?? '—')} × ${money(line.rate)}`} options={items.filter(i => i.is_purchase_item && !i.disabled && !i.is_stock_item).map(i => ({ value: String(i.name), label: String(i.item_name ?? i.name) }))} value={classified[index] ?? ''} onChange={value => setClassified(current => current.map((item, i) => i === index ? value : item))} required />)}<SearchableSelect label="Conto costo" options={accounts.filter(a => a.root_type === 'Expense' && !a.is_group && !a.disabled).map(a => ({ value: String(a.name), label: String(a.name) }))} value={expenseAccount} onChange={setExpenseAccount} required />{Number(incoming?.tax_total ?? 0) > 0 && <SearchableSelect label="Conto IVA" options={accounts.filter(a => a.account_type === 'Tax' && !a.is_group && !a.disabled).map(a => ({ value: String(a.name), label: String(a.name) }))} value={taxAccount} onChange={setTaxAccount} required />}<div className="form-grid"><Field label="Data registrazione" required><DateInput value={date} onChange={setDate} required /></Field><Field label="Scadenza" required><DateInput value={due} onChange={setDue} required /></Field></div></>}
    {choice === 'queue' && <Field label="Esito simulato" required><select value={outcome} onChange={e => setOutcome(e.target.value)}><option>Accepted</option><option>Rejected</option><option>Retryable Failure</option><option>Terminal Failure</option>{tab === 'TS' && <option>Correction Required</option>}</select></Field>}
    <Field label="Motivo" required><textarea value={reason} onChange={e => setReason(e.target.value)} required maxLength={2000} /></Field><FormError error={error} /><Button disabled={busy || !!loadError || (choice === 'reconcile' && !invoice) || (choice === 'draft' && (!lines.length || classified.some(x => !x) || !incoming))} type="submit">{busy ? 'Salvataggio…' : 'Conferma operazione'}</Button>
  </form>}</>}</section>
}
