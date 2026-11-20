import urllib.request
import re
import time
import json

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
unique_players = json.load(open('scripts/discovered_raw_players.json', encoding='utf-8'))
initial_count = len(unique_players)

for p in range(26, 46):
    url = f'https://www.fut.gg/players/?page={p}'
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as r:
            html = r.read().decode('utf-8', errors='ignore')
        matches = re.findall(r'<a[^>]+href="(/players/\d+-([^"/]+)/[^"]*)"[^>]*>.*?src="([^"]+futgg-player-item-card[^"]+)"[^>]*alt="([^"]*)"', html, re.DOTALL)
        for link, slug, img, alt in matches:
            if slug not in unique_players:
                clean_card = re.sub(r'width=\d+', 'width=500', img)
                unique_players[slug] = {
                    'slug': slug,
                    'link': link,
                    'card': clean_card,
                    'alt': alt
                }
    except Exception as e:
        print(f'Page {p} error: {e}')
    time.sleep(0.05)

print(f"Scanned up to page 45. Initial: {initial_count}, Now total: {len(unique_players)}")
with open('scripts/discovered_raw_players.json', 'w', encoding='utf-8') as f:
    json.dump(unique_players, f, indent=2)
