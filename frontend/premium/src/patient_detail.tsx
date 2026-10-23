import { useEffect, useRef, useState } from 'react'
import { type Boot, type Patient, type Row, displayDate, ops, requestKey, time } from './api'
import { demoPatient, demoText } from './demo_labels'
import { auditActorName, closureName, practitionerNameFor } from './display_names'
import { AppointmentTimeline } from './appointment_timeline'
import { NoteHistory } from './note_history'
import { PatientAssignments } from './patient_assignments'
import { PatientPackages } from './patient_packages'
import { saveArchive } from './scoped_api'
import { Button, Chip, Drawer, Empty, Field, FormError, Modal, type Feedback } from './ui'

type Profile = Row & { name: string; modified: string; first_name: string; last_name: string; email: string }
type History = { appointments: Row[]; truncated: boolean; settlements: Row[]; organizational_notes: Row[]; private_notes: Row[]; packages: Row[]; assignment_events?: Row[] }
const errorText = (cause: unknown) => cause instanceof Error ? cause.message : 'Operazione non riuscita.'

export function PatientDetail({ boot, patient, center, feedback, onClose, onSuccess }: {
  boot: Boot; patient: Patient; center: string; feedback: Feedback; onClose: () => void; onSuccess: () => void
}) {
  const [profile, setProfile] = useState<Profile | null>(null)
  const [history, setHistory] = useState<History | null>(null)
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
  const [events, setEvents] = useState<Row[] | null>(null)
  const manager = boot.roles.includes('CC Manager')
  const professional = boot.roles.includes('CC Professional')

  useEffect(() => {
    let live = true
    setLoading(true); setError(''); setHistory(null); setProfile(null); setAppointment(null)
    Promise.all([
      ops<Profile>('profiles.patient_detail', { center, name: patient.name }),
      ops<History>('workspace.patient_history', { center, patient: patient.name })
    ]).then(([record, activity]) => { if (live) { setProfile(record); setHistory(activity) } })
      .catch(cause => { if (live) setError(errorText(cause)) })
      .finally(() => { if (live) setLoading(false) })
    return () => { live = false }
  }, [center, patient.name, reload])

  useEffect(() => {
    if (!appointment) return
    let live = true
    setEvents(null)
    ops<Row[]>('workspace.appointment_events', { appointment: appointment.name })
      .then(result => { if (live) setEvents(result) })
      .catch(cause => { if (live) { setEvents([]); setError(errorText(cause)) } })
    return () => { live = false }
  }, [appointment])

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
      setNote(''); setCorrects(null); feedback(corrects ? 'Rettifica registrata.' : 'Nota registrata.'); refresh()
    } catch (cause) { setError(errorText(cause)); feedback(errorText(cause), true) }
    finally { setNoteBusy(false) }
  }
  const correct = (row: Row, privateNote: boolean) => { setCorrects(String(row.name)); setNote(String(row.content ?? '')); setNotePrivate(privateNote) }

  return <><Drawer title={demoPatient(patient.name, patient.patient_name)} onClose={onClose}>
    <div className="detail-summary"><Chip tone="blue">Paziente</Chip><h3>{demoPatient(patient.name, patient.patient_name)}</h3></div>
    {loading && <p role="status">Caricamento scheda paziente…</p>}
    {error && <p className="inline-error" role="alert">{error}</p>}
    {profile && <section className="detail-section"><h3>Anagrafica</h3><dl className="property-list"><div><dt>Nome</dt><dd>{profile.first_name || '—'}</dd></div><div><dt>Cognome</dt><dd>{profile.last_name || '—'}</dd></div><div><dt>Email</dt><dd>{profile.email || '—'}</dd></div></dl>{manager && <Button variant="secondary" onClick={() => { saveKey.current = requestKey(); setDraft({ ...profile }); setReason(''); setError('') }}>Modifica scheda</Button>}</section>}
    {history && <><section className="detail-section"><h3>Sedute</h3>{history.truncated && <p className="scope-note">Mostrate le ultime 100 sedute.</p>}{history.appointments.length ? history.appointments.map(row => <button className="patient-history-item" type="button" key={String(row.name)} onClick={() => setAppointment(row)}><strong>{displayDate(row.appointment_date)} · {time(row.appointment_time)} · {demoText(row.cc_service_label) || 'Seduta'}</strong><small>{closureName(row.cc_closure_state)} · {practitionerNameFor(String(row.practitioner ?? ''), boot.practitioners, String(row.practitioner_name ?? ''))}</small><span>Apri eventi</span></button>) : <p className="scope-note">Nessuna seduta nel centro.</p>}{appointment && <><h4>Eventi della seduta del {displayDate(appointment.appointment_date)}</h4>{events ? <AppointmentTimeline rows={events} /> : <p role="status">Caricamento eventi…</p>}</>}</section>
      <section className="detail-section"><h3>Assegnazioni: storico</h3>{history.assignment_events?.length ? <div className="timeline">{history.assignment_events.map((row, index) => <article key={index} className="note"><strong>{row.active ? 'Assegnazione attivata' : 'Assegnazione revocata'} · {practitionerNameFor(String(row.practitioner ?? ''), boot.practitioners)}</strong><small>{displayDate(row.event_time)} · {auditActorName(row.actor)}</small><p>Motivo: {String(row.reason ?? '—')}</p></article>)}</div> : <p className="scope-note">Nessun evento di assegnazione disponibile.</p>}</section>
      <section className="detail-section"><h3>Note organizzative</h3><NoteHistory rows={history.organizational_notes} onCorrect={row => correct(row, false)} />{professional && <><h3>Note professionali riservate</h3><NoteHistory rows={history.private_notes} privateNotes onCorrect={row => correct(row, true)} /></>}<form onSubmit={event => { event.preventDefault(); void addNote() }}><Field label={corrects ? 'Rettifica nota' : 'Nuova nota organizzativa'} required><textarea value={note} onChange={event => setNote(event.target.value)} required maxLength={100000} /></Field>{professional && <label className="checkbox-row"><input type="checkbox" checked={notePrivate} onChange={event => { setNotePrivate(event.target.checked); setCorrects(null) }} /> Nota professionale riservata</label>}<FormError error={error} /><Button type="submit" disabled={noteBusy || !note.trim()}>{noteBusy ? 'Salvataggio…' : corrects ? 'Registra rettifica' : 'Aggiungi nota'}</Button></form></section>
      <PatientPackages boot={boot} patient={patient.name} center={center} packages={history.packages} feedback={feedback} onSuccess={refresh} />
    </>}
    <PatientAssignments boot={boot} patient={patient.name} center={center} feedback={feedback} />
  </Drawer>{draft && <Modal title="Modifica paziente" onClose={() => setDraft(null)}><form onSubmit={event => { event.preventDefault(); void save() }}><Field label="Nome" required><input required value={draft.first_name ?? ''} onChange={event => { saveKey.current = requestKey(); setDraft({ ...draft, first_name: event.target.value }) }} /></Field><Field label="Cognome"><input value={draft.last_name ?? ''} onChange={event => { saveKey.current = requestKey(); setDraft({ ...draft, last_name: event.target.value }) }} /></Field><Field label="Email"><input type="email" value={draft.email ?? ''} onChange={event => { saveKey.current = requestKey(); setDraft({ ...draft, email: event.target.value }) }} /></Field><Field label="Motivo" required><textarea required maxLength={500} value={reason} onChange={event => { saveKey.current = requestKey(); setReason(event.target.value) }} /></Field><FormError error={error} /><div className="form-actions"><Button type="button" variant="secondary" onClick={() => setDraft(null)}>Annulla</Button><Button type="submit" disabled={saving}>{saving ? 'Salvataggio…' : 'Salva'}</Button></div></form></Modal>}</>
}
