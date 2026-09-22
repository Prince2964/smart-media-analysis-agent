from typing import Literal
from pydantic import BaseModel, Field

SourceType = Literal['video', 'image', 'link']

class Segment(BaseModel):
    id: str
    text: str
    label: str
    start: float | None = None
    end: float | None = None
    region: str | None = None

class MediaDocument(BaseModel):
    id: str
    source_type: SourceType
    source_name: str
    sample_name: str
    summary: str
    topics: list[str]
    extracted_text: str
    segments: list[Segment]
    visual_information: list[str] = []
    metadata: dict = Field(default_factory=dict)
    chunks: list[Segment]
    is_mock: bool = True

class Job(BaseModel):
    id: str
    source_type: SourceType
    source_name: str
    status: Literal['queued', 'processing', 'complete', 'failed'] = 'queued'
    stage: int = 0
    error: str | None = None
    document: MediaDocument | None = None
    storage_blob: str | None = None
    phase: str = 'Queued'
    timings: dict[str, float] = Field(default_factory=dict)

class ChatTurn(BaseModel):
    question: str = Field(max_length=1000)
    answer: str = Field(max_length=2000)

class Question(BaseModel):
    question: str = Field(min_length=1, max_length=1000)
    history: list[ChatTurn] = Field(default_factory=list, max_length=4)
    allow_web: bool = False

class DemoRequest(BaseModel):
    source_type: SourceType = 'video'
    simulate_failure: bool = False

class LinkRequest(BaseModel):
    url: str = Field(min_length=1, max_length=2048)
