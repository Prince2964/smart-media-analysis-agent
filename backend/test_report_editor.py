import asyncio
from . import report_editor as editor
from .models import MediaDocument, Segment


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
