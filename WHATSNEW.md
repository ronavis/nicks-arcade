# What's New

Keep track of the latest changes, updates, and feature additions to Nick's Arcade here!

## [v1.2.0] - 2026-09-26
### Added
- Created `README.md` and `WHATSNEW.md` to properly document the repository structure, usage instructions, and changelog.

### Changed
- **Artwork Overhaul**: Replaced all low-quality marquee thumbnails with high-definition, hand-restored arcade marquees directly downloaded from the official ProgettoSnaps artwork database.

## [v1.1.0] - 2026-09-26
### Added
- **Attract Mode Scroll**: Implemented a CSS-based continuous vertical scroll animation for the game list, recreating the idle "attract mode" of a real arcade machine.
- **Admin QR Login**: Added a dynamically generated QR Code at the bottom of the scroll list. Scanning or clicking it opens a simulated Google Sign-In prompt.
- **High Score Entry Form**: Added a modal UI for admins to search for a game and submit new high scores and player initials on the fly.

### Changed
- Rebuilt the layout from a blocky grid into a sleek 3-column row design (Marquee Image | Score | Initials).

## [v1.0.0] - 2026-09-26
### Added
- Initial project creation.
- Basic HTML, CSS, and JS structure with a custom CRT scanline visual effect.
- Manually transcribed the original 32 arcade games and top scores into the JS data array.
- Configured GitHub Pages deployment.
