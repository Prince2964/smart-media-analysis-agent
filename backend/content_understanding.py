"""Real image extraction; never substitutes fixture content on failure."""
import asyncio
import os
import re
from urllib.parse import urlsplit
import httpx
from .auth import get_credential, key_mode, required_key, service_headers
from .models import MediaDocument, Segment


class AnalysisFailure(RuntimeError):
    """Safe service failure detail suitable for the report status."""


def failure_detail(body):
    error = body.get('error') or {}
    code = error.get('code', '') if isinstance(error, dict) else ''
    # Never expose raw service messages, which may contain URLs or media text.
    suffix = f' (code: {code})' if isinstance(code, str) and re.fullmatch(r'[A-Za-z0-9_.-]{1,80}', code) else ''
    return 'Azure Content Understanding could not analyze this media' + suffix + '. Try a shorter clip or a different video encoding.'


async def analyze_image(job_id: str, name: str, data: bytes, content_type: str):
    return await analyze_media(job_id, name, data, content_type, 'image')


async def analyze_media(job_id: str, name: str, data: bytes, content_type: str, kind: str):
    analyzer = 'prebuilt-videoSearch' if kind == 'video' else 'prebuilt-imageSearch'
    endpoint = os.environ['CONTENT_UNDERSTANDING_ENDPOINT'].rstrip('/')
    host = urlsplit(endpoint)
    if host.scheme != 'https' or not host.hostname or not host.hostname.endswith('.services.ai.azure.com') or host.query or host.path:
        raise ValueError('Invalid Content Understanding endpoint')
    headers = await asyncio.to_thread(service_headers, 'CONTENT_UNDERSTANDING_KEY', 'https://cognitiveservices.azure.com/.default', get_credential, 'Ocp-Apim-Subscription-Key')
    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(endpoint + f'/contentunderstanding/analyzers/{analyzer}:analyzeBinary?api-version=2025-11-01',
                                     headers={**headers, 'Content-Type': content_type}, content=data)
        response.raise_for_status()
        operation = response.headers['operation-location']
        if urlsplit(operation).netloc != host.netloc or urlsplit(operation).scheme != 'https':
            raise ValueError('Unexpected analysis operation endpoint')
        for _ in range(200):
            await asyncio.sleep(3)
            result = await client.get(operation, headers=headers)
            result.raise_for_status()
            body = result.json()
            status = body.get('status', '').lower()
            if status == 'succeeded':
                return normalize_video(job_id, name, body) if kind == 'video' else normalize_image(job_id, name, body)
            if status in ('failed', 'canceled'):
                raise AnalysisFailure(failure_detail(body))
        raise AnalysisFailure('Azure Content Understanding is still processing after the polling limit. The report was not completed locally; try a shorter clip. The Azure operation may still be running.')


def normalize_image(job_id: str, name: str, body: dict):
    summaries = [item.get('fields', {}).get('Summary', {}).get('valueString', '')
                 for item in body.get('result', {}).get('contents', [])]
    summary = '\n\n'.join(s for s in summaries if s.strip())
    if not summary:
        raise ValueError('The analyzer returned no image description')
    # This analyzer returns a generated description, not guaranteed verbatim OCR.
    segments = [Segment(id=f'image-description-{i+1}', label=f'Image description {i+1}',
                        region='Whole image', text=text) for i, text in enumerate(summaries) if text.strip()]
    return MediaDocument(id=job_id, source_type='image', source_name=name, sample_name=name,
        summary=summary, topics=[], extracted_text=summary, segments=segments, chunks=segments,
        visual_information=[summary], is_mock=False,
        metadata={'duration_seconds': None, 'provider': 'azure-content-understanding',
                  'analyzer': 'prebuilt-imageSearch', 'notice': 'AI-generated description of your image. Verify important details against the original; this is not verbatim OCR.'})


def normalize_video(job_id: str, name: str, body: dict):
    segments = []
    summaries = []
    duration = 0
    for index, item in enumerate(body.get('result', {}).get('contents', [])):
        start = item.get('startTimeMs')
        end = item.get('endTimeMs')
        duration = max(duration, (end or 0) / 1000)
        summary = item.get('fields', {}).get('Summary', {}).get('valueString', '')
        if summary:
            summaries.append(summary)
        text = '\n\n'.join(part for part in (summary, item.get('markdown', '')) if part)
        if text.strip():
            segments.append(Segment(id=f'video-segment-{index+1}', label=f'Segment {index+1}',
                text=text, start=start / 1000 if start is not None else None,
                end=end / 1000 if end is not None else None))
    if not segments:
        raise ValueError('No video content returned')
    return MediaDocument(id=job_id, source_type='video', source_name=name, sample_name=name,
        summary='\n\n'.join(summaries) or 'No separate summary returned. Read the extracted segments below.',
        topics=[], extracted_text='\n\n'.join(s.text for s in segments), segments=segments, chunks=segments,
        is_mock=False, metadata={'duration_seconds': duration or None, 'provider':'azure-content-understanding',
        'analyzer':'prebuilt-videoSearch', 'notice':'Azure-generated scene descriptions and extracted transcript where available. Verify important details against the original video.'})

