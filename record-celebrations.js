'use strict';
// Observe public winner snapshots without replaying records on first load.
const ArcadeCelebrations = (() => {
  function value(score, kind) {
    if (kind !== 'time') return Number(String(score).replaceAll(',', ''));
    const parts = String(score).split(':');
    return parts.length === 2 ? Number(parts[0]) * 60 + Number(parts[1]) : Number(score);
  }
  function createObserver() {
    let previous = null, watermark = 0;
    return snapshot => {
      const current = new Map(snapshot.games.map(game => [game.id, game.record]));
      const events = [];
      if (previous) for (const game of snapshot.games) {
        const record = game.record, before = previous.get(game.id);
        if (!record || record.id === before?.id || record.revision !== 1 || !record.createdAt) continue;
        if (record.createdAt < Math.max(watermark, snapshot.updatedAt - 60)) continue;
        const better = !before || (game.kind === 'time' ? value(record.score, game.kind) < value(before.score, game.kind) : value(record.score, game.kind) > value(before.score, game.kind));
        if (better) events.push({ ...game, record: { ...record } });
      }
      previous = current; watermark = Math.max(watermark, snapshot.updatedAt);
      return events;
    };
  }
  return { createObserver };
})();
if (typeof module !== 'undefined') module.exports = ArcadeCelebrations;
