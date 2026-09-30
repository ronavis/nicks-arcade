# Launch validation — 2026-09-29

Software deployed and live core flow validated. Ron confirmed the live QR scan and Google sign-in on his phone on 2026-09-29. Phone score entry also passed. Retrying the original iPhone photo, TV and second-account acceptance remain pending.

## Latest release snapshot — September 29, 2026

- Latest frontend source `65ddf2c` uses the Bust-A-Move name and clean logo; Pages publication `38e472c8535944294a37886e00d575f6e4127f7c` (build and live assets verified). Notification marquees and pack filtering remain included. Menu-layering source remains `17c7d8b`. Backend last deployed at `cc2b075`; subsequent changes were frontend-only.
- QR/default landing and interactive sign-in return to the shared scoreboard. Enter a score leads the left-aligned menu for every role; admin actions remain role-restricted. The Manage scores label has no shield icon.
- Latest menu fix keeps leaderboard repaint layers beneath the menu. Mobile and rotated hit checks passed; the reported intermittent overlap still needs user confirmation, and fullscreen capture was inconclusive.
- The implementation remains in draft PR #1 on `codex/arcade-record-spotlight`. Default `master` retains the original implementation with an updated README; `gh-pages` serves the rebuilt site.
- The sections below are historical receipts. Older release IDs, test counts and temporary test-score states describe their respective checkpoints, not the current release.

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


## Thicker round dots — 2026-09-29

- Source `8cbc838`; Pages `e68d03271668a403179760bb9682a5571c1939f3`.
- Increased score font weight to 900 and added a proportional 0.016em outline, preserving round dots. CSS cache version updated.
- Build/check passed; TV and mobile inspected with local preview records. Published HTML and CSS match the build. No production data changed.


## Double-row dot construction — 2026-09-29

- Source `a77aac7`; Pages `92e494489c74db28be863847a12fd4c81ec465d3`.
- Replaced Doto with Bitcount Grid Double, using round elements at weight 400. Removed the synthetic outline. Build ships the new font and license and removes Doto.
- JavaScript check and build passed. Local browser inspection confirmed double-row strokes on TV, plus mobile long record/12-digit input and RON keypad entry. No scores submitted.
- Published HTML, CSS, font and license match production build bytes.


## Larger scoreboard values, same footprint — 2026-09-29

- Source `a336630`; Pages `7fc70ae9a70ec3bc09f35fb89c68f016167c8c05`.
- Increased featured score/initials and surrounding-game values while retaining prior line-box heights. Headers unchanged; abandoned header edit was removed before commit.
- Check/build passed. Portrait browser inspection confirmed readable double-row dots and no horizontal overflow in score, initials, surrounding rows or footer. Public HTML/CSS match build bytes.


## New-record TV celebration — 2026-09-29

- Source `10cc321`; Pages `54f2654da498ab3640abb70b1e89986bd06d1f13`.
- Silent 10-second TV takeover with artwork, initials, score, taunt, timed-record heading, and early-dismiss button. Rotation suspends during takeover; manual pause preserved. Reduced-motion entrance supported.
- Public winner snapshots skip first load, repeated winners, corrected/old/fallback records, and stale reconnection events. Same-game intermediate wins between polls are not replayed. Up to five queued winners.
- Seven detection regression tests, JS checks, and build pass. Local API submission triggered the real browser takeover; screenshot captured; automatic dismissal and no replay on refresh verified. No live records changed.
- GitHub Pages built; four published frontend files match build bytes. Backend unchanged.


## Matching dot-font headings — 2026-09-29

- Source `720a397`; Pages `012c584c05d42fdeb4d4b8eae131d471e1b167ff`.
- TV arcade title/High Scores subtitle and mobile wordmark now use Bitcount Grid Double. Header line heights retained.
- Checks/build passed; TV/mobile inspected; live HTML/CSS verified against build. Celebration still dismisses automatically after ten seconds. Pages build explicitly requested after push did not trigger it.


## Featured record improvement badges — 2026-09-29

- Source/backend `850bed6`; Pages `6c5654533b304d41edbb627ce227453002195cca`.
- Public winner records include a margin from their original activity previous_value, only for uncorrected record-breaking submissions. Imports, first records, nonpositive margins and corrected scores omit the badge. Times use exact hundredths.
- Badge appears only beside featured initials and celebration initials, with tap-to-explain text. Around-the-arcade rows unchanged.
- 67 backend tests, seven celebration tests, JS/build checks pass. Local browser verified featured +8,800 badge, its detail toggle, and automatic celebration +5,000. No production scores submitted or modified.
- Backup completed at /var/backups/nicks-arcade/pre-record-margin-20260929. Backend changed only leaderboard readback; no schema migration. Current release points to 850bed6, health reports production/ok, live 33-game response has improvement fields. Mission Control PID remained 2920079.
- Initial oversized archive transfer canceled before release creation; scoped service package deployed instead. Existing service resources retained. Pages build requested explicitly; public HTML/CSS/JS match production build.


## Record dates and empty-game guidance — 2026-09-29

- Source `e64f66b`; Pages `a9239c6ac6efee513a561fcacf3418c379af2fb0`.
- Featured submission age/date, honest unknown-date labels for legacy records, and My scores timestamps. Empty games explicitly say no saved score and offer admin Enter the first score.
- Live read-only investigation: 32 imported current winners and Simpsons with no record. Only two non-imported submissions exist, both earlier TST entries already removed. Zero invalid active submissions. User's game identification remains pending, so the phone report is not conclusively explained. No live data mutations.
- Eight frontend tests/check/build pass; local browser verified dated record and empty Simpsons admin action selecting score entry. Public frontend bytes verified after Pages build.


## Mobile date/carousel spacing — 2026-09-29

- Source `cb84bd3`; Pages `332bac530d8d6593178d0036f40a03733b5ff9a0`.
- Phone-only spacing adjustment (max-width 500px): less score line-height and date/carousel padding, same font sizes. Desktop rules unchanged.
- Reproduced overflow before fix; checked 320px and 390px afterward with carousel bottom at divider boundary and controls visually above it. Checks/build pass; live HTML/CSS match build.


## Admin cabinet catalog before first scores — 2026-09-29

- Source/backend `1611963`; Pages `b5d441ba10ac39bd8e996aab2244ad488a929161`.
- Admin-only POST /admin/games adds title/type without score, reuses normalized titles, and validates conflicting types. Uses existing games table; no migration.
- Manage games in TV menu and account is admin-only. Search, first-score filter, Show on TV and enter/manage score shortcuts. Empty games display Be the first / Your initials here and join rotation/search. Neutral artwork for new titles.
- 69 backend tests and eight frontend tests passed, checks/build passed. Local browser added NBA Jam with no score, filtered it and displayed it on TV; phone dialog inspected. No test games added to live catalog (still 33 games).
- Backup /var/backups/nicks-arcade/pre-manage-games-20260929 completed. Current service 1611963 active; public health production/ok; unauthenticated creation rejected 401. Mission Control PID 2920079 unchanged. Live frontend bytes verified.

### Unclaimed-game artwork — September 29, 2026

- Source: `969a420`; Pages: `4a3674d3f2d08d930992a871dd227e11501f92b0`; default-branch README: `725ba7f6f099c70186e54b6426e7e5d868594b4d`.
- Approved title/alias matching uses the 33 existing curated images plus the genuine NBA Jam cabinet marquee. Unknown titles and distinct unmatched editions retain the neutral fallback. Assigned artwork is preserved.
- Ten frontend tests passed, build/check passed; NBA Jam with no score visually verified locally at 540 × 960. All five changed published files matched the local production build byte-for-byte. No backend changes or production game/score writes.

## Searchable collection and eligibility — September 29, 2026

- Backend source/release `cc2b075`; frontend source `3fd3f98`; Pages `c1318ddee996aed906d000de6b83ea5e6256095b`; default README `6fa000c64dab54e889a9a80b969cb7deb17a88b6`.
- Search indexes 9,543 marquee entries, including ROM variants. Existing curated art takes priority; 1,685 exact matches prefer supplementary cabinet artwork. Some remaining pack artwork is stylized; previews show the selected image.
- Existing 33 games remain eligible; shared bypass defaults off. Server checks approval within the score transaction. Bypass-created games stay outside the approved collection; disabling bypass blocks new scores and hides them from player choices/TV while preserving history. Admins can add/remove eligibility.
- Admin configuration readback confirms Ron and Nick. Isolated tests verify equal permissions and regular-player rejection. Nick’s own interactive Google sign-in has not been performed by the agent.
- Backup `/var/backups/nicks-arcade/pre-collection-rules-20260929/COMPLETE` verified before migration. Restarted only nicks-arcade; Mission Control PID stayed 2920079. Live service is production/healthy, with 33 eligible games, 34 retained score rows, bypass off, and working catalog lookup. No live test scores or games were added.
- 72 backend tests and 10 frontend tests pass. Local browser confirmed visual search, adding a cabinet without a score, successful first-score submission, toggling bypass on/off, player control restrictions, and 390px catalog fit. Live 390px scoreboard confirms blank undated row retains height and carousel remains above divider. Four changed published frontend files match the production build byte-for-byte.

## Scoreboard landing — September 29, 2026

Source `1aab8de`, Pages `f71bd676ea0223e62fe4c4d369fb09b2efc676ea`, default README `f0d85ae97053368f5147e55ed0f1f7f223707c15`. QR scans/clicks and the default phone/desktop route now open the shared scoreboard; interactive sign-in returns there as well. Restoring a saved session preserves an explicitly opened score-entry/admin route. Local browser verified signed-out landing, player sign-in transition, QR target, and score-entry reload with a restored session. Ten frontend tests and syntax/build checks passed; both changed public assets matched the build. No backend or record changes.

## Primary score menu action — September 29, 2026

Source `ceefafb`; Pages `d902b1385fdde30f9e98e37736bcedbd4cae726f`. Enter a score is the first menu action for every role, with bold text and a turquoise bordered background. Local browser verified signed-out and admin order, working score-entry navigation, and 390px fit. Syntax/build and diff checks passed; both published files matched the production build. Backend and records unchanged.

## Left-aligned menu — September 29, 2026

Source `00689bf`; Pages `dda0a08e50efba93122c4008c44e2a936b67bc46`. Menu row contents now align left rather than inheriting centered button justification. Shared rule includes admin actions; prominent Enter a score remains first. Build/diff checks and 390px visual review passed. Both changed live assets matched the production build.

## Menu layering — September 29, 2026

Source `17c7d8b`; Pages `3b6567fa478144186b8ca061600349ec1fd3e702`. Isolated the board at z-index 0 beneath the menu, isolated the menu, made native details content overflow explicit, and removed inherited opacity transition. Mobile and rotated browser checks found every visible menu action uncovered at its center after leaderboard updates. Intermittent user report was not reproduced exactly; fullscreen automation capture was inconclusive. Build/diff checks pass and published HTML/CSS match. No backend/record changes.

## Catalog fallback and notification artwork — September 29, 2026

Source `b31be73`; Pages `f4a90cbc76a9ef9b402632f4f5b6843b86e21131`. The shared frontend artwork resolver rejects old remote space-pack references, including saved game selections, and uses exact approved title/ROM matches or a neutral placeholder. No games were removed from search. The backend retains historical image references; no backend release or database change was needed. Notifications and My scores share the artwork component and look up all games, including games outside the eligible collection.

All 11 frontend tests, syntax/build and diff checks passed. All 9,543 catalog entries were resolved without a rejected remote-pack URL. A 390px local browser check confirmed catalog placeholders, the correct NBA Jam cabinet image, and a Galaga record notification with loaded marquee, previous score, taunt, date and unread styling. One local-only score fixture was added; no live scores were created or changed.

GitHub reports the Pages build successful; all four changed published files match the production build byte-for-byte. Backend and production scores unchanged.

## Supplied token favicon — September 29, 2026

Source `240fb5d`; Pages `68d31ee19006d6d53f5831cb0ffaef4141c783ce`. Used the supplied photo unchanged in composition, converted to 32px PNG, multi-size ICO and 180px Apple touch icon. Original photo retained in source. Icon URLs versioned for cache refresh. Build and image-format checks passed; Pages reports built and all four changed live assets match the production build. No backend or data changes.

## Turquoise token background — September 29, 2026

Source `a432a0b`; Pages `bed4057b33c0d78e2d60c74a2808576d1438c0d6`. Background edited with the built-in image tool; original photo preserved. Browser and Apple icons converted from the edited asset. Build/diff checks passed; Pages built and published HTML plus all three icons match the build. No backend or data changes.

## Puzzle Bobble identity and Excitebike time edits — September 30, 2026

Source `95d0943` plus image optimization `097488a`; Pages `5ec90136b5e0c7cca5be5a79f0b000ef96505939` built successfully. All five changed live assets match the production build. Puzzle Bobble now uses the Japanese cabinet marquee, sized to 1600px. Seed data is corrected; its historical internal ID is retained. The separate Bubble Bobble game retains its own artwork in the catalog.

Before correcting the production game metadata, database/photos were backed up at `/var/backups/nicks-arcade/before-puzzle-bobble-20260930/COMPLETE`. The guarded correction script was validated on a local backup and checked for repeat-run safety. Production correction changed only the game's title, search key and image, added an audit receipt and asserted every score row unchanged within the transaction. Public API readback confirms Puzzle Bobble and its original 1,734,150 / RJW record. Backend remains cc2b075; no restart needed.

Nintendo's official VS. System release description confirms hundredths-of-a-second racing. Input 1:02:30 and 1:02.30 represent the same 62.30 seconds. Existing numeric scoring and display formatting remain unchanged. Entry/admin hints explain normalization; admin save feedback reports the stored value. A regression test confirms separator-only normalization and a genuinely different time persisting through an application reopen. 73 backend tests, 11 frontend tests, syntax/build and diff checks passed. No live Excitebike score was changed by this task.

## Bust-A-Move display branding — September 30, 2026

Source `65ddf2c`; Pages `38e472c8535944294a37886e00d575f6e4127f7c`. At Ron’s request, selected a clean wide Bust-A-Move logo after reviewing crowded marquee alternatives. Source seed and live display name/image updated, retaining the original game ID. Backup `/var/backups/nicks-arcade/before-bust-a-move-20260930/COMPLETE` preceded the audited metadata change; the transaction asserted every score row unchanged. Public API confirms Bust-A-Move with 1,734,150 / RJW. Local correction test, 11 frontend tests, build/diff checks passed. Pages built and all four changed live files matched. No backend restart.

## Admin marquee uploads and Puzzle Bobble logo — September 30, 2026

Source/backend `aea06f5`; Pages `f3a0d35fdee84f6d40c7b6d01ceb03ccbf2627fb`. Admins can upload, replace and restore artwork through Manage games. The override is shared across all devices and display surfaces. Immutable PNG storage preserves transparency, strips metadata and resizes accepted JPG/PNG/WebP/HEIC images. The schema adds an optional game marquee ID and before/after artwork audit history.

75 backend tests and 11 frontend tests passed, including admin authorization, stale-edit conflicts, invalid-image rejection, metadata stripping, transparent resizing, public image availability, restore-default behavior and backup recovery with image history. Browser upload/save/reopen/restore checks passed in the local admin preview; the upload dialog fits a 390 × 844 viewport. No test score or test upload was created on production. A real iPhone HEIC marquee upload remains device acceptance; existing HEIC proof-photo decoding tests pass.

Production backups completed before migration and after schema installation. Only nicks-arcade was restarted. Every score row matched the pre-release backup after migration. Public API health and unsigned-upload rejection (401) were verified. Pages reports built; index, app, CSS, artwork catalog and logo bytes all match the production build. The guarded Puzzle Bobble metadata correction asserted every score row unchanged, and live API readback confirms the clean logo with 1,734,150 / RJW. Daily backup now includes active and historical uploaded marquees.

## Compact game-management cards — September 30, 2026

Source `176988e`; Pages `b43125bb863bede83edc1d9eee626f676a0d4fe2`. Replaced tall stacked game actions with bordered cards: artwork and record together, separate horizontal actions on desktop and a two-column phone layout. Removal is visually secondary. All actions retain their existing handlers and admin role requirements. Upload button wording is now “Change marquee” after an override is saved.

Frontend syntax, all 11 frontend tests, build and diff checks passed. Local browser checks covered desktop/mobile appearance, upload-dialog entry, correct game selection in Manage scores, long Street Fighter titles without overflow, and 44px phone touch targets. Pages reports built; all three changed frontend files match the production build. No backend or score-data changes.
