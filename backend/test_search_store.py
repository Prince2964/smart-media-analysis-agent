from .search_store import make_rows
from .models import MediaDocument,Segment

def test_index_original_evidence_and_chunk_overlap():
    original='A'*2200
    s=Segment(id='s',text='Generated paraphrase',label='Topic',start=12,end=20)
    doc=MediaDocument(id='media',source_type='video',source_name='v',sample_name='v',summary='summary',topics=[],extracted_text=original,segments=[s],chunks=[s],is_mock=False,metadata={'original_passages':[{'id':'s','text':original}]})
    rows=make_rows(doc)
    assert len(rows)==2 and len(rows[0]['text'])==2000
    assert all('Generated' not in r['text'] for r in rows)
    assert rows[0]['start']==12 and rows[1]['media_id']=='media'
    assert rows[0]['id']!=rows[1]['id']
