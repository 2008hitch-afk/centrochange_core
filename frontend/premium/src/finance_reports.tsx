import { useEffect, useMemo, useState } from 'react'
import { ArrowRight, Download, Search } from 'lucide-react'
import { type Boot, type FinanceBoot, type Patient, type Row, displayDate, finance, money } from './api'
import { type Feedback, Button, Chip, DataTable, Empty, Field, Metric } from './ui'
import { demoCustomer, demoPatient, demoText } from './demo_labels'
import { centerNameFor, practitionerName } from './display_names'

type Props = {
  boot: FinanceBoot
  generalBoot?: Boot | null
  center: string
  start: string
  end: string
  feedback: Feedback
  initialMode?: 'patients' | 'customers' | 'professionals'
  initialPatient?: string
  buttonLabel?: string
  onClose?: () => void
}

const url = (method: string, args: Row) =>
  '/api/method/centrochange_core.finance.' +
  method +
  '?' +
  new URLSearchParams(Object.entries(args).map(([k, v]) => [k, String(v ?? '')]))

const errorText = (e: unknown) => (e instanceof Error ? e.message : 'Report non disponibile.')

export function FinanceReportsPage({
  boot,
  generalBoot,
  center,
  start,
  end,
  feedback,
  initialMode = 'patients',
  initialPatient = '',
  onClose,
}: Props) {
  const [mode, setMode] = useState<'patients' | 'customers' | 'professionals'>(initialMode)
  const [groups, setGroups] = useState<Row[]>([])
  const [key, setKey] = useState('')
  const [patientId, setPatientId] = useState(initialPatient)
  const [patientSearch, setPatientSearch] = useState('')
  const [practitioner, setPractitioner] = useState('')
  const [detail, setDetail] = useState<Row | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    setKey('')
    setPatientId(initialPatient)
    setPractitioner('')
    setGroups([])
    setDetail(null)
  }, [center])

  useEffect(() => {
    if (mode === 'professionals') return
    let live = true
    setLoading(true)
    setError('')
    finance<{ rows: Row[] }>('patient_reporting.patient_view', { center, start, end })
      .then(r => {
        if (live) {
          setGroups(r.rows)
          setLoading(false)
        }
      })
      .catch(e => {
        if (live) {
          setError(errorText(e))
          setLoading(false)
        }
      })
    return () => {
      live = false
    }
  }, [mode, center, start, end])

  // Single patient or customer detail
  useEffect(() => {
    if (mode === 'patients' && !patientId) return
    if (mode === 'customers' && !key) return
    if (mode === 'professionals' && !practitioner) return
    let live = true
    setLoading(true)
    setError('')
    setDetail(null)

    const task =
      mode === 'patients'
        ? finance<Row>('patient_reporting.patient_view', { center, start, end, patient: patientId })
        : mode === 'customers'
        ? finance<Row>('patient_reporting.patient_view', { center, start, end, key })
        : finance<Row>('reporting.professional_view', { center, start, end, practitioner })

    task
      .then(r => {
        if (live) {
          setDetail(r)
          setLoading(false)
        }
      })
      .catch(e => {
        if (live) {
          setError(errorText(e))
          setLoading(false)
        }
      })
    return () => {
      live = false
    }
  }, [mode, center, start, end, key, patientId, practitioner])

  // Extract flat patients list from groups + generalBoot
  const patientList = useMemo(() => {
    const map = new Map<string, { name: string; label: string; customer?: string; customer_label?: string }>()
    if (generalBoot?.patients) {
      for (const p of generalBoot.patients) {
        map.set(p.name, {
          name: p.name,
          label: demoPatient(p.name, p.patient_name, p.first_name, p.last_name),
        })
      }
    }
    for (const g of groups) {
      const pts = (g.patients as Array<{ name: string; label: string }> ?? [])
      for (const p of pts) {
        if (!map.has(p.name) || map.get(p.name)?.label === p.name) {
          map.set(p.name, {
            name: p.name,
            label: demoPatient(p.name, p.label),
            customer: String(g.customer ?? ''),
            customer_label: String(g.customer_label ?? ''),
          })
        }
      }
    }
    const q = patientSearch.trim().toLocaleLowerCase('it-IT')
    const all = Array.from(map.values())
    if (!q) return all.slice(0, 50)
    return all.filter(p => p.label.toLocaleLowerCase('it-IT').includes(q) || p.name.toLocaleLowerCase('it-IT').includes(q)).slice(0, 50)
  }, [groups, generalBoot, patientSearch])

  const counts = detail?.counts as Row | undefined
  const totals = detail?.totals as Row | undefined
  const economics = detail?.economics as Row | undefined
  const collectionsData = detail?.collections as { debts?: Row[] } | undefined
  const debts = collectionsData?.debts ?? []

  // When in single patient mode, filter sessions and debts strictly for that patient
  const patientSessions = useMemo(() => {
    if (mode !== 'patients' || !patientId || !detail?.sessions) return (detail?.sessions as Row[] ?? [])
    return (detail.sessions as Row[]).filter(s => s.patient === patientId)
  }, [mode, patientId, detail])

  const patientDebts = useMemo(() => {
    if (mode !== 'patients' || !patientId) return debts
    return debts.filter(d => d.patient === patientId)
  }, [mode, patientId, debts])

  const patientToSettleCount = useMemo(() => {
    return patientSessions.filter(
      s => !s.cc_paid && s.cc_economic_state === 'Due' && ['performed', 'closed_not_performed'].includes(String(s.category))
    ).length
  }, [patientSessions])

  const exportHref =
    mode === 'patients' && patientId
      ? url('patient_reporting.patient_export', { center, start, end, patient: patientId })
      : mode === 'customers' && key
      ? url('patient_reporting.patient_export', { center, start, end, key })
      : mode === 'professionals' && practitioner
      ? url('reporting.professional_export', { center, start, end, practitioner })
      : url('patient_reporting.patient_export', { center, start, end })

  return (
    <section className="panel finance-reports-page">
      <header className="patient-page-header">
        {onClose && (
          <button type="button" className="patient-back" onClick={onClose}>
            ← Torna al riepilogo
          </button>
        )}
        <h1>Report dettagliati</h1>
        <p className="scope-note" style={{ margin: '6px 0 0' }}>
          Periodo: {displayDate(start)} – {displayDate(end)} · Centro: {centerNameFor(center, boot.centers)}
        </p>
      </header>

      <div className="detail-section">
        <div className="segmented" role="tablist" aria-label="Modalità report dettagliati">
          <button
            role="tab"
            aria-selected={mode === 'patients'}
            className={mode === 'patients' ? 'selected' : ''}
            onClick={() => {
              setMode('patients')
              setDetail(null)
            }}
          >
            Per paziente
          </button>
          <button
            role="tab"
            aria-selected={mode === 'customers'}
            className={mode === 'customers' ? 'selected' : ''}
            onClick={() => {
              setMode('customers')
              setDetail(null)
            }}
          >
            Per soggetto fiscale
          </button>
          <button
            role="tab"
            aria-selected={mode === 'professionals'}
            className={mode === 'professionals' ? 'selected' : ''}
            onClick={() => {
              setMode('professionals')
              setDetail(null)
            }}
          >
            Per professionista
          </button>
        </div>
      </div>

      {mode === 'patients' && (
        <div className="detail-section">
          <h3>Ricerca paziente</h3>
          <p className="scope-note">
            Cerca per nome, cognome o codice. Consulta le sedute da saldare, i debiti operativi e la posizione del soggetto fiscale intestatario.
          </p>
          <div className="form-grid" style={{ marginBottom: 16 }}>
            <Field label="Cerca paziente">
              <label className="search-inline">
                <Search size={17} />
                <input
                  type="search"
                  placeholder="Cerca paziente per nome o codice"
                  value={patientSearch}
                  onChange={e => setPatientSearch(e.target.value)}
                />
              </label>
            </Field>
          </div>
          {!patientId && (
            <div className="patient-picker-list" style={{ maxHeight: 280, overflowY: 'auto', border: '1px solid var(--line, #dce5ee)', borderRadius: 8, padding: 8 }}>
              {patientList.length === 0 ? (
                <Empty title="Nessun paziente trovato" detail="Modifica il testo di ricerca." />
              ) : (
                <DataTable
                  rows={patientList as unknown as Row[]}
                  columns={[
                    { key: 'label', label: 'Paziente', render: v => <strong>{String(v)}</strong> },
                    { key: 'customer_label', label: 'Soggetto fiscale intestatario', render: (v, r) => demoCustomer(r.customer, v) },
                    { key: 'name', label: '', render: () => <ArrowRight size={16} /> },
                  ]}
                  onRow={r => setPatientId(String(r.name))}
                />
              )}
            </div>
          )}
          {patientId && (
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', margin: '8px 0 16px', flexWrap: 'wrap', gap: 8 }}>
              <span>Paziente selezionato: <strong>{patientList.find(p => p.name === patientId)?.label || patientId}</strong></span>
              <Button variant="secondary" onClick={() => { setPatientId(''); setDetail(null) }}>Cambia paziente</Button>
            </div>
          )}
        </div>
      )}

      {mode === 'customers' && (
        <div className="detail-section">
          <h3>Soggetti fiscali intestatari (Customer)</h3>
          <p className="scope-note">
            Una riga per Customer. Il saldo e le fatture competono all'intestatario fiscale e non vengono ripartiti artificiosamente tra i singoli pazienti.
          </p>
          <DataTable
            rows={groups}
            columns={[
              { key: 'customer_label', label: 'Soggetto fiscale', render: (value, row) => demoCustomer(row.key, value) },
              { key: 'state', label: 'Stato' },
              { key: 'totals', label: 'Residuo contabile', render: v => money((v as Row | undefined)?.outstanding) },
              { key: 'totals', label: 'Scaduto', render: v => money((v as Row | undefined)?.overdue) },
              { key: 'next_due_date', label: 'Prossima scadenza', render: displayDate },
            ]}
            onRow={r => setKey(String(r.key))}
          />
        </div>
      )}

      {mode === 'professionals' && (
        <div className="detail-section">
          <Field label="Professionista">
            <select value={practitioner} onChange={e => setPractitioner(e.target.value)}>
              <option value="">Seleziona un professionista</option>
              {boot.practitioners.map(p => (
                <option key={p.name} value={p.name}>
                  {practitionerName(p)}
                </option>
              ))}
            </select>
          </Field>
          <p className="scope-note">
            Fatture e pagamenti seguono il soggetto fornitore; il server non li ripartisce per seduta.
          </p>
        </div>
      )}

      {error && (
        <div className="detail-section">
          <p className="inline-error" role="alert">{error}</p>
        </div>
      )}

      {loading && <p className="detail-section panel-loading" role="status">Caricamento report…</p>}

      {detail && mode === 'patients' && patientId && (
        <>
          <div className="detail-section">
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8, flexWrap: 'wrap' }}>
              <Chip tone={detail.blocked ? 'bad' : patientToSettleCount > 0 ? 'warn' : 'good'}>
                {detail.blocked ? 'Blocco prenotazioni' : patientToSettleCount > 0 ? `${patientToSettleCount} sedute da saldare` : 'Posizione regolare'}
              </Chip>
              {Boolean(detail.deferred) && <Chip tone="blue">Scadenza differita</Chip>}
            </div>
            <h2>{patientList.find(p => p.name === patientId)?.label || patientId}</h2>
            <p className="scope-note">
              Soggetto fiscale intestatario: <strong>{demoCustomer(detail.key, detail.customer_label ?? '—')}</strong>
            </p>

            <div className="finance-report-metrics">
              <Metric label="Sedute nel periodo" value={String(patientSessions.length)} />
              <Metric label="Sedute svolte" value={String(patientSessions.filter(s => s.category === 'performed').length)} tone="green" />
              <Metric label="Sedute da saldare" value={String(patientToSettleCount)} tone={patientToSettleCount > 0 ? 'amber' : 'green'} />
              <Metric label="Debito operativo" value={money(patientDebts.reduce((sum, d) => sum + Number(d.amount || 0), 0))} tone={patientDebts.length > 0 ? 'amber' : 'blue'} />
            </div>
          </div>

          {patientDebts.length > 0 && (
            <div className="detail-section">
              <h3>Debiti operativi del paziente</h3>
              <p className="scope-note">
                Posizioni aperte di seduta per le quali non è ancora registrato il saldo operativo.
              </p>
              <DataTable
                rows={patientDebts}
                columns={[
                  { key: 'name', label: 'Riferimento seduta' },
                  { key: 'amount', label: 'Importo dovuto', render: (v, r) => money(v, String(r.currency || 'EUR')) },
                  { key: 'original_due_date', label: 'Scadenza originaria', render: displayDate },
                  { key: 'due_date', label: 'Scadenza effettiva', render: displayDate },
                  { key: 'override', label: 'Deroga', render: v => v ? 'Autorizzata' : 'Nessuna' },
                ]}
              />
            </div>
          )}

          <div className="detail-section">
            <div className="customer-fiscal-banner">
              <strong>Soggetto fiscale intestatario: {demoCustomer(detail.key, detail.customer_label ?? '—')}</strong>
              <p>
                Il residuo contabile, le fatture e gli incassi appartengono all'intestatario fiscale registrato (Customer) e non vengono suddivisi artificiosamente tra i singoli pazienti della famiglia.
              </p>
              <div style={{ display: 'flex', gap: 16, marginTop: 10, flexWrap: 'wrap' }}>
                <span>Residuo contabile: <strong>{money(totals?.outstanding)}</strong></span>
                <span>Fatturato periodo: <strong>{money(totals?.invoiced)}</strong></span>
                <span>Incassato periodo: <strong>{money(totals?.collected)}</strong></span>
                <span>Scaduto: <strong>{money(totals?.overdue)}</strong></span>
                <span>Fatture aperte: <strong>{String(totals?.open_invoices ?? 0)}</strong></span>
              </div>
            </div>
          </div>

          <div className="detail-section">
            <h3>Sedute del paziente nel periodo</h3>
            <DataTable
              rows={patientSessions}
              columns={[
                { key: 'appointment_date', label: 'Data', render: displayDate },
                { key: 'appointment_time', label: 'Ora' },
                { key: 'cc_service_label', label: 'Servizio' },
                { key: 'category', label: 'Esito' },
                { key: 'cc_price_snapshot', label: 'Tariffa', render: (v, r) => money(v, String(r.cc_currency_snapshot || 'EUR')) },
                { key: 'cc_paid', label: 'Pagata operativamente', render: v => v ? 'Sì' : 'No' },
              ]}
            />
          </div>

          <div className="detail-section">
            <a className="button secondary" href={exportHref}>
              <Download size={16} /> Esporta CSV paziente
            </a>
          </div>
        </>
      )}

      {detail && mode === 'customers' && (
        <>
          <div className="detail-section">
            <Chip tone={String(detail.state ?? 'OK').includes('verificare') ? 'warn' : 'blue'}>
              {demoText(detail.state ?? 'Report')}
            </Chip>
            <h2>{demoCustomer(detail.key, detail.customer_label ?? 'Dettaglio soggetto fiscale')}</h2>
            <div className="finance-report-metrics">
              <Metric label="Sedute del gruppo" value={String(counts?.sessions ?? 0)} />
              <Metric label="Svolte" value={String(counts?.performed ?? 0)} tone="green" />
              <Metric label="Residuo contabile" value={money(totals?.outstanding)} tone="amber" />
            </div>
            <p className="scope-note">
              Fatturato: {money(totals?.invoiced)} · Incassato: {money(totals?.collected)} · Scaduto: {money(totals?.overdue)} · Fatture aperte: {String(totals?.open_invoices ?? 0)}
            </p>
            <p className="scope-note">
              Stato incassi: {detail.blocked ? 'Prenotazioni bloccate' : 'Nessun blocco'} · {detail.deferred ? 'Scadenza differita' : 'Nessun differimento'} · Prossima scadenza: {displayDate(detail.next_due_date)}
            </p>
          </div>

          <div className="detail-section">
            <h3>Sedute nel periodo (tutti i pazienti collegati)</h3>
            <DataTable
              rows={(detail.sessions as Row[] ?? [])}
              columns={[
                { key: 'appointment_date', label: 'Data', render: displayDate },
                { key: 'patient_label', label: 'Paziente', render: value => demoPatient(value, value) },
                { key: 'cc_service_label', label: 'Servizio' },
                { key: 'category', label: 'Esito' },
              ]}
            />
          </div>

          <div className="detail-section">
            <h3>Fatture nel periodo</h3>
            <DataTable
              rows={(detail.invoices as Row[] ?? [])}
              columns={[
                { key: 'name', label: 'Fattura' },
                { key: 'posting_date', label: 'Data', render: displayDate },
                { key: 'grand_total', label: 'Totale', render: v => money(v) },
              ]}
            />
            <h3 style={{ marginTop: 20 }}>Pagamenti nel periodo</h3>
            <DataTable
              rows={(detail.payments as Row[] ?? [])}
              columns={[
                { key: 'name', label: 'Pagamento' },
                { key: 'posting_date', label: 'Data', render: displayDate },
                { key: 'collected_amount', label: 'Incassato', render: v => money(v) },
              ]}
            />
          </div>

          <div className="detail-section">
            <h3>Fatture aperte, posizione corrente</h3>
            <DataTable
              rows={(detail.open_invoices as Row[] ?? [])}
              columns={[
                { key: 'name', label: 'Fattura' },
                { key: 'outstanding_amount', label: 'Residuo', render: v => money(v) },
                { key: 'original_due_date', label: 'Scadenza originaria', render: displayDate },
                { key: 'effective_due_date', label: 'Scadenza effettiva', render: displayDate },
                { key: 'overdue', label: 'Scaduta', render: v => (v ? 'Sì' : 'No') },
              ]}
            />
            <p className="scope-note">I debiti operativi non sono sommati al residuo contabile delle fatture.</p>
          </div>

          <div className="detail-section">
            <a className="button secondary" href={exportHref}>
              <Download size={16} /> Esporta CSV soggetto fiscale
            </a>
          </div>
        </>
      )}

      {detail && mode === 'professionals' && (
        <>
          <div className="detail-section">
            <Chip tone={String(detail.state ?? 'OK').includes('verificare') ? 'warn' : 'blue'}>
              {demoText(detail.practitioner_name ?? 'Report professionista')}
            </Chip>
            <h2>{demoText(detail.practitioner_name ?? 'Dettaglio')}</h2>
            <div className="finance-report-metrics">
              <Metric label="Sedute" value={String(counts?.sessions ?? 0)} />
              <Metric label="Svolte" value={String(counts?.performed ?? 0)} tone="green" />
              <Metric label="Compenso atteso" value={money(economics?.expected)} tone="amber" />
            </div>
            <p className="scope-note">
              Attesi sospesi: {String(economics?.suspended ?? 0)} · Da verificare: {String(economics?.review ?? 0)} · Fatture ricevute: {String((economics?.supplier_invoices as Row[] ?? []).length)}.
            </p>
          </div>

          <div className="detail-section">
            <h3>Compensi attesi</h3>
            <DataTable
              rows={(economics?.expectations as Row[] ?? [])}
              columns={[
                { key: 'appointment', label: 'Seduta' },
                { key: 'state', label: 'Stato' },
                { key: 'amount', label: 'Importo', render: v => money(v) },
              ]}
            />
            <p className="scope-note">
              Attesi senza snapshot: {String((economics?.missing_expectation_sessions as string[] ?? []).length)} · Pagato a fornitori nel periodo: {money(economics?.supplier_paid)}
            </p>
          </div>

          <div className="detail-section">
            <h3>Fatture fornitore nel periodo</h3>
            <DataTable
              rows={(economics?.supplier_invoices as Row[] ?? [])}
              columns={[
                { key: 'name', label: 'Fattura' },
                { key: 'posting_date', label: 'Data', render: displayDate },
                { key: 'grand_total', label: 'Importo', render: v => money(v) },
              ]}
            />
          </div>

          <div className="detail-section">
            <h3>Confronti atteso e ricevuto</h3>
            <DataTable
              rows={(economics?.comparisons as Row[] ?? [])}
              columns={[
                { key: 'purchase_invoice', label: 'Fattura' },
                { key: 'state', label: 'Esito' },
                { key: 'expected_amount', label: 'Atteso', render: v => money(v) },
                { key: 'received_amount', label: 'Ricevuto', render: v => money(v) },
                { key: 'difference', label: 'Differenza', render: v => money(v) },
              ]}
            />
          </div>

          <div className="detail-section">
            <a className="button secondary" href={exportHref}>
              <Download size={16} /> Esporta CSV professionista
            </a>
          </div>
        </>
      )}

      {!detail && !loading && mode === 'professionals' && !practitioner && (
        <div className="detail-section">
          <Empty title="Seleziona un professionista" />
        </div>
      )}
    </section>
  )
}

// Wrapper for backwards compatibility
export function FinanceReports(props: Props) {
  const [open, setOpen] = useState(false)
  if (open) {
    return <FinanceReportsPage {...props} onClose={() => setOpen(false)} />
  }
  return (
    <Button variant="secondary" onClick={() => setOpen(true)}>
      {props.buttonLabel || 'Report dettagliati'}
    </Button>
  )
}
