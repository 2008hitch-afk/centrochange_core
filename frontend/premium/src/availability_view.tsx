import { useEffect, useState } from 'react'
import { Plus } from 'lucide-react'
import { type Boot, type Row, ops, schedule, romeToday, displayDate, time } from './api'
import { type Feedback, Button, Chip, DateInput, Empty, Field, FormError, Heading, Modal, useAction } from './ui'
import { practitionerName } from './display_names'

const weekdays = [['Monday', 'Lunedì'], ['Tuesday', 'Martedì'], ['Wednesday', 'Mercoledì'], ['Thursday', 'Giovedì'], ['Friday', 'Venerdì'], ['Saturday', 'Sabato'], ['Sunday', 'Domenica']]
type Slot = { day: string; from_time: string; to_time: string }

export function Availability({ boot, center, feedback }: { boot: Boot; center: string; feedback: Feedback }) {
  const [rows, setRows] = useState<Row[]>([])
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState('')
  const [form, setForm] = useState<'schedule' | 'absence' | 'cancel' | null>(null)
  const [target, setTarget] = useState('')
  const [practitioner, setPractitioner] = useState(boot.practitioners[0]?.name ?? '')
  const [weekday, setWeekday] = useState('Monday')
  const [startTime, setStartTime] = useState('09:00')
  const [endTime, setEndTime] = useState('12:00')
  const [startDate, setStartDate] = useState(romeToday())
  const [endDate, setEndDate] = useState(romeToday())
  const [reason, setReason] = useState('')
  const [reload, setReload] = useState(0)
  const { busy, error, run } = useAction(feedback, () => { setForm(null); setReload(value => value + 1) })

  useEffect(() => {
    if (!center) return
    let live = true
    setLoading(true); setLoadError('')
    ops<Row[]>('workspace.schedules', { center })
      .then(value => { if (live) setRows(value) })
      .catch(cause => { if (live) setLoadError(cause instanceof Error ? cause.message : 'Disponibilità non disponibile.') })
      .finally(() => { if (live) setLoading(false) })
    return () => { live = false }
  }, [center, reload])

  const open = (kind: 'schedule' | 'absence' | 'cancel', professional = boot.practitioners[0]?.name ?? '', absence = '') => {
    setForm(kind); setPractitioner(professional); setTarget(absence); setReason('')
  }
  const save = () => {
    if (form === 'cancel') return run(() => schedule('availability.cancel_absence', { availability: target, reason }, true), 'Assenza annullata.')
    if (form === 'absence') return run(() => schedule('availability.create_absence', { practitioner, center, start_date: startDate, end_date: endDate, start_time: startTime, end_time: endTime, reason }, true), 'Assenza registrata.')
    // The backend replaces the whole native schedule. Retain every other weekday.
    const existing = rows.find(row => row.practitioner === practitioner)
    const retained = ((existing?.time_slots as Slot[] | undefined) ?? []).filter(slot => slot.day !== weekday)
    const time_slots = [...retained, { day: weekday, from_time: startTime, to_time: endTime }]
    return run(() => schedule('availability.set_schedule', { practitioner, center, time_slots, reason,
      expected_modified: existing ? String(existing.modified ?? '') : '' }, true), 'Orario aggiornato.')
  }
  return <>
    <Heading eyebrow="OPERATIVITÀ" title="Disponibilità" subtitle="Orari ricorrenti e assenze dei professionisti." action={<div className="button-group"><Button variant="secondary" onClick={() => setReload(value => value + 1)}>Aggiorna</Button><Button variant="secondary" onClick={() => open('absence')}>Registra assenza</Button><Button onClick={() => open('schedule')}><Plus size={18} /> Modifica orario</Button></div>} />
    <section className="panel"><div className="panel-toolbar"><div className="panel-title"><h2>Orari del centro</h2><p>La modifica sostituisce le fasce del giorno selezionato; le altre giornate restano.</p></div></div>
      {loadError && <p className="inline-error" role="alert">{loadError}</p>}
      {loading ? <p className="panel-loading" role="status">Caricamento…</p> : !rows.length ? <Empty title="Nessun orario configurato" /> : <div className="schedule-grid">{rows.map(row => {
        const professional = boot.practitioners.find(value => value.name === row.practitioner)
        const absences = (row.absences as Row[] | undefined) ?? []
        return <article className="schedule-card" key={String(row.name)}><span className="avatar">{practitionerName(professional ?? { name: String(row.practitioner), practitioner_name: String(row.practitioner) }).slice(0, 2).toLocaleUpperCase('it-IT')}</span><h3>{practitionerName(professional ?? { name: String(row.practitioner), practitioner_name: String(row.practitioner) })}</h3>
          {((row.time_slots as Slot[] | undefined) ?? []).map((slot, index) => <p key={`${slot.day}-${index}`}><span>{weekdays.find(day => day[0] === slot.day)?.[1] ?? slot.day}</span><strong>{time(slot.from_time)} – {time(slot.to_time)}</strong></p>)}
          {absences.length > 0 && <div className="schedule-absences"><Chip tone="warn">{absences.length} {absences.length === 1 ? 'assenza' : 'assenze'}</Chip>{absences.map(absence => <div key={String(absence.name)} className="schedule-absence"><span>{displayDate(absence.start_date)} – {displayDate(absence.end_date || absence.start_date)} · {time(absence.start_time)}–{time(absence.end_time)}</span><Button variant="ghost" onClick={() => open('cancel', String(row.practitioner), String(absence.name))}>Annulla assenza</Button></div>)}</div>}
        </article>
      })}</div>}
    </section>
    {form && <Modal title={form === 'schedule' ? 'Modifica disponibilità' : form === 'absence' ? 'Registra assenza' : 'Annulla assenza'} onClose={() => setForm(null)}><form onSubmit={event => { event.preventDefault(); void save() }}>
      {form === 'cancel' ? <p>L'assenza selezionata sarà annullata. Indica il motivo per conservarlo nel registro.</p> : <Field label="Professionista" required><select value={practitioner} onChange={event => setPractitioner(event.target.value)}>{boot.practitioners.map(value => <option key={value.name} value={value.name}>{practitionerName(value)}</option>)}</select></Field>}
      {form === 'schedule' && <Field label="Giorno" required><select value={weekday} onChange={event => setWeekday(event.target.value)}>{weekdays.map(day => <option key={day[0]} value={day[0]}>{day[1]}</option>)}</select></Field>}
      {form === 'absence' && <div className="form-grid"><Field label="Dal" required><DateInput value={startDate} onChange={setStartDate} required /></Field><Field label="Al" required><DateInput value={endDate} onChange={setEndDate} required /></Field></div>}
      {form !== 'cancel' && <div className="form-grid"><Field label="Dalle" required><input type="time" value={startTime} onChange={event => setStartTime(event.target.value)} required /></Field><Field label="Alle" required><input type="time" value={endTime} onChange={event => setEndTime(event.target.value)} required /></Field></div>}
      <Field label="Motivo" required><textarea required value={reason} onChange={event => setReason(event.target.value)} maxLength={2000} /></Field><FormError error={error} /><div className="form-actions"><Button type="button" variant="secondary" onClick={() => setForm(null)}>Indietro</Button><Button type="submit" disabled={busy || !reason.trim()}>{busy ? 'Salvataggio…' : 'Conferma'}</Button></div>
    </form></Modal>}
  </>
}
