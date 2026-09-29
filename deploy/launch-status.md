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

## Legacy ownership — September 29, 2026

Source 368cc46 adds a private server-configured initials crosswalk, one-time binding to verified Google subjects, audited imported-score links and clear My scores origin labels. Backend release /opt/nicks-arcade/releases/368cc46 is active. Backup /var/backups/nicks-arcade/before-legacy-368cc46 includes the database, referenced photos and prior private service environment.

62 backend tests pass; JavaScript checks and production build pass. Live readback confirms seven RON records linked through an authenticated request. Every pre-existing score value, initials, photo reference, timestamp and removed state matches the backup; database integrity is okay. Nick's 13 NIC records and Martin's three MAR records await their sign-in; aliases NJW and RCA have no imported rows currently. Their identity mappings are kept only in the private service environment, not in this repository. Mission Control PID 2920079 remained unchanged. Historical activity is not reassigned.

Pages 064d6f8 reports built, and public app.js/index.html bytes match the tested production build. Default-branch README updated separately in 59169ae.

## Score artwork and test cleanup — September 29, 2026

Source e50f95a adds game artwork to My scores, hides removed entries from that view (admin history preserved), and mirrors the unread badge on the TV account button. JavaScript checks/build pass. Local 390x844 browser validation confirmed all seven imported RON artwork images decode, and a rival record-break event shows the previous record and taunt; both badge labels show one unread and Mark all read clears the badges. The browser demonstration used only local preview data.

Production cleanup: backed up SQLite and photos at /var/backups/nicks-arcade/before-tst-cleanup-20260929. Galaga TST was already removed. Soft-removed only Bubble Bobble TST (254258) with an audit entry; readback confirms zero active TST entries and all other score rows exactly unchanged. Backend release remains 368cc46; no service restart needed.

Pages commit c6462ac; default-branch README 6eee784.

Public app.js, main.css and index.html match the tested production artifact after Pages publication.

## Saved taunt settings — September 29, 2026

Source/backend 93fbb63 adds per-account saved taunt text and an enable/disable switch. Automatic taunts default off and are applied transactionally only when beating another player's existing record; ties, lower scores, first records and own-record improvements do not trigger them. Manual edits/clears remain supported. Retry fingerprints preserve idempotence even if preferences change after submission.

65 backend tests pass; JavaScript check/build pass. Normal-player mobile UI validation confirmed saving enabled text and retaining disabled status/text after reload. Backup before-taunt-93fbb63 completed before backend activation; live API is healthy, database integrity passes, pre-existing score/profile columns exactly match the backup. Mission Control PID 2920079 unchanged. Pages c1e2518; default README 4853382.

Published app.js, main.css and index.html match the tested production artifact.

## Friendly fair-play footer — September 29, 2026

Source a7c1c75 / Pages 4deee86 adds a cream square to the right of Scan. Play. Post.: “PLAY FAIR. Keep it fun. Post scores earned at Nick’s arcade. Brag honestly.” QR and note have equal square dimensions and aligned lower edges. Portrait browser checks at 1080x1920 and 540x960 show no footer overflow. JavaScript checks/build pass; published HTML/CSS match the tested artifact. No score or service changes.

## Scoreboard menu — September 29, 2026

Source 3b2e35f / Pages 79d2e62 replaces the faint lower TV control strip with an always-visible upper-right hamburger disclosure. Includes account, pause/play, full screen, rotate and score entry, plus unread count on the closed menu button. Native keyboard disclosure, outside click, Escape and action selection close behavior. Account/score navigation exits element fullscreen first. Local portrait browser verified expanded/collapsed appearance, Pause changing to Play, rotate/unrotate, full-screen toggle UI, signed-out account navigation, score-entry navigation and dismissals. JavaScript checks and production build pass. No backend or score changes.

Public HTML, CSS and JavaScript match the production menu artifact.

## Correct Simpsons artwork — September 29, 2026

Source 28db784 / Pages c6d8cd0 replaces the previously recovered space-themed pack graphic with the 3840x1132 cabinet marquee documented in docs/artwork-sources.md. Existing catalog path preserved; Simpsons-specific image cache version and script version updated. JavaScript checks/build pass. Pages reports built; public HTML, script and image bytes match the production artifact. Live browser selected The Simpsons and confirmed the correct image loads at 3840x1132. No backend or score changes.

## Bolder fair-play square — September 29, 2026

Source 169ba29 / Pages c4be7e6 increases fair-play contrast with a dark panel, cream border and bold body text, larger turquoise heading and red divider. Shortened middle copy to “Earn it at Nick’s arcade.” QR footprint retained; local portrait browser confirms no text overflow. Build and diff checks pass. No service or score changes.

Live HTML and CSS match the tested build after publication.

## Scout's-honor badge — September 29, 2026

Source 02b7ee7 / Pages 21f6d14 adds a generated transparent pixel-art three-finger salute alongside stacked PLAY FAIR lettering. Message reads “Earn it at Nick’s arcade. Brag honestly.” Square footprint preserved. Local portrait browser confirms image decode and no overflow; JS/build checks pass. Public HTML/CSS/image bytes match tested production build. No backend or score changes.

## Nick admin access — September 29, 2026

User-authorized private configuration update preserves Ron and adds Nick's previously confirmed Google account as administrator. Private environment backup saved before change; restarted only nicks-arcade. Running service environment readback confirms exactly those two admin accounts; public health passes. Isolated tests verify Ron/Nick admin session and moderation/export/display-settings access, and Martin player access with HTTP 403 for those admin routes. Nick's real Google sign-in still needs his next visit; no impersonated live auth was used. Mission Control PID remains 2920079. No score records changed.


## Admin score-management UX — 2026-09-29

- Source: `790d05d`; Pages: `d4663113c9aa245add26e5034f1c99a8548b1334`; default-branch README: `bd12550726865859b137893f4bf443d06a439983`.
- Added verified-admin-only Manage scores shortcut to the TV menu; non-admin direct routes redirect to score entry. Server authorization remains enforced independently.
- Redesigned management with artwork, current-record status, per-game submission search, active/removed filters, clear action buttons, named confirmations, Cancel, and success feedback.
- Validation: JavaScript checks and production build passed; 65 backend tests passed. Local browser checks covered signed-out/player/admin menus, player route rejection, search, edit, cancel removal, removal, and removed-history filtering. Mobile 390x844 and desktop 1000x950 inspected. Mutations used local preview data only.
- GitHub Pages reports built; public index.html, app.js, and main.css match production build byte for byte. No production records modified and no backend restart required.


## Round dot-matrix scores — 2026-09-29

- Source `9522474`; Pages `a87580e5f80ae04595740cf678722f142371d25d`.
- Locally hosted Doto variable font, weight 800 and round dots, for TV scores/initials, record preview, score entry, initial slots, My scores values, and admin score values. Headings retain Jersey 10. Font license bundled.
- JavaScript check, production build, and whitespace checks passed. Browser inspection covered portrait TV and mobile; seven-digit record, twelve-digit entry, and RON keypad entry fit with no page overflow. No score submitted.
- Published HTML, JS, CSS, font, and font license match build bytes. Backend unchanged.
