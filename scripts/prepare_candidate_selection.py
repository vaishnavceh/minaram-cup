import json
import re
import unicodedata

def to_slug(name):
    nfkd = unicodedata.normalize('NFKD', name)
    ascii_str = ''.join(c for c in nfkd if not unicodedata.combining(c))
    ascii_str = ascii_str.replace("'", "").replace("’", "")
    slug = re.sub(r'[^a-zA-Z0-9]+', '-', ascii_str.strip().lower())
    return slug.strip('-')

from build_hall_of_fame_data import PLAYERS_METADATA

# Collect all existing slugs and surname/clean forms
existing_slugs = set(to_slug(p["name"]) for p in PLAYERS_METADATA)

# Also explicitly list slugs in discovered_raw_players that correspond to existing 149 players
EXISTING_ALIASES = {
    "ronaldo", "henry", "zidane", "maldini", "ronaldinho", "charlton", "beckham",
    "gerrard", "lampard", "scholes", "rooney", "ibrahimovic", "benzema", "puyol",
    "robben", "ribery", "drogba", "aguero", "villa", "raul", "shevchenko", "klose",
    "kroos", "schweinsteiger", "vieira", "makelele", "seedorf", "van-der-sar",
    "kahn", "cech", "schmeichel", "ferdinand", "terry", "vidic", "pepe", "chiellini",
    "marcelo", "pique", "thuram", "zanetti", "cole", "zambrotta", "mascherano",
    "kompany", "carvalho", "desailly", "hummels", "varane", "toure", "silva",
    "alonso", "ozil", "sneijder", "nedved", "giggs", "rivaldo", "baggio", "bergkamp",
    "van-nistelrooy", "van-persie", "shearer", "owen", "torres", "larsson", "hagi",
    "riquelme", "stoichkov", "bale", "di-maria", "griezmann", "hazard", "nani",
    "okocha", "deco", "rui-costa", "dida", "julio-cesar", "lloris", "lehmann",
    "ivanovic", "samuel", "lucio", "godin", "bonucci", "evra", "abidal", "marquez",
    "hyypia", "ze-roberto", "gilberto-silva", "essien", "gattuso", "keane", "davids",
    "pires", "ballack", "cambiasso", "veron", "fabregas", "alcantara", "de-rossi",
    "cazorla", "hamsik", "stankovic", "nakata", "park-ji-sung", "batistuta", "crespo",
    "tevez", "forlan", "romario", "adriano", "kluivert", "makaay", "cavani",
    "trezeguet", "anelka", "yorke", "falcao", "dzeko", "berbatov", "higuain",
    "milito", "morientes", "messi", "cristiano-ronaldo", "lionel-messi",
    "gianluigi-buffon", "buffon", "andrea-pirlo", "pirlo", "kaka", "sergio-ramos",
    "ramos", "cafu", "roberto-carlos", "fabio-cannavaro", "cannavaro", "neymar",
    "luis-suarez", "suarez", "dani-alves", "alves", "iker-casillas", "casillas",
    "manuel-neuer", "neuer", "samuel-etoo", "francesco-totti", "totti",
    "alessandro-del-piero", "del-piero", "luis-figo", "figo", "sergio-busquets",
    "busquets", "philipp-lahm", "lahm", "alessandro-nesta", "nesta", "kolo-toure"
}

with open("scripts/discovered_raw_players.json", "r", encoding="utf-8") as f:
    raw = json.load(f)

candidates = []
for slug, data in raw.items():
    if slug in existing_slugs or slug in EXISTING_ALIASES:
        continue
    
    alt = data.get("alt", "")
    card = data.get("card", "")
    link = data.get("link", "")
    if not card or not link:
        continue
    
    m = re.search(r'-\s*(\d{2})\s*-', alt)
    rating = int(m.group(1)) if m else 0
    is_icon_hero = "Icon" in alt or "Hero" in alt
    
    candidates.append({
        "slug": slug,
        "alt": alt,
        "card": card,
        "link": link,
        "rating": rating,
        "is_icon_hero": is_icon_hero
    })

print(f"Total non-duplicate candidates: {len(candidates)}")

# Split into icons/heroes and high-rated superstars
icons_heroes = [c for c in candidates if c["is_icon_hero"]]
superstars = [c for c in candidates if not c["is_icon_hero"] and c["rating"] >= 85]

icons_heroes.sort(key=lambda x: x["rating"], reverse=True)
superstars.sort(key=lambda x: x["rating"], reverse=True)

print(f"Icons/Heroes: {len(icons_heroes)}")
print(f"Superstars (>=85): {len(superstars)}")

# We want 275 new players (149 + 275 = 424 total)
needed_total = 275
selected = icons_heroes + superstars[:(needed_total - len(icons_heroes))]

print(f"Selected total new players: {len(selected)}")
print(f"Combined total with existing: {len(PLAYERS_METADATA) + len(selected)}")

with open("scripts/selected_new_candidates.json", "w", encoding="utf-8") as f:
    json.dump(selected, f, indent=2)

print("Saved to scripts/selected_new_candidates.json")
