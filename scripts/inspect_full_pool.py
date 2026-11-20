import json
import re

with open("scripts/discovered_raw_players.json", "r", encoding="utf-8") as f:
    raw = json.load(f)

print(f"Total discovered raw players: {len(raw)}")

icons_heroes = {}
superstars = {}

for slug, data in raw.items():
    alt = data.get("alt", "")
    card = data.get("card", "")
    m = re.search(r'-\s*(\d{2})\s*-', alt)
    rating = int(m.group(1)) if m else 0
    
    if "Icon" in alt or "Hero" in alt:
        icons_heroes[slug] = (alt, card, rating)
    else:
        superstars[slug] = (alt, card, rating)

print(f"Icons and Heroes: {len(icons_heroes)}")
print(f"Other Superstars: {len(superstars)}")
print(f"Superstars >= 87: {len([s for s in superstars.values() if s[2] >= 87])}")
print(f"Superstars >= 85: {len([s for s in superstars.values() if s[2] >= 85])}")
