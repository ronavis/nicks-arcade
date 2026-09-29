import { mkdir, copyFile, readFile, writeFile, rm, cp } from 'node:fs/promises';
import { build } from 'esbuild';
const out = new URL('../dist/', import.meta.url);
await rm(out, { recursive: true, force: true });
await mkdir(new URL('vendor/', out), { recursive: true });
for (const name of ['index.html', 'main.css', 'app.js', 'config.js', 'favicon.ico', 'favicon-harry.png', 'apple-touch-icon.png']) {
  await copyFile(new URL('../' + name, import.meta.url), new URL(name, out));
}
if (process.env.ARCADE_API_BASE) {
  const endpoint = new URL(process.env.ARCADE_API_BASE);
  if (endpoint.protocol !== 'https:') throw new Error('Production API must use HTTPS.');
  await writeFile(new URL('config.js', out), `window.ARCADE_CONFIG = ${JSON.stringify({ apiBase: endpoint.href.replace(/\/$/, '') })};\n`);
}
await mkdir(new URL('images/', out), { recursive: true });
await copyFile(new URL('../images/new-game.svg', import.meta.url), new URL('images/new-game.svg', out));
const games = JSON.parse(await readFile(new URL('../data/games.json', import.meta.url)));
for (const game of games) {
  await mkdir(new URL('./', new URL(game.image, out)), { recursive: true });
  await copyFile(new URL('../' + game.image, import.meta.url), new URL(game.image, out));
}
await mkdir(new URL('data/', out), { recursive: true });
await copyFile(new URL('../data/games.json', import.meta.url), new URL('data/games.json', out));
await copyFile(new URL('../node_modules/@fontsource/jersey-10/files/jersey-10-latin-400-normal.woff2', import.meta.url), new URL('vendor/jersey10.woff2', out));
await cp(new URL('../node_modules/@phosphor-icons/web/src/bold/', import.meta.url), new URL('vendor/icons/', out), { recursive: true });
await build({ stdin: { contents: "export {toCanvas} from 'qrcode';", resolveDir: process.cwd() }, bundle: true, format: 'iife', globalName: 'ArcadeQR', outfile: new URL('vendor/qr.js', out).pathname, minify: true });
await mkdir(new URL('vendor/licenses/', out), { recursive: true });
for (const [source, name] of [['@fontsource/jersey-10/LICENSE', 'Jersey-10.txt'], ['@phosphor-icons/web/LICENSE', 'Phosphor.txt'], ['qrcode/license', 'QRCode.txt']]) {
  await copyFile(new URL('../node_modules/' + source, import.meta.url), new URL('vendor/licenses/' + name, out));
}
console.log(`Built static site in dist/ with the ${games.length} game images used by the app.`);
