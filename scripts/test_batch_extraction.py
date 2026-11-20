import urllib.request
import re
import json
import time
from concurrent.futures import ThreadPoolExecutor

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

with open("scripts/selected_new_candidates.json", "r", encoding="utf-8") as f:
    selected = json.load(f)

test_sample = selected[:15]

def test_fetch(item):
    slug = item["slug"]
    link = item["link"]
    card_url = item["card"]
    url = f"https://www.fut.gg{link}"
    
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=10) as r:
        html = r.read().decode("utf-8", errors="ignore")
    
    # Meta desc
    m = re.search(r'content="([^"]+?)\s+([0-9]{2})\s+OVR\s+([A-Z]{1,3})\s+\(([^)]+)\)', html)
    rating = item.get("rating", 88)
    pos = "Forward"
    club = "Unknown"
    if m:
        rating = int(m.group(2))
        pos = m.group(3)
        club = m.group(4)
    
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
        "pos": pos,
        "club": club,
        "rating": rating
    }

with ThreadPoolExecutor(max_workers=8) as executor:
    results = list(executor.map(test_fetch, test_sample))

print(f"Successfully processed {len(results)} sample candidates:")
for r in results:
    print(f"  {r['slug']:25} | {r['name']:25} | {r['nationality']:15} | {r['pos']} | {r['club']}")
