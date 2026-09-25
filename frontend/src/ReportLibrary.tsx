import {useEffect,useState} from 'react';
import {api,type Job} from './api';
type SavedReport={id:string;source_name:string;source_type:string;summary:string;topics:string[];is_mock:boolean};
export function ReportLibrary({onOpen}:{onOpen:(job:Job)=>void}){
 const [reports,setReports]=useState<SavedReport[]>([]);const [query,setQuery]=useState('');
 const [loading,setLoading]=useState(true);const [error,setError]=useState('');const [opening,setOpening]=useState('');
 async function refresh(){setLoading(true);setError('');try{const r=await api<{reports:SavedReport[]}>('/reports');setReports(r.reports);}catch(e){setError(e instanceof Error?e.message:'Unable to load reports.');}finally{setLoading(false);}}
 useEffect(()=>{void refresh();},[]);
 async function open(id:string){setOpening(id);setError('');try{onOpen(await api<Job>('/jobs/'+id));}catch(e){setError(e instanceof Error?e.message:'Unable to open report.');}finally{setOpening('');}}
 const matches=reports.filter(r=>(r.source_name+' '+r.topics.join(' ')).toLowerCase().includes(query.toLowerCase()));
 return <main className="workspace"><div className="page-title"><div><p className="eyebrow">SAVED ANALYSES</p><h1>Local report library</h1><p>Reopen completed reports without uploading again.</p></div><button className="secondary" disabled={loading} onClick={refresh}>Refresh library</button></div>
 <label htmlFor="report-filter">Find a report by filename or topic</label><input id="report-filter" value={query} onChange={e=>setQuery(e.target.value)} placeholder="Search saved reports…"/>
 {error&&<p role="alert" className="error">{error}</p>}{loading?<p role="status">Loading saved reports…</p>:matches.length?<div className="library-list">{matches.map(r=><article className="panel library-card" key={r.id}><div><span className="badge">{r.is_mock?'Prepared sample':'Uploaded media'} · {r.source_type}</span><h2>{r.source_name}</h2><p>{r.summary}{r.summary.length===240?'…':''}</p><p className="caption">Report {r.id.slice(0,8)}</p></div><button className="secondary" disabled={!!opening} onClick={()=>open(r.id)}>{opening===r.id?'Opening…':'Open report'}</button></article>)}</div>:<p>{reports.length?'No matching reports.':'No completed reports yet. Analyze media to save your first report.'}</p>}</main>;
}
