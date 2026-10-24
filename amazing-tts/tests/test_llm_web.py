import json
import httpx
import pytest
from fastapi.testclient import TestClient
from amazing_tts.llm import Gemini
from amazing_tts import web


def test_truncated_llm_response_rejected(monkeypatch, library):
    monkeypatch.setenv('GEMINI_API_KEY','fake')
    calls=[]
    client=httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(200,json={'candidates':[{'finishReason':'MAX_TOKENS','content':{'parts':[{'text':'{}'}]}}]})))
    llm=Gemini(library,'test',reserve=lambda tokens:calls.append(tokens),client=client)
    with pytest.raises(ValueError,match='truncated'): llm.adapt('Source',{},'')
    assert len(calls)==1


def test_provider_quota_does_not_retry(monkeypatch, library):
    monkeypatch.setenv('GEMINI_API_KEY','fake')
    calls=[]
    client=httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(429)))
    llm=Gemini(library,'test',reserve=lambda tokens:calls.append(tokens),client=client)
    with pytest.raises(RuntimeError,match='quota'): llm.adapt('Source',{},'')
    assert len(calls)==1


def test_valid_response_and_secret_in_header_only(monkeypatch, library, script):
    monkeypatch.setenv('GEMINI_API_KEY','secret-marker')
    def handle(request):
        assert 'secret-marker' not in str(request.url)
        assert request.headers['x-goog-api-key']=='secret-marker'
        assert json.loads(request.content)['generationConfig']['responseMimeType']=='application/json'
        return httpx.Response(200,json={'candidates':[{'finishReason':'STOP','content':{'parts':[{'text':script.model_dump_json()}]}}]})
    llm=Gemini(library,'test',reserve=lambda tokens:None,client=httpx.Client(transport=httpx.MockTransport(handle)))
    assert llm.adapt('Source',{},'')==script


def test_cached_website_request_does_not_start_generation(monkeypatch, tmp_path):
    monkeypatch.setattr(web,'ROOT',tmp_path)
    monkeypatch.setattr(web,'CLOUD',False)
    monkeypatch.setattr(web,'WORKER',False)
    b=web.library().book('https://novelping.com/book/test-novel')
    b.write('book.json',{'url':b.url,'title':'Test'})
    b.write('job.json',{'state':'complete','ready':2,'target':2})
    monkeypatch.setattr(web.executor,'submit',lambda *a,**k:pytest.fail('cached playback launched generation'))
    with TestClient(web.app) as client:
        assert client.get('/').status_code==200
        assert client.get('/api/books').json()[0]['title']=='Test'
        assert client.post('/api/books',json={'url':b.url,'chapters':1}).json()['ready']==2
        assert client.post('/internal/chapter',json={'book_id':'a'*32,'chapter':1,'run_id':'b'*32}).status_code==404
        assert client.get('/api/books/'+b.path.name+'/audio/1').status_code==404


def test_cloud_generation_requires_auth(monkeypatch):
    monkeypatch.setattr(web,'CLOUD',True)
    monkeypatch.setattr(web,'WORKER',False)
    from firebase_admin import auth
    monkeypatch.setattr(auth,'verify_id_token',lambda *a,**k: (_ for _ in ()).throw(ValueError('invalid token')))
    with TestClient(web.app) as client:
        assert client.post('/api/books',json={'url':'https://novelping.com/book/test-novel'}).status_code==401
