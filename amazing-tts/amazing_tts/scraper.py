from __future__ import annotations

import re
import time
from urllib.parse import urljoin, urlsplit, urlencode
import httpx
from bs4 import BeautifulSoup

USER_AGENT = "AmazingTTS/0.1 (personal audiobook importer; one request every 2 seconds)"


def book_url(url: str) -> str:
    p = urlsplit(url.strip())
    if p.scheme != "https" or p.netloc not in {"novelping.com", "www.novelping.com"} or not re.fullmatch(r"/book/[a-zA-Z0-9-]+/?", p.path):
        raise ValueError("Enter an HTTPS NovelPing novel URL: https://novelping.com/book/novel-slug")
    return "https://novelping.com" + p.path.rstrip("/")


def chapter_url(url: str, base: str) -> str:
    p = urlsplit(urljoin(base + "/", url))
    b = urlsplit(base)
    if p.scheme != "https" or p.netloc != b.netloc or not re.fullmatch(re.escape(b.path) + r"/chapter-\d+[^/]*", p.path):
        raise ValueError("Rejected chapter URL outside this novel")
    return p.scheme + "://" + p.netloc + p.path


def number(url: str) -> int:
    return int(re.search(r"/chapter-(\d+)", url).group(1))


def parse_book(html: str, url: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    title = soup.select_one('meta[property="og:novel:novel_name"]') or soup.select_one('meta[property="og:title"]')
    links = {}
    for a in soup.select("#list-chapter a[href]"):
        try:
            target = chapter_url(a["href"], url)
        except ValueError:
            continue
        links[number(target)] = target
    if not links:
        raise ValueError("No chapter links found; page layout changed or access was blocked")
    # A latest-chapter metadata URL is NOT a complete table of contents.
    return {"url": url, "title": title["content"] if title else soup.title.get_text(strip=True),
            "links": {str(n): links[n] for n in sorted(links)}, "archive_complete": False}


def parse_chapter(html: str, url: str, base: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    node = soup.select_one("#chr-content")
    heading = soup.select_one(".chr-title")
    if node is None or heading is None:
        raise ValueError("Chapter text missing; page layout changed or access was blocked")
    for junk in node.select("script, style, .js-ad-slot, .ads, ins, button, nav"):
        junk.decompose()
    paragraphs = [p.get_text(" ", strip=True) for p in node.find_all("p")]
    if not paragraphs:
        paragraphs = node.get_text("\n", strip=True).splitlines()
    text = "\n\n".join(p for p in paragraphs if p.strip())
    if len(text) < 100:
        raise ValueError("Implausibly short chapter; refusing to cache an error page")
    nxt = soup.select_one('a[data-chapter-nav="next"][href]') or soup.select_one('a[rel="next"][href]')
    next_url = None
    if nxt and not nxt.has_attr("disabled") and not nxt["href"].startswith("javascript:"):
        next_url = chapter_url(nxt["href"], base)
        if number(next_url) != number(url) + 1:
            raise ValueError("Next chapter is not consecutive; refusing a silent gap")
    return {"number": number(url), "url": url, "title": heading.get_text(" ", strip=True), "text": text, "next_url": next_url}


class Scraper:
    def __init__(self, client=None, delay=2.0):
        self.client = client or httpx.Client(timeout=40, follow_redirects=False, headers={"User-Agent": USER_AGENT})
        self.delay = max(2., delay)
        self.last_request = 0.

    def get(self, url: str) -> str:
        time.sleep(max(0., self.delay - (time.monotonic() - self.last_request)))
        self.last_request = time.monotonic()
        try:
            r = self.client.get(url)
            r.raise_for_status()
        except httpx.HTTPError as exc:
            raise RuntimeError("NovelPing fetch failed. No access challenges are bypassed; retry later or import local text.") from exc
        return r.text

    def discover(self, book):
        metadata = book.read("book.json")
        if metadata is None:
            metadata = parse_book(self.get(book.url), book.url)
            book.write("book.json", metadata)
        return metadata

    def download(self, book, limit: int = 1, start: int = 1):
        if limit < 1 or start < 1:
            raise ValueError("Start and limit must be positive")
        meta = self.discover(book)
        # Walk saved next links, so the first-30 preview never limits a long novel.
        for n in range(1, start + limit):
            name = book.chapter_name(n) + "/source.json"
            saved = book.read(name)
            if saved is None:
                target = meta["links"].get(str(n))
                if target is None:
                    if meta.get("archive_complete"):
                        break
                    raise ValueError(f"Missing URL for chapter {n}; cannot skip a chapter")
                saved = parse_chapter(self.get(target), target, book.url)
                book.write(name, saved)
            nxt = saved["next_url"]
            if nxt:
                meta["links"][str(n+1)] = nxt
            else:
                meta["archive_complete"] = True
                meta["last_chapter"] = n
            book.write("book.json", meta)
            if n >= start:
                yield saved
            if not nxt:
                break


def parse_archive(html: str, base: str) -> list[dict]:
    """Read the public chapter archive, including anchors inside HTML templates."""
    soup = BeautifulSoup(html, "html.parser")
    found = {}
    for a in soup.select('a[href]'):
        try:
            target = chapter_url(a["href"], base)
        except ValueError:
            continue
        n = number(target)
        title = a.get("title") or " ".join(a.stripped_strings) or f"Chapter {n}"
        found[n] = {"number": n, "title": title, "url": target}
    if not found:
        raise ValueError("No public chapter archive entries found")
    numbers = sorted(found)
    if numbers != list(range(1, numbers[-1]+1)):
        raise ValueError("Chapter archive contains gaps; refusing to label it complete")
    return [found[n] for n in numbers]


def import_archive(scraper: Scraper, book, html=None):
    meta = scraper.discover(book)
    if html is None:
        html = scraper.get("https://novelping.com/ajax/chapter-archive?" + urlencode({"novelId": book.url.rsplit("/", 1)[-1]}))
    catalog = parse_archive(html, book.url)
    meta["links"].update({str(c["number"]): c["url"] for c in catalog})
    meta["catalog_count"] = len(catalog)
    # Knowing the index is complete does not mean all chapter bodies are downloaded.
    meta["catalog_complete"] = True
    book.write("catalog.json", catalog)
    book.write("book.json", meta)
    return catalog
