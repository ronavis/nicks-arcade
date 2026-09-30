/* Match approved cabinet artwork without confusing different game editions. */
(function (root) {
  'use strict';
  const key = value => String(value || '').normalize('NFKD').toLowerCase().replace(/[^a-z0-9]/g, '');
  const catalog = new Map();
  for (const entry of root.ARCADE_ARTWORK || []) {
    for (const title of [entry.title, ...(entry.aliases || [])]) catalog.set(key(title), entry.image);
  }
  // These packs contain the rejected space background and miniature marquee layout.
  const legacyPack = image => /raw\.githubusercontent\.com\/ronavis\/nicks-arcade\/[^/]+\/images\/mame_marquees/i.test(image || '') || /^images\/mame_marquees(?:_clean|2)\//i.test(image || '');
  root.ArcadeArtwork = {
    resolve(game) {
      const rejected = legacyPack(game.image);
      const approved = catalog.get(key(game.title)) || catalog.get(key(game.id));
      if (rejected) return approved || 'images/new-game.svg';
      if (game.image && game.image !== 'images/new-game.svg') return game.image;
      return approved || 'images/new-game.svg';
    }
  };
})(typeof window === 'undefined' ? globalThis : window);
