import React, { useEffect, useMemo, useState } from 'react'
import { Check, CalendarDays, Clock, User, AlertCircle, ChevronRight, AlertTriangle } from 'lucide-react'
import { type Boot, type Row, call, displayDate, romeToday, time } from './api'
import { type Feedback, Button, Chip, DateInput, Empty, Field, FormError, Modal } from './ui'
import { demoPatient, demoText } from './demo_labels'
import { paymentMethodLabel } from './views'
import { economyName } from './display_names'

interface DayClosureSession {
  name: string
  appointment_date: string
  appointment_time: string
  duration: number
  patient: string
  patient_name?: string
  patient_first_name?: string
  patient_last_name?: string
  practitioner: string
  practitioner_name?: string
  cc_service_label?: string
  status: string
  cc_closure_state: string
  cc_economic_state: string
  cc_performed: number
  cc_paid: number
  mode_of_payment?: string | null
}

interface DayClosureResponse {
  date: string
  is_today: boolean
  is_past: boolean
  sessions: DayClosureSession[]
  arrear_dates: string[]
  practitioner?: string
}

interface ItemFormState {
  performed?: boolean
  paid: boolean
  mode_of_payment: string
  note: string
}

export function DayClosureModal({
  boot,
  center,
  onClose,
  onSuccess,
  feedback,
  initialDate
}: {
  boot: Boot
  center: string
  onClose: () => void
  onSuccess: () => void
  feedback: Feedback
  initialDate?: string
}) {
  const [selectedDate, setSelectedDate] = useState<string>(() => initialDate || romeToday())
  const [data, setData] = useState<DayClosureResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [formStates, setFormStates] = useState<Record<string, ItemFormState>>({})

  // Load sessions for selectedDate
  useEffect(() => {
    let live = true
    setLoading(true)
    setError('')
    call<DayClosureResponse>('operations.lifecycle.get_day_closure_sessions', {
      center,
      date: selectedDate
    })
      .then(res => {
        if (!live) return
        setData(res)
        // Initialize form states for actionable sessions
        const initialStates: Record<string, ItemFormState> = {}
        for (const s of res.sessions) {
          if (s.cc_closure_state === 'Closed' || s.status === 'Cancelled') {
            continue
          }
          initialStates[s.name] = {
            performed: undefined,
            paid: false,
            mode_of_payment: '',
            note: ''
          }
        }
        setFormStates(initialStates)
        setLoading(false)
      })
      .catch(e => {
        if (!live) return
        const msg = e instanceof Error ? e.message : 'Impossibile caricare le sedute del giorno.'
        setError(msg)
        setLoading(false)
      })
    return () => { live = false }
  }, [center, selectedDate])

  const sessions = data?.sessions || []
  const arrearDates = data?.arrear_dates || []

  const updateItem = (appName: string, patch: Partial<ItemFormState>) => {
    setFormStates(prev => ({
      ...prev,
      [appName]: {
        ...(prev[appName] || { paid: false, mode_of_payment: '', note: '' }),
        ...patch
      }
    }))
  }

  // Actionable sessions (not closed, not cancelled)
  const actionableSessions = useMemo(() => {
    return sessions.filter(s => s.cc_closure_state !== 'Closed' && s.status !== 'Cancelled')
  }, [sessions])

  // Count metrics
  const totalCount = sessions.length
  const performedCount = actionableSessions.filter(s => formStates[s.name]?.performed === true).length +
    sessions.filter(s => s.cc_closure_state === 'Closed' && s.cc_performed).length
  const notPerformedCount = actionableSessions.filter(s => formStates[s.name]?.performed === false).length +
    sessions.filter(s => s.cc_closure_state === 'Closed' && !s.cc_performed).length
  const paidCount = actionableSessions.filter(s => formStates[s.name]?.performed === true && formStates[s.name]?.paid).length +
    sessions.filter(s => s.cc_closure_state === 'Closed' && s.cc_paid).length
  const unpaidCount = actionableSessions.filter(s => formStates[s.name]?.performed === true && !formStates[s.name]?.paid).length +
    sessions.filter(s => s.cc_closure_state === 'Closed' && s.cc_performed && !s.cc_paid).length

  // Validation: are all actionable sessions assigned performed status?
  const isComplete = useMemo(() => {
    if (actionableSessions.length === 0) return false
    for (const s of actionableSessions) {
      const state = formStates[s.name]
      if (!state || state.performed === undefined) return false
      if (state.performed && state.paid && !state.mode_of_payment) return false
    }
    return true
  }, [actionableSessions, formStates])

  const handleSubmit = async () => {
    if (!isComplete || busy) return
    setBusy(true)
    setError('')

    const payload = actionableSessions.map(s => {
      const state = formStates[s.name]
      return {
        appointment: s.name,
        performed: state.performed ? 1 : 0,
        paid: (state.performed && state.paid) ? 1 : 0,
        mode_of_payment: (state.performed && state.paid) ? state.mode_of_payment : null,
        note: state.note || (state.performed ? 'Seduta svolta' : 'Seduta non svolta')
      }
    })

    const isArrear = selectedDate < romeToday()
    const reasonText = isArrear ? 'Completamento autonomo sedute arretrate' : 'Chiusura della mia giornata'

    try {
      const res = await call<{ status?: string; day_closed?: boolean; remaining_pending?: number }>('operations.lifecycle.close_day', {
        center,
        date: selectedDate,
        sessions: JSON.stringify(payload),
        reason: reasonText,
        allow_partial: 0
      }, true)
      if (res && res.day_closed === false && (res.remaining_pending ?? 0) > 0) {
        feedback(`Chiusura parziale registrata: restano ${res.remaining_pending} sedute da completare.`)
      } else {
        feedback(`Chiusura giornata completata per il ${displayDate(selectedDate)}.`)
      }
      onSuccess()
    } catch (cause) {
      const msg = cause instanceof Error ? cause.message : 'Errore durante la chiusura della giornata.'
      setError(msg)
    } finally {
      setBusy(false)
    }
  }

  return (
    <Modal title="Chiudi la mia giornata" onClose={onClose}>
      <div className="day-closure-container">
        {/* Date Selector and Arrear Alert */}
        <div className="day-closure-toolbar">
          <div className="toolbar-left">
            <Field label="Data da chiudere">
              <DateInput value={selectedDate} onChange={setSelectedDate} required />
            </Field>
            {selectedDate !== romeToday() && (
              <Button variant="secondary" onClick={() => setSelectedDate(romeToday())}>
                Torna a oggi
              </Button>
            )}
          </div>
        </div>

        {arrearDates.length > 0 && (
          <div className="arrear-banner" role="status">
            <div className="arrear-banner-title">
              <AlertTriangle size={16} />
              <strong>Sedute arretrate da completare:</strong>
            </div>
            <div className="arrear-badges">
              {arrearDates.map(d => (
                <button
                  key={d}
                  type="button"
                  className={`arrear-badge ${d === selectedDate ? 'active' : ''}`}
                  onClick={() => setSelectedDate(d)}
                >
                  {displayDate(d)}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Sessions list */}
        {loading ? (
          <p className="panel-loading" role="status">Caricamento sedute in corso…</p>
        ) : error && !sessions.length ? (
          <FormError error={error} />
        ) : !sessions.length ? (
          <Empty
            title="Nessuna seduta programmata per questa data"
            detail="Non ci sono sedute da chiudere per il giorno selezionato."
          />
        ) : (
          <>
            <div className="day-closure-summary-grid">
              <div className="summary-card">
                <span>Totale sedute</span>
                <strong>{totalCount}</strong>
              </div>
              <div className="summary-card text-good">
                <span>Svolte</span>
                <strong>{performedCount}</strong>
              </div>
              <div className="summary-card text-neutral">
                <span>Non svolte</span>
                <strong>{notPerformedCount}</strong>
              </div>
              <div className="summary-card text-good">
                <span>Pagate</span>
                <strong>{paidCount}</strong>
              </div>
              <div className="summary-card text-warn">
                <span>Da incassare</span>
                <strong>{unpaidCount}</strong>
              </div>
            </div>

            <div className="day-closure-list">
              {sessions.map(s => {
                const isClosed = s.cc_closure_state === 'Closed'
                const isCancelled = s.status === 'Cancelled'
                const isAutoLocked = s.cc_closure_state === 'Auto Locked'
                const state = formStates[s.name] || { paid: false, mode_of_payment: '', note: '' }

                return (
                  <div key={s.name} className={`day-closure-card ${isClosed ? 'is-closed' : ''}`}>
                    <div className="day-closure-card-header">
                      <div className="card-patient">
                        <span className="patient-name">
                          <User size={14} /> {demoPatient(s.patient, s.patient_name, s.patient_first_name, s.patient_last_name)}
                        </span>
                        <span className="session-service">{demoText(s.cc_service_label) || 'Seduta'}</span>
                      </div>
                      <div className="card-meta">
                        <span className="session-time">
                          <Clock size={13} /> {time(s.appointment_time)} ({s.duration} min)
                        </span>
                        {isClosed ? (
                          <Chip tone="good">Già chiusa ({s.cc_performed ? 'Svolta' : 'Non svolta'})</Chip>
                        ) : isCancelled ? (
                          <Chip tone="neutral">Annullata</Chip>
                        ) : isAutoLocked ? (
                          <Chip tone="bad">Da completare in ritardo</Chip>
                        ) : (
                          <Chip tone="warn">Da chiudere</Chip>
                        )}
                      </div>
                    </div>

                    {!isClosed && !isCancelled && (
                      <div className="day-closure-card-body">
                        <div className="control-row">
                          <span className="control-label">Prestazione:</span>
                          <div className="segmented-toggle" role="group" aria-label={`Esito prestazione ${s.name}`}>
                            <button
                              type="button"
                              className={`segmented-btn ${state.performed === true ? 'selected-yes' : ''}`}
                              onClick={() => updateItem(s.name, { performed: true })}
                            >
                              Svolta
                            </button>
                            <button
                              type="button"
                              className={`segmented-btn ${state.performed === false ? 'selected-no' : ''}`}
                              onClick={() => updateItem(s.name, { performed: false, paid: false, mode_of_payment: '' })}
                            >
                              Non svolta
                            </button>
                          </div>
                        </div>

                        {state.performed === true && (
                          <div className="payment-subcontrols">
                            <label className="checkbox-row">
                              <input
                                type="checkbox"
                                checked={state.paid}
                                onChange={e => updateItem(s.name, {
                                  paid: e.target.checked,
                                  mode_of_payment: e.target.checked ? state.mode_of_payment : ''
                                })}
                              />
                              <span>Pagata al momento della seduta</span>
                            </label>

                            {state.paid && (
                              <Field label="Metodo di pagamento" required>
                                <select
                                  value={state.mode_of_payment}
                                  onChange={e => updateItem(s.name, { mode_of_payment: e.target.value })}
                                  required
                                >
                                  <option value="">Seleziona metodo</option>
                                  {boot.payment_methods.map(p => (
                                    <option key={p} value={p}>
                                      {paymentMethodLabel(p)}
                                    </option>
                                  ))}
                                </select>
                              </Field>
                            )}
                          </div>
                        )}

                        {state.performed === false && (
                          <div className="not-performed-subcontrols">
                            <Field label="Motivo (opzionale)">
                              <input
                                type="text"
                                placeholder="Es. Paziente assente o non presentatosi"
                                value={state.note}
                                onChange={e => updateItem(s.name, { note: e.target.value })}
                              />
                            </Field>
                            <div className="day-closure-economic-note">
                              <p className="economic-note-text">
                                La seduta verrà registrata come non svolta. Eventuali importi già dovuti o penali restano invariati.
                              </p>
                              {s.cc_economic_state && (
                                <p className="economic-note-status">
                                  Situazione economica registrata: <strong>{economyName(s.cc_economic_state)}</strong>.
                                </p>
                              )}
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                )
              })}
            </div>

            <FormError error={error} />

            <div className="form-actions">
              <Button type="button" variant="secondary" onClick={onClose}>
                Annulla
              </Button>
              {actionableSessions.length > 0 && (
                <Button
                  disabled={busy || !isComplete}
                  onClick={() => void handleSubmit()}
                >
                  {busy ? 'Salvataggio in corso…' : 'Conferma chiusura giornata'}
                </Button>
              )}
            </div>
          </>
        )}
      </div>
    </Modal>
  )
}
