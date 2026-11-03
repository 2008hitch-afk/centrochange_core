import { useRef, useState } from 'react'
import { ArrowLeft, ArrowRight, CalendarDays, Check, Clock3, Mail, MapPin, MonitorPlay, ShieldCheck, UserRound } from 'lucide-react'
import { type Row, displayDate, requestKey, romeToday, schedule, time } from './api'
import { DateInput, Field, FormError } from './ui'

type Mode = 'sede' | 'online'
type Director = 'Marco' | 'Francesca'
type Slot = { date: string; time: string }
type Projection = {
  route: Director; mode: Mode; service: string; duration: number
  price: number; currency: string; slots: Slot[]
}
const modeNames: Record<Mode, string> = { sede: 'In sede', online: 'Online' }
const steps = ['Modalità', 'Direttore', 'Data e ora', 'I tuoi dati']
const errorText = (value: unknown) => value instanceof Error ? value.message : 'Prenotazione non riuscita. Riprova.'

export function FirstMeeting() {
  const [step, setStep] = useState(0)
  const [mode, setMode] = useState<Mode | null>(null)
  const [route, setRoute] = useState<Director | null>(null)
  const [start, setStart] = useState(romeToday())
  const [projection, setProjection] = useState<Projection | null>(null)
  const [selected, setSelected] = useState('')
  const [firstName, setFirstName] = useState('')
  const [lastName, setLastName] = useState('')
  const [email, setEmail] = useState('')
  const [sex, setSex] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [confirmed, setConfirmed] = useState(false)
  const generation = useRef(0)
  const keys = useRef<Record<string, string>>({})
  const chosenSlot = projection?.slots.find(slot => slot.date + ' ' + slot.time === selected)

  const invalidate = () => {
    generation.current += 1
    setProjection(null)
    setSelected('')
    setError('')
    setBusy(false)
  }
  const selectMode = (value: Mode) => {
    if (value !== mode) {
      setMode(value); setRoute(null); invalidate()
    }
  }
  const selectDirector = (value: Director) => {
    if (value !== route) { setRoute(value); invalidate() }
  }
  const search = async () => {
    if (!mode || !route) return
    const id = ++generation.current
    setBusy(true); setError(''); setSelected(''); setProjection(null)
    try {
      const data = await schedule<Projection>('public_booking.available_slots',
        { route, mode, start_date: start })
      if (id !== generation.current) return
      if (data.mode !== mode || data.route !== route || Number(data.duration) !== 20 ||
        Number(data.price) !== 0 || data.currency !== 'EUR' || !Array.isArray(data.slots)) {
        throw new Error('Il colloquio gratuito non è configurato correttamente. Contatta la segreteria.')
      }
      setProjection(data)
    } catch (failure) {
      if (id === generation.current) setError(errorText(failure))
    } finally {
      if (id === generation.current) setBusy(false)
    }
  }
  const submit = async () => {
    if (!mode || !route || !chosenSlot || !projection || busy) return
    const payload = {
      mode, route, first_name: firstName.trim(), last_name: lastName.trim(),
      email: email.trim(), sex, appointment_date: chosenSlot.date, appointment_time: chosenSlot.time
    }
    const identity = JSON.stringify(payload)
    setBusy(true); setError('')
    try {
      await schedule<Row>('public_booking.first_meeting',
        { ...payload, request_key: keys.current[identity] ??= requestKey() }, true)
      setConfirmed(true); setStep(4)
    } catch (failure) { setError(errorText(failure)) }
    finally { setBusy(false) }
  }
  const next = () => {
    if (step === 0 && mode || step === 1 && route || step === 2 && chosenSlot) {
      setError(''); setStep(value => Math.min(value + 1, 3))
    }
  }
  const back = () => {
    if (step > 0 && step < 4) { setError(''); setStep(value => value - 1) }
  }
  const summary = <div className="booking-summary-content">
    <div className="booking-summary-title">
      <img src={import.meta.env.BASE_URL + 'logo.webp'} alt="" width="52" height="52" />
      <div><strong>Centro Change</strong><span>Bergamo · Primo incontro</span></div>
    </div>
    <div className="booking-summary-divider" />
    <div className="booking-summary-row"><span>Modalità</span><strong>{mode ? modeNames[mode] : 'Da scegliere'}</strong></div>
    <div className="booking-summary-row"><span>Direttore</span><strong>{route ?? 'Da scegliere'}</strong></div>
    <div className="booking-summary-row"><span>Giorno e ora</span><strong>{chosenSlot ? displayDate(chosenSlot.date) + ' · ' + time(chosenSlot.time) : 'Da scegliere'}</strong></div>
    <div className="booking-summary-divider" />
    <div className="booking-summary-row"><span>Colloquio conoscitivo</span><strong>20 minuti</strong></div>
    <div className="booking-summary-price"><strong>Totale</strong><strong>Gratuito · 0 €</strong></div>
    <p className="booking-summary-note">La prima seduta completa verrà concordata successivamente con la segreteria.</p>
  </div>

  return <main className="booking-public" id="cc-main">
    <a className="booking-skip" href="#booking-content">Vai alla prenotazione</a>
    <header className="booking-top">
      <div className="booking-brand"><img src={import.meta.env.BASE_URL + 'logo.webp'} alt="" width="36" height="36" /><span>Centro Change</span></div>
      <span className="booking-top-caption"><ShieldCheck size={17} aria-hidden="true" /> Prenotazione protetta</span>
    </header>
    <div className="booking-layout">
      <div id="booking-content" className="booking-main" tabIndex={-1}>
        {step < 4 && <nav className="booking-progress" aria-label="Avanzamento prenotazione">
          {steps.map((label, i) => <span key={label} aria-current={step === i ? 'step' : undefined}
            className={'booking-progress-item ' + (i <= step ? 'active' : '')}>
            <span className="booking-progress-num">{i < step ? <Check size={15} aria-hidden="true" /> : i + 1}</span>
            <span>{label}</span>
          </span>)}
        </nav>}
        {step === 0 && <section className="booking-stage">
          <p className="booking-eyebrow">IL TUO PRIMO PASSO</p>
          <h1>Prenota il tuo primo incontro</h1>
          <p className="booking-intro">Inizia con un colloquio conoscitivo gratuito di 20 minuti con uno dei Direttori del centro.</p>
          <h2>Scegli come incontrarci</h2>
          <div className="booking-mode-list" role="radiogroup" aria-label="Modalità del primo incontro">
            <label className={'booking-mode ' + (mode === 'sede' ? 'chosen' : '')}>
              <input type="radio" name="booking-mode" checked={mode === 'sede'} onChange={() => selectMode('sede')} />
              <span className="booking-option-icon"><MapPin size={24} aria-hidden="true" /></span>
              <span className="booking-option-copy"><strong>Primo Incontro in Sede con Direttore + Prima Seduta</strong>
                <small>Colloquio gratuito di 20 minuti presso il Centro Change, Bergamo.</small></span>
              <span className="booking-option-check"><Check size={17} aria-hidden="true" /></span>
            </label>
            <label className={'booking-mode ' + (mode === 'online' ? 'chosen' : '')}>
              <input type="radio" name="booking-mode" checked={mode === 'online'} onChange={() => selectMode('online')} />
              <span className="booking-option-icon"><MonitorPlay size={24} aria-hidden="true" /></span>
              <span className="booking-option-copy"><strong>Primo Incontro Online con Direttore + Prima Seduta</strong>
                <small>Colloquio conoscitivo gratuito di 20 minuti a distanza.</small></span>
              <span className="booking-option-check"><Check size={17} aria-hidden="true" /></span>
            </label>
          </div>
          <p className="booking-info"><Clock3 size={18} aria-hidden="true" /> La seduta completa successiva sarà fissata dalla segreteria dopo il colloquio.</p>
          <button type="button" className="booking-primary" disabled={!mode} onClick={next}>Continua <ArrowRight size={18} aria-hidden="true" /></button>
        </section>}
        {step === 1 && <section className="booking-stage">
          <p className="booking-eyebrow">SCEGLI CHI INCONTRARE</p>
          <h1>Con quale Direttore vuoi parlare?</h1>
          <p className="booking-intro">Seleziona Marco oppure Francesca: gli orari disponibili dipendono dal Direttore scelto.</p>
          <div className="booking-director-list" role="radiogroup" aria-label="Direttore">
            {(['Marco', 'Francesca'] as Director[]).map(name => <label key={name} className={'booking-director ' + (route === name ? 'chosen' : '')}>
              <input type="radio" name="booking-director" checked={route === name} onChange={() => selectDirector(name)} />
              <span className="booking-avatar"><UserRound size={23} aria-hidden="true" /></span>
              <span><strong>{name}</strong><small>Direttore · Centro Change</small></span>
              <span className="booking-option-check"><Check size={17} aria-hidden="true" /></span>
            </label>)}
          </div>
          <div className="booking-actions"><button type="button" className="booking-secondary" onClick={back}><ArrowLeft size={17} aria-hidden="true" /> Indietro</button>
            <button type="button" className="booking-primary" disabled={!route} onClick={next}>Continua <ArrowRight size={18} aria-hidden="true" /></button></div>
        </section>}
        {step === 2 && <section className="booking-stage">
          <p className="booking-eyebrow">SCEGLI QUANDO</p>
          <h1>Scegli giorno e orario</h1>
          <p className="booking-intro">Disponibilità reale di {route} per il colloquio {mode === 'sede' ? 'in sede' : 'online'} di 20 minuti.</p>
          <form className="booking-calendar-form" onSubmit={event => { event.preventDefault(); void search() }}>
            <Field label="Mostra disponibilità a partire dal" required>
              <DateInput required value={start} onChange={value => { setStart(value); invalidate() }} />
            </Field>
            <button className="booking-search" type="submit" disabled={busy}><CalendarDays size={18} aria-hidden="true" /> {busy ? 'Ricerca in corso…' : 'Cerca disponibilità'}</button>
          </form>
          {busy && <p className="booking-status" role="status">Stiamo cercando gli orari disponibili…</p>}
          {projection && <div className="booking-availability">
            <h2>Orari disponibili</h2>
            {projection.slots.length ? <div className="booking-slot-grid" role="radiogroup" aria-label="Orari disponibili">
              {projection.slots.map(slot => {
                const value = slot.date + ' ' + slot.time
                return <label key={value} className={'booking-slot ' + (selected === value ? 'chosen' : '')}>
                  <input type="radio" name="booking-slot" checked={selected === value} onChange={() => setSelected(value)} />
                  <span>{displayDate(slot.date)}</span><strong>{time(slot.time)}</strong>
                </label>
              })}
            </div> : <p className="booking-status">Nessun orario disponibile. Prova un altro periodo o un altro Direttore.</p>}
          </div>}
          {error && <FormError error={error} />}
          <div className="booking-actions"><button type="button" className="booking-secondary" onClick={back}><ArrowLeft size={17} aria-hidden="true" /> Indietro</button>
            <button type="button" className="booking-primary" disabled={!chosenSlot || busy} onClick={next}>Continua <ArrowRight size={18} aria-hidden="true" /></button></div>
        </section>}
        {step === 3 && <section className="booking-stage">
          <p className="booking-eyebrow">QUASI FATTO</p>
          <h1>Completa la prenotazione</h1>
          <p className="booking-intro">Confermi solo il colloquio conoscitivo gratuito di 20 minuti. La seduta completa sarà concordata successivamente dalla segreteria.</p>
          <form className="booking-details" onSubmit={event => { event.preventDefault(); void submit() }}>
            <div className="booking-form-row"><Field label="Nome" required><input required autoComplete="given-name" maxLength={80} value={firstName} onChange={event => setFirstName(event.target.value)} /></Field>
              <Field label="Cognome" required><input required autoComplete="family-name" maxLength={80} value={lastName} onChange={event => setLastName(event.target.value)} /></Field></div>
            <Field label="Email" required><input required type="email" autoComplete="email" maxLength={140} value={email} onChange={event => setEmail(event.target.value)} /></Field>
            <Field label="Sesso anagrafico" required><select required value={sex} onChange={event => setSex(event.target.value)}>
              <option value="">Seleziona</option><option value="Female">Femmina</option><option value="Male">Maschio</option><option value="Other">Altro</option>
            </select></Field>
            <p className="booking-info"><ShieldCheck size={18} aria-hidden="true" /> I dati saranno utilizzati per gestire la richiesta di prenotazione secondo l'informativa del centro.</p>
            {error && <FormError error={error} />}
            <div className="booking-actions"><button type="button" className="booking-secondary" disabled={busy} onClick={back}><ArrowLeft size={17} aria-hidden="true" /> Indietro</button>
              <button className="booking-primary" type="submit" disabled={busy}>{busy ? 'Prenotazione in corso…' : 'Conferma primo incontro'} <ArrowRight size={17} aria-hidden="true" /></button></div>
          </form>
        </section>}
        {step === 4 && confirmed && <section className="booking-stage booking-success" role="status">
          <span className="booking-success-icon"><Check size={32} aria-hidden="true" /></span>
          <h1>Prenotazione registrata</h1>
          <p>Il tuo colloquio conoscitivo gratuito di 20 minuti {mode === 'sede' ? 'in sede' : 'online'} con {route} è prenotato per il <strong>{chosenSlot ? displayDate(chosenSlot.date) : ''}</strong> alle <strong>{chosenSlot ? time(chosenSlot.time) : ''}</strong>.</p>
          <p>La segreteria organizzerà successivamente la prima seduta completa. Non è stata prenotata una seconda seduta.</p>
          <p className="booking-success-note"><Mail size={18} aria-hidden="true" /> Le conferme via email sono abilitate solo quando il centro avrà completato la configurazione del servizio.</p>
        </section>}
      </div>
      <aside className="booking-summary" aria-label="Riepilogo della prenotazione">{summary}</aside>
    </div>
    <footer className="booking-footer">Centro Change · Via Molino Baertsch 4, Bergamo</footer>
  </main>
}
