"""Export the saved library to a read-only, self-contained listening preview.

No inference or scraping occurs here. Uncached text remains a link to the source;
rebuild after importing more chapters to include their original text locally.
"""
from __future__ import annotations
import json
import hashlib
from pathlib import Path
import shutil
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from amazing_tts.storage import Library, DEFAULT_DATA, atomic_json

ROOT = Path(__file__).resolve().parents[1]


def build(root=ROOT / 'preview-dist', data=DEFAULT_DATA):
    root = Path(root); root.mkdir(parents=True, exist_ok=True)
    lib = Library(data)
    static = ROOT / 'amazing_tts' / 'static'
    (root / 'assets').mkdir(exist_ok=True)
    for name in ['app.js', 'styles.css']:
        shutil.copyfile(static / name, root / 'assets' / name)
    index = (static / 'index.html').read_text()
    index = index.replace('<script src="/assets/app.js" type="module">', '<script>window.AMAZING_TTS_SNAPSHOT=true;</script><script src="/assets/app.js" type="module">')
    if 'window.AMAZING_TTS_SNAPSHOT' not in index:
        index = index.replace('</head>', '<script>window.AMAZING_TTS_SNAPSHOT=true;</script></head>')
    for asset in ['app.js', 'styles.css']:
        fingerprint = hashlib.sha256((static / asset).read_bytes()).hexdigest()[:12]
        index = index.replace('/assets/' + asset, '/assets/' + asset + '?v=' + fingerprint)
    (root / 'index.html').write_text(index)
    books = []
    for path in lib.books():
        meta = json.loads(path.read_text()); book = lib.book(meta['url']); bid = path.parent.name
        job = book.read('job.json', {'state': 'imported', 'ready': 0, 'target': 1})
        destination = root / 'data' / bid
        (destination / 'text').mkdir(parents=True, exist_ok=True)
        (destination / 'script').mkdir(exist_ok=True)
        (destination / 'audio').mkdir(exist_ok=True)
        chapters = []; cached = []
        for source_path in book.chapters():
            source = json.loads(source_path.read_text()); n = source['number']
            atomic_json(destination / 'text' / f'{n}.json', source); cached.append(n)
            script = book.read(book.chapter_name(n) + '/script.json')
            if script:
                atomic_json(destination / 'script' / f'{n}.json', {k: script[k] for k in ['model', 'script', 'approved']})
            manifest = book.read(book.chapter_name(n) + '/audio.json')
            if manifest:
                audio = (source_path.parent / manifest['file']).with_suffix('.mp3')
                if audio.exists():
                    target = destination / 'audio' / audio.name
                    if not target.exists() or target.stat().st_size != audio.stat().st_size:
                        shutil.copyfile(audio, target)
                    chapters.append({'number': n, 'title': source['title'] + (' — cast audition' if manifest.get('scope') == 'cast_audition' else ''), 'scope': manifest.get('scope', 'chapter'), 'duration_seconds': manifest['duration_seconds'], 'audio': f'/data/{bid}/audio/{audio.name}'})
        summary = {'id': bid, 'title': meta['title'], 'url': meta['url'], **job, 'catalog_count': meta.get('catalog_count',len(chapters))}
        detail = {**summary, 'chapters': chapters, 'catalog': book.read('catalog.json', chapters), 'cast': book.read('cast.json', {}), 'cached_text': cached}
        atomic_json(destination / 'book.json', detail); books.append(summary)
    atomic_json(root / 'data' / 'books.json', books)
    return {'books': len(books), 'indexed': sum(b['catalog_count'] for b in books), 'audio': sum(b.get('ready',0) for b in books)}


if __name__ == '__main__':
    print(build())
