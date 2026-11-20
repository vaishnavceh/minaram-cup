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

existing_slugs = set(to_slug(p["name"]) for p in PLAYERS_METADATA)

# All possible aliases / short names
ALL_EXISTING_ALIASES = set(existing_slugs)
for p in PLAYERS_METADATA:
    parts = p["name"].lower().split()
    for pt in parts:
        pt_slug = to_slug(pt)
        if len(pt_slug) > 3:
            ALL_EXISTING_ALIASES.add(pt_slug)

additional = {
    "ronaldo", "messi", "zidane", "maldini", "xavi", "iniesta", "ronaldinho", "henry",
    "buffon", "pirlo", "kaka", "ramos", "cafu", "cannavaro", "neymar", "suarez",
    "alves", "casillas", "neuer", "etoo", "totti", "del-piero", "figo", "beckham",
    "gerrard", "lampard", "scholes", "rooney", "ibrahimovic", "benzema", "busquets",
    "lahm", "nesta", "puyol", "robben", "ribery", "drogba", "aguero", "villa",
    "raul", "shevchenko", "klose", "kroos", "schweinsteiger", "vieira", "makelele",
    "seedorf", "van-der-sar", "kahn", "cech", "schmeichel", "ferdinand", "terry",
    "vidic", "pepe", "chiellini", "marcelo", "pique", "thuram", "zanetti", "cole",
    "zambrotta", "mascherano", "kompany", "carvalho", "desailly", "hummels",
    "varane", "toure", "silva", "alonso", "ozil", "sneijder", "nedved", "giggs",
    "rivaldo", "baggio", "bergkamp", "van-nistelrooy", "van-persie", "shearer",
    "owen", "torres", "larsson", "hagi", "riquelme", "stoichkov", "bale", "di-maria",
    "griezmann", "hazard", "nani", "juninho", "okocha", "deco", "rui-costa",
    "taffarel", "dida", "julio-cesar", "lloris", "lehmann", "ivanovic", "samuel",
    "lucio", "godin", "bonucci", "evra", "abidal", "kolo-toure", "marquez", "hyypia",
    "ze-roberto", "gilberto-silva", "essien", "gattuso", "keane", "davids", "pires",
    "ballack", "cambiasso", "veron", "fabregas", "alcantara", "de-rossi", "cazorla",
    "hamsik", "stankovic", "nakata", "park-ji-sung", "batistuta", "crespo", "tevez",
    "forlan", "romario", "adriano", "kluivert", "makaay", "cavani", "trezeguet",
    "anelka", "yorke", "falcao", "dzeko", "berbatov", "higuain", "milito", "morientes"
}
ALL_EXISTING_ALIASES.update(additional)

with open("scripts/discovered_raw_players.json", "r", encoding="utf-8") as f:
    raw = json.load(f)

new_pool = []
for slug, data in raw.items():
    if slug in ALL_EXISTING_ALIASES:
        continue
    
    alt = data.get("alt", "")
    card = data.get("card", "")
    link = data.get("link", "")
    if not card or not link:
        continue
    
    m = re.search(r'-\s*(\d{2})\s*-', alt)
    rating = int(m.group(1)) if m else 0
    is_icon_hero = "Icon" in alt or "Hero" in alt
    
    new_pool.append({
        "slug": slug,
        "alt": alt,
        "card": card,
        "link": link,
        "rating": rating,
        "is_icon_hero": is_icon_hero
    })

icons_heroes = [c for c in new_pool if c["is_icon_hero"]]
superstars = [c for c in new_pool if not c["is_icon_hero"] and c["rating"] >= 85]

icons_heroes.sort(key=lambda x: x["rating"], reverse=True)
superstars.sort(key=lambda x: x["rating"], reverse=True)

print(f"Total existing: {len(PLAYERS_METADATA)}")
print(f"Icons/Heroes available: {len(icons_heroes)}")
print(f"Superstars (>= 85) available: {len(superstars)}")

# Target: 270 new players -> 149 + 270 = 419 total!
target_new = 270
selected = icons_heroes + superstars[:(target_new - len(icons_heroes))]
print(f"Selected new players: {len(selected)}")
print(f"Total in Hall of Fame: {len(PLAYERS_METADATA) + len(selected)}")

with open("scripts/selected_curated_new_players.json", "w", encoding="utf-8") as f:
    json.dump(selected, f, indent=2)

print("Saved to scripts/selected_curated_new_players.json")
