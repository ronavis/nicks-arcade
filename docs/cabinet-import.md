# Starting cabinet inventory

Source: Nick's October 1, 2026 email, "Nick's Arcade List", Excel attachment `Nick's Arcade List.xlsx`, tabs `Sheet1` and `Nicks-Arcade`.

`data/cabinets.json` contains 18 described cabinet codes and their game titles. The v1 migration creates cabinets and exact existing-title links. The v2 migration completes confirmed assignments and creates missing eligible games without scores. A fresh database has 98 games (33 original plus 65 new); existing production additions may change that total.

Reviewed aliases reuse Donkey Kong Junior and the existing Street Fighter II World Warrior, Champion Edition and Hyper Fighting entries. Dragon's Lair II is displayed as Dragon's Lair II: Time Warp. Nintendo Vs. titles remain separate from ambiguous legacy Nintendo records: those scores are not transferred by assumption.

Both migrations run once, transactionally. The v2 upgrade respects any game with an administrator assignment audit, and preserves existing scores, game eligibility, uploaded marquees and cabinet edits. Subsequent restarts do not recreate removed links. No live Google file is modified or synchronized.

Dragon's Lair Cabinet now contains Dragon's Lair, Dragon's Lair II: Time Warp, and Space Ace. The latter two have documented local cabinet artwork. The full current 98-game collection now has artwork coverage; Space Invaders Color uses shared Space Invaders artwork. Games without records show “Be the first to set a record.”

Pending source questions:
- MC2 has game assignments but no cabinet description in the lookup. No MC2 cabinet is invented; games with other confirmed cabinet assignments are still imported there.
- The King of Fighters Neowave, Ninja Gaiden, Playchoice-10: Super Mario Bros., Playchoice-10: Super Mario Bros. 3, and Tekken 4 have no cabinet assignments.
- Legacy Nintendo scores require explicit edition confirmation before linking them to Nintendo Vs. titles.

Generic cabinet art is generated illustration, not a photo of Nick's equipment. Admins may upload actual cabinet photographs. Cabinet management, confirmed assignments and the preview-first importer were deployed on October 1, 2026. The unresolved source questions above remain open.

## Future inventory imports

Use the README-linked Excel/CSV template. Upload the Excel workbook directly (only Games is read), or export the Games sheet as CSV. Manage cabinets → Import spreadsheet performs a read-only preview followed by an explicit additive commit. Standard-library CSV parsing supports quoted names, UTF-8 BOMs, blank cabinet cells and repeated game rows. Matching uses normalized exact game/cabinet names, without fuzzy edition guesses. Existing scores, eligibility, photos, marquees and assignments are preserved. See README for the schema and limits.
