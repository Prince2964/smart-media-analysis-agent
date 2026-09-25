import asyncio
import json
import pytest
from . import report_editor as editor
from .models import MediaDocument, Segment


@pytest.mark.parametrize('changed_timestamp', [False, True])
def test_hinglish_repair_preserves_report_and_validates_timestamps(monkeypatch, changed_timestamp):
    original = "Host introduces the news.\n00:00.110 --> 00:02.990\nWhat a big week this has been."
    text = '00:00.110 --> 00:02.990\nYeh hafta kitna bada raha hai.'
    if changed_timestamp:
        text = text.replace('00:02.990', '00:03.990')
    segment = Segment(id='s1', label='News', text='English scene description', start=0.11, end=2.99)
    doc = MediaDocument(id='test', source_type='video', source_name='clip', sample_name='',
                        summary='Keep summary', topics=['News'], extracted_text=original,
                        segments=[segment], chunks=[segment],
                        metadata={'original_passages':[{'id':'s1','text':original}]})
    class Response:
        def raise_for_status(self): pass
        def json(self):
            return {'choices':[{'finish_reason':'stop','message':{'content':json.dumps({'s1':text})}}]}
    class Client:
        def __init__(self, **kwargs): pass
        async def __aenter__(self): return self
        async def __aexit__(self, *args): pass
        async def post(self, url, **kwargs):
            assert 'translate English' in kwargs['json']['messages'][0]['content']
            assert json.loads(kwargs['json']['messages'][1]['content']) == {'s1':original}
            return Response()
    monkeypatch.setattr(editor.httpx, 'AsyncClient', Client)
    monkeypatch.setattr(editor, 'service_headers', lambda *args: {})
    monkeypatch.setenv('REPORT_MODEL_ENDPOINT', 'https://example.invalid')
    monkeypatch.setenv('REPORT_MODEL_DEPLOYMENT', 'test')
    before = doc.model_dump()
    if changed_timestamp:
        with pytest.raises(ValueError, match='timestamps changed'):
            asyncio.run(editor.update_hinglish(doc))
    else:
        result = asyncio.run(editor.update_hinglish(doc))
        assert result.metadata.pop('hinglish_passages') == [{'id':'s1','text':text}]
        assert result.model_dump() == before
    assert doc.model_dump() == before


def test_retry_does_not_mutate_original(monkeypatch):
    doc=MediaDocument(id='test',source_type='video',source_name='clip',sample_name='',
                      summary='Original',topics=[],extracted_text='',segments=[],chunks=[])
    attempts=[]
    async def edit(copy):
        attempts.append(copy.summary)
        copy.summary='Compact'
        if len(attempts)==1:
            raise ValueError('Truncated response')
        return copy
    async def no_sleep(seconds): pass
    monkeypatch.setattr(editor,'_edit_report',edit)
    monkeypatch.setattr(editor.asyncio,'sleep',no_sleep)
    result=asyncio.run(editor.edit_report(doc))
    assert attempts==['Original','Original']
    assert doc.summary=='Original'
    assert result.summary=='Compact'


def test_batches_preserve_all_scene_ids_and_timestamps(monkeypatch):
    segments=[Segment(id=f's{i}',label='Scene',text=f'Original {i}',start=i*10) for i in range(19)]
    doc=MediaDocument(id='test',source_type='video',source_name='clip',sample_name='',
                      summary='Original',topics=[],extracted_text='',segments=segments,chunks=segments)
    async def edit(copy):
        assert len(copy.segments)<=8
        copy.summary='Compact overview'
        copy.topics=['Topic']
        copy.metadata.update(original_passages=[{'id':s.id,'text':s.text} for s in copy.segments],
            hinglish_passages=[{'id':s.id,'text':''} for s in copy.segments],report_notice='Formatted')
        return copy
    monkeypatch.setattr(editor,'_edit_report',edit)
    result=asyncio.run(editor.edit_report(doc))
    assert [(s.id,s.start) for s in result.segments]==[(s.id,s.start) for s in segments]
    assert len(result.metadata['original_passages'])==19
    assert result.summary=='Compact overview'
