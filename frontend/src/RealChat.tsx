import {useState,useRef,useEffect} from 'react';
import {api,json,time,type Answer,type Segment} from './api';

export function RealChat({id,onSeek}:{id:string;onSeek:(s:Segment)=>void}){
 const history=useRef<HTMLDivElement>(null);
 const input=useRef<HTMLTextAreaElement>(null);
 const [allowWeb,setAllowWeb]=useState(false);
 const [pending,setPending]=useState('');
 const [question,setQuestion]=useState('');
 const [messages,setMessages]=useState<{question:string;reply:Answer}[]>([]);
 const [busy,setBusy]=useState(false);const [error,setError]=useState('');
 useEffect(()=>{if(history.current)history.current.scrollTop=history.current.scrollHeight;},[messages,busy,error]);
 async function ask(e:React.FormEvent){
  e.preventDefault();if(busy||!question.trim())return;
  const submitted=question.trim();setBusy(true);setPending(submitted);setError('');
  try{const reply=await api<Answer>('/jobs/'+id+'/questions',{...json({question:submitted,allow_web:allowWeb,history:messages.slice(-4).map(m=>({question:(m.reply.resolved_question||m.question).slice(0,1000),answer:(m.reply.answer+(m.reply.web_answer?" Web result: "+m.reply.web_answer:"")).slice(0,2000)}))}),signal:AbortSignal.timeout(300000)});setMessages(m=>[...m,{question:submitted,reply}]);setQuestion('');}
  catch(e){setError(e instanceof Error?e.message:'Unable to answer. Please retry.');}finally{setBusy(false);setPending('');requestAnimationFrame(()=>input.current?.focus({preventScroll:true}));}
 }
 return <aside className="chat-panel panel media-chat" aria-label="Media questions"><div className="chat-heading"><div><h2>Ask About Your Media</h2><p className="caption">Answers from this media’s extracted content</p></div></div>
 <div className="chat-content" ref={history} tabIndex={0} role="region" aria-label="Question and answer history" aria-live="polite">{!messages.length&&<p>Ask about a detail, topic, or moment in your media. Ask about this media or related concepts. Enable web search for related details missing from the media.</p>}
 {messages.map((m,i)=><div className="exchange" key={i}><div className="user-message"><small>YOU</small><p>{m.question}</p></div><div className="agent-message"><small>{m.reply.answer_kind==='out_of_scope'?'OUTSIDE THIS MEDIA TOPIC':m.reply.answer_kind==='clarification'?'QUICK CLARIFICATION':m.reply.answer_kind==='insufficient_evidence'?'MEDIA CHECK':'FROM YOUR MEDIA'}</small><p style={{whiteSpace:'pre-wrap'}}>{m.reply.answer_kind==='insufficient_evidence' ? (m.reply.web_sources?.length ? 'I couldn’t find this detail in the retrieved video passages. Here is what external sources report:' : m.reply.web_answer || m.reply.web_error ? 'I couldn’t find this detail in the retrieved video passages.' : 'I couldn’t find this detail in the retrieved video passages. Enable web search below to check related information, then ask again.') : m.reply.answer}</p><div className="citations">{m.reply.citations.map((s,j)=><button className="timestamp" key={j} onClick={()=>onSeek(s)}>[p{m.reply.retrieved_context.findIndex(p=>p.id===s.id&&p.text===s.text)+1}] {s.start!==null?time(s.start):s.label}</button>)}</div>
 {m.reply.resolved_question&&m.reply.resolved_question!==m.question&&<p className="caption">Understood as: {m.reply.resolved_question}</p>}
 {m.reply.web_answer&&<section className="web-answer"><small>FROM THE WEB · NOT VIDEO EVIDENCE</small><p><WebText text={m.reply.web_answer} sources={m.reply.web_sources??[]}/></p>{!!m.reply.web_sources?.length&&<ul>{m.reply.web_sources.map(s=><li key={s.url}><a href={s.url} target="_blank" rel="noopener noreferrer">{s.title}</a></li>)}</ul>}</section>}{m.reply.web_error&&<p role="alert">{m.reply.web_error}</p>}
 {m.reply.citations.length>0&&<details><summary>View supporting passages</summary>{m.reply.citations.map((s,j)=><p key={j}>{s.text}</p>)}</details>}</div></div>)}
 {busy&&<div><div className="user-message"><p>{pending}</p></div><p role="status">Checking your media{allowWeb?' and searching the web if needed':''}…</p></div>}{error&&<p role="alert">{error}</p>}</div>
 <form className="question-form" onSubmit={ask}><label htmlFor="media-question">Your question</label><textarea ref={input} placeholder="Ask about a topic, detail, or timestamp…" id="media-question" value={question} onChange={e=>setQuestion(e.target.value)} maxLength={1000} disabled={busy} rows={2}/><label className="web-toggle"><input type="checkbox" checked={allowWeb} disabled={busy} onChange={e=>setAllowWeb(e.target.checked)}/> Search the web if media has no answer</label><button className="primary" disabled={busy||!question.trim()}>{busy?'Answering…':'Ask'}</button><p>Recent questions provide context. Web search sends the resolved question to Bing and may add Azure charges.</p></form></aside>;
}

function WebText({text,sources}:{text:string;sources:{url:string;title:string}[]}){
 const allowed=new Set(sources.map(s=>s.url));
 return <>{text.split(/(\[[^\]]+\]\(https?:\/\/[^\s)]+\))/g).map((part,i)=>{
  const match=part.match(/^\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)$/);
  return match&&allowed.has(match[2])?<a key={i} href={match[2]} target="_blank" rel="noopener noreferrer">{match[1]}</a>:<span key={i}>{part}</span>;
 })}</>;
}
