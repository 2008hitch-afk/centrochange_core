import { useEffect, useState } from 'react'
import { Download } from 'lucide-react'
import { type FinanceBoot, type Row, displayDate, finance, money } from './api'
import { type Feedback, Button, Chip, DataTable, Drawer, Empty, Field, Metric } from './ui'

type Props = { boot: FinanceBoot; center: string; start: string; end: string; feedback: Feedback }
const url = (method: string, args: Row) => '/api/method/centrochange_core.finance.' + method + '?' + new URLSearchParams(Object.entries(args).map(([k, v]) => [k, String(v ?? '')]))
const errorText = (e: unknown) => e instanceof Error ? e.message : 'Report non disponibile.'

export function FinanceReports({ boot, center, start, end, feedback }: Props) {
  const [open, setOpen] = useState(false)
  const [mode, setMode] = useState<'patients' | 'professionals'>('patients')
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
  return <><Button variant="secondary" onClick={() => setOpen(true)}>Report dettagliati</Button>{open && <Drawer title="Report dettagliati" onClose={() => setOpen(false)}>
    <div className="detail-section"><p>Periodo: {displayDate(start)} – {displayDate(end)} · Centro: {center}</p><div className="segmented"><button className={mode === 'patients' ? 'selected' : ''} onClick={() => { setMode('patients'); setDetail(null) }}>Pazienti e soggetti fiscali</button><button className={mode === 'professionals' ? 'selected' : ''} onClick={() => { setMode('professionals'); setDetail(null) }}>Professionisti</button></div></div>
    {mode === 'patients' ? <div className="detail-section"><h3>Soggetti fiscali</h3><p>Una riga per Customer. Nessuna ripartizione inventata tra pazienti con lo stesso soggetto fiscale.</p><DataTable rows={groups} columns={[{ key: 'customer_label', label: 'Soggetto' }, { key: 'state', label: 'Stato' }, { key: 'totals', label: 'Residuo', render: v => money((v as Row | undefined)?.outstanding) }]} onRow={r => setKey(String(r.key))} /></div>
      : <div className="detail-section"><Field label="Professionista"><select value={practitioner} onChange={e => setPractitioner(e.target.value)}><option value="">Seleziona</option>{boot.practitioners.map(p => <option key={p.name} value={p.name}>{p.practitioner_name}</option>)}</select></Field><p>Fatture e pagamenti seguono il soggetto fornitore; il server non li ripartisce per seduta.</p></div>}
    {error && <div className="detail-section"><p className="inline-error" role="alert">{error}</p><Button variant="secondary" onClick={() => feedback(error, true)}>Mostra errore</Button></div>}
    {loading && <p className="detail-section" role="status">Caricamento report…</p>}
    {detail && <><div className="detail-section"><Chip tone={String(detail.state ?? 'OK').includes('verificare') ? 'warn' : 'blue'}>{String(detail.state ?? detail.practitioner_name ?? 'Report')}</Chip><h3>{String(detail.customer_label ?? detail.practitioner_name ?? 'Dettaglio')}</h3><div className="finance-report-metrics"><Metric label="Sedute" value={String(counts?.sessions ?? 0)} /><Metric label="Svolte" value={String(counts?.performed ?? 0)} tone="green" /><Metric label={mode === 'patients' ? 'Residuo contabile' : 'Compenso atteso'} value={money(mode === 'patients' ? totals?.outstanding : economics?.expected)} tone="amber" /></div>{mode === 'patients' && <p>Fatturato {money(totals?.invoiced)} · Incassato {money(totals?.collected)} · Scaduto {money(totals?.overdue)}</p>}{mode === 'professionals' && <p>Attesi sospesi: {String(economics?.suspended ?? 0)} · Da verificare: {String(economics?.review ?? 0)}. Fatture ricevute: {String((economics?.supplier_invoices as Row[] ?? []).length)}.</p>}</div><div className="detail-section"><h3>Sedute nel periodo</h3><DataTable rows={detail.sessions as Row[] ?? []} columns={[{ key: 'appointment_date', label: 'Data', render: displayDate }, { key: 'patient_label', label: 'Paziente' }, { key: 'cc_service_label', label: 'Servizio' }, { key: 'category', label: 'Esito' }]} /></div>{mode === 'patients' ? <><div className="detail-section"><h3>Fatture e incassi</h3><DataTable rows={detail.invoices as Row[] ?? []} columns={[{ key: 'name', label: 'Fattura' }, { key: 'posting_date', label: 'Data', render: displayDate }, { key: 'grand_total', label: 'Totale', render: v => money(v) }]} /><h3>Pagamenti</h3><DataTable rows={detail.payments as Row[] ?? []} columns={[{ key: 'name', label: 'Pagamento' }, { key: 'posting_date', label: 'Data', render: displayDate }, { key: 'collected_amount', label: 'Incassato', render: v => money(v) }]} /></div></> : <div className="detail-section"><h3>Confronti atteso e ricevuto</h3><DataTable rows={economics?.comparisons as Row[] ?? []} columns={[{ key: 'purchase_invoice', label: 'Fattura' }, { key: 'state', label: 'Esito' }, { key: 'expected_amount', label: 'Atteso', render: v => money(v) }, { key: 'received_amount', label: 'Ricevuto', render: v => money(v) }]} /></div>}<div className="detail-section"><p className="scope-note">{String(detail.scope_note ?? '')}</p></div></>}
    {!detail && !loading && mode === 'professionals' && !practitioner && <Empty title="Seleziona un professionista" />}
    <div className="detail-section"><a className="button secondary" href={exportHref} aria-disabled={mode === 'professionals' && !practitioner} onClick={e => { if (mode === 'professionals' && !practitioner) e.preventDefault() }}><Download size={16} /> Esporta CSV</a></div>
  </Drawer>}</>
}
