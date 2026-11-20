import json
import re

with open("scripts/discovered_raw_players.json", "r", encoding="utf-8") as f:
    raw = json.load(f)

print(f"Total discovered raw players: {len(raw)}")

# Check how many are Icons or Heroes or high rating
icons_heroes = []
others = []

for slug, data in raw.items():
    alt = data["alt"]
    if "Icon" in alt or "Hero" in alt:
        icons_heroes.append((slug, alt, data["card"]))
    else:
        # Check rating in alt e.g. "Mbappé - 92 - ..."
        m = re.search(r'-\s*(\d{2})\s*-', alt)
        rating = int(m.group(1)) if m else 0
        others.append((slug, alt, data["card"], rating))

print(f"Icons and Heroes found: {len(icons_heroes)}")
print(f"Other players found: {len(others)}")

# Sample of icons and heroes
print("\nSample Icons/Heroes:")
for slug, alt, card in icons_heroes[:20]:
    print(f"  {slug:25} -> {alt}")
