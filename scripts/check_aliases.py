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

existing_names_clean = set()
for p in PLAYERS_METADATA:
    s = to_slug(p["name"]).replace('-', '')
    existing_names_clean.add(s)

with open("scripts/discovered_raw_players.json", "r", encoding="utf-8") as f:
    raw = json.load(f)

# Potential aliases of existing 149 players:
# e.g. "ronaldo" is Ronaldo Nazário (already in 149 as ronaldo-nazario)
# "henry" is Thierry Henry (already in 149 as thierry-henry)
# "zidane" is Zinedine Zidane (already in 149 as zinedine-zidane)
# "maldini" is Paolo Maldini (already in 149 as paolo-maldini)
# "ronaldinho" is Ronaldinho (already in 149 as ronaldinho)
# "charlton" -> Bobby Charlton
# "beckham" -> David Beckham
# "gerrard" -> Steven Gerrard
# "lampard" -> Frank Lampard
# "scholes" -> Paul Scholes
# "rooney" -> Wayne Rooney
# "ibrahimovic" -> Zlatan Ibrahimovic
# "benzema" -> Karim Benzema
# "puyol" -> Carles Puyol
# "robben" -> Arjen Robben
# "ribery" -> Franck Ribery
# "drogba" -> Didier Drogba
# "aguero" -> Sergio Aguero
# "villa" -> David Villa
# "raul" -> Raul
# "shevchenko" -> Andriy Shevchenko
# "klose" -> Miroslav Klose
# "kroos" -> Toni Kroos
# "schweinsteiger" -> Bastian Schweinsteiger
# "vieira" -> Patrick Vieira
# "makelele" -> Claude Makelele
# "seedorf" -> Clarence Seedorf
# "van-der-sar" -> Edwin van der Sar
# "kahn" -> Oliver Kahn
# "cech" -> Petr Cech
# "schmeichel" -> Peter Schmeichel
# "ferdinand" -> Rio Ferdinand
# "terry" -> John Terry
# "vidic" -> Nemanja Vidic
# "pepe" -> Pepe
# "chiellini" -> Giorgio Chiellini
# "marcelo" -> Marcelo
# "pique" -> Gerard Pique
# "thuram" -> Lilian Thuram
# "zanetti" -> Javier Zanetti
# "cole" -> Ashley Cole
# "zambrotta" -> Gianluca Zambrotta
# "mascherano" -> Javier Mascherano
# "kompany" -> Vincent Kompany
# "carvalho" -> Ricardo Carvalho
# "desailly" -> Marcel Desailly
# "hummels" -> Mats Hummels
# "varane" -> Raphael Varane
# "toure" -> Yaya Toure
# "silva" -> David Silva
# "alonso" -> Xabi Alonso
# "ozil" -> Mesut Ozil
# "sneijder" -> Wesley Sneijder
# "nedved" -> Pavel Nedved
# "giggs" -> Ryan Giggs
# "rivaldo" -> Rivaldo
# "baggio" -> Roberto Baggio
# "bergkamp" -> Dennis Bergkamp
# "van-nistelrooy" -> Ruud van Nistelrooy
# "van-persie" -> Robin van Persie
# "shearer" -> Alan Shearer
# "owen" -> Michael Owen
# "torres" -> Fernando Torres
# "larsson" -> Henrik Larsson
# "hagi" -> Gheorghe Hagi
# "riquelme" -> Juan Roman Riquelme
# "stoichkov" -> Hristo Stoichkov
# "bale" -> Gareth Bale
# "di-maria" -> Angel Di Maria
# "griezmann" -> Antoine Griezmann
# "hazard" -> Eden Hazard
# "nani" -> Nani
# "okocha" -> Jay-Jay Okocha
# "deco" -> Deco
# "rui-costa" -> Rui Costa
# "dida" -> Dida
# "julio-cesar" -> Julio Cesar
# "lloris" -> Hugo Lloris
# "lehmann" -> Jens Lehmann
# "ivanovic" -> Branislav Ivanovic
# "samuel" -> Walter Samuel
# "lucio" -> Lucio
# "godin" -> Diego Godin
# "bonucci" -> Leonardo Bonucci
# "evra" -> Patrice Evra
# "abidal" -> Eric Abidal
# "marquez" -> Rafael Marquez
# "hyypia" -> Sami Hyypia
# "ze-roberto" -> Ze Roberto
# "gilberto-silva" -> Gilberto Silva
# "essien" -> Michael Essien
# "gattuso" -> Gennaro Gattuso
# "keane" -> Roy Keane
# "davids" -> Edgar Davids
# "pires" -> Robert Pires
# "ballack" -> Michael Ballack
# "cambiasso" -> Esteban Cambiasso
# "veron" -> Juan Sebastian Veron
# "fabregas" -> Cesc Fabregas
# "alcantara" -> Thiago Alcantara
# "de-rossi" -> Daniele De Rossi
# "cazorla" -> Santi Cazorla
# "hamsik" -> Marek Hamsik
# "stankovic" -> Dejan Stankovic
# "nakata" -> Hidetoshi Nakata
# "park-ji-sung" -> Park Ji-sung
# "batistuta" -> Gabriel Batistuta
# "crespo" -> Hernan Crespo
# "tevez" -> Carlos Tevez
# "forlan" -> Diego Forlan
# "romario" -> Romario
# "adriano" -> Adriano
# "kluivert" -> Patrick Kluivert
# "makaay" -> Roy Makaay
# "cavani" -> Edinson Cavani
# "trezeguet" -> David Trezeguet
# "anelka" -> Nicolas Anelka
# "yorke" -> Dwight Yorke
# "falcao" -> Radamel Falcao
# "dzeko" -> Edin Dzeko
# "berbatov" -> Dimitar Berbatov
# "higuain" -> Gonzalo Higuain
# "milito" -> Diego Milito
# "morientes" -> Fernando Morientes

print("Aliases check ready.")
