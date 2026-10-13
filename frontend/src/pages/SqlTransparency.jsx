import { useState } from 'react'
import { Check, Copy, Database, GitBranch, Sigma } from 'lucide-react'
import { ErrorState, Loading, PageHead } from '../components/UI'
import { useApi } from '../hooks'

function QueryBlock({query}){const [copied,setCopied]=useState(false);return <details className="query-block"><summary><span><code>{query.name}</code><small>{query.section}</small></span><b>View SQL</b></summary><p>{query.purpose}</p><div className="code-wrap"><button onClick={()=>{navigator.clipboard.writeText(query.sql);setCopied(true);setTimeout(()=>setCopied(false),1200)}}>{copied?<Check/>:<Copy/>}</button><pre><code>{query.sql.trim()}</code></pre></div></details>}
export default function SqlTransparency(){const q=useApi('/api/debug/queries');if(q.loading)return <Loading/>;if(q.error)return <ErrorState error={q.error}/>;return <><PageHead eyebrow="Methods · SQL transparency" title="See the SQL behind every result" copy="Open any named query to see exactly how Supabase data is joined, grouped, filtered, and summarized for the dashboard."/>
  <div className="sql-stats"><div><Database/><strong>{q.data.count}</strong><span>named SQL statements</span></div><div><GitBranch/><strong>3</strong><span>normalized tables</span></div><div><Sigma/><strong>14</strong><span>analytical queries</span></div></div>
  <div className="query-list">{q.data.queries.map(query=><QueryBlock query={query} key={query.name}/>)}</div></>}
