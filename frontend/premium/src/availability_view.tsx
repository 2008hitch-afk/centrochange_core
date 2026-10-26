import { useEffect, useState } from 'react'
import { Plus } from 'lucide-react'
import { type Boot, type Row, ops, schedule, romeToday, displayDate, time } from './api'
import { type Feedback, Button, Chip, DateInput, Time24Input, Empty, Field, FormError, Heading, Modal, useAction } from './ui'
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
  const [draftSlots, setDraftSlots] = useState<Slot[]>([])
  const [originalSlots, setOriginalSlots] = useState<Slot[]>([])
  const [expectedModified, setExpectedModified] = useState('')
  const [reviewed, setReviewed] = useState(false)
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

  const resetSchedule = (person: string) => {
    const existing = rows.find(row => row.practitioner === person)
    const slots = ((existing?.time_slots as Slot[] | undefined) ?? []).map(slot => ({
      day: slot.day, from_time: time(slot.from_time), to_time: time(slot.to_time)
    }))
    setOriginalSlots(slots)
    setDraftSlots(slots.map(slot => ({ ...slot })))
    setExpectedModified(existing ? String(existing.modified ?? '') : '')
    setReviewed(false)
  }
  const open = (kind: 'schedule' | 'absence' | 'cancel', professional = boot.practitioners[0]?.name ?? '', absence = '') => {
    setForm(kind); setPractitioner(professional); setTarget(absence); setReason('')
    if (kind === 'schedule') { setWeekday('Monday'); resetSchedule(professional) }
    if (kind === 'absence') {
      setStartDate(romeToday()); setEndDate(romeToday())
      setStartTime('09:00'); setEndTime('12:00')
    }
  }
  const editSlot = (index: number, patch: Partial<Slot>) => {
    setDraftSlots(current => current.map((slot, i) => i === index ? { ...slot, ...patch } : slot))
    setReviewed(false)
  }
  const timeValid = (value: string) => /^(?:[01][0-9]|2[0-3]):[0-5][0-9]$/.test(value)
  const slotsValid = draftSlots.length > 0 && draftSlots.every(slot => timeValid(slot.from_time) && timeValid(slot.to_time) && slot.from_time < slot.to_time) &&
    !draftSlots.some((slot, index) => draftSlots.some((other, second) => index !== second && slot.day === other.day && slot.from_time < other.to_time && slot.to_time > other.from_time))
  const scheduleChanged = JSON.stringify(draftSlots) !== JSON.stringify(originalSlots)
  const daySlots = draftSlots.map((slot, index) => ({ slot, index })).filter(entry => entry.slot.day === weekday)
  const save = () => {
    if (form === 'cancel') return run(() => schedule('availability.cancel_absence', { availability: target, reason }, true), 'Assenza annullata.')
    if (form === 'absence') return run(() => schedule('availability.create_absence', { practitioner, center, start_date: startDate, end_date: endDate, start_time: startTime, end_time: endTime, reason }, true), 'Assenza registrata.')
    // Send the complete reviewed snapshot: all other weekdays and multiple daily slots stay intact.
    if (!reviewed || !slotsValid || !scheduleChanged || loading || loadError) return Promise.resolve(false)
    return run(() => schedule('availability.set_schedule', {
      practitioner, center, time_slots: draftSlots, reason, expected_modified: expectedModified
    }, true), 'Orario aggiornato.')
  }
  return <>
    <Heading eyebrow="OPERATIVITÀ" title="Disponibilità" subtitle="Orari ricorrenti e assenze dei professionisti." action={<div className="button-group"><Button variant="secondary" onClick={() => setReload(value => value + 1)}>Aggiorna</Button><Button variant="secondary" onClick={() => open('absence')}>Registra assenza</Button><Button disabled={loading || !!loadError} onClick={() => open('schedule')}><Plus size={18} /> Modifica orario</Button></div>} />
    <section className="panel"><div className="panel-toolbar"><div className="panel-title"><h2>Orari del centro</h2><p>Verifica tutte le fasce prima di salvare: le altre giornate restano invariate.</p></div></div>
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
      {form === 'cancel' ? <p>L'assenza selezionata sarà annullata. Indica il motivo per conservarlo nel registro.</p> : <Field label="Professionista" required><select value={practitioner} onChange={event => { setPractitioner(event.target.value); if (form === 'schedule') resetSchedule(event.target.value) }}>{boot.practitioners.map(value => <option key={value.name} value={value.name}>{practitionerName(value)}</option>)}</select></Field>}
      {form === 'schedule' && <>
        <Field label="Giorno da modificare" required><select value={weekday} onChange={event => { setWeekday(event.target.value); setReviewed(false) }}>{weekdays.map(day => <option key={day[0]} value={day[0]}>{day[1]}</option>)}</select></Field>
        <div className="schedule-editor">
          <p className="scope-note">Fasce attuali del giorno selezionato. Modifica, aggiungi o rimuovi solo quelle necessarie.</p>
          {daySlots.map(({ slot, index }) => <div className="schedule-editor-slot" key={index}>
            <Field label={`Dalle (fascia ${daySlots.findIndex(item => item.index === index) + 1})`} required><Time24Input value={slot.from_time} onChange={value => editSlot(index, { from_time: value })} /></Field>
            <Field label="Alle" required><Time24Input value={slot.to_time} onChange={value => editSlot(index, { to_time: value })} /></Field>
            <Button type="button" variant="secondary" onClick={() => { setDraftSlots(current => current.filter((_, i) => i !== index)); setReviewed(false) }}>Rimuovi</Button>
          </div>)}
          {!daySlots.length && <p>Nessuna fascia prevista per questo giorno.</p>}
          <Button type="button" variant="secondary" onClick={() => { setDraftSlots(current => [...current, { day: weekday, from_time: '09:00', to_time: '12:00' }]); setReviewed(false) }}><Plus size={16} /> Aggiungi fascia</Button>
          {!slotsValid && <p className="inline-error" role="alert">Controlla gli orari: usa HH:mm (24 ore), intervalli validi e senza sovrapposizioni. Mantieni almeno una fascia settimanale.</p>}
          <p className="scope-note">Orario precedente: {originalSlots.map(slot => `${weekdays.find(day => day[0] === slot.day)?.[1] ?? slot.day}: ${slot.from_time}–${slot.to_time}`).join('; ') || 'nessuno'}.</p>
          <p className="scope-note">Nuovo orario completo: {draftSlots.map(slot => `${weekdays.find(day => day[0] === slot.day)?.[1] ?? slot.day}: ${slot.from_time}–${slot.to_time}`).join('; ') || 'nessuno'}.</p>
          <label className="checkbox-row"><input type="checkbox" checked={reviewed} onChange={event => setReviewed(event.target.checked)} /> Ho verificato le fasce precedenti e quelle nuove; confermo questa modifica.</label>
        </div>
      </>}
      {form === 'absence' && <div className="form-grid"><Field label="Dal" required><DateInput value={startDate} onChange={setStartDate} required /></Field><Field label="Al" required><DateInput value={endDate} onChange={setEndDate} required /></Field></div>}
      {form === 'absence' && <div className="form-grid"><Field label="Dalle" required><Time24Input value={startTime} onChange={setStartTime} /></Field><Field label="Alle" required><Time24Input value={endTime} onChange={setEndTime} /></Field></div>}
      <Field label="Motivo" required><textarea required value={reason} onChange={event => setReason(event.target.value)} maxLength={2000} /></Field><FormError error={error} /><div className="form-actions"><Button type="button" variant="secondary" onClick={() => setForm(null)}>Indietro</Button><Button type="submit" disabled={busy || !reason.trim() || (form === 'schedule' && (!slotsValid || !reviewed || !scheduleChanged))}>{busy ? 'Salvataggio…' : 'Conferma'}</Button></div>
    </form></Modal>}
  </>
}
