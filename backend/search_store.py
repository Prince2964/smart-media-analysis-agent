"""Azure AI Search keyword retrieval, scoped to one media document."""
import hashlib
import os
import httpx
from .auth import get_credential
from .models import Segment

class SearchStore:
    def __init__(self):
        self.endpoint=os.environ['AZURE_SEARCH_ENDPOINT'].rstrip('/')
        self.index=os.environ['AZURE_SEARCH_INDEX']
        self.credential=get_credential()

    def request(self, method, path, body=None):
        token=self.credential.get_token('https://search.azure.com/.default').token
        response=httpx.request(method, self.endpoint+path, params={'api-version':'2024-07-01'},
            headers={'Authorization':'Bearer '+token},json=body,timeout=30)
        response.raise_for_status()
        return response.json() if response.content else {}

    def ensure_index(self):
        try:
            self.request('GET',f'/indexes/{self.index}')
            return
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code != 404: raise
        fields=[{'name':'id','type':'Edm.String','key':True},
            {'name':'media_id','type':'Edm.String','filterable':True},
            {'name':'segment_id','type':'Edm.String'},
            {'name':'text','type':'Edm.String','searchable':True},
            {'name':'label','type':'Edm.String','searchable':True},
            {'name':'start','type':'Edm.Double'},{'name':'end','type':'Edm.Double'},
            {'name':'region','type':'Edm.String'}]
        self.request('POST','/indexes',{'name':self.index,'fields':fields})

    def index_document(self, doc):
        rows=make_rows(doc)
        for offset in range(0,len(rows),100):
            result=self.request('POST',f'/indexes/{self.index}/docs/index',{'value':rows[offset:offset+100]})
            if not all(row.get('status') for row in result['value']):
                raise RuntimeError('Some search passages failed to index')

    def search(self, doc, query):
        if not query.strip(): return []
        result=self.request('POST',f'/indexes/{self.index}/docs/search',{
            'search':query,'queryType':'simple','searchFields':'text,label','top':5,
            'filter':"media_id eq '"+doc.id.replace("'","''")+"'"})
        return [Segment(id=r['segment_id'],text=r['text'],label=r['label'],
            start=r.get('start'),end=r.get('end'),region=r.get('region')) for r in result['value']]

def make_rows(doc):
    originals={p['id']:p['text'] for p in doc.metadata.get('original_passages',[])}
    rows=[]
    for s in doc.segments:
        text=originals.get(s.id,s.text)
        # Preserve original evidence; generated Hinglish and report paraphrases aren't indexed.
        for offset in range(0,len(text),1800):
            key=hashlib.sha256(f'{doc.id}:{s.id}:{offset}'.encode()).hexdigest()
            rows.append({'@search.action':'mergeOrUpload','id':key,'media_id':doc.id,
                'segment_id':s.id,'text':text[offset:offset+2000],'label':s.label,
                'start':s.start,'end':s.end,'region':s.region})
    return rows
