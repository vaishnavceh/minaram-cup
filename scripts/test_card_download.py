import os
import urllib.request
import re
import json
import unicodedata
from concurrent.futures import ThreadPoolExecutor

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

os.makedirs('frontend/public/images/hall-of-fame-cards', exist_ok=True)
os.makedirs('frontend/dist/images/hall-of-fame-cards', exist_ok=True)

with open('scripts/selected_curated_new_players.json', 'r', encoding='utf-8') as f:
    candidates = json.load(f)

test_candidates = candidates[:5]

def download_card(item):
    slug = item['slug']
    card_url = item['card']
    pub_path = f'frontend/public/images/hall-of-fame-cards/{slug}.webp'
    dist_path = f'frontend/dist/images/hall-of-fame-cards/{slug}.webp'
    
    req = urllib.request.Request(card_url, headers=headers)
    with urllib.request.urlopen(req, timeout=12) as r:
        content = r.read()
    
    with open(pub_path, 'wb') as f:
        f.write(content)
    with open(dist_path, 'wb') as f:
        f.write(content)
    
    return slug, len(content)

with ThreadPoolExecutor(max_workers=5) as ex:
    results = list(ex.map(download_card, test_candidates))

for slug, size in results:
    print(f"Downloaded {slug}: {size} bytes")
