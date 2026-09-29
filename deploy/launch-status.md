# Launch validation — 2026-09-29

Deployment in progress. Do not equate published files with complete opening-night acceptance.

## Completed with receipts

- Original source branch and dirty original main.css preserved. Source rebuilt in isolated codex/arcade-record-spotlight branch.
- Source code pushed to GitHub; Pages published static-only commit `64bf1981dc8f4f19d95cafb33b2df639c3482c63`, parent `2ba50d8f789ad6045f69bb68f6622451dcb406a8`. Existing gh-pages branch/source unchanged; no forced push. Old commit retained for rollback.
- GitHub reports Pages built successfully. Public index.html, app.js, main.css and config.js bytes match the release exactly.
- Isolated nicks-arcade account, Python 3.12 venv, root-owned code release `/opt/nicks-arcade/releases/0b873b1`, service on loopback 8766, protected persistent data `/var/lib/nicks-arcade`.
- Public API at `https://midconversation.com/arcade-api`. Health reports production; all 32 records returned; unsigned score/photo requests rejected; no production demo route; expected CORS origin accepted and unrelated origin rejected.
- Nginx config backed up to `/root/nicks-arcade-nginx-before-20260929.conf`; only the arcade location added. Config test and reload succeeded. Existing `/app/` remained HTTP 200. Mission Control process PID 2920079 and active timestamp 2026-09-24 11:03:18 UTC unchanged.
- Service restart retained all 32 records and initial Galaga score.
- Daily backup timer enabled for 06:00 UTC. First backup exited successfully. Private off-host copy restored into independent local app and verified 32 games and Galaga record. Database backups include account information; not stored in public repo or public receipts. Automatic off-host copying not configured.
- Existing Google project and client inspected through the signed-in owner's Console. Authorized JavaScript origin already `https://ronavis.github.io`; no client credentials or origins changed. Consent audience is Testing. Google's basic Sign in with Google exception means a Testing label alone does not establish an allowlist blocker: https://support.google.com/cloud/answer/15549945?hl=en
- Local build/syntax checks and all 37 backend tests passed before publication.

- Real Google sign-in as Ron succeeded with no OAuth setting changes. The browser showed signed-in state and admin controls.
- Submitted disposable 41,511 / TST through the public website with an 800×500 test photo. The public scoreboard loaded it; the admin retrieved the saved photo.
- Restarted the production service with the submission present: score and proof reference survived. A second off-host backup restored both the real submission and readable photo.
- Corrected the test to 41,512 using the live admin UI, then removed it. The independent public TV view automatically reverted to 41,510 / JJH without a reload. Test removal is retained in audit history.
- Fixed optional rotation scaling: measure the unrotated board width and rotate within a stable viewport. At 960×540, the rotated board bounds are exactly 960×540 and its layout width remains 540; screenshot inspected without overlap.

## Still pending

- A second real Google account for live non-admin verification (automated permission-denial tests pass).
- Actual phone QR scan and Nick's TV/browser/fullscreen/rotation test.
- Confirm source game naming ambiguities and interpretation of VS. Excitebike's time; identify any real scores entered only in the old site's local browser storage.

## Receipts

Local outputs/launch-receipts holds installation logs, public API checks, Pages verification, restart evidence and backup timer evidence. Private raw backup copies remain in work/launch/private-backups, not in the public project. Update this file only from new evidence.
