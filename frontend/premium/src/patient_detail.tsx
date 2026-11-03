import { useEffect, useRef, useState } from 'react'
import { type Boot, type FinanceBoot, type Patient, type Row, displayDate, money, ops, finance, requestKey, time } from './api'
import { demoPatient, demoText } from './demo_labels'
import { auditActorName, closureName, practitionerNameFor } from './display_names'
import { AppointmentTimeline } from './appointment_timeline'
import { NoteHistory } from './note_history'
import { PatientAssignments } from './patient_assignments'
import { PatientPackages } from './patient_packages'
import { saveArchive } from './scoped_api'
import { Button, Chip, Empty, Field, FormError, Modal, Metric, DataTable, type Feedback } from './ui'

type Profile = Row & { name: string; modified: string; first_name: string; last_name: string; email: string; active_assignment: boolean }
type History = { appointments: Row[]; truncated: boolean; settlements: Row[]; organizational_notes: Row[]; private_notes: Row[]; packages: Row[]; assignment_events?: Row[]; total_appointments?: number; page?: number; total_pages?: number }
const errorText = (cause: unknown) => cause instanceof Error ? cause.message : 'Operazione non riuscita.'

export function PatientDetail({ boot, financeBoot, patient, center, feedback, initialTab, onOpenReport, onClose, onSuccess }: {
  boot: Boot; financeBoot?: FinanceBoot | null; patient: Patient; center: string; feedback: Feedback;
  initialTab?: 'Riepilogo' | 'Sedute' | 'Assegnazioni' | 'Note' | 'Pacchetti' | 'Pagamenti';
  onOpenReport?: (patientId?: string) => void;
  onClose: () => void; onSuccess: () => void
}) {
  const [profile, setProfile] = useState<Profile | null>(null)
  const [history, setHistory] = useState<History | null>(null)
  const [historyPage, setHistoryPage] = useState(1)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [reload, setReload] = useState(0)
  const [draft, setDraft] = useState<Profile | null>(null)
  const [reason, setReason] = useState('')
  const [saving, setSaving] = useState(false)
  const saveKey = useRef(requestKey())
  const [note, setNote] = useState('')
  const [notePrivate, setNotePrivate] = useState(false)
  const [corrects, setCorrects] = useState<string | null>(null)
  const [noteBusy, setNoteBusy] = useState(false)
  const [appointment, setAppointment] = useState<Row | null>(null)

  const canViewPayments = Boolean(
    financeBoot &&
    !boot.roles.includes('CC Professional') &&
    boot.roles.some(r => ['CC Manager', 'CC Secretariat', 'CC Finance', 'CC Accountant'].includes(r))
  )

  const [tab, setTab] = useState<'Riepilogo' | 'Sedute' | 'Assegnazioni' | 'Note' | 'Pacchetti' | 'Pagamenti'>(() => {
    if (initialTab === 'Pagamenti' && canViewPayments) return 'Pagamenti'
    if (initialTab && ['Riepilogo', 'Sedute', 'Assegnazioni', 'Note', 'Pacchetti'].includes(initialTab)) return initialTab
    return 'Riepilogo'
  })

  const tabs = canViewPayments
    ? (['Riepilogo', 'Sedute', 'Assegnazioni', 'Note', 'Pacchetti', 'Pagamenti'] as const)
    : (['Riepilogo', 'Sedute', 'Assegnazioni', 'Note', 'Pacchetti'] as const)

  const [events, setEvents] = useState<Row[] | null>(null)
  const [eventsError, setEventsError] = useState('')
  const savedScroll = useRef(0)
  const sourceAppointment = useRef('')
  const backButton = useRef<HTMLButtonElement | null>(null)
  const manager = boot.roles.includes('CC Manager')
  const professional = boot.roles.includes('CC Professional')
  const patientLabel = demoPatient(patient.name, profile?.patient_name ?? patient.patient_name,
    profile?.first_name ?? patient.first_name, profile?.last_name ?? patient.last_name)
  const historical = profile?.active_assignment === false

  useEffect(() => {
    let live = true
    setLoading(true); setError(''); setAppointment(null); setProfile(null); setHistory(null)
    setNote(''); setCorrects(null); setNotePrivate(false); setDraft(null)
    Promise.all([
      ops<Profile>('profiles.patient_detail', { center, name: patient.name }),
      ops<History>('workspace.patient_history', { center, patient: patient.name, page: historyPage, page_length: 50 })
    ]).then(([record, activity]) => { if (live) { setProfile(record); setHistory(activity) } })
      .catch(cause => { if (live) setError(errorText(cause)) })
      .finally(() => { if (live) setLoading(false) })
    return () => { live = false }
  }, [center, patient.name, reload, historyPage])

  useEffect(() => {
    if (!appointment) return
    let live = true
    setEvents(null); setEventsError('')
    ops<Row[]>('workspace.appointment_events', { appointment: appointment.name })
      .then(result => { if (live) setEvents(result) })
      .catch(cause => { if (live) setEventsError(errorText(cause)) })
    return () => { live = false }
  }, [appointment])

  useEffect(() => {
    if (!appointment) return
    const drawer = document.querySelector<HTMLElement>('.patient-detail-page')
    if (drawer) drawer.scrollTop = 0
    backButton.current?.focus()
  }, [appointment])

  const openAppointment = (row: Row, button: HTMLButtonElement) => {
    savedScroll.current = button.closest<HTMLElement>('.patient-detail-page')?.scrollTop ?? 0
    sourceAppointment.current = String(row.name)
    setAppointment(row)
  }
  const returnToPatient = () => {
    setAppointment(null)
    requestAnimationFrame(() => {
      const drawer = document.querySelector<HTMLElement>('.patient-detail-page')
      if (drawer) drawer.scrollTop = savedScroll.current
      Array.from(drawer?.querySelectorAll<HTMLButtonElement>('button[data-appointment]') ?? [])
        .find(button => button.dataset.appointment === sourceAppointment.current)?.focus({ preventScroll: true })
    })
  }

  const refresh = () => { setReload(value => value + 1); onSuccess() }
  const save = async () => {
    if (!profile || !draft || !reason.trim()) return
    setSaving(true); setError('')
    try {
      await saveArchive(center, 'Patient', profile, draft, reason.trim(), saveKey.current)
      setDraft(null); feedback('Scheda paziente salvata.'); refresh()
    } catch (cause) { setError(errorText(cause)); feedback(errorText(cause), true) }
    finally { setSaving(false) }
  }
  const addNote = async () => {
    if (!note.trim()) return
    setNoteBusy(true); setError('')
    try {
      await ops('notes.add_note', { patient: patient.name, center, content: note.trim(), private: notePrivate ? 1 : 0, corrects }, true)
      setNote(''); setCorrects(null); setNotePrivate(false); feedback(corrects ? 'Rettifica registrata.' : 'Nota registrata.'); refresh()
    } catch (cause) { setError(errorText(cause)); feedback(errorText(cause), true) }
    finally { setNoteBusy(false) }
  }
  const correct = (row: Row, privateNote: boolean) => { setCorrects(String(row.name)); setNote(String(row.content ?? '')); setNotePrivate(privateNote) }

  return <><article className="patient-detail-page" data-active-tab={tab}>
    <header className="patient-page-header"><button type="button" className="patient-back" onClick={onClose}>← Torna ai pazienti</button><h1>{appointment ? 'Dettaglio seduta' : patientLabel}</h1></header>
    {!appointment && <nav className="patient-page-tabs" aria-label="Sezioni della scheda paziente">{tabs.map(next => <button type="button" key={next} aria-current={tab === next ? 'page' : undefined} onClick={() => setTab(next)}>{next}</button>)}</nav>}
    {appointment ? <section className="detail-section patient-appointment-detail">
      <button ref={backButton} className="patient-back" type="button" onClick={returnToPatient}>← Torna alla scheda paziente</button>
      <h3>{demoText(appointment.cc_service_label) || 'Seduta'}</h3>
      <dl className="property-list">
        <div><dt>Paziente</dt><dd>{patientLabel}</dd></div>
        <div><dt>Data e ora</dt><dd>{displayDate(appointment.appointment_date)} · {time(appointment.appointment_time)}</dd></div>
        <div><dt>Professionista</dt><dd>{practitionerNameFor(String(appointment.practitioner ?? ''), boot.practitioners, String(appointment.practitioner_name ?? ''))}</dd></div>
        <div><dt>Stato</dt><dd>{closureName(appointment.cc_closure_state)}</dd></div>
      </dl>
      <h3>Eventi della seduta</h3>
      {eventsError && <p className="inline-error" role="alert">{eventsError}</p>}
      {!events && !eventsError && <p role="status">Caricamento eventi…</p>}
      {events && <AppointmentTimeline rows={events} />}
    </section> : <>
    {loading && <p role="status">Caricamento scheda paziente…</p>}
    {error && <p className="inline-error" role="alert">{error}</p>}
    {profile && <section className="detail-section patient-tab-summary"><h3>Anagrafica</h3>{historical && <p className="scope-note" role="status">Nessuna assegnazione attiva in questo centro. La scheda è consultabile come storico; per riprendere le operazioni, registra una nuova assegnazione autorizzata.</p>}<dl className="property-list"><div><dt>Nome</dt><dd>{profile.first_name || '—'}</dd></div><div><dt>Cognome</dt><dd>{profile.last_name || '—'}</dd></div><div><dt>Email</dt><dd>{profile.email || '—'}</dd></div></dl>{manager && !historical && <Button variant="secondary" onClick={() => { saveKey.current = requestKey(); setDraft({ ...profile }); setReason(''); setError('') }}>Modifica scheda</Button>}</section>}
    {history && <><section className="detail-section patient-tab-sessions"><h3>Sedute {history.total_appointments ? `(${history.total_appointments})` : ''}</h3>
      {history.total_pages && history.total_pages > 1 ? (
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center', marginBottom: '12px' }}>
          <Button variant="secondary" disabled={historyPage <= 1} onClick={() => setHistoryPage(p => Math.max(1, p - 1))}>Precedente</Button>
          <span style={{ fontSize: '13px', color: '#64748b' }}>Pagina {historyPage} di {history.total_pages}</span>
          <Button variant="secondary" disabled={historyPage >= history.total_pages} onClick={() => setHistoryPage(p => p + 1)}>Successiva</Button>
        </div>
      ) : null}
      {history.truncated && !history.total_pages && <p className="scope-note">Mostrate le prime 100 sedute.</p>}
      {history.appointments.length ? history.appointments.map(row => <button className="patient-history-item" type="button" data-appointment={String(row.name)} key={String(row.name)} onClick={event => openAppointment(row, event.currentTarget)}><strong>{displayDate(row.appointment_date)} · {time(row.appointment_time)} · {demoText(row.cc_service_label) || 'Seduta'}</strong><small>{closureName(row.cc_closure_state)} · {practitionerNameFor(String(row.practitioner ?? ''), boot.practitioners, String(row.practitioner_name ?? ''))}</small><span>Apri eventi</span></button>) : <p className="scope-note">Nessuna seduta nel centro.</p>}</section>
      <section className="detail-section patient-tab-assignments"><h3>Assegnazioni: storico</h3>{history.assignment_events?.length ? <div className="timeline">{history.assignment_events.map((row, index) => <article key={index} className="note"><strong>{row.active ? 'Assegnazione attivata' : 'Assegnazione revocata'} · {practitionerNameFor(String(row.practitioner ?? ''), boot.practitioners)}</strong><small>{displayDate(row.event_time)} · {auditActorName(row.actor)}</small><p>Motivo: {String(row.reason ?? '—')}</p></article>)}</div> : <p className="scope-note">Nessun evento di assegnazione disponibile.</p>}</section>
      <section className="detail-section patient-tab-notes"><h3>Note organizzative</h3><NoteHistory rows={history.organizational_notes} onCorrect={historical ? undefined : row => correct(row, false)} />{professional && <><h3>Note professionali riservate</h3><NoteHistory rows={history.private_notes} privateNotes onCorrect={historical ? undefined : row => correct(row, true)} /></>}{!historical && <form onSubmit={event => { event.preventDefault(); void addNote() }}><h3>{corrects ? `Rettifica di una nota ${notePrivate ? 'professionale riservata' : 'organizzativa'}` : 'Nuova nota'}</h3>{!corrects && professional && <fieldset className="note-kind"><legend>Tipo di nota</legend><label><input type="radio" name="note-kind" checked={!notePrivate} onChange={() => setNotePrivate(false)} /> Organizzativa</label><label><input type="radio" name="note-kind" checked={notePrivate} onChange={() => setNotePrivate(true)} /> Professionale riservata</label></fieldset>}<p className="scope-note" role="status">{notePrivate ? 'La nota professionale è visibile soltanto al professionista autorizzato nel contesto del paziente.' : 'La nota organizzativa è visibile ai ruoli autorizzati nel centro.'} {corrects ? 'La rettifica conserva il tipo e la versione precedente nello storico.' : 'Dopo il salvataggio il testo non si modifica: eventuali correzioni si registrano come rettifiche.'}</p><Field label={corrects ? 'Testo della rettifica' : 'Testo della nota'} required><textarea value={note} onChange={event => setNote(event.target.value)} required maxLength={100000} /></Field><FormError error={error} /><div className="form-actions">{corrects && <Button type="button" variant="secondary" onClick={() => { setCorrects(null); setNote(''); setNotePrivate(false) }}>Annulla rettifica</Button>}<Button type="submit" disabled={noteBusy || !note.trim()}>{noteBusy ? 'Salvataggio…' : corrects ? 'Registra rettifica' : 'Aggiungi nota'}</Button></div></form>}</section>
      <div className="patient-tab-packages"><PatientPackages boot={boot} patient={patient.name} center={center} packages={history.packages} feedback={feedback} onSuccess={refresh} readOnly={historical} /></div>
    </>}
    {canViewPayments && <PatientPaymentsTab patient={patient} center={center} onOpenReport={onOpenReport} />}
    {profile && history && <div className="patient-tab-assignments"><PatientAssignments boot={boot} patient={patient.name} center={center} feedback={feedback} onSuccess={refresh} /></div>}
    </>}
  </article>{draft && <Modal title="Modifica paziente" onClose={() => setDraft(null)}><form onSubmit={event => { event.preventDefault(); void save() }}><Field label="Nome" required><input required value={draft.first_name ?? ''} onChange={event => { saveKey.current = requestKey(); setDraft({ ...draft, first_name: event.target.value }) }} /></Field><Field label="Cognome"><input value={draft.last_name ?? ''} onChange={event => { saveKey.current = requestKey(); setDraft({ ...draft, last_name: event.target.value }) }} /></Field><Field label="Email"><input type="email" value={draft.email ?? ''} onChange={event => { saveKey.current = requestKey(); setDraft({ ...draft, email: event.target.value }) }} /></Field><Field label="Motivo" required><textarea required maxLength={500} value={reason} onChange={event => { saveKey.current = requestKey(); setReason(event.target.value) }} /></Field><FormError error={error} /><div className="form-actions"><Button type="button" variant="secondary" onClick={() => setDraft(null)}>Annulla</Button><Button type="submit" disabled={saving}>{saving ? 'Salvataggio…' : 'Salva'}</Button></div></form></Modal>}</>
}

function PatientPaymentsTab({ patient, center, onOpenReport }: {
  patient: Patient; center: string; onOpenReport?: (patientId?: string) => void
}) {
  const [position, setPosition] = useState<{
    blocked: boolean;
    debts: Array<{
      doctype: string;
      name: string;
      amount: number;
      currency: string;
      due_date?: string;
      original_due_date?: string;
      override?: string | null;
    }>;
    agreement?: { mode: string; due_date?: string } | null;
  } | null>(null)
  const [project, setProject] = useState<{
    customer?: string | null;
    customer_label?: string | null;
    accounting_mapping_available?: boolean;
    totals?: {
      invoiced?: number | null;
      collected?: number | null;
      outstanding?: number | null;
      overdue?: number | null;
      open_invoices?: number;
    };
    open_invoices?: Array<{
      name: string;
      posting_date: string;
      currency: string;
      grand_total: number;
      outstanding_amount: number;
      effective_due_date?: string;
    }>;
    scope_note?: string;
  } | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let live = true
    setLoading(true); setError('')
    const now = new Date()
    const start = `${now.getFullYear()}-01-01`
    const end = `${now.getFullYear()}-12-31`
    Promise.allSettled([
      finance<typeof position>('collections.position', { patient: patient.name, center }),
      finance<typeof project>('patient_reporting.patient_view', { center, start, end, patient: patient.name })
    ]).then(([posRes, projRes]) => {
      if (!live) return
      if (posRes.status === 'fulfilled') setPosition(posRes.value)
      if (projRes.status === 'fulfilled') setProject(projRes.value)
      if (posRes.status === 'rejected' && projRes.status === 'rejected') {
        setError('Impossibile caricare i dati economici per questo paziente.')
      }
      setLoading(false)
    })
    return () => { live = false }
  }, [patient.name, center])

  if (loading) return <section className="detail-section patient-tab-payments"><p role="status">Caricamento situazione economica e pagamenti…</p></section>
  if (error) return <section className="detail-section patient-tab-payments"><p className="inline-error" role="alert">{error}</p></section>

  const operationalDebts = (position?.debts ?? []).filter(d => d.doctype === 'Patient Appointment')
  const unpaidSessionsCount = operationalDebts.length
  const operationalDebtTotal = operationalDebts.reduce((sum, d) => sum + (Number(d.amount) || 0), 0)
  const accountingResidual = project?.totals?.outstanding ?? null
  const isBlocked = position?.blocked ?? false

  const agreementLabel = !position?.agreement ? 'Standard (seduta per seduta)' :
    position.agreement.mode === 'Immediate' ? 'Pagamento immediato' :
    position.agreement.mode === 'Month End' ? 'Fine mese' :
    position.agreement.mode === 'Specific Date' ? `Data concordata (${displayDate(position.agreement.due_date)})` :
    position.agreement.mode

  return (
    <section className="detail-section patient-tab-payments">
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16, flexWrap: 'wrap', gap: 12 }}>
        <div>
          <h3 style={{ margin: 0, fontSize: 18 }}>Situazione economica e pagamenti</h3>
          <p className="scope-note" style={{ margin: '4px 0 0' }}>
            Accordo di pagamento: <strong>{agreementLabel}</strong>
          </p>
        </div>
        <Chip tone={isBlocked ? 'bad' : unpaidSessionsCount > 0 ? 'warn' : 'good'}>
          {isBlocked ? 'Blocco prenotazioni attivo' : unpaidSessionsCount > 0 ? `${unpaidSessionsCount} ${unpaidSessionsCount === 1 ? 'seduta da saldare' : 'sedute da saldare'}` : 'Posizione regolare'}
        </Chip>
      </div>

      <div className="metrics-grid" style={{ marginBottom: 20 }}>
        <Metric
          label="Sedute da saldare"
          value={unpaidSessionsCount}
          tone={unpaidSessionsCount > 0 ? 'amber' : 'green'}
        />
        <Metric
          label="Debito operativo"
          value={money(operationalDebtTotal, 'EUR')}
          tone={operationalDebtTotal > 0 ? 'amber' : 'green'}
        />
        <Metric
          label="Residuo contabile fatture"
          value={accountingResidual != null ? money(accountingResidual, 'EUR') : 'N/D'}
          tone={accountingResidual && accountingResidual > 0 ? 'amber' : 'blue'}
        />
        <Metric
          label="Stato prenotazioni"
          value={isBlocked ? 'Bloccato' : 'Autorizzato'}
          tone={isBlocked ? 'amber' : 'green'}
        />
      </div>

      <h3>Sedute da saldare e posizioni operative</h3>
      <p className="scope-note">
        Sedute svolte o addebitate in attesa di saldo o fatturazione nel centro.
      </p>
      {operationalDebts.length ? (
        <DataTable
          rows={operationalDebts as unknown as Row[]}
          columns={[
            { key: 'name', label: 'Riferimento seduta', render: v => <strong>{String(v)}</strong> },
            { key: 'amount', label: 'Importo', render: (v, r) => money(v, String(r.currency || 'EUR')) },
            { key: 'due_date', label: 'Scadenza', render: v => displayDate(v) },
            {
              key: 'override',
              label: 'Proroga',
              render: v => v ? <Chip tone="blue">Deroga autorizzata</Chip> : <span>Termine ordinario</span>
            }
          ]}
        />
      ) : (
        <Empty title="Nessuna seduta da saldare" detail="Tutte le sedute svolte risultano saldate o non addebitabili." />
      )}

      {project?.customer ? (
        <div className="customer-fiscal-banner" style={{ marginTop: 24 }}>
          <strong>Soggetto fiscale collegato:</strong> {project.customer_label || project.customer}
          <p>
            <strong>Residuo contabile complessivo:</strong> {money(project.totals?.outstanding ?? 0, 'EUR')} ({project.open_invoices?.length ?? 0} {project.open_invoices?.length === 1 ? 'fattura aperta' : 'fatture aperte'}).
            <br />
            Il residuo contabile è intestato formalmente al soggetto fiscale e non viene sommato o attribuito arbitrariamente al singolo paziente. I debiti operativi sopra indicati si riferiscono alle sedute svolte dal paziente non ancora saldate.
          </p>
          {project.open_invoices && project.open_invoices.length > 0 && (
            <div style={{ marginTop: 12 }}>
              <DataTable
                rows={project.open_invoices as unknown as Row[]}
                columns={[
                  { key: 'name', label: 'Fattura', render: v => <strong>{String(v)}</strong> },
                  { key: 'posting_date', label: 'Data', render: v => displayDate(v) },
                  { key: 'grand_total', label: 'Totale', render: (v, r) => money(v, String(r.currency || 'EUR')) },
                  { key: 'outstanding_amount', label: 'Residuo', render: (v, r) => <strong>{money(v, String(r.currency || 'EUR'))}</strong> },
                  { key: 'effective_due_date', label: 'Scadenza', render: v => displayDate(v) }
                ]}
              />
            </div>
          )}
        </div>
      ) : (
        <div className="customer-fiscal-banner" style={{ marginTop: 24 }}>
          <strong>Nessun soggetto fiscale collegato</strong>
          <p>
            Questo paziente non è associato a un soggetto fiscale cliente. I debiti operativi sono gestiti esclusivamente tramite le sedute.
          </p>
        </div>
      )}

      {onOpenReport && (
        <div style={{ marginTop: 24, paddingTop: 16, borderTop: '1px solid var(--border-subtle, #e2e8f0)' }}>
          <Button variant="secondary" onClick={() => onOpenReport(patient.name)}>
            Visualizza report dettagliato nel periodo →
          </Button>
        </div>
      )}
    </section>
  )
}
