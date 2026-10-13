import { useState } from 'react'
import { NavLink, useLocation } from 'react-router-dom'
import { AnimatePresence, motion } from 'framer-motion'
import { Activity, BadgeIndianRupee, BookOpenText, Building2, ChartNoAxesCombined, ChevronRight, Database, LayoutDashboard, Menu, Search, ShieldAlert, X } from 'lucide-react'
import { pageMotion } from '../motion'

const groups = [
  { label: 'Overview', links: [{ to: '/', label: 'Dashboard', icon: LayoutDashboard }] },
  { label: 'Explore', links: [
    { to: '/search', label: 'Medicine finder', icon: Search },
    { to: '/manufacturers', label: 'Manufacturers', icon: Building2 },
    { to: '/savings', label: 'Savings explorer', icon: BadgeIndianRupee },
    { to: '/safety', label: 'Safety signals', icon: ShieldAlert },
  ]},
  { label: 'Insights', links: [
    { to: '/chart-insights', label: 'Insights', icon: BookOpenText },
    { to: '/insights', label: 'EDA report', icon: ChartNoAxesCombined },
    { to: '/sql', label: 'SQL transparency', icon: Database },
  ]},
]

export default function Layout({ children }) {
  const [open, setOpen] = useState(false)
  const location = useLocation()
  const current = groups.flatMap(g => g.links).find(link => link.to === location.pathname)?.label || 'Dashboard'
  return <div className="app-shell">
    <aside className={`sidebar ${open ? 'open' : ''}`}>
      <div className="brand"><img className="brand-logo" src="/Medintel Healthcare Analytics Logo.png" alt="MedIntel India Healthcare Analytics" /></div>
      <button className="mobile-close" onClick={() => setOpen(false)}><X/></button>
      <nav>{groups.map(group => <div className="nav-group" key={group.label}>
        <p>{group.label}</p>{group.links.map(({to,label,icon:Icon}) => <NavLink to={to} key={to} end={to === '/'} onClick={() => setOpen(false)}><Icon size={18}/><span>{label}</span></NavLink>)}
      </div>)}</nav>
      <div className="sidebar-foot"><Activity size={18}/><div><strong>Live data layer</strong><span>Supabase PostgreSQL</span></div><i/></div>
    </aside>
    {open && <button className="scrim" aria-label="Close menu" onClick={() => setOpen(false)}/>} 
    <main><header className="topbar"><button className="menu-button" onClick={() => setOpen(true)}><Menu/></button><div className="crumbs"><span>MedIntel</span><ChevronRight/><strong>{current}</strong></div><div className="top-actions"><div className="dataset-pill"><span/><div><b>6,196 live records</b><small>Synced today · Supabase</small></div></div><a className="source-link" href="https://www.kaggle.com/datasets/mohneesh7/indian-medicine-data" target="_blank">Source ↗</a><div className="project-avatar" title="T.Y. B.Tech AIDS mini-project">MI</div></div></header><AnimatePresence mode="wait"><motion.div className="page-wrap" key={location.pathname} {...pageMotion}>{children}</motion.div></AnimatePresence></main>
  </div>
}
