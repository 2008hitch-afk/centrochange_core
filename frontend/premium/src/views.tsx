import React, { useEffect, useMemo, useRef, useState } from 'react'
import { Calendar, dayjsLocalizer, Views } from 'react-big-calendar'
import dayjs from 'dayjs'
import 'dayjs/locale/it'
import { Plus, ChevronLeft, ChevronRight, RefreshCw, Filter, Download, CalendarDays, Check, Search, ArrowRight, UserRound, Clock3 } from 'lucide-react'
import { type Appointment, type Boot, type FinanceBoot, type Patient, type Row, ops, finance, schedule, call, requestKey, romeToday, displayDate, money, time } from './api'
import { type Feedback, Button, Chip, DataTable, DateInput, Drawer, Empty, Field, FormError, Heading, Metric, Modal, SearchableSelect, dateColumn, moneyColumn, useAction } from './ui'
import { FinanceActions } from './finance_actions'
import { FinanceCreate } from './finance_create'
import { ProfessionalWorkflow } from './professional_workflow'
import { PatientAssignments } from './patient_assignments'
import { PatientPackages } from './patient_packages'
import { FinanceReports } from './finance_reports'
import { financeFieldLabel, financeFieldValue } from './finance_locale'
import { NoteHistory } from './note_history'

dayjs.locale('it')
const localizer = dayjsLocalizer(dayjs)
const iso = (d: Date) => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
const wallDate = (date: string, clock = '00:00') => { const [y, m, d] = date.slice(0, 10).split('-').map(Number); const [h, min] = clock.slice(0, 5).split(':').map(Number); return new Date(y, m - 1, d, h || 0, min || 0) }
const fullName = (row: Appointment) => row.patient_name || row.patient
type Context = { boot: Boot; center: string; feedback: Feedback }
const monthLabel = (date: Date) => new Intl.DateTimeFormat('it-IT', { month: 'long', year: 'numeric', timeZone: 'Europe/Rome' }).format(date)
const getError = (e: unknown) => e instanceof Error ? e.message : 'Caricamento non riuscito.'
const csvUrl = (method: string, params: Row) => '/api/method/centrochange_core.' + method + '?' + new URLSearchParams(Object.entries(params).map(([k, v]) => [k, String(v ?? '')]))

export function Agenda({ boot, center, feedback, refreshBoot }: Context & { refreshBoot: () => Promise<void> }) {
  const [date, setDate] = useState(() => wallDate(romeToday(), '12:00'))
  const [mode, setMode] = useState<'day' | 'week'>('day')
  const [rows, setRows] = useState<Appointment[]>([])
  const [selected, setSelected] = useState<Appointment | null>(null)
  const [booking, setBooking] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [practitioner, setPractitioner] = useState('all')
  const [reload, setReload] = useState(0)
  const start = mode === 'week' ? dayjs(date).subtract((date.getDay() + 6) % 7, 'day').toDate() : date
  const end = mode === 'week' ? dayjs(start).add(6, 'day').toDate() : date
  useEffect(() => {
    if (!center) return
    let live = true; setLoading(true); setError('')
    ops<{ appointments: Appointment[]; truncated: boolean }>('workspace.agenda', { center, start: iso(start), end: iso(end) }).then(data => {
      if (!live) return; setRows(data.appointments); if (data.truncated) setError('Più di 200 sedute: restringi il periodo.'); setLoading(false)
    }).catch(e => { if (live) { setError(getError(e)); setLoading(false) } })
    return () => { live = false }
  }, [center, iso(start), iso(end), reload])
  const resources = boot.practitioners.filter(p => practitioner === 'all' || p.name === practitioner).map(p => ({ id: p.name, title: p.practitioner_name }))
  const events = rows.filter(r => practitioner === 'all' || r.practitioner === practitioner).map(r => ({ id: r.name, title: `${time(r.appointment_time)}  ${fullName(r)} · ${r.cc_service_label || 'Seduta'}`, start: wallDate(r.appointment_date, r.appointment_time), end: dayjs(wallDate(r.appointment_date, r.appointment_time)).add(Number(r.duration || 60), 'minute').toDate(), resourceId: r.practitioner, row: r }))
  const visitCount = rows.length
  const completed = rows.filter(r => !!r.cc_performed).length
  const step = (n: number) => setDate(dayjs(date).add(n * (mode === 'week' ? 7 : 1), 'day').toDate())
  const refresh = () => { setSelected(null); setBooking(false); setReload(x => x + 1); void refreshBoot() }
  return <><Heading eyebrow="IL TUO SPAZIO DI LAVORO" title="Agenda" subtitle={`${displayDate(iso(start))}${mode === 'week' ? ' – ' + displayDate(iso(end)) : ''}  ·  ${monthLabel(date)}`} action={<Button onClick={() => setBooking(true)}><Plus size={18} /> Nuova prenotazione</Button>} />
    <div className="metrics-grid"><Metric label="Sedute nel periodo" value={visitCount} tone="blue" /><Metric label="Sedute svolte" value={completed} tone="green" /><Metric label="Da completare" value={visitCount - completed} tone="amber" /><Metric label="Professionisti" value={resources.length} tone="purple" /></div>
    <section className="panel calendar-panel"><div className="panel-toolbar"><div className="toolbar-left"><div className="segmented"><button className={mode === 'day' ? 'selected' : ''} onClick={() => setMode('day')}>Giorno</button><button className={mode === 'week' ? 'selected' : ''} onClick={() => setMode('week')}>Settimana</button></div><button className="icon-button bordered" title="Precedente" aria-label="Periodo precedente" onClick={() => step(-1)}><ChevronLeft /></button><button className="icon-button bordered" title="Successivo" aria-label="Periodo successivo" onClick={() => step(1)}><ChevronRight /></button><Button variant="secondary" onClick={() => setDate(wallDate(romeToday(), '12:00'))}>Oggi</Button></div><div className="toolbar-right"><label className="select-wrap"><Filter size={16} /><select value={practitioner} onChange={e => setPractitioner(e.target.value)} aria-label="Professionista"><option value="all">Tutti i professionisti</option>{boot.practitioners.map(p => <option key={p.name} value={p.name}>{p.practitioner_name}</option>)}</select></label><button className="icon-button bordered" title="Aggiorna" aria-label="Aggiorna agenda" onClick={() => setReload(x => x + 1)}><RefreshCw /></button></div></div>
      {error && <p className="inline-error" role="alert">{error}</p>}
      {loading ? <div className="calendar-loading" role="status">Caricamento agenda…</div> : !resources.length ? <Empty title="Nessun professionista disponibile" detail="Verifica l'assegnazione al centro selezionato." /> : <div className="calendar-wrap"><Calendar localizer={localizer} culture="it" events={events} resources={mode === 'day' ? resources : undefined} resourceIdAccessor="id" resourceTitleAccessor="title" view={mode === 'day' ? Views.DAY : Views.WEEK} date={date} onNavigate={setDate} onView={v => setMode(v === Views.WEEK ? 'week' : 'day')} toolbar={false} popup selectable min={wallDate(iso(date), '07:00')} max={wallDate(iso(date), '21:00')} step={30} timeslots={2} startAccessor="start" endAccessor="end" onSelectEvent={e => setSelected(e.row)} onSelectSlot={slot => { setDate(slot.start); setBooking(true) }} eventPropGetter={e => ({ className: e.row.status === 'Cancelled' ? 'event-cancelled' : e.row.cc_performed ? 'event-done' : 'event-booked' })} messages={{ noEventsInRange: 'Nessuna seduta nel periodo', showMore: count => `+ ${count} altre`, allDay: 'Tutto il giorno' }} /></div>}
    </section>{booking && <Booking boot={boot} center={center} onClose={() => setBooking(false)} onSuccess={refresh} feedback={feedback} date={iso(date)} />}{selected && <AppointmentDetail row={selected} boot={boot} center={center} onClose={() => setSelected(null)} onSuccess={refresh} feedback={feedback} />}</>
}

function Booking({ boot, center, onClose, onSuccess, feedback, date }: { boot: Boot; center: string; onClose: () => void; onSuccess: () => void; feedback: Feedback; date: string }) {
  const keys = useRef<Record<string, string>>({})
  const [patient, setPatient] = useState(boot.patients[0]?.name ?? '')
  const [practitioner, setPractitioner] = useState(boot.practitioners[0]?.name ?? '')
  const [service, setService] = useState(boot.services[0]?.name ?? '')
  const [day, setDay] = useState(date)
  const [clock, setClock] = useState('09:00')
  const [reason, setReason] = useState('')
  const [packageName, setPackageName] = useState('')
  const { busy, error, run } = useAction(feedback, onSuccess)
  const packages = boot.packages.filter(r => r.patient === patient && r.service_item === boot.services.find(s => s.name === service)?.cc_service_item && (!r.practitioner || r.practitioner === practitioner) && Number(r.available) > 0)
  const submit = () => {
    const payload = { patient, practitioner, center, appointment_type: service, appointment_date: day, appointment_time: clock, patient_package: packageName || null, reason }
    const key = JSON.stringify(payload)
    return run(() => schedule('booking.book', { ...payload, request_key: keys.current[key] ??= requestKey() }, true), 'Prenotazione registrata.')
  }
  return <Modal title="Nuova prenotazione" onClose={onClose}><form onSubmit={e => { e.preventDefault(); void submit() }}><div className="form-grid"><SearchableSelect label="Paziente" options={boot.patients.map(p => ({ value: p.name, label: p.patient_name }))} value={patient} onChange={setPatient} required /><SearchableSelect label="Professionista" options={boot.practitioners.map(p => ({ value: p.name, label: p.practitioner_name }))} value={practitioner} onChange={setPractitioner} required /><SearchableSelect label="Servizio" options={boot.services.map(s => ({ value: s.name, label: s.cc_service_label || s.name }))} value={service} onChange={setService} required /><SearchableSelect label="Pacchetto" options={packages.map(p => ({ value: String(p.name), label: `${String(p.label)} · ${String(p.available)} disponibili` }))} value={packageName} onChange={setPackageName} empty="Nessun pacchetto" /><Field label="Data" required><DateInput value={day} onChange={setDay} required /></Field><Field label="Ora" required><input type="time" value={clock} onChange={e => setClock(e.target.value)} required /></Field></div><Field label="Motivo" required><textarea value={reason} onChange={e => setReason(e.target.value)} required maxLength={2000} rows={3} /></Field><FormError error={error} /><div className="form-actions"><Button type="button" variant="secondary" onClick={onClose}>Annulla</Button><Button disabled={busy || !patient || !practitioner || !service} type="submit">{busy ? 'Salvataggio…' : 'Conferma prenotazione'}</Button></div></form></Modal>
}

function AppointmentDetail({ row, boot, center, onClose, onSuccess, feedback }: { row: Appointment; boot: Boot; center: string; onClose: () => void; onSuccess: () => void; feedback: Feedback }) {
  const [tab, setTab] = useState<'Seduta' | 'Storico' | 'Note'>('Seduta')
  const [history, setHistory] = useState<Row | null>(null)
  const [action, setAction] = useState('')
  const [reason, setReason] = useState('')
  const [moveDate, setMoveDate] = useState(row.appointment_date)
  const [moveTime, setMoveTime] = useState(time(row.appointment_time))
  const [paid, setPaid] = useState(Boolean(row.cc_paid))
  const [paymentMethod, setPaymentMethod] = useState(boot.payment_methods[0] ?? '')
  const [note, setNote] = useState('')
  const [privateNote, setPrivateNote] = useState(false)
  const [corrects, setCorrects] = useState<string | null>(null)
  const { busy, error, run } = useAction(feedback, onSuccess)
  useEffect(() => { if (tab !== 'Seduta') ops<Row>('workspace.patient_history', { patient: row.patient, center }).then(setHistory).catch(e => feedback(getError(e), true)) }, [tab, row.patient, center])
  const administrative = boot.roles.some(r => ['CC Manager', 'CC Secretariat'].includes(r))
  const finalized = ['Closed', 'Auto Locked'].includes(row.cc_closure_state ?? '')
  const mutable = !finalized && !['Cancelled', 'No Show'].includes(row.status)
  const actions = [
    ...(mutable && (row.status !== 'Closed' || row.cc_closure_state === 'Reopened') ? [{ id: 'close', label: 'Chiudi seduta' }, { id: 'move', label: 'Sposta' }] : []),
    ...(mutable && !row.cc_performed ? [{ id: 'cancel', label: 'Cancella' }] : []),
    ...(administrative && finalized ? [{ id: 'reopen', label: 'Riapri' }] : []),
    ...(administrative && ['Due', 'Package Covered'].includes(row.cc_economic_state ?? '') ? [{ id: 'waive', label: 'Rinuncia economica' }] : [])
  ]
  const submit = async () => {
    const args = action === 'move' ? { appointment: row.name, appointment_date: moveDate, appointment_time: moveTime, reason } : action === 'close' ? { appointment: row.name, paid: paid ? 1 : 0, mode_of_payment: paid ? paymentMethod : null, reason } : { appointment: row.name, reason }
    const method = action === 'move' ? schedule : ops
    const name = action === 'move' ? 'booking.reschedule' : `lifecycle.${action}`
    if (await run(() => method(name, args, true))) setAction('')
  }
  const entries = (key: string) => Array.isArray(history?.[key]) ? history[key] as Row[] : []
  return <Drawer title={fullName(row)} onClose={onClose}><div className="detail-summary"><Chip tone={row.status === 'Cancelled' ? 'bad' : row.cc_performed ? 'good' : 'blue'}>{row.status === 'Cancelled' ? 'Cancellata' : row.cc_performed ? 'Svolta' : 'Prenotata'}</Chip><h3>{row.cc_service_label || 'Seduta'}</h3><p><CalendarDays size={16} /> {displayDate(row.appointment_date)} · {time(row.appointment_time)}</p><p><UserRound size={16} /> {row.practitioner_name}</p><p><Clock3 size={16} /> {row.duration} min · {money(row.cc_price_snapshot, row.cc_currency_snapshot || 'EUR')}</p></div><div className="detail-tabs" role="tablist">{(['Seduta', 'Storico', 'Note'] as const).map(t => <button key={t} role="tab" aria-selected={tab === t} onClick={() => setTab(t)}>{t}</button>)}</div>
    {tab === 'Seduta' && <><div className="detail-section"><h3>Stato operativo</h3><p>Chiusura: {row.cc_closure_state || '—'}<br />Economia: {row.cc_economic_state || '—'}</p><div className="action-grid">{actions.map(a => <Button key={a.id} variant={a.id === 'close' ? 'primary' : a.id === 'cancel' ? 'danger' : 'secondary'} onClick={() => setAction(a.id)}>{a.label}</Button>)}</div></div>{action && <form className="action-form" onSubmit={e => { e.preventDefault(); void submit() }}><h3>{actions.find(a => a.id === action)?.label}</h3>{action === 'move' && <div className="form-grid"><Field label="Nuova data"><DateInput value={moveDate} onChange={setMoveDate} required /></Field><Field label="Nuova ora"><input type="time" value={moveTime} onChange={e => setMoveTime(e.target.value)} required /></Field></div>}{action === 'close' && <><label className="checkbox-row"><input type="checkbox" checked={paid} onChange={e => setPaid(e.target.checked)} /> Pagata</label>{paid && <Field label="Metodo di pagamento" required><select value={paymentMethod} onChange={e => setPaymentMethod(e.target.value)} required>{boot.payment_methods.map(p => <option key={p}>{p}</option>)}</select></Field>}</>}<Field label="Motivo" required><textarea value={reason} onChange={e => setReason(e.target.value)} required maxLength={2000} /></Field><FormError error={error} /><div className="form-actions"><Button type="button" variant="secondary" onClick={() => setAction('')}>Annulla</Button><Button disabled={busy} type="submit">{busy ? 'Salvataggio…' : 'Conferma'}</Button></div></form>}</>}
    {tab === 'Storico' && <div className="detail-section"><h3>Storico sedute</h3>{!history ? <p>Caricamento…</p> : <div className="timeline">{entries('appointments').map((a, i) => <article key={i}><strong>{displayDate(a.appointment_date)} · {String(a.cc_service_label ?? 'Seduta')}</strong><span>{String(a.cc_closure_state ?? '—')} · {String(a.cc_economic_state ?? '—')}</span></article>)}</div>}<h3>Pacchetti</h3>{entries('packages').map((p, i) => <p key={i}>{String(p.label)} · Residue: {String(p.remaining)}</p>)}</div>}
    {tab === 'Note' && <div className="detail-section"><h3>Note organizzative</h3><NoteHistory rows={entries('organizational_notes')} onCorrect={n => { setNote(String(n.content ?? '')); setPrivateNote(false); setCorrects(String(n.name)) }} />{boot.roles.includes('CC Professional') && <><h3>Note riservate</h3><NoteHistory rows={entries('private_notes')} privateNotes onCorrect={n => { setNote(String(n.content ?? '')); setPrivateNote(true); setCorrects(String(n.name)) }} /></>}<form onSubmit={e => { e.preventDefault(); void run(() => ops('notes.add_note', { patient: row.patient, center, content: note, private: privateNote ? 1 : 0, corrects }, true), 'Nota registrata.').then(ok => { if (ok) { setNote(''); setCorrects(null); setHistory(null); void ops<Row>('workspace.patient_history', { patient: row.patient, center }).then(setHistory) } }) }}><Field label={corrects ? "Rettifica nota" : "Nuova nota"}><textarea required value={note} onChange={e => setNote(e.target.value)} maxLength={100000} /></Field>{boot.roles.includes('CC Professional') && <label className="checkbox-row"><input type="checkbox" checked={privateNote} onChange={e => setPrivateNote(e.target.checked)} /> Nota professionale riservata</label>}<FormError error={error} /><Button disabled={busy || !note} type="submit">{corrects ? "Registra rettifica" : "Aggiungi nota"}</Button></form></div>}
  </Drawer>
}

export function Patients({ boot, center, query, feedback, refreshBoot }: Context & { query: string; refreshBoot: () => Promise<void> }) {
  const [search, setSearch] = useState(query)
  const [rows, setRows] = useState<Patient[]>(boot.patients)
  const [selected, setSelected] = useState<Patient | null>(null)
  const [history, setHistory] = useState<Row | null>(null)
  const [historyReload, setHistoryReload] = useState(0)
  const [error, setError] = useState('')
  useEffect(() => { setSearch(query) }, [query])
  useEffect(() => { if (!center) return; let live = true; ops<{ patients: Patient[] }>('workspace.patient_search', { center, query: search }).then(r => { if (live) { setRows(r.patients); setError('') } }).catch(e => { if (live) setError(getError(e)) }); return () => { live = false } }, [center, search])
  useEffect(() => { if (!selected) return; let live = true; setHistory(null); ops<Row>('workspace.patient_history', { patient: selected.name, center }).then(r => { if (live) setHistory(r) }).catch(e => feedback(getError(e), true)); return () => { live = false } }, [selected, center, historyReload])
  return <><Heading eyebrow="PERCORSO PAZIENTE" title="Pazienti" subtitle="Cerca, consulta e segui il percorso operativo nel centro." /><section className="panel"><div className="panel-toolbar"><div className="panel-title"><h2>Elenco pazienti</h2><p>{rows.length} {rows.length === 1 ? "risultato" : "risultati"} nel centro selezionato</p></div><label className="search-inline"><Search size={17} /><input placeholder="Cerca per nome o codice" aria-label="Cerca pazienti" value={search} onChange={e => setSearch(e.target.value)} /></label></div>{error && <p className="inline-error">{error}</p>}<DataTable rows={rows as unknown as Row[]} columns={[{ key: 'patient_name', label: 'Paziente', render: v => <strong>{String(v)}</strong> }, { key: 'name', label: 'Codice' }, { key: 'name', label: '', render: () => <ArrowRight size={17} /> }]} onRow={r => setSelected(r as Patient)} /></section>{selected && <Drawer title={selected.patient_name} onClose={() => setSelected(null)}><div className="detail-summary"><Chip tone="blue">Paziente</Chip><h3>{selected.patient_name}</h3><p>Codice: {selected.name}</p></div>{!history ? <p className="detail-section">Caricamento storico…</p> : <div className="detail-section"><h3>Sedute</h3>{(history.appointments as Row[] ?? []).map((a, i) => <article className="note" key={i}><strong>{displayDate(a.appointment_date)} · {String(a.cc_service_label ?? 'Seduta')}</strong><small>{String(a.cc_closure_state ?? '—')}</small></article>)}<h3>Note organizzative</h3><NoteHistory rows={history.organizational_notes as Row[] ?? []} /></div>}<PatientPackages boot={boot} patient={selected.name} center={center} packages={history?.packages as Row[] ?? []} feedback={feedback} onSuccess={() => { setHistoryReload(n => n + 1); void refreshBoot() }} /><PatientAssignments boot={boot} patient={selected.name} center={center} feedback={feedback} /></Drawer>}</>
}

export function ServiceCatalog({ boot, center }: { boot: Boot; center: string }) {
  const [query, setQuery] = useState('')
  const [selected, setSelected] = useState<(typeof boot.services)[number] | null>(null)
  const search = query.trim().toLocaleLowerCase('it-IT')
  const services = boot.services.filter(service => `${service.cc_service_label ?? ''} ${service.name}`.toLocaleLowerCase('it-IT').includes(search))
  return <><Heading eyebrow="OPERATIVITÀ" title="Servizi e professionisti" subtitle="Servizi disponibili nel centro selezionato e professionisti associati." />
    <section className="panel"><div className="panel-toolbar"><div className="panel-title"><h2>Servizi del centro</h2><p>{center} · {services.length} {services.length === 1 ? "servizio" : "servizi"} · tariffe e durata dallo snapshot del catalogo autorizzato.</p></div><label className="search-inline"><Search size={17} /><input type="search" value={query} onChange={e => setQuery(e.target.value)} aria-label="Cerca servizi" placeholder="Cerca servizio" /></label></div><DataTable rows={services as unknown as Row[]} columns={[{ key: 'cc_service_label', label: 'Servizio', render: (value, row) => <strong>{String(value || row.name)}</strong> }, { key: 'duration', label: 'Durata', render: value => value == null ? 'Da definire' : `${String(value)} min` }, { key: 'cc_price_snapshot', label: 'Tariffa', render: (value, row) => money(value, String(row.cc_currency_snapshot || 'EUR')) }]} onRow={row => setSelected(row as typeof selected)} /></section>
    <section className="panel catalog-practitioners"><div className="panel-toolbar"><div className="panel-title"><h2>Professionisti</h2><p>Associati al centro secondo le appartenenze e lo stato correnti del backend.</p></div></div><div className="schedule-grid">{boot.practitioners.map(practitioner => <article className="schedule-card" key={practitioner.name}><span className="avatar">{practitioner.practitioner_name.slice(0, 2).toLocaleUpperCase('it-IT')}</span><h3>{practitioner.practitioner_name}</h3><Chip tone="good">Attivo nel centro</Chip></article>)}</div>{!boot.practitioners.length && <Empty title="Nessun professionista attivo" />}</section>
    {selected && <Drawer title={selected.cc_service_label || selected.name} onClose={() => setSelected(null)}><div className="detail-summary"><Chip tone="blue">Servizio disponibile</Chip><h3>{selected.cc_service_label || selected.name}</h3><p>Centro: {center}</p></div><div className="detail-section"><h3>Scheda servizio</h3><dl className="property-list"><div><dt>Codice</dt><dd>{selected.name}</dd></div><div><dt>Articolo canonico</dt><dd>{selected.cc_service_item || '—'}</dd></div><div><dt>Durata</dt><dd>{selected.duration == null ? 'Da definire' : `${selected.duration} min`}</dd></div><div><dt>Tariffa corrente per prenotazione</dt><dd>{money(selected.cc_price_snapshot, selected.cc_currency_snapshot || 'EUR')}</dd></div></dl><p className="scope-note">Tariffa corrente del catalogo autorizzato. Le sedute già prenotate conservano il proprio snapshot; questa scheda non modifica Item, Item Price o Appointment Type.</p></div></Drawer>}
  </>
}

export function Availability({ boot, center, feedback }: Context) {
  const [rows, setRows] = useState<Row[]>([])
  const [loading, setLoading] = useState(true)
  const [form, setForm] = useState<'schedule' | 'absence' | null>(null)
  const [practitioner, setPractitioner] = useState(boot.practitioners[0]?.name ?? '')
  const [weekday, setWeekday] = useState('Monday')
  const [startTime, setStartTime] = useState('09:00')
  const [endTime, setEndTime] = useState('12:00')
  const [startDate, setStartDate] = useState(romeToday())
  const [endDate, setEndDate] = useState(romeToday())
  const [reason, setReason] = useState('')
  const [reload, setReload] = useState(0)
  const { busy, error, run } = useAction(feedback, () => { setForm(null); setReload(x => x + 1) })
  useEffect(() => { if (!center) return; let live = true; setLoading(true); ops<Row[]>('workspace.schedules', { center }).then(r => { if (live) { setRows(r); setLoading(false) } }).catch(e => { if (live) { feedback(getError(e), true); setLoading(false) } }); return () => { live = false } }, [center, reload])
  const days = [['Monday', 'Lunedì'], ['Tuesday', 'Martedì'], ['Wednesday', 'Mercoledì'], ['Thursday', 'Giovedì'], ['Friday', 'Venerdì'], ['Saturday', 'Sabato'], ['Sunday', 'Domenica']]
  return <><Heading eyebrow="OPERATIVITÀ" title="Disponibilità" subtitle="Orari ricorrenti e assenze dei professionisti." action={<div className="button-group"><Button variant="secondary" onClick={() => setForm('absence')}>Registra assenza</Button><Button onClick={() => setForm('schedule')}><Plus size={18} /> Modifica orario</Button></div>} /><section className="panel"><div className="panel-toolbar"><div className="panel-title"><h2>Orari del centro</h2><p>La modifica sostituisce l'orario ricorrente indicato.</p></div></div>{loading ? <p className="panel-loading">Caricamento…</p> : !rows.length ? <Empty title="Nessun orario configurato" /> : <div className="schedule-grid">{rows.map((r, i) => <article className="schedule-card" key={i}><span className="avatar">{String(boot.practitioners.find(p => p.name === r.practitioner)?.practitioner_name ?? r.practitioner).slice(0, 2).toUpperCase()}</span><h3>{boot.practitioners.find(p => p.name === r.practitioner)?.practitioner_name ?? String(r.practitioner)}</h3>{(r.time_slots as Row[] ?? []).map((s, j) => <p key={j}><span>{days.find(d => d[0] === s.day)?.[1] ?? String(s.day)}</span><strong>{time(s.from_time)} – {time(s.to_time)}</strong></p>)}{(r.absences as Row[] ?? []).length > 0 && <Chip tone="warn">{(r.absences as Row[]).length} assenze</Chip>}</article>)}</div>}</section>{form && <Modal title={form === 'schedule' ? 'Modifica disponibilità' : 'Registra assenza'} onClose={() => setForm(null)}><form onSubmit={e => { e.preventDefault(); const args = form === 'schedule' ? { practitioner, center, time_slots: [{ day: weekday, from_time: startTime, to_time: endTime }], reason } : { practitioner, center, start_date: startDate, end_date: endDate, start_time: startTime, end_time: endTime, reason }; void run(() => schedule(`availability.${form === 'schedule' ? 'set_schedule' : 'create_absence'}`, args, true)) }}><Field label="Professionista" required><select value={practitioner} onChange={e => setPractitioner(e.target.value)}>{boot.practitioners.map(p => <option key={p.name} value={p.name}>{p.practitioner_name}</option>)}</select></Field>{form === 'schedule' ? <Field label="Giorno" required><select value={weekday} onChange={e => setWeekday(e.target.value)}>{days.map(d => <option key={d[0]} value={d[0]}>{d[1]}</option>)}</select></Field> : <div className="form-grid"><Field label="Dal" required><DateInput value={startDate} onChange={setStartDate} required /></Field><Field label="Al" required><DateInput value={endDate} onChange={setEndDate} required /></Field></div>}<div className="form-grid"><Field label="Dalle" required><input type="time" value={startTime} onChange={e => setStartTime(e.target.value)} /></Field><Field label="Alle" required><input type="time" value={endTime} onChange={e => setEndTime(e.target.value)} /></Field></div><Field label="Motivo" required><textarea required value={reason} onChange={e => setReason(e.target.value)} maxLength={2000} /></Field><FormError error={error} /><div className="form-actions"><Button type="button" variant="secondary" onClick={() => setForm(null)}>Annulla</Button><Button type="submit" disabled={busy}>Conferma</Button></div></form></Modal>}</>
}

export function Reports({ center, feedback }: Context) {
  const [start, setStart] = useState(dayjs(romeToday()).startOf('month').format('YYYY-MM-DD'))
  const [end, setEnd] = useState(romeToday())
  const [data, setData] = useState<Row | null>(null)
  const [loading, setLoading] = useState(true)
  useEffect(() => { if (!center) return; let live = true; setLoading(true); ops<Row>('reporting.summary', { center, start, end }).then(r => { if (live) { setData(r); setLoading(false) } }).catch(e => { if (live) { feedback(getError(e), true); setLoading(false) } }); return () => { live = false } }, [center, start, end])
  const currencies = data?.currencies as Record<string, Row> ?? {}
  return <><Heading eyebrow="OPERATIVITÀ" title="Report" subtitle="Andamento delle sedute e dati operativi del centro." action={<a className="button secondary" href={csvUrl('operations.reporting.export_csv', { center, start, end })} aria-disabled={loading || !!data?.truncated} onClick={e => { if (loading || data?.truncated) e.preventDefault() }}><Download size={17} /> Esporta CSV</a>} /><section className="panel"><div className="panel-toolbar"><div className="panel-title"><h2>Riepilogo operativo</h2><p>Pagamenti operativi distinti dal saldo contabile. I valori restano separati per valuta.</p></div><div className="toolbar-right"><Field label="Dal"><DateInput value={start} onChange={setStart} required /></Field><Field label="Al"><DateInput value={end} onChange={setEnd} required /></Field></div></div>{loading ? <p className="panel-loading">Caricamento…</p> : !Object.keys(currencies).length ? <Empty title="Nessun dato nel periodo" /> : Object.entries(currencies).map(([currency, r]) => <div className="report-currency" key={currency}><h3>{currency === 'UNSET' ? 'Valuta da verificare' : currency}</h3><div className="metrics-grid inset"><Metric label="Sedute" value={String(r.sessions ?? 0)} /><Metric label="Svolte" value={String(r.performed ?? 0)} tone="green" /><Metric label="Pagate operativamente" value={String(r.operational_paid ?? 0)} tone="green" /><Metric label="Con economia dovuta" value={String(r.due ?? 0)} tone="amber" /><Metric label="Valore dovuto" value={currency === 'UNSET' ? 'Da verificare' : money(r.due_snapshot_amount, currency)} tone="purple" /></div></div>)}{Boolean(data?.truncated) && <p className="inline-error" role="alert">Totali parziali: restringi il periodo. L'esportazione è sospesa.</p>}</section></>
}

type FinanceTab = 'Riepilogo' | 'Fatture pazienti' | 'XML ricevuti' | 'Fatture fornitori' | 'Banca' | 'Professionisti' | 'Coda amministrativa' | 'SdI' | 'TS'
const financeTabs: FinanceTab[] = ['Riepilogo', 'Fatture pazienti', 'XML ricevuti', 'Fatture fornitori', 'Banca', 'Professionisti', 'Coda amministrativa', 'SdI', 'TS']
const financeDoctype: Partial<Record<FinanceTab, string>> = { 'Fatture pazienti': 'Sales Invoice', 'XML ricevuti': 'CC Incoming Invoice', 'Fatture fornitori': 'Purchase Invoice', Banca: 'Bank Transaction', Professionisti: 'CC Professional Expectation' }
export function FinanceView({ boot, center, feedback }: { boot: FinanceBoot; center: string; feedback: Feedback }) {
  const [tab, setTab] = useState<FinanceTab>('Riepilogo')
  const [createOpen, setCreateOpen] = useState(false)
  const [start, setStart] = useState(dayjs(romeToday()).startOf('month').format('YYYY-MM-DD'))
  const [end, setEnd] = useState(romeToday())
  const [data, setData] = useState<Row | Row[] | null>(null)
  const [selected, setSelected] = useState<Row | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [reload, setReload] = useState(0)
  useEffect(() => {
    if (!center) return
    let live = true; setLoading(true); setData(null); setError('')
    let task: Promise<Row | Row[]>
    if (tab === 'Riepilogo') task = finance<Row>('reporting.summary', { center, start, end })
    else if (tab === 'Coda amministrativa') task = finance<Row[]>('admin_queue.list_items', { center })
    else if (tab === 'SdI' || tab === 'TS') task = finance<Row[]>('fiscal.records', { center, domain: tab === 'SdI' ? 'SDI' : 'TS' })
    else task = finance<Row[]>('reporting.records', { center, doctype: financeDoctype[tab] })
    task.then(r => { if (live) { setData(r); setLoading(false) } }).catch(e => { if (live) { setError(getError(e)); setLoading(false) } })
    return () => { live = false }
  }, [center, tab, start, end, reload])
  const summary = tab === 'Riepilogo' && data && !Array.isArray(data) ? data as Row : null
  const totals = summary?.totals as Row | undefined
  const rows = Array.isArray(data) ? data : []
  const columns: Record<FinanceTab, { key: string; label: string; render?: (v: unknown, row: Row) => React.ReactNode }[]> = {
    Riepilogo: [],
    'Fatture pazienti': [{ key: 'name', label: 'Documento' }, { key: 'posting_date', label: 'Data', render: displayDate }, { key: 'customer', label: 'Cliente' }, { key: 'grand_total', label: 'Importo', render: v => money(v) }, { key: 'outstanding_amount', label: 'Residuo', render: v => money(v) }],
    'XML ricevuti': [{ key: 'invoice_number', label: 'Documento' }, { key: 'state', label: 'Stato', render: v => financeFieldValue('state', v) }, { key: 'supplier', label: 'Fornitore' }, { key: 'total', label: 'Importo', render: v => money(v) }, { key: 'problem', label: 'Da verificare' }],
    'Fatture fornitori': [{ key: 'name', label: 'Documento' }, { key: 'posting_date', label: 'Data', render: displayDate }, { key: 'supplier', label: 'Fornitore' }, { key: 'grand_total', label: 'Importo', render: v => money(v) }, { key: 'outstanding_amount', label: 'Residuo', render: v => money(v) }],
    Banca: [{ key: 'date', label: 'Data', render: displayDate }, { key: 'reference_number', label: 'Riferimento' }, { key: 'deposit', label: 'Entrata', render: v => money(v) }, { key: 'withdrawal', label: 'Uscita', render: v => money(v) }, { key: 'unallocated_amount', label: 'Da riconciliare', render: v => money(v) }],
    Professionisti: [{ key: 'appointment_label', label: 'Seduta' }, { key: 'practitioner', label: 'Professionista' }, { key: 'state', label: 'Stato', render: v => financeFieldValue('state', v) }, { key: 'amount', label: 'Atteso', render: v => money(v) }, { key: 'problem', label: 'Da verificare' }],
    'Coda amministrativa': [{ key: 'exception_type', label: 'Condizione' }, { key: 'reference_name', label: 'Fonte' }, { key: 'state', label: 'Stato', render: v => financeFieldValue('state', v) }, { key: 'priority', label: 'Priorità' }, { key: 'assignee', label: 'Responsabile' }],
    SdI: [{ key: 'reference_name', label: 'Documento' }, { key: 'direction', label: 'Direzione', render: v => financeFieldValue('direction', v) }, { key: 'status', label: 'Stato', render: v => financeFieldValue('status', v) }, { key: 'attempt_count', label: 'Tentativi' }, { key: 'error_class', label: 'Esito' }],
    TS: [{ key: 'reference_name', label: 'Fonte spesa' }, { key: 'status', label: 'Stato', render: v => financeFieldValue('status', v) }, { key: 'attempt_count', label: 'Tentativi' }, { key: 'error_class', label: 'Da verificare' }]
  }
  const createable = boot.can_write && ['Fatture pazienti', 'XML ricevuti', 'Banca', 'Coda amministrativa', 'SdI', 'TS'].includes(tab)
  return <><Heading eyebrow="CONTROLLO FINANZIARIO" title="Finanza" subtitle="Contabilità e amministrazione del centro, dai sistemi Frappe ed ERPNext." action={<div className="button-group"><a className="button secondary" href={csvUrl('finance.reporting.export_csv', { center, start, end })}><Download size={17} /> Esporta CSV</a>{tab === 'Riepilogo' && <FinanceReports boot={boot} center={center} start={start} end={end} feedback={feedback} />}{boot.can_write && tab === 'Professionisti' && <ProfessionalWorkflow boot={boot} center={center} feedback={feedback} onSuccess={() => setReload(x => x + 1)} />}{createable && <Button onClick={() => setCreateOpen(true)}><Plus size={17} /> Nuova operazione</Button>}</div>} /><div className="finance-status"><Chip tone={boot.simulation_only ? 'warn' : 'good'}>{boot.simulation_only ? 'Ambiente simulato' : 'Ambiente'}</Chip><span>Solo dati autorizzati del centro selezionato · Nessun invio a provider reali</span></div><div className="tab-nav" role="tablist" aria-label="Aree finanza">{financeTabs.map(t => <button key={t} role="tab" aria-selected={tab === t} onClick={() => { setTab(t); setSelected(null) }}>{t}</button>)}</div>
    <section className="panel finance-panel"><div className="panel-toolbar"><div className="panel-title"><h2>{tab === 'Riepilogo' ? 'Panoramica finanziaria' : tab}</h2><p>{tab === 'Riepilogo' ? 'Valori registrati; margine da definire secondo regole approvate.' : 'Elenco circoscritto al centro selezionato.'}</p></div>{tab === 'Riepilogo' && <div className="toolbar-right"><Field label="Dal"><DateInput value={start} onChange={setStart} required /></Field><Field label="Al"><DateInput value={end} onChange={setEnd} required /></Field></div>}</div>{error && <p className="inline-error" role="alert">{error}</p>}{loading ? <p className="panel-loading" role="status">Caricamento…</p> : summary ? <><div className="metrics-grid inset"><Metric label="Ricavi netti" value={money(totals?.revenue_net)} /><Metric label="Incassato" value={money(totals?.collected)} tone="green" /><Metric label="Crediti residui" value={money(totals?.receivable_outstanding)} tone="amber" /><Metric label="Costi fornitori" value={money(totals?.purchase_net)} tone="purple" /></div><div className="finance-secondary"><div><span>Debito residuo</span><strong>{money(totals?.payable_outstanding)}</strong></div><div><span>Compensi attesi</span><strong>{money(totals?.expected_compensation)}</strong></div><div><span>Attesi da verificare</span><strong>{String(totals?.unresolved_expectations ?? 0)}</strong></div><div><span>Sedute</span><strong>{String(totals?.sessions ?? 0)}</strong></div></div><div className="summary-tables"><div><h3>Fatture pazienti</h3><DataTable rows={(summary.sales_invoices as Row[] ?? []).slice(0, 5)} columns={[{ key: 'name', label: 'Documento' }, { key: 'customer', label: 'Cliente' }, moneyColumn('outstanding_amount', 'Residuo')]} /></div><div><h3>Fatture fornitori</h3><DataTable rows={(summary.purchase_invoices as Row[] ?? []).slice(0, 5)} columns={[{ key: 'name', label: 'Documento' }, { key: 'supplier', label: 'Fornitore' }, moneyColumn('outstanding_amount', 'Residuo')]} /></div></div><p className="scope-note">Le date di registrazione regolano la contabilità; le date delle sedute regolano l’operatività. I ricavi pazienti includono il pagatore fiscale condiviso. Le fatture fornitori sono totali fiscali del fornitore, senza attribuzione dedotta ai singoli professionisti. Il margine resta da definire secondo regole approvate.</p></> : <DataTable rows={rows} columns={columns[tab]} onRow={setSelected} />}</section>{selected && <FinanceDetail row={selected} tab={tab} center={center} canWrite={boot.can_write} assignees={boot.assignees ?? []} accounts={boot.accounts ?? []} suppliers={boot.suppliers ?? []} items={boot.items ?? []} feedback={feedback} onClose={() => setSelected(null)} onChange={() => { setSelected(null); setReload(x => x + 1) }} />}{createOpen && <FinanceCreate tab={tab} center={center} feedback={feedback} start={start} end={end} onClose={() => setCreateOpen(false)} onSuccess={() => { setCreateOpen(false); setReload(x => x + 1) }} />}</>
}

function FinanceDetail({ row, tab, center, canWrite, assignees, accounts, suppliers, items, feedback, onClose, onChange }: { row: Row; tab: FinanceTab; center: string; canWrite: boolean; assignees: string[]; accounts: Row[]; suppliers: Row[]; items: Row[]; feedback: Feedback; onClose: () => void; onChange: () => void }) {
  const [detail, setDetail] = useState<Row | null>(null)
  const [reason, setReason] = useState('')
  const [action, setAction] = useState(false)
  const [priority, setPriority] = useState(Number(row.priority ?? 2))
  const [assignee, setAssignee] = useState(String(row.assignee ?? ''))
  const [dueAt, setDueAt] = useState('')
  const [deferUntil, setDeferUntil] = useState('')
  const { busy, error, run } = useAction(feedback, onChange)
  useEffect(() => { let live = true; const name = String(row.name ?? ''); const method = tab === 'Fatture pazienti' ? 'receivables.position' : tab === 'Fatture fornitori' ? 'incoming.position' : tab === 'Professionisti' ? 'professional_economics.position' : null; if (method) finance<Row>(method, tab === 'Professionisti' ? { center, practitioner: row.practitioner } : { name }).then(r => { if (live) setDetail(r) }).catch(e => feedback(getError(e), true)); return () => { live = false } }, [row, tab, center])
  const title = String(row.invoice_number ?? row.name ?? row.reference_name ?? row.exception_type ?? 'Dettaglio')
  return <Drawer title={title} onClose={onClose}><div className="detail-summary"><Chip tone={String(row.state ?? row.status).includes('Error') ? 'bad' : 'blue'}>{financeFieldValue('state', row.state ?? row.status ?? tab)}</Chip><h3>{title}</h3><p>Centro: {center}</p></div><div className="detail-section"><h3>Informazioni</h3><dl className="property-list">{Object.entries(row).filter(([k]) => !['name', 'problem'].includes(k)).map(([k, v]) => <div key={k}><dt>{financeFieldLabel(k)}</dt><dd>{financeFieldValue(k, v)}</dd></div>)}</dl>{detail && <><h3>Posizione</h3><dl className="property-list">{Object.entries(detail).filter(([, v]) => !Array.isArray(v) && typeof v !== 'object').map(([k, v]) => <div key={k}><dt>{financeFieldLabel(k)}</dt><dd>{financeFieldValue(k, v)}</dd></div>)}</dl></>}{Boolean(row.problem) && <p className="inline-error">{String(row.problem)}</p>}{canWrite && tab === 'Coda amministrativa' && <><Button variant="secondary" onClick={() => setAction(true)}>Gestisci condizione</Button>{action && <form onSubmit={e => { e.preventDefault(); void run(() => finance('admin_queue.manage', { name: row.name, priority, assignee: assignee || null, due_at: dueAt ? dueAt.replace('T', ' ') : null, defer_until: deferUntil ? deferUntil.replace('T', ' ') : null, reason }, true)) }}><Field label="Priorità" required><select value={priority} onChange={e => setPriority(Number(e.target.value))}>{[1, 2, 3, 4].map(n => <option key={n} value={n}>{n}</option>)}</select></Field><Field label="Assegnatario"><select value={assignee} onChange={e => setAssignee(e.target.value)}><option value="">Nessuno</option>{assignees.map(u => <option key={u} value={u}>{u}</option>)}</select></Field><Field label="Scadenza UTC"><input type="datetime-local" value={dueAt} onChange={e => setDueAt(e.target.value)} /></Field><Field label="Rinvio fino a UTC"><input type="datetime-local" value={deferUntil} onChange={e => setDeferUntil(e.target.value)} /></Field><Field label="Motivo" required><textarea value={reason} onChange={e => setReason(e.target.value)} required /></Field><FormError error={error} /><Button disabled={busy} type="submit">Conferma</Button></form>}</>}</div><FinanceActions row={row} tab={tab} center={center} canWrite={canWrite} accounts={accounts} suppliers={suppliers} items={items} feedback={feedback} onChange={onChange} /></Drawer>
}

export function Access({ center, feedback }: Context) {
  const [data, setData] = useState<Row | null>(null)
  const [form, setForm] = useState<'membership' | 'practitioner' | null>(null)
  const [user, setUser] = useState('')
  const [practitioner, setPractitioner] = useState('')
  const [active, setActive] = useState('1')
  const [reason, setReason] = useState('')
  const [reload, setReload] = useState(0)
  const { busy, error, run } = useAction(feedback, () => { setForm(null); setReload(x => x + 1) })
  useEffect(() => {
    if (!center) return
    let live = true
    ops<Row>('workspace.management_context', { center }).then(r => { if (live) setData(r) }).catch(e => feedback(getError(e), true))
    return () => { live = false }
  }, [center, reload])
  const users = data?.users as Row[] ?? []
  const practitioners = data?.practitioners as Row[] ?? []
  const submit = () => form === 'membership'
    ? call('security.lifecycle.set_membership', { user, center, active, reason }, true)
    : call('security.lifecycle.set_practitioner_state', { practitioner, active, reason }, true)
  return <><Heading eyebrow="AMMINISTRAZIONE" title="Gestione accessi" subtitle="Utenti e appartenenze al centro. Ogni modifica passa dal servizio con audit." action={<div className="button-group"><Button variant="secondary" onClick={() => setForm('practitioner')}>Stato professionista</Button><Button onClick={() => setForm('membership')}><Plus size={17} /> Appartenenza</Button></div>} />
    <section className="panel"><div className="panel-toolbar"><div className="panel-title"><h2>Appartenenze</h2><p>Stato degli utenti nel centro selezionato.</p></div></div>{!data ? <p className="panel-loading">Caricamento…</p> : <DataTable rows={data.memberships as Row[] ?? []} columns={[{ key: 'user', label: 'Utente' }, { key: 'active', label: 'Stato', render: v => <Chip tone={v ? 'good' : 'neutral'}>{v ? 'Attivo' : 'Disattivo'}</Chip> }]} />}</section>
    {form && <Modal title={form === 'membership' ? 'Appartenenza al centro' : 'Stato professionista'} onClose={() => setForm(null)}><form onSubmit={e => { e.preventDefault(); void run(submit) }}>
      {form === 'membership' ? <Field label="Utente" required><select value={user} onChange={e => setUser(e.target.value)} required><option value="">Seleziona</option>{users.map(u => <option key={String(u.name)} value={String(u.name)}>{String(u.full_name ?? u.name)}</option>)}</select></Field> : <Field label="Professionista" required><select value={practitioner} onChange={e => setPractitioner(e.target.value)} required><option value="">Seleziona</option>{practitioners.map(p => <option key={String(p.name)} value={String(p.name)}>{String(p.practitioner_name ?? p.name)}</option>)}</select></Field>}
      <Field label="Stato" required><select value={active} onChange={e => setActive(e.target.value)}><option value="1">Attivo</option><option value="0">Disattivo</option></select></Field>
      <Field label="Motivo" required><textarea value={reason} onChange={e => setReason(e.target.value)} required maxLength={2000} /></Field><FormError error={error} /><div className="form-actions"><Button type="button" variant="secondary" onClick={() => setForm(null)}>Annulla</Button><Button type="submit" disabled={busy}>Conferma</Button></div>
    </form></Modal>}</>
}

export function Notifications({ center }: { center: string; feedback: Feedback }) {
  const [rows, setRows] = useState<Row[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [reload, setReload] = useState(0)
  useEffect(() => { let live = true; setLoading(true); setRows([]); setError(''); call<Row[]>('frappe.client.get_list', { doctype: 'CC Notification', fields: ['name', 'message', 'state', 'creation'], limit_page_length: 100, order_by: 'creation desc' }).then(r => { if (live) { setRows(r); setLoading(false) } }).catch(e => { if (live) { setError(getError(e)); setLoading(false) } }); return () => { live = false } }, [center, reload])
  return <><Heading eyebrow="CENTRO CHANGE" title="Notifiche" subtitle="Esiti e comunicazioni operative." /><section className="panel"><div className="panel-toolbar"><div className="panel-title"><h2>Notifiche recenti</h2></div></div>{loading ? <p className="panel-loading" role="status">Caricamento notifiche…</p> : error ? <div className="notification-error" role="alert"><p>{error}</p><Button variant="secondary" onClick={() => setReload(n => n + 1)}>Riprova</Button></div> : rows.length ? <DataTable rows={rows} columns={[{ key: 'message', label: 'Messaggio' }, { key: 'state', label: 'Stato' }, dateColumn('creation', 'Data')]} /> : <Empty title="Nessuna notifica recente" detail="Le comunicazioni del centro appariranno qui." />}</section></>
}
