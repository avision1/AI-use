from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import json
import sqlite3
import wave
import pytest
from filelock import Timeout
from amazing_tts.audio import Renderer, valid_wav, split_text
from amazing_tts.models import validate_script, Script, Character
from amazing_tts.pipeline import prepare, process, accept_script
from amazing_tts.voices import initial_cast, merge_cast, cast, signature, validate_voice


class LLM:
    model = 'test-model'
    def __init__(self, script): self.script, self.calls = script, 0
    def adapt(self, *args): self.calls += 1; return self.script


class Speech:
    version = 'test-pcm-v1'
    def __init__(self, fail_at=0): self.calls, self.fail_at = 0, fail_at
    def synthesize(self, text, voice, path):
        self.calls += 1
        if self.fail_at == self.calls: raise RuntimeError('interrupted')
        with wave.open(str(path), 'wb') as f:
            f.setparams((1, 2, 24000, 0, 'NONE', 'not compressed'))
            f.writeframes(b'\x01\x00' * 2400)


def test_unchanged_run_calls_neither_provider_twice(library, book, source, script):
    llm, speech = LLM(script), Speech()
    first = process(book, source, llm, Renderer(library, speech))
    second = process(book, source, llm, Renderer(library, speech))
    assert first['audio'] == second['audio']
    assert llm.calls == 1 and speech.calls == 2
    assert valid_wav(__import__('pathlib').Path(first['audio']))


def test_resume_uses_completed_chunks(library, book, source, script):
    prepare(book, source, LLM(script))
    speech = Speech(fail_at=2)
    with pytest.raises(RuntimeError): Renderer(library, speech).render(book, 1, script, book.read('cast.json'))
    assert len(list((library.root/'audio-cache').glob('*.wav'))) == 1
    speech2 = Speech()
    Renderer(library, speech2).render(book, 1, script, book.read('cast.json'))
    assert speech2.calls == 1


def test_one_edit_regenerates_one_chunk(library, book, source, script):
    speech = Speech()
    process(book, source, LLM(script), Renderer(library, speech))
    script.segments[1].text = 'Hello, my friend!'
    Renderer(library, speech).render(book, 1, script, book.read('cast.json'))
    assert speech.calls == 3


def test_changed_voice_invalidates_only_affected_speech(library, book, source, script):
    speech = Speech()
    process(book, source, LLM(script), Renderer(library, speech))
    cast = book.read('cast.json')
    cast['mira']['voice']['speed'] = .95
    Renderer(library, speech).render(book, 1, script, cast)
    assert speech.calls == 3


def test_pronunciation_invalidates_only_affected_speech(library, book, source, script):
    speech = Speech()
    process(book, source, LLM(script), Renderer(library, speech))
    book.write('pronunciation.json', {'Mira': 'Mee rah'})
    Renderer(library, speech).render(book, 1, script, book.read('cast.json'))
    assert speech.calls == 3


@pytest.mark.parametrize('mutation', ['omit', 'reorder', 'invent', 'duplicate'])
def test_source_corruption_rejected(script, source, mutation):
    if mutation == 'omit': script.segments.pop()
    elif mutation == 'reorder': script.segments.reverse()
    elif mutation == 'invent': script.segments[0].source += 'dragon'
    else: script.segments.append(script.segments[0])
    with pytest.raises(ValueError, match='coverage'): validate_script(script, source['text'], {})


def test_unknown_speaker_rejected(script, source):
    script.segments[1].speaker = 'invented'
    with pytest.raises(ValueError, match='unknown speaker'): validate_script(script, source['text'], {})


def test_uncertain_speaker_blocks_audio(library, book, source, script):
    script.segments[1].confidence = .4
    speech = Speech()
    assert process(book, source, LLM(script), Renderer(library, speech))['state'] == 'needs_review'
    assert speech.calls == 0
    accept_script(book, source, script, approve=True)
    assert process(book, source, None, Renderer(library, speech))['state'] == 'ready'


def test_candidate_reused_after_validation_failure(book, source, script):
    script.segments[1].speaker = 'wrong'
    llm = LLM(script)
    with pytest.raises(ValueError): prepare(book, source, llm)
    with pytest.raises(ValueError): prepare(book, source, llm)
    assert llm.calls == 1


def test_identity_and_aliases_do_not_recast(script):
    original = merge_cast(script, initial_cast())
    script.characters[0].age = 'elder'
    script.characters[0].aliases = ['Miss Mira']
    updated = merge_cast(script, original)
    assert updated['mira']['voice'] == original['mira']['voice']
    assert 'Miss Mira' in updated['mira']['aliases']
    script.characters[0].id = 'another_mira'
    with pytest.raises(ValueError, match='collision'): merge_cast(script, updated)


def test_existing_id_cannot_become_someone_else(script):
    original = merge_cast(script, initial_cast())
    script.characters[0].name = 'A different character'
    with pytest.raises(ValueError, match='Identity mismatch'): merge_cast(script, original)


def test_many_characters_have_persistent_unique_cast():
    registry = initial_cast()
    for n in range(70):
        c = Character(id=f'person_{n}', name=f'Person {n}', gender='male', evidence='Explicitly described as a man')
        voice = cast(c, registry)
        validate_voice(voice)
        registry[c.id] = {'name': c.name, 'voice': voice}
    assert len({signature(c['voice']) for c in registry.values()}) == 71


def test_bad_blend_rejected():
    with pytest.raises(ValueError): validate_voice({'parts': [{'id':'am_adam','weight':.5},{'id':'bm_george','weight':.5}], 'speed':1})


def test_whole_chapter_summary_memory_requires_order(book, source, script):
    source['number'] = 2
    with pytest.raises(ValueError, match='in order'): prepare(book, source, LLM(script))


def test_quota_atomic_across_threads(library):
    def reserve(_):
        try: library.budget('m', 2, 5, 10000, 100); return True
        except RuntimeError: return False
    with ThreadPoolExecutor(max_workers=8) as pool: results = list(pool.map(reserve, range(8)))
    assert sum(results) == 2
    with sqlite3.connect(library.root/'quota.sqlite') as db: assert db.execute('SELECT count(*) FROM calls').fetchone()[0] == 2


def test_book_lock_prevents_parallel_writers(book):
    with book.lock():
        with pytest.raises(Timeout):
            with book.lock(): pass


def test_chunking_does_not_drop_words():
    text = ('A long phrase, with punctuation! ' * 80) + 'x'*1000
    chunks = list(split_text(text))
    assert ''.join(''.join(chunks).split()) == ''.join(text.split())
    assert max(map(len, chunks)) <= 450
