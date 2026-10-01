# Artwork source notes

## The Simpsons

Replaced the space-themed pack image on September 29, 2026 with the cabinet marquee from [LaunchBox Games Database](https://gamesdb.launchbox-app.com/games/images/2327-the-simpsons), listed as Arcade - Marquee, 3840 x 1132.

Source image: https://images.launchbox-app.com/ac673f59-67e8-4271-9cd5-a41e74b2e17e.jpg

Converted to PNG for the existing catalog path without changing dimensions or artwork. Game marks/artwork belong to their respective owners.

## NBA Jam and unclaimed games

NBA Jam uses the original 3840 × 1138 cabinet marquee from [LaunchBox Games Database](https://gamesdb.launchbox-app.com/games/images/10554-nba-jam).

Source image: https://images.launchbox-app.com/f33928fb-9b67-4285-9cf6-8e17d609c6b4.jpg

Stored unchanged as `images/cabinet-marquees/nbajam.jpg`. Artwork belongs to its respective owners. The build combines the existing curated game images with `data/artwork.json`; `artwork.js` matches titles and explicit aliases for games that lack assigned artwork or contain a rejected pack reference. This applies to unclaimed games and scored games alike. Unmatched editions retain the neutral fallback; the old space-themed packs are not used as automatic matches.

## Searchable collection catalog

`data/arcade-catalog.json` indexes 9,543 entries from the existing MAME artwork library, with human-readable names from [Libretro MAME metadata](https://github.com/libretro/libretro-database/blob/master/metadat/mame/MAME.dat). Regional/revision variants remain separate. Some entries without matching metadata are searchable by their ROM identifier.

1,685 exact ROM matches prefer the supplementary [Snapouille cabinet-marquee collection](https://github.com/Snapouille/DX_Theme_Arcade_Add-On), pinned to commit `fa59103d8d1ad2f3248874cda9ffc7b15c36c4ea`. Established curated arcade images and the corrected Simpsons/NBA Jam images override pack artwork. The frontend now rejects the old space-background pack URLs, including references already saved for games. It resolves exact title/ROM matches from the supplementary and curated artwork index, then uses a neutral placeholder when no replacement exists. Catalog results label that case “Marquee unavailable.” All 9,543 games remain searchable. The backend catalog retains historical image references; the shared frontend resolver prevents those rejected images from rendering on any app surface. Images are loaded on demand from pinned public GitHub files, with a neutral graphic on load failure. No entire artwork pack is downloaded to players’ devices. Game artwork belongs to its respective owners.

## Token favicon background

Ron supplied `images/nicks-arcade-token.jpg`. The built-in image tool produced `images/nicks-arcade-token-turquoise.png`; that asset supplies the PNG/ICO browser icons and Apple touch icon. Original retained.

Edit prompt: “Edit the supplied Nick's Arcade token photograph for use as a square favicon. Replace ONLY the white background outside the circular token with solid turquoise #27c4cd. Preserve the gold coin, exact lettering Nick's Arcade, original patina, details, proportions and framing. Do not redesign or redraw the coin, add anything, or change text. Output square image with opaque turquoise background.”

## Puzzle Bobble

Nick corrected the imported record from Bubble Bobble to Puzzle Bobble on September 30, 2026. Cabinet artwork: [LaunchBox Puzzle Bobble marquee](https://gamesdb.launchbox-app.com/games/images/38330-bust-a-move), Japanese marquee https://images.launchbox-app.com/756610fa-9134-4788-85fa-b02edcb9823e.png, stored as `images/cabinet-marquees/puzzle-bobble.png`. Original Bubble Bobble artwork remains available for that separate game.

## Bust-A-Move display artwork

Ron requested the Bust-A-Move name if no better Puzzle Bobble marquee was available. Using the clean, wide logo from [LaunchBox](https://gamesdb.launchbox-app.com/games/images/38330-bust-a-move), https://images.launchbox-app.com/ed5349f3-dc34-4136-ac22-14d817c934c5.png, resized proportionally to 1600px. This is a clear logo, not a cabinet marquee scan. Original game ID, scores and ownership are preserved.

## Puzzle Bobble clear logo (current)

Ron chose the Puzzle Bobble name and logo instead of Bust-A-Move. The transparent Japan clear logo from [LaunchBox](https://gamesdb.launchbox-app.com/games/images/38330-bust-a-move) is [this source PNG](https://images.launchbox-app.com/2de4a3cc-6932-48c1-a733-68747a392ee9.png), resized proportionally to 1600 px and saved as `images/cabinet-marquees/puzzle-bobble-logo.png`. All score rows and the historical internal game ID remain unchanged. Admin-uploaded artwork takes precedence over this and all catalog defaults.

## Dragon’s Lair cabinet games (October 1, 2026)

Space Ace uses the [LaunchBox Arcade marquee](https://gamesdb.launchbox-app.com/games/images/38989-space-ace), [original JPEG](https://images.launchbox-app.com/b8bc8b65-264a-4fcc-a0d1-1b8a86e7e436.jpg), 3840 × 1203. Stored unchanged at `images/cabinet-marquees/space-ace.jpg`.

Dragon’s Lair II: Time Warp uses the [LaunchBox Arcade marquee](https://gamesdb.launchbox-app.com/games/images/11819-dragons-lair-ii-time-warp), [original PNG](https://images.launchbox-app.com/f576c1ab-3b25-449f-a6d2-8fd1f553aa82.png), 1920 × 540. Stored unchanged at `images/cabinet-marquees/dragons-lair-ii.png`.

Both were visually reviewed. Explicit title/ROM aliases resolve imported titles and neutral/rejected catalog images to these files. Admin-uploaded marquees retain priority. Artwork belongs to its respective owners; catalog-wide artwork gaps remain.

## Galaxian, Dig Dug II and Super Pac-Man (October 1, 2026)

Added visually reviewed Arcade marquees from LaunchBox, stored unchanged locally:

- [Galaxian](https://gamesdb.launchbox-app.com/games/images/7561-galaxian): [source JPEG](https://images.launchbox-app.com/3e28c2c2-df0c-4838-81ff-f2a5adc7bfa4.jpg), 3840 × 957, `images/cabinet-marquees/galaxian.jpg`.
- [Dig Dug II](https://gamesdb.launchbox-app.com/games/images/26068-dig-dug-ii): [source JPEG](https://images.launchbox-app.com/c408a5b0-59a3-4e92-8339-e274f870fcb7.jpg), 3840 × 1414, `images/cabinet-marquees/dig-dug-ii.jpg`.
- [Super Pac-Man](https://gamesdb.launchbox-app.com/games/images/7547-super-pac-man): [source JPEG](https://images.launchbox-app.com/40fd0d10-a836-4194-84df-8e7aecfc4d63.jpg), 3840 × 1430, `images/cabinet-marquees/super-pac-man.jpg`.

Shared title/ROM aliases replace neutral or rejected-pack artwork across the app. Custom admin-uploaded marquees retain priority. Artwork belongs to its respective owners.

## Full collection artwork audit — October 1, 2026

Audited all 98 games returned by the local cabinet preview API, including scoreless imported titles. Initially 59 resolved to the neutral placeholder. Added 58 game-specific assets from the [LaunchBox public metadata export](https://gamesdb.launchbox-app.com/Metadata.zip): 46 marquee images and 12 clear logos after visual review. Exact source image URLs, matched database titles and IDs are recorded in `data/artwork-provenance.json`. Full database export stays outside the repository.

Neo Geo card-style layouts were replaced with clear logos for readability. A mislabeled Hyper Street Fighter II marquee was rejected in favor of the Anniversary Edition logo. Assets are proportionally fitted within 1600 × 800 and encoded as WebP quality 88, preserving transparency and avoiding upscaling. Artwork belongs to the respective owners.

Space Invaders Color shares the existing Space Invaders branding; this is intentionally not claimed as a unique Color-edition marquee. The sheet's shortened “Street Fighter III” uses New Generation artwork; edition-specific scores were not merged or changed. All other reviewed title expansions are recorded in the provenance manifest.

This audit covers the actual 98-game collection, not every regional/bootleg variant in the 9,543-entry search catalog. The broader search catalog may still show neutral placeholders. Uploaded admin marquees remain higher priority than these defaults.

Repeat the read-only current-collection check after building:

```sh
npm run build
npm run audit:artwork -- http://127.0.0.1:4174
```

The audit reads the leaderboard, uses the actual artwork resolver, and checks every resolved image URL for an image response with a non-empty body. Missing/failing artwork returns a nonzero exit status. It does not modify scores or game assignments. Local raster files were separately decoded with Pillow and new source artwork was visually reviewed.
