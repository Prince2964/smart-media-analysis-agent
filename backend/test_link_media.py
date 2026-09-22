import pytest
from . import link_media as links

def test_youtube_normalization():
    assert links.normalize_link('https://youtu.be/BwMEA-bEOEU?si=tracking') == ('https://www.youtube.com/watch?v=BwMEA-bEOEU',True)

@pytest.mark.parametrize('url',['file:///secret','http://example.com/a.mp4','https://user:pass@example.com/a.mp4','https://example.com:8443/a.mp4','https://youtube.com/playlist?list=abc','https://example.com/page'])
def test_invalid_urls(url):
    with pytest.raises(links.LinkError): links.normalize_link(url)

@pytest.mark.parametrize('address',['127.0.0.1','10.0.0.1','169.254.169.254','::1'])
def test_private_dns_rejected(monkeypatch,address):
    monkeypatch.setattr(links.socket,'getaddrinfo',lambda *a,**k:[(None,None,None,None,(address,443))])
    with pytest.raises(links.LinkError): links.public_addresses('example.com')

def test_direct_video_download_and_size_limit(monkeypatch):
    payload=b'\x00\x00\x00\x18ftypisom'+b'0'*20
    class Response:
        status=200
        def getheader(self,name,default=''): return str(len(payload)) if name=='Content-Length' else default
        def read(self,n):
            if getattr(self,'done',False): return b''
            self.done=True
            return payload
    class Connection:
        def __init__(self,*a,**k): pass
        def request(self,*a,**k): pass
        def getresponse(self): return Response()
        def close(self): pass
    monkeypatch.setattr(links,'public_addresses',lambda host:['93.184.216.34'])
    monkeypatch.setattr(links.http.client,'HTTPSConnection',Connection)
    assert links.download_public('https://example.com/clip.mp4')==(payload,'video/mp4')
    monkeypatch.setattr(links,'MAX_BYTES',10)
    with pytest.raises(links.LinkError,match='100 MB'): links.download_public('https://example.com/clip.mp4')

def test_link_pipeline_uses_downloaded_bytes_for_real_analysis(monkeypatch):
    import asyncio
    from . import main
    from .models import Job,MediaDocument
    monkeypatch.setenv('PROCESSING_MODE','azure-media')
    monkeypatch.delenv('REPORT_MODEL_ENDPOINT',raising=False)
    monkeypatch.setattr(main,'storage',None)
    monkeypatch.setattr(main,'search_store',None)
    monkeypatch.setattr(main,'fetch_video',lambda url:('Real linked clip',b'video bytes','video/mp4'))
    async def analyze(id,name,data,content_type,kind):
        assert data==b'video bytes' and kind=='video'
        return MediaDocument(id=id,source_type=kind,source_name=name,sample_name='',summary='Real extraction',topics=[],extracted_text='',segments=[],chunks=[],is_mock=False)
    monkeypatch.setattr(main,'analyze_media',analyze)
    job=Job(id='linked',source_type='link',source_name='Video from link')
    asyncio.run(main.process(job,link_url='https://example.com/video.mp4'))
    assert job.status=='complete'
    assert not job.document.is_mock
    assert job.document.metadata['input_method']=='public-video-link'
