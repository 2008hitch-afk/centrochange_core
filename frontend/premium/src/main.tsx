import React, { useEffect, useRef, useState } from 'react'
import { createRoot } from 'react-dom/client'
import { CalendarDays, UsersRound, Clock3, ChartNoAxesCombined, WalletCards, Bell, Menu, Search, LogOut, ChevronDown, PanelLeftClose, X, Settings2, History, BookOpen, Archive } from 'lucide-react'
import { type Boot, type FinanceBoot, ops, finance, call } from './api'
import { Agenda, Patients, ServiceCatalog, Availability, Reports, FinanceView, Access, Notifications } from './views'
import { AuditLog } from './audit_log'
import { MasterArchive, syntheticArchive } from './master_archive'
import './style.css'

export type View = 'Agenda' | 'Pazienti' | 'Servizi' | 'Disponibilità' | 'Report' | 'Finanza' | 'Archivi' | 'Gestione accessi' | 'Registro modifiche' | 'Notifiche'
const icons: Record<View, React.ReactNode> = {
  Agenda: <CalendarDays />, Pazienti: <UsersRound />, Servizi: <BookOpen />, Disponibilità: <Clock3 />, Report: <ChartNoAxesCombined />,
  Finanza: <WalletCards />, Archivi: <Archive />, 'Gestione accessi': <Settings2 />, 'Registro modifiche': <History />, Notifiche: <Bell />
}
const allViews: View[] = ['Agenda', 'Pazienti', 'Servizi', 'Disponibilità', 'Report', 'Finanza', 'Archivi', 'Gestione accessi', 'Registro modifiche', 'Notifiche']
function fromHash(): View { const raw = decodeURIComponent(location.hash.slice(1)); return allViews.includes(raw as View) ? raw as View : 'Agenda' }

function App() {
  const [view, setView] = useState<View>(fromHash)
  const [boot, setBoot] = useState<Boot | null>(null)
  const [financeBoot, setFinanceBoot] = useState<FinanceBoot | null>(null)
  const [center, setCenter] = useState('')
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [mobileOpen, setMobileOpen] = useState(false)
  const [loading, setLoading] = useState(true)
  const [query, setQuery] = useState('')
  const hydratedCenter = useRef('')

  useEffect(() => { const fn = () => setView(fromHash()); addEventListener('hashchange', fn); return () => removeEventListener('hashchange', fn) }, [])
  useEffect(() => {
    if (center && hydratedCenter.current === center) { hydratedCenter.current = ''; return }
    let live = true
    setLoading(true); setError(''); setBoot(null); setFinanceBoot(null)
    Promise.allSettled([ops<Boot>('workspace.bootstrap', center ? { center } : {}), finance<FinanceBoot>('reporting.bootstrap', center ? { center } : {})]).then(([o, f]) => {
      if (!live) return
      if (o.status === 'fulfilled') setBoot(o.value)
      if (f.status === 'fulfilled') setFinanceBoot(f.value)
      if (!center) { const selected = o.status === 'fulfilled' ? o.value.center : f.status === 'fulfilled' ? f.value.center : ''; if (selected) { hydratedCenter.current = selected; setCenter(selected) } }
      if (o.status === 'rejected' && f.status === 'rejected') setError('Nessuna area disponibile per questo account. Verifica assegnazione e ruolo.')
      setLoading(false)
    })
    return () => { live = false }
  }, [center])
  const roles = boot?.roles ?? []
  const available = allViews.filter(v => v === 'Finanza' ? !!financeBoot : v === 'Archivi' ? syntheticArchive && (roles.includes('CC Manager') || !!financeBoot?.can_write) : ['Gestione accessi', 'Registro modifiche', 'Notifiche'].includes(v) ? roles.includes('CC Manager') : !!boot)
  const currentView = available.includes(view) ? view : available[0]
  const centers = boot?.centers?.length ? boot.centers : financeBoot?.centers ?? []
  const switchView = (next: View) => { location.hash = encodeURIComponent(next); setView(next); setMobileOpen(false); setError(''); setNotice('') }
  const feedback = (message: string, fail = false) => { if (fail) setError(message); else { setNotice(message); setError('') } }
  const refreshBoot = async () => { if (!center) return; const fresh = await ops<Boot>('workspace.bootstrap', { center }); setBoot(fresh) }
  const changeCenter = (next: string) => { hydratedCenter.current = ''; setBoot(null); setFinanceBoot(null); setQuery(''); setCenter(next) }

  return <div className="app-shell">
    <a href="#main" className="skip-link">Vai al contenuto</a>
    <aside className={`sidebar ${mobileOpen ? 'sidebar-open' : ''}`} aria-label="Navigazione principale">
      <div className="brand"><img src={import.meta.env.BASE_URL + 'logo.webp'} alt="Centro Change" width="36" height="35" /><div><strong>centro<span>change</span></strong><small>WORKSPACE</small></div><button className="icon-button sidebar-close" aria-label="Chiudi menu" onClick={() => setMobileOpen(false)}><PanelLeftClose /></button></div>
      <div className="sidebar-label">WORKSPACE</div>
      <nav>{available.filter(v => !['Finanza', 'Archivi', 'Gestione accessi', 'Registro modifiche'].includes(v)).map(v => <button key={v} className={`nav-item ${currentView === v ? 'active' : ''}`} aria-current={currentView === v ? 'page' : undefined} onClick={() => switchView(v)}>{icons[v]}<span>{v}</span>{v === 'Agenda' && <span className="nav-dot" />}</button>)}</nav>
      {available.some(v => ['Finanza', 'Archivi', 'Gestione accessi', 'Registro modifiche'].includes(v)) && <><div className="sidebar-label section-gap">AMMINISTRAZIONE</div><nav>{available.filter(v => ['Finanza', 'Archivi', 'Gestione accessi', 'Registro modifiche'].includes(v)).map(v => <button key={v} className={`nav-item ${currentView === v ? 'active' : ''}`} aria-current={currentView === v ? 'page' : undefined} onClick={() => switchView(v)}>{icons[v]}<span>{v}</span></button>)}</nav></>}
      <div className="sidebar-foot"><span className="sidebar-avatar">CC</span><div><strong>Centro Change</strong><small>Area riservata</small></div><button className="icon-button" title="Esci" aria-label="Esci" onClick={async () => { try { await call('logout', {}, true) } finally { location.href = '/login?redirect-to=/premium' } }}><LogOut /></button></div>
    </aside>
    {mobileOpen && <button className="scrim" aria-label="Chiudi menu" onClick={() => setMobileOpen(false)} />}
    <div className="workspace">
      <header className="topbar"><button className="icon-button menu-toggle" aria-label="Apri menu" onClick={() => setMobileOpen(true)}><Menu /></button><div className="breadcrumbs"><span>Workspace</span><span className="breadcrumb-slash">/</span><strong>{currentView}</strong></div><div className="top-actions"><div className="search-shell"><Search /><input value={query} onChange={e => setQuery(e.target.value)} onKeyDown={e => { if (e.key === 'Enter' && query.trim()) switchView('Pazienti') }} placeholder="Cerca pazienti..." aria-label="Cerca pazienti" disabled={!boot} /></div>{centers.length > 0 && <label className="center-selector"><span className="sr-only">Centro</span><select value={center} onChange={e => changeCenter(e.target.value)}>{centers.map(c => <option key={c.name} value={c.name}>{c.branch || c.name}</option>)}</select><ChevronDown /></label>}<span className="top-avatar" aria-hidden="true">CC</span></div></header>
      <main id="main" className="content" tabIndex={-1}>
        {loading && <div className="loading-state" role="status"><div className="skeleton heading-skeleton" /><div className="skeleton wide-skeleton" /><div className="skeleton panel-skeleton" /></div>}
        {error && <div className="alert error" role="alert"><span>{error}</span><button onClick={() => setError('')} aria-label="Chiudi errore"><X /></button></div>}
        {notice && <div className="alert success" role="status"><span>{notice}</span><button onClick={() => setNotice('')} aria-label="Chiudi avviso"><X /></button></div>}
        {!loading && currentView === 'Agenda' && boot && <Agenda boot={boot} center={center} feedback={feedback} refreshBoot={refreshBoot} />}
        {!loading && currentView === 'Pazienti' && boot && <Patients boot={boot} center={center} query={query} feedback={feedback} refreshBoot={refreshBoot} />}
        {!loading && currentView === 'Servizi' && boot && <ServiceCatalog boot={boot} center={center} />}
        {!loading && currentView === 'Disponibilità' && boot && <Availability boot={boot} center={center} feedback={feedback} />}
        {!loading && currentView === 'Report' && boot && <Reports boot={boot} center={center} feedback={feedback} />}
        {!loading && currentView === 'Finanza' && financeBoot && <FinanceView boot={financeBoot} center={center} feedback={feedback} />}
        {!loading && currentView === 'Archivi' && boot && <MasterArchive boot={boot} financeBoot={financeBoot} center={center} />}
        {!loading && currentView === 'Gestione accessi' && boot && <Access boot={boot} center={center} feedback={feedback} />}
        {!loading && currentView === 'Registro modifiche' && boot && <AuditLog feedback={feedback} />}
        {!loading && currentView === 'Notifiche' && boot && <Notifications center={center} feedback={feedback} />}
      </main>
    </div>
  </div>
}

const root = document.getElementById('root')!
createRoot(root).render(<React.StrictMode><App /></React.StrictMode>)
