import urllib.request
import re
import json

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

with open("scripts/discovered_raw_players.json", "r", encoding="utf-8") as f:
    raw = json.load(f)

test_slugs = ["pele", "diego-maradona", "johan-cruyff", "kylian-mbappe", "erling-haaland", "jude-bellingham", "lothar-matthaus", "george-best", "thibaut-courtois", "zico"]

for slug in test_slugs:
    link = raw[slug]["link"]
    url = f"https://www.fut.gg{link}"
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as r:
            html = r.read().decode("utf-8", errors="ignore")
        
        # Meta desc regex
        m = re.search(r'content="([^"]+)\s+([0-9]{2})\s+OVR\s+([A-Z]{1,3})\s+\(([^)]+)\)', html)
        if not m:
            m = re.search(r'<meta[^>]+name="description"[^>]+content="([^"]+)"', html)
            desc = m.group(1) if m else "No desc"
        else:
            desc = m.groups()
        
        # Schema
        schemas = re.findall(r'<script[^>]+type="application/ld\+json"[^>]*>(.*?)</script>', html, re.DOTALL)
        person = None
        for s in schemas:
            try:
                data = json.loads(s)
                if data.get("@type") == "Person" or "nationality" in data:
                    person = data
                    break
            except:
                pass
        
        print(f"{slug:20} -> Desc: {desc} | Person: name={person.get('name') if person else None}, nat={person.get('nationality') if person else None}, dob={person.get('birthDate') if person else None}")
    except Exception as e:
        print(f"{slug} error: {e}")
