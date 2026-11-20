import json
import re

with open("scripts/discovered_raw_players.json", "r", encoding="utf-8") as f:
    raw = json.load(f)

# Load existing 149
from build_hall_of_fame_data import PLAYERS_METADATA
existing_slugs = set(p["name"].lower() for p in PLAYERS_METADATA)

print(f"Total discovered in json: {len(raw)}")

# Check items
candidates = []
for slug, data in raw.items():
    alt = data.get("alt", "")
    card = data.get("card", "")
    link = data.get("link", "")
    
    # check if icon or hero or rating >= 86
    m = re.search(r'-\s*(\d{2})\s*-', alt)
    rating = int(m.group(1)) if m else 0
    is_icon_hero = "Icon" in alt or "Hero" in alt
    
    candidates.append({
        "slug": slug,
        "alt": alt,
        "card": card,
        "link": link,
        "rating": rating,
        "is_icon_hero": is_icon_hero
    })

print(f"Total candidates: {len(candidates)}")
print(f"Icons/Heroes: {len([c for c in candidates if c['is_icon_hero']])}")
print(f"Rating >= 88: {len([c for c in candidates if c['rating'] >= 88])}")
print(f"Rating >= 86: {len([c for c in candidates if c['rating'] >= 86])}")
print(f"Rating >= 84: {len([c for c in candidates if c['rating'] >= 84])}")
