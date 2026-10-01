# Cabinet image release — October 1, 2026

- Source implementation: `ffb7a16`; Pages publication: `be8c3e4`.
- 18 real reference cabinet images bundled locally with source provenance in `data/cabinet-art.json`.
- Custom uploaded photos retain priority in management, assignments and the featured display.
- Public leaderboard exposes only cabinet ID, name, reference code and current photo ID; management remains admin-only.
- Validation: 91 backend tests, 11 frontend tests, JavaScript syntax checks and production build passed.
- Browser checks: cabinet management images, tap-to-open cabinet list, portrait 540×960 and mobile 390×844. Four tile bounds were identical in each viewport. No physical Firestick test performed.
- Backend release `/opt/nicks-arcade/releases/ffb7a16`; pre-release backup `/var/backups/nicks-arcade/pre-cabinet-images-ffb7a16`.
- Readback compared every SQLite table with the backup: all unchanged, including 37 scores, 98 games, 18 cabinets, 122 assignments and 34 score audit entries.
- Reference images are not verified photographs of Nick’s exact machines. An admin may upload an actual photo in Manage cabinets → Edit cabinet.
