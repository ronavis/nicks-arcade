const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const entries = [...JSON.parse(fs.readFileSync('data/games.json')), ...JSON.parse(fs.readFileSync('data/artwork.json'))];
const context = { ARCADE_ARTWORK: entries };
vm.runInNewContext(fs.readFileSync('artwork.js', 'utf8'), context);
const resolve = context.ArcadeArtwork.resolve;
test('unclaimed titles use approved artwork across spelling punctuation and case', () => {
  for (const title of ['NBA Jam', 'nba-jam', ' NBA JAM ']) assert.equal(resolve({ title, image: 'images/new-game.svg' }), 'images/cabinet-marquees/nbajam.jpg');
  assert.equal(resolve({ title: 'The Simpsons' }), entries.find(g => g.id === 'simpsons').image);
});
test('preserve assigned artwork and avoid incorrect matches for different editions', () => {
  assert.equal(resolve({ title: 'NBA Jam', image: 'custom.jpg' }), 'custom.jpg');
  assert.equal(resolve({ title: 'NBA Jam Tournament Edition' }), 'images/new-game.svg');
  assert.equal(resolve({ title: 'Unknown cabinet' }), 'images/new-game.svg');
  for (const entry of entries) assert.ok(fs.existsSync(entry.image), entry.image);
});
