import asyncio
import io
import os
from .config import load_backend_env
from .auth import key_mode
from time import perf_counter
from contextlib import asynccontextmanager, contextmanager
from uuid import uuid4, UUID
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from PIL import Image, UnidentifiedImageError
from .models import Job, MediaDocument, DemoRequest, LinkRequest, Question, SourceType
from .processing import MockProcessor, resolve_link
from .retrieval import LocalRetriever, FixtureAgent
from .storage import AzureBlobStorage
from .content_understanding import analyze_media, AnalysisFailure
from .report_editor import edit_report
from .search_store import SearchStore
from .job_store import save_job, load_jobs
from .foundry_agent import answer_question
from .web_answers import answer_with_fallback
from .link_media import normalize_link, fetch_video, LinkError

jobs: dict[str, Job] = {}
tasks: set[asyncio.Task] = set()
MAX_BYTES = 100 * 1024 * 1024
processor = MockProcessor()
retriever = LocalRetriever()
agent = FixtureAgent(retriever)
storage_verified = False
storage: AzureBlobStorage | None = None
search_store: SearchStore | None = None

@asynccontextmanager
async def lifespan(app):
    global storage, search_store, storage_verified
    load_backend_env()
    jobs.update(load_jobs())
    if os.getenv('AZURE_SEARCH_ENDPOINT'):
        search_store = SearchStore()
        await asyncio.to_thread(search_store.ensure_index)
    if os.getenv('PROCESSING_MODE', 'mock') not in ('mock', 'azure-image', 'azure-media'):
        raise RuntimeError('Use PROCESSING_MODE=mock or azure-image.')
    if os.getenv('PROCESSING_MODE') in ('azure-image', 'azure-media') and not os.getenv('CONTENT_UNDERSTANDING_ENDPOINT'):
        raise RuntimeError('CONTENT_UNDERSTANDING_ENDPOINT is required.')
    storage_mode = os.getenv('STORAGE_MODE', 'discard')
    if storage_mode not in ('discard', 'azure'):
        raise RuntimeError('STORAGE_MODE must be discard or azure.')
    if storage_mode == 'azure':
        storage = AzureBlobStorage.from_env()
        try:
            await asyncio.to_thread(storage.container.get_container_properties)
            storage_verified = True
        except Exception:
            # Saved reports and chat remain usable when upload storage is unavailable.
            storage_verified = False
    yield
    for task in tasks:
        task.cancel()
    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)
    if storage:
        storage.close()
        storage = None
    if search_store:
        if search_store.credential:
            search_store.credential.close()
        search_store = None

app = FastAPI(title='Smart Media Analysis Agent — local mock API', lifespan=lifespan)

@contextmanager
def timed_phase(job, key, label):
    job.phase = label
    started = perf_counter()
    try:
        yield
    finally:
        job.timings[key] = round(perf_counter() - started, 3)


async def process(job: Job, fail: bool = False, data: bytes | None = None, content_type: str = 'application/octet-stream', link_url: str | None = None):
    started = perf_counter()
    try:
        job.status = 'processing'
        if link_url:
            with timed_phase(job, 'download', 'Downloading video from link'):
                name, data, content_type = await asyncio.wait_for(asyncio.to_thread(fetch_video, link_url), timeout=180)
                job.source_name = name
                job.source_type = 'video'
        if storage and data is not None:
            with timed_phase(job, 'upload', 'Saving upload to Azure Storage'):
                job.storage_blob = await asyncio.to_thread(storage.upload, data, content_type)
        for stage in range(1, 4):
            job.stage = stage
            if data is None:
                await asyncio.sleep(0.35)
        if fail:
            raise ValueError('Simulated processing failure. Retry with a sample or choose another file.')
        if data is not None and (job.source_type == 'image' or os.getenv('PROCESSING_MODE') == 'azure-media') and os.getenv('PROCESSING_MODE') in ('azure-image', 'azure-media'):
            with timed_phase(job, 'analysis', 'Analyzing media in Azure'):
                job.document = await analyze_media(job.id, job.source_name, data, content_type, job.source_type)
            if os.getenv('REPORT_MODEL_ENDPOINT'):
                try:
                    with timed_phase(job, 'formatting', 'Preparing summary, topics and readable transcript'):
                        job.document = await edit_report(job.document)
                except Exception:
                    job.document.metadata['report_notice'] = 'Compact report generation failed. Original extraction is shown.'
        else:
            job.document = processor.analyze(job.id, job.source_type, job.source_name)
        if link_url:
            job.document.metadata['input_method'] = 'public-video-link'
        if search_store and not job.document.is_mock:
            try:
                with timed_phase(job, 'indexing', 'Making report searchable'):
                    await asyncio.to_thread(search_store.index_document, job.document)
                job.document.metadata['search_provider'] = 'azure-ai-search'
            except Exception:
                job.document.metadata['search_provider'] = 'indexing-failed'
        job.stage = 4
        job.status = 'complete'
        job.phase = 'Report ready'
    except LinkError as exc:
        job.error = str(exc)
        job.status = 'failed'
        job.phase = 'Link could not be analyzed'
    except asyncio.CancelledError:
        raise
    except Exception as exc:
        # Record only non-secret diagnostic categories, never raw service responses.
        import logging
        logging.getLogger(__name__).warning('Job %s failed in %s: %s', job.id, job.phase, type(exc).__name__)
        if isinstance(exc, AnalysisFailure):
            job.error = str(exc)
        elif job.phase == 'Saving upload to Azure Storage':
            job.error = 'Saving the file to Azure Storage failed. Check the connection and storage access, then retry your file upload.'
        else:
            job.error = 'Azure media analysis failed. Please retry. Your saved reports are unaffected.'
        job.status = 'failed'
        job.phase = 'Processing failed'
    finally:
        job.timings['total'] = round(perf_counter() - started, 3)
        if job.status in ('complete', 'failed'):
            await asyncio.to_thread(save_job, job)

def create_job(kind: SourceType, name: str, fail: bool = False, data: bytes | None = None, content_type: str = 'application/octet-stream', link_url: str | None = None):
    if len(jobs) >= 100:
        finished = next((key for key, value in jobs.items() if value.status in ('complete', 'failed')), None)
        if finished:
            del jobs[finished]
        else:
            raise HTTPException(429, 'Too many active jobs. Try again shortly.')
    job = Job(id=str(uuid4()), source_type=kind, source_name=name)
    jobs[job.id] = job
    task = asyncio.create_task(process(job, fail, data, content_type, link_url))
    tasks.add(task)
    task.add_done_callback(tasks.discard)
    return job

def get_job(job_id: str) -> Job:
    if job_id not in jobs:
        saved = load_jobs().get(job_id)
        if saved:
            jobs[job_id] = saved
        else:
            raise HTTPException(404, 'Job not found. The local server may have restarted.')
    return jobs[job_id]

def get_document(job_id: str):
    job = get_job(job_id)
    if job.status != 'complete' or not job.document:
        raise HTTPException(409, 'The report is not ready.')
    return job.document

@app.get('/api/health')
def health():
    return {'mode': os.getenv('PROCESSING_MODE', 'mock'), 'azure_connected': storage is not None or search_store is not None,
            'agent': 'azure-openai' if key_mode() else 'foundry-agent' if os.getenv('FOUNDRY_AGENT_NAME') else 'local-fixture',
            'agent_configured': bool(os.getenv('REPORT_MODEL_KEY')) if key_mode() else bool(os.getenv('FOUNDRY_AGENT_NAME')),
            'storage': 'azure' if storage else 'discard', 'blob_access_verified': storage_verified}

@app.get('/api/reports')
def report_library():
    saved = load_jobs()
    saved.update(jobs)
    return {'reports': [{'id': j.id, 'source_name': j.source_name,
                        'source_type': j.source_type, 'summary': j.document.summary[:240],
                        'topics': j.document.topics[:6], 'is_mock': j.document.is_mock}
                       for j in saved.values() if j.status == 'complete' and j.document],
            'scope': 'local-shared'}

@app.post('/api/demo', status_code=202)
async def demo(request: DemoRequest):
    return create_job(request.source_type, 'Prepared image sample' if request.source_type == 'image' else 'Prepared product briefing sample', request.simulate_failure)

@app.post('/api/links', status_code=202)
async def link(request: LinkRequest):
    url = request.url.strip()
    if url == 'https://example.com/demo/product-briefing':
        return create_job('link', resolve_link(url))
    if os.getenv('PROCESSING_MODE') != 'azure-media':
        raise HTTPException(422, 'Real video links require Azure media mode. Upload a file or use the demo link.')
    try:
        normalized, _ = normalize_link(url)
    except LinkError as exc:
        raise HTTPException(422, str(exc))
    return create_job('link', 'Video from link', link_url=normalized)

@app.post('/api/uploads', status_code=202)
async def upload(source_type: SourceType = Form(...), file: UploadFile = File(...)):
    try:
        if source_type not in ('video', 'image'):
            raise HTTPException(422, 'Choose video or image for file upload.')
        data = await file.read(MAX_BYTES + 1)
        if not data:
            raise HTTPException(422, 'The file is empty. Choose a video or image.')
        if len(data) > MAX_BYTES:
            raise HTTPException(413, 'Local demo limit is 100 MB per file.')
        name = (file.filename or 'upload').replace('\\', '/').split('/')[-1][:200]
        suffix = name.rsplit('.', 1)[-1].lower()
        if source_type == 'image':
            if suffix not in ('png', 'jpg', 'jpeg', 'webp'):
                raise HTTPException(415, 'Use a PNG, JPG or WebP image.')
            try:
                with Image.open(io.BytesIO(data)) as picture:
                    if picture.format not in ('PNG','JPEG','WEBP') or picture.width * picture.height > 25_000_000:
                        raise ValueError('Unsupported image')
                    picture.verify()
            except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError):
                raise HTTPException(415, 'The image is invalid or exceeds 25 megapixels.')
        else:
            mp4 = suffix in ('mp4', 'mov') and len(data) > 16 and data[4:8] == b'ftyp'
            webm = suffix == 'webm' and data[:4] == bytes.fromhex('1a45dfa3')
            if not (mp4 or webm):
                raise HTTPException(415, 'Use an MP4, MOV or WebM file with a valid container header.')
        content_types = {'png': 'image/png', 'jpg': 'image/jpeg', 'jpeg': 'image/jpeg',
                         'webp': 'image/webp', 'mp4': 'video/mp4', 'mov': 'video/quicktime', 'webm': 'video/webm'}
        # Real storage is optional and independent from fixture analysis.
        return create_job(source_type, name, data=data if storage or os.getenv('PROCESSING_MODE') in ('azure-image', 'azure-media') else None, content_type=content_types[suffix])
    finally:
        await file.close()

@app.get('/api/jobs/{job_id}')
def status(job_id: str):
    return get_job(job_id)

report_repairs: set[str] = set()

@app.post('/api/jobs/{job_id}/format-report')
async def format_report(job_id: str):
    document = get_document(job_id)
    if document.is_mock or not os.getenv('REPORT_MODEL_ENDPOINT'):
        raise HTTPException(409, 'Compact report generation is not available.')
    if job_id in report_repairs:
        raise HTTPException(409, 'This report is already being formatted. Please wait.')
    report_repairs.add(job_id)
    try:
        edited = await edit_report(document)
        job = get_job(job_id)
        job.document = edited
        await asyncio.to_thread(save_job, job)
        return job
    except Exception:
        raise HTTPException(503, 'Compact formatting could not finish. Your original extraction is saved; please retry.')
    finally:
        report_repairs.discard(job_id)

@app.post('/api/recover-report')
def recover_report(document: MediaDocument):
    try:
        UUID(document.id)
    except ValueError:
        raise HTTPException(422, 'Invalid report identifier.')
    if document.id in jobs:
        return jobs[document.id]
    # Browser-held reports are recoverable display copies, not trusted search evidence.
    document.metadata['search_provider'] = 'not-indexed'
    document.metadata['report_notice'] = 'Recovered from your open browser. Search indexing has not been verified for this copy.'
    job = Job(id=document.id, source_type=document.source_type, source_name=document.source_name,
              status='complete', stage=4, document=document)
    save_job(job)
    jobs[job.id] = job
    return job

@app.get('/api/jobs/{job_id}/search')
def search(job_id: str, q: str = ''):
    if len(q) > 1000:
        raise HTTPException(422, 'Search must be 1000 characters or fewer.')
    document = get_document(job_id)
    if search_store and not document.is_mock:
        try:
            if document.metadata.get('search_provider') != 'azure-ai-search':
                # A recovered report remains explicitly browser-sourced, even when searchable.
                search_store.index_document(document)
                document.metadata['search_provider'] = 'azure-ai-search'
                save_job(get_job(job_id))
            return {'results':search_store.search(document,q),'mode':'azure-ai-search'}
        except Exception:
            raise HTTPException(503, 'Azure AI Search is unavailable. Please retry.')
    return {'results': retriever.search(document, q), 'mode': 'local-keyword'}

@app.post('/api/jobs/{job_id}/questions')
def ask(job_id: str, request: Question):
    if not request.question.strip():
        raise HTTPException(422, 'Enter a question.')
    document = get_document(job_id)
    if not document.is_mock:
        if not search_store or not (os.getenv('REPORT_MODEL_KEY') if key_mode() else os.getenv('FOUNDRY_AGENT_NAME')):
            raise HTTPException(409, 'Media chat is not configured on this server.')
        try:
            if document.metadata.get('search_provider') != 'azure-ai-search':
                search_store.index_document(document)
                document.metadata['search_provider'] = 'azure-ai-search'
                save_job(get_job(job_id))
            return answer_with_fallback(document, request, search_store, answer_question)
        except Exception:
            raise HTTPException(503, 'Media chat is temporarily unavailable. Please retry. Your report is saved.')
    return agent.answer(document, request.question)


