'use strict';
// Observe public winner snapshots without replaying records on first load.
const ArcadeCelebrations = (() => {
  function value(score, kind) {
    if (kind !== 'time') return Number(String(score).replaceAll(',', ''));
    const parts = String(score).split(':');
    return parts.length === 2 ? Number(parts[0]) * 60 + Number(parts[1]) : Number(score);
  }
  // A poll can skip several wins. Only pair the saved winning margin with its
  // matching observed baseline; otherwise omit the uncertain older milestone.
  function previousMilestone(game, before) {
    const improvement = game.record?.improvement;
    if (!before || !improvement) return null;
    const delta = game.kind === 'time' ? value(before.score, 'time') - value(game.record.score, 'time') : value(game.record.score, game.kind) - value(before.score, game.kind);
    const amount = Number(String(improvement.amount).replaceAll(',', '').replace(/s$/, ''));
    return delta > 0 && Math.abs(delta - amount) < 0.00001 ? { ...before } : null;
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
        if (better) events.push({ ...game, record: { ...record }, previousRecord: previousMilestone(game, before) });
      }
      previous = current; watermark = Math.max(watermark, snapshot.updatedAt);
      return events;
    };
  }
  function recordAge(record, now = Date.now()) {
    if (!record) return 'No score posted yet';
    if (!record.createdAt) return '';
    const created = new Date(record.createdAt * 1000), current = new Date(now);
    if (!Number.isFinite(created.getTime()) || !Number.isFinite(current.getTime())) return '';
    // Compare displayed local calendar dates, not elapsed 24-hour periods (DST-safe).
    const dayNumber = date => Date.UTC(date.getFullYear(), date.getMonth(), date.getDate()) / 86400000;
    const days = Math.max(0, dayNumber(current) - dayNumber(created));
    const date = created.toLocaleDateString(undefined, {month:'short', day:'numeric', year:'numeric'});
    if (record.revision > 1) return `Submitted ${date} · corrected`;
    return `${days === 0 ? 'Set today' : days === 1 ? 'Set 1 day ago' : `Set ${days} days ago`} · ${date}`;
  }
  return { createObserver, recordAge, previousMilestone };
})();
if (typeof module !== 'undefined') module.exports = ArcadeCelebrations;
