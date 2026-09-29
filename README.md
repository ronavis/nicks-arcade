# Nick's Arcade

A portrait arcade record board and a phone score-entry app. Starting with Nick's original 32 records, keeping the turquoise-and-cream design and authentic game artwork.

## What works

- Portrait 9:16 TV board, rotating featured game, three neighboring records, permanent QR, fullscreen and rotation controls.
- Phone entry with Google sign-in, a clickable A–Z keypad, three initials, DEL, and optional proof photo.
- Scores appear without approval; the TV refreshes every five seconds. Lower scores remain in history. Equal scores preserve the earlier record. VS. Excitebike uses the lowest time.
- Admin correction/removal, conflict protection, audit history and JSON export. Removing the top score promotes the best remaining entry.
- Search ignores punctuation and spaces. The Simpsons is ready for its first record; signed-in players can add any missing game with their first score. New games persist in the shared database and appear on the TV.
- iPhone HEIC/HEIF, JPG, PNG and WebP proof photos up to 40 MB and 64 megapixels are automatically resized to a maximum 1600-pixel edge and saved as JPEG.
- Durable SQLite database and separate photo storage. Public responses exclude account details. Photos require sign-in and uploads are re-encoded to remove metadata.

## Local preview

Requires Node 22 and Python 3.11+ (verified with Python 3.12).

```sh
npm ci
npm run build
python3.12 -m venv .venv
.venv/bin/pip install -r tests/requirements.txt
ARCADE_DEMO=1 .venv/bin/python -m server.app
```

Open `http://127.0.0.1:4173/?view=preview` for the side-by-side design, `/#play` for phone entry, or `/#tv` for the display. Preview sign-in buttons create **local test identities**, not Google sessions. The banner makes that distinction explicit. The preview binds only to loopback and its database is `.local-preview/`; production cannot enable the demo route through the normal server factory.

Do not scan the local preview QR from a phone: localhost refers to the phone itself. The production QR is generated from `ARCADE_PUBLIC_URL` after deployment.

## Production architecture

GitHub Pages hosts the built `dist/` frontend. An isolated Python service on the VPS owns scores, authentication verification, and photos. GitHub Pages itself does not save submissions or run the database.

Build for production with `ARCADE_API_BASE=https://midconversation.com/arcade-api npm run build`. The build writes the endpoint into the published config while leaving the local preview configuration unchanged. The API verifies Google's signed ID tokens; a typed email or browser flag cannot grant administrator rights. Existing public Google client ID is retained, and Ron is the initial administrator.

Keep `ARCADE_DATA_DIR` outside releases. Rebuilding or replacing frontend files must never replace that directory. See [deployment plan](deploy/README.md) for the staged setup, production acceptance, backup and rollback steps. Production API and GitHub Pages were deployed on 2026-09-29. See deploy/launch-status.md for completed and pending acceptance checks.

## Validation

```sh
npm run check
npm run build
.venv/bin/python -m pytest -q
```

Tests cover persistent records, independent clients, concurrency, duplicate retries, score/time validation, verified Google-token claims, administrator authorization, correction/removal history, photo processing/privacy, origin restrictions, rate limits, and backups. See [design QA](design-qa.md) for visual and browser verification.

## Source record questions before opening night

All 32 starting values are imported once from the existing repository, never overwritten on restart. Original imported timestamps are unknown. The source slide and repo disagree on Bubble Bobble / Bust-a-Move and one Street Fighter edition; these mappings remain unchanged pending confirmation. VS. Excitebike's legacy `1:02:30` is interpreted as `1:02.30` (minutes:seconds.hundredths), matching the existing order but requiring confirmation at the cabinet.

This does not silently import earlier browser-local scores. Export any real scores entered in the old site before switching.

## Artwork and packages

Existing game artwork remains in the repository; the build copies only the 32 used files. Four marquees were recovered from Nick's shared source presentation. Game marks belong to their owners. Jersey 10 (OFL), Phosphor (MIT), and QRCode (MIT) notices ship in `dist/vendor/licenses/`.
