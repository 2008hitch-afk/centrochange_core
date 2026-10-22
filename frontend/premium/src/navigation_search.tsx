import React, { useEffect, useRef, useState } from 'react'
import { Search, X } from 'lucide-react'
import { type Boot, type Patient, ops } from './api'
import { demoPatient } from './demo_labels'

type Props = {
  boot: Boot | null
  center: string
  onSelect: (patient: Patient) => void
  onSearchAll: (query: string) => void
}

export function PatientQuickSearch({ boot, center, onSelect, onSearchAll }: Props) {
  const [query, setQuery] = useState('')
  const [rows, setRows] = useState<Patient[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [truncated, setTruncated] = useState(false)
  const [open, setOpen] = useState(false)
  const [mobileOpen, setMobileOpen] = useState(false)
  const [active, setActive] = useState(-1)
  const input = useRef<HTMLInputElement>(null)
  const toggle = useRef<HTMLButtonElement>(null)
  const container = useRef<HTMLDivElement>(null)
  const term = query.trim()

  useEffect(() => {
    if (!boot || !center || boot.center !== center || term.length < 2) {
      setRows([]); setLoading(false); setError(''); setTruncated(false); setOpen(false); return
    }
    let live = true
    setRows([]); setLoading(true); setError(''); setTruncated(false); setOpen(true); setActive(-1)
    const timer = window.setTimeout(() => {
      ops<{ patients: Patient[]; truncated: boolean }>('workspace.patient_search', { center, query: term }).then(data => {
        if (!live) return
        const aliases = boot.patients.filter(row =>
          demoPatient(row.name, row.patient_name).toLocaleLowerCase('it-IT').includes(term.toLocaleLowerCase('it-IT')))
        const merged = [...new Map([...data.patients, ...aliases].map(row => [row.name, row])).values()]
        setRows(merged.slice(0, 50))
        setTruncated(Boolean(data.truncated) || merged.length > 50)
        setLoading(false)
      }).catch(() => { if (live) { setRows([]); setLoading(false); setTruncated(false); setError('Ricerca non disponibile. Riprova.') } })
    }, 180)
    return () => { live = false; window.clearTimeout(timer) }
  }, [boot, center, term])

  useEffect(() => {
    const outside = (event: MouseEvent) => { if (!container.current?.contains(event.target as Node)) setOpen(false) }
    document.addEventListener('mousedown', outside)
    return () => document.removeEventListener('mousedown', outside)
  }, [])

  const choose = (patient: Patient) => {
    setOpen(false); setMobileOpen(false); setQuery(''); onSelect(patient)
  }
  const close = () => {
    setOpen(false)
    if (mobileOpen) { setMobileOpen(false); requestAnimationFrame(() => toggle.current?.focus()) }
  }
  const onKeyDown = (event: React.KeyboardEvent<HTMLInputElement>) => {
    if (event.key === 'Escape') { event.preventDefault(); close() }
    if (event.key === 'ArrowDown' && open && rows.length) { event.preventDefault(); setActive(index => (index + 1) % rows.length) }
    if (event.key === 'ArrowUp' && open && rows.length) { event.preventDefault(); setActive(index => index <= 0 ? rows.length - 1 : index - 1) }
    if (event.key === 'Enter' && term) {
      event.preventDefault()
      if (open && active >= 0 && rows[active]) choose(rows[active])
      else { setOpen(false); setMobileOpen(false); onSearchAll(term) }
    }
  }
  return <div className={`quick-search ${mobileOpen ? 'quick-search-mobile-open' : ''}`} ref={container}>
    <button className="icon-button mobile-search-toggle" ref={toggle} aria-label="Apri ricerca pazienti" aria-expanded={mobileOpen} onClick={() => { setMobileOpen(true); requestAnimationFrame(() => input.current?.focus()) }}><Search /></button>
    <div className="search-shell"><Search aria-hidden="true" /><input ref={input} type="search" role="combobox" aria-label="Ricerca globale pazienti" aria-autocomplete="list" aria-expanded={open && term.length >= 2} aria-controls={open && term.length >= 2 ? 'quick-patient-results' : undefined} aria-activedescendant={active >= 0 && open ? `quick-patient-${active}` : undefined} value={query} maxLength={140} onChange={event => { setQuery(event.target.value); setOpen(true) }} onFocus={() => { if (term.length >= 2) setOpen(true) }} onKeyDown={onKeyDown} placeholder="Cerca pazienti..." disabled={!boot} />
      {mobileOpen && <button className="icon-button quick-search-close" aria-label="Chiudi ricerca pazienti" onClick={close}><X /></button>}
      {open && term.length >= 2 && <div className="quick-results" id="quick-patient-results" role="listbox" aria-label="Risultati pazienti">
        {loading ? <p role="status">Ricerca in corso…</p> : error ? <p role="alert">{error}</p> : rows.length ? <>{rows.map((row, index) => <button key={row.name} id={`quick-patient-${index}`} type="button" role="option" aria-selected={active === index} onMouseEnter={() => setActive(index)} onClick={() => choose(row)}>{demoPatient(row.name, row.patient_name)}</button>)}{truncated && <p>Mostrati i primi 50 risultati. Affina la ricerca.</p>}</> : <p>Nessun paziente trovato nel centro.</p>}
      </div>}
    </div>
  </div>
}
