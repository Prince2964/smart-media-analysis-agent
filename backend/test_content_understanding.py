import pytest
from .content_understanding import failure_detail


def test_failure_detail_exposes_only_safe_error_code():
    assert 'UnsupportedMedia' in failure_detail({'error': {'code': 'UnsupportedMedia', 'message': 'private media URL'}})
    assert 'private' not in failure_detail({'error': {'code': 'bad https://private', 'message': 'private'}})
from .content_understanding import normalize_image
from .main import app,jobs
from .models import Job
from fastapi.testclient import TestClient

def test_real_report_and_no_fixture_chat():
    body={'result':{'contents':[{'fields':{'Summary':{'valueString':'Workshop at 10:30 in Room 204.'}}}]}}
    doc=normalize_image('real','image.png',body)
    assert not doc.is_mock and doc.topics == []
    assert doc.segments[0].start is None
    with TestClient(app) as client:
        jobs['real']=Job(id='real',source_type='image',source_name='image.png',status='complete',document=doc)
        assert client.post('/api/jobs/real/questions',json={'question':'What port is shown?'}).status_code==409
        assert client.get('/api/jobs/real/search?q=204').json()['results']

@pytest.mark.parametrize('body',[{}, {'result':{'contents':[{'fields':{}}]}}])
def test_empty_result_is_not_a_report(body):
    with pytest.raises(ValueError): normalize_image('id','test.png',body)

def test_video_timestamps_and_description_search():
    from .content_understanding import normalize_video
    body={'result':{'contents':[{'startTimeMs':840,'endTimeMs':5040,'markdown':'Transcript: Welcome.', 'fields':{'Summary':{'valueString':'Room 204 is shown.'}}}]}}
    doc=normalize_video('v','clip.mp4',body)
    assert doc.segments[0].start == .84 and doc.segments[0].end == 5.04
    assert '204' in doc.chunks[0].text and 'Welcome' in doc.extracted_text
    assert doc.is_mock is False
