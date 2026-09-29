'use strict';
const $ = (id) => document.getElementById(id);
const state = { games: [], selected: 'galaga', featured: 'galaga', initials: '', user: null, token: '', config: null, paused: false, posting: false, requestId: crypto.randomUUID(), editing: null, objectUrl: null, pickerFor: 'entry', connected: false };
const apiBase = (window.ARCADE_CONFIG?.apiBase || '/api').replace(/\/$/, '');
const display = new Intl.NumberFormat('en-US');
const node = (tag, className, text) => { const el = document.createElement(tag); if (className) el.className = className; if (text !== undefined) el.textContent = text; return el; };
const gameById = (id) => state.games.find(game => game.id === id);
const scoreText = (game) => game?.record?.score || '—';
const initialsText = (game) => game?.record?.initials || '___';
const icon = (name) => { const el = node('i', `ph-bold ph-${name}`); el.setAttribute('aria-hidden', 'true'); return el; };

async function api(path, options = {}) {
  const headers = { ...(options.headers || {}) };
  if (state.token) headers.Authorization = `Bearer ${state.token}`;
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 20000);
  try {
    const response = await fetch(`${apiBase}${path}`, { ...options, headers, signal: controller.signal, cache: 'no-store' });
    if (!response.ok) {
      let message = 'The arcade could not save that change. Please try again.';
      try { message = (await response.json()).error || message; } catch (_) { /* Use the readable fallback. */ }
      if (response.status === 401) signOut(false);
      throw new Error(message);
    }
    return options.blob ? response.blob() : response.json();
  } catch (error) {
    if (error.name === 'AbortError' || error instanceof TypeError) throw new Error('Cannot reach the arcade right now. Your entry is still here; try again when the connection returns.');
    throw error;
  } finally { clearTimeout(timer); }
}

function renderBoard() {
  const game = gameById(state.featured) || state.games[0];
  if (!game) return;
  state.featured = game.id;
  $('hero-marquee').src = game.image;
  $('hero-marquee').alt = `${game.title} marquee`;
  $('hero-title').textContent = game.title;
  $('record-label').textContent = game.kind === 'time' ? 'TIME TO BEAT' : 'RECORD TO BEAT';
  $('hero-score').textContent = scoreText(game);
  $('hero-score').className = `hero-score${scoreText(game).length > 10 ? ' very-long' : scoreText(game).length > 7 ? ' long' : ''}`;
  $('hero-initials').textContent = initialsText(game);
  const index = state.games.indexOf(game);
  const around = game.id === 'galaga' ? ['donkeykong', 'mspacman', 'tetris'].map(gameById) : [1, 2, 3].map(offset => state.games[(index + offset) % state.games.length]);
  $('around-list').replaceChildren(...around.filter(Boolean).map(other => {
    const button = node('button', 'around-row');
    button.setAttribute('aria-label', `Feature ${other.title}, ${scoreText(other)}, ${initialsText(other)}`);
    const image = node('img'); image.src = other.image; image.alt = other.title;
    const info = node('div'); info.append(node('strong', scoreText(other).length > 8 ? 'long' : '', scoreText(other)), node('span', '', initialsText(other)));
    button.append(image, info); button.addEventListener('click', () => feature(other.id)); return button;
  }));
  const positions = Array.from({ length: Math.min(5, state.games.length) }, (_, offset) => (index + offset) % state.games.length);
  $('page-dots').replaceChildren(...positions.map((position, offset) => {
    const dot = node('button', `page-dot${offset === 0 ? ' active' : ''}`);
    dot.setAttribute('aria-label', `Show ${state.games[position].title}`);
    if (!offset) dot.setAttribute('aria-current', 'true');
    dot.addEventListener('click', () => feature(state.games[position].id)); return dot;
  }));
}
function feature(id) { state.featured = id; renderBoard(); }
function advance(step = 1) {
  if (!state.games.length) return;
  const index = Math.max(0, state.games.findIndex(game => game.id === state.featured));
  feature(state.games[(index + step + state.games.length) % state.games.length].id);
}
function renderEntry() {
  const game = gameById(state.selected) || state.games[0];
  if (!game) return;
  state.selected = game.id;
  $('entry-title').textContent = game.title;
  $('entry-marquee').src = game.image; $('entry-marquee').alt = game.title;
  $('entry-record').textContent = game.record ? `${scoreText(game)} · ${initialsText(game)}` : 'Set the first record';
  $('entry-record').classList.toggle('small-record', $('entry-record').textContent.length > 17);
  $('score-label').textContent = game.kind === 'time' ? 'Your time' : 'Your score';
  $('score-input').inputMode = game.kind === 'time' ? 'text' : 'numeric';
  $('score-input').placeholder = game.kind === 'time' ? '1:02.30' : '0';
  $('score-hint').textContent = game.kind === 'time' ? 'Minutes:seconds.hundredths. Lower is better.' : '';
}
function renderInitials() {
  $('initials-slots').replaceChildren(...[0, 1, 2].map(index => node('span', index === state.initials.length ? 'active' : '', state.initials[index] || '_')));
  $('initials-slots').setAttribute('aria-label', `Initials: ${state.initials || 'empty'}. ${3 - state.initials.length} letters remaining.`);
}
function enterLetter(letter) {
  if (!state.user || state.posting) return;
  state.initials = letter === 'DEL' ? state.initials.slice(0, -1) : (state.initials + letter).slice(0, 3);
  state.requestId = crypto.randomUUID(); renderInitials();
}
for (const letter of [...'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'DEL']) {
  const button = node('button', letter === 'DEL' ? 'delete' : '', letter);
  button.type = 'button'; button.setAttribute('aria-label', letter === 'DEL' ? 'Delete last initial' : `Initial ${letter}`);
  button.addEventListener('click', () => enterLetter(letter)); $('alphabet').append(button);
}
document.addEventListener('keydown', event => {
  if ($('phone-panel').hidden || document.querySelector('dialog[open]') || /INPUT|TEXTAREA|SELECT/.test(document.activeElement.tagName) || event.ctrlKey || event.metaKey || event.altKey) return;
  if (/^[a-z]$/i.test(event.key)) { enterLetter(event.key.toUpperCase()); event.preventDefault(); }
  else if (event.key === 'Backspace') { enterLetter('DEL'); event.preventDefault(); }
});
function setMessage(text = '', error = false) { $('form-message').textContent = text; $('form-message').classList.toggle('error', error); }

function renderSession() {
  const signed = Boolean(state.user);
  $('login-panel').hidden = signed;
  $('entry-fields').disabled = !signed || state.posting;
  $('signout').hidden = !signed;
  $('admin-link').hidden = !state.user?.admin;
  $('account-label').textContent = signed ? state.config?.demo ? `Preview account · ${state.user.admin ? 'admin' : 'player'}` : 'Signed in with Google' : 'Sign in to join the board';
  if (state.config?.demo && signed) $('account-label').title = 'Local test account. This is not a Google sign-in.';
  if (!signed && location.hash === '#admin') location.hash = '#play';
}
async function signIn(token) {
  state.token = token;
  state.user = await api('/session');
  try { sessionStorage.setItem('arcade_session', token); } catch (_) { /* Private browsing can disable browser storage. */ }
  renderSession(); setMessage();
}
function signOut(announce = true) {
  state.user = null; state.token = '';
  try { sessionStorage.removeItem('arcade_session'); } catch (_) { /* Optional storage. */ }
  window.google?.accounts.id.disableAutoSelect(); renderSession();
  if (announce) setMessage('Signed out. Your unfinished entry stays on this screen.');
}
function loadGoogle() {
  if (state.config.demo) {
    $('google-button').hidden = true; $('login-help').hidden = true; $('demo-login').hidden = false; return;
  }
  const script = document.createElement('script'); script.src = 'https://accounts.google.com/gsi/client'; script.async = true;
  script.onload = () => {
    google.accounts.id.initialize({ client_id: state.config.googleClientId, callback: async response => {
      try { await signIn(response.credential); } catch (error) { setMessage(error.message, true); }
    }, auto_select: false });
    google.accounts.id.renderButton($('google-button'), { theme: 'outline', size: 'large', text: 'signin_with', width: 280 });
    $('login-help').textContent = 'Your email stays off the public scoreboard.';
  };
  script.onerror = () => { $('login-help').textContent = 'Google sign-in did not load. Check your connection and reload.'; };
  document.head.append(script);
}
for (const role of ['player', 'admin']) $(`demo-${role}`).addEventListener('click', async () => {
  try {
    const result = await api('/demo-session', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ role }) });
    await signIn(result.token);
  } catch (error) { setMessage(error.message, true); }
});
$('signout').addEventListener('click', () => signOut());

function route() {
  const preview = state.config?.demo && new URLSearchParams(location.search).get('view') === 'preview' && location.hash !== '#admin';
  const mode = location.hash === '#admin' ? 'admin' : location.hash === '#tv' ? 'tv' : location.hash === '#play' ? 'play' : innerWidth < 700 ? 'play' : 'tv';
  $('experience').className = `experience ${preview ? 'preview' : mode}`;
  $('display-panel').hidden = !preview && mode !== 'tv';
  $('phone-panel').hidden = !preview && mode !== 'play';
  $('admin-panel').hidden = mode !== 'admin';
  if (mode === 'admin') {
    if (!state.user?.admin) { location.hash = '#play'; setMessage('Sign in as the arcade administrator to manage scores.', true); }
    else loadAdmin();
  }
  resizeBoard();
}
function resizeBoard() { const width = $('board').clientWidth; if (width > 0) $('board').style.setProperty('--u', `${width / 100}px`); }
new ResizeObserver(resizeBoard).observe($('board'));
window.addEventListener('hashchange', route);
window.addEventListener('resize', resizeBoard);
$('previous-game').addEventListener('click', () => advance(-1));
$('next-game').addEventListener('click', () => advance());
$('pause').addEventListener('click', () => { state.paused = !state.paused; $('pause').replaceChildren(icon(state.paused ? 'play' : 'pause'), document.createTextNode(state.paused ? ' Play' : ' Pause')); });
$('fullscreen').addEventListener('click', async () => {
  try { if (document.fullscreenElement) await document.exitFullscreen(); else await $('display-panel').requestFullscreen(); } catch (_) { $('connection').hidden = false; $('connection').textContent = 'Use your browser’s full-screen control on this device.'; }
});
$('rotate').addEventListener('click', () => { document.body.classList.toggle('rotated'); resizeBoard(); });
setInterval(() => { if (!state.paused && !document.hidden && !matchMedia('(prefers-reduced-motion: reduce)').matches && !document.querySelector('dialog[open]')) advance(); }, 15000);

function renderPicker() {
  const query = $('game-search').value.trim().toLowerCase();
  const matches = state.games.filter(game => game.title.toLowerCase().includes(query));
  $('game-options').replaceChildren(...matches.map(game => {
    const button = node('button', 'game-option'); const image = node('img'); image.src = game.image; image.alt = '';
    const info = node('div'); info.append(node('strong', '', game.title), node('small', '', `${scoreText(game)} · ${initialsText(game)}`));
    button.append(image, info);
    button.addEventListener('click', () => { state.selected = game.id; $('score-input').value = ''; state.requestId = crypto.randomUUID(); renderEntry(); setMessage(); $('game-picker').close(); $('score-input').focus(); });
    return button;
  }));
  if (!matches.length) $('game-options').append(node('p', 'small', 'No games found. Try another name.'));
}
$('change-game').addEventListener('click', () => { $('game-search').value = ''; renderPicker(); $('game-picker').showModal(); $('game-search').focus(); });
$('game-search').addEventListener('input', renderPicker);
$('close-picker').addEventListener('click', () => $('game-picker').close());
$('score-input').addEventListener('input', () => { state.requestId = crypto.randomUUID(); setMessage(); });

function clearPhoto() {
  $('proof').value = ''; $('photo-preview').hidden = true; $('photo-copy').replaceChildren(document.createTextNode('Add photo '), node('small', '', '(optional)'));
  if (state.objectUrl) URL.revokeObjectURL(state.objectUrl); state.objectUrl = null;
  $('proof-preview').removeAttribute('src');
}
$('remove-photo').addEventListener('click', () => { clearPhoto(); state.requestId = crypto.randomUUID(); });
$('proof').addEventListener('change', () => {
  const file = $('proof').files[0]; if (!file) return;
  if (file.size > 8 * 1024 * 1024 || !['image/jpeg', 'image/png', 'image/webp'].includes(file.type)) { clearPhoto(); setMessage('Choose a JPG, PNG or WebP photo smaller than 8 MB.', true); return; }
  if (state.objectUrl) URL.revokeObjectURL(state.objectUrl);
  state.objectUrl = URL.createObjectURL(file); $('proof-preview').src = state.objectUrl; $('photo-preview').hidden = false; $('photo-copy').textContent = 'Change proof photo'; state.requestId = crypto.randomUUID(); setMessage();
});
$('score-form').addEventListener('submit', async event => {
  event.preventDefault();
  if (state.posting || !state.user) return;
  if (state.initials.length !== 3) { setMessage('Tap three letters to enter your initials.', true); $('alphabet').querySelector('button').focus(); return; }
  const form = new FormData(); form.set('gameId', state.selected); form.set('score', $('score-input').value.trim()); form.set('initials', state.initials); form.set('requestId', state.requestId);
  if ($('proof').files[0]) form.set('photo', $('proof').files[0]);
  state.posting = true; renderSession(); $('submit-score').textContent = 'Posting…'; setMessage();
  try {
    const result = await api('/scores', { method: 'POST', body: form });
    $('score-form').hidden = true; $('record-preview').hidden = true; $('success-panel').hidden = false;
    $('success-title').textContent = result.isRecord ? 'NEW HIGH SCORE!' : 'SCORE POSTED!';
    $('success-detail').textContent = `${result.record.initials} · ${result.record.score} on ${gameById(state.selected).title}. ${result.isRecord ? 'Your record is on the board.' : 'Your score is saved in the game’s history.'}`;
    state.featured = state.selected; state.requestId = crypto.randomUUID(); await refreshBoard();
  } catch (error) { setMessage(error.message, true); }
  finally { state.posting = false; renderSession(); $('submit-score').textContent = 'Post score'; }
});
$('play-again').addEventListener('click', () => { $('success-panel').hidden = true; $('score-form').hidden = false; $('record-preview').hidden = false; $('score-input').value = ''; state.initials = ''; renderInitials(); clearPhoto(); setMessage(); $('score-input').focus(); });

async function refreshBoard() {
  try {
    const result = await api('/leaderboard'); state.games = result.games; state.connected = true;
    $('connection').hidden = true; renderBoard(); renderEntry();
  } catch (error) {
    state.connected = false; $('connection').hidden = false;
    $('connection').textContent = state.games.length ? 'Connection lost · showing the last received records. Reconnecting…' : 'The scoreboard service is unavailable. Please check the connection.';
  }
}
setInterval(() => { if (!document.hidden) refreshBoard(); }, 5000);
window.addEventListener('online', refreshBoard);
document.addEventListener('visibilitychange', () => { if (!document.hidden) refreshBoard(); });

$('admin-link').addEventListener('click', () => { $('admin-game').value = state.selected; location.hash = '#admin'; });
$('admin-game').addEventListener('change', loadAdmin);
async function loadAdmin() {
  $('admin-message').textContent = 'Loading submissions…';
  try {
    const { scores } = await api(`/admin/scores?gameId=${encodeURIComponent($('admin-game').value || state.selected)}`);
    $('admin-list').replaceChildren(...scores.map(score => {
      const row = node('article', `admin-score${score.deleted ? ' removed' : ''}`);
      row.append(node('div', 'record', `${score.score} · ${score.initials}`));
      row.append(node('p', '', `${score.email} · ${score.createdAt ? new Date(score.createdAt * 1000).toLocaleString() : 'Starting record'}${score.deleted ? ' · Removed' : ''}`));
      if (!score.deleted) {
        const actions = node('div', 'admin-actions');
        for (const [label, action] of [['Correct', 'edit'], ['Remove', 'delete']]) {
          const button = node('button', `text-button${action === 'delete' ? ' danger' : ''}`, label);
          button.addEventListener('click', () => openEdit(score, action)); actions.append(button);
        }
        if (score.hasPhoto) { const proof = node('button', 'text-button', 'View photo'); proof.addEventListener('click', () => showPhoto(score.photoId)); actions.append(proof); }
        row.append(actions);
      }
      return row;
    }));
    $('admin-message').textContent = scores.length ? `${scores.length} submissions shown (up to 200).` : 'No submissions for this game.';
  } catch (error) { $('admin-message').textContent = error.message; }
}
function openEdit(score, action) {
  state.editing = { score, action }; $('edit-heading').textContent = action === 'delete' ? 'REMOVE SCORE?' : 'CORRECT SCORE';
  $('edit-summary').textContent = action === 'delete' ? `Remove ${score.score} by ${score.initials}? The best remaining score will appear on the board. The removal is kept in the admin history.` : 'Save a correction to this submission. The change is recorded in the admin history.';
  $('edit-fields').hidden = action === 'delete'; $('edit-score').disabled = action === 'delete'; $('edit-initials').disabled = action === 'delete';
  $('edit-score').value = score.score; $('edit-initials').value = score.initials; $('edit-message').textContent = '';
  $('save-edit').textContent = action === 'delete' ? 'Remove score' : 'Save correction'; $('edit-dialog').showModal();
}
$('close-edit').addEventListener('click', () => $('edit-dialog').close());
$('edit-form').addEventListener('submit', async event => {
  event.preventDefault(); const { score, action } = state.editing; $('save-edit').disabled = true;
  try {
    await api(`/admin/scores/${score.id}`, { method: action === 'delete' ? 'DELETE' : 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ revision: score.revision, score: $('edit-score').value, initials: $('edit-initials').value }) });
    $('edit-dialog').close(); await loadAdmin(); await refreshBoard();
  } catch (error) { $('edit-message').textContent = error.message; }
  finally { $('save-edit').disabled = false; }
});
async function showPhoto(id) {
  try {
    const blob = await api(`/photos/${id}`, { blob: true });
    if ($('view-proof').dataset.url) URL.revokeObjectURL($('view-proof').dataset.url);
    const url = URL.createObjectURL(blob); $('view-proof').src = url; $('view-proof').dataset.url = url; $('photo-dialog').showModal();
  } catch (error) { $('admin-message').textContent = error.message; }
}
$('close-photo').addEventListener('click', () => $('photo-dialog').close());
$('photo-dialog').addEventListener('close', () => { if ($('view-proof').dataset.url) URL.revokeObjectURL($('view-proof').dataset.url); $('view-proof').removeAttribute('src'); delete $('view-proof').dataset.url; });
$('export-records').addEventListener('click', async () => {
  try { const data = await api('/admin/export'); const url = URL.createObjectURL(new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })); const a = node('a'); a.href = url; a.download = 'nicks-arcade-records.json'; a.click(); setTimeout(() => URL.revokeObjectURL(url), 1000); }
  catch (error) { $('admin-message').textContent = error.message; }
});

async function init() {
  route();
  try {
    state.config = await api('/config');
    $('preview-note').hidden = !state.config.demo;
    new ResizeObserver(() => document.documentElement.style.setProperty('--preview-height', `${$('preview-note').getBoundingClientRect().height}px`)).observe($('preview-note'));
    const submitUrl = new URL(state.config.publicUrl); submitUrl.hash = 'play';
    $('qr-link').href = submitUrl.toString();
    // Internal click opens entry here; scanning uses the configured public origin.
    $('qr-link').addEventListener('click', event => { event.preventDefault(); location.hash = '#play'; });
    await ArcadeQR.toCanvas($('qr-code'), submitUrl.toString(), { width: 240, margin: 1, errorCorrectionLevel: 'M', color: { dark: '#071418', light: '#ffffff' } });
    await refreshBoard();
    $('admin-game').replaceChildren(...state.games.map(game => { const option = node('option', '', game.title); option.value = game.id; return option; }));
    $('admin-game').value = state.selected;
    loadGoogle();
    try { const token = sessionStorage.getItem('arcade_session'); if (token) await signIn(token); } catch (_) { signOut(false); }
    renderSession(); route();
  } catch (error) { $('connection').hidden = false; $('connection').textContent = error.message; $('login-help').textContent = 'The score service must be connected before sign-in is available.'; }
}
init();
