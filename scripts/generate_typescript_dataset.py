# -*- coding: utf-8 -*-
"""
Generates frontend/src/data/hallOfFamePlayers.ts from PLAYERS_METADATA.
"""

import json
import unicodedata
import re
from pathlib import Path
from build_hall_of_fame_data import PLAYERS_METADATA

def to_slug(name):
    nfkd = unicodedata.normalize('NFKD', name)
    ascii_str = ''.join(c for c in nfkd if not unicodedata.combining(c))
    ascii_str = ascii_str.replace("'", "").replace("’", "")
    slug = re.sub(r'[^a-zA-Z0-9]+', '-', ascii_str.strip().lower())
    return slug.strip('-')

COUNTRY_FLAGS = {
    "AR": "🇦🇷",
    "PT": "🇵🇹",
    "FR": "🇫🇷",
    "BR": "🇧🇷",
    "IT": "🇮🇹",
    "ES": "🇪🇸",
    "DE": "🇩🇪",
    "NL": "🇳🇱",
    "ENG": "🏴󠁧󠁢󠁥󠁮󠁧󠁿",
    "CI": "🇨🇮",
    "UA": "🇺🇦",
    "CM": "🇨🇲",
    "SE": "🇸🇪",
    "CZ": "🇨🇿",
    "DK": "🇩🇰",
    "RS": "🇷🇸",
    "BE": "🇧🇪",
    "WAL": "🏴󠁧󠁢󠁷󠁬󠁳󠁿",
    "RO": "🇷🇴",
    "BG": "🇧🇬",
    "NG": "🇳🇬",
    "UY": "🇺🇾",
    "MX": "🇲🇽",
    "FI": "🇫🇮",
    "GH": "🇬🇭",
    "IE": "🇮🇪",
    "SK": "🇸🇰",
    "JP": "🇯🇵",
    "KR": "🇰🇷",
    "TT": "🇹🇹",
    "CO": "🇨🇴",
    "BA": "🇧🇦",
}

# Iconic legends to highlight in the Featured Legends Carousel
FEATURED_NAMES = [
    "Lionel Messi", "Cristiano Ronaldo", "Zinedine Zidane", "Ronaldo Nazário",
    "Ronaldinho", "Paolo Maldini", "Andrés Iniesta", "Thierry Henry",
    "Gianluigi Buffon", "Kaká", "Andrea Pirlo", "Neymar"
]

def generate_ts():
    out_file = Path("frontend/src/data/hallOfFamePlayers.ts")
    out_file.parent.mkdir(parents=True, exist_ok=True)

    players = []
    for p in PLAYERS_METADATA:
        slug = to_slug(p["name"])
        flag = COUNTRY_FLAGS.get(p["countryCode"], "⚽")
        is_featured = p["name"] in FEATURED_NAMES

        player_obj = {
            "id": slug,
            "name": p["name"],
            "slug": slug,
            "nationality": p["nationality"],
            "countryCode": p["countryCode"],
            "flagEmoji": flag,
            "position": p["position"],
            "detailedPosition": p.get("detailedPosition", p["position"]),
            "famousClubs": p["famousClubs"],
            "internationalRetirementStatus": p["internationalRetirementStatus"],
            "clubRetirementStatus": p["clubRetirementStatus"],
            "retirementYear": p["retirementYear"],
            "era": p["era"],
            "image": f"/images/hall-of-fame-cards/{slug}.webp?v=fc27",
            "imageAttribution": "Wikimedia Commons / CC-BY-SA (reusable public football portrait)",
            "bio": p.get("bio", f"Legendary football icon celebrating an immortal career in the beautiful game."),
            "isFeatured": is_featured
        }
        players.append(player_obj)

    ts_content = f"""// AUTO-GENERATED: Complete dataset of all 149 football legends
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

export const HALL_OF_FAME_PLAYERS: HallOfFamePlayer[] = {json.dumps(players, indent=2, ensure_ascii=False)};

export const TOTAL_HALL_OF_FAME_COUNT = {len(players)};
"""

    with open(out_file, "w", encoding="utf-8") as f:
        f.write(ts_content)

    print(f"Generated {out_file} with {len(players)} players successfully!")

if __name__ == "__main__":
    generate_ts()
