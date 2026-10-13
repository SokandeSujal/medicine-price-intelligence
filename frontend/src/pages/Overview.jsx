import { useState } from 'react'
import { Activity, ArrowRight, Building2, IndianRupee, PackageSearch } from 'lucide-react'
import { motion } from 'framer-motion'
import { Link } from 'react-router-dom'
import { money } from '../api'
import { Donut, HorizontalBars, PriceHistogramChart } from '../components/Charts'
import { AnimatedNumber, Card, ErrorState, Loading, SqlHint } from '../components/UI'
import { useApi } from '../hooks'

export default function Overview() {
  const [log,setLog]=useState(false)
  const kpis=useApi('/api/overview'), histogram=useApi('/api/price-distribution'), top=useApi('/api/manufacturers/top?limit=7'), gaps=useApi('/api/price-gaps?min_brands=5&limit=5'), safety=useApi('/api/safety/overview')
  if (kpis.loading) return <Loading/>
  if (kpis.error) return <ErrorState error={kpis.error}/>
  const k=kpis.data
  const cards=[
    {label:'Medicines indexed',value:k.total_medicines,detail:'Cleaned and verified records',icon:PackageSearch},
    {label:'Manufacturers',value:k.total_manufacturers,detail:'Represented in the dataset',icon:Building2},
    {label:'Active ingredients',value:k.total_salts,detail:`Across ${k.total_categories} treatment categories`,icon:Activity},
    {label:'Typical listed price',value:k.median_price,detail:`Average is ${money(k.avg_price)}`,icon:IndianRupee,money:true},
  ]
  return <>
    <motion.section className="overview-hero dashboard-hero" initial={{opacity:0,y:14}} animate={{opacity:1,y:0}} transition={{duration:.5}}>
      <div className="hero-copy"><span className="eyebrow">Executive overview · live Supabase data</span><h1>Medicine market dashboard</h1><p>Key numbers for price, coverage, savings, and safety across 6,196 cleaned Indian medicine records.</p><div className="hero-actions"><Link to="/chart-insights">Read the full analysis <ArrowRight/></Link><span className="live-status"><i/>Database connected</span></div></div>
      <div className="hero-visual"><div className="hero-halo"/><img src="/medintel-hero-3d.png" alt="Blue and white 3D medicine forms with an analytical data ribbon"/><span className="float-chip top"><b>{k.total_categories}</b> categories</span><span className="float-chip bottom"><b>{k.life_threatening_pct}%</b> safety-flagged</span></div>
    </motion.section>

    <div className="kpi-grid">{cards.map(({label,value,detail,icon:Icon,money:currency},i)=><motion.div className="kpi" key={label} initial={{opacity:0,y:12}} animate={{opacity:1,y:0}} transition={{delay:.1+i*.055,duration:.38}} whileHover={{y:-4}}><div><span>{label}</span><i><Icon size={18}/></i></div><strong><AnimatedNumber value={value} format={n=>currency?money(n):Math.round(n).toLocaleString('en-IN')}/></strong><p>{detail}</p></motion.div>)}</div>

    <div className="dashboard-grid dashboard-summary" id="price-landscape">
      <Card className="span-2 dashboard-primary-chart" title="Medicine price distribution" note="Number of medicines in each listed-price range" action={<button className="toggle" onClick={()=>setLog(!log)}>{log?'Log scale':'Regular scale'}</button>}>
        {histogram.loading?<Loading/>:<PriceHistogramChart data={histogram.data} log={log} height={310}/>}<SqlHint name="PRICE_HISTOGRAM"/>
      </Card>

      <Card className="safety-summary" title="Safety flag share" note="Records requiring high-priority interaction review">
        {safety.loading?<Loading/>:<><Donut flagged={safety.data.flagged} safe={safety.data.not_flagged}/><div className="dashboard-stat-row"><div><strong>{safety.data.flagged.toLocaleString('en-IN')}</strong><span>flagged records</span></div><div><strong>{safety.data.not_flagged.toLocaleString('en-IN')}</strong><span>not flagged</span></div></div></>}<SqlHint name="SAFETY_OVERVIEW"/>
      </Card>

      <Card className="span-2" title="Largest manufacturer portfolios" note="Companies with the most medicine listings in this dataset">
        {top.loading?<Loading/>:<HorizontalBars data={top.data||[]}/>}<SqlHint name="TOP_MANUFACTURERS"/>
      </Card>

      <Card className="savings-summary" title="Top savings opportunities" note="Cheapest versus highest-priced brand for the same active ingredient">
        {gaps.loading?<Loading/>:<div className="dashboard-savings-list">{(gaps.data||[]).map((row,index)=><div key={row.primary_salt}><span>{String(index+1).padStart(2,'0')}</span><p><strong>{row.primary_salt}</strong><small>{money(row.min_price)} to {money(row.max_price)}</small></p><b>{Number(row.max_savings_pct).toFixed(1)}%</b></div>)}</div>}<Link className="dashboard-more" to="/savings">Open Savings Explorer <ArrowRight/></Link><SqlHint name="PRICE_GAPS"/>
      </Card>
    </div>
  </>
}
