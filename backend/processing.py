"""Provider boundaries. Mock extraction never inspects or claims to describe user media."""
from typing import Protocol
from .models import MediaDocument, Segment, SourceType

DEMO_URL = 'https://example.com/demo/product-briefing'

class MediaProcessor(Protocol):
    def analyze(self, job_id: str, source_type: SourceType, source_name: str) -> MediaDocument: ...

class LinkAdapter(Protocol):
    def supports(self, url: str) -> bool: ...
    def resolve(self, url: str) -> str: ...

class DemoLinkAdapter:
    def supports(self, url: str) -> bool:
        return url == DEMO_URL

    def resolve(self, url: str) -> str:
        if not self.supports(url):
            raise ValueError('Unsupported link. Only the displayed local demo link is configured.')
        return 'Product briefing (local link fixture)'

LINK_ADAPTERS: list[LinkAdapter] = [DemoLinkAdapter()]

def resolve_link(url: str) -> str:
    # No network fetch, redirects, DNS lookup or arbitrary URL downloading in mock mode.
    for adapter in LINK_ADAPTERS:
        if adapter.supports(url):
            return adapter.resolve(url)
    raise ValueError('Unsupported link. Only the displayed local demo link is configured.')

class MockProcessor:
    def analyze(self, job_id: str, source_type: SourceType, source_name: str) -> MediaDocument:
        image = source_type == 'image'
        if image:
            segments = [
                Segment(id='region-1', label='API Gateway', region='Region 01', text='API Gateway / Webhook Ingress (Port 443 HTTPS).'),
                Segment(id='region-2', label='Worker queue', region='Region 02', text='Event Stream Broker → Decoupled Worker Queue.'),
                Segment(id='region-3', label='Context store', region='Region 03', text='Retrieval Context Store & Verification Gateway.'),
            ]
            summary = 'The sample diagram shows an API Gateway / Webhook Ingress on HTTPS port 443, an event stream and worker queue, and a retrieval context store.'
        else:
            segments = [
                Segment(id='segment-1', label='Overview', start=15, end=45, text='Welcome to our product briefing. The workspace brings project notes and team tasks together.'),
                Segment(id='segment-2', label='Pricing & plans', start=92, end=115, text="Let's look at pricing and plans. The standard team tier is twenty-four dollars per member per month."),
                Segment(id='segment-3', label='Rollout schedule', start=140, end=175, text='The rollout begins with a pilot in October, followed by a wider release in November.'),
            ]
            summary = 'This sample product briefing introduces a shared workspace, explains the standard team plan, and describes the rollout schedule.'
        return MediaDocument(id=job_id, source_type=source_type, source_name=source_name,
            sample_name='architecture-whiteboard.png' if image else 'Product briefing video',
            summary=summary, topics=[s.label for s in segments], extracted_text='\n'.join(s.text for s in segments),
            segments=segments, chunks=segments,
            visual_information=[s.text for s in segments] if image else [],
            metadata={'duration_seconds': None if image else 180, 'provider': 'local-fixture',
                      'notice': 'Prepared sample content, not analysis of your uploaded file or URL.'})
