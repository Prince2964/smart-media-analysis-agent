from .foundry_agent import format_answer, answer_question
from .models import Segment
from .retrieval import FALLBACK


def test_no_evidence_needs_no_credentials():
    assert answer_question('What is the price?', [])['answer'] == FALLBACK


def test_unknown_citation_is_rejected():
    passage = Segment(id='real', text='Evidence', label='Scene', start=12)
    result = format_answer({'supported': True, 'answer': 'Made up', 'citation_ids': ['p99']}, [passage])
    assert result['answer'] == FALLBACK
    assert result['citations'] == []


def test_citation_uses_server_timestamp():
    passage = Segment(id='real', text='Evidence', label='Scene', start=12)
    result = format_answer({'supported': True, 'answer': 'Answer', 'citation_ids': ['p1', 'p1']}, [passage])
    assert len(result['citations']) == 1
    assert result['citations'][0]['start'] == 12
