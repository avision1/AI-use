let selected = null, data = null, user = null, cloud = false, preview = false;
let auth = null, loginFn = null, chapterIndex = 0, readingChapter = null, catalogData = [];
const $ = id => document.getElementById(id);
const escape = s => String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const positionKey = () => 'amazing-position-' + selected;
function savedPosition() { try { return JSON.parse(localStorage.getItem(positionKey()) || '{}'); } catch { return {}; } }
function message(text, error = false) { $('message').textContent = text; $('message').className = 'message' + (error ? ' error' : ''); }
async function api(path, options = {}) {
  if (window.AMAZING_TTS_SNAPSHOT) {
    if (options.method && options.method !== 'GET') throw Error('This preview plays saved audio; new model generation is disabled.');
    if (path === '/api/config') return {cloud: false, preview: true};
    let target;
    if (path === '/api/books') target = '/data/books.json';
    else {
      const match = path.match(/^\/api\/books\/([a-f0-9]{20})(?:\/(text|script)\/(\d+))?$/);
      if (!match) throw Error('Not available in this saved preview');
      target = '/data/' + match[1] + (match[2] ? '/' + match[2] + '/' + match[3] + '.json' : '/book.json');
    }
    const response = await fetch(target, {cache: 'no-store'});
    if (!response.ok) throw Error('This chapter has not been cached yet. Open its NovelPing link or refresh after import finishes.');
    try { return await response.json(); } catch { throw Error('This chapter is still being imported. Please refresh shortly.'); }
  }
  options.headers = {...options.headers};
  if (user) options.headers.Authorization = 'Bearer ' + await user.getIdToken();
  if (options.body) options.headers['Content-Type'] = 'application/json';
  const r = await fetch(path, options);
  if (!r.ok) { const b = await r.json().catch(() => ({})); throw Error(typeof b.detail === 'string' ? b.detail : 'Request failed. Please try again.'); }
  return r.json();
}
async function init() {
  const c = await api('/api/config'); cloud = c.cloud; preview = c.preview;
  if (preview) { $('request').hidden = true; $('previewnotice').hidden = false; $('login').textContent = 'Listening preview'; $('login').disabled = true; }
  if (cloud) {
    $('login').textContent = 'Sign in with Google';
    if (!c.firebase.apiKey) { message('Cloud sign-in needs Firebase configuration.', true); return; }
    const [{initializeApp}, {getAuth, GoogleAuthProvider, signInWithPopup, onAuthStateChanged, signOut}] = await Promise.all([
      import('https://www.gstatic.com/firebasejs/11.6.0/firebase-app.js'), import('https://www.gstatic.com/firebasejs/11.6.0/firebase-auth.js')]);
    auth = getAuth(initializeApp(c.firebase)); loginFn = () => user ? signOut(auth) : signInWithPopup(auth, new GoogleAuthProvider());
    onAuthStateChanged(auth, u => { user = u; $('login').textContent = u ? 'Sign out' : 'Sign in with Google'; });
  }
  await load();
  const preferred = catalogData.find(b => b.catalog_count) || catalogData.find(b => b.id === localStorage.getItem('amazing-last-book')) || catalogData[0];
  if (preferred) await openBook(preferred.id);
}
$('login').onclick = () => loginFn?.().catch(e => message(e.message, true));
async function load() {
  catalogData = await api('/api/books');
  catalogData.sort((a, b) => (b.catalog_count || 0) - (a.catalog_count || 0));
  $('books').innerHTML = catalogData.length ? catalogData.map(b => `<button class="card ${b.id === selected ? 'active' : ''}" data-book="${escape(b.id)}"><span class="status">${escape((b.state || 'saved').replaceAll('_', ' '))}</span><h3>${escape(b.title)}</h3><div class="meta">${b.ready || 0} recordings saved${b.catalog_count ? ' · ' + b.catalog_count + ' chapters indexed' : ' · ' + (b.target || 1) + ' requested'}</div></button>`).join('') : '<div class="empty">No stories yet. Paste a novel link to begin.</div>';
  document.querySelectorAll('[data-book]').forEach(b => b.onclick = () => openBook(b.dataset.book).catch(e => message(e.message, true)));
}
async function openBook(id) {
  selected = id; localStorage.setItem('amazing-last-book', id); data = await api('/api/books/' + id); readingChapter = null;
  await load(); renderPlayer(); renderCatalog();
  if (preview) $('previewnotice').textContent = data.audio_scope === 'cast_audition'
    ? 'Low-compute preview: a short three-voice audition from Chapter 1. All ' + (data.catalog || []).length + ' chapters are available as text. Full-chapter audio has not been generated.'
    : 'Low-compute preview: saved recordings and the chapter catalog. No model requests run from this page.';
}
function audioRows() {
  return data.chapters.map((c, i) => `<button class="chapter ${i === chapterIndex ? 'selected' : ''}" data-index="${i}"><span>${escape(c.title)}</span><span>${Math.round(c.duration_seconds / 60)} min</span></button>`).join('');
}
function bindAudioRows() { document.querySelectorAll('[data-index]').forEach(b => b.onclick = () => play(+b.dataset.index, true)); }
function renderPlayer() {
  const saved = savedPosition(); chapterIndex = Math.max(0, data.chapters.findIndex(c => c.number === saved.chapter));
  $('detail').innerHTML = `<div class="player"><span class="tag">${data.audio_scope === 'cast_audition' ? 'CAST AUDITION · CHAPTER 1 EXCERPTS' : 'SAVED AUDIO'}</span><h2 style="margin-top:14px">${escape(data.title)}</h2><div class="meta" id="chapterTitle"></div><audio id="audio" controls preload="metadata"></audio><div class="controls"><button id="previous">← Previous</button><label>PLAYBACK SPEED <select id="speed"><option>.75</option><option selected>1</option><option>1.25</option><option>1.5</option><option>2</option></select></label><button id="next">Next →</button></div><div class="chapters">${audioRows()}</div>${!data.chapters.length ? '<p>No audio yet. Saved recordings will appear here as chapters finish.</p>' : ''}<p id="jobstate" class="meta">${escape((data.state || 'saved').replaceAll('_', ' '))}${data.error ? ' · ' + escape(data.error) : ''}</p><details><summary>Meet the cast · ${Object.keys(data.cast).length} voices</summary><div class="cast">${Object.values(data.cast).map(c => `<span class="chip">${escape(c.name)}<br><small>${escape(c.voice.parts.map(p => p.id).join(' + '))}</small></span>`).join('')}</div></details>${!preview && ['needs_review', 'paused'].includes(data.state) ? '<details><summary>Review this chapter</summary><p>Check the speaker assignments and spoken text against the original before approving.</p><button id="reviewload">Load script for review</button><div id="reviewpanel"></div></details>' : ''}</div>`;
  if (data.chapters.length) play(chapterIndex, false, saved.time || 0);
  $('previous').onclick = () => play(chapterIndex - 1, true); $('next').onclick = () => play(chapterIndex + 1, true);
  $('speed').onchange = () => { $('audio').playbackRate = +$('speed').value; }; bindAudioRows();
  if ($('reviewload')) $('reviewload').onclick = loadReview;
}
function play(i, autoplay = false, time = 0) {
  if (i < 0 || i >= data.chapters.length) return;
  chapterIndex = i; const c = data.chapters[i], a = $('audio'); a.src = c.audio; $('chapterTitle').textContent = c.title;
  a.onloadedmetadata = () => { a.currentTime = Math.min(time, Math.max(0, a.duration - 1)); a.playbackRate = +$('speed').value; };
  a.ontimeupdate = () => localStorage.setItem(positionKey(), JSON.stringify({chapter: c.number, time: a.currentTime}));
  a.onended = () => play(i + 1, true);
  a.onerror = () => message('The audio is unavailable. Select the chapter again to refresh its link.', true);
  $('previous').disabled = i === 0; $('next').disabled = i === data.chapters.length - 1;
  document.querySelectorAll('[data-index]').forEach(b => b.classList.toggle('selected', +b.dataset.index === i));
  if (autoplay) a.play().catch(() => {});
}
function renderCatalog() {
  const section = $('chapterbrowser'); section.hidden = false;
  section.innerHTML = '<div class="catalog-heading"><h2>Every chapter</h2><input id="chapterSearch" aria-label="Find a chapter" placeholder="Search by title or chapter number"></div><p class="chapter-count" id="catalogCount"></p><div class="catalog-grid" id="catalogGrid"></div><article class="reading-pane" id="readingPane" hidden></article>';
  $('chapterSearch').oninput = drawCatalog; drawCatalog();
}
function drawCatalog() {
  const all = data.catalog || data.chapters, q = $('chapterSearch').value.trim().toLowerCase().replace(/^#/, '');
  const entries = all.filter(c => !q || c.title.toLowerCase().includes(q) || String(c.number) === q);
  $('catalogCount').textContent = `${all.length} chapters indexed · ${data.chapters.length} saved ${data.audio_scope === 'cast_audition' ? 'cast audition' : 'recordings'}. Other chapters open as text without model calls.`;
  const ready = new Set(data.chapters.map(c => c.number));
  $('catalogGrid').innerHTML = entries.map(c => `<button class="catalog-entry ${ready.has(c.number) ? 'ready' : ''}" data-chapter="${c.number}"><small>${ready.has(c.number) ? (data.audio_scope === 'cast_audition' ? '● Voice audition · read full chapter' : '● Audio ready · read or listen') : 'Text · audio not generated'}</small><span>${escape(c.title)}</span></button>`).join('') || '<p>No matching chapters.</p>';
  $('catalogGrid').querySelectorAll('[data-chapter]').forEach(b => b.onclick = () => readChapter(+b.dataset.chapter));
}
async function readChapter(n) {
  readingChapter = n; const pane = $('readingPane'); pane.hidden = false; pane.innerHTML = '<p>Opening chapter…</p>';
  const c = (data.catalog || data.chapters).find(c => c.number === n), index = data.chapters.findIndex(c => c.number === n);
  try {
    const original = await api(`/api/books/${selected}/text/${n}`); if (readingChapter !== n) return;
    pane.innerHTML = `<div class="reading-tools"><span class="tag">CHAPTER ${n}</span><div>${index >= 0 ? '<button id="listenChapter">▶ Listen to saved recording</button> <button id="scriptToggle">Show audiobook script</button>' : ''} <a href="${escape(original.url)}" target="_blank" rel="noopener">NovelPing ↗</a></div></div><h2 style="margin-top:20px">${escape(c.title)}</h2><div class="meta" id="readingMode">Original chapter · cached after first read</div><div class="prose" id="readingText"></div>`;
    function showOriginal() { $('readingText').innerHTML = original.text.split('\n\n').map(p => `<p>${escape(p)}</p>`).join(''); $('readingMode').textContent = 'Original chapter · cached after first read'; }
    showOriginal(); let scriptVisible = false;
    if (index >= 0) {
      $('listenChapter').onclick = () => { play(index, true); $('detail').scrollIntoView({behavior: 'smooth', block: 'start'}); };
      $('scriptToggle').onclick = async () => {
        try {
          if (scriptVisible) { showOriginal(); $('scriptToggle').textContent = 'Show audiobook script'; scriptVisible = false; return; }
          const s = await api(`/api/books/${selected}/script/${n}`); if (readingChapter !== n) return;
          $('readingText').innerHTML = s.script.segments.map(segment => `<span class="speaker">${escape(data.cast[segment.speaker]?.name || segment.speaker)} · ${escape(segment.kind)}</span><p>${escape(segment.text)}</p>`).join('');
          $('readingMode').textContent = 'Saved audiobook script · ' + s.model; $('scriptToggle').textContent = 'Show original text'; scriptVisible = true;
        } catch (e) { $('readingMode').textContent = e.message; }
      };
    }
    pane.scrollIntoView({behavior: 'smooth', block: 'start'});
  } catch (e) { pane.innerHTML = `<p class="reader-error">${escape(e.message)}</p><a href="${escape(c.url)}" target="_blank" rel="noopener">Open this chapter on NovelPing ↗</a>`; }
}
async function loadReview() {
  try {
    const review = await api('/api/books/' + selected + '/review');
    $('reviewpanel').innerHTML = '<h3>Original chapter</h3><pre id="original"></pre><label for="script">SCRIPT JSON</label><textarea id="script"></textarea><button id="approve" class="primary">Approve & continue</button>';
    $('original').textContent = review.source?.text || 'Source unavailable'; $('script').value = typeof review.script === 'string' ? review.script : JSON.stringify(review.script, null, 2);
    $('approve').onclick = async () => { try { await api('/api/books/' + selected + '/review', {method: 'POST', body: JSON.stringify({script: JSON.parse($('script').value)})}); message('Approved. Generation will continue.'); await openBook(selected); } catch (e) { message(e.message, true); } };
  } catch (e) { message(e.message, true); }
}
$('request').onsubmit = async e => {
  e.preventDefault(); $('create').disabled = true;
  try { if (cloud && !user) throw Error('Sign in with Google to request an audiobook.'); const b = await api('/api/books', {method: 'POST', body: JSON.stringify({url: $('url').value, chapters: +$('count').value})}); message(b.ready >= +$('count').value ? 'Using the saved audiobook.' : 'Request saved. Chapters will appear as they finish.'); await openBook(b.id); }
  catch (e) { message(e.message, true); } finally { $('create').disabled = false; }
};
$('refresh').onclick = async () => { try { if (selected) await openBook(selected); else await load(); } catch (e) { message(e.message, true); } };
// Preserve the player and reading pane while updating ready chapters.
setInterval(async () => {
  try { await load(); if (!selected) return; const fresh = await api('/api/books/' + selected), changed = fresh.chapters.length !== data.chapters.length; data = fresh;
    if (changed) { if (!$('audio')?.getAttribute('src')) renderPlayer(); else { document.querySelector('.chapters').innerHTML = audioRows(); bindAudioRows(); } if ($('catalogGrid')) drawCatalog(); }
    if ($('jobstate')) $('jobstate').textContent = (fresh.state || 'saved').replaceAll('_', ' ') + ' · ' + (fresh.ready || 0) + ' recordings saved' + (fresh.error ? ' · ' + fresh.error : '');
  } catch { /* Preserve playback during a temporary status failure. */ }
}, 15000);
init().catch(e => message(e.message, true));
