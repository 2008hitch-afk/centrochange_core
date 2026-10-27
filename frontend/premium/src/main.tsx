import React, { useEffect, useRef, useState } from 'react'
import { createRoot } from 'react-dom/client'
import { CalendarDays, UsersRound, Clock3, ChartNoAxesCombined, WalletCards, Bell, Menu, LogOut, ChevronDown, PanelLeftClose, X, Settings2, History, BookOpen, Archive } from 'lucide-react'
import { type Boot, type FinanceBoot, ops, finance, call } from './api'
import { Agenda, Patients, Professionals, ServiceCatalog, Availability, Reports, FinanceView, Access, Notifications } from './views'
import { AuditLog } from './audit_log'
import { MasterArchive, syntheticArchive } from './master_archive'
import { ScopedArchive } from './scoped_archive'
import { configureDemoLabels } from './demo_labels'
import { centerName } from './display_names'
import './style.css'

export type View = 'Agenda' | 'Pazienti' | 'Professionisti' | 'Servizi' | 'Disponibilità' | 'Report' | 'Finanza' | 'Archivi' | 'Gestione accessi' | 'Registro modifiche' | 'Notifiche'
const icons: Record<View, React.ReactNode> = {
  Agenda: <CalendarDays />, Pazienti: <UsersRound />, Professionisti: <UsersRound />, Servizi: <BookOpen />, Disponibilità: <Clock3 />, Report: <ChartNoAxesCombined />,
  Finanza: <WalletCards />, Archivi: <Archive />, 'Gestione accessi': <Settings2 />, 'Registro modifiche': <History />, Notifiche: <Bell />
}
const allViews: View[] = ['Agenda', 'Pazienti', 'Professionisti', 'Servizi', 'Disponibilità', 'Report', 'Finanza', 'Archivi', 'Gestione accessi', 'Registro modifiche', 'Notifiche']
function fromHash(): View {
  try { const raw = decodeURIComponent(location.hash.slice(1)); return allViews.includes(raw as View) ? raw as View : 'Agenda' }
  catch { return 'Agenda' }
}

function App() {
  const [view, setView] = useState<View>(fromHash)
  const [boot, setBoot] = useState<Boot | null>(null)
  const [financeBoot, setFinanceBoot] = useState<FinanceBoot | null>(null)
  const [center, setCenter] = useState('')
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [mobileOpen, setMobileOpen] = useState(false)
  const [mobileViewport, setMobileViewport] = useState(() => window.matchMedia('(max-width: 760px)').matches)
  const [loading, setLoading] = useState(true)
  const [loggingOut, setLoggingOut] = useState(false)
  const [userMenuOpen, setUserMenuOpen] = useState(false)
  const menuToggle = useRef<HTMLButtonElement>(null)
  const menuClose = useRef<HTMLButtonElement>(null)
  const sidebar = useRef<HTMLElement>(null)
  const hydratedCenter = useRef('')

  useEffect(() => {
    const media = window.matchMedia('(max-width: 760px)')
    const update = () => { setMobileViewport(media.matches); if (!media.matches) setMobileOpen(false) }
    media.addEventListener('change', update)
    return () => media.removeEventListener('change', update)
  }, [])

  useEffect(() => {
    const fn = () => {
      const next = fromHash()
      if (location.hash !== '#' + encodeURIComponent(next) && next === 'Agenda')
        history.replaceState(null, '', location.pathname + location.search + '#Agenda')
      setView(next)
    }
    addEventListener('hashchange', fn)
    return () => removeEventListener('hashchange', fn)
  }, [])
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
  const available = allViews.filter(v => v === 'Finanza' ? !!financeBoot : v === 'Archivi' ? syntheticArchive ? (roles.includes('CC Manager') || !!financeBoot?.can_write) : !!boot || !!financeBoot : v === 'Notifiche' ? roles.includes('CC Manager') || roles.includes('CC Professional') : ['Gestione accessi', 'Registro modifiche'].includes(v) ? roles.includes('CC Manager') : !!boot)
  const isPureProfessional = roles.includes('CC Professional') && !roles.includes('CC Manager') && !roles.includes('CC Secretariat') && !financeBoot?.can_write
  const adminViews = isPureProfessional ? ['Finanza', 'Gestione accessi', 'Registro modifiche'] : ['Finanza', 'Archivi', 'Gestione accessi', 'Registro modifiche']
  const currentView = available.includes(view) ? view : available[0]
  useEffect(() => {
    if (loading || !currentView) return
    const canonical = '#' + encodeURIComponent(currentView)
    if (location.hash !== canonical) history.replaceState(null, '', location.pathname + location.search + canonical)
    if (view !== currentView) setView(currentView)
  }, [loading, currentView, view])
  useEffect(() => {
    if (!mobileOpen) return
    menuClose.current?.focus()
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') { event.preventDefault(); setMobileOpen(false); requestAnimationFrame(() => menuToggle.current?.focus()) }
      if (event.key !== 'Tab' || !sidebar.current) return
      const focusable = [...sidebar.current.querySelectorAll<HTMLButtonElement>('button:not(:disabled)')]
      if (!focusable.length) return
      if (event.shiftKey && document.activeElement === focusable[0]) { event.preventDefault(); focusable.at(-1)?.focus() }
      if (!event.shiftKey && document.activeElement === focusable.at(-1)) { event.preventDefault(); focusable[0].focus() }
    }
    document.addEventListener('keydown', onKeyDown)
    return () => document.removeEventListener('keydown', onKeyDown)
  }, [mobileOpen])
  const centers = boot?.centers?.length ? boot.centers : financeBoot?.centers ?? []
  configureDemoLabels(boot, financeBoot)
  const switchView = (next: View) => { location.hash = encodeURIComponent(next); setView(next); setMobileOpen(false); setUserMenuOpen(false); setError(''); setNotice(''); if (mobileOpen) requestAnimationFrame(() => document.getElementById('main')?.focus()) }
  const feedback = (message: string, fail = false) => { if (fail) setError(message); else { setNotice(message); setError('') } }
  const refreshBoot = async () => { if (!center) return; const fresh = await ops<Boot>('workspace.bootstrap', { center }); setBoot(fresh) }
  const changeCenter = (next: string) => { if (next === center) return; hydratedCenter.current = ''; setBoot(null); setFinanceBoot(null); setCenter(next) }
  const logout = async () => {
    setLoggingOut(true); setUserMenuOpen(false)
    try { await call('logout', {}, true); location.replace('/login?redirect-to=/premium') }
    catch { feedback('Uscita non riuscita. Riprova.', true); setLoggingOut(false) }
  }

  return <div className="app-shell">
    <a href="#main" className="skip-link" onClick={event => { event.preventDefault(); document.getElementById('main')?.focus() }}>Vai al contenuto</a>
    <aside ref={sidebar} className={`sidebar ${mobileOpen ? 'sidebar-open' : ''}`} aria-label="Navigazione principale" inert={mobileViewport && !mobileOpen} aria-hidden={mobileViewport && !mobileOpen}>
      <div className="brand"><img src={import.meta.env.BASE_URL + 'logo.webp'} alt="Centro Change" width="36" height="35" /><div><strong>centro<span>change</span></strong><small>AREA OPERATIVA</small></div><button ref={menuClose} className="icon-button sidebar-close" aria-label="Chiudi menu" onClick={() => { setMobileOpen(false); requestAnimationFrame(() => menuToggle.current?.focus()) }}><PanelLeftClose /></button></div>
      <div className="sidebar-label">AREA OPERATIVA</div>
      <nav>{available.filter(v => !adminViews.includes(v)).map(v => <button key={v} className={`nav-item ${currentView === v ? 'active' : ''}`} aria-current={currentView === v ? 'page' : undefined} onClick={() => switchView(v)}>{icons[v]}<span>{v}</span>{v === 'Agenda' && <span className="nav-dot" />}</button>)}</nav>
      {available.some(v => adminViews.includes(v)) && <><div className="sidebar-label section-gap">AMMINISTRAZIONE</div><nav>{available.filter(v => adminViews.includes(v)).map(v => <button key={v} className={`nav-item ${currentView === v ? 'active' : ''}`} aria-current={currentView === v ? 'page' : undefined} onClick={() => switchView(v)}>{icons[v]}<span>{v}</span></button>)}</nav></>}
      <div className="sidebar-foot"><span className="sidebar-avatar">CC</span><div><strong>Centro Change</strong><small>Area riservata</small></div><button className="icon-button" title="Esci" aria-label="Esci" disabled={loggingOut} onClick={() => void logout()}><LogOut /></button></div>
    </aside>
    {mobileOpen && <button className="scrim" aria-label="Chiudi menu" onClick={() => { setMobileOpen(false); requestAnimationFrame(() => menuToggle.current?.focus()) }} />}
    <div className="workspace" inert={mobileViewport && mobileOpen}>
      <header className="topbar"><button ref={menuToggle} className="icon-button menu-toggle" aria-label="Apri menu" aria-expanded={mobileOpen} onClick={() => setMobileOpen(true)}><Menu /></button><div className="breadcrumbs"><span>Area operativa</span><span className="breadcrumb-slash">/</span><strong>{currentView}</strong></div><div className="top-actions">{centers.length === 1 ? <div className="center-selector center-context" aria-label={`Sede operativa: ${centerName(centers[0])}`}><span className="center-badge">{centerName(centers[0])}</span></div> : centers.length > 1 ? <label className="center-selector"><span className="sr-only">Centro</span><select value={center} onChange={e => changeCenter(e.target.value)}>{centers.map(c => <option key={c.name} value={c.name}>{centerName(c)}</option>)}</select><ChevronDown /></label> : null}<div className="user-menu"><button className="top-avatar" aria-label="Menu utente" aria-expanded={userMenuOpen} onClick={() => setUserMenuOpen(open => !open)}>CC</button>{userMenuOpen && <div className="user-menu-panel"><strong>Centro Change</strong><span>Area riservata</span><button disabled={loggingOut} onClick={() => void logout()}><LogOut /> Esci</button></div>}</div></div></header>
      <main id="main" className="content" tabIndex={-1}>
        {loading && <div className="loading-state" role="status"><div className="skeleton heading-skeleton" /><div className="skeleton wide-skeleton" /><div className="skeleton panel-skeleton" /></div>}
        {error && <div className="alert error" role="alert"><span>{error}</span><button onClick={() => setError('')} aria-label="Chiudi errore"><X /></button></div>}
        {notice && <div className="alert success" role="status"><span>{notice}</span><button onClick={() => setNotice('')} aria-label="Chiudi avviso"><X /></button></div>}
        {!loading && currentView === 'Agenda' && boot && <Agenda boot={boot} center={center} feedback={feedback} refreshBoot={refreshBoot} />}
        {!loading && currentView === 'Pazienti' && boot && <Patients boot={boot} center={center} feedback={feedback} refreshBoot={refreshBoot} />}
        {!loading && currentView === 'Professionisti' && boot && <Professionals boot={boot} center={center} />}
        {!loading && currentView === 'Servizi' && boot && <ServiceCatalog boot={boot} center={center} />}
        {!loading && currentView === 'Disponibilità' && boot && <Availability boot={boot} center={center} feedback={feedback} />}
        {!loading && currentView === 'Report' && boot && <Reports boot={boot} center={center} feedback={feedback} financeBoot={financeBoot} />}
        {!loading && currentView === 'Finanza' && financeBoot && <FinanceView boot={financeBoot} center={center} feedback={feedback} />}
        {!loading && currentView === 'Archivi' && (boot || financeBoot) && (syntheticArchive ? boot && <MasterArchive boot={boot} financeBoot={financeBoot} center={center} /> : <ScopedArchive boot={boot} financeBoot={financeBoot} center={center} />)}
        {!loading && currentView === 'Gestione accessi' && boot && <Access boot={boot} center={center} feedback={feedback} />}
        {!loading && currentView === 'Registro modifiche' && boot && <AuditLog feedback={feedback} />}
        {!loading && currentView === 'Notifiche' && boot && <Notifications boot={boot} center={center} feedback={feedback} />}
      </main>
      <footer className="app-footer">Centro Change · Area riservata</footer>
    </div>
  </div>
}

const root = document.getElementById('root')!
createRoot(root).render(<React.StrictMode><App /></React.StrictMode>)
