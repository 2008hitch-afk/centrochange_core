import { useEffect, useState } from 'react'
import dayjs from 'dayjs'
import { type Row, call, displayDate, romeToday } from './api'
import { type Feedback, Button, DataTable, DateInput, Drawer, Field, Heading } from './ui'

const labels: Record<string, string> = {
  APPOINTMENT_BOOKED: 'Prenotazione creata', APPOINTMENT_RESCHEDULED: 'Prenotazione spostata',
  SESSION_CANCELLED: 'Seduta cancellata', SESSION_CLOSED: 'Seduta chiusa',
  SESSION_REOPENED: 'Seduta riaperta', ORGANIZATIONAL_NOTE_CREATED: 'Nota organizzativa registrata',
  PRIVATE_NOTE_CREATED: 'Nota professionale registrata', PACKAGE_ISSUED: 'Pacchetto emesso',
  CENTER_MEMBERSHIP: 'Appartenenza al centro', PATIENT_ASSIGNMENT: 'Assegnazione paziente',
  RECEIPT_POSTED: 'Pagamento registrato', PROFESSIONAL_RULE_CONFIGURED: 'Regola compenso configurata',
  SCHEDULE_CHANGED: 'Orario aggiornato', ABSENCE_CREATED: 'Assenza registrata',
  ABSENCE_CANCELLED: 'Assenza annullata', SESSION_AUTO_LOCKED: 'Chiusura seduta bloccata automaticamente',
  SESSION_LATE_COMPLETED: 'Chiusura tardiva seduta'
}
const eventName = (value: unknown) => labels[String(value)] ?? 'Modifica registrata'
const eventStamp = (value: unknown) => {
  const raw = String(value ?? '')
  return raw ? `${displayDate(raw)}${raw.length >= 16 ? ' · ' + raw.slice(11, 16) : ''}` : 'Data non disponibile'
}
const parse = (value: unknown): Row => {
  try { const parsed = JSON.parse(String(value ?? '{}')); return parsed && typeof parsed === 'object' && !Array.isArray(parsed) ? parsed as Row : {} }
  catch { return {} }
}

interface ScheduleSlot {
  day: string
  from_time: string
  to_time: string
}

const dayOrder = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
const dayNamesItalian: Record<string, string> = {
  Monday: 'Lunedì',
  Tuesday: 'Martedì',
  Wednesday: 'Mercoledì',
  Thursday: 'Giovedì',
  Friday: 'Venerdì',
  Saturday: 'Sabato',
  Sunday: 'Domenica'
}

const parseSlots = (val: unknown): ScheduleSlot[] | null => {
  if (val == null || val === '') return []
  let arr: unknown = val
  if (typeof val === 'string') {
    try { arr = JSON.parse(val) }
    catch { return null }
  }
  if (!Array.isArray(arr)) return null
  const valid: ScheduleSlot[] = []
  for (const item of arr) {
    if (item && typeof item === 'object') {
      const row = item as Record<string, unknown>
      const day = String(row.day ?? '').trim()
      const from = String(row.from_time ?? '').trim()
      const to = String(row.to_time ?? '').trim()
      if (day) {
        valid.push({
          day,
          from_time: from.length >= 5 ? from.slice(0, 5) : from,
          to_time: to.length >= 5 ? to.slice(0, 5) : to
        })
      }
    }
  }
  return valid
}

const groupSlotsByDay = (slots: ScheduleSlot[]): Record<string, string[]> => {
  const map: Record<string, string[]> = {}
  for (const slot of slots) {
    if (!map[slot.day]) map[slot.day] = []
    const formatted = slot.from_time && slot.to_time ? `${slot.from_time} – ${slot.to_time}` : (slot.from_time || '—')
    map[slot.day].push(formatted)
  }
  for (const day of Object.keys(map)) {
    map[day].sort()
  }
  return map
}

interface ScheduleDayChange {
  day: string
  dayItalian: string
  beforeText: string
  afterText: string
}

const diffSchedule = (beforeSlots: ScheduleSlot[] | null, afterSlots: ScheduleSlot[] | null) => {
  if (beforeSlots === null || afterSlots === null) {
    return { changes: [] as ScheduleDayChange[], status: 'malformed' as const }
  }
  if (beforeSlots.length === 0 && afterSlots.length === 0) {
    return { changes: [] as ScheduleDayChange[], status: 'empty' as const }
  }

  const beforeGroup = groupSlotsByDay(beforeSlots)
  const afterGroup = groupSlotsByDay(afterSlots)

  const allDaysSet = new Set([...Object.keys(beforeGroup), ...Object.keys(afterGroup)])
  const allDays = Array.from(allDaysSet).sort((a, b) => {
    const idxA = dayOrder.indexOf(a)
    const idxB = dayOrder.indexOf(b)
    return (idxA !== -1 ? idxA : 99) - (idxB !== -1 ? idxB : 99)
  })

  const changes: ScheduleDayChange[] = []
  for (const day of allDays) {
    const bSlots = beforeGroup[day] || []
    const aSlots = afterGroup[day] || []
    const bStr = bSlots.join(', ')
    const aStr = aSlots.join(', ')
    if (bStr !== aStr) {
      changes.push({
        day,
        dayItalian: dayNamesItalian[day] || day,
        beforeText: bStr || 'Nessuna fascia oraria',
        afterText: aStr || 'Nessuna fascia oraria'
      })
    }
  }

  if (changes.length === 0) {
    return { changes: [] as ScheduleDayChange[], status: 'identical' as const }
  }

  return { changes, status: 'ok' as const }
}
const words: Record<string, string> = { appointment: 'seduta', patient: 'paziente', practitioner: 'professionista', center: 'centro', time: 'ora', date: 'data', paid: 'pagata', economic: 'economico', closure: 'chiusura', state: 'stato', status: 'stato', service: 'servizio', price: 'prezzo', currency: 'valuta', reason: 'motivo', duration: 'durata', package: 'pacchetto', supplier: 'fornitore', amount: 'importo', previous: 'precedente', new: 'nuovo' }
const fieldLabels: Record<string, string> = {
  appointment_time: 'Ora seduta',
  appointment_date: 'Data seduta',
  start_date: 'Data inizio',
  end_date: 'Data fine',
  start_time: 'Ora inizio',
  end_time: 'Ora fine',
  from_time: 'Ora inizio',
  to_time: 'Ora fine',
  docstatus: 'Stato del documento'
}
const label = (key: string, event: string) => {
  const lower = key.toLowerCase()
  if (event === 'CENTER_MEMBERSHIP' && lower === 'active') return 'Stato appartenenza'
  if (fieldLabels[lower]) return fieldLabels[lower]
  if (fieldLabels[key]) return fieldLabels[key]
  return key.split('_').map(word => words[word.toLowerCase()] ?? word).join(' ')
}
const textValue = (key: string, value: unknown, event: string, present: boolean) => {
  if (!present) return 'Non registrato'
  if (value == null || value === '') return 'Non indicato'
  if (key.toLowerCase() === 'docstatus') {
    const num = Number(value)
    if (num === 0) return 'Bozza'
    if (num === 1) return 'Confermato'
    if (num === 2) return 'Annullato'
  }
  if (event === 'CENTER_MEMBERSHIP' && key.toLowerCase() === 'active' && [0, 1, '0', '1', true, false].includes(value as never))
    return Number(value) === 1 ? 'Attivo' : 'Disattivo'
  if (typeof value === 'boolean') return value ? 'Sì' : 'No'
  if (typeof value === 'object') return JSON.stringify(value)
  const text = String(value)
  if (key.includes('time') && /^\d\d:\d\d:\d\d$/.test(text)) return text.slice(0, 5)
  if (key.includes('date') && /^\d{4}-\d\d-\d\d/.test(text)) return displayDate(text)
  return text
}

export function AuditLog({ feedback }: { feedback: Feedback }) {
  const [start, setStart] = useState(dayjs(romeToday()).startOf('month').format('YYYY-MM-DD'))
  const [end, setEnd] = useState(romeToday())
  const [reference, setReference] = useState('')
  const [query, setQuery] = useState('')
  const [offset, setOffset] = useState(0)
  const [rows, setRows] = useState<Row[]>([])
  const [hasMore, setHasMore] = useState(false)
  const [selected, setSelected] = useState<Row | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  useEffect(() => {
    let live = true
    setLoading(true); setError('')
    call<{ events: Row[]; has_more: boolean }>('security.audit_view.events', { start, end, reference: query, offset })
      .then(result => { if (live) { setRows(result.events); setHasMore(result.has_more); setLoading(false) } })
      .catch(e => { if (live) { const message = e instanceof Error ? e.message : 'Registro non disponibile.'; setError(message); setLoading(false); feedback(message, true) } })
    return () => { live = false }
  }, [start, end, query, offset])
  const isSchedule = selected?.event_type === 'SCHEDULE_CHANGED'
  const scheduleDiff = isSchedule ? diffSchedule(parseSlots(selected?.before_state), parseSlots(selected?.after_state)) : null
  const before = selected && !isSchedule ? parse(selected.before_state) : {}
  const after = selected && !isSchedule ? parse(selected.after_state) : {}
  const changes = Array.from(new Set([...Object.keys(before), ...Object.keys(after)])).filter(key => JSON.stringify(before[key]) !== JSON.stringify(after[key]))
  return <><Heading eyebrow="AMMINISTRAZIONE" title="Registro modifiche" subtitle="Consulta le modifiche registrate, chi le ha effettuate e il relativo motivo." />
    <section className="panel"><div className="panel-toolbar audit-filters"><div className="panel-title"><h2>Eventi</h2><p>Filtra per periodo o riferimento. L'ora mostrata è quella registrata dal sito.</p></div><div className="toolbar-right"><Field label="Dal"><DateInput value={start} onChange={value => { setStart(value); setOffset(0) }} required /></Field><Field label="Al"><DateInput value={end} onChange={value => { setEnd(value); setOffset(0) }} required /></Field></div></div>
      <form className="audit-search" onSubmit={e => { e.preventDefault(); setQuery(reference); setOffset(0) }}><Field label="Riferimento documento"><input value={reference} onChange={e => setReference(e.target.value)} maxLength={140} placeholder="Codice o parte del codice" /></Field><Button type="submit" variant="secondary">Cerca</Button></form>
      {error && <p className="inline-error" role="alert">{error}</p>}{loading ? <p className="panel-loading" role="status">Caricamento eventi…</p> : <DataTable rows={rows} columns={[{ key: 'event_type', label: 'Evento', render: value => eventName(value) }, { key: 'event_time', label: 'Quando', render: eventStamp }, { key: 'actor', label: 'Autore' }, { key: 'reference_name', label: 'Riferimento' }, { key: 'reason', label: 'Motivo' }]} onRow={setSelected} />}
      <div className="audit-pager"><Button variant="secondary" disabled={offset === 0} onClick={() => setOffset(value => Math.max(0, value - 100))}>Precedenti</Button><span>Pagina {Math.floor(offset / 100) + 1}</span><Button variant="secondary" disabled={!hasMore} onClick={() => setOffset(value => value + 100)}>Successivi</Button></div>
    </section>{selected && <Drawer title={eventName(selected.event_type)} onClose={() => setSelected(null)}><div className="detail-summary"><p>{eventStamp(selected.event_time)} · {String(selected.actor ?? 'Autore non disponibile')}</p><p>Riferimento: {String(selected.reference_name ?? '—')}</p></div><div className="detail-section"><h3>Motivo</h3><p>{String(selected.reason ?? '—')}</p><h3>Cosa è cambiato</h3>{isSchedule && scheduleDiff ? (scheduleDiff.status === 'malformed' ? <p>Dati dell’orario non disponibili o non conformi.</p> : scheduleDiff.status === 'empty' ? <p>Nessuna fascia oraria definita.</p> : scheduleDiff.status === 'identical' ? <p>Nessuna variazione di orario registrata.</p> : <div className="audit-changes">{scheduleDiff.changes.map(c => <div key={c.day}><strong>{c.dayItalian}</strong><p><span>Prima:</span> {c.beforeText}</p><p><span>Dopo:</span> {c.afterText}</p></div>)}</div>) : changes.length ? <div className="audit-changes">{changes.map(key => <div key={key}><strong>{label(key, String(selected.event_type ?? ''))}</strong><p><span>Prima:</span> {textValue(key, before[key], String(selected.event_type ?? ''), Object.prototype.hasOwnProperty.call(before, key))}</p><p><span>Dopo:</span> {textValue(key, after[key], String(selected.event_type ?? ''), Object.prototype.hasOwnProperty.call(after, key))}</p></div>)}</div> : <p>Dettaglio della modifica non disponibile in forma comparabile.</p>}<p className="scope-note">Il registro conserva l'evento originale; questa vista mostra solo la differenza leggibile.</p></div></Drawer>}</>
}
