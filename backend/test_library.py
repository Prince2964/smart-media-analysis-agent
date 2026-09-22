from . import main
from .models import Job, MediaDocument

def test_library_includes_saved_reports_without_storage_paths(monkeypatch):
    doc=MediaDocument(id='saved',source_type='video',source_name='clip.mp4',sample_name='',summary='Summary',topics=['Audio'],extracted_text='',segments=[],chunks=[],is_mock=False)
    saved=Job(id='saved',source_type='video',source_name='clip.mp4',status='complete',document=doc,storage_blob='private/path')
    monkeypatch.setattr(main,'jobs',{})
    monkeypatch.setattr(main,'load_jobs',lambda:{'saved':saved})
    result=main.report_library()
    assert result['scope']=='local-shared'
    assert result['reports'][0]['source_name']=='clip.mp4'
    assert 'storage_blob' not in result['reports'][0]
    assert main.get_job('saved').document==doc
