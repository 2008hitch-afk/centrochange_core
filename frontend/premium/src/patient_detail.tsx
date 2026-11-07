import { useEffect, useRef, useState } from 'react'
import { type Boot, type FinanceBoot, type Patient, type Row, displayDate, money, ops, finance, requestKey, romeToday, time } from './api'
import { demoPatient, demoText, serviceLabel } from './demo_labels'
import { auditActorName, closureName, paymentMethodLabel, practitionerNameFor } from './display_names'
import { AppointmentTimeline } from './appointment_timeline'
import { NoteHistory } from './note_history'
import { PatientAssignments } from './patient_assignments'
import { PatientPackages } from './patient_packages'
import { saveArchive } from './scoped_api'
import { Button, Chip, Empty, Field, FormError, Modal, Metric, DataTable, type Feedback } from './ui'

type Profile = Row & { name: string; modified: string; first_name: string; last_name: string; email: string; mobile: string; phone: string; cc_ts_preference?: string | null; active_assignment: boolean; fiscal_customer?: string | null; fiscal_customer_label?: string | null; fiscal_payer_external?: boolean }
type History = { appointments: Row[]; truncated: boolean; settlements: Row[]; organizational_notes: Row[]; private_notes: Row[]; packages: Row[]; assignment_events?: Row[]; total_appointments?: number; page?: number; total_pages?: number }
const patientIdentityPart = (value: unknown) => { const text = String(value ?? '').trim(); return /^(?:CC-(?:HTTP|MVP-POS)-|SYNTHETIC[-_]|PAT-[A-Z0-9-]+$)/i.test(text) ? '' : text }
const tsPreferenceLabel = (value: unknown) => value === 'No Opposition' ? 'Non si oppone alla trasmissione' : value === 'Opposed' ? 'Si oppone alla trasmissione' : 'Informazione non registrata'
const errorText = (cause: unknown) => cause instanceof Error ? cause.message : 'Operazione non riuscita.'
const receiptMethodLabel = (value: unknown) => /^CC-MVP-POS-/i.test(String(value ?? '')) ? 'Carta POexport function PatientDetail({ boot, financeBoot, patient, center, feedback, initialTab, onOpenReport, onClose, onSuccess }: {
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
  const payerKey = useRef(requestKey())
  const [payerOpen,setPayerOpen] = useState(false)
  const [payerMode,setPayerMode] = useState<'self'|'existing'|'new'>('self')
  const [payerCustomer,setPayerCustomer] = useState('')
  const [payerSearch,setPayerSearch] = useState('')
  const [payerChoices,setPayerChoices] = useState<Array<{name:string;label:string;tax_hint?:string}>>([])
  const [payerFirst,setPayerFirst] = useState('')
  const [payerLast,setPayerLast] = useState('')
  const [payerTaxId,setPayerTaxId] = useState('')
  const [payerReason,setPayerReason] = useState('')
  const [payerBusy,setPayerBusy] = useState(false)
  const [payerError,setPayerError] = useState('')
  const [note, setNote] = useState('')
  const [notePrivate, setNotePrivate] = useState(false)
  const [corrects, setCorrects] = useState<string | null>(null)
  const [noteBusy, setNoteBusy] = useState(false)
  const [appointment, setAppointment] = useState<Row | null>(null)
  const [tsHistory, setTsHistory] = useState<Row[]>([])
  const [tsHistoryError, setTsHistoryError] = useState('')

  useEffect(() => {
    if (!payerOpen || payerMode !== 'existing') return
    let live = true
    ops<Array<{name:string;label:string;tax_hint?:string}>>('profiles.fiscal_payers',{center,search:payerSearch})
      .then(rows => {if(live) setPayerChoices(rows)})
      .catch(cause => {if(live) setPayerError(errorText(cause))})
    return () => {live = false}
  }, [center,payerOpen,payerMode,payerSearch])
  const canViewPayments = Boolean(
    financeBoot &&
    !boot.roles.includes('CC Professional') &&
    boot.roles.some(r => ['CC Manager', 'CC Secretariat', 'CC Finance', 'CC Accountant'].includes(r))
  )

  const [tab, setTab] = useState<'Riepilogo' | 'Sedute' | 'Assegnazioni' | 'Note' | 'Pacchetti' | 'Pagamenti'>(() => {
    if (initialTab === 'Pagamenti' && canViewPayments) return 'Pagamenti'
    if (initialTab === 'Assegnazioni') return initialTab
    return 'Riepilogo'
  })

  const tabs = canViewPayments
    ? (['Riepilogo', 'Assegnazioni', 'Pagamenti'] as const)
    : (['Riepilogo', 'Assegnazioni'] as const)

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
    if (!manager) return
    let live = true
    setTsHistory([]); setTsHistoryError('')
    ops<Row[]>('profiles.patient_ts_history', {center, name: patient.name}).then(rows => { if (!Array.isArray(rows)) throw new Error('Storico TS non disponibile'); if (live) setTsHistory(rows) }).catch(cause => { if (live) setTsHistoryError(errorText(cause)) })
    return () => { live = false }
  }, [center, patient.name, reload, manager])

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
  const savePayer = async () => {
    if (!profile || !payerReason.trim()) return
    setPayerBusy(true);setPayerError('')
    try {
      const fiscal = payerMode === 'existing' ? {payer_customer:payerCustomer}
        : payerMode === 'new' ? {payer_first_name:payerFirst,payer_last_name:payerLast,payer_tax_id:payerTaxId}
        : {}
      await ops('profiles.patient_fiscal_payer_save',{
        center,name:patient.name,payer_mode:payerMode,expected_version:profile.modified,
        request_key:payerKey.current,reason:payerReason.trim(),...fiscal
      },true)
      setPayerOpen(false);feedback('Intestatario fiscale aggiornato.');refresh()
    } catch(cause){setPayerError(errorText(cause))}
    finally{setPayerBusy(false)}
  }
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
      <h3>{serviceLabel(appointment.cc_service_label) || 'Seduta'}</h3>
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
    {profile && <section className="detail-section patient-tab-summary"><h3>Anagrafica</h3>{historical && <p className="scope-note" role="status">Nessuna assegnazione attiva in questo centro. La scheda è consultabile come storico; per riprendere le operazioni, registra una nuova assegnazione autorizzata.</p>}<dl className="property-list"><div><dt>Nome</dt><dd>{patientIdentityPart(profile.first_name) || '—'}</dd></div><div><dt>Cognome</dt><dd>{patientIdentityPart(profile.last_name) || '—'}</dd></div><div><dt>Email</dt><dd>{profile.email || '—'}</dd></div><div><dt>Telefono</dt><dd>{profile.phone || '—'}</dd></div><div><dt>Cellulare</dt><dd>{profile.mobile || '—'}</dd></div>{manager && <div><dt>Intestatario fiscale</dt><dd>{profile.fiscal_customer_label || 'Da collegare'}</dd></div>}{manager && <div><dt>Preferenza anagrafica Sistema Tessera Sanitaria</dt><dd>{tsPreferenceLabel(profile.cc_ts_preference)}</dd></div>}</dl>{manager && <p className="scope-note">La preferenza anagrafica non modifica le scelte registrate per singole spese e non attiva trasmissioni.</p>}{manager && <details><summary>Storico preferenza TS</summary>{tsHistoryError && <p className="inline-error" role="alert">{tsHistoryError}</p>}{tsHistory.map((event, index) => <p key={index}>{displayDate(event.event_time)} · {auditActorName(event.actor)}: {tsPreferenceLabel(event.before)} → {tsPreferenceLabel(event.after)}</p>)}{!tsHistoryError && !tsHistory.length && <p>Nessuna variazione registrata.</p>}</details>}{manager && !historical && <Button variant="secondary" onClick={() => { saveKey.current = requestKey(); setDraft({ ...profile, first_name: patientIdentityPart(profile.first_name), last_name: patientIdentityPart(profile.last_name) }); setReason(''); setError('') }}>Modifica scheda</Button>}{manager && !historical && <Button variant="secondary" onClick={() => {
  payerKey.current=requestKey();setPayerMode(profile.fiscal_payer_external?'existing':'self')
  setPayerCustomer(profile.fiscal_customer||'');setPayerReason('');setPayerError('');setPayerOpen(true)
}}>Modifica intestatario fiscale</Button>}</section>}
    {profile && history && <div className="patient-tab-assignments"><PatientAssignments boot={boot} patient={patient.name} center={center} feedback={feedback} onSuccess={refresh} /></div>}
    {history && <><section className="detail-section patient-tab-sessions"><h3>Sedute {history.total_appointments ? `(${history.total_appointments})` : ''}</h3>
      {history.total_pages && history.total_pages > 1 ? (
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center', marginBottom: '12px' }}>
          <Button variant="secondary" disabled={historyPage <= 1} onClick={() => setHistoryPage(p => Math.max(1, p - 1))}>Precedente</Button>
          <span style={{ fontSize: '13px', color: '#64748b' }}>Pagina {historyPage} di {history.total_pages}</span>
          <Button variant="secondary" disabled={historyPage >= history.total_pages} onClick={() => setHistoryPage(p => p + 1)}>Successiva</Button>
        </div>
      ) : null}
      {history.truncated && !history.total_pages && <p className="scope-note">Mostrate le prime 100 sedute.</p>}
      {history.appointments.length ? history.appointments.map(row => <button className="patient-history-item" type="button" data-appointment={String(row.name)} key={String(row.name)} onClick={event => openAppointment(row, event.currentTarget)}><strong>{displayDate(row.appointment_date)} · {time(row.appointment_time)} · {serviceLabel(row.cc_service_label) || 'Seduta'}</strong><small>{closureName(row.cc_closure_state)} · {practitionerNameFor(String(row.practitioner ?? ''), boot.practitioners, String(row.practitioner_name ?? ''))}</small><span>Apri eventi</span></button>) : <p className="scope-note">Nessuna seduta nel centro.</p>}</section>
      <section className="detail-section patient-tab-assignments"><h3>Assegnazioni: storico</h3>{history.assignment_events?.length ? <div className="timeline">{history.assignment_events.map((row, index) => <article key={index} className="note"><strong>{row.active ? 'Assegnazione attivata' : 'Assegnazione revocata'} · {practitionerNameFor(String(row.practitioner ?? ''), boot.practitioners)}</strong><small>{displayDate(row.event_time)}</small><details><summary>Dettagli dell’evento</summary><p>Operatore: {auditActorName(row.actor)}</p><p>Motivo: {String(row.reason ?? '—')}</p></details></article>)}</div> : <p className="scope-note">Nessun evento di assegnazione disponibile.</p>}</section>
      <section className="detail-section patient-tab-notes"><h3>Note organizzative</h3><NoteHistory rows={history.organizational_notes} onCorrect={historical ? undefined : row => correct(row, false)} />{professional && <><h3>Note professionali riservate</h3><NoteHistory rows={history.private_notes} privateNotes onCorrect={historical ? undefined : row => correct(row, true)} /></>}{!historical && <form onSubmit={event => { event.preventDefault(); void addNote() }}><h3>{corrects ? `Rettifica di una nota ${notePrivate ? 'professionale riservata' : 'organizzativa'}` : 'Nuova nota'}</h3>{!corrects && professional && <fieldset className="note-kind"><legend>Tipo di nota</legend><label><input type="radio" name="note-kind" checked={!notePrivate} onChange={() => setNotePrivate(false)} /> Organizzativa</label><label><input type="radio" name="note-kind" checked={notePrivate} onChange={() => setNotePrivate(true)} /> Professionale riservata</label></fieldset>}<p className="scope-note" role="status">{notePrivate ? 'La nota professionale è visibile soltanto al professionista autorizzato nel contesto del paziente.' : 'La nota organizzativa è visibile ai ruoli autorizzati nel centro.'} {corrects ? 'La rettifica conserva il tipo e la versione precedente nello storico.' : 'Dopo il salvataggio il testo non si modifica: eventuali correzioni si registrano come rettifiche.'}</p><Field label={corrects ? 'Testo della rettifica' : 'Testo della nota'} required><textarea value={note} onChange={event => setNote(event.target.value)} required maxLength={100000} /></Field><FormError error={error} /><div className="form-actions">{corrects && <Button type="button" variant="secondary" onClick={() => { setCorrects(null); setNote(''); setNotePrivate(false) }}>Annulla rettifica</Button>}<Button type="submit" disabled={noteBusy || !note.trim()}>{noteBusy ? 'Salvataggio…' : corrects ? 'Registra rettifica' : 'Aggiungi nota'}</Button></div></form>}</section>
      <div className="patient-tab-packages"><PatientPackages boot={boot} patient={patient.name} center={center} packages={history.packages} feedback={feedback} onSuccess={refresh} readOnly={historical} /></div>
    </>}
    {canViewPayments && <PatientPaymentsTab patient={patient} center={center} boot={boot} canWrite={Boolean(financeBoot?.can_write)} onOpenReport={onOpenReport} onOpenSession={(row, button) => openAppointment(row, button)} />}
    </>}
  </article>{draft && <Modal title="Modifica paziente" onClose={() => setDraft(null)}><form onSubmit={event => { event.preventDefault(); void save() }}><Field label="Nome" required><input required value={draft.first_name ?? ''} onChange={event => { saveKey.current = requestKey(); setDraft({ ...draft, first_name: event.target.value }) }} /></Field><Field label="Cognome"><input value={draft.last_name ?? ''} onChange={event => { saveKey.current = requestKey(); setDraft({ ...draft, last_name: event.target.value }) }} /></Field><Field label="Email"><input type="email" value={draft.email ?? ''} onChange={event => { saveKey.current = requestKey(); setDraft({ ...draft, email: event.target.value }) }} /></Field><Field label="Cellulare"><input type="tel" value={draft.mobile ?? ''} onChange={event => { saveKey.current = requestKey(); setDraft({ ...draft, mobile: event.target.value }) }} /></Field><Field label="Telefono"><input type="tel" value={draft.phone ?? ''} onChange={event => { saveKey.current = requestKey(); setDraft({ ...draft, phone: event.target.value }) }} /></Field><Field label="Preferenza anagrafica Sistema Tessera Sanitaria"><select value={draft.cc_ts_preference ?? ''} onChange={event => { saveKey.current = requestKey(); setDraft({ ...draft, cc_ts_preference: event.target.value }) }}><option value="">Informazione non registrata</option><option value="No Opposition">Non si oppone alla trasmissione</option><option value="Opposed">Si oppone alla trasmissione</option></select></Field><Field label="Motivo" required><textarea required maxLength={500} value={reason} onChange={event => { saveKey.current = requestKey(); setReason(event.target.value) }} /></Field><FormError error={error} /><div className="form-actions"><Button type="button" variant="secondary" onClick={() => setDraft(null)}>Annulla</Button><Button type="submit" disabled={saving}>{saving ? 'Salvataggio…' : 'Salva'}</Button></div></form></Modal>}{payerOpen && <Modal title="Intestatario fiscale" onClose={() => setPayerOpen(false)}><form onSubmit={e => {e.preventDefault();void savePayer()}}>
  <p className="scope-note">La modifica è consentita soltanto in assenza di appuntamenti o documenti economici già registrati.</p>
  <fieldset className="detail-section">
    <legend>Chi è l'intestatario fiscale?</legend>
    <label><input type="radio" name="edit-payer-mode" checked={payerMode==='self'} onChange={() => {setPayerMode('self');payerKey.current=requestKey()}} /> Il paziente stesso</label>
    <label><input type="radio" name="edit-payer-mode" checked={payerMode==='existing'} onChange={() => {setPayerMode('existing');payerKey.current=requestKey()}} /> Un'altra persona già registrata</label>
    <label><input type="radio" name="edit-payer-mode" checked={payerMode==='new'} onChange={() => {setPayerMode('new');payerKey.current=requestKey()}} /> Una nuova persona</label>
  </fieldset>
  {payerMode==='existing' && <>
    <Field label="Cerca intestatario"><input value={payerSearch} onChange={e => {setPayerSearch(e.target.value);payerKey.current=requestKey()}} /></Field>
    <Field label="Seleziona intestatario fiscale" required><select required value={payerCustomer} onChange={e => {setPayerCustomer(e.target.value);payerKey.current=requestKey()}}><option value="">Seleziona una persona</option>{payerChoices.map(row => <option value={row.name} key={row.name}>{row.label}{row.tax_hint?' · '+row.tax_hint:''}</option>)}</select></Field>
  </>}
  {payerMode==='new' && <>
    <Field label="Nome intestatario" required><input required maxLength={140} value={payerFirst} onChange={e => {setPayerFirst(e.target.value);payerKey.current=requestKey()}} /></Field>
    <Field label="Cognome intestatario" required><input required maxLength={140} value={payerLast} onChange={e => {setPayerLast(e.target.value);payerKey.current=requestKey()}} /></Field>
    <Field label="Identificativo fiscale intestatario" required><input required maxLength={50} value={payerTaxId} onChange={e => {setPayerTaxId(e.target.value);payerKey.current=requestKey()}} /></Field>
  </>}
  <Field label="Motivo della modifica" required><textarea required value={payerReason} onChange={e => {setPayerReason(e.target.value);payerKey.current=requestKey()}} maxLength={500} /></Field>
  <FormError error={payerError} />
  <div className="form-actions"><Button type="button" variant="secondary" onClick={() => setPayerOpen(false)}>Annulla</Button><Button type="submit" disabled={payerBusy || !payerReason.trim() || (payerMode==='existing'&&!payerCustomer) || (payerMode==='new'&&(!payerFirst.trim()||!payerLast.trim()||!payerTaxId.trim()))}>{payerBusy?'Salvataggio…':'Salva intestatario'}</Button></div>
</form></Modal>}</>
}

type="submit" disabled={saving}>{saving ? 'Salvataggio…' : 'Salva'}</Button></div></form></Modal>}</>
}

function PatientPaymentsTab({ patient, center, boot, canWrite, onOpenReport, onOpenSession }: {
  patient: Patient; center: string; boot: Boot; canWrite: boolean; onOpenReport?: (patientId?: string) => void; onOpenSession: (row: Row, button: HTMLButtonElement) => void
}) {
  const [position, setPosition] = useState<{
    blocked: boolean;
    debts: Array<{
      doctype: string;
      name: string;
      amount: number;
      currency: string;
      due_date?: string;
      appointment_date?: string;
      service_label?: string;
      invoice_draft?: boolean;
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
  const [reload, setReload] = useState(0)
  const [recording, setRecording] = useState(false)
  const [amounts, setAmounts] = useState<Record<string, string>>({})
  const [method, setMethod] = useState('')
  const [date, setDate] = useState(romeToday())
  const [reason, setReason] = useState('')
  const [saving, setSaving] = useState(false)
  const [receiptError, setReceiptError] = useState('')
  const [receipts, setReceipts] = useState<Array<{name: string; receipt_date: string; creation?: string; mode_of_payment: string; reason: string; actor: string; reversed: boolean; allocations: Array<{cents: number; appointment?: string; appointment_date?: string; service_label?: string; session?: Row; reversal_of?: string}>}>>([])
  const [receiptDetail, setReceiptDetail] = useState<{receipt: typeof receipts[number]; index: number} | null>(null)
  const [historyError, setHistoryError] = useState(false)
  const [correcting, setCorrecting] = useState('')
  const [correctionReason, setCorrectionReason] = useState('')
  const correctionKey = useRef(requestKey())
  const receiptKey = useRef(requestKey())

  useEffect(() => {
    let live = true
    setLoading(true); setError('')
    const now = new Date()
    const start = `${now.getFullYear()}-01-01`
    const end = `${now.getFullYear()}-12-31`
    Promise.allSettled([
      finance<typeof position>('collections.position', { patient: patient.name, center }),
      finance<typeof project>('patient_reporting.patient_view', { center, start, end, patient: patient.name }),
      finance<typeof receipts>('operational_receipts.history', { center, patient: patient.name })
    ]).then(([posRes, projRes, receiptRes]) => {
      if (!live) return
      const validPosition = posRes.status === 'fulfilled' && posRes.value && typeof posRes.value.blocked === 'boolean' && Array.isArray(posRes.value.debts) && posRes.value.debts.every(debt => debt && typeof debt.name === 'string' && debt.name.length > 0 && typeof debt.currency === 'string' && debt.currency.length > 0 && (typeof debt.amount === 'number' || typeof (debt.amount as unknown) === 'string' && String(debt.amount).trim() !== '') && Number.isFinite(Number(debt.amount)) && Number(debt.amount) >= 0)
      if (validPosition && posRes.status === 'fulfilled') setPosition(posRes.value)
      if (projRes.status === 'fulfilled') setProject(projRes.value)
      if (receiptRes.status === 'fulfilled') { setReceipts(receiptRes.value); setHistoryError(false) }
      else { setReceipts([]); setHistoryError(true) }
      if (!validPosition) {
        setError('Impossibile caricare i dati economici per questo paziente.')
      }
      setLoading(false)
    })
    return () => { live = false }
  }, [patient.name, center, reload])

  if (loading) return <section className="detail-section patient-tab-payments"><p role="status">Caricamento situazione economica e pagamenti…</p></section>
  if (error) return <section className="detail-section patient-tab-payments"><p className="inline-error" role="alert">{error}</p></section>

  const operationalDebts = (position?.debts ?? []).filter(d => d.doctype === 'Patient Appointment')
  const unpaidSessionsCount = operationalDebts.length
  const operationalDebtTotal = operationalDebts.reduce((sum, d) => sum + (Number(d.amount) || 0), 0)
  const accountingResidual = project?.totals?.outstanding ?? null
  const isBlocked = position?.blocked ?? false
  const latestReceipt = [...receipts].filter(r => !r.allocations[0]?.reversal_of && !r.reversed).sort((a, b) => b.receipt_date.localeCompare(a.receipt_date) || String(b.creation ?? '').localeCompare(String(a.creation ?? '')))[0]

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
          label="Da incassare"
          value={money(operationalDebtTotal, 'EUR')}
          tone={operationalDebtTotal > 0 ? 'amber' : 'green'}
        />
        <Metric
          label="Ultimo incasso"
          value={historyError ? 'Non disponibile' : latestReceipt ? money(latestReceipt.allocations.reduce((sum, item) => sum + item.cents, 0) / 100, 'EUR') : 'Nessuno'}
          tone="blue"
        />
        <Metric
          label="Stato prenotazioni"
          value={isBlocked ? 'Bloccato' : 'Autorizzato'}
          tone={isBlocked ? 'amber' : 'green'}
        />
      </div>

      {canWrite && operationalDebts.some(d => !d.invoice_draft) && <Button onClick={() => setRecording(true)}>Registra incasso</Button>}
      {recording && <form className="action-form" onSubmit={event => {
        event.preventDefault(); setSaving(true); setReceiptError('')
        const allocations = operationalDebts.filter(d => !d.invoice_draft && Number(amounts[d.name]) > 0).map(d => ({ appointment: d.name, amount: amounts[d.name] }))
        finance('operational_receipts.record', { patient: patient.name, center, receipt_date: date, mode_of_payment: method, reason, request_key: receiptKey.current, allocations }, true)
          .then(() => { receiptKey.current = requestKey(); setAmounts({}); setReason(''); setRecording(false); setReload(n => n + 1) })
          .catch(e => setReceiptError(errorText(e))).finally(() => setSaving(false))
      }}><h3>Registra incasso</h3><p>Indica l’importo ricevuto per ogni seduta. Puoi registrare un pagamento parziale.</p>
        {operationalDebts.map(d => <Field key={d.name} label={`Seduta del ${displayDate(d.appointment_date)} · residuo ${money(d.amount, d.currency)}`}><input type="number" disabled={d.invoice_draft} title={d.invoice_draft ? 'Seduta collegata a una bozza di fattura: verifica la posizione contabile.' : undefined} min="0" max={d.amount} step="0.01" value={amounts[d.name] || ''} onChange={e => setAmounts({...amounts, [d.name]: e.target.value})} /></Field>)}
        <Field label="Data incasso" required><input type="date" required value={date} onChange={e => setDate(e.target.value)} /></Field>
        <Field label="Metodo" required><select required value={method} onChange={e => setMethod(e.target.value)}><option value="">Seleziona</option>{boot.payment_methods.map(m => <option key={m} value={m}>{m}</option>)}</select></Field>
        <Field label="Causale" required><textarea required value={reason} onChange={e => setReason(e.target.value)} maxLength={2000} /></Field>
        <FormError error={receiptError} /><div className="form-actions"><Button type="button" variant="secondary" onClick={() => setRecording(false)}>Annulla</Button><Button disabled={saving} type="submit">{saving ? 'Registrazione…' : 'Conferma incasso'}</Button></div>
      </form>}
      {historyError && <p className="inline-error" role="alert">Impossibile caricare i movimenti di pagamento. Riprova.</p>}
      {receipts.length > 0 && <><h3>Movimenti di pagamento</h3><div className="table-wrap"><table><thead><tr><th>Data</th><th>Servizio / seduta</th><th>Importo</th><th>Metodo</th><th>Dettaglio</th></tr></thead><tbody>{receipts.flatMap(r => r.allocations.map((item, index) => <tr key={`${r.name}-${index}`}><td>{displayDate(r.receipt_date)}</td><td><strong>{serviceLabel(item.service_label) || 'Seduta'}</strong><br /><small>{item.appointment_date ? displayDate(item.appointment_date) : 'Data non disponibile'}</small>{item.session && <button type="button" className="patient-back" onClick={event => onOpenSession(item.session!, event.currentTarget)}>Vai alla seduta</button>}</td><td>{money(item.cents / 100)}{item.reversal_of ? <small>Rettifica</small> : r.reversed ? <small>Incasso rettificato</small> : null}</td><td>{receiptMethodLabel(r.mode_of_payment)}</td><td><Button type="button" variant="secondary" onClick={() => setReceiptDetail({receipt:r, index})}>Visualizza</Button></td></tr>))}</tbody></table></div>{receiptDetail && <Modal title="Dettaglio incasso" onClose={() => setReceiptDetail(null)}><div className="receipt-detail"><p>{receiptDetail.receipt.allocations[receiptDetail.index].reversal_of ? 'Rettifica del registro, non un rimborso' : receiptDetail.receipt.reversed ? 'Incasso rettificato' : 'Incasso'}</p><p>Riferimento: {receiptDetail.receipt.name}</p><p>Operatore: {auditActorName(receiptDetail.receipt.actor)}</p><p>Causale: {receiptDetail.receipt.reason}</p>{receiptDetail.receipt.allocations[receiptDetail.index].reversal_of && <p>Incasso originale: {receiptDetail.receipt.allocations[receiptDetail.index].reversal_of}</p>}{canWrite && !receiptDetail.receipt.reversed && !receiptDetail.receipt.allocations[receiptDetail.index].reversal_of && receiptDetail.index === 0 && <Button type="button" variant="secondary" onClick={() => { setCorrecting(receiptDetail.receipt.name); setReceiptDetail(null); setCorrectionReason(''); setReceiptError('') }}>Rettifica incasso</Button>}</div></Modal>}{receipts.map(r => correcting === r.name && <form key={r.name} className="action-form" onSubmit={event => { event.preventDefault(); setSaving(true); setReceiptError(''); finance('operational_receipts.reverse', {patient: patient.name, center, receipt: r.name, reason: correctionReason, request_key: correctionKey.current}, true).then(() => { correctionKey.current = requestKey(); setCorrecting(''); setReload(n => n + 1) }).catch(e => setReceiptError(errorText(e))).finally(() => setSaving(false)) }}><p>La rettifica annulla l’intera registrazione e ripristina i residui. Non effettua un rimborso.</p><Field label="Motivo della rettifica" required><textarea required maxLength={2000} value={correctionReason} onChange={e => setCorrectionReason(e.target.value)} /></Field><FormError error={receiptError} /><div className="form-actions"><Button type="button" variant="secondary" onClick={() => setCorrecting('')}>Annulla</Button><Button type="submit" disabled={saving}>Conferma rettifica</Button></div></form>)}</>}
      <h3>Sedute da saldare e posizioni operative</h3>
      <p className="scope-note">
        Sedute svolte o addebitate in attesa di saldo o fatturazione nel centro.
      </p>
      {operationalDebts.length ? (
        <DataTable
          rows={operationalDebts as unknown as Row[]}
          columns={[
            { key: 'appointment_date', label: 'Seduta', render: (v, r) => <strong>{displayDate(v)} · {serviceLabel(r.service_label) || 'Seduta'}</strong> },
            { key: 'amount', label: 'Importo', render: (v, r) => <>{money(v, String(r.currency || 'EUR'))}{r.invoice_draft ? ' · Bozza fattura da verificare' : ''}</> },
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
