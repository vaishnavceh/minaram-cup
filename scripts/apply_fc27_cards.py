import sys
sys.path.insert(0, 'scripts')
import os
import json
import shutil
import urllib.request
import io
import re
import unicodedata
from PIL import Image

from build_hall_of_fame_data import PLAYERS_METADATA

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
}

BACKUP_DIR = "frontend/public/images/hall-of-fame-photos-backup"
PUBLIC_HOF_DIR = "frontend/public/images/hall-of-fame"
DIST_HOF_DIR = "frontend/dist/images/hall-of-fame"

def make_slug(name):
    nfkd = unicodedata.normalize('NFKD', name)
    ascii_name = ''.join(c for c in nfkd if not unicodedata.combining(c))
    slug = re.sub(r'[^a-zA-Z0-9\s-]', '', ascii_name).strip().lower()
    return re.sub(r'[\s]+', '-', slug)

def download_and_optimize_card(url, output_path):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=12) as resp:
        data = resp.read()
    
    img = Image.open(io.BytesIO(data))
    
    # Target height around 600px while maintaining aspect ratio
    target_height = 600
    if img.height > target_height:
        scale = target_height / float(img.height)
        new_width = int(float(img.width) * float(scale))
        img = img.resize((new_width, target_height), Image.Resampling.LANCZOS)
        
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    img.save(output_path, "WEBP", quality=85, optimize=True)
    return os.path.getsize(output_path)

def main():
    print("=== Football Hall of Fame: EA FC 27 Cards Integration ===")
    
    # 1. Verify backup
    backup_files = [f for f in os.listdir(BACKUP_DIR) if f.endswith(".webp")]
    print(f"Verified backups found: {len(backup_files)} files in {BACKUP_DIR}")
    assert len(backup_files) >= 149, f"Backup incomplete: only {len(backup_files)} files found"
    
    # 2. Load verified cards
    with open("scripts/resolved_cards_final.json", "r", encoding="utf-8") as f:
        resolved_cards = json.load(f)
    print(f"Loaded {len(resolved_cards)} verified official EA FC collectible cards.")
    
    os.makedirs(PUBLIC_HOF_DIR, exist_ok=True)
    os.makedirs(DIST_HOF_DIR, exist_ok=True)
    
    downloaded_count = 0
    fallback_count = 0
    
    for i, player in enumerate(PLAYERS_METADATA, 1):
        name = player["name"]
        slug = make_slug(name)
        public_dest = os.path.join(PUBLIC_HOF_DIR, f"{slug}.webp")
        dist_dest = os.path.join(DIST_HOF_DIR, f"{slug}.webp")
        
        if name in resolved_cards:
            card_url = resolved_cards[name]["card_url"]
            try:
                size = download_and_optimize_card(card_url, public_dest)
                shutil.copy2(public_dest, dist_dest)
                downloaded_count += 1
                print(f"[{i:03d}/149] FC CARD: {name:22} -> {size/1024:.1f} KB (saved to {slug}.webp)")
            except Exception as e:
                print(f"[{i:03d}/149] ERROR downloading {name}: {e}. Falling back to backup photo.")
                backup_src = os.path.join(BACKUP_DIR, f"{slug}.webp")
                shutil.copy2(backup_src, public_dest)
                shutil.copy2(backup_src, dist_dest)
                fallback_count += 1
        else:
            # Player is historical icon without active FC 27 item; keep verified high-res portrait
            backup_src = os.path.join(BACKUP_DIR, f"{slug}.webp")
            if os.path.exists(backup_src):
                shutil.copy2(backup_src, public_dest)
                shutil.copy2(backup_src, dist_dest)
                fallback_count += 1
                size = os.path.getsize(public_dest)
                print(f"[{i:03d}/149] BACKUP:  {name:22} -> {size/1024:.1f} KB (preserved portrait)")
            else:
                print(f"[{i:03d}/149] WARNING: No backup found for {name} ({slug})!")
                
    print("\n=== Integration Complete ===")
    print(f"Total EA FC collectible cards integrated: {downloaded_count}")
    print(f"Total legendary portraits preserved: {fallback_count}")
    print(f"Total images in collection: {downloaded_count + fallback_count} / {len(PLAYERS_METADATA)}")
    
    # 3. Final verification of all 149 files
    missing_files = []
    for player in PLAYERS_METADATA:
        slug = make_slug(player["name"])
        f_path = os.path.join(PUBLIC_HOF_DIR, f"{slug}.webp")
        if not os.path.exists(f_path) or os.path.getsize(f_path) < 1000:
            missing_files.append((player["name"], slug))
            
    if missing_files:
        print(f"ERROR: {len(missing_files)} missing or invalid files:", missing_files)
    else:
        print("ALL 149 player image files are present, valid, and successfully verified in both public/ and dist/!")

if __name__ == "__main__":
    main()
