# Settings design QA — October 3, 2026

- Source visual truth: `/Users/studio/.codex/generated_images/01a0ed69-4bdd-71d2-b765-99cd8dd40c66/exec-662d399f-acd6-423a-b374-ff2f6ace7d61.png` (first displayed mockup, selected by Ron).
- Implementation screenshots: `docs/screenshots/account-settings.jpg`, `docs/screenshots/leaderboard-order.jpg`.
- Viewport: 540 × 1100 CSS pixels; screenshots 540 × 1100, density 1. Also inspected in the in-app browser at 390 × 844.
- Source generated image is 879 × 1790; normalize to approximately 540 × 1100 for comparison. Actual modal retains a 90dvh scroll limit rather than shrinking form content to fit the complete mock.
- State: local demo administrator, Settings selected. No production records were used or altered for these captures.

## Findings

No actionable P0/P1/P2 findings. All four management actions are equal-width outlined controls with the same type and spacing. Filled turquoise controls consistently save changes. Existing admin visibility remains enforced, including the new order setting.

## Fidelity checks

- Typography: existing Jersey 10 display font for management, tabs, headings and saves; existing sans-serif body/input font retained. Controls remain readable at phone width.
- Spacing: 12px management gaps, aligned labels and chevrons, section dividers, usable scrolling at both tested widths. Mock's long-form taunt helper copy remains the existing app wording; this intentionally takes more room.
- Colors: existing cream, cyan and ink tokens retained; pale hover state visible on the first action in the captured desktop image.
- Assets: no new raster assets required. Existing Phosphor chevrons match navigation function and screenshot style.
- Copy: existing functional labels retained. Arcade rules & TV display disclosure additionally contains the user-requested leaderboard sort choice.

## Comparison evidence

Full view checked against option 1; management group and personal-settings transition inspected separately in the screenshots and browser. Scroll state for the new order control captured separately. No P0/P1/P2 revision loop was required.

## Interaction validation

- Admin demo sign-in, account tabs and settings disclosure operate.
- Saved newest record first, closed/reopened Settings and confirmed selected choice persisted.
- Saved alphabetical again through the browser.
- Regular-player demo sign-in shows personal settings only, without management or shared arcade controls.
- Browser error log: no errors captured in the validation tab.
- Frontend: 21 tests pass; backend: 101 tests pass. Tests include sorting dates/ties/undated records, administrator enforcement, invalid values, shared settings and persistence after app recreation.
- Actual Fire Stick hardware not available for this validation.

final result: passed

# Manage Games grid — October 3, 2026

Source visual truth: `/Users/studio/.codex/generated_images/01a0ed69-4bdd-71d2-b765-99cd8dd40c66/exec-92516510-e94a-408e-90db-9a0b80fe235d.png` (second displayed Manage Games mockup, selected by Ron).
Implementation: `docs/screenshots/manage-games-grid.jpg`, `docs/screenshots/manage-games-phone.jpg`, `docs/screenshots/manage-game-editor.jpg`.
Viewports: 725×1180 and 390×844 CSS px, density 1. Source is a generated 966×1629 screen; compare its approximately 700px-wide panel to the 700px implementation dialog. Actual dialog retains 90dvh scrolling, so fewer rows appear at once than in the full concept image.
State: local demo admin, Your games selected; separate game editor for Asteroids. Demo data differs from production names/counts/artwork. No live scores or images were changed for validation.

Fidelity: existing cream/cyan/ink tokens and Jersey 10 display typography retained. Two equal grid columns, aligned marquee slots using contain (no stretching), sans-serif record details, visible checkbox and single Edit game per tile. Search and import stack on phones. No invented artwork; original game assets preserved. Mock's one-line collection count moves below filters for readability. Existing modal header and source-game records remain accurate to local data.

Iteration: P2 excess reserved title whitespace reduced from 2.1em to 1.05em; desktop and phone recaptured. Full view and individual cards/editor inspected. Lazy images were decoded before final desktop capture. No remaining actionable P0/P1/P2 findings.

Browser validation: tabs, catalog search, No scores filter, leaderboard checkbox off/on, spreadsheet import open/close, editor rename/marquee/assignment open/close, Manage scores routing to correct game, and regular-player admin-control hiding passed. Console reported zero errors and warnings. Existing 21 frontend tests and syntax/build checks passed. Backend unchanged; no backend redeployment needed.

final result: passed

# Manage Scores timeline — October 3, 2026

Source visual truth: `/Users/studio/.codex/generated_images/01a0ed69-4bdd-71d2-b765-99cd8dd40c66/exec-48a2004d-920d-4a3b-a0fe-2ff7066a08a9.png` (third displayed Manage Scores mockup selected by Ron).
Implementation captures: `docs/screenshots/manage-scores-timeline.jpg` (760×1180) and `docs/screenshots/manage-scores-phone.jpg` (390×844), CSS pixels and density 1. Generated source 1006×1564 normalized to the implementation panel width. Local demo admin with illustrative Asteroids submissions; desktop captured before removing test records, phone after removal to validate state labels. Production score data was untouched.

Full-view and focused timeline inspection: cream/cyan/ink tokens, existing Jersey 10 headings/buttons and ScoreDots score type, horizontal artwork/game summary, equal tabs, flat chronological timeline and full-width Manage submission actions match the chosen direction. Mobile summary remains a compact side-by-side block, long content wraps, page scroll exposes the complete timeline. Existing assets retained without stretching. Dates/player metadata remain truthful to records.

Intentional data constraints: milestones show original values; the management dialog uses current saved values. Corrected and removed states are explicit. Historical improvement amounts in the concept are omitted because adjacent milestones are not reliable baselines after corrections/removals. No unknown legacy dates are manufactured. The existing 200-submission management window is retained with explanatory copy for older milestones.

Browser interactions: record/all-submission tabs, search, show-removed, edit-and-save, reopening a corrected score (verified 8,561 instead of original 8,560), removal confirmation, current-record removal promoting the remaining best score, and read-only removed entries passed against isolated local demo data. One locator was narrowed after a search also matched the submitting admin email; no production action occurred. Console reported zero errors/warnings. All 22 frontend tests pass, including status-label precedence for deleted/current/corrected/imported milestones. No backend changes.

No actionable P0/P1/P2 findings remain. Follow-up: optional pagination beyond the existing latest-200 submission window is outside this visual redesign.

final result: passed

# Public game profile timeline — October 3, 2026

Reference: user Crystal Castles profile screenshot `/var/folders/xx/6tpmrqn15mb5zhg76493sgpm0000gn/T/codex-clipboard-cb86e17d-9863-4c78-ad1b-671155df306a.png` and the selected Manage Scores timeline implemented above.
Captures: `docs/screenshots/game-profile-timeline.jpg` at 760×1180 and `docs/screenshots/game-profile-phone.jpg` at 390×844, density 1. State: local Crystal Castles public profile with imported record and Centipede Cabinet assignment.

Full view and focused timeline/cabinet review passed: cream/cyan/ink colors, Jersey headings and ScoreDots scores match the adopted design; artwork and cabinet photos retain contain sizing; timeline labels precede scores and dates. Duplicate current-record summary hidden only when the same uncorrected record is already present. Corrected current value and empty-game summary remain visible. Phone layout has no horizontal overflow or clipped controls. Public metadata contains no email or administrator actions.

Browser checks: ordinary imported record, corrected record (separate current summary), empty game, open/close and both screen sizes passed. Console: zero errors/warnings. All 23 frontend tests pass, including exact duplicate detection and correction/empty-history cases. No backend changes or live data mutations.

final result: passed

Public profile follow-up validation: rapid close/reopen exposed a queued-close-event race that left the replacement profile loading. The close handler now invalidates requests only while the dialog is actually closed. Added regression coverage, then repeated ordinary → corrected → empty-profile browser transitions successfully. All 24 frontend tests pass. Final result remains passed.


# New-record celebration timeline — October 3, 2026

The selected record-history design now carries into the TV takeover. The cyan timeline shows the new record, initials and known date, followed by a matching previously observed milestone. Marquee, winning margin, optional taunt, cabinet images and automatic ten-second return remain available. Unknown legacy dates stay blank. The previous milestone is omitted if polling skipped an intervening win and the observed value no longer matches the server's saved margin. This is a compact celebration, not the complete historical ledger.

Captures: `docs/screenshots/celebration-timeline.jpg` (760×1180) and `docs/screenshots/celebration-phone.jpg` (390×844). These are local illustrative Centipede events; no scores were submitted to production. Reviewed actual rendered cream/cyan typography, timeline alignment, uncropped marquee and contained cabinet photo. Phone checks also covered a timed record, four cabinets, long taunt, first score, absent artwork assignments, dismissal button and the real ten-second automatic dismissal. No horizontal or vertical overflow in the four-cabinet test. Browser console: zero errors/warnings. All 26 frontend tests, syntax checks and build pass. No backend or stored-score changes.

final result: passed


# Cabinet gallery and dedicated profile — October 3, 2026

Selected references: gallery `exec-93c13cd8-1930-42fb-b5be-8554f1464b29.png`, profile `exec-d6f8a0de-d4e3-4a7c-98ad-2a58b0245032.png`; user explicitly chose gallery 1 opening profile 3. Combined flow `exec-e7ff9dd2-8e1e-44f9-9de4-45394560323c.png`. Existing real cabinet assets and stored game assignments were retained rather than replacing them with generated artwork.

In-app-browser captures at 1000×1180 and 390×844: `docs/screenshots/cabinet-gallery.png`, `cabinet-profile.png`, `cabinet-gallery-phone.png`, `cabinet-profile-phone.png`. Source and rendered gallery/profile images were opened together in one comparison. Full composition and readable control/typography regions reviewed. Actual cabinet roster/photo differences from mock data are intentional. The real list scrolls beyond the first six cabinets and first four assigned games.

Initial P1: inherited full-width primary-button styling overlapped the desktop gallery heading. Fixed Add cabinet and Add games widths, rebuilt and captured again. Final review: three-column gallery, two-column phone gallery, separate full-width profile, contained cabinet photos, cream/cyan styling, consistent outlined controls and readable game rows match the selected flow. Phone buttons stack and remain reachable without horizontal clipping.

Browser checks passed: gallery → profile → gallery; filtered search retained; return focus/scroll restored to selected cabinet; assigned-game filtering and empty results; assignment dialog; edit-name focus; photo-input focus; add-games flow; removal confirmation opened and cancelled. No production records were mutated. Console had zero warnings/errors. Syntax checks, 26 existing frontend tests and static build passed. Backend unchanged; upload/scoring algorithms were not re-tested because their implementation did not change.

final result: passed


# Mobile carousel clearance — October 3, 2026

User screenshot showed rotation dots/arrows crossing the cyan border above Around the arcade. Reproduced at 390px: rotation bottom 484.64 vs divider top 481.69. Scoped the fix to <=500px: reserve bottom clearance, increase control-row padding, slightly reduce marquee allocation, and let the cabinet artwork row shrink proportionally when vertical space is tight. Score and initials typography unchanged. Date row keeps its existing reserved height even for undated legacy records.

In-app browser checks at 320×568, 390×844, 430×932. Initial fixed-size attempt still overlapped at 320; flexible cabinet-row sizing resolved that (4.27px control-box-to-divider gap). At 430 the gap is 6.44px. Final 390 screenshot confirms Dig Dug, three cabinet images/labels, carousel and next section are separated. Screenshot: docs/screenshots/mobile-carousel-fixed.png. No console warnings/errors. 26 frontend tests passed; build and diff check passed. Desktop CSS outside the mobile query is unchanged. Physical iPhone Safari not directly tested.

final result: passed
