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
