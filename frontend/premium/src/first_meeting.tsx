import { useRef, useState } from 'react'
import { CalendarDays, Clock3, Mail, ArrowRight } from 'lucide-react'
import { type Row, displayDate, money, requestKey, romeToday, schedule, time } from './api'
import { Button, DateInput, Field, FormError } from './ui'

type Slot = { date: string; time: string }
type Projection = { route: string; service: string; duration: number; price: number; currency: string; slots: Slot[] }
const message = (error: unknown) => error instanceof Error ? error.message : 'Operazione non riuscita.'

export function FirstMeeting() {
  const [route, setRoute] = useState('Marco')
  const [start, setStart] = useState(romeToday())
  const [projection, setProjection] = useState<Projection | null>(null)
  const [selected, setSelected] = useState('')
  const [firstName, setFirstName] = useState('')
  const [lastName, setLastName] = useState('')
  const [email, setEmail] = useState('')
  const [sex, setSex] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [confirmed, setConfirmed] = useState('')
  const generation = useRef(0)
  const keys = useRef<Record<string, string>>({})
  const search = async () => {
    const id = ++generation.current
    setBusy(true); setError(''); setProjection(null); setSelected('')
    try { const result = await schedule<Projection>('public_booking.available_slots', { route, start_date: start }); if (generation.current === id) setProjection(result) }
    catch (e) { if (generation.current === id) setError(message(e)) }
    finally { if (generation.current === id) setBusy(false) }
  }
  const submit = async () => {
    const slot = projection?.slots[Number(selected)]
    if (!slot) return
    const payload = { route, first_name: firstName.trim(), last_name: lastName.trim(), email: email.trim(), sex, appointment_date: slot.date, appointment_time: slot.time }
    const key = JSON.stringify(payload)
    setBusy(true); setError('')
    try {
      const result = await schedule<Row>('public_booking.first_meeting', { ...payload, request_key: keys.current[key] ??= requestKey() }, true)
      const confirmation = result.confirmation as Row | undefined
      setConfirmed(`Primo incontro prenotato per ${displayDate(slot.date)} alle ${time(slot.time)}. ${confirmation?.state === 'Failed' ? 'Conferma email da ritentare dalla Direzione.' : 'Conferma registrata in simulazione. Nessuna email reale inviata.'}`)
    } catch (e) { setError(message(e)) }
    finally { setBusy(false) }
  }
  return <main className="public-layout"><div className="public-brand"><img src={import.meta.env.BASE_URL + 'logo.webp'} alt="Centro Change" /><strong>centro<span>change</span></strong></div><div className="public-hero"><div className="eyebrow">IL PRIMO PASSO</div><h1>Iniziamo da qui, insieme.</h1><p>Scegli il professionista e l'orario più adatto a te. La segreteria ti aiuterà per gli incontri successivi.</p></div><section className="public-card"><div className="public-card-head"><span className="public-step">01</span><div><h2>Trova il tuo orario</h2><p>Disponibilità nei prossimi sette giorni dalla data scelta.</p></div></div><form onSubmit={e => { e.preventDefault(); void search() }}><div className="form-grid"><Field label="Professionista" required><select value={route} onChange={e => { setRoute(e.target.value); setProjection(null); setSelected('') }}><option>Marco</option><option>Francesca</option></select></Field><Field label="Dal" required><DateInput value={start} onChange={v => { setStart(v); setProjection(null); setSelected('') }} required /></Field></div><Button disabled={busy} type="submit"><CalendarDays size={17} /> {busy ? 'Ricerca…' : 'Cerca disponibilità'}</Button></form>{projection && <><div className="public-service"><Clock3 size={17} /> {projection.service} · {projection.duration} min · {money(projection.price, projection.currency)}</div>{projection.slots.length ? <div className="slot-grid" role="radiogroup" aria-label="Orari disponibili">{projection.slots.map((slot, i) => <button type="button" role="radio" aria-checked={selected === String(i)} key={slot.date + slot.time} onClick={() => setSelected(String(i))}>{displayDate(slot.date)}<strong>{time(slot.time)}</strong></button>)}</div> : <p className="public-empty">Nessun orario disponibile. Prova un altro periodo.</p>}</>}{error && <FormError error={error} />}</section>{selected && !confirmed && <section className="public-card"><div className="public-card-head"><span className="public-step">02</span><div><h2>I tuoi dati</h2><p>Solo le informazioni necessarie per la prenotazione.</p></div></div><form onSubmit={e => { e.preventDefault(); void submit() }}><div className="form-grid"><Field label="Nome" required><input autoComplete="given-name" maxLength={80} value={firstName} onChange={e => setFirstName(e.target.value)} required /></Field><Field label="Cognome" required><input autoComplete="family-name" maxLength={80} value={lastName} onChange={e => setLastName(e.target.value)} required /></Field></div><Field label="Email" required><input type="email" autoComplete="email" maxLength={140} value={email} onChange={e => setEmail(e.target.value)} required /></Field><Field label="Sesso" required><select value={sex} onChange={e => setSex(e.target.value)} required><option value="">Seleziona</option><option value="Female">Femmina</option><option value="Male">Maschio</option><option value="Other">Altro</option></select></Field><Button type="submit" disabled={busy}>{busy ? 'Prenotazione…' : 'Conferma primo incontro'} <ArrowRight size={17} /></Button></form></section>}{confirmed && <section className="public-card public-confirmation" role="status"><Mail /><h2>Prenotazione registrata</h2><p>{confirmed}</p></section>}<footer className="public-footer">Centro Change · Primo incontro</footer></main>
}
