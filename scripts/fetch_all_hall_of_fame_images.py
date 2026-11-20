# -*- coding: utf-8 -*-
"""
Fetches and processes player portraits for all 149 Hall of Fame legends.
Saves local WebP images in frontend/public/images/hall-of-fame/ and frontend/dist/images/hall-of-fame/.
Generates a fallback card for any player if no photo is available.
"""

import unicodedata
import re
import urllib.request
import urllib.parse
import json
import time
import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import io

from build_hall_of_fame_data import PLAYERS_METADATA

HEADERS = {
    'User-Agent': 'MinaramCupHallOfFame/1.0 (https://minaramcup.org; contact@minaramcup.org) Python/3.13'
}

def to_slug(name):
    nfkd = unicodedata.normalize('NFKD', name)
    ascii_str = ''.join(c for c in nfkd if not unicodedata.combining(c))
    ascii_str = ascii_str.replace("'", "").replace("’", "")
    slug = re.sub(r'[^a-zA-Z0-9]+', '-', ascii_str.strip().lower())
    return slug.strip('-')

def get_initials(name):
    parts = name.replace("’", "").replace("'", "").split()
    if len(parts) >= 2:
        return f"{parts[0][0]}{parts[-1][0]}".upper()
    elif len(parts) == 1:
        return parts[0][:2].upper()
    return "FC"

def create_fallback_portrait(name, position, out_path):
    """
    Creates a premium eFootball / EA FC style metallic portrait with initials
    and positional gradient accents.
    """
    w, h = 360, 520
    img = Image.new("RGB", (w, h), color="#080C16")
    draw = ImageDraw.Draw(img)

    # Position theme colors
    color_map = {
        "Forward": ((225, 29, 72), (159, 18, 57)),      # Crimson
        "Midfielder": ((212, 175, 55), (161, 98, 7)),    # Gold
        "Defender": ((56, 189, 248), (2, 132, 199)),     # Sky Blue
        "Goalkeeper": ((16, 185, 129), (4, 120, 87)),   # Emerald
    }
    c_primary, c_dark = color_map.get(position, ((212, 175, 55), (161, 98, 7)))

    # Draw sleek gradient lines and card geometry
    for y in range(h):
        ratio = y / h
        r = int(8 + (c_dark[0] - 8) * (ratio * 0.45))
        g = int(12 + (c_dark[1] - 12) * (ratio * 0.45))
        b = int(22 + (c_dark[2] - 22) * (ratio * 0.45))
        draw.line([(0, y), (w, y)], fill=(r, g, b))

    # Geometric hexagon badge in center
    cx, cy = w // 2, h // 2 - 20
    radius = 90
    draw.ellipse([cx - radius, cy - radius, cx + radius, cy + radius], outline=c_primary, width=3)
    draw.ellipse([cx - radius + 8, cy - radius + 8, cx + radius - 8, cy + radius - 8], fill=(12, 18, 32), outline=(40, 50, 70), width=1)

    initials = get_initials(name)

    # Draw large initials text
    try:
        font = ImageFont.truetype("arial.ttf", 64)
        sub_font = ImageFont.truetype("arial.ttf", 16)
    except Exception:
        font = ImageFont.load_default()
        sub_font = ImageFont.load_default()

    # Draw initials centered
    draw.text((cx, cy), initials, fill="#FFFFFF", font=font, anchor="mm")
    draw.text((cx, cy + radius + 30), position.upper(), fill=c_primary, font=sub_font, anchor="mm")
    draw.text((cx, cy + radius + 55), "HALL OF FAME LEGEND", fill="#94A3B8", font=sub_font, anchor="mm")

    img.save(out_path, format="WEBP", quality=85)

def fetch_wiki_thumbnail(wiki_title, fallback_query):
    # 1. Direct page summary
    summary_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(wiki_title.replace(' ', '_'))}"
    try:
        req = urllib.request.Request(summary_url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=6) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            if data.get("thumbnail", {}).get("source"):
                return data["thumbnail"]["source"], data.get("description", "")
    except Exception:
        pass

    # 2. Search fallback
    if fallback_query:
        search_url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={urllib.parse.quote(fallback_query)}&format=json"
        try:
            req = urllib.request.Request(search_url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=6) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                results = data.get("query", {}).get("search", [])
                if results:
                    top_title = results[0]["title"]
                    sub_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(top_title.replace(' ', '_'))}"
                    req2 = urllib.request.Request(sub_url, headers=HEADERS)
                    with urllib.request.urlopen(req2, timeout=6) as resp2:
                        data2 = json.loads(resp2.read().decode('utf-8'))
                        if data2.get("thumbnail", {}).get("source"):
                            return data2["thumbnail"]["source"], data2.get("description", "")
        except Exception:
            pass

    return None, ""

def process_and_save_image(img_url, out_path):
    req = urllib.request.Request(img_url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = resp.read()

    with Image.open(io.BytesIO(data)) as img:
        img = img.convert("RGB")
        w, h = img.size
        # Crop or resize cleanly to ~480-550px height
        if h > 550:
            new_h = 550
            new_w = int(w * (new_h / h))
            img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        img.save(out_path, format="WEBP", quality=82, method=6)

def main():
    pub_dir = Path("frontend/public/images/hall-of-fame")
    dist_dir = Path("frontend/dist/images/hall-of-fame")
    pub_dir.mkdir(parents=True, exist_ok=True)
    dist_dir.mkdir(parents=True, exist_ok=True)

    print(f"Starting image fetch for {len(PLAYERS_METADATA)} players...")
    success_count = 0
    fallback_count = 0

    for i, p in enumerate(PLAYERS_METADATA, 1):
        name = p["name"]
        slug = to_slug(name)
        pub_file = pub_dir / f"{slug}.webp"
        dist_file = dist_dir / f"{slug}.webp"

        # If already exists and valid, skip
        if pub_file.exists() and pub_file.stat().st_size > 1000:
            if not dist_file.exists() or dist_file.stat().st_size != pub_file.stat().st_size:
                import shutil
                shutil.copy2(pub_file, dist_file)
            success_count += 1
            continue

        print(f"[{i}/{len(PLAYERS_METADATA)}] Fetching {name} ({slug})...")
        img_url, desc = fetch_wiki_thumbnail(p.get("wikiTitle", name), f"{name} footballer")
        
        saved = False
        if img_url:
            try:
                process_and_save_image(img_url, pub_file)
                import shutil
                shutil.copy2(pub_file, dist_file)
                print(f"   -> OK: {pub_file.stat().st_size // 1024} KB")
                success_count += 1
                saved = True
            except Exception as e:
                print(f"   -> Download error for {name}: {e}")

        if not saved:
            print(f"   -> Generating fallback portrait for {name}")
            create_fallback_portrait(name, p["position"], pub_file)
            import shutil
            shutil.copy2(pub_file, dist_file)
            fallback_count += 1

        time.sleep(0.2)

    print(f"\nDone! Photos fetched: {success_count}, Fallbacks generated: {fallback_count}")
    print(f"Total images in folder: {len(list(pub_dir.glob('*.webp')))}")

if __name__ == "__main__":
    main()
