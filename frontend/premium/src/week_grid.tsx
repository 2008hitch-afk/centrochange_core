import { type Appointment, type Row, displayDate, time, romeToday } from './api'
import { demoPatient, demoText } from './demo_labels'

type Resource = { id: string; title: string }
type Positioned = { row: Appointment; top: number; height: number; lane: number; lanes: number }
const pixelsPerMinute = 0.8
const minutes = (value: string) => {
  const [hours, mins] = String(value).split(':').map(Number)
  return Number.isFinite(hours) && Number.isFinite(mins) ? hours * 60 + mins : 0
}
const clock = (value: number) => `${String(Math.floor(value / 60)).padStart(2, '0')}:00`

function position(rows: Appointment[], first: number): Positioned[] {
  const sorted = [...rows].sort((a, b) => minutes(a.appointment_time) - minutes(b.appointment_time) || a.name.localeCompare(b.name))
  const result: Positioned[] = []
  let cluster: { row: Appointment; start: number; end: number; lane: number }[] = []
  let clusterEnd = 0
  const flush = () => {
    const lanes = Math.max(1, ...cluster.map(item => item.lane + 1))
    cluster.forEach(item => result.push({ row: item.row, top: (item.start - first) * pixelsPerMinute,
      height: Math.max(32, (item.end - item.start) * pixelsPerMinute), lane: item.lane, lanes }))
    cluster = []; clusterEnd = 0
  }
  for (const row of sorted) {
    const start = minutes(row.appointment_time)
    const end = start + Math.max(1, Number(row.duration) || 60)
    if (cluster.length && start >= clusterEnd) flush()
    const used = new Set(cluster.filter(item => item.end > start).map(item => item.lane))
    let lane = 0
    while (used.has(lane)) lane++
    cluster.push({ row, start, end, lane })
    clusterEnd = Math.max(clusterEnd, end)
  }
  if (cluster.length) flush()
  return result
}

export function WeekGrid({ days, resources, rows, schedules, onSelect, onBook }: {
  days: string[]; resources: Resource[]; rows: Appointment[]; schedules?: Row[];
  onSelect: (row: Appointment) => void; onBook: (day: string, practitioner: string) => void
}) {
  const today = romeToday()
  const visible = rows.filter(row => days.includes(row.appointment_date) && resources.some(resource => resource.id === row.practitioner))
  const first = Math.max(0, Math.floor(Math.min(8 * 60, ...visible.map(row => minutes(row.appointment_time))) / 60) * 60)
  const last = Math.min(24 * 60, Math.ceil(Math.max(20 * 60, ...visible.map(row => minutes(row.appointment_time) + (Number(row.duration) || 60))) / 60) * 60)
  const height = (last - first) * pixelsPerMinute
  const ticks = Array.from({ length: Math.ceil((last - first) / 120) + 1 }, (_, index) => first + index * 120).filter(value => value <= last)
  return <div className="week-scroll" role="region" aria-label="Agenda settimanale" tabIndex={0}>
    <div className="week-grid" style={{ '--week-timeline-height': `${height}px` } as React.CSSProperties}>
      <div className="week-header"><div className="week-corner">Professionista</div>{days.map(day => <div className={`week-day ${day === today ? 'week-day-today' : ''}`} key={day} data-date={day}><strong>{new Intl.DateTimeFormat('it-IT', { weekday: 'long' }).format(new Date(`${day}T12:00:00`))}</strong><span>{displayDate(day)}</span>{day === today && <span className="today-badge">Oggi</span>}</div>)}</div>
      {resources.map(resource => {
        const schedule = schedules?.find(s => s.practitioner === resource.id)
        return <div className="week-row" key={resource.id} data-practitioner={resource.id}>
          <div className="week-professional"><span className="avatar">{demoText(resource.title).slice(0, 2).toLocaleUpperCase('it-IT')}</span><strong>{demoText(resource.title)}</strong><div className="week-hour-axis" aria-hidden="true">{ticks.map(tick => <span key={tick} style={{ top: `${(tick - first) * pixelsPerMinute}px` }}>{clock(tick)}</span>)}</div></div>
          {days.map(day => {
            const weekdayEn = new Intl.DateTimeFormat('en-US', { weekday: 'long' }).format(new Date(`${day}T12:00:00`))
            const daySlots = (schedule?.time_slots as { day: string; from_time: string; to_time: string }[] | undefined)?.filter(slot => slot.day === weekdayEn) ?? []
            const absences = (schedule?.absences as { start_date: string; end_date: string; start_time?: string; end_time?: string }[] | undefined)?.filter(a => day >= a.start_date && day <= a.end_date) ?? []
            const isOff = schedule && daySlots.length === 0
            const hasAbsence = absences.length > 0
            return <div className={`week-cell ${isOff ? 'week-cell-off' : ''}`} key={day} data-date={day} data-practitioner={resource.id}>
              {hasAbsence && <div className="week-absence-block" title="Assenza registrata">Assenza / Non disponibile</div>}
              {isOff && !hasAbsence && <div className="week-off-indicator" aria-hidden="true">Non in servizio</div>}
              <div className="week-sessions">{position(visible.filter(row => row.practitioner === resource.id && row.appointment_date === day), first).map(({ row, top, height: eventHeight, lane, lanes }) => <button key={row.name} className={`week-event ${row.status === 'Cancelled' ? 'event-cancelled' : row.cc_performed ? 'event-done' : 'event-booked'}`} data-time={time(row.appointment_time)} style={{ top: `${top}px`, height: `${eventHeight}px`, left: `${lane * 100 / lanes}%`, width: `${100 / lanes}%` }} onClick={() => onSelect(row)} aria-label={`${time(row.appointment_time)} ${demoPatient(row.patient, row.patient_name, row.patient_first_name, row.patient_last_name)} · ${demoText(row.cc_service_label) || 'Seduta'}`}><time>{time(row.appointment_time)}</time><strong>{demoPatient(row.patient, row.patient_name, row.patient_first_name, row.patient_last_name)}</strong><span>{demoText(row.cc_service_label) || 'Seduta'}</span></button>)}</div>
              <button className="week-add" aria-label={`Nuova prenotazione ${demoText(resource.title)} ${displayDate(day)}`} onClick={() => onBook(day, resource.id)}>+</button>
            </div>
          })}
        </div>
      })}
    </div>
  </div>
}
