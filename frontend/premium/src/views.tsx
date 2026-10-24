import React, { useEffect, useMemo, useRef, useState } from 'react'
import { Calendar, dayjsLocalizer, Views } from 'react-big-calendar'
import dayjs from 'dayjs'
import 'dayjs/locale/it'
import { Plus, ChevronLeft, ChevronRight, RefreshCw, Filter, Download, CalendarDays, Check, Search, ArrowRight, UserRound, Clock3 } from 'lucide-react'
import { type Appointment, type Boot, type FinanceBoot, type Patient, type Practitioner, type ReschedulePaymentBlock, type Row, ops, finance, schedule, call, requestKey, romeToday, displayDate, money, time } from './api'
import { type Feedback, Button, Chip, DataTable, DateInput, Drawer, Empty, Field, FormError, Heading, Metric, Modal, SearchableSelect, dateColumn, moneyColumn, useAction } from './ui'
import { FinanceActions } from './finance_actions'
import { FinanceCreate } from './finance_create'
import { ProfessionalWorkflow } from './professional_workflow'
import { PatientAssignments } from './patient_assignments'
import { PatientPackages, availableUnitLabel } from './patient_packages'
import { PatientDetail } from './patient_detail'
import { FinanceReports } from './finance_reports'
import { financeFieldLabel, financeFieldValue } from './finance_locale'
import { NoteHistory } from './note_history'
import { AppointmentTimeline } from './appointment_timeline'
import { WeekGrid } from './week_grid'
import { demoPatient, demoText, syntheticCode } from './demo_labels'
import { centerNameFor, closureName, economyName, practitionerName, practitionerNameFor } from './display_names'

dayjs.locale('it')
const localizer = dayjsLocalizer(dayjs)
const iso = (d: Date) => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
const wallDate = (date: string, clock = '00:00') => { const [y, m, d] = date.slice(0, 10).split('-').map(Number); const [h, min] = clock.slice(0, 5).split(':').map(Number); return new Date(y, m - 1, d, h || 0, min || 0) }
const fullName = (row: Appointment) => demoPatient(row.patient, row.patient_name, row.patient_first_name, row.patient_last_name)
type Context = { boot: Boot; center: string; feedback: Feedback }
const monthLabel = (date: Date) => new Intl.DateTimeFormat('it-IT', { month: 'long', year: 'numeric', timeZone: 'Europe/Rome' }).format(date)
const getError = (e: unknown) => e instanceof Error ? e.message : 'Caricamento non riuscito.'
const csvUrl = (method: string, params: Row) => '/api/method/centrochange_core.' + method + '?' + new URLSearchParams(Object.entries(params).map(([k, v]) => [k, String(v ?? '')]))

function CalendarPopover({ current, onSelect, onClose }: { current: Date; onSelect: (d: Date) => void; onClose: () => void }) {
  const [viewDate, setViewDate] = useState(current)
  const ref = useRef<HTMLDivElement>(null)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => { if (e.key === 'Escape') { e.preventDefault(); onClose() } }
    const handleClickOutside = (e: MouseEvent) => { if (ref.current && !ref.current.contains(e.target as Node)) onClose() }
    document.addEventListener('keydown', handleKeyDown)
    document.addEventListener('mousedown', handleClickOutside)
    return () => { document.removeEventListener('keydown', handleKeyDown); document.removeEventListener('mousedown', handleClickOutside) }
  }, [onClose])
  const startOfMonth = dayjs(viewDate).startOf('month')
  const daysInMonth = startOfMonth.daysInMonth()
  const startDayOfWeek = (startOfMonth.day() + 6) % 7
  const days: (number | null)[] = []
  for (let i = 0; i < startDayOfWeek; i++) days.push(null)
  for (let i = 1; i <= daysInMonth; i++) days.push(i)
  const monthName = new Intl.DateTimeFormat('it-IT', { month: 'long', year: 'numeric' }).format(viewDate)
  const weekdays = ['Lu', 'Ma', 'Me', 'Gi', 'Ve', 'Sa', 'Do']
  const todayStr = romeToday()
  const currentStr = iso(current)
  const pickDay = (dayNum: number) => {
    const chosen = dayjs(viewDate).date(dayNum).hour(12).minute(0).second(0).toDate()
    onSelect(chosen); onClose()
  }
  return <div className="calendar-popover" ref={ref} role="dialog" aria-label="Seleziona data">
    <div className="calendar-popover-header">
      <button type="button" className="icon-button bordered" aria-label="Mese precedente" onClick={() => setViewDate(dayjs(viewDate).subtract(1, 'month').toDate())}><ChevronLeft size={16} /></button>
      <strong style={{ textTransform: 'capitalize' }}>{monthName}</strong>
      <button type="button" className="icon-button bordered" aria-label="Mese successivo" onClick={() => setViewDate(dayjs(viewDate).add(1, 'month').toDate())}><ChevronRight size={16} /></button>
    </div>
    <div className="calendar-popover-grid">
      {weekdays.map(w => <div key={w} className="calendar-popover-weekday">{w}</div>)}
      {days.map((d, i) => {
        if (d === null) return <div key={`empty-${i}`} />
        const thisDateStr = dayjs(viewDate).date(d).format('YYYY-MM-DD')
        const isToday = thisDateStr === todayStr
        const isSelected = thisDateStr === currentStr
        return <button type="button" key={d} className={`calendar-popover-day ${isSelected ? 'selected' : ''} ${isToday ? 'today' : ''}`} onClick={() => pickDay(d)}>{d}</button>
      })}
    </div>
  </div>
}

function PractitionerMultiSelect({
  practitioners,
  selected,
  onChange
}: {
  practitioners: Practitioner[]
  selected: string[]
  onChange: (selected: string[]) => void
}) {
  const [open, setOpen] = useState(false)
  const [query, setQuery] = useState('')
  const ref = useRef<HTMLDivElement>(null)
  const isAll = selected.length === 0 || selected.length === practitioners.length

  useEffect(() => {
    if (!open) return
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        e.preventDefault()
        setOpen(false)
      }
    }
    const handleClickOutside = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false)
      }
    }
    document.addEventListener('keydown', handleKeyDown)
    const timer = setTimeout(() => {
      document.addEventListener('click', handleClickOutside)
    }, 0)
    return () => {
      clearTimeout(timer)
      document.removeEventListener('keydown', handleKeyDown)
      document.removeEventListener('click', handleClickOutside)
    }
  }, [open])

  const filtered = practitioners.filter(p => {
    if (!query.trim()) return true
    const q = query.toLowerCase()
    return practitionerName(p).toLowerCase().includes(q) || p.name.toLowerCase().includes(q)
  })

  const toggle = (id: string) => {
    if (isAll) {
      onChange([id])
    } else {
      if (selected.includes(id)) {
        const next = selected.filter(x => x !== id)
        onChange(next)
      } else {
        const next = [...selected, id]
        onChange(next.length === practitioners.length ? [] : next)
      }
    }
  }

  const selectAll = () => {
    onChange([])
    setQuery('')
  }

  const label = isAll
    ? `Tutti i professionisti (${practitioners.length})`
    : selected.length === 1
      ? practitionerName(practitioners.find(p => p.name === selected[0]) ?? { name: selected[0], practitioner_name: selected[0] } as Practitioner)
      : `${selected.length} professionisti selezionati`

  return (
    <div className="practitioner-multi-wrap" ref={ref}>
      <button
        type="button"
        className="button secondary practitioner-filter-trigger"
        onClick={() => setOpen(o => !o)}
        aria-haspopup="dialog"
        aria-expanded={open}
        aria-label="Filtro professionisti"
      >
        <Filter size={15} />
        <span className="filter-label-text">{label}</span>
      </button>
      {open && (
        <div className="practitioner-multi-popover" role="dialog" aria-label="Seleziona professionisti">
          <div className="multi-popover-search">
            <Search size={14} className="search-icon" />
            <input
              type="text"
              placeholder="Cerca professionista…"
              value={query}
              onChange={e => setQuery(e.target.value)}
              aria-label="Cerca professionista"
              autoFocus
            />
          </div>
          <div className="multi-popover-actions">
            <button type="button" className="text-button" onClick={selectAll}>Tutti</button>
            <button type="button" className="text-button" onClick={() => onChange([])}>Reset</button>
          </div>
          <div className="multi-popover-list" role="group" aria-label="Elenco professionisti">
            {filtered.length === 0 ? (
              <div className="multi-popover-empty">Nessun professionista trovato</div>
            ) : (
              filtered.map(p => {
                const checked = isAll || selected.includes(p.name)
                return (
                  <label key={p.name} className="multi-popover-item">
                    <input
                      type="checkbox"
                      checked={checked}
                      onChange={() => toggle(p.name)}
                      aria-label={practitionerName(p)}
                    />
                    <span className="p-avatar">{(practitionerName(p) || p.name).slice(0, 2).toUpperCase()}</span>
                    <span className="p-name">{practitionerName(p)}</span>
                  </label>
                )
              })
            )}
          </div>
          {!isAll && selected.length > 0 && (
            <div className="multi-popover-chips">
              {selected.map(id => {
                const p = practitioners.find(x => x.name === id)
                return (
                  <span key={id} className="chip-badge">
                    {p ? practitionerName(p) : id}
                    <button type="button" onClick={() => toggle(id)} aria-label={`Rimuovi ${p ? practitionerName(p) : id}`}>×</button>
                  </span>
                )
              })}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export function Agenda({ boot, center, feedback, refreshBoot }: Context & { refreshBoot: () => Promise<void> }) {
  const isManager = boot.roles.includes('CC Manager')
  const isSecretariat = boot.roles.includes('CC Secretariat')
  const isProfessional = boot.roles.includes('CC Professional') && !isManager && !isSecretariat

  const [date, setDate] = useState(() => wallDate(romeToday(), '12:00'))
  const [mode, setMode] = useState<'day' | 'week'>('week')
  const [rows, setRows] = useState<Appointment[]>([])
  const [selected, setSelected] = useState<Appointment | null>(null)
  const [booking, setBooking] = useState(false)
  const [bookingPractitioner, setBookingPractitioner] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [selectedPractitioners, setSelectedPractitioners] = useState<string[]>([])
  const [calendarOpen, setCalendarOpen] = useState(false)
  const [schedules, setSchedules] = useState<Row[]>([])
  const [reload, setReload] = useState(0)

  const start = mode === 'week' ? dayjs(date).subtract((date.getDay() + 6) % 7, 'day').toDate() : date
  const end = mode === 'week' ? dayjs(start).add(6, 'day').toDate() : date

  useEffect(() => {
    if (!center) return
    ops<Row[]>('workspace.schedules', { center }).then(setSchedules).catch(() => {})
  }, [center, reload])

  useEffect(() => {
    if (!center) return
    let live = true; setLoading(true); setError('')
    const pracParam = isProfessional ? (boot.practitioners[0]?.name || undefined) : (selectedPractitioners.length ? selectedPractitioners.join(',') : undefined)
    ops<{ appointments: Appointment[]; truncated: boolean }>('workspace.agenda', { center, start: iso(start), end: iso(end), practitioner: pracParam }).then(data => {
      if (!live) return; setRows(data.appointments); if (data.truncated) setError('Più di 500 sedute: restringi il periodo o filtra per professionista.'); setLoading(false)
    }).catch(e => { if (live) { setError(getError(e)); setLoading(false) } })
    return () => { live = false }
  }, [center, iso(start), iso(end), selectedPractitioners, reload])

  const isAll = !isProfessional && (selectedPractitioners.length === 0 || selectedPractitioners.length === boot.practitioners.length)
  const effectivePractitioners = isProfessional
    ? [boot.practitioners[0]?.name].filter(Boolean) as string[]
    : (isAll ? boot.practitioners.map(p => p.name) : selectedPractitioners)
  const resources = boot.practitioners.filter(p => effectivePractitioners.includes(p.name)).map(p => ({ id: p.name, title: practitionerName(p) }))
  const displayedRows = rows.filter(r => effectivePractitioners.includes(r.practitioner))
  const events = displayedRows.map(r => ({ id: r.name, title: `${time(r.appointment_time)}  ${fullName(r)} · ${demoText(r.cc_service_label) || 'Seduta'}`, start: wallDate(r.appointment_date, r.appointment_time), end: dayjs(wallDate(r.appointment_date, r.appointment_time)).add(Number(r.duration || 60), 'minute').toDate(), resourceId: r.practitioner, row: r }))
  const bookingPractitionerId = (!isAll && effectivePractitioners.length === 1) ? effectivePractitioners[0] : (isProfessional ? (boot.practitioners[0]?.name || '') : '')
  const days = Array.from({ length: 7 }, (_, index) => dayjs(start).add(index, 'day').toDate())
  const visitCount = displayedRows.length
  const completed = displayedRows.filter(r => !!r.cc_performed && r.status !== 'Cancelled').length
  const nowRome = dayjs()
  const toClose = displayedRows.filter(r => {
    if (r.cc_performed || r.status === 'Cancelled') return false
    const end = dayjs(`${r.appointment_date}T${r.appointment_time || '00:00:00'}`).add(Number(r.duration || 60), 'minute')
    return !end.isAfter(nowRome)
  }).length
  const step = (n: number) => setDate(dayjs(date).add(n * (mode === 'week' ? 7 : 1), 'day').toDate())
  const refresh = () => { setSelected(null); setBooking(false); setReload(x => x + 1); void refreshBoot() }

  return <><Heading eyebrow="IL TUO SPAZIO DI LAVORO" title="Agenda" subtitle={`${displayDate(iso(start))}${mode === 'week' ? ' – ' + displayDate(iso(end)) : ''}  ·  ${monthLabel(date)}`} action={<Button onClick={() => { setBookingPractitioner(bookingPractitionerId); setBooking(true) }}><Plus size={18} /> Nuova prenotazione</Button>} />
    <div className="metrics-grid"><Metric label="Sedute nel periodo" value={visitCount} tone="blue" /><Metric label="Sedute svolte" value={completed} tone="green" /><Metric label="Sedute da chiudere" value={toClose} tone="amber" /><Metric label="Professionisti" value={resources.length} tone="purple" /></div>
    <section className="panel calendar-panel"><div className="panel-toolbar"><div className="toolbar-left"><div className="segmented"><button className={mode === 'day' ? 'selected' : ''} onClick={() => setMode('day')}>Giorno</button><button className={mode === 'week' ? 'selected' : ''} onClick={() => setMode('week')}>Settimana</button></div><button className="icon-button bordered" title="Precedente" aria-label="Periodo precedente" onClick={() => step(-1)}><ChevronLeft /></button><button className="icon-button bordered" title="Successivo" aria-label="Periodo successivo" onClick={() => step(1)}><ChevronRight /></button><Button variant="secondary" onClick={() => setDate(wallDate(romeToday(), '12:00'))}>Oggi</Button><div className="calendar-popover-wrap"><Button variant="secondary" onClick={() => setCalendarOpen(open => !open)} aria-expanded={calendarOpen} aria-label="Apri calendario"><CalendarDays size={16} /> Scegli data</Button>{calendarOpen && <CalendarPopover current={date} onSelect={setDate} onClose={() => setCalendarOpen(false)} />}</div></div><div className="toolbar-right">{isProfessional ? <span className="agenda-practitioner-label">Professionista: <strong>{practitionerName(boot.practitioners[0] ?? { name: effectivePractitioners[0], practitioner_name: 'Mio profilo' } as Practitioner)}</strong></span> : <><PractitionerMultiSelect practitioners={boot.practitioners} selected={selectedPractitioners} onChange={setSelectedPractitioners} /><select aria-label="Professionista" value={selectedPractitioners.length === 1 ? selectedPractitioners[0] : isAll ? 'all' : selectedPractitioners.join(',')} onChange={e => { const val = e.target.value; setSelectedPractitioners(val === 'all' || !val ? [] : [val]) }} style={{ position: 'absolute', opacity: 0, pointerEvents: 'none', width: 0, height: 0, margin: 0, padding: 0 }} tabIndex={-1}><option value="all">Tutti i professionisti</option>{boot.practitioners.map(p => <option key={p.name} value={p.name}>{practitionerName(p)}</option>)}</select></>}<button className="icon-button bordered" title="Aggiorna" aria-label="Aggiorna agenda" onClick={() => setReload(x => x + 1)}><RefreshCw /></button></div></div>
      {error && <p className="inline-error" role="alert">{error}</p>}
      {loading ? <div className="calendar-loading" role="status">Caricamento agenda…</div> : !resources.length ? <Empty title="Nessun professionista disponibile" detail="Verifica l'assegnazione al centro selezionato." /> : mode === 'week' ? <WeekGrid days={days.map(iso)} resources={resources} rows={rows} schedules={schedules} onSelect={setSelected} onBook={(day, professional) => { setDate(wallDate(day, '12:00')); setBookingPractitioner(professional); setBooking(true) }} /> : <div className="calendar-wrap"><Calendar localizer={localizer} culture="it" events={events} resources={resources} resourceIdAccessor="id" resourceTitleAccessor="title" view={Views.DAY} date={date} onNavigate={setDate} onView={v => setMode(v === Views.WEEK ? 'week' : 'day')} toolbar={false} popup selectable min={wallDate(iso(date), '07:00')} max={wallDate(iso(date), '21:00')} step={30} timeslots={2} startAccessor="start" endAccessor="end" onSelectEvent={e => setSelected(e.row)} onSelectSlot={slot => { setDate(slot.start); setBookingPractitioner(bookingPractitionerId); setBooking(true) }} eventPropGetter={e => ({ className: e.row.status === 'Cancelled' ? 'event-cancelled' : e.row.cc_performed ? 'event-done' : 'event-booked' })} messages={{ noEventsInRange: 'Nessuna seduta nel periodo', showMore: count => `+ ${count} altre`, allDay: 'Tutto il giorno' }} /></div>}
    </section>{booking && <Booking boot={boot} center={center} onClose={() => setBooking(false)} onSuccess={refresh} feedback={feedback} date={iso(date)} initialPractitioner={bookingPractitioner} />}{selected && <AppointmentDetail row={selected} boot={boot} center={center} onClose={() => setSelected(null)} onSuccess={refresh} feedback={feedback} />}</>
}

function Booking({ boot, center, onClose, onSuccess, feedback, date, initialPractitioner = '' }: { boot: Boot; center: string; onClose: () => void; onSuccess: () => void; feedback: Feedback; date: string; initialPractitioner?: string }) {
  const keys = useRef<Record<string, string>>({})
  const [patient, setPatient] = useState(boot.patients[0]?.name ?? '')
  const [practitioner, setPractitioner] = useState(initialPractitioner || boot.practitioners[0]?.name || '')
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
  return <Modal title="Nuova prenotazione" onClose={onClose}><form onSubmit={e => { e.preventDefault(); void submit() }}><div className="form-grid"><SearchableSelect label="Paziente" options={boot.patients.map(p => ({ value: p.name, label: demoPatient(p.name, p.patient_name, p.first_name, p.last_name) }))} value={patient} onChange={setPatient} required /><SearchableSelect label="Professionista" options={boot.practitioners.map(p => ({ value: p.name, label: practitionerName(p) }))} value={practitioner} onChange={setPractitioner} required /><SearchableSelect label="Servizio" options={boot.services.map(s => ({ value: s.name, label: demoText(s.cc_service_label) || s.name }))} value={service} onChange={setService} required /><SearchableSelect label="Pacchetto" options={packages.map(p => ({ value: String(p.name), label: `${demoText(p.label || p.name)} · ${availableUnitLabel(Number(p.available))}` }))} value={packageName} onChange={setPackageName} empty="Nessun pacchetto" /><Field label="Data" required><DateInput value={day} onChange={setDay} required /></Field><Field label="Ora" required><input type="time" value={clock} onChange={e => setClock(e.target.value)} required /></Field></div><Field label="Motivo" required><textarea value={reason} onChange={e => setReason(e.target.value)} required maxLength={2000} rows={3} /></Field><FormError error={error} /><div className="form-actions"><Button type="button" variant="secondary" onClick={onClose}>Annulla</Button><Button disabled={busy || !patient || !practitioner || !service} type="submit">{busy ? 'Salvataggio…' : 'Conferma prenotazione'}</Button></div></form></Modal>
}

function AppointmentDetail({ row, boot, center, onClose, onSuccess, feedback }: { row: Appointment; boot: Boot; center: string; onClose: () => void; onSuccess: () => void; feedback: Feedback }) {
  const overrideKeys = useRef<Record<string, string>>({})
  const [tab, setTab] = useState<'Seduta' | 'Storico' | 'Note'>('Seduta')
  const [history, setHistory] = useState<Row | null>(null)
  const [events, setEvents] = useState<Row[] | null>(null)
  const [eventsError, setEventsError] = useState('')
  const [action, setAction] = useState('')
  const [reason, setReason] = useState('')
  const [moveDate, setMoveDate] = useState(row.appointment_date)
  const [moveTime, setMoveTime] = useState(time(row.appointment_time))
  const [paymentBlock, setPaymentBlock] = useState<ReschedulePaymentBlock | null>(null)
  const [overrideReason, setOverrideReason] = useState('')
  const [overrideDue, setOverrideDue] = useState('')
  const [moveBusy, setMoveBusy] = useState(false)
  const [moveError, setMoveError] = useState('')
  const [paid, setPaid] = useState(Boolean(row.cc_paid))
  const [paymentMethod, setPaymentMethod] = useState(boot.payment_methods[0] ?? '')
  const [note, setNote] = useState('')
  const [privateNote, setPrivateNote] = useState(false)
  const [corrects, setCorrects] = useState<string | null>(null)
  const { busy, error, run } = useAction(feedback, onSuccess)
  useEffect(() => {
    if (tab === 'Seduta') return
    let live = true
    ops<Row>('workspace.patient_history', { patient: row.patient, center })
      .then(value => { if (live) setHistory(value) })
      .catch(e => { if (live) feedback(getError(e), true) })
    return () => { live = false }
  }, [tab, row.patient, center])
  useEffect(() => {
    if (tab !== 'Storico') return
    let live = true
    setEvents(null); setEventsError('')
    ops<Row[]>('workspace.appointment_events', { appointment: row.name })
      .then(value => { if (live) setEvents(value) })
      .catch(e => { if (live) setEventsError(getError(e)) })
    return () => { live = false }
  }, [tab, row.name])
  const administrative = boot.roles.some(r => ['CC Manager', 'CC Secretariat'].includes(r))
  const finalized = ['Closed', 'Auto Locked'].includes(row.cc_closure_state ?? '')
  const mutable = !finalized && !['Cancelled', 'No Show'].includes(row.status)
  const nowRome = romeToday()
  const clockRome = new Intl.DateTimeFormat('en-GB', { timeZone: 'Europe/Rome', hour: '2-digit', minute: '2-digit', hourCycle: 'h23' }).format(new Date())
  const futureSlot = row.appointment_date > nowRome || (row.appointment_date === nowRome && time(row.appointment_time) > clockRome)
  const [startHour, startMinute] = time(row.appointment_time).split(':').map(Number)
  const [nowHour, nowMinute] = clockRome.split(':').map(Number)
  const sessionEnded = row.appointment_date < nowRome || (row.appointment_date === nowRome &&
    startHour * 60 + startMinute + Number(row.duration || 60) <= nowHour * 60 + nowMinute)
  const actions = [
    ...(mutable && sessionEnded && (row.status !== 'Closed' || row.cc_closure_state === 'Reopened') ? [{ id: 'close', label: 'Chiudi seduta' }] : []),
    ...(mutable && futureSlot ? [{ id: 'move', label: 'Sposta' }] : []),
    ...(mutable && !row.cc_performed ? [{ id: 'cancel', label: 'Cancella' }] : []),
    ...(administrative && finalized ? [{ id: 'reopen', label: 'Riapri' }] : []),
    ...(administrative && ['Due', 'Package Covered'].includes(row.cc_economic_state ?? '') ? [{ id: 'waive', label: 'Rinuncia economica' }] : [])
  ]
  const submit = async () => {
    if (action === 'move') {
      setMoveBusy(true); setMoveError('')
      const args = { appointment: row.name, appointment_date: moveDate, appointment_time: moveTime, reason }
      try {
        await schedule('booking.reschedule', args, true)
        feedback('Prenotazione spostata.'); setAction(''); onSuccess()
      } catch (cause) {
        const message = getError(cause)
        if (message.includes('Serve una verifica dei pagamenti prima della prossima seduta')) {
          try {
            const block = await schedule<ReschedulePaymentBlock>('booking.reschedule_payment_blockers', {
              appointment: row.name, appointment_date: moveDate, appointment_time: moveTime
            })
            if (block.blocked) { setPaymentBlock(block); setOverrideDue(moveDate); setOverrideReason('') }
            else setMoveError('La posizione dei pagamenti è cambiata. Riprova lo spostamento.')
          } catch (previewError) { setMoveError(getError(previewError)) }
        } else setMoveError(message)
      } finally { setMoveBusy(false) }
      return
    }
    const args = action === 'close' ? { appointment: row.name, paid: paid ? 1 : 0, mode_of_payment: paid ? paymentMethod : null, reason } : { appointment: row.name, reason }
    if (await run(() => ops(`lifecycle.${action}`, args, true))) setAction('')
  }
  const authorizeAndMove = async () => {
    if (!paymentBlock?.can_override) return
    setMoveBusy(true); setMoveError('')
    const args = { appointment: row.name, appointment_date: moveDate, appointment_time: moveTime, reason,
      override_reason: overrideReason, due_date: overrideDue,
      expected_references: paymentBlock.debts.map(debt => ({ reference_doctype: debt.reference_doctype, reference_name: debt.reference_name })) }
    const key = JSON.stringify(args)
    try {
      await schedule('booking.reschedule_with_payment_override', { ...args, request_key: overrideKeys.current[key] ??= requestKey() }, true)
      setPaymentBlock(null); setAction(''); feedback('Deroga registrata e prenotazione spostata.'); onSuccess()
    } catch (cause) { setMoveError(getError(cause)) }
    finally { setMoveBusy(false) }
  }
  const entries = (key: string) => Array.isArray(history?.[key]) ? history[key] as Row[] : []
  return <><Drawer title={fullName(row)} onClose={onClose}><div className="detail-summary"><Chip tone={row.status === 'Cancelled' ? 'bad' : row.cc_performed ? 'good' : 'blue'}>{row.status === 'Cancelled' ? 'Cancellata' : row.cc_performed ? 'Svolta' : 'Prenotata'}</Chip><h3>{demoText(row.cc_service_label) || 'Seduta'}</h3><p><CalendarDays size={16} /> {displayDate(row.appointment_date)} · {time(row.appointment_time)}</p><p><UserRound size={16} /> {practitionerNameFor(row.practitioner, boot.practitioners, row.practitioner_name)}</p><p><Clock3 size={16} /> {row.duration} min · {money(row.cc_price_snapshot, row.cc_currency_snapshot || 'EUR')}</p></div><div className="detail-tabs" role="tablist">{(['Seduta', 'Storico', 'Note'] as const).map(t => <button key={t} role="tab" aria-selected={tab === t} onClick={() => setTab(t)}>{t}</button>)}</div>
    {tab === 'Seduta' && <><div className="detail-section"><h3>Stato operativo</h3><p>Chiusura: {closureName(row.cc_closure_state)}<br />Economia: {economyName(row.cc_economic_state)}</p><div className="action-grid">{actions.map(a => <Button key={a.id} variant={a.id === 'close' ? 'primary' : a.id === 'cancel' ? 'danger' : 'secondary'} onClick={() => setAction(a.id)}>{a.label}</Button>)}</div></div>{action && <form className="action-form" onSubmit={e => { e.preventDefault(); void submit() }}><h3>{actions.find(a => a.id === action)?.label}</h3>{action === 'move' && <div className="form-grid"><Field label="Nuova data"><DateInput value={moveDate} onChange={value => { setMoveDate(value); setPaymentBlock(null) }} required /></Field><Field label="Nuova ora"><input type="time" value={moveTime} onChange={e => { setMoveTime(e.target.value); setPaymentBlock(null) }} required /></Field></div>}{action === 'close' && <><label className="checkbox-row"><input type="checkbox" checked={paid} onChange={e => setPaid(e.target.checked)} /> Pagata</label>{paid && <Field label="Metodo di pagamento" required><select value={paymentMethod} onChange={e => setPaymentMethod(e.target.value)} required>{boot.payment_methods.map(p => <option key={p}>{p}</option>)}</select></Field>}</>}<Field label="Motivo" required><textarea value={reason} onChange={e => setReason(e.target.value)} required maxLength={2000} /></Field><FormError error={action === 'move' ? moveError : error} /><div className="form-actions"><Button type="button" variant="secondary" onClick={() => { setAction(''); setPaymentBlock(null) }}>Annulla</Button><Button disabled={busy || moveBusy} type="submit">{busy || moveBusy ? 'Salvataggio…' : 'Conferma'}</Button></div></form>}</>}
    {tab === 'Storico' && <div className="detail-section"><h3>Eventi della seduta</h3><p className="scope-note">Modifiche e motivi relativi a questa seduta. Le versioni delle note sono nella scheda Note.</p>{eventsError && <p className="inline-error" role="alert">{eventsError}</p>}{!events && !eventsError ? <p role="status">Caricamento eventi…</p> : events && <AppointmentTimeline rows={events} />}<h3>Altre sedute del paziente</h3>{!history ? <p role="status">Caricamento sedute…</p> : entries('appointments').length ? <div className="timeline">{entries('appointments').map((a, i) => <article key={i}><strong>{displayDate(a.appointment_date)} · {demoText(a.cc_service_label) || 'Seduta'}</strong><span>{closureName(a.cc_closure_state)} · {economyName(a.cc_economic_state)}</span></article>)}</div> : <Empty title="Nessun'altra seduta nel centro" />}<h3>Pacchetti</h3>{entries('packages').map((p, i) => <p key={i}>{demoText(p.label)} · Residue: {String(p.remaining)}</p>)}</div>}
    {tab === 'Note' && <div className="detail-section"><h3>Note organizzative</h3><NoteHistory rows={entries('organizational_notes')} onCorrect={n => { setNote(String(n.content ?? '')); setPrivateNote(false); setCorrects(String(n.name)) }} />{boot.roles.includes('CC Professional') && <><h3>Note riservate</h3><NoteHistory rows={entries('private_notes')} privateNotes onCorrect={n => { setNote(String(n.content ?? '')); setPrivateNote(true); setCorrects(String(n.name)) }} /></>}<form onSubmit={e => { e.preventDefault(); void run(() => ops('notes.add_note', { patient: row.patient, center, content: note, private: privateNote ? 1 : 0, corrects }, true), 'Nota registrata.').then(ok => { if (ok) { setNote(''); setCorrects(null); setHistory(null); void ops<Row>('workspace.patient_history', { patient: row.patient, center }).then(setHistory) } }) }}><Field label={corrects ? "Rettifica nota" : "Nuova nota"}><textarea required value={note} onChange={e => setNote(e.target.value)} maxLength={100000} /></Field>{boot.roles.includes('CC Professional') && <label className="checkbox-row"><input type="checkbox" checked={privateNote} onChange={e => setPrivateNote(e.target.checked)} /> Nota professionale riservata</label>}<FormError error={error} /><Button disabled={busy || !note} type="submit">{corrects ? "Registra rettifica" : "Aggiungi nota"}</Button></form></div>}
  </Drawer>{paymentBlock && <Modal title="Verifica pagamenti prima dello spostamento" onClose={() => { setPaymentBlock(null); setMoveError('') }}><p className="scope-note">La prenotazione resta invariata finché la verifica non viene completata.</p>{paymentBlock.can_override ? <form onSubmit={e => { e.preventDefault(); void authorizeAndMove() }}><p>Posizioni che impediscono lo spostamento:</p><ul className="payment-block-list">{paymentBlock.debts.map((debt, index) => <li key={`${debt.reference_doctype}:${debt.reference_name}`}><strong>{debt.reference_doctype === 'Sales Invoice' ? 'Fattura' : 'Seduta non fatturata'} {index + 1}</strong><span>{money(debt.amount, debt.currency)} · scadenza {displayDate(debt.due_date)} · {centerNameFor(debt.center, boot.centers)}</span></li>)}</ul><p className="scope-note">Debito, fatture e scadenze originarie restano conservati nello storico.</p><Field label="Motivazione della deroga" required><textarea value={overrideReason} onChange={e => setOverrideReason(e.target.value)} required maxLength={2000} /></Field><Field label="Nuova scadenza" required><DateInput value={overrideDue} onChange={setOverrideDue} required /></Field><FormError error={moveError} /><div className="form-actions"><Button type="button" variant="secondary" onClick={() => { setPaymentBlock(null); setMoveError('') }}>Annulla</Button><Button disabled={moveBusy || !overrideReason.trim() || !overrideDue} type="submit">{moveBusy ? 'Verifica in corso…' : 'Autorizza e procedi'}</Button></div></form> : <><p role="alert">Serve una verifica dei pagamenti. Contatta la segreteria o la Direzione: il tuo ruolo non può autorizzare una deroga.</p><div className="form-actions"><Button onClick={() => setPaymentBlock(null)}>Chiudi</Button></div></>}</Modal>}</>
}

export function Patients({ boot, center, feedback, refreshBoot }: Context & { refreshBoot: () => Promise<void> }) {
  const [search, setSearch] = useState('')
  const [rows, setRows] = useState<Patient[]>(boot.patients)
  const [selected, setSelected] = useState<Patient | null>(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [truncated, setTruncated] = useState(false)
  useEffect(() => {
    if (!center) return
    const term = search.trim().toLocaleLowerCase('it-IT')
    const aliases = term ? boot.patients.filter(row =>
      demoPatient(row.name, row.patient_name, row.first_name, row.last_name).toLocaleLowerCase('it-IT').includes(term)) : []
    let live = true
    setRows([]); setLoading(true); setError(''); setTruncated(false)
    ops<{ patients: Patient[]; truncated: boolean }>('workspace.patient_search', { center, query: search })
      .then(result => { if (live) { const merged = [...new Map([...result.patients, ...aliases].map(row => [row.name, row])).values()]; setRows(merged.slice(0, 50)); setTruncated(result.truncated || merged.length > 50); setLoading(false) } })
      .catch(cause => { if (live) { setRows([]); setError(getError(cause)); setLoading(false) } })
    return () => { live = false }
  }, [center, search, boot])
  return <><Heading eyebrow="PERCORSO PAZIENTE" title="Pazienti" subtitle="Cerca, consulta e segui il percorso operativo nel centro." /><section className="panel"><div className="panel-toolbar"><div className="panel-title"><h2>Elenco pazienti</h2><p>{rows.length} {rows.length === 1 ? 'risultato' : 'risultati'} nel centro selezionato</p></div><label className="search-inline"><Search size={17} /><input placeholder="Cerca per nome o codice" aria-label="Cerca pazienti" value={search} onChange={event => setSearch(event.target.value)} /></label></div>{loading && <p className="panel-loading" role="status">Caricamento pazienti…</p>}{error && <p className="inline-error" role="alert">{error}</p>}{truncated && <p className="scope-note">Mostrati i primi 50 risultati. Affina la ricerca.</p>}{!loading && !error && (rows.length ? <DataTable rows={rows as unknown as Row[]} columns={[{ key: 'patient_name', label: 'Paziente', render: (value, row) => <><strong>{demoPatient(row.name, value, row.first_name, row.last_name)}</strong>{row.active_assignment === false && <Chip tone="warn">Storico</Chip>}</> }, { key: 'name', label: '', render: () => <ArrowRight size={17} /> }]} onRow={row => setSelected(row as Patient)} /> : <Empty title="Nessun paziente trovato nel centro." />)}</section>{selected && <PatientDetail boot={boot} patient={selected} center={center} feedback={feedback} onClose={() => setSelected(null)} onSuccess={() => { void refreshBoot() }} />}</>
}

export function Professionals({ boot, center }: { boot: Boot; center: string }) {
  const [query, setQuery] = useState('')
  const [rows, setRows] = useState<Practitioner[]>([])
  const [hasMore, setHasMore] = useState(false)
  const [selected, setSelected] = useState<Practitioner | null>(null)
  const [detail, setDetail] = useState<Row | null>(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const [detailLoading, setDetailLoading] = useState(false)
  const searchGeneration = useRef(0)
  const canReadProfile = boot.roles.includes('CC Manager') || boot.roles.includes('CC Professional')
  const term = query.trim()
  useEffect(() => {
    searchGeneration.current += 1
    setSelected(null); setDetail(null); setRows([]); setHasMore(false); setError('')
    if (!canReadProfile) {
      const needle = term.toLocaleLowerCase('it-IT')
      setRows(boot.practitioners.filter(row => practitionerName(row).toLocaleLowerCase('it-IT').includes(needle)))
      setLoading(false)
      return
    }
    let live = true
    setLoading(true)
    const timer = window.setTimeout(() => {
      ops<{ rows: Practitioner[]; has_more: boolean }>('profiles.practitioners', { center, limit: 50, offset: 0, search: term })
        .then(result => { if (live) { setRows(result.rows); setHasMore(result.has_more) } })
        .catch(cause => { if (live) setError(getError(cause)) })
        .finally(() => { if (live) setLoading(false) })
    }, term ? 180 : 0)
    return () => { live = false; clearTimeout(timer) }
  }, [center, term, boot, canReadProfile])
  const more = async () => {
    const generation = searchGeneration.current
    setLoading(true); setError('')
    try {
      const result = await ops<{ rows: Practitioner[]; has_more: boolean }>('profiles.practitioners', { center, limit: 50, offset: rows.length, search: term })
      if (generation === searchGeneration.current) { setRows(current => [...current, ...result.rows]); setHasMore(result.has_more) }
    } catch (cause) { if (generation === searchGeneration.current) setError(getError(cause)) }
    finally { if (generation === searchGeneration.current) setLoading(false) }
  }
  useEffect(() => {
    if (!selected || !canReadProfile) return
    let live = true; setDetailLoading(true); setError(''); setDetail(null)
    ops<Row>('profiles.practitioner_detail', { center, name: selected.name }).then(value => { if (live) setDetail(value) }).catch(cause => { if (live) setError(getError(cause)) }).finally(() => { if (live) setDetailLoading(false) })
    return () => { live = false }
  }, [selected, center, canReadProfile])
  const selectedStatus = String(detail?.status ?? selected?.status ?? 'Active')
  return <><Heading eyebrow="OPERATIVITÀ" title="Professionisti" subtitle="Professionisti autorizzati per il centro selezionato." />
    <section className="panel"><div className="panel-toolbar"><div className="panel-title"><h2>Elenco professionisti</h2><p>{rows.length} {rows.length === 1 ? 'professionista' : 'professionisti'} nel centro{hasMore ? ' · altri disponibili' : ''}</p></div><label className="search-inline"><Search size={17} /><input type="search" value={query} onChange={event => setQuery(event.target.value)} aria-label="Cerca professionisti" placeholder="Cerca professionista" /></label></div>{loading && <p className="panel-loading" role="status">Caricamento professionisti…</p>}{error && <p className="inline-error" role="alert">{error}</p>}{!loading && !error && (rows.length ? <DataTable rows={rows as unknown as Row[]} columns={[{ key: 'practitioner_name', label: 'Professionista', render: (_value, row) => <strong>{practitionerName(row as Practitioner)}</strong> }, { key: 'status', label: 'Stato', render: (value) => value && value !== 'Active' ? 'Non attivo' : 'Attivo' }, { key: 'name', label: 'Scheda', render: () => <ArrowRight size={17} /> }]} onRow={row => { setSelected(row as Practitioner); setDetail(null); setError('') }} /> : <Empty title="Nessun professionista trovato nel centro." />)}{hasMore && <Button variant="secondary" disabled={loading} onClick={() => void more()}>Carica altri</Button>}</section>
    {selected && <Drawer title={practitionerName(selected)} onClose={() => { setSelected(null); setDetail(null) }}><div className="detail-summary"><Chip tone={selectedStatus !== 'Active' ? 'warn' : 'good'}>{selectedStatus !== 'Active' ? 'Non attivo' : 'Attivo nel centro'}</Chip><p>Centro: {centerNameFor(center, boot.centers)}</p></div>{detailLoading && <p className="detail-section" role="status">Caricamento scheda…</p>}{error && <p className="detail-section inline-error" role="alert">{error}</p>}{detail && <div className="detail-section"><h3>Scheda professionista</h3><dl className="property-list">{syntheticCode(detail.first_name) ? <div><dt>Identità</dt><dd>{practitionerName(selected)}</dd></div> : <><div><dt>Nome</dt><dd>{String(detail.first_name ?? '—')}</dd></div><div><dt>Cognome</dt><dd>{String(detail.last_name ?? '—')}</dd></div></>}</dl><p className="scope-note">Scheda consultabile secondo i permessi del server. Le modifiche autorizzate restano nell'archivio dedicato.</p></div>}{!canReadProfile && <div className="detail-section"><p>È disponibile la sola identità operativa autorizzata per questo centro.</p></div>}</Drawer>}
  </>
}

export function ServiceCatalog({ boot, center }: { boot: Boot; center: string }) {
  const [query, setQuery] = useState('')
  const [selected, setSelected] = useState<(typeof boot.services)[number] | null>(null)
  const search = query.trim().toLocaleLowerCase('it-IT')
  const services = boot.services.filter(service => `${demoText(service.cc_service_label)} ${service.cc_service_label ?? ''} ${service.name}`.toLocaleLowerCase('it-IT').includes(search))
  return <><Heading eyebrow="OPERATIVITÀ" title="Servizi e professionisti" subtitle="Servizi disponibili nel centro selezionato e professionisti associati." />
    <section className="panel"><div className="panel-toolbar"><div className="panel-title"><h2>Servizi del centro</h2><p>{centerNameFor(center, boot.centers)} · {services.length} {services.length === 1 ? "servizio" : "servizi"} · tariffe e durata dallo snapshot del catalogo autorizzato.</p></div><label className="search-inline"><Search size={17} /><input type="search" value={query} onChange={e => setQuery(e.target.value)} aria-label="Cerca servizi" placeholder="Cerca servizio" /></label></div><DataTable rows={services as unknown as Row[]} columns={[{ key: 'cc_service_label', label: 'Servizio', render: (value, row) => <strong>{demoText(value || row.name)}</strong> }, { key: 'duration', label: 'Durata', render: value => value == null ? 'Da definire' : `${String(value)} min` }, { key: 'cc_price_snapshot', label: 'Tariffa', render: (value, row) => money(value, String(row.cc_currency_snapshot || 'EUR')) }]} onRow={row => setSelected(row as typeof selected)} /></section>
    <section className="panel catalog-practitioners"><div className="panel-toolbar"><div className="panel-title"><h2>Professionisti</h2><p>Associati al centro secondo le appartenenze e lo stato correnti del backend.</p></div></div><div className="schedule-grid">{boot.practitioners.map(practitioner => <article className="schedule-card" key={practitioner.name}><span className="avatar">{practitionerName(practitioner).slice(0, 2).toLocaleUpperCase('it-IT')}</span><h3>{practitionerName(practitioner)}</h3><Chip tone="good">Attivo nel centro</Chip></article>)}</div>{!boot.practitioners.length && <Empty title="Nessun professionista attivo" />}</section>
    {selected && <Drawer title={demoText(selected.cc_service_label || selected.name)} onClose={() => setSelected(null)}><div className="detail-summary"><Chip tone="blue">Servizio disponibile</Chip><h3>{demoText(selected.cc_service_label || selected.name)}</h3><p>Centro: {centerNameFor(center, boot.centers)}</p></div><div className="detail-section"><h3>Scheda servizio</h3><dl className="property-list"><div><dt>Codice</dt><dd>{demoText(selected.name)}</dd></div><div><dt>Articolo canonico</dt><dd>{demoText(selected.cc_service_item || '—')}</dd></div><div><dt>Durata</dt><dd>{selected.duration == null ? 'Da definire' : `${selected.duration} min`}</dd></div><div><dt>Tariffa corrente per prenotazione</dt><dd>{money(selected.cc_price_snapshot, selected.cc_currency_snapshot || 'EUR')}</dd></div></dl><p className="scope-note">Tariffa corrente del catalogo autorizzato. Le sedute già prenotate conservano il proprio snapshot; questa scheda non modifica Item, Item Price o Appointment Type.</p></div></Drawer>}
  </>
}

export { Availability } from './availability_view'

export function Reports({ boot, center, feedback, financeBoot }: Context & { financeBoot?: FinanceBoot | null }) {
  const isManager = boot.roles.includes('CC Manager')
  const isSecretariat = boot.roles.includes('CC Secretariat')
  const isProfessional = boot.roles.includes('CC Professional') && !isManager && !isSecretariat
  const myPractitioner = isProfessional ? (boot.practitioners[0]?.name || '') : ''

  const [start, setStart] = useState(dayjs(romeToday()).startOf('month').format('YYYY-MM-DD'))
  const [end, setEnd] = useState(romeToday())
  const [preset, setPreset] = useState<'today' | 'week' | 'month' | 'last_month' | 'custom'>('month')
  const [data, setData] = useState<Row | null>(null)
  const [loading, setLoading] = useState(true)
  const [professionalOpen, setProfessionalOpen] = useState(false)
  const [professional, setProfessional] = useState(isProfessional ? myPractitioner : '')
  const [selectedKpi, setSelectedKpi] = useState<string>('all')
  const [selectedCurrency, setSelectedCurrency] = useState<string>('all')
  const [sessions, setSessions] = useState<Appointment[]>([])
  const [sessionsLoading, setSessionsLoading] = useState(false)
  const [sessionsError, setSessionsError] = useState('')
  const [page, setPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [totalSessions, setTotalSessions] = useState(0)
  const [selectedAppointment, setSelectedAppointment] = useState<Appointment | null>(null)
  const [reload, setReload] = useState(0)

  const [profSessions, setProfSessions] = useState<Appointment[]>([])
  const [profLoading, setProfLoading] = useState(false)
  const [profError, setProfError] = useState('')

  const applyPreset = (p: 'today' | 'week' | 'month' | 'last_month') => {
    setPreset(p)
    setPage(1)
    const today = dayjs(romeToday())
    if (p === 'today') {
      setStart(today.format('YYYY-MM-DD'))
      setEnd(today.format('YYYY-MM-DD'))
    } else if (p === 'week') {
      const mon = today.subtract((today.day() + 6) % 7, 'day')
      setStart(mon.format('YYYY-MM-DD'))
      setEnd(mon.add(6, 'day').format('YYYY-MM-DD'))
    } else if (p === 'month') {
      setStart(today.startOf('month').format('YYYY-MM-DD'))
      setEnd(today.format('YYYY-MM-DD'))
    } else if (p === 'last_month') {
      const prev = today.subtract(1, 'month')
      setStart(prev.startOf('month').format('YYYY-MM-DD'))
      setEnd(prev.endOf('month').format('YYYY-MM-DD'))
    }
  }

  const effectivePractitioner = isProfessional ? myPractitioner : professional

  useEffect(() => {
    if (!center) return
    let live = true
    setLoading(true)
    const profParam = effectivePractitioner || undefined
    ops<Row>('reporting.summary', { center, start, end, practitioner: profParam })
      .then(r => { if (live) { setData(r); setLoading(false) } })
      .catch(e => { if (live) { setData(null); feedback(getError(e), true); setLoading(false) } })
    return () => { live = false }
  }, [center, start, end, effectivePractitioner, reload])

  useEffect(() => {
    if (!center) return
    let live = true
    setSessionsLoading(true)
    setSessionsError('')
    const profParam = effectivePractitioner || undefined
    const currParam = selectedCurrency !== 'all' ? selectedCurrency : undefined
    ops<{ appointments: Appointment[]; total: number; total_pages?: number }>('reporting.sessions', {
      center, start, end, practitioner: profParam, kpi: selectedKpi, currency: currParam, page, page_length: 50
    })
      .then(result => {
        if (live) {
          setSessions(result.appointments || [])
          setTotalSessions(result.total ?? (result.appointments || []).length)
          setTotalPages(result.total_pages ?? Math.max(1, Math.ceil((result.total ?? 0) / 50)))
          setSessionsLoading(false)
        }
      })
      .catch(cause => {
        if (live) {
          setSessions([])
          setTotalSessions(0)
          setTotalPages(1)
          setSessionsError(getError(cause) || 'Impossibile caricare il dettaglio delle sedute dal server.')
          setSessionsLoading(false)
        }
      })
    return () => { live = false }
  }, [center, start, end, effectivePractitioner, selectedKpi, selectedCurrency, page, reload])

  useEffect(() => {
    if (!center || !professionalOpen || !professional) {
      setProfSessions([])
      return
    }
    let live = true
    setProfLoading(true)
    setProfError('')
    ops<{ appointments: Appointment[]; total: number }>('reporting.sessions', {
      center, start, end, practitioner: professional, kpi: 'all', page: 1, page_length: 0
    }).then(res => {
      if (live) {
        setProfSessions(res.appointments || [])
        setProfLoading(false)
      }
    }).catch(err => {
      if (live) {
        setProfError(getError(err))
        setProfLoading(false)
      }
    })
    return () => { live = false }
  }, [center, start, end, professionalOpen, professional, reload])

  const currencies = data?.currencies as Record<string, Row> ?? {}
  const kpiLabel: Record<string, string> = {
    all: 'Tutte le sedute',
    performed: 'Sedute svolte',
    future: 'Appuntamenti futuri',
    to_close: 'Sedute da chiudere',
    operational_paid: 'Con pagamento registrato',
    operational_unpaid: 'Svolte senza pagamento',
    cancelled: 'Sedute annullate',
    due: 'Con tariffa prevista'
  }

  const exportUrl = csvUrl('operations.reporting.export_csv', {
    center, start, end, practitioner: effectivePractitioner || '', kpi: selectedKpi || 'all', currency: selectedCurrency !== 'all' ? selectedCurrency : ''
  })

  const exportProfessional = () => {
    if (!professional || profLoading || !!profError) return
    const safe = (value: unknown) => { const text = String(value ?? ''); const guarded = /^[=+\-@\t\r\n]/.test(text.trimStart()) ? "'" + text : text; return '"' + guarded.replaceAll('"', '""') + '"' }
    const rows = [['Data', 'Ora', 'Paziente', 'Servizio', 'Stato'], ...profSessions.map(row => [displayDate(row.appointment_date), time(row.appointment_time), demoPatient(row.patient, row.patient_name, row.patient_first_name, row.patient_last_name), demoText(row.cc_service_label) || 'Seduta', row.cc_performed ? 'Svolta' : row.status === 'Cancelled' ? 'Annullata' : 'In programma'])]
    const blob = new Blob(['\ufeff' + rows.map(row => row.map(safe).join(';')).join('\r\n')], { type: 'text/csv;charset=utf-8' })
    const href = URL.createObjectURL(blob); const link = document.createElement('a'); link.href = href; link.download = 'centrochange-report-professionista.csv'; link.click(); setTimeout(() => URL.revokeObjectURL(href), 1000)
  }

  const selectKpi = (k: string, curr: string = 'all') => {
    setSelectedKpi(k)
    setSelectedCurrency(curr)
    setPage(1)
  }

  return <><Heading eyebrow="OPERATIVITÀ" title="Report" subtitle="Andamento delle sedute e dati operativi del centro." action={<div className="button-group"><Button variant="secondary" onClick={() => setProfessionalOpen(v => !v)}>Report professionisti</Button><a className="button secondary" href={exportUrl} aria-disabled={loading || !!data?.truncated}><Download size={17} /> Esporta CSV centro</a>{financeBoot && <FinanceReports boot={financeBoot} center={center} start={start} end={end} feedback={feedback} initialMode={isProfessional ? 'professionals' : 'patients'} buttonLabel="Compensi e fatture autorizzati" />}</div>} />
    <section className="panel"><div className="panel-toolbar"><div className="panel-title"><h2>Riepilogo operativo</h2><p>Pagamenti operativi distinti dal saldo contabile. Fai clic su un indicatore per filtrare le sedute.</p></div><div className="toolbar-right">{isProfessional ? <span className="agenda-practitioner-label">Report personale: <strong>{practitionerName(boot.practitioners[0] ?? { name: myPractitioner, practitioner_name: 'Mio profilo' } as Practitioner)}</strong></span> : <Field label="Professionista"><select aria-label="Filtro professionista" value={professional} onChange={event => { setProfessional(event.target.value); setPage(1) }}><option value="">Tutti i professionisti</option>{boot.practitioners.map(row => <option key={row.name} value={row.name}>{practitionerName(row)}</option>)}</select></Field>}<Field label="Dal"><DateInput value={start} onChange={v => { setStart(v); setPreset('custom'); setPage(1) }} required /></Field><Field label="Al"><DateInput value={end} onChange={v => { setEnd(v); setPreset('custom'); setPage(1) }} required /></Field></div></div>
      <div className="period-presets" role="group" aria-label="Scorciatoie periodo"><button type="button" className={preset === 'today' ? 'selected' : ''} onClick={() => applyPreset('today')}>Oggi</button><button type="button" className={preset === 'week' ? 'selected' : ''} onClick={() => applyPreset('week')}>Questa settimana</button><button type="button" className={preset === 'month' ? 'selected' : ''} onClick={() => applyPreset('month')}>Questo mese</button><button type="button" className={preset === 'last_month' ? 'selected' : ''} onClick={() => applyPreset('last_month')}>Mese scorso</button></div>
      {loading ? <p className="panel-loading">Caricamento…</p> : !Object.keys(currencies).length ? <Empty title="Nessun dato nel periodo" /> : Object.entries(currencies).map(([currency, r]) => <div className="report-currency" key={currency}>
        <div className="report-group">
          <h3 className="report-group-title">Sedute e appuntamenti ({currency === 'UNSET' ? 'Valuta da verificare' : currency})</h3>
          <div className="metrics-grid inset">
            <Metric label="Sedute totali" value={String(r.sessions ?? 0)} onClick={() => selectKpi('all', currency)} active={selectedKpi === 'all' && (selectedCurrency === currency || selectedCurrency === 'all')} />
            <Metric label="Sedute svolte" value={String(r.performed ?? 0)} tone="green" onClick={() => selectKpi('performed', currency)} active={selectedKpi === 'performed' && (selectedCurrency === currency || selectedCurrency === 'all')} />
            <Metric label="Appuntamenti futuri" value={String(r.future ?? 0)} tone="blue" onClick={() => selectKpi('future', currency)} active={selectedKpi === 'future' && (selectedCurrency === currency || selectedCurrency === 'all')} />
            <Metric label="Sedute da chiudere" value={String(r.to_close ?? 0)} tone="amber" onClick={() => selectKpi('to_close', currency)} active={selectedKpi === 'to_close' && (selectedCurrency === currency || selectedCurrency === 'all')} />
            <Metric label="Sedute annullate" value={String(r.cancelled ?? 0)} tone="purple" onClick={() => selectKpi('cancelled', currency)} active={selectedKpi === 'cancelled' && (selectedCurrency === currency || selectedCurrency === 'all')} />
          </div>
        </div>
        <div className="report-group">
          <h3 className="report-group-title">Stato pagamenti operativi</h3>
          <div className="metrics-grid inset">
            <Metric label="Con pagamento registrato" value={String(r.operational_paid ?? 0)} tone="green" onClick={() => selectKpi('operational_paid', currency)} active={selectedKpi === 'operational_paid' && (selectedCurrency === currency || selectedCurrency === 'all')} />
            <Metric label="Svolte senza pagamento" value={String(r.operational_unpaid ?? 0)} tone="amber" onClick={() => selectKpi('operational_unpaid', currency)} active={selectedKpi === 'operational_unpaid' && (selectedCurrency === currency || selectedCurrency === 'all')} />
            <Metric label="Con tariffa prevista" value={String(r.due ?? 0)} tone="purple" onClick={() => selectKpi('due', currency)} active={selectedKpi === 'due' && (selectedCurrency === currency || selectedCurrency === 'all')} />
            <Metric label="Valore tariffe previste" value={currency === 'UNSET' ? 'Da verificare' : money(r.due_snapshot_amount, currency)} tone="purple" />
          </div>
          <p className="scope-note">Valore tariffe previste: importo teorico calcolato sulle tariffe di catalogo delle sedute con economia dovuta; non costituisce estratto conto contabile né incasso.</p>
        </div>
      </div>)}{Boolean(data?.truncated) && <p className="inline-error" role="alert">Totali parziali: restringi il periodo. L'esportazione è sospesa.</p>}
      <div className="report-drilldown"><div className="report-drilldown-header"><h3>Dettaglio sedute — {kpiLabel[selectedKpi] || 'Tutte'}{selectedCurrency !== 'all' && Object.keys(currencies).length > 1 ? ` (${selectedCurrency})` : ''} ({totalSessions})</h3><div className="button-group">{selectedCurrency !== 'all' && Object.keys(currencies).length > 1 && <Button variant="secondary" onClick={() => { setSelectedCurrency('all'); setPage(1) }}>Tutte le valute</Button>}<a className={`button secondary ${sessionsError || sessionsLoading ? 'disabled' : ''}`} href={sessionsError || sessionsLoading ? undefined : exportUrl} aria-disabled={sessionsLoading || !!sessionsError || !!data?.truncated} onClick={e => { if (sessionsError || sessionsLoading) e.preventDefault() }}><Download size={16} /> Esporta CSV ({kpiLabel[selectedKpi] || 'Filtro'}{selectedCurrency !== 'all' && Object.keys(currencies).length > 1 ? ` ${selectedCurrency}` : ''})</a></div></div>{sessionsLoading ? <p className="panel-loading" role="status">Caricamento sedute…</p> : sessionsError ? <p className="inline-error" role="alert">{sessionsError}</p> : !sessions.length ? <Empty title="Nessuna seduta per questo filtro" detail="Modifica il filtro KPI o il periodo per visualizzare i record." /> : <><DataTable rows={sessions as unknown as Row[]} columns={[dateColumn('appointment_date', 'Data'), { key: 'appointment_time', label: 'Ora', render: time }, { key: 'patient_name', label: 'Paziente', render: (_v, row) => demoPatient(row.patient, row.patient_name, row.patient_first_name, row.patient_last_name) }, { key: 'practitioner_name', label: 'Professionista', render: (_v, row) => demoText(row.practitioner_name || row.practitioner) }, { key: 'cc_service_label', label: 'Servizio', render: v => demoText(v) || 'Seduta' }, { key: 'status', label: 'Stato seduta', render: (v, row) => row.cc_performed ? 'Svolta' : (v === 'Cancelled' ? 'Annullata' : (row.cc_classified_future ? 'In programma' : 'Da chiudere')) }, { key: 'cc_paid', label: 'Pagamento operativo', render: (v, row) => { if (v) return <Chip tone="good">Registrato</Chip>; if (row.status === 'Cancelled') return <Chip tone="neutral">— (annullata)</Chip>; if (row.cc_classified_future) return <Chip tone="blue">In programma</Chip>; if (['Non Due', 'Waived', 'Package Covered'].includes(String(row.cc_economic_state))) return <Chip tone="neutral">Non dovuto</Chip>; return <Chip tone="warn">Da incassare</Chip> } }, { key: 'mode_of_payment', label: 'Metodo', render: v => String(v || '—') }, { key: 'cc_price_snapshot', label: 'Tariffa prevista', render: (v, row) => v != null ? money(v, String(row.cc_currency_snapshot || 'EUR')) : '—' }]} onRow={row => setSelectedAppointment(row as unknown as Appointment)} />{totalPages > 1 && <div className="pagination-bar" role="navigation" aria-label="Paginazione sedute"><span>Pagina <strong>{page}</strong> di <strong>{totalPages}</strong> ({totalSessions} sedute totali)</span><div className="button-group"><Button variant="secondary" disabled={page <= 1 || sessionsLoading} onClick={() => setPage(p => Math.max(1, p - 1))}>Precedente</Button><Button variant="secondary" disabled={page >= totalPages || sessionsLoading} onClick={() => setPage(p => Math.min(totalPages, p + 1))}>Successiva</Button></div></div>}</>}</div>
    </section>
    {professionalOpen && <section className="panel professional-report"><div className="panel-toolbar"><div className="panel-title"><h2>Report professionisti</h2><p>Sedute del professionista nel periodo selezionato. Nessuna attribuzione contabile dedotta.</p></div><div className="toolbar-right"><Field label="Professionista"><select aria-label="Professionista report" value={professional} onChange={event => setProfessional(event.target.value)}><option value="">Seleziona</option>{boot.practitioners.map(row => <option key={row.name} value={row.name}>{practitionerName(row)}</option>)}</select></Field><Button variant="secondary" onClick={exportProfessional} disabled={!professional || profLoading || !!profError}><Download size={16} /> Esporta CSV</Button>{financeBoot && <FinanceReports boot={financeBoot} center={center} start={start} end={end} feedback={feedback} initialMode="professionals" buttonLabel="Compensi e fatture autorizzati" />}</div></div>{!professional ? <Empty title="Seleziona un professionista" /> : profLoading ? <p className="panel-loading" role="status">Caricamento sedute…</p> : profError ? <p className="inline-error" role="alert">{profError}</p> : (() => {
      const performed = profSessions.filter(row => !!row.cc_performed && row.status !== 'Cancelled').length
      const cancelled = profSessions.filter(row => row.status === 'Cancelled').length
      const toClose = profSessions.filter(row => row.cc_classified_to_close).length
      return <><div className="metrics-grid inset"><Metric label="Sedute nel periodo" value={String(profSessions.length)} /><Metric label="Sedute svolte" value={String(performed)} tone="green" /><Metric label="Sedute da chiudere" value={String(toClose)} tone="amber" /><Metric label="Sedute annullate" value={String(cancelled)} tone="purple" /></div><DataTable rows={profSessions as unknown as Row[]} columns={[dateColumn('appointment_date', 'Data'), { key: 'appointment_time', label: 'Ora', render: time }, { key: 'patient_name', label: 'Paziente', render: (value, row) => demoPatient(row.patient, value, row.patient_first_name, row.patient_last_name) }, { key: 'cc_service_label', label: 'Servizio', render: v => demoText(v) || 'Seduta' }, { key: 'status', label: 'Stato', render: (value, row) => row.cc_performed ? 'Svolta' : value === 'Cancelled' ? 'Annullata' : 'In programma' }]} onRow={row => setSelectedAppointment(row as unknown as Appointment)} /></>
    })()}</section>}
    {selectedAppointment && <AppointmentDetail row={selectedAppointment} boot={boot} center={center} onClose={() => setSelectedAppointment(null)} onSuccess={() => { setSelectedAppointment(null); setReload(x => x + 1) }} feedback={feedback} />}
  </>
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
    <section className="panel finance-panel"><div className="panel-toolbar"><div className="panel-title"><h2>{tab === 'Riepilogo' ? 'Panoramica finanziaria' : tab}</h2><p>{tab === 'Riepilogo' ? 'Valori registrati; margine da definire secondo regole approvate.' : 'Elenco circoscritto al centro selezionato.'}</p></div>{tab === 'Riepilogo' && <div className="toolbar-right"><Field label="Dal"><DateInput value={start} onChange={setStart} required /></Field><Field label="Al"><DateInput value={end} onChange={setEnd} required /></Field></div>}</div>{error && <p className="inline-error" role="alert">{error}</p>}{loading ? <p className="panel-loading" role="status">Caricamento…</p> : summary ? <><div className="metrics-grid inset"><Metric label="Ricavi netti" value={money(totals?.revenue_net)} /><Metric label="Incassato" value={money(totals?.collected)} tone="green" /><Metric label="Crediti residui" value={money(totals?.receivable_outstanding)} tone="amber" /><Metric label="Costi fornitori" value={money(totals?.purchase_net)} tone="purple" /></div><div className="finance-secondary"><div><span>Debito residuo</span><strong>{money(totals?.payable_outstanding)}</strong></div><div><span>Compensi attesi</span><strong>{money(totals?.expected_compensation)}</strong></div><div><span>Attesi da verificare</span><strong>{String(totals?.unresolved_expectations ?? 0)}</strong></div><div><span>Sedute</span><strong>{String(totals?.sessions ?? 0)}</strong></div></div><div className="summary-tables"><div><h3>Fatture pazienti</h3><DataTable rows={(summary.sales_invoices as Row[] ?? []).slice(0, 5)} columns={[{ key: 'name', label: 'Documento' }, { key: 'customer', label: 'Cliente' }, moneyColumn('outstanding_amount', 'Residuo')]} /></div><div><h3>Fatture fornitori</h3><DataTable rows={(summary.purchase_invoices as Row[] ?? []).slice(0, 5)} columns={[{ key: 'name', label: 'Documento' }, { key: 'supplier', label: 'Fornitore' }, moneyColumn('outstanding_amount', 'Residuo')]} /></div></div><p className="scope-note">Le date di registrazione regolano la contabilità; le date delle sedute regolano l’operatività. I ricavi pazienti includono il pagatore fiscale condiviso. Le fatture fornitori sono totali fiscali del fornitore, senza attribuzione dedotta ai singoli professionisti. Il margine resta da definire secondo regole approvate.</p></> : <DataTable rows={rows} columns={columns[tab]} onRow={setSelected} />}</section>{selected && <FinanceDetail row={selected} tab={tab} center={center} centers={boot.centers} canWrite={boot.can_write} assignees={boot.assignees ?? []} accounts={boot.accounts ?? []} suppliers={boot.suppliers ?? []} items={boot.items ?? []} feedback={feedback} onClose={() => setSelected(null)} onChange={() => { setSelected(null); setReload(x => x + 1) }} />}{createOpen && <FinanceCreate tab={tab} center={center} feedback={feedback} start={start} end={end} onClose={() => setCreateOpen(false)} onSuccess={() => { setCreateOpen(false); setReload(x => x + 1) }} />}</>
}

function FinanceDetail({ row, tab, center, centers, canWrite, assignees, accounts, suppliers, items, feedback, onClose, onChange }: { row: Row; tab: FinanceTab; center: string; centers: FinanceBoot['centers']; canWrite: boolean; assignees: string[]; accounts: Row[]; suppliers: Row[]; items: Row[]; feedback: Feedback; onClose: () => void; onChange: () => void }) {
  const [detail, setDetail] = useState<Row | null>(null)
  const [reason, setReason] = useState('')
  const [action, setAction] = useState(false)
  const [priority, setPriority] = useState(Number(row.priority ?? 2))
  const [assignee, setAssignee] = useState(String(row.assignee ?? ''))
  const [dueAt, setDueAt] = useState('')
  const [deferUntil, setDeferUntil] = useState('')
  const { busy, error, run } = useAction(feedback, onChange)
  useEffect(() => { let live = true; const name = String(row.name ?? ''); const method = tab === 'Fatture pazienti' ? 'receivables.position' : tab === 'Fatture fornitori' ? 'incoming.position' : tab === 'Professionisti' ? 'professional_economics.position' : null; if (method) finance<Row>(method, tab === 'Professionisti' ? { center, practitioner: row.practitioner } : { name }).then(r => { if (live) setDetail(r) }).catch(e => feedback(getError(e), true)); return () => { live = false } }, [row, tab, center])
  const title = demoText(row.invoice_number ?? row.name ?? row.reference_name ?? row.exception_type ?? 'Dettaglio')
  return <Drawer title={title} onClose={onClose}><div className="detail-summary"><Chip tone={String(row.state ?? row.status).includes('Error') ? 'bad' : 'blue'}>{financeFieldValue('state', row.state ?? row.status ?? tab)}</Chip><h3>{title}</h3><p>Centro: {centerNameFor(center, centers)}</p></div><div className="detail-section"><h3>Informazioni</h3><dl className="property-list">{Object.entries(row).filter(([k]) => !['name', 'problem'].includes(k)).map(([k, v]) => <div key={k}><dt>{financeFieldLabel(k)}</dt><dd>{financeFieldValue(k, v)}</dd></div>)}</dl>{detail && <><h3>Posizione</h3><dl className="property-list">{Object.entries(detail).filter(([, v]) => !Array.isArray(v) && typeof v !== 'object').map(([k, v]) => <div key={k}><dt>{financeFieldLabel(k)}</dt><dd>{financeFieldValue(k, v)}</dd></div>)}</dl></>}{Boolean(row.problem) && <p className="inline-error">{String(row.problem)}</p>}{canWrite && tab === 'Coda amministrativa' && <><Button variant="secondary" onClick={() => setAction(true)}>Gestisci condizione</Button>{action && <form onSubmit={e => { e.preventDefault(); void run(() => finance('admin_queue.manage', { name: row.name, priority, assignee: assignee || null, due_at: dueAt ? dueAt.replace('T', ' ') : null, defer_until: deferUntil ? deferUntil.replace('T', ' ') : null, reason }, true)) }}><Field label="Priorità" required><select value={priority} onChange={e => setPriority(Number(e.target.value))}>{[1, 2, 3, 4].map(n => <option key={n} value={n}>{n}</option>)}</select></Field><Field label="Assegnatario"><select value={assignee} onChange={e => setAssignee(e.target.value)}><option value="">Nessuno</option>{assignees.map(u => <option key={u} value={u}>{u}</option>)}</select></Field><Field label="Scadenza UTC"><input type="datetime-local" value={dueAt} onChange={e => setDueAt(e.target.value)} /></Field><Field label="Rinvio fino a UTC"><input type="datetime-local" value={deferUntil} onChange={e => setDeferUntil(e.target.value)} /></Field><Field label="Motivo" required><textarea value={reason} onChange={e => setReason(e.target.value)} required /></Field><FormError error={error} /><Button disabled={busy} type="submit">Conferma</Button></form>}</>}</div><FinanceActions row={row} tab={tab} center={center} canWrite={canWrite} accounts={accounts} suppliers={suppliers} items={items} feedback={feedback} onChange={onChange} /></Drawer>
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
      {form === 'membership' ? <Field label="Utente" required><select value={user} onChange={e => setUser(e.target.value)} required><option value="">Seleziona</option>{users.map(u => <option key={String(u.name)} value={String(u.name)}>{String(u.full_name ?? u.name)}</option>)}</select></Field> : <Field label="Professionista" required><select value={practitioner} onChange={e => setPractitioner(e.target.value)} required><option value="">Seleziona</option>{practitioners.map(p => <option key={String(p.name)} value={String(p.name)}>{String(demoText(p.practitioner_name) ?? p.name)}</option>)}</select></Field>}
      <Field label="Stato" required><select value={active} onChange={e => setActive(e.target.value)}><option value="1">Attivo</option><option value="0">Disattivo</option></select></Field>
      <Field label="Motivo" required><textarea value={reason} onChange={e => setReason(e.target.value)} required maxLength={2000} /></Field><FormError error={error} /><div className="form-actions"><Button type="button" variant="secondary" onClick={() => setForm(null)}>Annulla</Button><Button type="submit" disabled={busy}>Conferma</Button></div>
    </form></Modal>}</>
}

export function Notifications({ boot, center }: Context) {
  const personal = boot.roles.includes('CC Professional') && !boot.roles.includes('CC Manager')
  const [rows, setRows] = useState<Row[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [reload, setReload] = useState(0)
  useEffect(() => { let live = true; setLoading(true); setRows([]); setError(''); call<Row[]>('frappe.client.get_list', {
    doctype: personal ? 'Notification Log' : 'CC Notification',
    fields: personal ? ['name', 'subject', 'creation', 'read'] : ['name', 'message', 'state', 'creation'],
    limit_page_length: 100, order_by: 'creation desc'
  }).then(r => { if (live) { setRows(r); setLoading(false) } }).catch(e => { if (live) { setError(getError(e)); setLoading(false) } }); return () => { live = false } }, [center, personal, reload])
  return <><Heading eyebrow="CENTRO CHANGE" title="Notifiche" subtitle={personal ? 'Promemoria e comunicazioni personali.' : 'Esiti e comunicazioni operative.'} /><section className={`panel${personal ? ' personal-notifications' : ''}`}><div className="panel-toolbar"><div className="panel-title"><h2>Notifiche recenti</h2></div></div>{loading ? <p className="panel-loading" role="status">Caricamento notifiche…</p> : error ? <div className="notification-error" role="alert"><p>{error}</p><Button variant="secondary" onClick={() => setReload(n => n + 1)}>Riprova</Button></div> : rows.length ? <DataTable rows={rows} columns={personal ? [{ key: 'subject', label: 'Messaggio' }, { key: 'read', label: 'Lettura', render: value => value ? 'Letta' : 'Da leggere' }, dateColumn('creation', 'Data')] : [{ key: 'message', label: 'Messaggio' }, { key: 'state', label: 'Stato' }, dateColumn('creation', 'Data')]} /> : <Empty title="Nessuna notifica recente" detail="Le comunicazioni del centro appariranno qui." />}</section></>
}
