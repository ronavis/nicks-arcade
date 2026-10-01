// Read-only audit of every game returned by an arcade API, using the built resolver.
// Usage: npm run audit:artwork -- http://127.0.0.1:4174 [https://frontend/base/]
import { readFile } from 'node:fs/promises';
import vm from 'node:vm';

const api = process.argv[2];
if (!api) throw new Error('Provide the API origin to audit. Run npm run build first.');
const site = process.argv[3] || api;
const context = { window: {} };
vm.createContext(context);
vm.runInContext(await readFile(new URL('../dist/artwork-catalog.js', import.meta.url), 'utf8'), context);
vm.runInContext(await readFile(new URL('../artwork.js', import.meta.url), 'utf8'), context);
const response = await fetch(`${api.replace(/\/$/, '')}/api/leaderboard`);
if (!response.ok) throw new Error(`Leaderboard HTTP ${response.status}`);
const { games } = await response.json();
const results = [];
for (const game of games) {
  const image = game.marqueeId ? `${api.replace(/\/$/, '')}/api/marquees/${game.marqueeId}` : context.window.ArcadeArtwork.resolve(game);
  let status = 'ok';
  if (image === 'images/new-game.svg') status = 'placeholder';
  else {
    try {
      const res = await fetch(new URL(image, site.replace(/\/$/, '') + '/'), { signal: AbortSignal.timeout(15000) });
      if (!res.ok || !res.headers.get('content-type')?.startsWith('image/')) status = `failed: HTTP ${res.status}`;
      else if (!(await res.arrayBuffer()).byteLength) status = 'failed: empty image';
    } catch (error) { status = `failed: ${error.message}`; }
  }
  results.push({ title: game.title, image, status });
}
console.log(JSON.stringify({ total: results.length, ok: results.filter(r => r.status === 'ok').length, results }, null, 2));
if (results.some(r => r.status !== 'ok')) process.exitCode = 1;
