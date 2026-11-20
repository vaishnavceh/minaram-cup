import urllib.request
import re
import json
import time
from concurrent.futures import ThreadPoolExecutor

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

with open("scripts/discovered_raw_players.json", "r", encoding="utf-8") as f:
    raw = json.load(f)

test_slugs = ["pele", "diego-maradona", "johan-cruyff", "kylian-mbappe", "erling-haaland"]

def fetch_player_info(slug):
    data = raw[slug]
    link = data["link"]
    card_url = data["card"]
    url = f"https://www.fut.gg{link}"
    
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=10) as r:
        html = r.read().decode("utf-8", errors="ignore")
    
    # Meta desc
    m = re.search(r'content="([^"]+)\s+([0-9]{2})\s+OVR\s+([A-Z]{1,3})\s+\(([^)]+)\)', html)
    pos = "Forward"
    det_pos = "Striker"
    club = "Unknown"
    rating = 90
    if m:
        rating = int(m.group(2))
        raw_pos = m.group(3)
        club = m.group(4)
        
        pos_map = {
            "GK": ("Goalkeeper", "Goalkeeper"),
            "CB": ("Defender", "Center Back"),
            "LB": ("Defender", "Left Back"),
            "RB": ("Defender", "Right Back"),
            "LWB": ("Defender", "Left Wing Back"),
            "RWB": ("Defender", "Right Wing Back"),
            "CM": ("Midfielder", "Central Midfielder"),
            "CDM": ("Midfielder", "Defensive Midfielder"),
            "CAM": ("Midfielder", "Attacking Midfielder / Playmaker"),
            "LM": ("Midfielder", "Left Midfielder"),
            "RM": ("Midfielder", "Right Midfielder"),
            "ST": ("Forward", "Striker"),
            "CF": ("Forward", "Center Forward"),
            "LW": ("Forward", "Left Winger"),
            "RW": ("Forward", "Right Winger")
        }
        pos, det_pos = pos_map.get(raw_pos, ("Forward", "Forward"))
    
    # Schema Person
    schemas = re.findall(r'<script[^>]+type="application/ld\+json"[^>]*>(.*?)</script>', html, re.DOTALL)
    person = {}
    for s in schemas:
        try:
            d = json.loads(s)
            if d.get("@type") == "Person" or "nationality" in d:
                person = d
                break
        except:
            pass
    
    name = person.get("name") or slug.replace('-', ' ').title()
    nationality = person.get("nationality") or "Unknown"
    birth_date = person.get("birthDate")
    
    return {
        "slug": slug,
        "name": name,
        "nationality": nationality,
        "birth_date": birth_date,
        "position": pos,
        "detailed_position": det_pos,
        "club": club,
        "rating": rating,
        "card_url": card_url
    }

start = time.time()
with ThreadPoolExecutor(max_workers=5) as executor:
    results = list(executor.map(fetch_player_info, test_slugs))

duration = time.time() - start
print(f"Fetched {len(results)} in {duration:.2f} seconds!")
for r in results:
    print(r)
