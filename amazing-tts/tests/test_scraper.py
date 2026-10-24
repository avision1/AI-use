import pytest
from amazing_tts.scraper import book_url, parse_book, parse_chapter, Scraper

BASE = 'https://novelping.com/book/test-novel'
TEXT = 'This is a story paragraph with enough text to pass the minimum content size check. ' * 4


def html(n, nxt=True):
    return f'<h2><a class="chr-title">Chapter {n}</a></h2><div id="chr-content"><div class="js-ad-slot"><p>ADVERTISEMENT</p></div><p>{TEXT}</p><p>Dialogue follows.</p></div>'+ (f'<a data-chapter-nav="next" href="{BASE}/chapter-{n+1}-test">Next</a>' if nxt else '')


def test_canonicalizes_url():
    assert book_url(BASE+'/?tracking=1#abc') == BASE
    assert book_url(BASE.replace('novelping.com', 'www.novelping.com')) == BASE


@pytest.mark.parametrize('url', ['https://evil.com/book/x', 'http://novelping.com/book/x', BASE+'/chapter-1-x', 'https://novelping.com@evil.com/book/x'])
def test_rejects_arbitrary_urls(url):
    with pytest.raises(ValueError): book_url(url)


def test_template_chapters_sorted_not_latest_metadata():
    b = parse_book(f'<meta property="og:novel:novel_name" content="Novel"><meta property="og:novel:lastest_chapter_url" content="{BASE}/chapter-999-x"><div id="list-chapter"><template><a href="{BASE}/chapter-2-test">2</a><a href="{BASE}/chapter-1-test">1</a></template></div>', BASE)
    assert list(b['links']) == ['1', '2']
    assert not b['archive_complete']


def test_extracts_only_story_and_next():
    c = parse_chapter(html(1), BASE+'/chapter-1-test', BASE)
    assert 'ADVERTISEMENT' not in c['text']
    assert c['next_url'] == BASE+'/chapter-2-test'


@pytest.mark.parametrize('target', ['https://evil.com/book/x/chapter-2-y', BASE+'/chapter-3-gap'])
def test_rejects_bad_next_link(target):
    with pytest.raises(ValueError): parse_chapter(html(1).replace(BASE+'/chapter-2-test',target), BASE+'/chapter-1-test',BASE)


def test_follows_next_beyond_preview_and_reuses_sources(book):
    calls = []
    scraper = Scraper(client=object())
    def get(url):
        calls.append(url)
        n = int(url.rsplit('/chapter-',1)[1].split('-')[0])
        return html(n, n<33)
    scraper.get = get
    book.write('book.json', {'url':BASE,'title':'Test','links':{'1':BASE+'/chapter-1-test'}, 'archive_complete':False})
    result = list(scraper.download(book, limit=33))
    assert len(result) == 33 and result[-1]['number'] == 33
    assert len(calls) == 33
    assert len(list(scraper.download(book, limit=100))) == 33
    assert len(calls) == 33


def test_access_page_not_saved():
    with pytest.raises(ValueError): parse_chapter('<h1>Verify you are human</h1>',BASE+'/chapter-1-test',BASE)
