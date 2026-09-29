/* Match approved cabinet artwork without confusing different game editions. */
(function (root) {
  'use strict';
  const key = value => String(value || '').normalize('NFKD').toLowerCase().replace(/[^a-z0-9]/g, '');
  const catalog = new Map();
  for (const entry of root.ARCADE_ARTWORK || []) {
    for (const title of [entry.title, ...(entry.aliases || [])]) catalog.set(key(title), entry.image);
  }
  root.ArcadeArtwork = {
    resolve(game) {
      if (game.image && game.image !== 'images/new-game.svg') return game.image;
      return catalog.get(key(game.title)) || 'images/new-game.svg';
    }
  };
})(typeof window === 'undefined' ? globalThis : window);
