import sys
sys.path.insert(0, 'scripts')
import urllib.request
import urllib.parse
import re
import time
import json
import unicodedata

from build_hall_of_fame_data import PLAYERS_METADATA

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
}

# Explicit verified direct URLs or exact query overrides for players
OVERRIDES = {
    "Ronaldo Nazário": "Ronaldo",
    "Sergio Ramos": "https://www.fut.gg/players/155862-sergio-ramos/",
    "Neymar": "https://www.fut.gg/players/190871-neymar-jr/",
    "Dani Alves": "https://www.fut.gg/players/146530-dani-alves/",
    "Samuel Eto’o": "Samuel Eto",
    "Karim Benzema": "https://www.fut.gg/players/165153-karim-benzema/",
    "Arjen Robben": "https://www.fut.gg/players/9014-arjen-robben/",
    "John Terry": "https://www.fut.gg/players/13732-john-terry/",
    "Jay-Jay Okocha": "Okocha",
    "Park Ji-sung": "Park",
}

def clean_slug(s):
    nfkd = unicodedata.normalize('NFKD', s.lower())
    return ''.join(c for c in nfkd if not unicodedata.combining(c)).replace("'", "").replace("-", " ")

def get_card_for_player(name):
    target = OVERRIDES.get(name, name)
    if target.startswith("http"):
        try:
            req = urllib.request.Request(target, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=8) as r:
                html = r.read().decode('utf-8', errors='ignore')
            cards = re.findall(r'(https://game-assets\.fut\.gg/[^"\'\s>]+futgg-player-item-card[^"\'\s>]+)', html)
            if cards:
                return re.sub(r'width=\d+', 'width=500', cards[0]), target
        except Exception as e:
            pass
            
    # Search query
    url = f"https://www.fut.gg/players/?name={urllib.parse.quote(target)}"
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=8) as r:
            html = r.read().decode('utf-8', errors='ignore')
        matches = re.findall(r'<a[^>]+href="(/players/\d+-([^"/]+)/[^"]*)"[^>]*>.*?src="([^"]+futgg-player-item-card[^"]+)"', html, re.DOTALL)
        if matches:
            # Check match quality
            for link, slug, img in matches:
                # check if slug matches name keywords
                cleaned_slug = slug.replace("-", " ")
                cleaned_name = clean_slug(name)
                # check if key words match
                name_words = [w for w in cleaned_name.split() if len(w) > 2]
                if any(w in cleaned_slug for w in name_words):
                    return re.sub(r'width=\d+', 'width=500', img), slug
            # If no keyword matched, but full name was searched and returned results
            if target == name and matches:
                return re.sub(r'width=\d+', 'width=500', matches[0][2]), matches[0][1]
    except Exception as e:
        pass
        
    return None, None

if __name__ == "__main__":
    resolved = {}
    missing = []
    
    print(f"Resolving cards for {len(PLAYERS_METADATA)} players...")
    for i, p in enumerate(PLAYERS_METADATA, 1):
        name = p["name"]
        card, ref = get_card_for_player(name)
        if card:
            resolved[name] = {
                "card_url": card,
                "ref": ref
            }
            print(f"[{i:03d}/149] OK: {name:24} -> {ref}")
        else:
            missing.append(name)
            print(f"[{i:03d}/149] MISSING: {name:24}")
        time.sleep(0.04)
        
    print(f"\n================ SUMMARY ================")
    print(f"Resolved: {len(resolved)} / {len(PLAYERS_METADATA)}")
    print(f"Missing count: {len(missing)}")
    print("Missing names:", missing)
    
    with open("scripts/resolved_cards_temp.json", "w", encoding="utf-8") as f:
        json.dump(resolved, f, indent=2)
