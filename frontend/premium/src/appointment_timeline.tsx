import { type Row, displayDate, time } from './api'
import { Empty } from './ui'
import { auditActorName, closureName, economyName } from './display_names'

const events: Record<string, string> = {
  APPOINTMENT_BOOKED: 'Prenotazione creata',
  APPOINTMENT_RESCHEDULED: 'Prenotazione spostata',
  SESSION_CANCELLED: 'Seduta cancellata',
  SESSION_CLOSED: 'Seduta chiusa',
  SESSION_AUTO_LOCKED: 'Seduta bloccata automaticamente',
  SESSION_REOPENED: 'Seduta riaperta',
  ECONOMIC_WAIVER: 'Rinuncia economica registrata',
  OPERATIONAL_SETTLEMENT: 'Pagamento operativo registrato'
}
const fields: Record<string, string> = {
  appointment_date: 'Data', appointment_time: 'Ora', late: 'Disdetta tardiva',
  economic: 'Stato economico', performed: 'Seduta svolta', closure: 'Chiusura',
  paid: 'Pagata', method: 'Metodo di pagamento'
}
const fact = (key: string, value: unknown) => {
  if (value == null || value === '') return '—'
  if (key === 'appointment_date') return displayDate(value)
  if (key === 'appointment_time') return time(value)
  if (key === 'economic') return economyName(String(value))
  if (key === 'closure') return closureName(String(value))
  if (['late', 'performed', 'paid'].includes(key)) return value === true || value === 1 ? 'Sì' : 'No'
  return String(value)
}
const stamp = (value: unknown) => {
  const raw = String(value ?? '')
  return raw ? `${displayDate(raw)}${raw.length >= 16 ? ` · ${time(raw.slice(11))}` : ''}` : 'Data non disponibile'
}

export function AppointmentTimeline({ rows }: { rows: Row[] }) {
  if (!rows.length) return <Empty title="Nessun evento registrato per questa seduta" />
  return <div className="timeline appointment-timeline">{rows.map((row, index) => {
    const before = row.before && typeof row.before === 'object' && !Array.isArray(row.before) ? row.before as Row : {}
    const after = row.after && typeof row.after === 'object' && !Array.isArray(row.after) ? row.after as Row : {}
    const changes = Array.from(new Set([...Object.keys(before), ...Object.keys(after)]))
      .filter(key => JSON.stringify(before[key]) !== JSON.stringify(after[key]))
    return <article key={`${String(row.event_type)}-${String(row.event_time)}-${index}`}>
      <strong>{events[String(row.event_type)] ?? 'Modifica registrata'}</strong>
      <span>{stamp(row.event_time)} · {auditActorName(row.actor)}</span>
      {Boolean(row.reason) && <p><b>Motivo:</b> {String(row.reason)}</p>}
      {changes.length > 0 && <dl>{changes.map(key => <div key={key}><dt>{fields[key] ?? 'Dettaglio'}</dt><dd>{key in before ? `${fact(key, before[key])} → ${fact(key, after[key])}` : fact(key, after[key])}</dd></div>)}</dl>}
    </article>
  })}</div>
}
