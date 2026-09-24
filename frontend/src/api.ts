export type Kind = 'video'|'image'|'link';
export type Segment = {id:string;text:string;label:string;start:number|null;end:number|null;region:string|null};
export type MediaDocument = {id:string;source_type:Kind;source_name:string;sample_name:string;summary:string;topics:string[];extracted_text:string;segments:Segment[];chunks:Segment[];visual_information:string[];metadata:{duration_seconds:number|null;notice:string;search_provider?:string;report_notice?:string;original_passages?:{id:string;text:string}[];hinglish_passages?:{id:string;text:string}[]};is_mock:boolean};
export type Job = {storage_blob?:string|null;phase?:string;timings?:Record<string,number>;id:string;source_type:Kind;source_name:string;status:'queued'|'processing'|'complete'|'failed';stage:number;error:string|null;document:MediaDocument|null};
export type Answer = {resolved_question?:string;web_answer?:string;web_sources?:{url:string;title:string}[];web_error?:string;answer:string;citations:Segment[];retrieved_context:Segment[];answer_kind:string;notice:string;search_provider?:string;report_notice?:string;original_passages?:{id:string;text:string}[];hinglish_passages?:{id:string;text:string}[]};
export const DEMO_URL='https://example.com/demo/product-briefing';
export async function api<T>(path:string, options:RequestInit={}):Promise<T>{
 const response=await fetch('/api'+path,{...options,signal:options.signal??AbortSignal.timeout(30000)});
 if(!response.ok){const body=await response.json().catch(()=>({}));throw new Error(typeof body.detail==='string'?body.detail:'The request could not be completed. Check the input and try again.');}
 return response.json();
}
export const json=(body:unknown):RequestInit=>({method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
export function time(seconds:number){return `${Math.floor(seconds/60).toString().padStart(2,'0')}:${Math.floor(seconds%60).toString().padStart(2,'0')}`;}


