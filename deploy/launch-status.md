# Launch validation — 2026-09-29

Software deployed and live core flow validated. Ron confirmed the live QR scan and Google sign-in on his phone on 2026-09-29. Phone score entry also passed. Retrying the original iPhone photo, TV and second-account acceptance remain pending.

## Initial deployment checks (historical) — completed with receipts

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
- Retry the original iPhone photo after the HEIC and size-limit update; phone initials and score submission passed.
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

## Display initials follow-up — 2026-09-29

Featured record initials are approximately 17% larger, with positive letter spacing and centered alignment. Portrait checks at 540×960 and 1080×1920 found no score/control overlap. Source commits 2dc7c18 and c177b42 are published through Pages commit 07a171590d16068afae01078bc2ef848f848e153. Public HTML/CSS matched the build; live browser inspection confirmed the new typography after versioning the stylesheet to avoid a cached older copy. No backend or score changes were needed.

## Accounts, notifications and taunts — 2026-09-29

- Added a top-of-entry Account button with an unread badge, Notifications, My scores, saved default initials, sign out and an admin-only Manage scores shortcut.
- Added authenticated activity for new submissions and record breaks. A prior Google-account record holder receives a personalized record-break message; imported records have no linked Google identity. Activity starts at deployment and shows the latest 100 entries. Read status and initials persist per account. No email or push delivery.
- Optional 140-character taunts are displayed using text nodes. Admin score correction can edit/clear a taunt; removal hides the submission from activity. Duplicate submission retries do not duplicate events. Same-second equal scores now retain insertion order rather than ordering by random IDs.
- 55 backend tests passed, covering ownership, auth, personal record-break targeting, taunts, time records, ties, self-improvements, event atomicity, read cursors, moderation and account/activity backup restoration. Syntax/build checks passed.
- Two separate local browser player sessions exercised a first record, a rival's higher score with a taunt, personalized notification, My scores, saved initials, unread clearing and the admin shortcut at phone width. Example screenshot saved in outputs/screenshots/record-broken-notification.png; no test rivalry was inserted into production.
- Private backup /var/backups/nicks-arcade/before-account-5e65067 created before deployment. Migration passed on a copy first. Backend release 5e65067 installed; all 34 preexisting score rows preserved exactly, comparing original columns. Public health passed and unsigned /account and /activity returned 401. Mission Control process remained unchanged.
- Pages release 02322b86a9afba582a6cd42bdc6428ceb5561c21 published; public HTML, JavaScript and CSS matched the tested build. CSS/JS references are versioned to refresh browser caches.
- Live multi-account Google notification delivery has not yet been exercised; the two-player flow was validated locally with explicit preview identities. Existing physical TV, original iPhone photo retry and source naming questions remain pending.

## Shared TV rotation timing — 2026-09-29

- Admin Account → Settings now includes TV Display / Seconds per game, accepting whole numbers from 5 to 120. Default remains 15. The value is stored in SQLite metadata and included with public leaderboard polling; connected visible boards pick up a change within five seconds and restart their rotation interval. Pause and reduced-motion behavior remain respected.
- 57 backend tests passed, including independent-client readback, application restart persistence, admin-only writes and range/type validation. Build/syntax checks passed. Browser settings saved 5 seconds; the board advanced automatically and remained unchanged when paused across another interval.
- Backend b17f912 deployed after backup before-timing-b17f912. Scores, profiles, activity and metadata compared unchanged with the backup. Public API returns rotationSeconds=15 and rejects unsigned timing updates with 401. Mission Control PID remained unchanged.
- Pages 70cfe892059a463fe1cd860e9d32cf7d8d295a98 built successfully; published HTML/JS match the tested release. README updated on the default branch. Saved settings screenshot uses the explicitly labeled local preview; the live default was not changed for the test.
