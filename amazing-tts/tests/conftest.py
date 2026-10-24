import pytest
from amazing_tts.storage import Library
from amazing_tts.models import Script

URL = 'https://novelping.com/book/test-novel'

@pytest.fixture
def library(tmp_path):
    return Library(tmp_path)

@pytest.fixture
def book(library):
    return library.book(URL)

@pytest.fixture
def source():
    return {'number': 1, 'title': 'Chapter 1', 'url': URL+'/chapter-1-test', 'text': 'Mira stepped forward. “Hello, friend!”', 'next_url': URL+'/chapter-2-test'}

@pytest.fixture
def script(source):
    return Script.model_validate({
        'characters': [{'id': 'mira', 'name': 'Mira', 'gender': 'female', 'age': 'young', 'traits': ['bright'], 'evidence': 'The young woman is named Mira.'}],
        'segments': [{'source': 'Mira stepped forward. ', 'text': 'Mira stepped forward.', 'speaker': 'narrator', 'kind': 'narration', 'confidence': 1},
                     {'source': '“Hello, friend!”', 'text': 'Hello, friend!', 'speaker': 'mira', 'kind': 'dialogue', 'confidence': .99}],
        'summary': 'Mira greets her friend.', 'notes': []})
