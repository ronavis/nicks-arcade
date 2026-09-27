# Nick's Arcade

Welcome to **Nick's Arcade**! This is a web-based, retro-styled High Score tracking application. 
Designed to look exactly like an arcade cabinet's attract mode, this project features a glowing neon aesthetic, CRT scanline overlays, and a dynamic scrolling list of classic games and their top scores.

## Features

- **Retro Aesthetics**: Custom CRT scanline effects, glowing neon text, and classic arcade fonts (`Press Start 2P` and `VT323`).
- **Attract Mode Scroll**: The high score list slowly crawls up the screen indefinitely, perfectly mimicking an idle arcade machine.
- **Admin Login via QR Code**: Scanning the QR code at the bottom of the screen (or clicking it) opens a simulated Google Sign-In portal.
- **High Score Entry**: Authorized admins can search for a game and update the high score and initials directly from the web interface. 
- **Authentic Marquees**: Game entries feature high-resolution, restored arcade marquees sourced from the ProgettoSnaps arcade database.

## Setup and Usage

Because this is a static frontend site, no build steps are required!

1. Clone the repository: `git clone https://github.com/ronavis/nicks-arcade.git`
2. Open `index.html` in any modern web browser.
3. Enjoy the retro scrolling attract mode!

## Admin Features

To enter a new score:
1. Click the QR code at the bottom of the list.
2. When the Google Sign-In prompt appears, enter an admin email (e.g. `nick@gmail.com` or `ron@gmail.com`).
3. Search for the game you wish to update.
4. Input the new score and the player's 3-letter initials.
5. Hit Submit, and the list will instantly reflect the changes!

## Technologies Used

- HTML5 / Vanilla CSS3 / JavaScript
- `qrcode.js` for dynamic QR Code generation
- ProgettoSnaps HD Marquees
- Hosted on GitHub Pages
