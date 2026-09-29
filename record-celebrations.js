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
  function recordAge(record, now = Date.now()) {
    if (!record) return 'No score posted yet';
    if (!record.createdAt) return '';
    const days = Math.max(0, Math.floor((now - record.createdAt * 1000) / 86400000));
    const date = new Date(record.createdAt * 1000).toLocaleDateString(undefined, {month:'short', day:'numeric', year:'numeric'});
    if (record.revision > 1) return `Submitted ${date} · corrected`;
    return `${days === 0 ? 'Set today' : days === 1 ? 'Set 1 day ago' : `Set ${days} days ago`} · ${date}`;
  }
  return { createObserver, recordAge };
})();
if (typeof module !== 'undefined') module.exports = ArcadeCelebrations;
