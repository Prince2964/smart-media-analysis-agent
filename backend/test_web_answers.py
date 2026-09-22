from types import SimpleNamespace
from .models import Question
from . import web_answers as web
from contextlib import nullcontext


def test_db_definition_does_not_require_product_or_network():
    query = web.normalize_definition('what is db', [])
    assert 'decibel' in query


def test_yes_recovers_definition_after_bad_clarification():
    query = web.normalize_definition('yes', [
        {'question': 'what is db', 'answer': 'Which product do you mean?'}])
    assert 'decibel' in query


def response(url='https://example.com/specs', searched=True):
    return {'status': 'completed', 'output': ([{'type': 'web_search_call', 'status': 'completed'}] if searched else []) + [
        {'type': 'message', 'content': [{'type': 'output_text', 'text': 'Cited answer',
         'annotations': [{'type': 'url_citation', 'url': url, 'title': 'Specifications'}]}]}]}


def test_web_requires_actual_search_and_safe_sources():
    assert web.parse_web_response(response())['web_sources'][0]['url'] == 'https://example.com/specs'
    assert web.parse_web_response(response(searched=False))['web_sources'] == []
    assert web.parse_web_response(response('javascript:alert(1)'))['web_sources'] == []


def test_web_opt_in_and_media_priority(monkeypatch):
    monkeypatch.setattr(web, 'resolve_question', lambda *args: ('resolved question', ''))
    calls=[]
    monkeypatch.setattr(web, 'search_web', lambda q: calls.append(q) or {'web_answer':'Web only','web_sources':[]})
    store=SimpleNamespace(search=lambda doc,q: [])
    missing=lambda *args: {'answer':'No media evidence','answer_kind':'insufficient_evidence'}
    supported=lambda *args: {'answer':'Media evidence','answer_kind':'grounded_answer'}
    assert 'web_answer' not in web.answer_with_fallback(None,Question(question='Q'),store,missing)
    assert 'web_answer' not in web.answer_with_fallback(None,Question(question='Q',allow_web=True),store,supported)
    result=web.answer_with_fallback(None,Question(question='Q',allow_web=True),store,missing)
    assert calls == ['resolved question']
    assert result['answer'] == 'No media evidence'
    assert result['web_answer'] == 'Web only'


def test_ambiguous_question_never_searches(monkeypatch):
    monkeypatch.setattr(web,'resolve_question',lambda *args: ('','Which product and measurement?'))
    result=web.answer_with_fallback(None,Question(question='its db',allow_web=True),None,None)
    assert result['answer_kind'] == 'clarification'


def test_web_failure_preserves_media_answer(monkeypatch):
    monkeypatch.setattr(web,'resolve_question',lambda *args: ('resolved',''))
    def fail(q): raise RuntimeError('Unavailable')
    monkeypatch.setattr(web,'search_web',fail)
    result=web.answer_with_fallback(None,Question(question='Q',allow_web=True),SimpleNamespace(search=lambda *args:[]),
        lambda *args:{'answer':'No evidence','answer_kind':'insufficient_evidence'})
    assert result['answer']=='No evidence'
    assert 'web_error' in result


def test_unrelated_question_never_retrieves_or_searches(monkeypatch):
    monkeypatch.setattr(web, 'resolve_question', lambda *args: (None, 'Not related to your media.'))
    result=web.answer_with_fallback(None,Question(question='Write unrelated code',allow_web=True),None,None)
    assert result['answer_kind']=='out_of_scope'
    assert result['citations']==[]
    assert 'web_answer' not in result


def test_acronym_uses_original_passage_even_when_overview_omits_topic():
    document = SimpleNamespace(summary='Smartphone and chipset announcements',
        segments=[SimpleNamespace(id='upi', text='Payment updates'),
                  SimpleNamespace(id='phone', text='New smartphone')],
        metadata={'original_passages': [{'id': 'upi', 'text': 'MDR means merchant discount rate for UPI.'}]})
    assert web.matching_evidence('what is mdr', document) == ['MDR means merchant discount rate for UPI.']


def test_exact_user_term_precedes_broad_rewrite_and_deduplicates(monkeypatch):
    monkeypatch.setattr(web, 'resolve_question', lambda *args: ('What is MDR in this news roundup?', ''))
    match = SimpleNamespace(id='upi', text='MDR means merchant discount rate')
    other = SimpleNamespace(id='phone', text='Smartphone news')
    searches = []
    def search(doc, query):
        searches.append(query)
        return [match] if query == 'mdr' else [other, match]
    def answer(query, context):
        assert context == [match, other]
        return {'answer': 'Merchant discount rate', 'answer_kind': 'grounded_answer'}
    web.answer_with_fallback(None, Question(question='what is mdr'), SimpleNamespace(search=search), answer)
    assert searches[0] == 'mdr'


def test_price_followup_retrieves_resolved_product_before_other_prices(monkeypatch):
    resolved = 'What is the price of Xiaomi 18 Pro?'
    monkeypatch.setattr(web, 'resolve_question', lambda *args: (resolved, ''))
    calls = []
    store = SimpleNamespace(search=lambda doc, q: calls.append(q) or [])
    web.answer_with_fallback(None, Question(question='what is its price'), store,
        lambda *args: {'answer': 'Unavailable', 'answer_kind': 'insufficient_evidence'})
    assert calls == [resolved]


def test_followup_context_includes_product_from_previous_answer():
    document = SimpleNamespace(metadata={}, segments=[
        SimpleNamespace(id='one', text='Xiaomi 18 Pro launch discussion'),
        SimpleNamespace(id='two', text='Unrelated sale prices')])
    evidence = web.evidence_for_conversation('its price?', [
        {'question': 'Which phone launches?', 'answer': 'Xiaomi 18 Pro'}], document)
    assert 'Xiaomi 18 Pro launch discussion' in evidence


def test_web_uses_saved_agent_tool_not_request_scoped_tool(monkeypatch):
    monkeypatch.setenv('FOUNDRY_PROJECT_ENDPOINT', 'https://example.com/project')
    monkeypatch.setenv('FOUNDRY_AGENT_NAME', 'media-agent')
    monkeypatch.setenv('FOUNDRY_WEB_AGENT_VERSION', '3')
    monkeypatch.setattr(web, 'get_credential', lambda: nullcontext(
        SimpleNamespace(get_token=lambda scope: SimpleNamespace(token='test-token'))))
    def post(url, **kwargs):
        body = kwargs['json']
        assert body['agent_reference'] == {'type': 'agent_reference', 'name': 'media-agent', 'version': '3'}
        assert body['tool_choice'] == 'required'
        assert body['input'] == 'Product price?'
        assert 'tools' not in body and 'model' not in body
        return SimpleNamespace(raise_for_status=lambda: None, json=lambda: response())
    monkeypatch.setattr(web.httpx, 'post', post)
    assert web.search_web('Product price?')['web_sources']
