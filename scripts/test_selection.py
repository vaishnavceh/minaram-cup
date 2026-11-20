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

# Also create map of normalized names
existing_norm_names = set(to_slug(p["name"]).replace('-', '') for p in PLAYERS_METADATA)

with open("scripts/discovered_raw_players.json", "r", encoding="utf-8") as f:
    raw = json.load(f)

print(f"Total raw in json: {len(raw)}")

icons_heroes = []
superstars = []

for slug, data in raw.items():
    slug_clean = slug.replace('-', '')
    if slug in existing_slugs or slug_clean in existing_norm_names:
        continue
    
    alt = data.get("alt", "")
    m = re.search(r'-\s*(\d{2})\s*-', alt)
    rating = int(m.group(1)) if m else 0
    
    is_icon_hero = "Icon" in alt or "Hero" in alt
    item = {
        "slug": slug,
        "alt": alt,
        "card": data.get("card"),
        "link": data.get("link"),
        "rating": rating,
        "is_icon_hero": is_icon_hero
    }
    
    if is_icon_hero:
        icons_heroes.append(item)
    elif rating >= 86:
        superstars.append(item)

# Sort icons_heroes by rating descending
icons_heroes.sort(key=lambda x: x["rating"], reverse=True)
# Sort superstars by rating descending
superstars.sort(key=lambda x: x["rating"], reverse=True)

print(f"New Icons/Heroes available: {len(icons_heroes)}")
print(f"New Superstars (>= 86) available: {len(superstars)}")

# Target total: 414 players
# Existing: 149
# Needed: 265
needed = 265
selected_icons = icons_heroes # take all icons/heroes
needed_superstars = needed - len(selected_icons)
selected_superstars = superstars[:needed_superstars]

selected = selected_icons + selected_superstars
print(f"Selected new players: {len(selected)}")
print(f"Total legends will be: {len(existing_slugs) + len(selected)}")

# Preview top 20 selected
print("\nSample top selected icons/heroes:")
for s in selected_icons[:10]:
    print(f"  {s['slug']:25} -> {s['alt']}")

print("\nSample top selected superstars:")
for s in selected_superstars[:10]:
    print(f"  {s['slug']:25} -> {s['alt']}")
