import { AlertTriangle, Code2, Info } from 'lucide-react'
import { motion } from 'framer-motion'
import { useEffect, useRef, useState } from 'react'
import { cardMotion } from '../motion'

export function PageHead({ eyebrow, title, copy, actions }) {
  return <motion.div className="page-head" initial={{opacity:0,y:10}} animate={{opacity:1,y:0}} transition={{duration:.35}}><div><span className="eyebrow">{eyebrow}</span><h1>{title}</h1><p>{copy}</p></div>{actions && <div>{actions}</div>}</motion.div>
}
export function Card({ children, className='', title, note, action }) {
  return <motion.section className={`card ${className}`} {...cardMotion}><div className="card-head"><div>{title && <h2>{title}</h2>}{note && <p>{note}</p>}</div>{action}</div>{children}</motion.section>
}
export function Loading({ label='Querying Supabase', compact=false }) { return <div className={`skeleton-state ${compact?'compact':''}`} aria-label={label}><div className="skeleton-line short"/><div className="skeleton-line"/><div className="skeleton-grid"><i/><i/><i/></div><small>{label}…</small></div> }
export function ErrorState({ error }) { return <div className="state error"><AlertTriangle/><strong>Data connection unavailable</strong><p>{error?.message}</p></div> }
export function SqlHint({ name }) {
  const [open,setOpen]=useState(false)
  return <div className="sql-hint"><button onClick={()=>setOpen(!open)}><Code2 size={15}/>{open?'Hide query note':'View SQL source'}</button>{open&&<p>This visual is computed by <code>{name}</code> in the single query registry <code>backend/queries.py</code>.</p>}</div>
}
export function Empty({ children='No records match this selection.' }) { return <div className="state"><p>{children}</p></div> }

export function InfoTip({ children }) { return <span className="info-tip" tabIndex="0"><Info size={13}/><span>{children}</span></span> }

export function AnimatedNumber({ value, format=(n)=>Math.round(n).toLocaleString('en-IN'), duration=700 }) {
  const [shown,setShown]=useState(0), frame=useRef()
  useEffect(()=>{const target=Number(value)||0,start=performance.now();const tick=(now)=>{const p=Math.min(1,(now-start)/duration);setShown(target*(1-Math.pow(1-p,3)));if(p<1)frame.current=requestAnimationFrame(tick)};frame.current=requestAnimationFrame(tick);return()=>cancelAnimationFrame(frame.current)},[value,duration])
  return <>{format(shown)}</>
}
