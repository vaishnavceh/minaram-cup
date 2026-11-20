import urllib.request
import re
import json

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

with open("scripts/discovered_raw_players.json", "r", encoding="utf-8") as f:
    raw = json.load(f)

# Let's test 10 different links
test_slugs = ["pele", "diego-maradona", "johan-cruyff", "kylian-mbappe", "erling-haaland", "jude-bellingham", "lothar-matthaus", "george-best", "thibaut-courtois", "zico"]

for slug in test_slugs:
    data = raw.get(slug)
    if not data:
        print(f"Missing {slug}")
        continue
    link = data["link"]
    url = f"https://www.fut.gg{link}"
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as r:
            html = r.read().decode("utf-8", errors="ignore")
        
        # Look for player name, nation, position, club, etc.
        # Check meta title or og:title
        og_title = re.search(r'<meta[^>]+property="og:title"[^>]+content="([^"]+)"', html)
        og_desc = re.search(r'<meta[^>]+property="og:description"[^>]+content="([^"]+)"', html)
        meta_desc = re.search(r'<meta[^>]+name="description"[^>]+content="([^"]+)"', html)
        
        # Check title tag
        title_tag = re.search(r'<title>([^<]+)</title>', html)
        
        # Check if there is JSON in script id="__NEXT_DATA__" or similar
        next_data = re.search(r'<script[^>]+id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.DOTALL)
        
        print(f"\n=== {slug} ===")
        print("Title:", title_tag.group(1) if title_tag else "None")
        print("Meta Desc:", meta_desc.group(1) if meta_desc else "None")
        print("Has __NEXT_DATA__:", bool(next_data))
        if next_data:
            nd = json.loads(next_data.group(1))
            props = nd.get("props", {}).get("pageProps", {})
            # print top keys of pageProps
            print("pageProps keys:", list(props.keys()))
            # check player object
            player_obj = props.get("player") or props.get("item") or props.get("card")
            if player_obj:
                print("Player obj keys:", list(player_obj.keys())[:10])
    except Exception as e:
        print(f"Failed {slug}: {e}")
