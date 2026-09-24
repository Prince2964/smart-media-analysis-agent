import pytest
from . import link_media as links

def test_youtube_normalization():
    assert links.normalize_link('https://youtu.be/BwMEA-bEOEU?si=tracking') == ('https://www.youtube.com/watch?v=BwMEA-bEOEU',True)


def test_network_timeout_is_actionable_link_error(monkeypatch):
    def stalled(*args): raise TimeoutError('private host details')
    monkeypatch.setattr(links,'_download_public',stalled)
    with pytest.raises(links.LinkError,match='host stopped responding') as error:
        links.download_public('https://example.com/clip.mp4')
    assert 'private' not in str(error.value)


def test_download_timeout_is_not_reported_as_azure_failure(monkeypatch):
    import asyncio
    from . import main
    from .models import Job
    def stalled(*args): raise TimeoutError()
    monkeypatch.setattr(main,'fetch_video',stalled)
    job=Job(id='timeout',source_type='link',source_name='Video from link')
    asyncio.run(main.process(job,link_url='https://example.com/clip.mp4'))
    assert job.phase=='Link could not be analyzed'
    assert 'download exceeded' in job.error

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


def test_youtube_separate_streams_are_merged(monkeypatch):
    import yt_dlp
    class FakeYoutube:
        def __init__(self,*args,**kwargs): pass
        def __enter__(self): return self
        def __exit__(self,*args): pass
        def extract_info(self,*args,**kwargs):
            return {'title':'Clip','formats':[
                {'protocol':'https','ext':'mp4','vcodec':'h264','acodec':'none','height':360,'url':'https://r.googlevideo.com/v'},
                {'protocol':'https','ext':'m4a','vcodec':'none','acodec':'aac','url':'https://r.googlevideo.com/a'}]}
    monkeypatch.setattr(yt_dlp,'YoutubeDL',FakeYoutube)
    monkeypatch.setattr(links,'download_public',lambda url,audio=False:(b'audio' if audio else b'video','video/mp4'))
    def merge(v,a):
        assert v==b'video' and a==b'audio'
        return b'combined','video/mp4'
    monkeypatch.setattr(links,'merge_streams',merge)
    assert links.fetch_video('https://youtu.be/BwMEA-bEOEU')==('Clip',b'combined','video/mp4')
