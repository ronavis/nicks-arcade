# Launch validation — 2026-09-29

Software deployed and live core flow validated. Ron confirmed the live QR scan and Google sign-in on his phone on 2026-09-29. Phone score/photo entry, TV and second-account acceptance remain pending.

## Completed with receipts

- Original source branch and dirty original main.css preserved. Source rebuilt in isolated codex/arcade-record-spotlight branch.
- Source code pushed to GitHub; Pages published static-only commit `64bf1981dc8f4f19d95cafb33b2df639c3482c63`, parent `2ba50d8f789ad6045f69bb68f6622451dcb406a8`. Rotation follow-up published as `c618d2cd3304df33667b8609318e981fa1dc08a4`; its public HTML, JavaScript, CSS and config hashes match the release. Existing gh-pages branch/source unchanged; no forced push. Old commit retained for rollback.
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

- Ron confirmed on 2026-09-29 that scanning the live QR code and signing in with Google worked on his physical phone (user-reported validation).

## Still pending

- A second real Google account for live non-admin verification (automated permission-denial tests pass).
- Initials keypad, score submission and photo selection/upload on the physical phone.
- Nick's actual TV/browser/fullscreen/rotation test.
- Confirm source game naming ambiguities and interpretation of VS. Excitebike's time. The 32 visible records in Ron's still-open old Chrome tab matched the imported records; other devices' browser-local records have not been inspected.

## Source history

Draft PR: https://github.com/ronavis/nicks-arcade/pull/1. Source branch update initially encountered GitHub internal errors; a normal non-force HTTP/1.1 push succeeded and was independently read back. The original checkout remains untouched. PR remains draft pending external acceptance; master has not been merged.

## Receipts

Local outputs/launch-receipts holds installation logs, public API checks, Pages verification, restart evidence and backup timer evidence. Private raw backup copies remain in work/launch/private-backups, not in the public project. Update this file only from new evidence.

## Phone feedback fixes — 2026-09-29

- Ron's phone submitted Bubble Bobble 254,258 / TST successfully without a photo. Read-only production database verification confirmed the entry; it remains in history beneath the original 1,734,150 record.
- The old search was limited to the 32 seeded games. The Simpsons is now included with no invented starting score. Signed-in players can add missing games with their first score, choosing points or fastest time. Game and score are saved atomically; names differing only in punctuation/spacing reuse the existing game. Added games persist in SQLite, appear in search/TV/admin, and are included in database backups.
- Photo support now includes HEIC/HEIF, JPG, PNG and WebP up to 40 MB / 64 megapixels. The server resizes to a 1600-pixel maximum edge and saves JPEG without EXIF. Browser previews gracefully tolerate unsupported HEIC rendering; upload waits allow slower phone connections.
- 47 backend tests passed, including new-game persistence/concurrency/admin correction, legacy score preservation, all 33 game submissions, HEIC, 48-megapixel JPEG and an upload above the former 8 MB limit. Build and syntax checks passed. Browser search tested all 33 games without punctuation/spaces; a local first-record submission passed. Phone-width dialog visually checked.
- Backend release ac00a64 installed after a private database/photo backup at /var/backups/nicks-arcade/before-photo-catalog-ac00a64. Nginx changed only the Arcade request size to 41 MB including form overhead; config test passed. Mission Control PID and activation time unchanged, existing /app/ HTTP 200.
- Production score rows matched the pre-release backup exactly. HEIC and 8064x6048 JPEG conversion passed in an isolated test instance on the VPS. Public production health passed.
- Pages release de78c62bbcf9ef410905057a42eab5853bb67a69 published; HTML, JS, CSS, config, Simpsons art and fallback art verified byte-for-byte. Live browser found and opened The Simpsons.
- Still pending: retry Ron's original iPhone photo, physical TV acceptance, a second real non-admin account and source game/time naming questions. No claim that the original photo has already been successfully retried.
