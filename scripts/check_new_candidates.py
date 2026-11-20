import json
import re
import unicodedata

def to_slug(name):
    nfkd = unicodedata.normalize('NFKD', name)
    ascii_str = ''.join(c for c in nfkd if not unicodedata.combining(c))
    ascii_str = ascii_str.replace("'", "").replace("’", "")
    slug = re.sub(r'[^a-zA-Z0-9]+', '-', ascii_str.strip().lower())
    return slug.strip('-')

from build_hall_of_fame_data import PLAYERS_METADATA
existing_slugs = set(to_slug(p["name"]) for p in PLAYERS_METADATA)

with open("scripts/discovered_raw_players.json", "r", encoding="utf-8") as f:
    raw = json.load(f)

new_icons_heroes = {}
new_superstars = {}

for slug, data in raw.items():
    if slug in existing_slugs:
        continue
    alt = data.get("alt", "")
    card = data.get("card", "")
    
    m = re.search(r'-\s*(\d{2})\s*-', alt)
    rating = int(m.group(1)) if m else 0
    
    if "Icon" in alt or "Hero" in alt:
        new_icons_heroes[slug] = (alt, card, rating, data)
    elif rating >= 85:
        new_superstars[slug] = (alt, card, rating, data)

print(f"Existing dataset: {len(existing_slugs)} players")
print(f"New Icons & Heroes available: {len(new_icons_heroes)}")
print(f"New Superstars (>= 85) available: {len(new_superstars)}")
print(f"Total new high-caliber candidates: {len(new_icons_heroes) + len(new_superstars)}")
