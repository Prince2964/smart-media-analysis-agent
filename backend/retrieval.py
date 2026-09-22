"""Local keyword retrieval and conservative fixture Q&A; no LLM or Foundry claim."""
import re
from typing import Protocol
from .models import MediaDocument, Segment

FALLBACK = "I can't determine that from the provided media."
STOP = {'the','a','an','is','are','was','were','did','do','does','they','it','this','that','what','when','where','how','about','in','of','to','and','for','from','with','at','media','please'}

def tokens(text: str) -> set[str]:
    words = set(re.findall(r'[a-z0-9]+', text.lower())) - STOP
    if 'entry' in words:
        words.add('gateway')
    if 'price' in words:
        words.add('pricing')
    return words

class Retriever(Protocol):
    def search(self, document: MediaDocument, query: str) -> list[Segment]: ...

class LocalRetriever:
    def search(self, document: MediaDocument, query: str) -> list[Segment]:
        words = tokens(query)
        ranked = [(len(words & tokens(s.text + ' ' + s.label)), s) for s in document.chunks]
        return [s for score, s in sorted(ranked, key=lambda item: -item[0]) if score > 0][:3]

class GroundedAgent(Protocol):
    def answer(self, document: MediaDocument, question: str) -> dict: ...

class FixtureAgent:
    def __init__(self, retriever: Retriever):
        self.retriever = retriever

    def answer(self, document: MediaDocument, question: str) -> dict:
        context = self.retriever.search(document, question)
        normalized = re.sub(r'[^a-z0-9 ]', '', question.lower()).strip()
        # Exact supported intents prevent plausible but unrelated fixture answers.
        allowed = {
            'when did they discuss pricing': ('segment-2', 'The pricing discussion starts at approximately 01:32.'),
            'what is the standard team price': ('segment-2', 'The standard team tier is twenty-four dollars per member per month.'),
            'when does the rollout begin': ('segment-3', 'The rollout begins with a pilot in October.'),
            'what is the entry point': ('region-1', 'The entry point is the API Gateway / Webhook Ingress on HTTPS port 443.'),
            'what port is shown': ('region-1', 'The sample diagram shows port 443 HTTPS.'),
            'what follows the event stream broker': ('region-2', 'The diagram shows a Decoupled Worker Queue after the Event Stream Broker.'),
        }
        intent = allowed.get(normalized)
        citation = next((s for s in context if intent and s.id == intent[0]), None)
        return {'answer': intent[1] if citation else FALLBACK,
                'citations': [citation.model_dump()] if citation else [],
                'retrieved_context': [s.model_dump() for s in context],
                'answer_kind': 'prepared_sample_answer' if citation else 'insufficient_evidence',
                'is_mock': True, 'provider': 'local-fixture',
                'notice': 'Deterministic sample Q&A; no generative model or Azure agent is connected.'}
