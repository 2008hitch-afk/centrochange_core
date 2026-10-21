import { useEffect, useState } from 'react'
import { Download } from 'lucide-react'
import { type FinanceBoot, type Row, displayDate, finance, money } from './api'
import { type Feedback, Button, Chip, DataTable, Drawer, Empty, Field, Metric } from './ui'
import { demoPreferred, demoText } from './demo_labels'

type Props = { boot: FinanceBoot; center: string; start: string; end: string; feedback: Feedback; initialMode?: 'patients' | 'professionals'; buttonLabel?: string }
const url = (method: string, args: Row) => '/api/method/centrochange_core.finance.' + method + '?' + new URLSearchParams(Object.entries(args).map(([k, v]) => [k, String(v ?? '')]))
const errorText = (e: unknown) => e instanceof Error ? e.message : 'Report non disponibile.'

export function FinanceReports({ boot, center, start, end, feedback, initialMode = 'patients', buttonLabel = 'Report dettagliati' }: Props) {
  const [open, setOpen] = useState(false)
  const [mode, setMode] = useState<'patients' | 'professionals'>(initialMode)
  const [groups, setGroups] = useState<Row[]>([])
  const [key, setKey] = useState('')
  const [practitioner, setPractitioner] = useState('')
  const [detail, setDetail] = useState<Row | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  useEffect(() => { setKey(''); setPractitioner(''); setGroups([]); setDetail(null) }, [center])
  useEffect(() => {
    if (!open || mode !== 'patients') return
    let live = true
    setLoading(true); setError(''); setDetail(null)
    finance<{ rows: Row[] }>('patient_reporting.patient_view', { center, start, end }).then(r => {
      if (live) { setGroups(r.rows); setLoading(false) }
    }).catch(e => { if (live) { setError(errorText(e)); setLoading(false) } })
    return () => { live = false }
  }, [open, mode, center, start, end])
  useEffect(() => {
    if (!open || mode === 'patients' && !key || mode === 'professionals' && !practitioner) return
    let live = true
    setLoading(true); setError(''); setDetail(null)
    const task = mode === 'patients'
      ? finance<Row>('patient_reporting.patient_view', { center, start, end, key })
      : finance<Row>('reporting.professional_view', { center, start, end, practitioner })
    task.then(r => { if (live) { setDetail(r); setLoading(false) } }).catch(e => { if (live) { setError(errorText(e)); setLoading(false) } })
    return () => { live = false }
  }, [open, mode, center, start, end, key, practitioner])
  const counts = detail?.counts as Row | undefined
  const totals = detail?.totals as Row | undefined
  const economics = detail?.economics as Row | undefined
  const exportHref = mode === 'patients'
    ? url('patient_reporting.patient_export', { center, start, end, ...(key ? { key } : {}) })
    : url('reporting.professional_export', { center, start, end, practitioner })
  return <><Button variant="secondary" onClick={() => { setMode(initialMode); setOpen(true) }}>{buttonLabel}</Button>{open && <Drawer title="Report dettagliati" onClose={() => setOpen(false)}>
    <div className="detail-section"><p>Periodo: {displayDate(start)} – {displayDate(end)} · Centro: {demoText(center)}</p><div className="segmented"><button className={mode === 'patients' ? 'selected' : ''} onClick={() => { setMode('patients'); setDetail(null) }}>Pazienti e soggetti fiscali</button><button className={mode === 'professionals' ? 'selected' : ''} onClick={() => { setMode('professionals'); setDetail(null) }}>Professionisti</button></div></div>
    {mode === 'patients' ? <div className="detail-section"><h3>Soggetti fiscali</h3><p>Una riga per Customer. Nessuna ripartizione inventata tra pazienti con lo stesso soggetto fiscale.</p><DataTable rows={groups} columns={[{ key: 'customer_label', label: 'Soggetto', render: (value, row) => demoPreferred(row.key, value) }, { key: 'state', label: 'Stato' }, { key: 'totals', label: 'Residuo', render: v => money((v as Row | undefined)?.outstanding) }, { key: 'totals', label: 'Scaduto', render: v => money((v as Row | undefined)?.overdue) }, { key: 'next_due_date', label: 'Prossima scadenza', render: displayDate }]} onRow={r => setKey(String(r.key))} /></div>
      : <div className="detail-section"><Field label="Professionista"><select value={practitioner} onChange={e => setPractitioner(e.target.value)}><option value="">Seleziona</option>{boot.practitioners.map(p => <option key={p.name} value={p.name}>{demoText(p.practitioner_name)}</option>)}</select></Field><p>Fatture e pagamenti seguono il soggetto fornitore; il server non li ripartisce per seduta.</p></div>}
    {error && <div className="detail-section"><p className="inline-error" role="alert">{error}</p></div>}
    {loading && <p className="detail-section" role="status">Caricamento report…</p>}
    {detail && <><div className="detail-section"><Chip tone={String(detail.state ?? 'OK').includes('verificare') ? 'warn' : 'blue'}>{demoText(detail.state ?? detail.practitioner_name ?? 'Report')}</Chip><h3>{mode === 'patients' ? demoPreferred(detail.key, detail.customer_label ?? 'Dettaglio') : demoText(detail.practitioner_name ?? 'Dettaglio')}</h3><div className="finance-report-metrics"><Metric label="Sedute" value={String(counts?.sessions ?? 0)} /><Metric label="Svolte" value={String(counts?.performed ?? 0)} tone="green" /><Metric label={mode === 'patients' ? 'Residuo contabile' : 'Compenso atteso'} value={money(mode === 'patients' ? totals?.outstanding : economics?.expected)} tone="amber" /></div>{mode === 'patients' && <p>Fatturato {money(totals?.invoiced)} · Incassato {money(totals?.collected)} · Scaduto {money(totals?.overdue)} · Fatture aperte: {String(totals?.open_invoices ?? 0)}</p>}{mode === 'patients' && <p>Stato incassi: {detail.blocked ? 'Prenotazioni bloccate' : 'Nessun blocco'} · {detail.deferred ? 'Scadenza differita' : 'Nessun differimento'} · Prossima scadenza: {displayDate(detail.next_due_date)}</p>}{mode === 'professionals' && <p>Attesi sospesi: {String(economics?.suspended ?? 0)} · Da verificare: {String(economics?.review ?? 0)}. Fatture ricevute: {String((economics?.supplier_invoices as Row[] ?? []).length)}.</p>}</div><div className="detail-section"><h3>Sedute nel periodo</h3><DataTable rows={detail.sessions as Row[] ?? []} columns={[{ key: 'appointment_date', label: 'Data', render: displayDate }, { key: 'patient_label', label: 'Paziente' }, { key: 'cc_service_label', label: 'Servizio' }, { key: 'category', label: 'Esito' }]} /></div>{mode === 'patients' ? <><div className="detail-section"><h3>Fatture nel periodo</h3><DataTable rows={detail.invoices as Row[] ?? []} columns={[{ key: 'name', label: 'Fattura' }, { key: 'posting_date', label: 'Data', render: displayDate }, { key: 'grand_total', label: 'Totale', render: v => money(v) }]} /><h3>Pagamenti nel periodo</h3><DataTable rows={detail.payments as Row[] ?? []} columns={[{ key: 'name', label: 'Pagamento' }, { key: 'posting_date', label: 'Data', render: displayDate }, { key: 'collected_amount', label: 'Incassato', render: v => money(v) }]} /></div><div className="detail-section"><h3>Fatture aperte, posizione corrente</h3><DataTable rows={detail.open_invoices as Row[] ?? []} columns={[{ key: 'name', label: 'Fattura' }, { key: 'outstanding_amount', label: 'Residuo', render: v => money(v) }, { key: 'original_due_date', label: 'Scadenza originaria', render: displayDate }, { key: 'effective_due_date', label: 'Scadenza effettiva', render: displayDate }, { key: 'overdue', label: 'Scaduta', render: v => v ? 'Sì' : 'No' }]} /><p className="scope-note">I debiti operativi non sono sommati al residuo delle fatture.</p></div></> : <><div className="detail-section"><h3>Compensi attesi</h3><DataTable rows={economics?.expectations as Row[] ?? []} columns={[{ key: 'appointment', label: 'Seduta' }, { key: 'state', label: 'Stato' }, { key: 'amount', label: 'Importo', render: v => money(v) }]} /><p>Attesi senza snapshot: {String((economics?.missing_expectation_sessions as string[] ?? []).length)} · Pagato a fornitori nel periodo: {money(economics?.supplier_paid)}</p></div><div className="detail-section"><h3>Fatture fornitore nel periodo</h3><DataTable rows={economics?.supplier_invoices as Row[] ?? []} columns={[{ key: 'name', label: 'Fattura' }, { key: 'posting_date', label: 'Data', render: displayDate }, { key: 'grand_total', label: 'Importo', render: v => money(v) }]} /></div><div className="detail-section"><h3>Confronti atteso e ricevuto</h3><DataTable rows={economics?.comparisons as Row[] ?? []} columns={[{ key: 'purchase_invoice', label: 'Fattura' }, { key: 'state', label: 'Esito' }, { key: 'expected_amount', label: 'Atteso', render: v => money(v) }, { key: 'received_amount', label: 'Ricevuto', render: v => money(v) }, { key: 'difference', label: 'Differenza', render: v => money(v) }]} /></div></>}<div className="detail-section"><p className="scope-note">{String(detail.scope_note ?? '')}</p></div></>}
    {!detail && !loading && mode === 'professionals' && !practitioner && <Empty title="Seleziona un professionista" />}
    <div className="detail-section"><a className="button secondary" href={exportHref} aria-disabled={mode === 'professionals' && !practitioner} onClick={e => { if (mode === 'professionals' && !practitioner) e.preventDefault() }}><Download size={16} /> Esporta CSV</a></div>
  </Drawer>}</>
}
