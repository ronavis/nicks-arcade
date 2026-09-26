import os
import json
import time
import re
import urllib.request
import urllib.error

CLIENT_ID = 'f958z59fr523uuj802cnfd8ltw3k4u'
CLIENT_SECRET = '3p8shavopgf2ey8tq0fjlhlxrad08k'

def get_twitch_token():
    url = f"https://id.twitch.tv/oauth2/token?client_id={CLIENT_ID}&client_secret={CLIENT_SECRET}&grant_type=client_credentials"
    req = urllib.request.Request(url, method='POST')
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            return data['access_token']
    except urllib.error.URLError as e:
        raise Exception(f"Twitch OAuth Error: {e}")

GAMES = [
    "Asteroids", "BurgerTime", "Bust-A-Move", "Centipede", "Crystal Castles",
    "Dig Dug", "Donkey Kong", "Donkey Kong Junior", "Donkey Kong 3", "Dragon's Lair",
    "Frogger", "Galaga", "Gauntlet II", "Mappy", "Ms. Pac-Man", "Pac-Land",
    "Pac-Man", "Pac-Mania", "Pengo", "Q*bert", "Shinobi", "Space Invaders",
    "Star Wars", "Street Fighter", "Street Fighter II The World Warrior",
    "Street Fighter II Champion Edition", "Street Fighter II Hyper Fighting",
    "VS. Excitebike", "The Goonies", "Super Mario Bros.", "Super Mario Bros. 3", "Tetris"
]

def fetch_images():
    print("Getting token...")
    try:
        token = get_twitch_token()
    except Exception as e:
        print(f"Failed to get token: {e}")
        return

    headers = {
        'Client-ID': CLIENT_ID,
        'Authorization': f'Bearer {token}',
        'Content-Type': 'text/plain'
    }

    images_dir = os.path.join('C:\\Users\\Ron\\.gemini\\antigravity-ide\\scratch\\nicks-arcade', 'images')
    os.makedirs(images_dir, exist_ok=True)

    for game in GAMES:
        print(f"Searching for {game}...")
        body = f'search "{game}"; fields name, artworks.image_id, screenshots.image_id, cover.image_id; limit 1;'
        req = urllib.request.Request('https://api.igdb.com/v4/games', data=body.encode('utf-8'), headers=headers, method='POST')
        
        try:
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read().decode())
                if data:
                    game_data = data[0]
                    image_id = None
                    
                    if 'artworks' in game_data and len(game_data['artworks']) > 0:
                        image_id = game_data['artworks'][0]['image_id']
                    elif 'screenshots' in game_data and len(game_data['screenshots']) > 0:
                        image_id = game_data['screenshots'][0]['image_id']
                    elif 'cover' in game_data:
                        image_id = game_data['cover']['image_id']
                    
                    if image_id:
                        img_url = f"https://images.igdb.com/igdb/image/upload/t_screenshot_med/{image_id}.jpg"
                        print(f"  Found image: {img_url}")
                        
                        img_req = urllib.request.Request(img_url)
                        try:
                            with urllib.request.urlopen(img_req) as img_res:
                                filename = re.sub(r'[^a-z0-9]', '', game.lower()) + '.jpg'
                                with open(os.path.join(images_dir, filename), 'wb') as f:
                                    f.write(img_res.read())
                        except Exception as e:
                            print(f"  Failed to download image: {e}")
                    else:
                        print(f"  No image ID found for {game}.")
                else:
                    print(f"  No results found for {game}.")
        except urllib.error.URLError as e:
            error_body = e.read().decode() if hasattr(e, 'read') else ''
            print(f"  API Error: {e} {error_body}")
            
        time.sleep(0.3)

if __name__ == '__main__':
    fetch_images()
