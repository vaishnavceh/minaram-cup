import urllib.request
import re
import time
import json

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

unique_players = {}

for p in range(1, 26):
    url = f'https://www.fut.gg/players/?page={p}'
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=8) as r:
            html = r.read().decode('utf-8', errors='ignore')
        matches = re.findall(r'<a[^>]+href="(/players/\d+-([^"/]+)/[^"]*)"[^>]*>.*?src="([^"]+futgg-player-item-card[^"]+)"[^>]*alt="([^"]*)"', html, re.DOTALL)
        for link, slug, img, alt in matches:
            if slug not in unique_players:
                # parse name and rating from alt if possible e.g. "Puskás - 92 - Base Icon"
                clean_card = re.sub(r'width=\d+', 'width=500', img)
                unique_players[slug] = {
                    "slug": slug,
                    "link": link,
                    "card": clean_card,
                    "alt": alt
                }
    except Exception as e:
        print(f"Page {p} error: {e}")
    time.sleep(0.04)

print(f"Scanned 25 pages: Found {len(unique_players)} unique players!")
with open("scripts/discovered_raw_players.json", "w", encoding="utf-8") as f:
    json.dump(unique_players, f, indent=2)
