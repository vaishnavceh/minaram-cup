import urllib.request
import re
import json

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

test_links = [
    "/players/237067-pele/27-237067/",
    "/players/242516-johan-cruyff/27-242516/",
    "/players/231747-kylian-mbappe/27-84117827/",
    "/players/239053-erling-haaland/27-239053/",
    "/players/238420-lev-yashin/27-238420/"
]

for link in test_links:
    url = f"https://www.fut.gg{link}"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=8) as r:
            html = r.read().decode('utf-8', errors='ignore')
        
        # Meta description:
        # e.g. <meta name="description" content="Pelé Base Icon 95 OVR CF (Icons) on EA FC 27 - FUT.GG" />
        m_desc = re.search(r'<meta[^>]+name="description"[^>]+content="([^"]+)"', html)
        desc = m_desc.group(1) if m_desc else "N/A"
        
        # JSON-LD schema
        schema_match = re.findall(r'<script[^>]+type="application/ld\+json"[^>]*>(.*?)</script>', html, re.DOTALL)
        schemas = []
        for s in schema_match:
            try:
                schemas.append(json.loads(s))
            except:
                pass
        
        # Also look for club, nation, position in html or schema
        print(f"\n--- {link} ---")
        print(f"Meta Desc: {desc}")
        for s in schemas:
            if isinstance(s, dict) and (s.get('@type') == 'Person' or 'nationality' in s):
                print(f"Schema Person: name={s.get('name')}, nationality={s.get('nationality')}, birthDate={s.get('birthDate')}")
    except Exception as e:
        print(f"Error {link}: {e}")
