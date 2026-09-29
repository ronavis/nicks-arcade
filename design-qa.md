# Design and interaction QA — 2026-09-29

Status: **Local design/interaction pass**. Production acceptance remains pending.

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

## Remaining production/device checks

Real Google sign-in/authorized origin/consent, public API through nginx, physical QR scan, live multi-device submission and restart, Nick's physical TV browser/fullscreen/rotation, off-host scheduled backups and ambiguous source game mappings. Fullscreen and rotation controls are implemented but not certified on the target hardware. No live deploy was performed.
