from pathlib import Path
import json
import pytest
from fastapi.testclient import TestClient
from amazing_tts.agent_plan import compile_plan, spoken
from amazing_tts.models import compact
from amazing_tts.scraper import parse_archive, import_archive, Scraper
from amazing_tts import web
from amazing_tts.preview import build


def plan():
    return {'characters':[{'id':'mira','name':'Mira','gender':'female','evidence':'She is named Mira.'}],
            'assignments':[{'start':1,'end':1,'speaker':'mira','kind':'dialogue','confidence':.99}],
            'replacements':[], 'summary':'Mira greets someone.', 'notes':[]}


def test_agent_plan_keeps_every_source_span_and_uses_cast():
    source='Mira entered.\n\n“Hello!”\n\nThe door closed.\n\nSilence followed.'
    script=compile_plan(source,plan())
    assert compact(''.join(s.source for s in script.segments))==compact(source)
    assert script.segments[1].speaker=='mira' and script.segments[1].text=='Hello!'
    assert len(script.segments)==3  # Adjacent narration fragments are joined.


@pytest.mark.parametrize('assignment',[{'start':-1,'end':1},{'start':0,'end':99},{'start':2,'end':1}])
def test_bad_agent_ranges_fail(assignment):
    p=plan();p['assignments']=[{**p['assignments'][0],**assignment}]
    with pytest.raises(ValueError,match='outside'):compile_plan('One.\n\nTwo.',p)


def test_overlapping_agent_ranges_fail():
    p=plan();p['assignments'].append(p['assignments'][0])
    with pytest.raises(ValueError,match='Overlapping'):compile_plan('One.\n\nTwo.',p)


def test_display_notation_becomes_spoken_content():
    assert spoken('[Family Fortune: 100 (Declining)]')=='Family Fortune: 100 (Declining)'
    assert spoken('First Realm → Second Realm')=='First Realm , then  Second Realm'
    assert spoken('"Open it!!"')=='Open it!'


def test_complete_archive_includes_template_titles():
    base='https://novelping.com/book/test-novel'
    html=f'<template><a href="{base}/chapter-2-y" title="Chapter 2: Next">Next</a><a href="{base}/chapter-1-x" title="Chapter 1: Start">Start</a></template>'
    result=parse_archive(html,base)
    assert [c['number'] for c in result]==[1,2]
    assert result[0]['title']=='Chapter 1: Start'


def test_archive_gaps_are_not_labeled_complete():
    base='https://novelping.com/book/test-novel'
    with pytest.raises(ValueError,match='gaps'):parse_archive(f'<a href="{base}/chapter-3-x">3</a>',base)


def test_static_snapshot_contains_sources_but_never_runs_models(library,book,source,tmp_path):
    book.write('book.json',{'url':book.url,'title':'Test','catalog_count':2})
    book.write('catalog.json',[{'number':1,'title':'One','url':source['url']},{'number':2,'title':'Two','url':source['next_url']}])
    book.write('chapters/000001/source.json',source)
    target=tmp_path/'snapshot';result=build(target,library.root)
    assert result['indexed']==2 and result['audio']==0
    assert 'window.AMAZING_TTS_SNAPSHOT=true' in (target/'index.html').read_text()
    detail=json.loads((target/'data'/book.path.name/'book.json').read_text())
    assert detail['cached_text']==[1] and len(detail['catalog'])==2
    assert (target/'assets/app.js').exists()
    assert not (target/'data'/book.path.name/'text/2.json').exists()


def test_preview_source_and_assets_work_without_generation(monkeypatch,tmp_path,source):
    monkeypatch.setattr(web,'ROOT',tmp_path)
    monkeypatch.setattr(web,'CLOUD',False)
    monkeypatch.setattr(web,'WORKER',False)
    monkeypatch.setattr(web,'PREVIEW',True)
    b=web.library().book('https://novelping.com/book/test-novel')
    b.write('book.json',{'url':b.url,'title':'Test','links':{'1':source['url']}})
    b.write('chapters/000001/source.json',source)
    monkeypatch.setattr(web.executor,'submit',lambda *a,**k:pytest.fail('preview launched generation'))
    with TestClient(web.app) as client:
        assert client.get('/assets/app.js').status_code==200
        assert client.get('/api/config').json()['preview']
        assert client.get('/api/books/'+b.path.name+'/text/1').json()['text']==source['text']
        assert client.get('/api/books/'+b.path.name+'/text/999').status_code==404
        assert client.post('/api/books',json={'url':b.url}).status_code==409
        assert client.post('/api/books/'+b.path.name+'/review',json={'script':{}}).status_code==409
