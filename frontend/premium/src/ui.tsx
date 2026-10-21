import React, { useEffect, useState } from 'react'
import { ArrowDownRight, ArrowUpRight, X } from 'lucide-react'
import { displayDate, money, type Row } from './api'

export type Feedback = (message: string, fail?: boolean) => void
export function Heading({ eyebrow, title, subtitle, action }: { eyebrow?: string; title: string; subtitle?: string; action?: React.ReactNode }) {
  return <div className="page-heading"><div><div className="eyebrow">{eyebrow ?? 'CENTRO CHANGE'}</div><h1>{title}</h1>{subtitle && <p>{subtitle}</p>}</div>{action && <div className="heading-action">{action}</div>}</div>
}
export function Button({ children, variant = 'primary', ...rest }: React.ButtonHTMLAttributes<HTMLButtonElement> & { variant?: 'primary' | 'secondary' | 'ghost' | 'danger' }) { return <button {...rest} className={`button ${variant} ${rest.className ?? ''}`}>{children}</button> }
export function Chip({ children, tone = 'neutral' }: { children: React.ReactNode; tone?: 'neutral' | 'good' | 'warn' | 'bad' | 'blue' }) { return <span className={`chip ${tone}`}><span className="chip-dot" />{children}</span> }
export function Empty({ title, detail }: { title: string; detail?: string }) { return <div className="empty-state"><div className="empty-mark">✦</div><strong>{title}</strong>{detail && <p>{detail}</p>}</div> }
export function Modal({ title, children, onClose, footer }: { title: string; children: React.ReactNode; onClose: () => void; footer?: React.ReactNode }) {
  useEffect(() => { const fn = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose() }; addEventListener('keydown', fn); return () => removeEventListener('keydown', fn) }, [onClose])
  return <div className="modal-backdrop" onMouseDown={e => { if (e.target === e.currentTarget) onClose() }}><section className="modal" role="dialog" aria-modal="true" aria-label={title}><header className="modal-head"><div><span className="eyebrow">CENTRO CHANGE</span><h2>{title}</h2></div><button className="icon-button" onClick={onClose} aria-label="Chiudi"><X /></button></header><div className="modal-body">{children}</div>{footer && <footer className="modal-foot">{footer}</footer>}</section></div>
}
export function Drawer({ title, children, onClose }: { title: string; children: React.ReactNode; onClose: () => void }) {
  useEffect(() => { const fn = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose() }; addEventListener('keydown', fn); return () => removeEventListener('keydown', fn) }, [onClose])
  return <div className="drawer-backdrop" onMouseDown={e => { if (e.target === e.currentTarget) onClose() }}><aside className="drawer" role="dialog" aria-modal="true" aria-label={title}><header className="drawer-head"><div><span className="eyebrow">DETTAGLIO</span><h2>{title}</h2></div><button className="icon-button" aria-label="Chiudi" onClick={onClose}><X /></button></header><div className="drawer-body">{children}</div></aside></div>
}
export function Field({ label, name, required, children }: { label: string; name?: string; required?: boolean; children: React.ReactNode }) { return <label className="field"><span>{label}{required && <b className="required"> *</b>}</span>{children}</label> }
export function DateInput({ value, onChange, required = false }: { value: string; onChange: (iso: string) => void; required?: boolean }) {
  const [draft, setDraft] = useState(displayDate(value))
  useEffect(() => setDraft(displayDate(value)), [value])
  const parse = (text: string) => {
    if (!required && text.trim() === '') { onChange(''); return true }
    const m = /^(\d{2})\/(\d{2})\/(\d{4})$/.exec(text)
    if (!m) return false
    const [, dd, mm, yyyy] = m
    const date = new Date(Date.UTC(Number(yyyy), Number(mm) - 1, Number(dd)))
    if (date.getUTCDate() !== Number(dd) || date.getUTCMonth() + 1 !== Number(mm) || date.getUTCFullYear() !== Number(yyyy)) return false
    onChange(`${yyyy}-${mm}-${dd}`)
    return true
  }
  return <input className="date-input" type="text" inputMode="numeric" placeholder="GG/MM/AAAA" pattern="[0-9]{2}/[0-9]{2}/[0-9]{4}" title="Usa il formato GG/MM/AAAA" value={draft} onChange={e => { setDraft(e.target.value); e.currentTarget.setCustomValidity(parse(e.target.value) ? '' : 'Inserisci una data valida nel formato GG/MM/AAAA') }} onBlur={e => { e.currentTarget.setCustomValidity(parse(e.target.value) ? '' : 'Inserisci una data valida nel formato GG/MM/AAAA') }} required={required} />
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
export function Metric({ label, value, trend, tone = 'blue' }: { label: string; value: React.ReactNode; trend?: string; tone?: 'blue' | 'green' | 'amber' | 'purple' }) { return <article className={`metric-card ${tone}`}><div className="metric-top"><span>{label}</span>{trend && <span className="metric-trend">{trend.startsWith('+') ? <ArrowUpRight /> : <ArrowDownRight />}{trend}</span>}</div><strong>{value}</strong><div className="metric-rule" /></article> }
export function DataTable({ rows, columns, onRow }: { rows: Row[]; columns: { key: string; label: string; render?: (value: unknown, row: Row) => React.ReactNode }[]; onRow?: (row: Row) => void }) {
  if (!rows.length) return <Empty title="Nessun elemento" detail="Modifica i filtri o scegli un altro periodo." />
  return <div className="table-scroll"><table><thead><tr>{columns.map((c, i) => <th key={`${c.key}-${i}`} scope="col">{c.label}</th>)}</tr></thead><tbody>{rows.map((row, i) => <tr key={String(row.name ?? i)} className={onRow ? 'clickable' : ''} onClick={() => onRow?.(row)} onKeyDown={e => { if (onRow && (e.key === 'Enter' || e.key === ' ')) { e.preventDefault(); onRow(row) } }} tabIndex={onRow ? 0 : undefined}>{columns.map((c, j) => <td key={`${c.key}-${j}`}>{c.render ? c.render(row[c.key], row) : String(row[c.key] ?? '—')}</td>)}</tr>)}</tbody></table></div>
}
export const dateColumn = (key: string, label: string) => ({ key, label, render: (v: unknown) => displayDate(v) })
export const moneyColumn = (key: string, label: string) => ({ key, label, render: (v: unknown) => money(v) })
