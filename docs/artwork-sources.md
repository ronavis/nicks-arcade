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
