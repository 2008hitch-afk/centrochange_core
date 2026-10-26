import React, { useEffect, useState } from 'react'
import { ArrowDownRight, ArrowUpRight, CalendarDays, ChevronLeft, ChevronRight, X } from 'lucide-react'
import { displayDate, money, romeToday, type Row } from './api'
import { demoText } from './demo_labels'

export type Feedback = (message: string, fail?: boolean) => void
export function Heading({ eyebrow, title, subtitle, action }: { eyebrow?: string; title: string; subtitle?: string; action?: React.ReactNode }) {
  return <div className="page-heading"><div><div className="eyebrow">{eyebrow ?? 'CENTRO CHANGE'}</div><h1>{title}</h1>{subtitle && <p>{subtitle}</p>}</div>{action && <div className="heading-action">{action}</div>}</div>
}
export function Button({ children, variant = 'primary', ...rest }: React.ButtonHTMLAttributes<HTMLButtonElement> & { variant?: 'primary' | 'secondary' | 'ghost' | 'danger' }) { return <button {...rest} className={`button ${variant} ${rest.className ?? ''}`}>{children}</button> }
export function Chip({ children, tone = 'neutral' }: { children: React.ReactNode; tone?: 'neutral' | 'good' | 'warn' | 'bad' | 'blue' }) { return <span className={`chip ${tone}`}><span className="chip-dot" />{children}</span> }
export function Empty({ title, detail }: { title: string; detail?: string }) { return <div className="empty-state"><div className="empty-mark">✦</div><strong>{title}</strong>{detail && <p>{detail}</p>}</div> }
function useDialogFocus(onClose: () => void) {
  const ref = React.useRef<HTMLElement>(null)
  const closeRef = React.useRef(onClose)
  closeRef.current = onClose
  useEffect(() => {
    const previous = document.activeElement instanceof HTMLElement ? document.activeElement : null
    const items = () => Array.from(ref.current?.querySelectorAll<HTMLElement>('button:not(:disabled), input:not(:disabled), select:not(:disabled), textarea:not(:disabled), a[href], [tabindex]:not([tabindex="-1"])') ?? []).filter(el => el.getClientRects().length > 0)
    items()[0]?.focus()
    const keydown = (e: KeyboardEvent) => {
      const dialogs = Array.from(document.querySelectorAll<HTMLElement>('[role="dialog"]'))
      if (dialogs.at(-1) !== ref.current) return
      if (e.key === 'Escape') { e.preventDefault(); closeRef.current(); return }
      if (e.key !== 'Tab') return
      const focusable = items(); if (!focusable.length) { e.preventDefault(); return }
      const first = focusable[0], last = focusable[focusable.length - 1]
      if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus() }
      else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus() }
    }
    addEventListener('keydown', keydown)
    return () => { removeEventListener('keydown', keydown); previous?.focus() }
  }, [])
  return ref
}
export function Modal({ title, children, onClose, footer }: { title: string; children: React.ReactNode; onClose: () => void; footer?: React.ReactNode }) {
  const ref = useDialogFocus(onClose)
  return <div className="modal-backdrop" onMouseDown={e => { if (e.target === e.currentTarget) onClose() }}><section ref={ref} className="modal" role="dialog" aria-modal="true" aria-label={title}><header className="modal-head"><div><span className="eyebrow">CENTRO CHANGE</span><h2>{title}</h2></div><button className="icon-button" onClick={onClose} aria-label="Chiudi"><X /></button></header><div className="modal-body">{children}</div>{footer && <footer className="modal-foot">{footer}</footer>}</section></div>
}
export function Drawer({ title, children, onClose }: { title: string; children: React.ReactNode; onClose: () => void }) {
  const ref = useDialogFocus(onClose)
  return <div className="drawer-backdrop" onMouseDown={e => { if (e.target === e.currentTarget) onClose() }}><aside ref={ref} className="drawer" role="dialog" aria-modal="true" aria-label={title}><header className="drawer-head"><div><span className="eyebrow">DETTAGLIO</span><h2>{title}</h2></div><button className="icon-button" aria-label="Chiudi" onClick={onClose}><X /></button></header><div className="drawer-body">{children}</div></aside></div>
}
export function Field({ label, name, required, children }: { label: string; name?: string; required?: boolean; children: React.ReactNode }) { return <label className="field"><span>{label}{required && <b className="required"> *</b>}</span>{children}</label> }
export function SearchableSelect({ label, options, value, onChange, required = false, empty = 'Seleziona', disabled = false }: { label: string; options: { value: string; label: string }[]; value: string; onChange: (value: string) => void; required?: boolean; empty?: string; disabled?: boolean }) {
  const id = React.useId()
  const root = React.useRef<HTMLDivElement>(null)
  const input = React.useRef<HTMLInputElement>(null)
  const [open, setOpen] = useState(false)
  const [query, setQuery] = useState('')
  const [active, setActive] = useState(-1)
  const [invalidQuery, setInvalidQuery] = useState(false)
  const selected = options.find(option => option.value === value)
  const search = query.trim().toLocaleLowerCase('it-IT')
  const visible = search ? options.filter(option => option.label.toLocaleLowerCase('it-IT').includes(search)) : options
  const choose = (next: string) => { onChange(next); input.current?.setCustomValidity(''); setInvalidQuery(false); setQuery(''); setOpen(false) }
  const move = (delta: number) => {
    setOpen(true)
    setActive(current => Math.max(0, Math.min(visible.length - 1, current + delta)))
  }
  return <div className="field searchable-select" ref={root}>
    <label htmlFor={id}>{label}{required && <b className="required"> *</b>}</label>
    <div className="combobox-shell">
      <input ref={input} id={id} role="combobox" type="text" aria-autocomplete="list" aria-expanded={open} aria-controls={open ? `${id}-list` : undefined} aria-activedescendant={open && visible[active] ? `${id}-option-${active}` : undefined} aria-invalid={invalidQuery} autoComplete="off" placeholder={empty} disabled={disabled} required={required} value={query || selected?.label || ''}
        onFocus={event => { setOpen(true); setQuery(''); setActive(options.findIndex(option => option.value === value)); event.currentTarget.select() }}
        onClick={() => { if (!open) { setQuery(''); setActive(options.findIndex(option => option.value === value)); setOpen(true) } }}
        onChange={event => { event.currentTarget.setCustomValidity(event.target.value.trim() ? 'Seleziona una voce dall’elenco.' : ''); setInvalidQuery(false); setQuery(event.target.value); setActive(-1); setOpen(true); onChange('') }}
        onBlur={event => { if (!root.current?.contains(event.relatedTarget as Node)) { if (query.trim() && !value) { setInvalidQuery(true); setQuery('') } setOpen(false) } }}
        onKeyDown={event => {
          if (event.key === 'ArrowDown') { event.preventDefault(); move(1) }
          else if (event.key === 'ArrowUp') { event.preventDefault(); move(-1) }
          else if (event.key === 'Enter' && open && visible[active]) { event.preventDefault(); choose(visible[active].value) }
          else if (event.key === 'Escape' && open) { event.preventDefault(); event.stopPropagation(); setOpen(false); setQuery(''); setInvalidQuery(false); event.currentTarget.setCustomValidity('') }
        }} />
      {(value || invalidQuery) && !disabled && <button type="button" className="combobox-clear" aria-label={`Cancella ${label.toLocaleLowerCase('it-IT')}`} onMouseDown={event => event.preventDefault()} onClick={() => { choose(''); input.current?.focus() }}>×</button>}
    </div>
    {open && !disabled && <div id={`${id}-list`} role="listbox" aria-label={`Opzioni ${label.toLocaleLowerCase('it-IT')}`} className="combobox-options">
      {visible.length ? visible.map((option, index) => <button type="button" role="option" id={`${id}-option-${index}`} data-value={option.value} aria-selected={option.value === value} className={index === active ? 'active' : ''} key={option.value} onMouseDown={event => event.preventDefault()} onClick={() => choose(option.value)}>{option.label}</button>) : <p>Nessun risultato. Modifica la ricerca.</p>}
    </div>}
    {invalidQuery && <small className="combobox-error" role="alert">Nessuna voce selezionata. Scegli dall’elenco o cancella il campo.</small>}
  </div>
}

const itMonths = ['Gennaio', 'Febbraio', 'Marzo', 'Aprile', 'Maggio', 'Giugno', 'Luglio', 'Agosto', 'Settembre', 'Ottobre', 'Novembre', 'Dicembre']
const itWeekdays = ['Lu', 'Ma', 'Me', 'Gi', 'Ve', 'Sa', 'Do']

/** Date-only conversion uses UTC to avoid client timezone and DST changes. */
export function parseItalianDate(text: string): string | null {
  const match = /^(\d{2})\/(\d{2})\/(\d{4})$/.exec(text.trim())
  if (!match) return null
  const [, day, month, year] = match
  const y = Number(year), m = Number(month), d = Number(day)
  if (y < 1000 || y > 9999 || m < 1 || m > 12 || d < 1 || d > 31) return null
  const date = new Date(Date.UTC(y, m - 1, d))
  if (date.getUTCFullYear() !== y || date.getUTCMonth() !== m - 1 || date.getUTCDate() !== d) return null
  return year + '-' + month + '-' + day
}

export function Time24Input({ value, onChange, required = true }: { value: string; onChange: (time: string) => void; required?: boolean }) {
  return <input type="text" inputMode="numeric" autoComplete="off" placeholder="HH:mm" title="Inserisci l'ora in formato 24 ore (HH:mm)"
    pattern="(?:[01][0-9]|2[0-3]):[0-5][0-9]" maxLength={5} value={value} required={required}
    onChange={event => onChange(event.target.value)} />
}

export function DateInput({ value, onChange, required = false, onValidityChange, calendarLabel, resetKey }: {
  value: string
  onChange: (iso: string) => void
  required?: boolean
  onValidityChange?: (valid: boolean) => void
  calendarLabel?: string
  resetKey?: string
}) {
  const [draft, setDraft] = useState(displayDate(value))
  const [open, setOpen] = useState(false)
  const [cursor, setCursor] = useState((value || romeToday()).slice(0, 7))
  const root = React.useRef<HTMLDivElement>(null)
  const trigger = React.useRef<HTMLButtonElement>(null)
  const inputRef = React.useRef<HTMLInputElement>(null)
  const popover = React.useRef<HTMLDivElement>(null)
  useEffect(() => { setDraft(displayDate(value)); inputRef.current?.setCustomValidity(''); onValidityChange?.(!!value || !required) }, [value, resetKey])
  useEffect(() => {
    if (!open) return
    const outside = (event: PointerEvent) => {
      if (root.current && !root.current.contains(event.target as Node)) setOpen(false)
    }
    document.addEventListener('pointerdown', outside)
    return () => document.removeEventListener('pointerdown', outside)
  }, [open])
  const commit = (text: string) => {
    const iso = parseItalianDate(text)
    if (iso) { onChange(iso); onValidityChange?.(true); return true }
    if (!required && !text.trim()) { onChange(''); onValidityChange?.(true); return true }
    onValidityChange?.(false)
    return false
  }
  const choose = (iso: string) => {
    inputRef.current?.setCustomValidity(''); setDraft(displayDate(iso)); onChange(iso); onValidityChange?.(true); setOpen(false)
    trigger.current?.focus()
  }
  const [year, month] = cursor.split('-').map(Number)
  const firstWeekday = (new Date(Date.UTC(year, month - 1, 1)).getUTCDay() + 6) % 7
  const daysInMonth = new Date(Date.UTC(year, month, 0)).getUTCDate()
  const moveMonth = (delta: number) => {
    const date = new Date(Date.UTC(year, month - 1 + delta, 1))
    setCursor(date.getUTCFullYear() + '-' + String(date.getUTCMonth() + 1).padStart(2, '0'))
  }
  return <div className="cc-date-control" ref={root} onKeyDown={event => {
    if (open && event.key === 'Escape') { event.preventDefault(); event.stopPropagation(); setOpen(false); trigger.current?.focus() }
  }}>
    <input ref={inputRef} className="date-input" type="text" inputMode="numeric" autoComplete="off" placeholder="GG/MM/AAAA"
      pattern="[0-9]{2}/[0-9]{2}/[0-9]{4}" title="Usa una data valida nel formato GG/MM/AAAA"
      aria-label={calendarLabel ? calendarLabel + ' (GG/MM/AAAA)' : undefined}
      value={draft} required={required}
      onChange={event => {
        const text = event.target.value
        setDraft(text)
        event.currentTarget.setCustomValidity(commit(text) ? '' : 'Inserisci una data valida nel formato GG/MM/AAAA')
      }}
      onBlur={event => { event.currentTarget.setCustomValidity(commit(event.target.value) ? '' : 'Inserisci una data valida nel formato GG/MM/AAAA') }} />
    <button ref={trigger} type="button" className="cc-date-trigger" aria-label={calendarLabel ? 'Apri calendario ' + calendarLabel : 'Apri calendario'}
      aria-expanded={open} onClick={() => {
        if (open) { setOpen(false); return }
        setCursor((parseItalianDate(draft) || value || romeToday()).slice(0, 7))
        setOpen(true)
        window.setTimeout(() => popover.current?.querySelector<HTMLSelectElement>('select')?.focus(), 0)
      }}><CalendarDays size={17} aria-hidden="true" /></button>
    {open && <div ref={popover} className="cc-date-popover" role="dialog" aria-label={calendarLabel ? 'Calendario ' + calendarLabel : 'Calendario'}>
      <div className="cc-date-navigation">
        <button type="button" aria-label="Mese precedente" onClick={() => moveMonth(-1)}><ChevronLeft size={17} /></button>
        <select aria-label="Mese" value={month} onChange={event => setCursor(year + '-' + String(event.target.value).padStart(2, '0'))}>
          {itMonths.map((label, index) => <option key={label} value={index + 1}>{label}</option>)}
        </select>
        <select aria-label="Anno" value={year} onChange={event => setCursor(event.target.value + '-' + String(month).padStart(2, '0'))}>
          {Array.from({ length: 201 }, (_, i) => i + 1900).map(y => <option key={y} value={y}>{y}</option>)}
        </select>
        <button type="button" aria-label="Mese successivo" onClick={() => moveMonth(1)}><ChevronRight size={17} /></button>
      </div>
      <div className="cc-date-grid">
        {itWeekdays.map(day => <span key={day} className="cc-date-weekday">{day}</span>)}
        {Array.from({ length: firstWeekday }, (_, index) => <span key={'empty-' + index} aria-hidden="true" />)}
        {Array.from({ length: daysInMonth }, (_, index) => {
          const day = index + 1
          const iso = year + '-' + String(month).padStart(2, '0') + '-' + String(day).padStart(2, '0')
          return <button type="button" key={iso} aria-label={displayDate(iso)} aria-pressed={value === iso}
            className={value === iso ? 'selected' : ''} onClick={() => choose(iso)}>{day}</button>
        })}
      </div>
      <div className="cc-date-foot"><button type="button" onClick={() => choose(romeToday())}>Oggi</button><button type="button" onClick={() => { setOpen(false); trigger.current?.focus() }}>Annulla</button></div>
    </div>}
  </div>
}

export function FormError({ error }: { error: string }) { return error ? <p className="form-error" role="alert">{error}</p> : null }
export function useAction(feedback: Feedback, onSuccess?: () => void) {
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const run = async (action: () => Promise<unknown>, success = 'Operazione registrata.') => {
    setBusy(true); setError('')
    try { await action(); feedback(success); onSuccess?.(); return true }
    catch (e) { const message = e instanceof Error ? e.message : 'Operazione non riuscita.'; setError(message); feedback(message, true); return false }
    finally { setBusy(false) }
  }
  return { busy, error, run }
}
export function Metric({ label, value, trend, tone = 'blue', onClick, active, className = '' }: { label: string; value: React.ReactNode; trend?: string; tone?: 'blue' | 'green' | 'amber' | 'purple'; onClick?: () => void; active?: boolean; className?: string }) {
  const isClickable = !!onClick
  return <article className={`metric-card ${tone} ${isClickable ? 'clickable' : ''} ${active ? 'active' : ''} ${className}`.trim()} onClick={onClick} onKeyDown={e => { if (onClick && (e.key === 'Enter' || e.key === ' ')) { e.preventDefault(); onClick() } }} tabIndex={isClickable ? 0 : undefined} role={isClickable ? 'button' : undefined} aria-pressed={isClickable ? active : undefined}><div className="metric-top"><span>{label}</span>{trend && <span className="metric-trend">{trend.startsWith('+') ? <ArrowUpRight /> : <ArrowDownRight />}{trend}</span>}</div><strong>{value}</strong><div className="metric-rule" /></article>
}
export function DataTable({ rows, columns, onRow }: { rows: Row[]; columns: { key: string; label: string; render?: (value: unknown, row: Row) => React.ReactNode }[]; onRow?: (row: Row) => void }) {
  if (!rows.length) return <Empty title="Nessun elemento" detail="Modifica i filtri o scegli un altro periodo." />
  return <div className="table-scroll"><table><thead><tr>{columns.map((c, i) => <th key={`${c.key}-${i}`} scope="col">{c.label}</th>)}</tr></thead><tbody>{rows.map((row, i) => <tr key={String(row.name ?? i)} className={onRow ? 'clickable' : ''} onClick={() => onRow?.(row)} onKeyDown={e => { if (onRow && (e.key === 'Enter' || e.key === ' ')) { e.preventDefault(); onRow(row) } }} tabIndex={onRow ? 0 : undefined}>{columns.map((c, j) => <td key={`${c.key}-${j}`}>{c.render ? c.render(row[c.key], row) : demoText(row[c.key] ?? '—')}</td>)}</tr>)}</tbody></table></div>
}
export const dateColumn = (key: string, label: string) => ({ key, label, render: (v: unknown) => displayDate(v) })
export const moneyColumn = (key: string, label: string) => ({ key, label, render: (v: unknown) => money(v) })
