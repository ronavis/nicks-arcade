import os
import shutil
import glob
import re

games = [
    "Asteroids", "BurgerTime", "Bust-A-Move", "Centipede", "Crystal Castles",
    "Dig Dug", "Donkey Kong", "Donkey Kong Junior", "Donkey Kong 3", "Dragon's Lair",
    "Frogger", "Galaga", "Gauntlet II", "Mappy", "Ms. Pac-Man", "Pac-Land",
    "Pac-Man", "Pac-Mania", "Pengo", "Q*bert", "Shinobi", "Space Invaders",
    "Star Wars", "Street Fighter", "Street Fighter II The World Warrior",
    "Street Fighter II Champion Edition", "Street Fighter II Hyper Fighting",
    "VS. Excitebike", "The Goonies", "Super Mario Bros.", "Super Mario Bros. 3", "Tetris"
]

mapping = {
    "Asteroids": "asteroid",
    "BurgerTime": "btime",
    "Bust-A-Move": "pbobble", # or bustamov
    "Centipede": "centiped",
    "Crystal Castles": "ccastles",
    "Dig Dug": "digdug",
    "Donkey Kong": "dkong",
    "Donkey Kong Junior": "dkongjr",
    "Donkey Kong 3": "dkong3",
    "Dragon's Lair": "dlair",
    "Frogger": "frogger",
    "Galaga": "galaga",
    "Gauntlet II": "gaunt2",
    "Mappy": "mappy",
    "Ms. Pac-Man": "mspacman",
    "Pac-Land": "pacland",
    "Pac-Man": "pacman",
    "Pac-Mania": "pacmania",
    "Pengo": "pengo",
    "Q*bert": "qbert",
    "Shinobi": "shinobi",
    "Space Invaders": "invaders",
    "Star Wars": "starwars",
    "Street Fighter": "sf",
    "Street Fighter II The World Warrior": "sf2",
    "Street Fighter II Champion Edition": "sf2ce",
    "Street Fighter II Hyper Fighting": "sf2hf",
    "VS. Excitebike": "vsxcite",
    "The Goonies": "goonies",
    "Super Mario Bros.": "suprmrio",
    "Super Mario Bros. 3": "smb3",
    "Tetris": "tetris"
}

source_dir = r"C:\Users\Ron\.gemini\antigravity-ide\scratch\nicks-arcade\images\mame_marquees"
dest_dir = r"C:\Users\Ron\.gemini\antigravity-ide\scratch\nicks-arcade\images"

# List all available files
available = os.listdir(source_dir)
available_lower = {f.lower(): f for f in available}

for game in games:
    clean_name = re.sub(r'[^a-z0-9]', '', game.lower())
    mame_name = mapping.get(game, clean_name)
    
    # Try exact png
    target = f"{mame_name}.png"
    if target in available_lower:
        shutil.copy(os.path.join(source_dir, available_lower[target]), os.path.join(dest_dir, f"{clean_name}.png"))
        print(f"Copied {target} for {game}")
        continue
        
    # Try bustamov for bust-a-move
    if game == "Bust-A-Move" and "bustamov.png" in available_lower:
        shutil.copy(os.path.join(source_dir, available_lower["bustamov.png"]), os.path.join(dest_dir, f"{clean_name}.png"))
        print(f"Copied bustamov.png for {game}")
        continue
        
    # Try fuzzy match
    found = False
    for f in available:
        if f.startswith(mame_name) and f.endswith(".png"):
            shutil.copy(os.path.join(source_dir, f), os.path.join(dest_dir, f"{clean_name}.png"))
            print(f"Copied {f} (fuzzy) for {game}")
            found = True
            break
            
    if not found:
        print(f"MISSING: {game} (looked for {mame_name})")
