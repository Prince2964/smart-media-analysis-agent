"""Bounded public HTTPS video downloads. No cookies, login, playlists or DRM."""
import http.client
import ipaddress
import socket
import time
from urllib.parse import urlsplit, urljoin, parse_qs
import re
from pathlib import Path
import tempfile
from .media_guardrails import run_ffmpeg, MediaRejected

MAX_BYTES = 100 * 1024 * 1024


class LinkError(ValueError):
    pass


def validate_url(url):
    try:
        u = urlsplit(url)
        if u.scheme != 'https' or not u.hostname or u.username or u.password or u.port not in (None, 443):
            raise ValueError()
        if any(ord(c) < 32 for c in url):
            raise ValueError()
    except ValueError:
        raise LinkError('Use a public HTTPS video link, without a username or password.')
    return u


def public_addresses(host):
    addresses = list(dict.fromkeys(row[4][0] for row in socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)))
    if not addresses or any(not ipaddress.ip_address(ip).is_global for ip in addresses):
        raise LinkError('Local and private network links are not supported.')
    return addresses


def normalize_link(url):
    u = validate_url(url)
    if u.hostname in ('youtu.be', 'www.youtube.com', 'youtube.com', 'm.youtube.com'):
        video_id = u.path.strip('/') if u.hostname == 'youtu.be' else (
            parse_qs(u.query).get('v', [''])[0] if u.path == '/watch' else
            u.path.split('/')[-1] if u.path.startswith(('/shorts/', '/embed/')) else '')
        if not re.fullmatch(r'[A-Za-z0-9_-]{11}', video_id):
            raise LinkError('Paste a single YouTube video link, not a channel or playlist.')
        return f'https://www.youtube.com/watch?v={video_id}', True
    if not u.path.lower().endswith(('.mp4', '.mov', '.webm')):
        raise LinkError('This website page is not supported yet. Use a YouTube video, a direct MP4/MOV/WebM link, or upload the file.')
    return url, False


def download_public(url, audio=False):
    try:
        return _download_public(url, audio)
    except (TimeoutError, socket.timeout):
        raise LinkError('The video host stopped responding during download. Try a shorter video or upload the file directly.') from None
    except (OSError, http.client.HTTPException):
        raise LinkError('The connection to the video host was interrupted. Retry the link or upload the file directly.') from None


def _download_public(url, audio=False):
    deadline = time.monotonic() + 120
    for _ in range(5):
        u = validate_url(url)
        addresses = public_addresses(u.hostname)
        connection = http.client.HTTPSConnection(u.hostname, timeout=20)
        # Pin to a validated public address, retaining the hostname for TLS verification.
        connection._create_connection = lambda address, timeout, source_address=None: socket.create_connection(
            (addresses[0], 443), timeout, source_address)
        try:
            connection.request('GET', u.path + ('?' + u.query if u.query else ''),
                               headers={'User-Agent': 'Mozilla/5.0', 'Accept-Encoding': 'identity'})
            response = connection.getresponse()
            if response.status in (301, 302, 303, 307, 308):
                url = urljoin(url, response.getheader('Location', ''))
                continue
            if response.status != 200:
                raise LinkError('The website blocked or could not provide this video. Download it through an authorized method and upload the file.')
            if int(response.getheader('Content-Length', '0')) > MAX_BYTES:
                raise LinkError('The complete video exceeds the 100 MB limit. Upload a shorter clip instead.')
            data = bytearray()
            while True:
                if time.monotonic() > deadline:
                    raise LinkError('Video download timed out. Try a shorter video or upload the file.')
                reader = getattr(response, 'read1', response.read)
                chunk = reader(min(65536, MAX_BYTES + 1 - len(data)))
                if not chunk:
                    break
                data.extend(chunk)
                if len(data) > MAX_BYTES:
                    raise LinkError('The complete video exceeds the 100 MB limit. Upload a shorter clip instead.')
            if len(data) > 16 and data[4:8] == b'ftyp':
                return bytes(data), 'audio/mp4' if audio else 'video/mp4'
            if data[:4] == bytes.fromhex('1a45dfa3'):
                return bytes(data), 'video/webm'
            raise LinkError('The link did not return a supported video file. Upload an MP4, MOV or WebM file.')
        finally:
            connection.close()
    raise LinkError('Too many redirects. Use a direct video link.')


def media_host(url):
    host = validate_url(url).hostname
    if not (host == 'googlevideo.com' or host.endswith('.googlevideo.com')):
        raise LinkError('Unsupported YouTube media host.')


def merge_streams(video, audio):
    if len(video) + len(audio) > MAX_BYTES:
        raise LinkError('The complete video exceeds the 100 MB limit.')
    with tempfile.TemporaryDirectory(prefix='media-merge-') as folder:
        v, a, out = [Path(folder)/name for name in ('video.mp4','audio.m4a','merged.mp4')]
        v.write_bytes(video); a.write_bytes(audio)
        try:
            result = run_ffmpeg(['-v','error','-i',str(v),'-i',str(a),'-map','0:v:0',
                '-map','1:a:0','-c','copy','-movflags','+faststart','-fs',str(MAX_BYTES+1),str(out)], timeout=45)
        except MediaRejected:
            raise LinkError('Combining video and audio timed out. Upload the file instead.')
        if result.returncode or not out.exists() or out.stat().st_size > MAX_BYTES:
            raise LinkError('Could not combine this video within the upload limit. Upload a smaller MP4.')
        return out.read_bytes(), 'video/mp4'


def fetch_video(url):
    url, youtube = normalize_link(url)
    title = urlsplit(url).path.rsplit('/', 1)[-1]
    media_url = url
    if youtube:
        from yt_dlp import YoutubeDL
        class PublicYoutubeDL(YoutubeDL):
            def urlopen(self, request):
                target = request if isinstance(request, str) else request.url
                host = validate_url(target).hostname
                if not any(host == d or host.endswith('.' + d) for d in ('youtube.com', 'youtube-nocookie.com', 'googlevideo.com', 'ytimg.com', 'youtubei.googleapis.com')):
                    raise LinkError('Unsupported redirect from YouTube.')
                public_addresses(host)
                return super().urlopen(request)
        class QuietLogger:
            def debug(self, message): pass
            def warning(self, message): pass
            def error(self, message): pass
        try:
            with PublicYoutubeDL({'quiet': True, 'logger': QuietLogger(), 'noplaylist': True,
                                  'socket_timeout': 15, 'retries': 0, 'extractor_retries': 0,
                                  'skip_download': True, 'cachedir': False}) as downloader:
                info = downloader.extract_info(url, download=False)
        except Exception:
            raise LinkError('YouTube could not provide a public video download. Private, restricted or blocked videos require file upload.')
        if info.get('is_live') or info.get('has_drm') or info.get('_type') == 'playlist':
            raise LinkError('Live streams, playlists and protected videos are not supported.')
        formats = [f for f in info.get('formats', []) if f.get('protocol') == 'https'
                   and f.get('ext') in ('mp4', 'webm') and f.get('acodec') not in (None, 'none')
                   and f.get('vcodec') not in (None, 'none') and not f.get('has_drm')]
        candidates = [f for f in formats if (f.get('filesize') or f.get('filesize_approx') or 0) <= MAX_BYTES]
        if not candidates:
            usable = [f for f in info.get('formats', []) if f.get('protocol') == 'https' and not f.get('has_drm')]
            videos = [f for f in usable if f.get('ext') == 'mp4' and f.get('vcodec') not in (None,'none') and f.get('acodec') == 'none']
            audios = [f for f in usable if f.get('ext') in ('m4a','mp4') and f.get('acodec') not in (None,'none') and f.get('vcodec') == 'none']
            pairs = [(v,a) for v in videos for a in audios if
                (v.get('filesize') or v.get('filesize_approx') or 0) +
                (a.get('filesize') or a.get('filesize_approx') or 0) <= MAX_BYTES]
            if not pairs:
                raise LinkError('No supported public video/audio download fits the 100 MB limit. Upload a shorter clip instead.')
            v,a = min(pairs, key=lambda pair: (abs((pair[0].get('height') or 360)-360),pair[1].get('abr') or 0))
            media_host(v['url']); media_host(a['url'])
            video,_ = download_public(v['url'])
            audio,_ = download_public(a['url'], audio=True)
            data,mime = merge_streams(video,audio)
            return (info.get('title') or 'YouTube video')[:200],data,mime
        # Prefer a modest resolution for analysis instead of the largest available file.
        chosen = min(candidates, key=lambda f: abs((f.get('height') or 360) - 360))
        media_url = chosen['url']
        host = validate_url(media_url).hostname
        if not (host == 'googlevideo.com' or host.endswith('.googlevideo.com')):
            raise LinkError('Unsupported YouTube media host.')
        title = info.get('title') or 'YouTube video'
    data, content_type = download_public(media_url)
    return title[:200], data, content_type
