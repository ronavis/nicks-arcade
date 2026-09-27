import urllib.request
import urllib.parse
import json
import re
import os
import time

GAMES = [
    "Asteroids", "BurgerTime", "Bust-A-Move", "Centipede", "Crystal Castles",
    "Dig Dug", "Donkey Kong", "Donkey Kong Junior", "Donkey Kong 3", "Dragon's Lair",
    "Frogger", "Galaga", "Gauntlet II", "Mappy", "Ms. Pac-Man", "Pac-Land",
    "Pac-Man", "Pac-Mania", "Pengo", "Q*bert", "Shinobi", "Space Invaders",
    "Star Wars", "Street Fighter", "Street Fighter II The World Warrior",
    "Street Fighter II Champion Edition", "Street Fighter II Hyper Fighting",
    "VS. Excitebike", "The Goonies", "Super Mario Bros.", "Super Mario Bros. 3", "Tetris"
]

images_dir = os.path.join('C:\\Users\\Ron\\.gemini\\antigravity-ide\\scratch\\nicks-arcade', 'images')
os.makedirs(images_dir, exist_ok=True)

def fetch_bing_image(query):
    url = "https://www.bing.com/images/search?q=" + urllib.parse.quote(query)
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'})
    try:
        html = urllib.request.urlopen(req).read().decode('utf-8', errors='ignore')
        urls = re.findall(r'murl&quot;:&quot;(.*?)&quot;', html)
        if urls:
            return urls[0]
    except Exception as e:
        print("Error fetching Bing", e)
    return None

for game in GAMES:
    print("Searching marquee for", game)
    query = f"{game} arcade marquee flyer clear"
    img_url = fetch_bing_image(query)
    if img_url:
        print("  Found:", img_url)
        try:
            req = urllib.request.Request(img_url, headers={'User-Agent': 'Mozilla/5.0'})
            img_data = urllib.request.urlopen(req, timeout=10).read()
            filename = re.sub(r'[^a-z0-9]', '', game.lower()) + '.jpg'
            with open(os.path.join(images_dir, filename), 'wb') as f:
                f.write(img_data)
        except Exception as e:
            print("  Failed downloading image", e)
            
            # Fallback to second image
            print("  Trying second image fallback...")
            try:
                html = urllib.request.urlopen(urllib.request.Request("https://www.bing.com/images/search?q=" + urllib.parse.quote(query), headers={'User-Agent': 'Mozilla/5.0'})).read().decode('utf-8', errors='ignore')
                urls = re.findall(r'murl&quot;:&quot;(.*?)&quot;', html)
                if len(urls) > 1:
                    img_url2 = urls[1]
                    req2 = urllib.request.Request(img_url2, headers={'User-Agent': 'Mozilla/5.0'})
                    img_data2 = urllib.request.urlopen(req2, timeout=10).read()
                    with open(os.path.join(images_dir, filename), 'wb') as f:
                        f.write(img_data2)
            except Exception as e2:
                print("  Fallback failed", e2)
    else:
        print("  No image found for", game)
    time.sleep(1)
