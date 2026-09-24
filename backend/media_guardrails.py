"""File validation and Azure moderation. Sampled frames are not exhaustive screening."""
import base64
import io
import math
import os
from pathlib import Path
import re
import subprocess
import tempfile

import httpx
from PIL import Image
from imageio_ffmpeg import get_ffmpeg_exe
from .auth import service_headers


class MediaRejected(ValueError):
    pass


def enabled():
    return os.getenv('MEDIA_GUARDRAILS', 'off').lower() == 'azure'


def run_ffmpeg(args, timeout=90):
    try:
        return subprocess.run([get_ffmpeg_exe(), '-nostdin', '-hide_banner',
            '-protocol_whitelist', 'file,pipe'] + args, capture_output=True,
            timeout=timeout, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    except subprocess.TimeoutExpired:
        raise MediaRejected('Video validation timed out. Try a shorter clip.')


def jpeg(data):
    try:
        with Image.open(io.BytesIO(data)) as im:
            if im.format not in ('PNG', 'JPEG', 'WEBP') or im.width * im.height > 25_000_000:
                raise MediaRejected('Use a valid PNG, JPEG or WebP image under 25 megapixels.')
            im.load()
            im.thumbnail((1024, 1024))
            out = io.BytesIO()
            im.convert('RGB').save(out, format='JPEG', quality=80)
            return out.getvalue()
    except (OSError, ValueError, Image.DecompressionBombError):
        raise MediaRejected('The image cannot be decoded safely.')


def video_frames(data):
    with tempfile.TemporaryDirectory(prefix='media-check-') as folder:
        source = Path(folder) / 'input.video'
        source.write_bytes(data)
        probe = run_ffmpeg(['-i', str(source)], timeout=20)
        info = probe.stderr.decode('utf-8', errors='replace')
        duration = re.search(r'Duration: (\d+):(\d+):(\d+(?:\.\d+)?)', info)
        if not duration or 'Video:' not in info:
            raise MediaRejected('The file is not a readable video. Export it as MP4 and try again.')
        seconds = int(duration[1])*3600 + int(duration[2])*60 + float(duration[3])
        if not math.isfinite(seconds) or seconds <= 0 or seconds > 1200:
            raise MediaRejected('Use a video between 0 and 20 minutes long.')
        result = run_ffmpeg(['-v', 'error', '-xerror', '-i', str(source), '-an',
            '-vf', "fps=1/10:start_time=0,scale=640:640:force_original_aspect_ratio=decrease,format=yuvj420p",
            '-frames:v', '121', str(Path(folder)/'frame-%03d.jpg')])
        frames = sorted(Path(folder).glob('frame-*.jpg'))
        if result.returncode:
            raise MediaRejected('The video contains unreadable frames. Export it as MP4 and try again.')
        if not frames:  # Very short clips may have no frame at the sampling interval.
            result = run_ffmpeg(['-v','error','-i',str(source),'-frames:v','1',
                '-vf','scale=640:640:force_original_aspect_ratio=decrease,format=yuvj420p', str(Path(folder)/'frame-000.jpg')])
            frames = sorted(Path(folder).glob('frame-*.jpg'))
        if result.returncode or not frames:
            raise MediaRejected('No readable video frames were found.')
        return [p.read_bytes() for p in frames]


def check_scores(result):
    rows = result.get('categoriesAnalysis')
    expected = {'Hate', 'Sexual', 'SelfHarm', 'Violence'}
    if not isinstance(rows, list) or {r.get('category') for r in rows} != expected:
        raise MediaRejected('Safety screening returned an incomplete result. Please retry.')
    for row in rows:
        score = row.get('severity')
        if type(score) is not int or score not in (0, 2, 4, 6):
            raise MediaRejected('Safety screening returned an invalid result. Please retry.')
        if score >= 4:
            raise MediaRejected('Content blocked by safety screening: ' + row['category'] + '. Choose different media.')


def moderate(kind, payload):
    endpoint = (os.getenv('CONTENT_SAFETY_ENDPOINT') or os.getenv('CONTENT_UNDERSTANDING_ENDPOINT', '')).rstrip('/')
    key_name = 'CONTENT_SAFETY_KEY' if os.getenv('CONTENT_SAFETY_KEY') else 'CONTENT_UNDERSTANDING_KEY'
    try:
        headers = service_headers(key_name, 'https://cognitiveservices.azure.com/.default', key_header='Ocp-Apim-Subscription-Key')
        response = httpx.post(endpoint + f'/contentsafety/{kind}:analyze',
            params={'api-version':'2024-09-01'}, headers=headers,
            json={**payload, 'outputType':'FourSeverityLevels'}, timeout=30)
        response.raise_for_status()
        check_scores(response.json())
    except (httpx.HTTPError, KeyError, TypeError) as exc:
        raise MediaRejected('Safety screening is unavailable. Processing stopped; please retry later.') from exc


def screen_media(data, kind):
    if not enabled():
        return
    if not data or len(data) > 100 * 1024 * 1024:
        raise MediaRejected('Media must be nonempty and no larger than 100 MB.')
    frames = [jpeg(data)] if kind == 'image' else video_frames(data)
    for frame in frames:
        moderate('image', {'image': {'content':base64.b64encode(frame).decode('ascii')}})


def screen_text(text):
    if enabled():
        for offset in range(0, len(text), 9000):
            moderate('text', {'text':text[offset:offset+10000]})
