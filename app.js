'use strict';
const $ = (id) => document.getElementById(id);
const state = { games: [], boardGames: [], allGames: [], bypassGamesRestriction: false, account: null, accountView: 'activity', automaticTaunt: false, latestEvent: 0, pendingGame: null, selected: 'galaga', featured: 'galaga', initials: '', user: null, token: '', config: null, paused: false, posting: false, requestId: crypto.randomUUID(), editing: null, objectUrl: null, pickerFor: 'entry', connected: false };
const apiBase = (window.ARCADE_CONFIG?.apiBase || '/api').replace(/\/$/, '');
const display = new Intl.NumberFormat('en-US');
const node = (tag, className, text) => { const el = document.createElement(tag); if (className) el.className = className; if (text !== undefined) el.textContent = text; return el; };
const gameById = (id) => state.allGames.find(game => game.id === id) || (state.pendingGame?.id === id ? state.pendingGame : undefined);
const artworkUrl = game => game.marqueeId ? `${apiBase}/marquees/${game.marqueeId}` : `${ArcadeArtwork.resolve(game)}?v=${game.id === 'simpsons' ? 'simpsons-cabinet-1' : 'marquee-2'}`;
const scoreText = (game) => game?.record?.score || '—';
const initialsText = (game) => game?.record?.initials || '___';
const icon = (name) => { const el = node('i', `ph-bold ph-${name}`); el.setAttribute('aria-hidden', 'true'); return el; };

async function api(path, options = {}) {
  const headers = { ...(options.headers || {}) };
  if (state.token) headers.Authorization = `Bearer ${state.token}`;
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), options.body instanceof FormData ? 120000 : 20000);
  try {
    const response = await fetch(`${apiBase}${path}`, { ...options, headers, signal: controller.signal, cache: 'no-store' });
    if (!response.ok) {
      let message = 'The arcade could not save that change. Please try again.';
      try { message = (await response.json()).error || message; } catch (_) { /* Use the readable fallback. */ }
      if (response.status === 401) signOut(false);
      const error = new Error(message); error.status = response.status; throw error;
    }
    return options.blob ? response.blob() : response.json();
  } catch (error) {
    if (error.name === 'AbortError' || error instanceof TypeError) throw new Error('Cannot reach the arcade right now. Your entry is still here; try again when the connection returns.');
    throw error;
  } finally { clearTimeout(timer); }
}

function renderImprovement(id, record) {
  const badge = $(id), margin = record?.improvement;
  badge.hidden = !margin; badge.replaceChildren();
  if (!margin) return;
  badge.setAttribute('aria-label', margin.label); badge.setAttribute('aria-expanded', 'false');
  badge.append(document.createTextNode(`${margin.direction === 'down' ? '↓ ' : '↑ +'}${margin.amount}`));
  const detail = node('span', 'improvement-detail', margin.label); detail.hidden = true;
  badge.append(detail);
  badge.onclick = () => { detail.hidden = !detail.hidden; badge.setAttribute('aria-expanded', String(!detail.hidden)); };
  badge.onblur = () => { detail.hidden = true; badge.setAttribute('aria-expanded', 'false'); };
  badge.onkeydown = event => { if (event.key === 'Escape') { detail.hidden = true; badge.setAttribute('aria-expanded', 'false'); } };
}
function renderBoard() {
  const game = state.boardGames.find(game => game.id === state.featured) || state.boardGames[0];
  if (!game) {
    renderFeaturedCabinets(null); $('hero-marquee').src = 'images/new-game.svg'; $('hero-marquee').alt = 'Nick’s Arcade';
    $('hero-title').textContent = 'Nick’s Arcade'; $('record-label').textContent = 'LEADERBOARD';
    $('hero-score').textContent = 'COMING SOON'; $('hero-score').className = 'hero-score empty-record';
    $('hero-initials').textContent = ''; $('record-age').textContent = '';
    renderImprovement('hero-improvement', null); $('around-list').replaceChildren(); delete $('around-list').dataset.rendered; $('page-dots').replaceChildren();
    return;
  }
  state.featured = game.id; renderFeaturedCabinets(game);
  if ($('hero-marquee').getAttribute('src') !== artworkUrl(game)) $('hero-marquee').src = artworkUrl(game);
  $('hero-marquee').alt = `${game.title} marquee`;
  $('hero-title').textContent = game.title;
  $('record-label').textContent = !game.record ? 'SET THE FIRST RECORD' : game.kind === 'time' ? 'TIME TO BEAT' : 'RECORD TO BEAT';
  refreshRecordAge();
  $('hero-score').textContent = game.record ? scoreText(game) : 'BE THE FIRST';
  $('hero-score').className = `hero-score${scoreText(game).length > 10 ? ' very-long' : scoreText(game).length > 7 ? ' long' : ''}`;
  $('hero-score').classList.toggle('empty-record', !game.record);
  $('hero-initials').classList.toggle('empty-record', !game.record);
  $('hero-initials').textContent = game.record ? initialsText(game) : 'YOUR INITIALS HERE'; renderImprovement('hero-improvement', game.record);
  const index = state.boardGames.indexOf(game);
  const preferred = game.id === 'galaga' ? ['donkeykong', 'mspacman', 'tetris'].map(id => state.boardGames.find(other => other.id === id)).filter(Boolean) : [];
  const around = [...preferred, ...[1, 2, 3].map(offset => state.boardGames[(index + offset) % state.boardGames.length])].filter((other, i, games) => other && other.id !== game.id && games.findIndex(entry => entry?.id === other.id) === i).slice(0, 3);
  const aroundSignature=JSON.stringify(around.map(other=>[other.id,other.title,artworkUrl(other),other.record?.score,other.record?.initials]));
  if ($('around-list').dataset.rendered !== aroundSignature) {
  $('around-list').dataset.rendered=aroundSignature;
  $('around-list').replaceChildren(...around.filter(Boolean).map(other => {
    const button = node('button', 'around-row');
    button.setAttribute('aria-label', `View ${other.title} history, ${scoreText(other)}, ${initialsText(other)}`);
    const image = node('img'); image.src = artworkUrl(other); image.alt = other.title;
    const info = node('div'); info.append(node('strong', scoreText(other).length > 8 ? 'long' : '', other.record ? scoreText(other) : 'OPEN RECORD'), node('span', '', other.record ? initialsText(other) : 'Be the first'));
    button.append(image, info); button.addEventListener('click', () => { feature(other.id); openWhereToPlay(other); }); return button;
  }));
  }
  warmArtwork(around.map(artworkUrl));
  const positions = Array.from({ length: Math.min(5, state.boardGames.length) }, (_, offset) => (index + offset) % state.boardGames.length);
  $('page-dots').replaceChildren(...positions.map((position, offset) => {
    const dot = node('button', `page-dot${offset === 0 ? ' active' : ''}`);
    dot.setAttribute('aria-label', `Show ${state.boardGames[position].title}`);
    if (!offset) dot.setAttribute('aria-current', 'true');
    dot.addEventListener('click', () => feature(state.boardGames[position].id)); return dot;
  }));
}
function refreshRecordAge() {
  const game = state.boardGames.find(game => game.id === state.featured) || state.boardGames[0];
  const label = $('record-age'), text = game ? ArcadeCelebrations.recordAge(game.record) : '';
  label.textContent = text;
  const parts = text.split(' · ');
  if (parts.length === 2) {
    const corrected = parts[1] === 'corrected';
    label.replaceChildren(node('strong', 'record-age-value', corrected ? 'Corrected' : parts[0]), node('span', 'record-age-date', corrected ? parts[0] : parts[1]));
  }
}
// Keep time labels fresh even when a score fetch fails or rotation is paused.
setInterval(refreshRecordAge, 30000);
window.addEventListener('pageshow', refreshRecordAge);
window.addEventListener('focus', refreshRecordAge);
document.addEventListener('visibilitychange', () => { if (!document.hidden) refreshRecordAge(); });
function feature(id) { state.featured = id; renderBoard(); }
function advance(step = 1) {
  if (!state.boardGames.length) return;
  const index = Math.max(0, state.boardGames.findIndex(game => game.id === state.featured));
  feature(state.boardGames[(index + step + state.boardGames.length) % state.boardGames.length].id);
}
function renderEntry() {
  const game = gameById(state.selected) || state.games[0];
  if (!game) return;
  state.selected = game.id;
  $('entry-title').textContent = game.title;
  $('entry-marquee').src = artworkUrl(game); $('entry-marquee').alt = game.title;
  $('entry-record').textContent = game.record ? `${scoreText(game)} · ${initialsText(game)}` : 'Set the first record';
  $('entry-record').classList.toggle('small-record', $('entry-record').textContent.length > 17);
  $('score-label').textContent = game.kind === 'time' ? 'Your time' : 'Your score';
  $('score-input').inputMode = game.kind === 'time' ? 'text' : 'numeric';
  $('score-input').placeholder = game.kind === 'time' ? '1:02.30' : '0';
  $('score-hint').textContent = game.kind === 'time' ? 'Minutes:seconds.hundredths. 1:02:30 and 1:02.30 both mean 1 min 2.30 sec. Lower is better.' : '';
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
  $('account-button').hidden = false;
  $('account-button').setAttribute('aria-label', signed ? 'My account' : 'My account · sign in');
  $('account-admin').hidden = !state.user?.admin;
  $('admin-link').hidden = !state.user?.admin;
  $('tv-admin-button').hidden = !state.user?.admin;
  $('tv-setup-button').hidden = !state.user?.admin; $('account-tv-setup').hidden = !state.user?.admin;
  if (!state.user?.admin) $('tv-setup-dialog').close();
  $('tv-cabinets-button').hidden = !state.user?.admin; $('account-cabinets').hidden = !state.user?.admin;
  if (!state.user?.admin) for (const id of ['cabinets-dialog','cabinet-editor','assignment-dialog','cabinet-add-dialog']) $(id).close();
  $('tv-games-button').hidden = !state.user?.admin; $('account-games').hidden = !state.user?.admin;
  if (!state.user?.admin) { $('games-dialog').close(); $('arcade-games-list').replaceChildren(); }
  if (!state.user?.admin) { $('admin-list').replaceChildren(); $('admin-feedback').textContent = ''; }
  $('account-label').textContent = signed ? state.config?.demo ? `Preview account · ${state.user.admin ? 'admin' : 'player'}` : 'Signed in with Google' : 'Sign in to join the board';
  if (state.config?.demo && signed) $('account-label').title = 'Local test account. This is not a Google sign-in.';
  if (!signed && location.hash === '#admin') location.hash = '#play';
}
function applySavedTaunt() {
  state.automaticTaunt = Boolean(state.account?.tauntEnabled);
  $('taunt-input').value = state.automaticTaunt ? state.account.defaultTaunt : '';
  state.requestId = crypto.randomUUID();
}
async function signIn(token, { goToBoard = state.accountSignIn || location.hash !== '#play', restore = false } = {}) {
  state.token = token;
  if (!restore && !state.config?.demo) {
    const session = await api('/session', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({remember:$('remember-device').checked})});
    state.token = session.token; state.user = session.user;
    try { localStorage.removeItem('arcade_session');sessionStorage.removeItem('arcade_session');($('remember-device').checked ? localStorage : sessionStorage).setItem('arcade_session',state.token); } catch (_) { try { sessionStorage.setItem('arcade_session',state.token); } catch (_) {} }
  } else { state.user = await api('/session'); if (!restore) try { sessionStorage.setItem('arcade_session',token); } catch (_) {} }
  state.accountSignIn = false;
  renderSession(); setMessage(); await refreshAccount(); applySavedTaunt();
  if (!state.initials && state.account?.initials) { state.initials = state.account.initials; renderInitials(); }
  if (goToBoard) { $('account-dialog').close(); location.hash = '#tv'; route(); }
}
async function signOut(announce = true) {
  if (announce && state.token?.startsWith('arcade_')) {
    try { await api('/session', {method:'DELETE'}); }
    catch (error) { if (error.status !== 401) { setMessage('Could not sign out on the server. Check your connection and try again.',true);$('account-message').textContent='Could not sign out. Check your connection and try again.';return; } }
  }
  $('taunt-input').value = ''; state.automaticTaunt = false;
  state.user = null; state.token = ''; state.account = null; $('account-dialog').close(); $('unread-count').hidden = true; $('tv-unread-count').hidden = true; $('menu-unread-count').hidden = true; $('display-menu-toggle').setAttribute('aria-label', 'Scoreboard menu'); $('activity-list').replaceChildren(); $('my-scores-list').replaceChildren();
  try { sessionStorage.removeItem('arcade_session'); } catch (_) {}
  try { localStorage.removeItem('arcade_session'); } catch (_) {}
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

const tvAngles = [0, 90, 180, 270];
const validTvAngle = value => value !== null && value !== '' && tvAngles.includes(Number(value));
let tvOrientation = 0;
try { const stored = localStorage.getItem('arcade_tv_orientation'); if (validTvAngle(stored)) tvOrientation = Number(stored); } catch (_) { /* The bookmarked TV link also works without storage. */ }
const linkedTvAngle = new URLSearchParams(location.search).get('tvRotation');
if (validTvAngle(linkedTvAngle)) tvOrientation = Number(linkedTvAngle);
function applyTvOrientation(active) {
  document.body.classList.toggle('rotated', active && tvOrientation !== 0);
  document.body.classList.toggle('tv-quarter-turn', active && tvOrientation % 180 !== 0);
  document.body.style.setProperty('--tv-angle', `${tvOrientation}deg`);
}
function tvSetupUrl(angle) {
  const url = new URL(location.href); url.searchParams.delete('view'); url.searchParams.set('tvRotation', String(angle)); url.hash = 'tv'; return url.href;
}
function saveTvOrientation(angle) {
  if (!tvAngles.includes(angle)) return false;
  tvOrientation = angle;
  let saved = true;
  try { localStorage.setItem('arcade_tv_orientation', String(angle)); } catch (_) { saved = false; }
  history.replaceState(null, '', tvSetupUrl(angle));
  return saved;
}
function updateTvLink() { $('tv-setup-link').value = tvSetupUrl(Number($('tv-orientation').value)); }
async function openTvSetup() {
  if (!state.user?.admin) return;
  if (document.fullscreenElement) await document.exitFullscreen();
  $('display-menu').open = false; $('account-dialog').close();
  $('tv-orientation').value = String(tvOrientation); $('tv-setup-message').textContent = ''; updateTvLink(); $('tv-setup-dialog').showModal();
}
$('tv-setup-button').addEventListener('click', openTvSetup);
$('account-tv-setup').addEventListener('click', openTvSetup);
$('close-tv-setup').addEventListener('click', () => $('tv-setup-dialog').close());
$('tv-orientation').addEventListener('change', updateTvLink);
$('copy-tv-link').addEventListener('click', async () => {
  if (!state.user?.admin) return;
  try { await navigator.clipboard.writeText($('tv-setup-link').value); $('tv-setup-message').textContent = 'TV link copied. Set it as the TV browser’s startup page or bookmark.'; }
  catch (_) { $('tv-setup-link').focus(); $('tv-setup-link').select(); $('tv-setup-message').textContent = 'Select and copy the TV link above.'; }
});
$('tv-setup-form').addEventListener('submit', event => {
  event.preventDefault(); if (!state.user?.admin) return;
  const saved = saveTvOrientation(Number($('tv-orientation').value)); route();
  $('tv-setup-message').textContent = saved ? 'Saved for this browser. Close this window to view the TV screen. Bookmark the TV link to keep the angle even if browser data is cleared.' : 'Orientation applied. Browser storage is unavailable; use the TV link as your startup page to remember it.';
});

function route() {
  $('display-menu').open = false;
  const preview = state.config?.demo && new URLSearchParams(location.search).get('view') === 'preview' && location.hash !== '#admin';
  const mode = location.hash === '#admin' ? 'admin' : location.hash === '#tv' ? 'tv' : location.hash === '#play' ? 'play' : 'tv';
  $('experience').className = `experience ${preview ? 'preview' : mode}`;
  $('display-panel').hidden = !preview && mode !== 'tv';
  $('phone-panel').hidden = !preview && mode !== 'play';
  $('admin-panel').hidden = mode !== 'admin';
  if (mode === 'admin') {
    if (!state.user?.admin) { location.hash = '#play'; setMessage('Sign in as the arcade administrator to manage scores.', true); }
    else loadAdmin();
  }
  applyTvOrientation(mode === 'tv' && !preview);
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
$('rotate').addEventListener('click', () => { saveTvOrientation((tvOrientation + 90) % 360); route(); });
let rotationTimer;
let rotationSeconds;
function applyDisplaySettings(settings) {
  state.bypassGamesRestriction = Boolean(settings?.bypassGamesRestriction);
  if ($('game-picker').open) renderPicker();
  const seconds = settings?.rotationSeconds || 15;
  if (seconds === rotationSeconds) return;
  rotationSeconds = seconds;
  clearInterval(rotationTimer);
  rotationTimer = setInterval(() => {
    if (!state.paused && !celebrationActive && !document.hidden && !matchMedia('(prefers-reduced-motion: reduce)').matches && !document.querySelector('dialog[open]')) advance();
  }, seconds * 1000);
}
applyDisplaySettings({ rotationSeconds: 15 });

function renderPicker() {
  const normalize = value => value.normalize('NFKD').toLowerCase().replace(/[^a-z0-9]/g, '');
  const query = normalize($('game-search').value);
  const matches = state.games.filter(game => normalize(game.title).includes(query) || normalize(game.id).includes(query));
  $('game-options').replaceChildren(...matches.map(game => {
    const button = node('button', 'game-option'); const image = node('img'); image.src = artworkUrl(game); image.alt = '';
    const info = node('div'); info.append(node('strong', '', game.title), node('small', '', `${scoreText(game)} · ${initialsText(game)}`));
    button.append(image, info);
    button.addEventListener('click', () => { state.pendingGame = null; state.selected = game.id; $('score-input').value = ''; state.requestId = crypto.randomUUID(); renderEntry(); setMessage(); $('game-picker').close(); $('score-input').focus(); });
    return button;
  }));
  if (!matches.length) $('game-options').append(node('p', 'small', state.bypassGamesRestriction ? 'No games in the arcade match. Search the marquee catalog below.' : 'Not in Nick’s arcade yet. Ask Nick or Ron to add this cabinet.'));
  if (state.bypassGamesRestriction && query) renderCatalogSearch('entry', $('game-search').value);
  $('add-game-fields').hidden = !state.bypassGamesRestriction || !query || state.games.some(game => normalize(game.title) === query || normalize(game.id) === query);
  $('add-game').textContent = `Add “${$('game-search').value.trim()}”`;
  $('add-game').disabled = !state.user;
}
$('change-game').addEventListener('click', () => { $('game-search').value = ''; renderPicker(); $('game-picker').showModal(); $('game-search').focus(); });
$('game-search').addEventListener('input', renderPicker);
$('add-game').addEventListener('click', () => {
  if (!state.bypassGamesRestriction) return;
  const title = $('game-search').value.trim();
  if (title.length < 2 || title.length > 80) return;
  state.pendingGame = { id: 'new-game', title, kind: $('new-game-kind').value, image: 'images/new-game.svg', record: null };
  state.selected = 'new-game'; $('score-input').value = ''; state.requestId = crypto.randomUUID();
  renderEntry(); setMessage('Your first score will add this game to the arcade.'); $('game-picker').close(); $('score-input').focus();
});
$('close-picker').addEventListener('click', () => $('game-picker').close());
$('taunt-input').addEventListener('input', () => { state.automaticTaunt = false; state.requestId = crypto.randomUUID(); });
$('score-input').addEventListener('input', () => { state.requestId = crypto.randomUUID(); setMessage(); });

function clearPhoto() {
  $('proof').value = ''; $('photo-preview').hidden = true; $('photo-copy').replaceChildren(document.createTextNode('Add photo '), node('small', '', '(optional)'));
  if (state.objectUrl) URL.revokeObjectURL(state.objectUrl); state.objectUrl = null;
  $('proof-preview').removeAttribute('src');
}
$('proof-preview').addEventListener('error', () => { $('proof-preview').hidden = true; $('photo-copy').textContent = 'Photo selected · ready to upload'; });
$('remove-photo').addEventListener('click', () => { clearPhoto(); state.requestId = crypto.randomUUID(); });
$('proof').addEventListener('change', () => {
  const file = $('proof').files[0]; if (!file) return;
  if (file.size > 40 * 1024 * 1024) { clearPhoto(); setMessage('Choose a photo under 40 MB. Most camera photos work as they are.', true); return; }
  if (file.type && !['image/jpeg', 'image/png', 'image/webp', 'image/heic', 'image/heif', 'image/heic-sequence', 'image/heif-sequence'].includes(file.type) && !/\.(heic|heif|jpe?g|png|webp)$/i.test(file.name)) { clearPhoto(); setMessage('Choose an iPhone HEIC, JPG, PNG or WebP photo.', true); return; }
  if (state.objectUrl) URL.revokeObjectURL(state.objectUrl);
  $('proof-preview').hidden = false; state.objectUrl = URL.createObjectURL(file); $('proof-preview').src = state.objectUrl; $('photo-preview').hidden = false; $('photo-copy').textContent = 'Change proof photo'; state.requestId = crypto.randomUUID(); setMessage();
});
$('score-form').addEventListener('submit', async event => {
  event.preventDefault();
  if (state.posting || !state.user) return;
  if (state.initials.length !== 3) { setMessage('Tap three letters to enter your initials.', true); $('alphabet').querySelector('button').focus(); return; }
  const form = new FormData(); form.set('gameId', state.selected); form.set('score', $('score-input').value.trim()); form.set('initials', state.initials); form.set('taunt', $('taunt-input').value.trim()); form.set('requestId', state.requestId); form.set('automaticTaunt', String(state.automaticTaunt));
  if (state.pendingGame && state.selected === 'new-game') { form.set('gameTitle', state.pendingGame.title); form.set('gameKind', state.pendingGame.kind); if (state.pendingGame.catalogId) form.set('catalogId', state.pendingGame.catalogId); }
  if ($('proof').files[0]) form.set('photo', $('proof').files[0]);
  state.posting = true; renderSession(); $('submit-score').textContent = 'Posting…'; setMessage();
  try {
    const result = await api('/scores', { method: 'POST', body: form });
    if (result.game) { state.selected = result.game.id; state.pendingGame = null; if (!gameById(result.game.id)) { state.allGames.push(result.game); state.games.push(result.game); } }
    $('score-form').hidden = true; $('record-preview').hidden = true; $('success-panel').hidden = false;
    $('success-title').textContent = result.isRecord ? 'NEW HIGH SCORE!' : 'SCORE POSTED!';
    $('success-detail').textContent = `${result.record.initials} · ${result.record.score} on ${gameById(state.selected).title}. ${result.isRecord ? result.game?.showOnLeaderboard === 1 ? 'Your record is on the board.' : 'Your record is saved. This game is hidden from the TV leaderboard; an admin can enable Show on leaderboard in Manage games.' : 'Your score is saved in the game’s history.'}`;
    state.featured = state.selected; state.requestId = crypto.randomUUID(); await refreshBoard(); await refreshAccount();
  } catch (error) { setMessage(error.message, true); }
  finally { state.posting = false; renderSession(); $('submit-score').textContent = 'Post score'; }
});
$('play-again').addEventListener('click', () => { $('success-panel').hidden = true; $('score-form').hidden = false; $('record-preview').hidden = false; $('score-input').value = ''; state.initials = state.account?.initials || ''; applySavedTaunt(); renderInitials(); clearPhoto(); setMessage(); $('score-input').focus(); });

const observeRecords = ArcadeCelebrations.createObserver();
const celebrationQueue = [];
let celebrationTimer, celebrationActive = false, boardRefreshing = null, boardRefreshAgain = false;
function closeCelebration(clearQueue = false) {
  clearTimeout(celebrationTimer); celebrationActive = false;
  $('record-celebration').hidden = true;
  if (clearQueue) celebrationQueue.length = 0;
  else showNextCelebration();
}
function showNextCelebration() {
  if (celebrationActive || !celebrationQueue.length) return;
  if ($('display-panel').hidden || document.hidden || document.querySelector('dialog[open]')) { celebrationQueue.length = 0; return; }
  const game = celebrationQueue.shift(), record = game.record;
  celebrationActive = true;
  $('celebration-heading').textContent = game.kind === 'time' ? 'NEW RECORD TIME!' : 'NEW HIGH SCORE!';
  $('celebration-art').src = artworkUrl(game); $('celebration-art').alt = `${game.title} marquee`;
  $('celebration-game').textContent = game.title;
  $('celebration-score').textContent = record.score;
  $('celebration-score').classList.toggle('long', record.score.length > 9);
  $('celebration-initials').textContent = record.initials; renderImprovement('celebration-improvement', record);
  $('celebration-taunt').textContent = record.taunt || ''; $('celebration-taunt').hidden = !record.taunt;
  $('record-celebration').hidden = false;
  celebrationTimer = setTimeout(() => closeCelebration(), 10000);
}
$('dismiss-celebration').addEventListener('click', () => closeCelebration());
window.addEventListener('hashchange', () => closeCelebration(true));
document.addEventListener('visibilitychange', () => { if (document.hidden) closeCelebration(true); });

// A mutation arriving during a poll needs a subsequent request, not the old response.
function refreshBoard() {
  boardRefreshAgain = true;
  if (boardRefreshing) return boardRefreshing;
  boardRefreshing = (async () => {
    do { boardRefreshAgain = false; await fetchBoard(); } while (boardRefreshAgain);
  })().finally(() => { boardRefreshing = null; });
  return boardRefreshing;
}

function renderAdminGameOptions() {
  const select = $('admin-game'), previous = select.value;
  const games = [...state.allGames].sort((a, b) => a.title.localeCompare(b.title, undefined, {numeric:true, sensitivity:'base'}));
  // Do not replace native options on every poll while an operator is choosing.
  const signature = JSON.stringify(games.map(game => [game.id, game.title]));
  if (select.dataset.games === signature) return;
  select.replaceChildren(...games.map(game => { const option = node('option', '', game.title); option.value = game.id; return option; }));
  select.dataset.games = signature;
  select.value = games.some(game => game.id === previous) ? previous : games.some(game => game.id === state.selected) ? state.selected : games[0]?.id || '';
}

async function fetchBoard() {
  try {
    const result = await api('/leaderboard');
    const visibleGames = result.games.filter(game => game.eligible !== 0 || result.displaySettings?.bypassGamesRestriction);
    const boardGames = visibleGames.filter(game => game.showOnLeaderboard === 1);
    const celebrations = observeRecords({...result, games:boardGames});
    if (!$('display-panel').hidden && !document.hidden && !document.querySelector('dialog[open]')) celebrationQueue.push(...celebrations.slice(0, 5 - celebrationQueue.length));
    state.allGames = result.games; state.games = visibleGames; state.boardGames = boardGames;
    if (!state.games.some(game => game.id === state.selected) && !state.pendingGame) state.selected = state.games[0]?.id;
    state.connected = true; applyDisplaySettings(result.displaySettings);
    renderAdminGameOptions();
    $('connection').hidden = true; renderBoard(); renderEntry(); if ($('games-dialog').open) renderArcadeGames(); showNextCelebration();
  } catch (error) {
    state.connected = false; $('connection').hidden = false;
    $('connection').textContent = state.games.length ? 'Connection lost · showing the last received records. Reconnecting…' : 'The scoreboard service is unavailable. Please check the connection.';
  }
}
setInterval(() => { if (!document.hidden) refreshBoard(); }, 5000);
window.addEventListener('online', refreshBoard);
document.addEventListener('visibilitychange', () => { if (!document.hidden) refreshBoard(); });

$('admin-link').addEventListener('click', () => { $('admin-game').value = state.selected; location.hash = '#admin'; });
$('tv-admin-button').addEventListener('click', async () => {
  if (!state.user?.admin) return;
  if (document.fullscreenElement) await document.exitFullscreen();
  $('admin-game').value = state.featured; location.hash = '#admin';
});
$('admin-game').addEventListener('change', () => { $('admin-search').value = ''; $('admin-feedback').textContent = ''; loadAdmin(); });
$('admin-search').addEventListener('input', renderAdminScores);
$('admin-show-removed').addEventListener('change', renderAdminScores);
let adminScores = [];
let adminLoad = 0;
function renderAdminScores() {
  if (!state.user?.admin) { $('admin-list').replaceChildren(); return; }
  const query = $('admin-search').value.trim().toLowerCase();
  const scores = adminScores.filter(score => ($('admin-show-removed').checked || !score.deleted) && `${score.initials} ${score.email} ${score.score}`.toLowerCase().includes(query));
  const game = gameById($('admin-game').value);
  $('admin-list').replaceChildren(...scores.map(score => {
    const row = node('article', `admin-score${score.deleted ? ' removed' : ''}`);
    const status = score.deleted ? 'Removed' : score.id === game?.record?.id ? 'Current record' : 'Score history';
    row.append(node('span','admin-score-status',status), node('div','record',`${score.score} · ${score.initials}`));
    row.append(node('p','',score.email),node('p','small',score.createdAt ? new Date(score.createdAt*1000).toLocaleString() : 'Imported arcade record'));
    if (score.taunt) row.append(node('blockquote','',score.taunt));
    if (!score.deleted) {
      const actions = node('div','admin-actions');
      for (const [label, action] of [['Edit score','edit'],['Remove score','delete']]) {
        const button = node('button', action === 'delete' ? 'secondary danger' : 'secondary',label);
        button.setAttribute('aria-label', `${label}: ${score.initials}, ${score.score}`);
        button.addEventListener('click',()=>openEdit(score,action));actions.append(button);
      }
      if(score.hasPhoto){const proof=node('button','text-button','View proof photo');proof.addEventListener('click',()=>showPhoto(score.photoId));actions.append(proof);}
      row.append(actions);
    }
    return row;
  }));
  $('admin-message').textContent = `${scores.length} shown · ${adminScores.filter(s=>!s.deleted).length} active · ${adminScores.filter(s=>s.deleted).length} removed (latest 200)`;
  if (!scores.length) {
    const empty = node('div', 'admin-empty');
    empty.append(node('p', '', query ? 'No matching submissions. Try different initials, an email or a score.' : adminScores.length ? 'No active scores. Tick Show removed entries to view previously removed submissions.' : 'This game has no saved score yet. The blank scoreboard is an empty game, not an incomplete submission. There is no score to edit or remove.'));
    if (!query && !game?.record) {
      const add = node('button', 'primary', 'Enter the first score');
      add.addEventListener('click', () => {
        state.pendingGame = null; state.selected = game.id; state.requestId = crypto.randomUUID();
        $('score-input').value = ''; $('score-form').hidden = false; $('record-preview').hidden = false; $('success-panel').hidden = true;
        clearPhoto(); applySavedTaunt(); renderEntry(); setMessage('Enter the score and three initials, then choose Post score to save it.'); location.hash = '#play';
      });
      empty.append(add);
    }
    $('admin-list').append(empty);
  }
}

function renderRecordHistory(history, untracked) {
  $('record-history-note').textContent = 'Newest first · Scores and initials as originally entered. Corrections and removals are labeled.' + (untracked ? ` ${untracked} older submission${untracked === 1 ? '' : 's'} predate record tracking; their record status is unknown.` : '');
  $('record-history-list').replaceChildren(...history.map(entry => {
    const item = node('li', 'record-history-item');
    item.append(node('span', 'admin-score-status', entry.imported ? 'Imported starting record' : 'New record'));
    item.append(node('strong', 'record-history-score', `${entry.score} · ${entry.initials}`));
    item.append(node('p', 'small', entry.email ? `${entry.imported ? 'Linked player' : 'Submitted by'}: ${entry.email}` : 'Original player account not recorded'));
    const date = node('time', 'small', entry.createdAt ? new Date(entry.createdAt * 1000).toLocaleString() : 'Original date not recorded');
    if (entry.createdAt) date.dateTime = new Date(entry.createdAt * 1000).toISOString();
    item.append(date);
    if (entry.corrected || entry.deleted) item.append(node('p', 'history-change', [entry.corrected ? 'Later corrected by an admin' : '', entry.deleted ? 'Removed from the scoreboard' : ''].filter(Boolean).join(' · ')));
    return item;
  }));
  if (!history.length) $('record-history-list').append(node('li', 'small', 'No recorded milestones yet. The first new record will appear here.'));
}

async function loadAdmin() {
  if (!state.user?.admin) return;
  const requestNumber = ++adminLoad, token = state.token;
  const gameId = $('admin-game').value || state.selected, game = gameById(gameId);
  adminScores = []; $('admin-list').replaceChildren(); $('record-history-list').replaceChildren(); $('record-history-note').textContent = 'Loading record history…';
  $('admin-message').textContent = 'Loading submissions…';
  $('admin-game-title').textContent = game?.title || 'Choose a game';
  $('admin-marquee').src = game ? artworkUrl(game) : 'images/new-game.svg';
  $('admin-marquee').alt = game ? `${game.title} marquee` : '';
  $('admin-current-record').textContent = game?.record ? `Record to beat: ${game.record.score} · ${game.record.initials}` : 'No current record';
  try {
    const {scores, recordHistory = [], untrackedSubmissions = 0} = await api(`/admin/scores?gameId=${encodeURIComponent(gameId)}`);
    if (requestNumber !== adminLoad || token !== state.token || !state.user?.admin) return;
    adminScores = scores; renderAdminScores(); renderRecordHistory(recordHistory, untrackedSubmissions);
  } catch (error) { if (requestNumber === adminLoad && token === state.token) { $('admin-message').textContent = error.message; $('record-history-note').textContent = 'Record history could not be loaded. Try choosing the game again.'; } }
}
function openEdit(score, action) {
  state.editing = { score, action }; $('edit-heading').textContent = action === 'delete' ? 'REMOVE SCORE?' : 'CORRECT SCORE';
  $('edit-summary').textContent = action === 'delete' ? `Remove ${score.score} by ${score.initials} from ${gameById($('admin-game').value)?.title}? The best remaining score will appear on the board. The removal is kept in the admin history.` : `Editing ${score.initials} · ${score.score} on ${gameById($('admin-game').value)?.title}. Changes are recorded in admin history.`;
  $('edit-taunt').hidden = action === 'delete'; $('edit-taunt-label').hidden = action === 'delete'; $('edit-taunt').value = score.taunt || '';
  $('edit-fields').hidden = action === 'delete'; $('edit-score').disabled = action === 'delete'; $('edit-initials').disabled = action === 'delete';
  $('edit-time-hint').hidden = action === 'delete' || gameById($('admin-game').value)?.kind !== 'time';
  $('edit-score').value = score.score; $('edit-initials').value = score.initials; $('edit-message').textContent = '';
  $('save-edit').textContent = action === 'delete' ? 'Remove score' : 'Save correction'; $('edit-dialog').showModal();
}
$('cancel-edit').addEventListener('click', () => $('edit-dialog').close());
$('close-edit').addEventListener('click', () => $('edit-dialog').close());
$('edit-form').addEventListener('submit', async event => {
  event.preventDefault(); const { score, action } = state.editing; $('save-edit').disabled = true;
  try {
    await api(`/admin/scores/${score.id}`, { method: action === 'delete' ? 'DELETE' : 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ revision: score.revision, score: $('edit-score').value, initials: $('edit-initials').value, taunt: $('edit-taunt').value }) });
    $('edit-dialog').close(); await refreshBoard(); await loadAdmin(); $('admin-feedback').textContent = action === 'delete' ? 'Score removed. The scoreboard has been updated.' : `Correction saved: ${adminScores.find(item => item.id === score.id)?.score || 'score updated'}. The scoreboard is up to date.`;
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


async function refreshAccount() {
  if (!state.user) return;
  const token = state.token;
  try {
    const result = await api('/account');
    if (state.token !== token) return;
    state.account = result;
    for (const [button, badge] of [['account-button', 'unread-count'], ['tv-account-button', 'tv-unread-count'], ['display-menu-toggle', 'menu-unread-count']]) {
      $(badge).textContent = result.unread > 99 ? '99+' : String(result.unread);
      $(badge).hidden = !result.unread;
      const label = button === 'display-menu-toggle' ? 'Scoreboard menu' : 'My account';
      $(button).setAttribute('aria-label', result.unread ? `${label}, ${result.unread} unread notifications` : label);
    }
  } catch (_) { /* Keep entry usable during temporary notification outages. */ }
}
function accountSection(view) {
  state.accountView = view;
  for (const [name, id] of [['activity','show-activity'], ['my-scores','show-my-scores'], ['settings','show-settings']]) {
    $(name + '-section').hidden = name !== view;
    $(id).setAttribute('aria-pressed', String(name === view));
  }
}
function accountArtwork(title) {
  const game = state.allGames.find(game => game.title === title) || {title};
  const artwork = node('img', 'my-score-artwork');
  artwork.src = artworkUrl(game); artwork.alt = `${title} marquee`; artwork.loading = 'lazy';
  artwork.addEventListener('error', () => { artwork.hidden = true; }, {once:true});
  return artwork;
}
async function loadAccount(view = state.accountView) {
  if (!state.user) return;
  accountSection(view); $('account-message').textContent = 'Loading…';
  const token = state.token;
  try {
    if (view === 'activity') {
      const result = await api('/activity'); if (token !== state.token) return;
      state.latestEvent = result.latestId;
      $('activity-list').replaceChildren(...result.events.map(event => {
        const card = node('article', `activity-card${event.unread ? ' unread' : ''}`);
        const title = event.yourRecordBroken ? 'YOUR RECORD WAS BROKEN!' : event.isRecord ? (event.previousScore ? 'NEW RECORD!' : 'FIRST RECORD!') : 'SCORE POSTED';
        card.append(accountArtwork(event.gameTitle));
        card.append(node('strong', 'activity-title', title), node('h4', '', event.gameTitle), node('p', '', `${event.initials} · ${event.score}`));
        if (event.isRecord && event.previousScore) card.append(node('p', 'small', `Previous record: ${event.previousInitials} · ${event.previousScore}`));
        if (event.taunt) card.append(node('blockquote', '', event.taunt));
        card.append(node('p', 'small', new Date(event.createdAt * 1000).toLocaleString() + (event.corrected ? ' · Score corrected by admin' : '')));
        return card;
      }));
      if (!result.events.length) $('activity-list').append(node('p', '', 'Quiet for now. The next score starts the action!'));
      $('mark-read').disabled = !result.events.length;
    } else {
      const account = await api('/account'); if (token !== state.token) return; state.account = account;
      if (view === 'settings') { $('default-initials').value = account.initials; $('default-taunt').value = account.defaultTaunt || ''; $('taunt-enabled').checked = Boolean(account.tauntEnabled); $('display-settings-form').hidden = !state.user.admin; $('rotation-seconds').value = account.displaySettings.rotationSeconds; $('bypass-games-restriction').checked = Boolean(account.displaySettings.bypassGamesRestriction); $('display-settings-message').textContent = ''; }
      else {
        const visibleScores = account.scores.filter(score => !score.deleted);
        $('my-scores-list').replaceChildren(...visibleScores.map(score => {
          const card = node('article','activity-card my-score-card');
          card.append(accountArtwork(score.gameTitle));
          card.append(node('h4','',score.gameTitle), node('p','my-score-value',`${score.initials} · ${score.score}`), node('strong','small',score.deleted ? 'Removed by admin' : score.isRecord ? 'Current record holder' : 'Saved in game history'));
          card.append(node('p', 'small', score.createdAt ? `Submitted ${new Date(score.createdAt * 1000).toLocaleString()}` : 'Imported arcade record · date unknown'));
          if (score.taunt) card.append(node('blockquote','',score.taunt));
          if (score.hasPhoto && !score.deleted) { const button=node('button','text-button','View my photo'); button.addEventListener('click',()=>showPhoto(score.photoId)); card.append(button); }
          return card;
        }));
        if (!visibleScores.length) $('my-scores-list').append(node('p','','Your first score is waiting. Go claim a spot!'));
      }
    }
    $('account-message').textContent = ''; await refreshAccount();
  } catch (error) { $('account-message').textContent = error.message; }
}
function openAccount() {
  if (!state.user) { state.accountSignIn = true; location.hash = '#play'; route(); $('login-panel').scrollIntoView({ block: 'start' }); setMessage('Sign in with Google to open your account, scores and settings.'); return; }
  $('account-identity').textContent = `${state.user.email} · ${state.user.admin ? 'Arcade admin' : 'Player'}`;
  $('account-dialog').showModal(); loadAccount();
}
$('account-button').addEventListener('click', openAccount);
$('tv-settings-button').addEventListener('click', async () => {
  if (document.fullscreenElement) await document.exitFullscreen();
  $('display-menu').open = false;
  state.accountView = 'settings';
  openAccount();
});
$('tv-account-button').addEventListener('click', async () => {
  if (document.fullscreenElement) await document.exitFullscreen();
  openAccount();
});
document.querySelector('.display-menu-items a').addEventListener('click', async event => {
  if (document.fullscreenElement) { event.preventDefault(); await document.exitFullscreen(); location.hash = '#play'; }
});
$('close-account').addEventListener('click', () => $('account-dialog').close());
for (const [id, view] of [['show-activity','activity'],['show-my-scores','my-scores'],['show-settings','settings']]) $(id).addEventListener('click', () => loadAccount(view));
$('account-admin').addEventListener('click', () => { $('admin-game').value = state.selected; $('account-dialog').close(); });
$('mark-read').addEventListener('click', async () => {
  try { await api('/activity/read', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({throughId:state.latestEvent})}); await loadAccount('activity'); }
  catch(error) { $('account-message').textContent=error.message; }
});
$('display-settings-form').addEventListener('submit', async event => {
  event.preventDefault(); $('save-display-settings').disabled = true;
  try {
    const result = await api('/admin/display-settings', { method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ rotationSeconds: Number($('rotation-seconds').value), bypassGamesRestriction: $('bypass-games-restriction').checked }) });
    applyDisplaySettings(result.displaySettings);
    await refreshBoard();
    $('display-settings-message').textContent = `${result.displaySettings.bypassGamesRestriction ? 'Open game submissions enabled.' : 'Only Nick’s arcade games can accept scores.'} Saved: ${result.displaySettings.rotationSeconds} seconds per game. Open scoreboards pick this up within five seconds. Paused boards stay paused.`;
  } catch (error) { $('display-settings-message').textContent = error.message; }
  finally { $('save-display-settings').disabled = false; }
});
$('settings-form').addEventListener('submit', async event => {
  event.preventDefault();
  try { await api('/account',{method:'PATCH',headers:{'Content-Type':'application/json'},body:JSON.stringify({initials:$('default-initials').value})}); await refreshAccount(); $('account-message').textContent='Default initials saved.'; }
  catch(error) { $('account-message').textContent=error.message; }
});
setInterval(() => { if (!document.hidden && state.user) { refreshAccount(); if ($('account-dialog').open && state.accountView === 'activity') loadAccount('activity'); } }, 15000);

async function init() {
  route();
  try {
    state.config = await api('/config');
    $('preview-note').hidden = !state.config.demo;
    new ResizeObserver(() => document.documentElement.style.setProperty('--preview-height', `${$('preview-note').getBoundingClientRect().height}px`)).observe($('preview-note'));
    const submitUrl = new URL(state.config.publicUrl); submitUrl.hash = 'play';
    $('qr-link').href = submitUrl.toString();
    // Both clicking and scanning the QR open score entry.
    $('qr-link').addEventListener('click', event => { event.preventDefault(); state.accountSignIn = false; location.hash = '#play'; });
    await ArcadeQR.toCanvas($('qr-code'), submitUrl.toString(), { width: 240, margin: 1, errorCorrectionLevel: 'M', color: { dark: '#071418', light: '#ffffff' } });
    await refreshBoard();
    renderAdminGameOptions();
    loadGoogle();
    let savedToken='';
    try { savedToken=localStorage.getItem('arcade_session')||''; } catch (_) {}
    if(!savedToken)try { savedToken=sessionStorage.getItem('arcade_session')||''; } catch (_) {}
    if(savedToken)try { await signIn(savedToken,{goToBoard:false,restore:true}); } catch(error) { if(error.status===401)signOut(false);else {state.token='';state.user=null;setMessage('Your saved sign-in could not be checked. Please reload when the connection returns.',true);} }
    renderSession(); route();
  } catch (error) { $('connection').hidden = false; $('connection').textContent = error.message; $('login-help').textContent = 'The score service must be connected before sign-in is available.'; }
}
init();

$('taunt-settings-form').addEventListener('submit', async event => {
  event.preventDefault();
  const button = $('save-taunt-settings'); button.disabled = true;
  try {
    await api('/account', {method:'PATCH', headers:{'Content-Type':'application/json'}, body:JSON.stringify({defaultTaunt:$('default-taunt').value, tauntEnabled:$('taunt-enabled').checked})});
    await refreshAccount(); applySavedTaunt();
    $('account-message').textContent = state.account.tauntEnabled ? 'Taunt saved and enabled for record breaks.' : 'Taunt saved. Automatic taunts are off.';
  } catch (error) { $('account-message').textContent = error.message; }
  finally { button.disabled = false; }
});

// Native disclosure keeps the control list keyboard accessible without menu-role shortcuts.
$('display-menu').addEventListener('click', event => {
  if (event.target.closest('.display-menu-items button, .display-menu-items a')) $('display-menu').open = false;
});
document.addEventListener('click', event => {
  if (!event.target.closest('#display-menu')) $('display-menu').open = false;
});
document.addEventListener('keydown', event => {
  if (event.key === 'Escape' && $('display-menu').open) {
    $('display-menu').open = false; $('display-menu-toggle').focus();
  }
});


function renderArcadeGames() {
  if (!state.user?.admin) return;
  const query = $('arcade-games-search').value.trim().toLowerCase();
  const games = state.allGames.filter(game => game.title.toLowerCase().includes(query) && (!$('games-open-only').checked || !game.record));
  $('games-count').textContent = `${state.allGames.filter(game => game.eligible).length} games in Nick’s arcade · ${state.allGames.filter(game => game.eligible && !game.record).length} waiting for a first score`;
  $('arcade-games-list').replaceChildren(...games.map(game => {
    const card = node('article', 'arcade-game-card');
    const art = node('img'); art.src = artworkUrl(game); art.alt = `${game.title} artwork`; art.loading = 'lazy';
    const info = node('div', 'arcade-game-info'); info.append(node('h3', '', game.title), node('p', game.record ? 'small' : 'open-record-label', game.record ? `${game.record.score} · ${game.record.initials}` : 'FIRST SCORE WANTED'));
    const visibility = node('label', 'admin-removed-toggle');
    const checkbox = node('input'); checkbox.type = 'checkbox'; checkbox.checked = game.showOnLeaderboard === 1;
    checkbox.setAttribute('aria-label', `Show ${game.title} on leaderboard`);
    visibility.append(checkbox, document.createTextNode('Show on leaderboard')); info.append(visibility);
    checkbox.addEventListener('change', async () => {
      checkbox.disabled = true;
      try { await api(`/admin/games/${encodeURIComponent(game.id)}/leaderboard`, {method:'PATCH', headers:{'Content-Type':'application/json'}, body:JSON.stringify({showOnLeaderboard:checkbox.checked})}); await refreshBoard(); }
      catch (error) { checkbox.checked = game.showOnLeaderboard === 1; checkbox.disabled = false; $('games-feedback').textContent = error.message; }
    });
    const view = node('button', 'secondary', 'Show on TV');
    view.addEventListener('click', () => { $('games-dialog').close(); feature(game.id); location.hash = '#tv'; });
    const manage = node('button', 'secondary', game.record ? 'Manage scores' : 'Enter first score');
    manage.addEventListener('click', () => {
      $('games-dialog').close();
      if (game.record) { $('admin-game').value = game.id; if (location.hash === '#admin') loadAdmin(); else location.hash = '#admin'; }
      else { state.pendingGame = null; state.selected = game.id; state.requestId = crypto.randomUUID(); $('score-input').value = ''; clearPhoto(); applySavedTaunt(); $('score-form').hidden = false; $('record-preview').hidden = false; $('success-panel').hidden = true; renderEntry(); setMessage(); location.hash = '#play'; }
    });
    const eligibility = node('button', game.eligible ? 'secondary arcade-remove' : 'secondary', game.eligible ? 'Remove from arcade' : 'Add to Nick’s arcade');
    eligibility.addEventListener('click', async () => {
      eligibility.disabled = true;
      try { await api(`/admin/games/${encodeURIComponent(game.id)}`, {method:'PATCH', headers:{'Content-Type':'application/json'}, body:JSON.stringify({eligible:!game.eligible})}); await refreshBoard(); $('games-feedback').textContent = game.eligible ? `${game.title} removed from the eligible list. Score history is preserved.` : `${game.title} added to Nick’s arcade.`; }
      catch (error) { $('games-feedback').textContent = error.message; eligibility.disabled = false; }
    });
    if (!game.eligible) info.append(node('p', 'small', 'Outside Nick’s arcade'));
    view.hidden = !game.showOnLeaderboard || (!game.eligible && !state.bypassGamesRestriction);
    manage.hidden = !game.record && !game.eligible && !state.bypassGamesRestriction;
    const changeArt = node('button', 'secondary', game.marqueeId ? 'Change marquee' : 'Upload marquee');
    changeArt.addEventListener('click', () => openMarquee(game));
    if (game.marqueeId) info.append(node('p', 'small', 'Custom marquee'));
    const actions = node('div', 'arcade-game-actions');
    actions.setAttribute('role', 'group'); actions.setAttribute('aria-label', `${game.title} actions`);
    const assign = node('button', 'secondary', 'Assigned cabinets');
    assign.addEventListener('click', () => openCabinetAssignment(game));
    const rename = node('button', 'secondary', 'Edit name');
    rename.addEventListener('click', () => openGameName(game));
    actions.append(view, manage, rename, changeArt, assign, eligibility); card.append(art, info, actions); return card;
  }));
  if (!games.length) $('arcade-games-list').append(node('p', 'admin-empty', 'No games match this filter.'));
}
async function openArcadeGames() {
  if (!state.user?.admin) return;
  if (document.fullscreenElement) await document.exitFullscreen();
  $('account-dialog').close(); $('games-feedback').textContent = ''; renderArcadeGames(); $('games-dialog').showModal(); renderCatalogSearch('admin', $('catalog-search').value);
}
$('tv-games-button').addEventListener('click', openArcadeGames);
$('account-games').addEventListener('click', openArcadeGames);
$('close-games').addEventListener('click', () => $('games-dialog').close());
$('arcade-games-search').addEventListener('input', renderArcadeGames);
$('games-open-only').addEventListener('change', renderArcadeGames);
$('admin-add-game').addEventListener('submit', async event => {
  event.preventDefault(); if (!state.user?.admin) return;
  $('save-arcade-game').disabled = true;
  try {
    const result = await api('/admin/games', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({title:$('admin-game-title-input').value,kind:$('admin-game-kind').value})});
    await refreshBoard();
    $('games-feedback').textContent = result.alreadyExists ? `${result.game.title} is already in your arcade.` : `${result.game.title} added and ready for its first score. Enable Show on leaderboard to include it on the TV.`;
    $('admin-game-title-input').value = ''; $('arcade-games-search').value = ''; renderArcadeGames();
  } catch (error) { $('games-feedback').textContent = error.message; }
  finally { $('save-arcade-game').disabled = false; }
});

let catalogSearchVersion = {admin:0, entry:0};
async function renderCatalogSearch(mode, query) {
  const version = ++catalogSearchVersion[mode];
  const target = mode === 'admin' ? $('catalog-results') : $('game-options');
  if (mode === 'admin') { target.replaceChildren(); $('catalog-status').textContent = 'Searching marquees…'; }
  try {
    const result = await api(`/game-catalog?q=${encodeURIComponent(query)}`);
    if (version !== catalogSearchVersion[mode] || (mode === 'entry' && (!state.bypassGamesRestriction || $('game-search').value !== query))) return;
    if (mode === 'admin') $('catalog-status').textContent = `${result.total.toLocaleString()} matches${result.total > 40 ? ' · Showing the first 40. Keep typing to narrow the list.' : ''}`;
    for (const game of result.games) {
      if (mode === 'entry' && state.games.some(owned => owned.title === game.title)) continue;
      const button = node('button', 'game-option'); button.type = 'button';
      const image = node('img'); image.src = artworkUrl(game); image.alt = ''; image.loading = 'lazy';
      image.onerror = () => { image.onerror = null; image.src = 'images/new-game.svg'; };
      const info = node('div'); info.append(node('strong', '', game.title), node('small', '', mode === 'admin' ? (game.inArcade ? 'Already in Nick’s arcade' : 'Add to Nick’s arcade') : 'Choose this game'));
      if (!game.marqueeId && ArcadeArtwork.resolve(game) === 'images/new-game.svg') info.append(node('small', '', 'Marquee unavailable'));
      button.append(image, info); button.disabled = mode === 'admin' && game.inArcade;
      button.addEventListener('click', async () => {
        if (mode === 'entry') {
          state.pendingGame = {...game, id:'new-game', catalogId:game.id, record:null}; state.selected = 'new-game'; state.requestId = crypto.randomUUID(); $('score-input').value = ''; renderEntry(); setMessage('Open submissions are enabled. Set the first score for this game.'); $('game-picker').close(); return;
        }
        button.disabled = true;
        try {
          const added = await api('/admin/games', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({catalogId:game.id})});
          await refreshBoard(); $('games-feedback').textContent = `${added.game.title} is in Nick’s arcade and ready for scores.`; renderCatalogSearch('admin', $('catalog-search').value);
        } catch (error) { $('games-feedback').textContent = error.message; button.disabled = false; }
      });
      target.append(button);
    }
  } catch (error) { if (mode === 'admin' && version === catalogSearchVersion.admin) $('catalog-status').textContent = error.message; }
}
let catalogSearchTimer;
$('catalog-search').addEventListener('input', () => { ++catalogSearchVersion.admin; clearTimeout(catalogSearchTimer); catalogSearchTimer = setTimeout(() => renderCatalogSearch('admin', $('catalog-search').value), 200); });

document.addEventListener('error', event => { const image = event.target; if (image instanceof HTMLImageElement && !image.src.endsWith('/images/new-game.svg')) image.src = 'images/new-game.svg'; }, true);


let marqueeGame = null;
let marqueePreviewUrl = null;
let marqueeBusy = false;
function clearMarqueePreview() {
  if (marqueePreviewUrl) URL.revokeObjectURL(marqueePreviewUrl);
  marqueePreviewUrl = null;
}
function openMarquee(game) {
  if (!state.user?.admin) return;
  marqueeGame = {...game}; clearMarqueePreview();
  $('marquee-heading').textContent = `${game.title} artwork`;
  $('marquee-file').value = ''; $('marquee-message').textContent = '';
  $('marquee-preview').hidden = false; $('marquee-preview').src = artworkUrl(game);
  $('marquee-preview').alt = `${game.title} marquee preview`;
  $('marquee-save').disabled = true; $('marquee-reset').hidden = !game.marqueeId;
  $('marquee-dialog').showModal();
}
$('marquee-file').addEventListener('change', () => {
  clearMarqueePreview(); const file = $('marquee-file').files[0];
  $('marquee-message').textContent = ''; $('marquee-save').disabled = !file;
  if (!file) { $('marquee-preview').hidden = false; $('marquee-preview').src = artworkUrl(marqueeGame); return; }
  if (file.size > 40 * 1024 * 1024) { $('marquee-message').textContent = 'Choose an image under 40 MB.'; $('marquee-save').disabled = true; return; }
  marqueePreviewUrl = URL.createObjectURL(file);
  $('marquee-preview').hidden = false; $('marquee-preview').src = marqueePreviewUrl;
});
$('marquee-preview').addEventListener('error', () => {
  $('marquee-preview').hidden = true;
  $('marquee-message').textContent = 'Preview unavailable on this device. You can still upload an iPhone HEIC image.';
});
$('close-marquee').addEventListener('click', () => { if (!marqueeBusy) $('marquee-dialog').close(); });
$('marquee-dialog').addEventListener('cancel', event => { if (marqueeBusy) event.preventDefault(); });
$('marquee-dialog').addEventListener('close', clearMarqueePreview);
async function saveMarquee(reset = false) {
  if (!marqueeGame || !state.user?.admin || marqueeBusy) return;
  marqueeBusy = true;
  for (const id of ['marquee-save','marquee-reset','marquee-file','close-marquee']) $(id).disabled = true;
  $('marquee-message').textContent = reset ? 'Restoring default artwork…' : 'Uploading marquee…';
  try {
    let options;
    if (reset) options = {method:'DELETE',headers:{'Content-Type':'application/json'},body:JSON.stringify({expectedMarqueeId:marqueeGame.marqueeId || ''})};
    else {
      const body = new FormData(); body.set('marquee', $('marquee-file').files[0]); body.set('expectedMarqueeId',marqueeGame.marqueeId || '');
      options = {method:'POST',body};
    }
    await api(`/admin/games/${encodeURIComponent(marqueeGame.id)}/marquee`,options);
    await refreshBoard();
    $('games-feedback').textContent = reset ? `${marqueeGame.title}: default artwork restored.` : `${marqueeGame.title}: uploaded marquee is now used throughout the arcade.`;
    $('marquee-dialog').close();
  } catch(error) { $('marquee-message').textContent = error.message; }
  finally {
    marqueeBusy = false;
    for (const id of ['marquee-reset','marquee-file','close-marquee']) $(id).disabled = false;
    $('marquee-save').disabled = !$('marquee-file').files.length;
  }
}
$('marquee-form').addEventListener('submit', event => { event.preventDefault(); saveMarquee(); });
$('marquee-reset').addEventListener('click', () => saveMarquee(true));

let renamingGame=null;
function openGameName(game){
  renamingGame={id:game.id,title:game.title};
  $('game-name-input').value=game.title;$('game-name-message').textContent='';
  $('game-name-dialog').showModal();$('game-name-input').focus();
}
$('cancel-game-name').addEventListener('click',()=>$('game-name-dialog').close());
$('game-name-dialog').addEventListener('cancel',event=>{if($('save-game-name').disabled)event.preventDefault();});
$('game-name-form').addEventListener('submit',async event=>{
  event.preventDefault();if(!state.user?.admin||!renamingGame)return;
  $('save-game-name').disabled=true;$('cancel-game-name').disabled=true;
  try{
    const result=await api(`/admin/games/${encodeURIComponent(renamingGame.id)}/name`,{method:'PATCH',headers:{'Content-Type':'application/json'},body:JSON.stringify({title:$('game-name-input').value,expectedTitle:renamingGame.title})});
    $('game-name-dialog').close();$('arcade-games-search').value='';await refreshBoard();
    $('games-feedback').textContent=`Game renamed to ${result.title}. Scores and cabinet assignments were kept.`;
  }catch(error){$('game-name-message').textContent=error.message;}
  finally{$('save-game-name').disabled=false;$('cancel-game-name').disabled=false;}
});

window.addEventListener('storage',event=>{if(event.key==='arcade_session'&&!event.newValue&&state.user){try{if(!localStorage.getItem('arcade_session'))signOut(false);}catch(_){}}});

const artworkWarmCache=new Map();
function warmArtwork(urls){
  for(const url of urls){if(artworkWarmCache.has(url))continue;const image=new Image();image.src=url;artworkWarmCache.set(url,image);if(artworkWarmCache.size>100)artworkWarmCache.delete(artworkWarmCache.keys().next().value);}
}
