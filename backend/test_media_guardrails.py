import asyncio
import pytest
from .media_guardrails import check_scores, MediaRejected
from . import main
from .models import Job


def test_moderation_requires_complete_valid_scores():
    rows = [{'category':c,'severity':0} for c in ('Hate','Sexual','SelfHarm','Violence')]
    check_scores({'categoriesAnalysis':rows})
    rows[-1]['severity']=4
    with pytest.raises(MediaRejected,match='Violence'):
        check_scores({'categoriesAnalysis':rows})
    with pytest.raises(MediaRejected,match='incomplete'):
        check_scores({})


def test_rejected_media_never_reaches_storage_or_analysis(monkeypatch):
    def reject(*args): raise MediaRejected('Content blocked')
    monkeypatch.setattr(main,'screen_media',reject)
    job=Job(id='blocked',source_type='video',source_name='test')
    asyncio.run(main.process(job,data=b'bad'))
    assert job.status=='failed' and job.document is None and job.storage_blob is None
    assert job.error=='Content blocked'


def test_link_is_screened_too(monkeypatch):
    monkeypatch.setattr(main,'fetch_video',lambda url:('clip',b'bad','video/mp4'))
    def reject(*args): raise MediaRejected('Content blocked')
    monkeypatch.setattr(main,'screen_media',reject)
    job=Job(id='blocked-link',source_type='link',source_name='test')
    asyncio.run(main.process(job,link_url='https://example.com/video.mp4'))
    assert job.status=='failed' and job.storage_blob is None
