# Design and interaction QA — 2026-09-29

Status: **Local design/interaction and live core-flow checks passed**. Physical TV, the original iPhone photo retry and a second real account remain pending. The initial checks below are historical; follow-up results appear at the end.

## Reference and intentional choices

Reference: selected “Record Spotlight · Arcade Initials” revision (`exec-c8d1f9fe-d53b-4122-8885-311e69c2b60d.png`). Compared the reference alongside actual TV and phone screenshots in one visual review. Screenshots are saved in the parent outputs/screenshots directory.

Retained turquoise/cream, solid black arcade typography, red record accent, one dominant record, three smaller games, persistent QR, and the full A–Z keypad with DEL. Used bundled Jersey 10 as the available blocky face. Actual game artwork from Nick's files replaces the generated mockup's invented artwork, including the NES Tetris logo. Compact mobile labels leave room for touch targets and Post score. Local test identities are labeled instead of displaying a false Google sign-in claim.

## Visual checks

- 1080×1920 TV: board bottom exactly 1920; document 1080×1920, no overflow. Initials bottom 1045, neighboring section begins 1138: no collision.
- 540×960 portrait: traversed all 32 featured games; no rotation-control/neighbor-section overlap, including long game titles.
- 390×844 phone: 375 CSS-pixel content plus browser scrollbar; no horizontal overflow. A–Z and DEL have at least 44px height. Score, initials, photo action and Post score fit the entry view. Photos add a preview and may require scrolling.
- Desktop normal 1280px browser: side-by-side composition verified and saved as working-preview.png. Narrow preview stacks the panels.
- Actual screenshot comparison found a featured-initials overlap; fixed by reserving space for the logo, digits, initials and rotation controls. Removed obsolete banner height rule causing TV vertical overflow.
- Font cache mismatch fixed by giving the replacement font its own asset filename.
- Final mobile-entry.png and tv-portrait.png inspected alongside selected reference. No unresolved P0/P1/P2 visual findings in the tested states.

## Browser interactions exercised

- Preview player sign-in, A–Z selection, three-slot live display and DEL.
- Entered 42,500 / RON with a photo; successful submission appeared automatically on a separate TV tab.
- Opened admin view, loaded the saved proof image (375×893), corrected 42,500 to 42,600 and removed the disposable submission. Original 41,510 / JJH returned to the board; removal remains in history.
- Restarted local service; retained original record and database history.
- Game picker search for “excite” selected VS. Excitebike, changed to time input and explained minutes:seconds.hundredths and lower-is-better.
- Signed-out entry fields disabled. Preview cannot masquerade as Google authentication.
- No errors/warnings in the captured browser console for the final preview flow.

## Automated evidence

`npm run check` and `npm run build` passed. `python -m pytest -q`: **37 passed**, including a complete database/photo backup restored into an independent app instance. Google verification tests use locally signed test tokens with mocked certificate retrieval, exercising signature/audience/issuer/expiry checks; they are not a real Google browser login.

## Checks pending at the initial local review (historical)

Real Google sign-in/authorized origin/consent, public API through nginx, physical QR scan, live multi-device submission and restart, Nick's physical TV browser/fullscreen/rotation, off-host scheduled backups and ambiguous source game mappings. Fullscreen and rotation controls are implemented but not certified on the target hardware. No live deploy was performed.

## Production follow-up

Real Google sign-in, public score/photo submission, admin proof retrieval, correction/removal and automatic fallback passed on 2026-09-29. Production score and photo were included in a restored off-host backup. A rotation sizing bug discovered during launch was corrected and visually verified at 960×540. Ron subsequently confirmed phone QR scan, Google sign-in and score entry. Physical TV acceptance and the original iPhone photo retry remain pending; see deploy/launch-status.md.

## Catalog, photos and initials follow-up

- 47 backend tests passed after the catalog and iPhone photo update. All 33 supplied game names were found in browser search without punctuation/spaces; a missing-game first-record submission succeeded in local preview.
- The new-game dialog was visually checked at 390×844. The live Simpsons entry page loaded its artwork and first-record prompt.
- HEIC and 48-megapixel JPEG conversion passed in tests and an isolated instance on the production VPS. This does not substitute for retrying Ron’s original phone photo.
- Featured initials were enlarged approximately 17% with positive letter spacing. At 540×960 and 1080×1920 they did not overlap the score or rotation controls. Published HTML/CSS matched the build; live browser inspection confirmed the changed font size and spacing.

## Cabinet gallery review — October 1, 2026

Source visual: `/Users/studio/.codex/generated_images/01a0ed69-4bdd-71d2-b765-99cd8dd40c66/exec-e15441aa-f6a0-4f88-9771-37f59e345635.png` (1487 × 1058).
Implementation: `../cabinets-desktop.png` (1440 × 1024); phone captures `../cabinets-mobile.png` and `../cabinets-mobile-detail.png` (390 × 844).

State: local admin, Manage cabinets, Pac-Man filter, Pac-Man Cabinet selected. Desktop screenshot and source were opened together in one visual comparison. The source uses illustrative cabinet-specific art and invented hardware description; implementation intentionally uses a labeled generic illustration until actual photos are uploaded, and omits unsupported hardware claims. User requested removing Cabinets/Games tabs and keeping the existing Manage games screen. Source and implementation use near-identical aspect ratios; comparison covers overall hierarchy rather than pixel-identical raster sizing. Gallery, selected outline, cream/cyan palette and detail/game rows are preserved. Focused mobile captures verify the detail transition and readable controls.

Iteration findings: compacted the full-width Add games button, moved Add cabinet to the header on desktop, and prevented detail focus from scrolling the close control out of view on phones. Post-fix captures show the final layout. No remaining P0/P1/P2 findings. P3: actual cabinet photos would distinguish tiles better.

Browser checks: local admin login, menu access, gallery search, selecting cabinet, creating a test cabinet, adding Galaga as a fourth assignment, removing only that assignment, catalog search, existing Manage games Assigned cabinets action, and 390px responsive gallery/detail. Console error readback empty. Backend verifies role denial, persistence across app recreation, stale updates, photo processing and backup restoration. Latest checks: 81 backend tests, 11 frontend tests, JS syntax and static build pass. No production deployment or physical iPhone test claimed.

final result: passed

### October 1 — completed cabinet inventory and two marquee replacements

- Syntax checks, 11 frontend tests, static build and 82 backend tests passed.
- Upgrade test preserves every score row, an existing custom marquee/eligibility choice and an admin-removed cabinet assignment.
- Fresh inventory: 18 cabinets, 98 games, 65 newly created scoreless games. Unresolved MC2/five unassigned titles excluded.
- Local browser verified Dragon’s Lair cabinet contains all three games and each image loaded successfully. Unclaimed labels appear only on the two scoreless games.
- Desktop 1440×1024 and mobile 390×844 checked; mobile detail has no horizontal overflow. Screenshots saved outside the repo in outputs/cabinet-dragons-lair-complete.png and outputs/cabinet-dragons-lair-mobile.png.
- Local-only verification; no live deployment or production data changes. Remaining catalogue artwork gaps still use the neutral fallback.

### October 1 — full collection artwork pass

Scanned all 98 local database games (all eligible): 59 initial placeholders; after correction, 98 working image responses and zero placeholders/failures. All local image files passed Pillow decoding. The 58 new game-specific assets were visually reviewed, then optimized to 8.26 MB total WebP. Pac-Man, Neo Geo and CPS cabinet artwork was checked in the browser. Source manifest, exceptions and complete per-game results are recorded in data/artwork-provenance.json, docs/artwork-sources.md and docs/artwork-audit.md. This is a local candidate, not published or a claim of full search-library coverage.

### October 1 — spreadsheet inventory import

- Added admin-only CSV preview/commit with additive, transactional writes and an import audit.
- 85 backend tests, 11 frontend tests, syntax checks and static build passed. Coverage includes preview with no writes, role enforcement, malformed files/headers, scoring conflicts, all-or-nothing errors, stale previews, UTF-8 BOM, duplicate rows and repeat imports, and score/artwork/eligibility preservation.
- Browser uploaded a test CSV, previewed one assignment, committed it and verified a second preview had zero additions. Temporary assignment was removed through the UI.
- CSV and Excel templates were exported, visually inspected and served successfully by the local site. CSV parsed with zero errors. README and app link to both.
- Import modal verified at desktop and 390px mobile width, with no horizontal overflow.
- No live deployment; GitHub publication remains pending with the cabinet feature.
