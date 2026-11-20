# -*- coding: utf-8 -*-
"""
Build complete 400+ Legends Hall of Fame dataset with official EA FC collectible cards.
"""

import os
import sys
import json
import re
import time
import urllib.request
import unicodedata
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

# Add scripts directory to path to import existing metadata
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from build_hall_of_fame_data import PLAYERS_METADATA

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

PUBLIC_CARDS_DIR = Path("frontend/public/images/hall-of-fame-cards")
DIST_CARDS_DIR = Path("frontend/dist/images/hall-of-fame-cards")
PUBLIC_CARDS_DIR.mkdir(parents=True, exist_ok=True)
DIST_CARDS_DIR.mkdir(parents=True, exist_ok=True)

NATION_FLAGS = {
    "Argentina": ("AR", "🇦🇷"),
    "Brazil": ("BR", "🇧🇷"),
    "France": ("FR", "🇫🇷"),
    "Portugal": ("PT", "🇵🇹"),
    "Spain": ("ES", "🇪🇸"),
    "Italy": ("IT", "🇮🇹"),
    "Germany": ("DE", "🇩🇪"),
    "Netherlands": ("NL", "🇳🇱"),
    "England": ("ENG", "🏴󠁧󠁢󠁥󠁮󠁧󠁿"),
    "Belgium": ("BE", "🇧🇪"),
    "Norway": ("NO", "🇳🇴"),
    "Croatia": ("HR", "🇭🇷"),
    "Uruguay": ("UY", "🇺🇾"),
    "Poland": ("PL", "🇵🇱"),
    "Czech Republic": ("CZ", "🇨🇿"),
    "Denmark": ("DK", "🇩🇰"),
    "Sweden": ("SE", "🇸🇪"),
    "Ukraine": ("UA", "🇺🇦"),
    "Northern Ireland": ("NIR", "🇬🇧"),
    "Scotland": ("SCO", "🏴󠁧󠁢󠁳󠁣󠁴󠁿"),
    "Wales": ("WAL", "🏴󠁧󠁢󠁷󠁬󠁳󠁿"),
    "Republic of Ireland": ("IE", "🇮🇪"),
    "Ireland": ("IE", "🇮🇪"),
    "Hungary": ("HU", "🇭🇺"),
    "Bulgaria": ("BG", "🇧🇬"),
    "Romania": ("RO", "🇷🇴"),
    "Serbia": ("RS", "🇷🇸"),
    "Bosnia and Herzegovina": ("BA", "🇧🇦"),
    "Slovakia": ("SK", "🇸🇰"),
    "Slovenia": ("SI", "🇸🇮"),
    "Switzerland": ("CH", "🇨🇭"),
    "Austria": ("AT", "🇦🇹"),
    "Turkey": ("TR", "🇹🇷"),
    "Greece": ("GR", "🇬🇷"),
    "Georgia": ("GE", "🇬🇪"),
    "Russia": ("RU", "🇷🇺"),
    "Colombia": ("CO", "🇨🇴"),
    "Chile": ("CL", "🇨🇱"),
    "Mexico": ("MX", "🇲🇽"),
    "United States": ("US", "🇺🇸"),
    "USA": ("US", "🇺🇸"),
    "Canada": ("CA", "🇨🇦"),
    "Japan": ("JP", "🇯🇵"),
    "Korea Republic": ("KR", "🇰🇷"),
    "South Korea": ("KR", "🇰🇷"),
    "Australia": ("AU", "🇦🇺"),
    "Nigeria": ("NG", "🇳🇬"),
    "Cameroon": ("CM", "🇨🇲"),
    "Ivory Coast": ("CI", "🇨🇮"),
    "Côte d'Ivoire": ("CI", "🇨🇮"),
    "Ghana": ("GH", "🇬🇭"),
    "Senegal": ("SN", "🇸🇳"),
    "Egypt": ("EG", "🇪🇬"),
    "Morocco": ("MA", "🇲🇦"),
    "Algeria": ("DZ", "🇩🇿"),
    "Tunisia": ("TN", "🇹🇳"),
    "Saudi Arabia": ("SA", "🇸🇦"),
    "Ecuador": ("EC", "🇪🇨"),
    "Peru": ("PE", "🇵🇪"),
    "Paraguay": ("PY", "🇵🇾"),
    "Venezuela": ("VE", "🇻🇪"),
    "Costa Rica": ("CR", "🇨🇷"),
    "Trinidad and Tobago": ("TT", "🇹🇹"),
    "Liberia": ("LR", "🇱🇷"),
    "Mali": ("ML", "🇲🇱"),
    "Gabon": ("GA", "🇬🇦"),
    "Zambia": ("ZM", "🇿🇲"),
    "South Africa": ("ZA", "🇿🇦"),
    "Finland": ("FI", "🇫🇮"),
    "Iceland": ("IS", "🇮🇸"),
    "Haiti": ("HT", "🇭🇹"),
    "Jamaica": ("JM", "🇯🇲"),
    "Malawi": ("MW", "🇲🇼"),
    "Zambia": ("ZM", "🇿🇲"),
    "Albania": ("AL", "🇦🇱"),
    "Armenia": ("AM", "🇦🇲"),
    "Georgia": ("GE", "🇬🇪"),
    "Israel": ("IL", "🇮🇱"),
    "Montenegro": ("ME", "🇲🇪"),
    "North Macedonia": ("MK", "🇲🇰")
}

KNOWN_ICON_CLUBS = {
    "pele": ["Santos", "New York Cosmos"],
    "diego-maradona": ["Napoli", "Barcelona", "Boca Juniors", "Argentinos Juniors"],
    "johan-cruyff": ["Ajax", "Barcelona", "Feyenoord"],
    "franz-beckenbauer": ["Bayern Munich", "New York Cosmos", "Hamburger SV"],
    "ferenc-puskas": ["Real Madrid", "Budapest Honvéd"],
    "eusebio": ["Benfica", "Sporting CP", "Toronto Blizzard"],
    "garrincha": ["Botafogo", "Corinthians", "Flamengo"],
    "bobby-charlton": ["Manchester United", "Preston North End"],
    "lothar-matthaus": ["Bayern Munich", "Inter Milan", "Borussia Mönchengladbach"],
    "ruud-gullit": ["AC Milan", "Chelsea", "PSV Eindhoven", "Feyenoord"],
    "george-best": ["Manchester United", "Fulham", "Hibernian"],
    "lev-yashin": ["Dynamo Moscow"],
    "marco-van-basten": ["AC Milan", "Ajax"],
    "franco-baresi": ["AC Milan"],
    "gerd-muller": ["Bayern Munich", "1860 Munich"],
    "jairzinho": ["Botafogo", "Marseille", "Cruzeiro"],
    "carlos-alberto": ["Santos", "Fluminense", "New York Cosmos"],
    "kenny-dalglish": ["Liverpool", "Celtic"],
    "socrates": ["Corinthians", "Fiorentina", "Botafogo-SP"],
    "zico": ["Flamengo", "Udinese", "Kashima Antlers"],
    "mario-kempes": ["Valencia", "River Plate", "Rosario Central"],
    "emilio-butragueno": ["Real Madrid", "Atlético Celaya"],
    "hugo-sanchez": ["Real Madrid", "Atlético Madrid", "UNAM"],
    "ian-wright": ["Arsenal", "Crystal Palace", "West Ham United"],
    "gary-lineker": ["Tottenham Hotspur", "Barcelona", "Everton", "Leicester City"],
    "michael-laudrup": ["Barcelona", "Real Madrid", "Juventus", "Ajax"],
    "brian-laudrup": ["Rangers", "Bayern Munich", "Chelsea", "AC Milan"],
    "bobby-moore": ["West Ham United", "Fulham"],
    "eric-cantona": ["Manchester United", "Leeds United", "Marseille"],
    "laurent-blanc": ["Manchester United", "Inter Milan", "Barcelona", "Marseille"],
    "frank-rijkaard": ["AC Milan", "Ajax", "Sporting CP"],
    "ronald-koeman": ["Barcelona", "Ajax", "PSV Eindhoven", "Feyenoord"],
    "fernando-hierro": ["Real Madrid", "Bolton Wanderers"],
    "sol-campbell": ["Arsenal", "Tottenham Hotspur", "Portsmouth"],
    "emmanuel-petit": ["Arsenal", "Barcelona", "Chelsea", "Monaco"],
    "gianfranco-zola": ["Chelsea", "Parma", "Napoli"],
    "filippo-inzaghi": ["AC Milan", "Juventus", "Atalanta"],
    "christian-vieri": ["Inter Milan", "Juventus", "Atlético Madrid", "Lazio"],
    "freddie-ljungberg": ["Arsenal", "West Ham United", "Celtic"],
    "ole-gunnar-solskjaer": ["Manchester United", "Molde"],
    "robbie-keane": ["Tottenham Hotspur", "Liverpool", "Leeds United", "LA Galaxy"],
    "joe-cole": ["Chelsea", "West Ham United", "Liverpool", "Lille"],
    "landon-donovan": ["LA Galaxy", "Everton", "San Jose Earthquakes"],
    "clint-dempsey": ["Tottenham Hotspur", "Fulham", "Seattle Sounders"],
    "tim-cahill": ["Everton", "Millwall", "New York Red Bulls"],
    "dirk-kuyt": ["Liverpool", "Feyenoord", "Fenerbahçe"],
    "peter-crouch": ["Liverpool", "Tottenham Hotspur", "Stoke City"],
    "mario-gomez": ["Bayern Munich", "VfB Stuttgart", "Fiorentina", "Beşiktaş"],
    "joan-capdevila": ["Villarreal", "Deportivo La Coruña", "Espanyol", "Benfica"],
    "sidney-govou": ["Lyon", "Panathinaikos", "Évian"],
    "ludovic-giuly": ["Barcelona", "Monaco", "Paris Saint-Germain", "Roma"],
    "tomas-rosicky": ["Arsenal", "Borussia Dortmund", "Sparta Prague"],
    "nwankwo-kanu": ["Arsenal", "Ajax", "Inter Milan", "Portsmouth"],
    "john-arne-riise": ["Liverpool", "Roma", "Monaco", "Fulham"],
    "jerzy-dudek": ["Liverpool", "Real Madrid", "Feyenoord"],
    "bixente-lizarazu": ["Bayern Munich", "Bordeaux", "Athletic Bilbao"],
    "paulo-futre": ["Atlético Madrid", "Porto", "Benfica", "AC Milan"],
    "gianluca-vialli": ["Chelsea", "Juventus", "Sampdoria"],
    "david-ginola": ["Tottenham Hotspur", "Newcastle United", "Paris Saint-Germain"],
    "abedi-pele": ["Marseille", "Lille", "Lyon", "Torino"],
    "antonio-di-natale": ["Udinese", "Empoli"],
    "jurgen-kohler": ["Borussia Dortmund", "Juventus", "Bayern Munich"],
    "ivan-cordoba": ["Inter Milan", "San Lorenzo"],
    "claudio-marchisio": ["Juventus", "Zenit Saint Petersburg"],
    "mia-hamm": ["Washington Freedom", "North Carolina Tar Heels"],
    "birgit-prinz": ["1. FFC Frankfurt", "Carolina Courage"],
    "homare-sawa": ["INAC Kobe Leonessa", "NTV Beleza", "Atlanta Beat"],
    "kelly-smith": ["Arsenal", "Boston Breakers", "Philadelphia Charge"],
    "camille-abily": ["Lyon", "Paris Saint-Germain", "FC Gold Pride"],
    "sonia-bompastor": ["Lyon", "Paris Saint-Germain", "Montpellier", "Washington Freedom"],
    "alex-scott": ["Arsenal", "Boston Breakers", "Birmingham City"],
    "nadine-kessler": ["VfL Wolfsburg", "1. FFC Turbine Potsdam"],
    "jaap-stam": ["Manchester United", "AC Milan", "Lazio", "PSV Eindhoven"],
    "christine-sinclair": ["Portland Thorns", "Western New York Flash"],
    "nadine-angerer": ["Portland Thorns", "1. FFC Frankfurt", "Turbine Potsdam"],
}

ICONIC_FEATURED_NAMES = [
    "Lionel Messi", "Cristiano Ronaldo", "Zinedine Zidane", "Ronaldo Nazário",
    "Pelé", "Diego Maradona", "Johan Cruyff", "Franz Beckenbauer", "Ferenc Puskás",
    "Ronaldinho", "Paolo Maldini", "Andrés Iniesta", "Thierry Henry",
    "Gianluigi Buffon", "Kaká", "Andrea Pirlo", "Neymar"
]

def to_slug(name):
    nfkd = unicodedata.normalize('NFKD', name)
    ascii_str = ''.join(c for c in nfkd if not unicodedata.combining(c))
    ascii_str = ascii_str.replace("'", "").replace("’", "")
    slug = re.sub(r'[^a-zA-Z0-9]+', '-', ascii_str.strip().lower())
    return slug.strip('-')

def fetch_and_download_candidate(item):
    slug = item["slug"]
    link = item["link"]
    card_url = item["card"]
    alt = item.get("alt", "")
    is_icon_hero = item.get("is_icon_hero", False)
    
    # 1. Download card image if not already downloaded or if empty
    pub_path = PUBLIC_CARDS_DIR / f"{slug}.webp"
    dist_path = DIST_CARDS_DIR / f"{slug}.webp"
    if not pub_path.exists() or pub_path.stat().st_size < 1000:
        try:
            req = urllib.request.Request(card_url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=12) as r:
                card_bytes = r.read()
            with open(pub_path, "wb") as f:
                f.write(card_bytes)
            with open(dist_path, "wb") as f:
                f.write(card_bytes)
        except Exception as e:
            print(f"Error downloading card for {slug}: {e}")
    else:
        # ensure dist has it
        if not dist_path.exists() or dist_path.stat().st_size < 1000:
            import shutil
            shutil.copy(pub_path, dist_path)

    # 2. Scrape profile metadata from fut.gg
    url = f"https://www.fut.gg{link}"
    html = ""
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=10) as r:
            html = r.read().decode("utf-8", errors="ignore")
    except Exception as e:
        # print(f"Profile error {slug}: {e}")
        pass

    # Extract name, nationality, birthDate from Person Schema
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

    # Extract Position, Club, and Rating from meta description
    m = re.search(r'content="([^"]+?)\s+([0-9]{2})\s+OVR\s+([A-Z]{1,3})\s+\(([^)]+)\)', html)
    pos_code = "ST"
    club_meta = "Unknown"
    rating = item.get("rating", 88)
    
    if m:
        rating = int(m.group(2))
        pos_code = m.group(3)
        club_meta = m.group(4)
    else:
        # fallback from alt
        m_alt = re.search(r'-\s*(\d{2})\s*-', alt)
        if m_alt:
            rating = int(m_alt.group(1))

    # Determine Position & Detailed Position
    POS_MAP = {
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
    position, detailed_pos = POS_MAP.get(pos_code, ("Forward", "Forward"))

    # Determine Name
    raw_name = person.get("name")
    if not raw_name or len(raw_name) < 2:
        # derive from slug
        raw_name = slug.replace("-", " ").title()
    name = raw_name.strip()

    # Determine Nationality & Flag
    nationality = person.get("nationality", "").strip()
    if not nationality:
        # guess from known mapping
        nationality = "International"

    country_info = NATION_FLAGS.get(nationality)
    if not country_info:
        # try case insensitive
        for k, v in NATION_FLAGS.items():
            if k.lower() == nationality.lower():
                country_info = v
                nationality = k
                break
    if not country_info:
        country_code = nationality[:3].upper() if nationality else "INT"
        flag_emoji = "⚽"
    else:
        country_code, flag_emoji = country_info

    # Determine Birth Year & Era
    birth_date = person.get("birthDate", "")
    birth_year = None
    if birth_date and len(birth_date) >= 4:
        try:
            birth_year = int(birth_date[:4])
        except:
            birth_year = None

    if is_icon_hero:
        if birth_year:
            if birth_year <= 1945:
                era = "1950s–1970s"
            elif birth_year <= 1955:
                era = "1970s–1980s"
            elif birth_year <= 1968:
                era = "1980s–1990s"
            elif birth_year <= 1978:
                era = "1990s–2000s"
            else:
                era = "2000s–2010s"
        else:
            era = "1990s–2000s"
        int_status = "Retired"
        club_status = "Retired"
        retirement_year = (birth_year + 36) if birth_year else 2010
    else:
        # Active Superstar
        if birth_year:
            if birth_year <= 1993:
                era = "2010s–2020s"
            else:
                era = "2020s"
        else:
            era = "2020s"
        int_status = "Active"
        club_status = "Active"
        retirement_year = None

    # Determine Famous Clubs
    if slug in KNOWN_ICON_CLUBS:
        famous_clubs = KNOWN_ICON_CLUBS[slug]
    elif club_meta and club_meta not in ("ICON", "HERO", "Unknown", ""):
        famous_clubs = [club_meta]
    else:
        famous_clubs = ["Legendary Club", "National Team"]

    # Generate Bio
    if is_icon_hero:
        bio = f"Revered {nationality} {detailed_pos.lower()} and iconic football master with a {rating} OVR EA FC collectible card, immortalized in global football history."
    else:
        bio = f"World-class {nationality} {detailed_pos.lower()} performing at the pinnacle of modern football with {famous_clubs[0]} and an elite {rating} OVR rating."

    is_featured = name in ICONIC_FEATURED_NAMES

    return {
        "id": slug,
        "name": name,
        "slug": slug,
        "nationality": nationality,
        "countryCode": country_code,
        "flagEmoji": flag_emoji,
        "position": position,
        "detailedPosition": detailed_pos,
        "famousClubs": famous_clubs,
        "internationalRetirementStatus": int_status,
        "clubRetirementStatus": club_status,
        "retirementYear": retirement_year,
        "era": era,
        "image": f"/images/hall-of-fame-cards/{slug}.webp?v=fc27",
        "imageAttribution": "EA FC 27 Official Collectible Card",
        "bio": bio,
        "isFeatured": is_featured
    }

def main():
    with open("scripts/selected_curated_new_players.json", "r", encoding="utf-8") as f:
        candidates = json.load(f)

    print(f"Starting processing of {len(candidates)} new candidates with 12 worker threads...")
    start_time = time.time()
    
    enriched_new = []
    with ThreadPoolExecutor(max_workers=12) as executor:
        futures = {executor.submit(fetch_and_download_candidate, item): item for item in candidates}
        for future in as_completed(futures):
            try:
                res = future.result()
                enriched_new.append(res)
                if len(enriched_new) % 25 == 0 or len(enriched_new) == len(candidates):
                    print(f"Processed {len(enriched_new)}/{len(candidates)} candidates ({time.time() - start_time:.1f}s)...")
            except Exception as e:
                print(f"Worker error: {e}")

    print(f"Finished processing all {len(enriched_new)} new candidates in {time.time() - start_time:.2f}s!")

    # Sort new players alphabetically or by icon status
    enriched_new.sort(key=lambda p: (p["position"], p["name"]))

    # Now assemble the existing 149 players
    existing_players = []
    for p in PLAYERS_METADATA:
        slug = to_slug(p["name"])
        country_code = p["countryCode"]
        flag_info = NATION_FLAGS.get(p["nationality"])
        flag = flag_info[1] if flag_info else "⚽"
        is_featured = p["name"] in ICONIC_FEATURED_NAMES

        existing_players.append({
            "id": slug,
            "name": p["name"],
            "slug": slug,
            "nationality": p["nationality"],
            "countryCode": country_code,
            "flagEmoji": flag,
            "position": p["position"],
            "detailedPosition": p.get("detailedPosition", p["position"]),
            "famousClubs": p["famousClubs"],
            "internationalRetirementStatus": p["internationalRetirementStatus"],
            "clubRetirementStatus": p["clubRetirementStatus"],
            "retirementYear": p["retirementYear"],
            "era": p["era"],
            "image": f"/images/hall-of-fame-cards/{slug}.webp?v=fc27",
            "imageAttribution": "EA FC 27 Official Collectible Card",
            "bio": p.get("bio", f"Legendary football icon celebrating an immortal career in the beautiful game."),
            "isFeatured": is_featured
        })

    # Combined dataset
    all_players = existing_players + enriched_new
    print(f"\nExisting players: {len(existing_players)}")
    print(f"New players added: {len(enriched_new)}")
    print(f"TOTAL HALL OF FAME LEGENDS: {len(all_players)}")

    # Write out frontend/src/data/hallOfFamePlayers.ts
    out_file = Path("frontend/src/data/hallOfFamePlayers.ts")
    ts_content = f"""// AUTO-GENERATED: Complete dataset of all {len(all_players)} football legends with official EA FC cards
export interface HallOfFamePlayer {{
  id: string;
  name: string;
  slug: string;
  nationality: string;
  countryCode: string;
  flagEmoji: string;
  position: 'Forward' | 'Midfielder' | 'Defender' | 'Goalkeeper';
  detailedPosition: string;
  famousClubs: string[];
  internationalRetirementStatus: 'Retired' | 'Active';
  clubRetirementStatus: 'Retired' | 'Active';
  retirementYear: number | null;
  era: string;
  image: string;
  imageAttribution: string;
  bio: string;
  isFeatured?: boolean;
}}

export const HALL_OF_FAME_PLAYERS: HallOfFamePlayer[] = {json.dumps(all_players, indent=2, ensure_ascii=False)};

export const TOTAL_HALL_OF_FAME_COUNT = {len(all_players)};
"""
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(ts_content)

    print(f"\nSuccessfully wrote {out_file} with {len(all_players)} legends!")

    # Verify card files on disk
    pub_files = set(f.name for f in PUBLIC_CARDS_DIR.glob("*.webp"))
    missing = [p["slug"] for p in all_players if f"{p['slug']}.webp" not in pub_files]
    print(f"Card images in public: {len(pub_files)}")
    print(f"Missing card images: {len(missing)}")
    if missing:
        print(f"Sample missing: {missing[:10]}")

if __name__ == "__main__":
    main()
