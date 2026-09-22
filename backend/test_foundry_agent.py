from .foundry_agent import format_answer, answer_question
from .models import Segment
from .retrieval import FALLBACK
from . import foundry_agent
from types import SimpleNamespace


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


def test_key_answer_uses_direct_model_and_validates_citations(monkeypatch):
    monkeypatch.setenv('AZURE_AUTH_MODE', 'api-key')
    monkeypatch.setenv('REPORT_MODEL_KEY', 'test-key')
    monkeypatch.setenv('REPORT_MODEL_ENDPOINT', 'https://example.openai.azure.com')
    monkeypatch.setenv('REPORT_MODEL_DEPLOYMENT', 'test-model')
    def post(url, **kwargs):
        assert url.endswith('/openai/v1/chat/completions')
        assert kwargs['headers'] == {'api-key': 'test-key'}
        assert 'agent_reference' not in kwargs['json']
        return SimpleNamespace(raise_for_status=lambda: None, json=lambda: {'choices': [
            {'finish_reason': 'stop', 'message': {'content': '{"supported":true,"answer":"Blue train","citation_ids":["p1"]}'}}]})
    monkeypatch.setattr(foundry_agent.httpx, 'post', post)
    result = answer_question('What?', [Segment(id='s', text='Blue train', label='Scene', start=12)])
    assert result['provider'] == 'azure-openai'
    assert result['citations'][0]['start'] == 12
