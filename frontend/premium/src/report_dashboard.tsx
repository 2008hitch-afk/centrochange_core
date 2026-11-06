import {useEffect, useMemo, useState} from 'react'
import {type Boot, type FinanceBoot, type Row, finance, ops, romeToday, money, displayDate} from './api'
import {Button, DataTable, DateInput, Empty, Field, Heading, Metric, type Feedback} from './ui'
import {practitionerName} from './display_names'
import {FinanceReportsPage} from './finance_reports'

type Props = {boot: Boot; financeBoot?: FinanceBoot | null; center: string; feedback: Feedback; financeOnly?: boolean}
const states = ['Tutti', 'Saldata', 'Parziale', 'Da incassare', 'Non dovuto', 'Da definire', 'In programma']
export function ReportDashboard({boot, financeBoot, center, feedback, financeOnly = false}: Props) {
  const manager = Boolean(boot.is_manager || boot.roles.includes('CC Manager'))
  const [view, setView] = useState<'professional' | 'customer'>(financeOnly ? 'customer' : 'professional')
  const [practitioner, setPractitioner] = useState('')
  const [payment, setPayment] = useState('Tutti')
  const [start, setStart] = useState(romeToday().slice(0, 8) + '01')
  const [end, setEnd] = useState(romeToday())
  const [startValid, setStartValid] = useState(true)
  const [endValid, setEndValid] = useState(true)
  const [result, setResult] = useState<Row | null>(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const valid = Boolean(startValid && endValid && start && end && start <= end && (Date.parse(end)-Date.parse(start)) <= 93*86400000)
  useEffect(() => {
    if (view !== 'professional' || !center || !valid) {setResult(null); return}
    let live = true
    setError(''); setResult(null); setLoading(true)
    const request = manager ? finance<Row>('report_dashboard.professional', {center,start,end,practitioner,payment_state:payment}) : ops<Row>('reporting.sessions', {center,start,end,practitioner:practitioner || undefined, page:1,page_length:1000})
    request.then(value => {if (!manager && Number(value.total ?? 0) > 1000) throw new Error('Riduci il periodo per visualizzare tutti i risultati.'); if (live) {setResult(value); setLoading(false)}}).catch(e => {if (live) {setError(e instanceof Error ? e.message : 'Report non disponibile'); setLoading(false)}})
    return () => {live = false}
  }, [view,center,start,end,practitioner,payment,valid,manager])
  const rows = (result?.appointments as Row[] | undefined) ?? []
  const metrics = useMemo(() => {
    const count = (state: string) => rows.filter(row => (row.operational_payment as Row | undefined)?.state === state).length
    return {performed: rows.filter(row => Boolean(row.cc_performed) && row.status !== 'Cancelled').length, pending:rows.filter(row => Boolean(row.cc_classified_to_close)).length, paid:count('Saldata'),partial:count('Parziale'),due:count('Da incassare')}
  }, [rows])
  const csv = '/api/method/centrochange_core.finance.report_dashboard.professional_export?' + new URLSearchParams({center,start,end,practitioner,payment_state:payment})
  const charts = [{title:'Sedute per stato esito',items:[{label:'Svolte',n:metrics.performed},{label:'Esito da registrare',n:metrics.pending}]}, ...(manager ? [{title:'Sedute per stato pagamento',items:[{label:'Saldata',n:metrics.paid},{label:'Parziale',n:metrics.partial},{label:'Da incassare',n:metrics.due}]}] : [])]
  return <>
    <Heading title={view === 'professional' ? 'Report professionista' : 'Report cliente'} subtitle="Sedute, esiti e pagamenti nel periodo selezionato." action={<div className="button-group">{!financeOnly && <Button variant={view==='professional'?'primary':'secondary'} onClick={() => setView('professional')}>Report professionista</Button>}{financeBoot && <Button variant={view==='customer'?'primary':'secondary'} onClick={() => setView('customer')}>Report cliente</Button>}{view==='professional' && manager && <a className="button secondary" href={valid && result && !loading && !error ? csv : undefined} aria-disabled={!valid || !result || loading || !!error}>Esporta CSV</a>}</div>} />
    <section className="panel report-approved-filters"><div className="form-grid">
      {view==='professional' && <Field label="Professionista"><select value={practitioner} onChange={e=>setPractitioner(e.target.value)}><option value="">Tutti i professionisti</option>{boot.practitioners.map(p=><option value={p.name} key={p.name}>{practitionerName(p)}</option>)}</select></Field>}
      <Field label="Dal"><DateInput value={start} onChange={setStart} onValidityChange={setStartValid} calendarLabel="data iniziale" required /></Field><Field label="Al"><DateInput value={end} onChange={setEnd} onValidityChange={setEndValid} calendarLabel="data finale" required /></Field>
      {view==='professional' && manager && <Field label="Stato pagamento"><select value={payment} onChange={e=>setPayment(e.target.value)}>{states.map(s=><option key={s}>{s}</option>)}</select></Field>}
    </div>{!valid && <p className="inline-error" role="alert">Inserisci un periodo valido di massimo 93 giorni.</p>}</section>
    {view==='customer' && financeBoot ? <FinanceReportsPage boot={financeBoot} generalBoot={boot} center={center} start={start} end={end} feedback={feedback} initialMode="customers" dashboard /> : <>
      {loading && <p role="status">Caricamento report…</p>}{error && <p role="alert" className="inline-error">{error}</p>}
      {result && <><div className="metrics-grid report-approved-metrics"><Metric label="Sedute totali" value={String(rows.length)} /><Metric label="Sedute svolte" value={String(metrics.performed)} tone="green"/><Metric label="Esiti da registrare" value={String(metrics.pending)} tone="amber"/>{manager && <><Metric label="Sedute saldate" value={String(metrics.paid)} tone="green"/><Metric label="Pagamenti parziali" value={String(metrics.partial)} tone="blue"/><Metric label="Da incassare" value={result.remaining_cents == null ? 'Da verificare' : money(Number(result.remaining_cents)/100)} tone="amber"/><Metric label="Incassato nel periodo" value={money(Number(result.cash_cents)/100)} tone="green"/></>}</div>
      <div className="report-approved-charts">{charts.map(chart=><section className="panel customer-status-chart" key={chart.title}><h2>{chart.title}</h2>{chart.items.every(x=>!x.n)?<p>Nessun dato nel periodo.</p>:<>{chart.title === "Sedute per stato esito" && <div className="report-donut" aria-hidden="true" style={{background:`conic-gradient(#21a262 0 ${Math.round(100*metrics.performed/Math.max(1,rows.length))}%, #f6b74b 0 ${Math.round(100*(metrics.performed+metrics.pending)/Math.max(1,rows.length))}%, #e7edf5 0)`}}><span>{rows.length}<small>Sedute</small></span></div>}{chart.items.map(item=><div className="customer-chart-row" key={item.label}><span>{item.label}</span><div className="customer-chart-track"><span style={{width:`${Math.round(100*item.n/Math.max(1, rows.length))}%`}} /></div><strong>{item.n}</strong></div>)}</>}</section>)}</div>
      <section className="panel report-approved-table"><h2>Dettaglio sedute</h2>{rows.length===0?<Empty title="Nessuna seduta nel periodo"/>:<DataTable rows={rows} columns={[{key:'appointment_date',label:'Data',render:displayDate},{key:'appointment_time',label:'Ora'},{key:'patient_name',label:'Paziente'},{key:'practitioner_name',label:'Professionista'},{key:'cc_service_label',label:'Servizio'},{key:'status',label:'Esito',render:(v,r)=>r.cc_performed?'Svolta':v==='Cancelled'?'Annullata':r.cc_closure_state==='Closed'?'Non svolta':r.cc_classified_to_close?'Esito da registrare':'In programma'},...(manager?[{key:'operational_payment',label:'Pagamento',render:(v:unknown)=>String((v as Row)?.state ?? 'Da verificare')},{key:'cc_price_snapshot',label:'Tariffa',render:(v:unknown)=>v==null?'—':money(v)}]:[])]}/>}</section></>}
    </>}
  </>
}
