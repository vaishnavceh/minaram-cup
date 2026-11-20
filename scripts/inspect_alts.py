import json
import re

with open("scripts/discovered_raw_players.json", "r", encoding="utf-8") as f:
    raw = json.load(f)

print("Total players in discovered:", len(raw))

# Let's inspect 50 sample alt texts
sample = list(raw.items())[:50]
for slug, data in sample:
    print(f"{slug:25} | {data.get('alt')} | {data.get('card')[:60]}...")
