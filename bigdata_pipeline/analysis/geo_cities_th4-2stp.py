#!/usr/bin/env python3
"""Theme 4 (step 1) - infer a city for each channel.

Three complementary sources, from the most to the least reliable:
  1. DIRECT   the name of a major city of the channel's language is found in its title,
              description or username. The language is the one of Channel_Language.csv, or,
              when the channel has none (or nothing is found), the language the title is
              written in (script / letters based, no external service).
  2. NEIGHBOURS  a channel without a city takes the city most of its forwarding partners
              have (weighted vote on the forward graph, restricted to the countries of its
              language when known). Accuracy is measured by hiding known cities (holdout).
The built-in gazetteer (52 languages, editable) gives the cities of each language.

Outputs, under --out (layout <name>/<name>.csv like the other analysis scripts):
  channel_geo/                final table, one row per channel with a city (any source)
  channel_city/               direct matches, one row per (channel, city)
  channel_city_inferred/      neighbour-vote cities with their vote share
  propagation_accuracy/       holdout accuracy of the neighbour vote, by vote share
  city_coverage/, language_coverage/, geo_summary/
  validation_sample/          random channels per method to check by hand (fill `correct`)
  README.md, plus figures in --figdir.

Usage:
  python3 geo_cities.py --metadata telescope_files/Source_Channel_Metadata.csv \
      --languages telescope_files/Channel_Language.csv \
      --gold telescope_pipeline_files/gold \
      --out bigdata_pipeline/analysis/geo --figdir bigdata_pipeline/analysis/figures/geo
  python3 geo_cities.py --selftest
The neighbour vote needs community_detection_v2.py in the same folder (it reuses its edge reader).
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import tempfile
import unicodedata
from pathlib import Path as _P
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

csv.field_size_limit(10**9)
sys.path.insert(0, str(_P(__file__).resolve().parent))

RAW = """
ru|Russia|Moscow|москв*;moscow;мск
ru|Russia|Saint Petersburg|санкт-петербург*;петербург*;питер*;спб;spb;saint petersburg;st petersburg
ru|Russia|Novosibirsk|новосибирск*;novosibirsk
ru|Russia|Yekaterinburg|екатеринбург*;yekaterinburg;ekaterinburg
ru|Russia|Kazan|казань;казани;казанью;kazan
ru|Russia|Nizhny Novgorod|нижн* новгород*;nizhny novgorod
ru|Russia|Chelyabinsk|челябинск*;chelyabinsk
ru|Russia|Samara|самара;самары;самаре;самару;samara
ru|Russia|Omsk|омск*;omsk
ru|Russia|Rostov-on-Don|ростов*;rostov
ru|Russia|Ufa|уфа;уфе;уфы;уфу;ufa
ru|Russia|Krasnoyarsk|красноярск*;krasnoyarsk
ru|Russia|Voronezh|воронеж*;voronezh
ru|Russia|Perm|пермь;перми;пермск*
ru|Russia|Volgograd|волгоград*;volgograd
ru|Russia|Krasnodar|краснодар*;krasnodar
ru|Russia|Saratov|саратов*;saratov
ru|Russia|Tyumen|тюмен*;tyumen
ru|Russia|Vladivostok|владивосток*;vladivostok
ru|Russia|Khabarovsk|хабаровск*;khabarovsk
ru|Russia|Irkutsk|иркутск*;irkutsk
ru|Russia|Sevastopol|севастопол*;sevastopol
ru|Russia|Simferopol|симферопол*;simferopol
ru|Belarus|Minsk|минск*;minsk
ru|Kazakhstan|Almaty|алмат*;almaty
ru|Kazakhstan|Astana|астан*;astana;нур-султан*
ru|Ukraine|Donetsk|донецк*;donetsk
ru|Ukraine|Luhansk|луганск*;luhansk;lugansk
ru|Ukraine|Kharkiv|харьков*;kharkiv;kharkov
uk|Ukraine|Kyiv|київ*;киев*;kyiv;kiev
uk|Ukraine|Kharkiv|харків*;харьков*;kharkiv
uk|Ukraine|Odesa|одес*;odesa;odessa
uk|Ukraine|Dnipro|дніпр*;днепр*;dnipro
uk|Ukraine|Lviv|львів*;львов*;lviv
uk|Ukraine|Zaporizhzhia|запоріж*;запорож*;zaporizhzhia;zaporozhye
uk|Ukraine|Mykolaiv|миколаїв*;николаев*;mykolaiv
uk|Ukraine|Vinnytsia|вінниц*;винниц*;vinnytsia
uk|Ukraine|Kherson|херсон*;kherson
uk|Ukraine|Poltava|полтав*;poltava
uk|Ukraine|Chernihiv|чернігів*;чернигов*;chernihiv
uk|Ukraine|Mariupol|маріупол*;мариупол*;mariupol
uk|Ukraine|Zhytomyr|житомир*;zhytomyr
uk|Ukraine|Rivne|рівн*;rivne
be|Belarus|Minsk|мінск*;минск*;minsk
be|Belarus|Gomel|гомел*;gomel;homel
be|Belarus|Brest|брэст*;brest
be|Belarus|Vitebsk|віцебск*;vitebsk
ar|Egypt|Cairo|القاهرة;cairo
ar|Egypt|Alexandria|الاسكندرية;alexandria
ar|Saudi Arabia|Riyadh|الرياض;riyadh
ar|Saudi Arabia|Jeddah|جدة;jeddah
ar|UAE|Dubai|دبي;dubai
ar|UAE|Abu Dhabi|ابوظبي;abu dhabi
ar|Iraq|Baghdad|بغداد;baghdad
ar|Iraq|Mosul|الموصل;mosul
ar|Syria|Damascus|دمشق;damascus
ar|Syria|Aleppo|حلب;aleppo
ar|Syria|Idlib|ادلب;idlib
ar|Lebanon|Beirut|بيروت;beirut
ar|Jordan|Amman|عمّان;amman
ar|Qatar|Doha|الدوحة;doha
ar|Morocco|Casablanca|الدار البيضاء;casablanca
ar|Morocco|Rabat|الرباط;rabat
ar|Algeria|Algiers|algiers
ar|Tunisia|Tunis|tunis
ar|Libya|Tripoli|طرابلس;tripoli
ar|Palestine|Gaza|غزة;gaza
ar|Palestine|Jerusalem|القدس;jerusalem
ar|Yemen|Sanaa|صنعاء;sanaa
ar|Sudan|Khartoum|الخرطوم;khartoum
fa|Iran|Tehran|تهران;tehran
fa|Iran|Mashhad|مشهد;mashhad
fa|Iran|Isfahan|اصفهان;isfahan
fa|Iran|Shiraz|شیراز;shiraz
fa|Iran|Tabriz|تبریز;tabriz
fa|Iran|Karaj|کرج;karaj
fa|Iran|Ahvaz|اهواز;ahvaz
fa|Afghanistan|Kabul|کابل;kabul
fa|Afghanistan|Herat|هرات;herat
tr|Turkey|Istanbul|istanbul*;استانبول
tr|Turkey|Ankara|ankara*
tr|Turkey|Izmir|izmir*
tr|Turkey|Bursa|bursa*
tr|Turkey|Antalya|antalya*
tr|Turkey|Adana|adana*
tr|Turkey|Konya|konya*
tr|Turkey|Gaziantep|gaziantep*
tr|Turkey|Kayseri|kayseri*
tr|Turkey|Mersin|mersin*
en|USA|New York|new york;nyc
en|USA|Los Angeles|los angeles
en|USA|Chicago|chicago
en|USA|Houston|houston
en|USA|Washington DC|washington dc;washington d.c.
en|USA|Miami|miami
en|UK|London|london
en|UK|Manchester|manchester
en|UK|Birmingham|birmingham
en|Canada|Toronto|toronto
en|Australia|Sydney|sydney
en|Australia|Melbourne|melbourne
en|India|Delhi|delhi
en|India|Mumbai|mumbai
en|Nigeria|Lagos|lagos
en|Kenya|Nairobi|nairobi
en|South Africa|Johannesburg|johannesburg
en|Ireland|Dublin|dublin
es|Spain|Madrid|madrid
es|Spain|Barcelona|barcelona
es|Spain|Seville|sevilla;seville
es|Spain|Valencia|valencia
es|Mexico|Mexico City|ciudad de mexico;cdmx;mexico city
es|Mexico|Guadalajara|guadalajara
es|Mexico|Monterrey|monterrey
es|Argentina|Buenos Aires|buenos aires
es|Colombia|Bogota|bogota
es|Colombia|Medellin|medellin
es|Peru|Lima|lima
es|Chile|Santiago|santiago
es|Venezuela|Caracas|caracas
es|Uruguay|Montevideo|montevideo
es|Ecuador|Quito|quito
pt|Brazil|Sao Paulo|sao paulo
pt|Brazil|Rio de Janeiro|rio de janeiro
pt|Brazil|Brasilia|brasilia
pt|Brazil|Salvador|salvador
pt|Brazil|Belo Horizonte|belo horizonte
pt|Brazil|Fortaleza|fortaleza
pt|Brazil|Curitiba|curitiba
pt|Brazil|Porto Alegre|porto alegre
pt|Portugal|Lisbon|lisboa;lisbon
pt|Angola|Luanda|luanda
pt|Mozambique|Maputo|maputo
fr|France|Paris|paris
fr|France|Marseille|marseille
fr|France|Lyon|lyon
fr|France|Toulouse|toulouse
fr|France|Nice|nice
fr|France|Bordeaux|bordeaux
fr|France|Lille|lille
fr|Belgium|Brussels|bruxelles;brussels
fr|Switzerland|Geneva|geneve;geneva
fr|Canada|Montreal|montreal
fr|Senegal|Dakar|dakar
fr|Ivory Coast|Abidjan|abidjan
fr|DR Congo|Kinshasa|kinshasa
de|Germany|Berlin|berlin
de|Germany|Hamburg|hamburg
de|Germany|Munich|munchen;muenchen;munich
de|Germany|Cologne|koln;koeln;cologne
de|Germany|Frankfurt|frankfurt
de|Germany|Stuttgart|stuttgart
de|Germany|Dusseldorf|dusseldorf;duesseldorf
de|Germany|Dresden|dresden
de|Germany|Leipzig|leipzig
de|Austria|Vienna|wien;vienna
de|Switzerland|Zurich|zurich;zuerich
it|Italy|Rome|roma;rome
it|Italy|Milan|milano;milan
it|Italy|Naples|napoli;naples
it|Italy|Turin|torino;turin
it|Italy|Palermo|palermo
it|Italy|Genoa|genova;genoa
it|Italy|Bologna|bologna
it|Italy|Florence|firenze;florence
it|Italy|Venice|venezia;venice
pl|Poland|Warsaw|warszaw*;warsaw
pl|Poland|Krakow|krakow*;krakó*
pl|Poland|Lodz|łódź;lodz
pl|Poland|Wroclaw|wroclaw*;wrocław*
pl|Poland|Poznan|poznan*;poznań*
pl|Poland|Gdansk|gdansk*;gdańsk*
pl|Poland|Szczecin|szczecin*
pl|Poland|Lublin|lublin*
cs|Czechia|Prague|praha;prague;prah*
cs|Czechia|Brno|brno
cs|Czechia|Ostrava|ostrava
cs|Czechia|Plzen|plzen
cs|Czechia|Olomouc|olomouc
sk|Slovakia|Bratislava|bratislav*
sk|Slovakia|Kosice|kosice
sk|Slovakia|Presov|presov
bg|Bulgaria|Sofia|софия;sofia
bg|Bulgaria|Plovdiv|пловдив;plovdiv
bg|Bulgaria|Varna|варна;varna
bg|Bulgaria|Burgas|бургас;burgas
sr|Serbia|Belgrade|београд*;beograd*;belgrade
sr|Serbia|Novi Sad|нови сад*;novi sad
sr|Serbia|Nis|ниш;nis
hr|Croatia|Zagreb|zagreb
hr|Croatia|Split|split
hr|Croatia|Rijeka|rijeka
ro|Romania|Bucharest|bucuresti;bucharest
ro|Romania|Cluj-Napoca|cluj
ro|Romania|Timisoara|timisoara
ro|Romania|Iasi|iasi
ro|Romania|Constanta|constanta
hu|Hungary|Budapest|budapest
hu|Hungary|Debrecen|debrecen
hu|Hungary|Szeged|szeged
el|Greece|Athens|αθην*;athens;athina
el|Greece|Thessaloniki|θεσσαλονικ*;thessaloniki
he|Israel|Tel Aviv|תל אביב;tel aviv
he|Israel|Jerusalem|ירושלים;jerusalem
he|Israel|Haifa|חיפה;haifa
he|Israel|Beer Sheva|באר שבע;beer sheva
hi|India|Delhi|दिल्ली;delhi
hi|India|Mumbai|मुंबई;मुम्बई;mumbai
hi|India|Kolkata|कोलकाता;kolkata
hi|India|Chennai|चेन्नई;chennai
hi|India|Hyderabad|हैदराबाद;hyderabad
hi|India|Lucknow|लखनऊ;lucknow
hi|India|Jaipur|जयपुर;jaipur
ur|Pakistan|Karachi|کراچی;karachi
ur|Pakistan|Lahore|لاہور;lahore
ur|Pakistan|Islamabad|اسلام آباد;islamabad
ur|Pakistan|Rawalpindi|راولپنڈی;rawalpindi
bn|Bangladesh|Dhaka|ঢাকা;dhaka
bn|Bangladesh|Chittagong|চট্টগ্রাম;chittagong
bn|India|Kolkata|কলকাতা;kolkata
id|Indonesia|Jakarta|jakarta
id|Indonesia|Surabaya|surabaya
id|Indonesia|Bandung|bandung
id|Indonesia|Medan|medan
id|Indonesia|Semarang|semarang
id|Indonesia|Makassar|makassar
ms|Malaysia|Kuala Lumpur|kuala lumpur
ms|Malaysia|Johor Bahru|johor bahru
ms|Malaysia|George Town|george town;penang
th|Thailand|Bangkok|กรุงเทพ;bangkok
th|Thailand|Chiang Mai|เชียงใหม่;chiang mai
th|Thailand|Phuket|ภูเก็ต;phuket
vi|Vietnam|Hanoi|ha noi;hanoi
vi|Vietnam|Ho Chi Minh City|ho chi minh;saigon;sai gon
vi|Vietnam|Da Nang|da nang;đa nang
ja|Japan|Tokyo|東京;tokyo
ja|Japan|Osaka|大阪;osaka
ja|Japan|Nagoya|名古屋;nagoya
ja|Japan|Yokohama|横浜;yokohama
ja|Japan|Fukuoka|福岡;fukuoka
ja|Japan|Sapporo|札幌;sapporo
ko|South Korea|Seoul|서울;seoul
ko|South Korea|Busan|부산;busan
ko|South Korea|Incheon|인천;incheon
zh-cn|China|Beijing|北京;beijing
zh-cn|China|Shanghai|上海;shanghai
zh-cn|China|Guangzhou|广州;guangzhou
zh-cn|China|Shenzhen|深圳;shenzhen
zh-cn|China|Chengdu|成都;chengdu
zh-cn|China|Wuhan|武汉;wuhan
kk|Kazakhstan|Astana|астана*;астан*;astana;нур-султан*
kk|Kazakhstan|Almaty|алматы*;almaty
kk|Kazakhstan|Shymkent|шымкент*;shymkent
uz|Uzbekistan|Tashkent|toshkent;tashkent;ташкент*
uz|Uzbekistan|Samarkand|samarqand;samarkand
az|Azerbaijan|Baku|baki;baku;баку
ka|Georgia|Tbilisi|თბილის*;tbilisi
ka|Georgia|Batumi|ბათუმ*;batumi
hy|Armenia|Yerevan|երևան*;yerevan;ереван*
hy|Armenia|Gyumri|գյումրի;gyumri
nl|Netherlands|Amsterdam|amsterdam
nl|Netherlands|Rotterdam|rotterdam
nl|Netherlands|The Hague|den haag;the hague
nl|Netherlands|Utrecht|utrecht
nl|Belgium|Antwerp|antwerpen;antwerp
sv|Sweden|Stockholm|stockholm
sv|Sweden|Gothenburg|goteborg;gothenburg
sv|Sweden|Malmo|malmo
fi|Finland|Helsinki|helsinki
fi|Finland|Tampere|tampere
fi|Finland|Turku|turku
no|Norway|Oslo|oslo
no|Norway|Bergen|bergen
no|Norway|Trondheim|trondheim
da|Denmark|Copenhagen|kobenhavn;copenhagen
da|Denmark|Aarhus|aarhus
mk|North Macedonia|Skopje|скопје;skopje
mk|North Macedonia|Bitola|битола;bitola
sq|Albania|Tirana|tirane;tirana
sq|Kosovo|Pristina|prishtine;pristina;prishtina
sl|Slovenia|Ljubljana|ljubljana
sl|Slovenia|Maribor|maribor
tl|Philippines|Manila|maynila;manila
tl|Philippines|Quezon City|quezon city
tl|Philippines|Cebu|cebu
tl|Philippines|Davao|davao
ca|Spain|Barcelona|barcelona
so|Somalia|Mogadishu|muqdisho;mogadishu
so|Somalia|Hargeisa|hargeisa
af|South Africa|Cape Town|kaapstad;cape town
af|South Africa|Johannesburg|johannesburg
af|South Africa|Pretoria|pretoria
cy|UK|Cardiff|caerdydd;cardiff
te|India|Hyderabad|హైదరాబాద్;hyderabad
pa|India|Amritsar|ਅੰਮ੍ਰਿਤਸਰ;amritsar
pa|India|Ludhiana|ਲੁਧਿਆਣਾ;ludhiana
"""

def rows() -> list[tuple[str, str, str, str]]:
    """Parse RAW into (lang, country, city, aliases) tuples."""
    return [tuple(line.split("|")) for line in RAW.strip().splitlines()]


NULL_LANG = {"", "nan", "none", "unknown", "cannot determine", "und"}
FIELD_PRIORITY = ["title", "about", "username"]   # first field with a match wins
_SUBSTRING_RANGES = [(0x0E00, 0x0E7F), (0x3040, 0x9FFF), (0xAC00, 0xD7AF)]   # Thai, Japanese/Chinese, Korean


# ----------------------------------------------------------------- text normalisation
def norm(text: str) -> str:
    """Lower-case, strip accents/combining marks, unify a few Arabic/Persian letters."""
    text = unicodedata.normalize("NFKD", str(text))
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    text = text.casefold().replace("ك", "ک").replace("ي", "ی").replace("ى", "ی")
    text = text.replace("_", " ")
    return re.sub(r"\s+", " ", text).strip()


def needs_substring(alias: str) -> bool:
    """Scripts without spaces between words (CJK, Thai, Hangul) are matched as substrings."""
    return any(lo <= ord(c) <= hi for c in alias for lo, hi in _SUBSTRING_RANGES)


def alias_pattern(alias: str) -> str:
    """Regex for one normalised alias; a trailing '*' on a word means 'any ending'."""
    words = [(re.escape(w[:-1]) + r"\w*") if w.endswith("*") else re.escape(w) for w in alias.split(" ")]
    pat = r"\s+".join(words)
    return pat if needs_substring(alias) else rf"(?<!\w)(?:{pat})(?!\w)"


# ----------------------------------------------------------------- gazetteer
class Matcher:
    """One compiled regex per language; the matching group tells which city was found."""

    def __init__(self, rows: list[tuple[str, str, str, str]]):
        by_lang: dict[str, list[tuple[str, str, str]]] = {}
        for lang, country, city, aliases in rows:
            for a in aliases.split(";"):
                a = norm(a)
                if a:
                    by_lang.setdefault(lang.strip().lower(), []).append((a, country, city))
        self.cities: dict[str, list[tuple[str, str]]] = {}
        self.regex: dict[str, tuple[re.Pattern, list[tuple[str, str]]]] = {}
        for lang, items in by_lang.items():
            items = sorted(items, key=lambda t: -len(t[0]))      # longest alias first
            pat = "|".join(f"({alias_pattern(a)})" for a, _, _ in items)
            self.regex[lang] = (re.compile(pat), [(c, k) for _, k, c in items])
            self.cities[lang] = sorted({(k, c) for _, k, c in items})

    def languages(self) -> set[str]:
        return set(self.regex)

    def find(self, lang: str, text: str) -> list[tuple[str, str, str]]:
        """List of (city, country, matched_text) for the normalised `text`."""
        rx, meta = self.regex[lang]
        found, seen = [], set()
        for m in rx.finditer(text):
            city, country = meta[m.lastindex - 1]
            if (city, country) not in seen:
                seen.add((city, country))
                found.append((city, country, m.group(0)))
        return found


def load_gazetteer(path: str | None) -> list[tuple[str, str, str, str]]:
    if not path:
        return rows()
    df = pd.read_csv(path, dtype=str).fillna("")
    return list(df[["lang", "country", "city", "aliases"]].itertuples(index=False, name=None))


# ----------------------------------------------------------------- inputs
def load_languages(path: str) -> dict[int, str]:
    """channel id -> language code, from Channel_Language.csv (any separator)."""
    df = pd.read_csv(path, sep=None, engine="python", dtype=str)
    name_col = next(c for c in df.columns if "file" in str(c).lower() or "channel" in str(c).lower())
    lang_col = next(c for c in df.columns if "lang" in str(c).lower())
    ids = df[name_col].astype(str).str.extract(r"(\d+)")[0]
    langs = df[lang_col].astype(str).str.strip().str.lower()
    ok = ids.notna() & ~langs.isin(NULL_LANG)
    return dict(zip(ids[ok].astype("int64"), langs[ok]))


def channel_texts(obj: dict) -> dict[str, str]:
    """Raw searchable text fields of one channel JSON (only those that exist)."""
    texts = {"title": obj.get("title") or "", "about": obj.get("about") or obj.get("description") or ""}
    names = []
    if obj.get("username"):
        names.append(obj["username"])
    for u in obj.get("usernames") or []:
        if isinstance(u, dict) and u.get("username"):
            names.append(u["username"])
    texts["username"] = " ".join(names)
    return {k: str(v) for k, v in texts.items() if v}


def iter_metadata(path: str):
    """Yield (channel_id, raw text fields) for every valid row."""
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            try:
                obj = json.loads(row["data"])
                cid = int(row["id"])
            except (ValueError, KeyError, TypeError):
                continue
            yield cid, channel_texts(obj)


# ----------------------------------------------------------------- language written in the text
_SCRIPTS = [("cyr", 0x0400, 0x04FF), ("ara", 0x0600, 0x06FF), ("ara", 0x0750, 0x077F), ("heb", 0x0590, 0x05FF),
            ("grk", 0x0370, 0x03FF), ("dev", 0x0900, 0x097F), ("ben", 0x0980, 0x09FF), ("pan", 0x0A00, 0x0A7F),
            ("tel", 0x0C00, 0x0C7F), ("tha", 0x0E00, 0x0E7F), ("geo", 0x10A0, 0x10FF), ("arm", 0x0530, 0x058F),
            ("kor", 0xAC00, 0xD7AF), ("kor", 0x1100, 0x11FF), ("kana", 0x3040, 0x30FF), ("han", 0x4E00, 0x9FFF),
            ("lat", 0x0041, 0x024F), ("lat", 0x1E00, 0x1EFF)]
_SCRIPT_LANG = {"heb": "he", "grk": "el", "dev": "hi", "ben": "bn", "pan": "pa", "tel": "te", "tha": "th",
                "geo": "ka", "arm": "hy", "kor": "ko", "kana": "ja"}
_EN_WORDS = {"the", "news", "of", "and", "for", "official", "channel", "daily", "world", "live", "tv", "club",
             "team", "my", "our", "your", "with", "from", "online", "group"}


def _has(text: str, chars: str) -> bool:
    return any(c in text for c in chars)


def detect_text_language(text: str) -> str | None:
    """Language a short text is written in (script and distinctive letters). None when unsure.

    Latin text without a distinctive letter is 'en' only if it contains common English words.
    """
    low = str(text).lower()
    counts: Counter = Counter()
    for ch in low:
        o = ord(ch)
        if not ch.isalpha():
            continue
        for name, lo, hi in _SCRIPTS:
            if lo <= o <= hi:
                counts[name] += 1
                break
    if not counts or sum(counts.values()) < 2:
        return None
    script = counts.most_common(1)[0][0]
    if script in _SCRIPT_LANG:
        return _SCRIPT_LANG[script]
    if script == "han":
        return "ja" if counts.get("kana") else "zh-cn"
    if script == "cyr":
        if _has(low, "ў"): return "be"
        if _has(low, "їєґ"): return "uk"
        if _has(low, "ђћљњџ"): return "sr"
        if _has(low, "ѓќѕ"): return "mk"
        if _has(low, "әғқңөұүһ"): return "kk"
        if "і" in low and not _has(low, "ыэъ"): return "uk"
        return "ru"
    if script == "ara":
        if _has(low, "ٹڈڑےںھہ"): return "ur"
        if _has(low, "پچژگ"): return "fa"
        return "ar"
    # Latin script
    if _has(low, "ğı") or (_has(low, "ş") and not _has(low, "ă")): return "tr"
    if _has(low, "ășț"): return "ro"
    if _has(low, "ñ¿¡"): return "es"
    if _has(low, "ãõ"): return "pt"
    if _has(low, "ąęłśźżćń"): return "pl"
    if _has(low, "řěů"): return "cs"
    if _has(low, "őű"): return "hu"
    if _has(low, "đ") or _has(low, "ạảấầậắằặẹẻẽếềệỉịọỏốồộớờợụủứừựỳỷỹ"): return "vi"
    if _has(low, "äöüß"): return "de"
    if set(re.findall(r"[a-z]+", low)) & _EN_WORDS: return "en"
    return None


# ----------------------------------------------------------------- UTC offsets (standard time, no DST)
COUNTRY_UTC = {
    "Belarus": 3, "Kazakhstan": 5, "Ukraine": 2, "Egypt": 2, "Saudi Arabia": 3, "UAE": 4, "Iraq": 3, "Syria": 3,
    "Lebanon": 2, "Jordan": 3, "Qatar": 3, "Morocco": 1, "Algeria": 1, "Tunisia": 1, "Libya": 2, "Palestine": 2,
    "Yemen": 3, "Sudan": 2, "Iran": 3.5, "Afghanistan": 4.5, "Turkey": 3, "UK": 0, "India": 5.5, "Nigeria": 1,
    "Kenya": 3, "South Africa": 2, "Ireland": 0, "Spain": 1, "Argentina": -3, "Colombia": -5, "Peru": -5,
    "Chile": -4, "Venezuela": -4, "Uruguay": -3, "Ecuador": -5, "Brazil": -3, "Portugal": 0, "Angola": 1,
    "Mozambique": 2, "France": 1, "Belgium": 1, "Switzerland": 1, "Senegal": 0, "Ivory Coast": 0, "DR Congo": 1,
    "Germany": 1, "Austria": 1, "Italy": 1, "Poland": 1, "Czechia": 1, "Slovakia": 1, "Bulgaria": 2, "Serbia": 1,
    "Croatia": 1, "Romania": 2, "Hungary": 1, "Greece": 2, "Israel": 2, "Pakistan": 5, "Bangladesh": 6,
    "Malaysia": 8, "Thailand": 7, "Vietnam": 7, "Japan": 9, "South Korea": 9, "China": 8, "Uzbekistan": 5,
    "Azerbaijan": 4, "Georgia": 4, "Armenia": 4, "Netherlands": 1, "Sweden": 1, "Finland": 2, "Norway": 1,
    "Denmark": 1, "North Macedonia": 1, "Albania": 1, "Kosovo": 1, "Slovenia": 1, "Philippines": 8, "Somalia": 3,
}
CITY_UTC = {   # countries spanning several zones, or cities that differ from their country
    "Moscow": 3, "Saint Petersburg": 3, "Novosibirsk": 7, "Yekaterinburg": 5, "Kazan": 3, "Nizhny Novgorod": 3,
    "Chelyabinsk": 5, "Samara": 4, "Omsk": 6, "Rostov-on-Don": 3, "Ufa": 5, "Krasnoyarsk": 7, "Voronezh": 3,
    "Perm": 5, "Volgograd": 3, "Krasnodar": 3, "Saratov": 4, "Tyumen": 5, "Vladivostok": 10, "Khabarovsk": 10,
    "Irkutsk": 8, "Sevastopol": 3, "Simferopol": 3,
    "New York": -5, "Los Angeles": -8, "Chicago": -6, "Houston": -6, "Washington DC": -5, "Miami": -5,
    "Toronto": -5, "Montreal": -5, "Sydney": 10, "Melbourne": 10, "Mexico City": -6, "Guadalajara": -6,
    "Monterrey": -6, "Makassar": 8, "Jakarta": 7, "Surabaya": 7, "Bandung": 7, "Medan": 7, "Semarang": 7,
}


def offset_of(country: str, city: str) -> float:
    """Standard UTC offset (hours) of a gazetteer city, NaN if unknown."""
    if city in CITY_UTC:
        return float(CITY_UTC[city])
    return float(COUNTRY_UTC.get(country, np.nan))


def circ_dist(a, b, period=24.0):
    """Circular distance between two hours (or arrays of hours)."""
    d = np.abs((np.asarray(a, float) - np.asarray(b, float)) % period)
    return np.minimum(d, period - d)


def load_temporal(path: str, min_posts: int = 100):
    """Channel 24-hour activity profiles. Returns (channel ids, counts[n, 24]) for channels with enough posts."""
    df = pd.read_csv(path, dtype=str)
    ids = df.iloc[:, 0].astype(str).str.extract(r"(\d+)")[0]
    vals = df.iloc[:, 1:25].apply(pd.to_numeric, errors="coerce").fillna(0).to_numpy(float)
    ok = ids.notna().to_numpy() & (vals.sum(axis=1) >= min_posts)
    return ids[ok].astype("int64").to_numpy(), vals[ok]


def _phase(profile_sum: np.ndarray) -> tuple[float, float]:
    """First-harmonic phase (hours, 0-24) and relative amplitude of a 24-bin profile."""
    h = np.arange(24) + 0.5
    z = (profile_sum * np.exp(-2j * np.pi * h / 24)).sum()
    tot = profile_sum.sum()
    return float((-np.angle(z) * 24 / (2 * np.pi)) % 24), float(abs(z) / tot) if tot else 0.0


def timezone_check(single: pd.DataFrame, tids: np.ndarray, P: np.ndarray, min_channels: int = 30):
    """Are the hours in Temporal_Channel_Metadata UTC or local time?

    Channels with a known city and a known UTC offset are pooled per city. If the hours are UTC, the
    daily peak of a city moves with its offset (peak_utc + offset is the same everywhere); if they are
    local time, peak_utc itself is the same everywhere. The test compares the two alignments.
    Needs cities with at least two different offsets (at least 2 h apart).
    """
    pos = {int(c): i for i, c in enumerate(tids)}
    rows = []
    for (country, city), g in single.groupby(["country", "city"]):
        off = offset_of(country, city)
        idx = [pos[int(c)] for c in g.channel_id if int(c) in pos]
        if np.isnan(off) or len(idx) < min_channels:
            continue
        prof = (P[idx] / P[idx].sum(axis=1, keepdims=True)).sum(axis=0)
        peak, amp = _phase(prof)
        rows.append({"country": country, "city": city, "utc_offset": off, "n_channels": len(idx),
                     "peak_hour_in_file": round(peak, 2), "peak_if_file_is_utc_local_hour": round((peak + off) % 24, 2),
                     "daily_cycle_strength": round(amp, 3)})
    t = pd.DataFrame(rows)
    if len(t) < 2 or t.utc_offset.nunique() < 2 or (t.utc_offset.max() - t.utc_offset.min()) < 2:
        return t, "inconclusive", {"reason": "need cities with offsets at least 2 h apart (>= min_channels channels each)"}
    w = t.n_channels.to_numpy(float)

    def resultant(hours):
        z = (w * np.exp(2j * np.pi * np.asarray(hours) / 24)).sum() / w.sum()
        return float(abs(z))
    r_utc = resultant(t.peak_hour_in_file + t.utc_offset)
    r_loc = resultant(t.peak_hour_in_file)
    verdict = "UTC" if r_utc >= r_loc + 0.15 else ("local" if r_loc >= r_utc + 0.15 else "inconclusive")
    return t, verdict, {"alignment_if_utc": round(r_utc, 3), "alignment_if_local": round(r_loc, 3)}


def estimate_offsets(single: pd.DataFrame, tids: np.ndarray, P: np.ndarray, seed: int = 42):
    """UTC offset of every channel from its profile, calibrated on channels with a known city.

    The reference daily curve (in local time) is the mean profile of labelled channels shifted by their
    city offset. A channel's offset is the shift of the reference that best matches its profile.
    Labelled channels are scored with a reference built from the other half (2-fold), so they are not
    graded on their own data. Returns {channel: (offset, score)}.
    """
    Pn = P / P.sum(axis=1, keepdims=True)
    pos = {int(c): i for i, c in enumerate(tids)}
    lab = []
    for c, ctry, city in zip(single.channel_id, single.country, single.city):
        off = offset_of(ctry, city)
        if int(c) in pos and not np.isnan(off):
            lab.append((pos[int(c)], int(np.floor(off + 0.5))))
    if len(lab) < 50:
        return {}
    lab_i = np.array([a for a, _ in lab]); lab_o = np.array([b for _, b in lab])

    def local_ref(sel):
        loc = np.array([np.roll(Pn[i], o) for i, o in zip(lab_i[sel], lab_o[sel])])     # local hour = utc hour + offset
        r = loc.mean(axis=0)
        return (r - r.mean()) / (np.linalg.norm(r - r.mean()) or 1.0)

    shifts = np.arange(-12, 13)

    def score(rows, ref):
        X = Pn[rows] - Pn[rows].mean(axis=1, keepdims=True)
        X = X / np.where(np.linalg.norm(X, axis=1, keepdims=True) == 0, 1, np.linalg.norm(X, axis=1, keepdims=True))
        S = np.stack([np.roll(X, s, axis=1) @ ref for s in shifts], axis=1)          # correlation for each candidate offset
        best = S.argmax(axis=1)
        return shifts[best], S.max(axis=1)

    rng = np.random.default_rng(seed)
    fold = rng.integers(0, 2, len(lab_i))
    est: dict[int, tuple[float, float]] = {}
    is_lab = np.zeros(len(tids), bool)
    is_lab[lab_i] = True
    for f in (0, 1):                                                                    # labelled: other half's reference
        rows = lab_i[fold == f]
        o, sc = score(rows, local_ref(fold != f))
        for i, a, b in zip(rows, o, sc):
            est[int(tids[i])] = (float(a), float(b))
    o, sc = score(np.where(~is_lab)[0], local_ref(np.ones(len(lab_i), bool)))            # others: full reference
    for i, a, b in zip(np.where(~is_lab)[0], o, sc):
        est[int(tids[i])] = (float(a), float(b))
    return est


# ----------------------------------------------------------------- direct matching
def assign_cities(metadata: str, langs: dict[int, str], matcher: Matcher, text_language: bool = True):
    """Direct matches. Returns (rows, per-language channel counters, stats, channel info).

    A channel is searched with the language of Channel_Language.csv and, when it has none or
    nothing was found, with the language its title is written in. `info[cid]` = (language, source).
    """
    gaz = matcher.languages()
    rows_out, stats = [], Counter()
    n_lang, n_city = Counter(), Counter()
    info: dict[int, tuple[str, str]] = {}
    for cid, raw in iter_metadata(metadata):
        stats["metadata_rows"] += 1
        known = langs.get(cid)
        text_lang = detect_text_language(" ".join(raw.get(k, "") for k in ("title", "about"))) if text_language else None
        tries = []
        if known:
            tries.append((known, "channel_language"))
            stats["with_language"] += 1
        if text_lang and text_lang != known:
            tries.append((text_lang, "title_language"))
        label = known or text_lang
        if label:
            n_lang[label] += 1
            info[cid] = (label, "channel_language" if known else "title_language")
        if not known and text_lang:
            stats["language_from_title"] += 1
        norm_texts = {k: norm(v) for k, v in raw.items()}
        done = False
        for lang, src in tries:
            if lang not in gaz:
                continue
            stats["searched"] += 1
            for field in FIELD_PRIORITY:
                if field not in norm_texts:
                    continue
                found = matcher.find(lang, norm_texts[field])
                if found:
                    for city, country, alias in found:
                        rows_out.append({"channel_id": cid, "language": lang, "language_source": src,
                                         "country": country, "city": city, "field": field,
                                         "matched_text": alias, "n_cities": len(found),
                                         "title": raw.get("title", "")})
                    n_city[lang] += 1
                    stats["direct_" + src] += 1
                    stats["matched_channels"] += 1
                    done = True
                    break
            if done:
                break
    return rows_out, n_lang, n_city, stats, info


# ----------------------------------------------------------------- neighbour vote
def propagate(net, labels: dict[int, tuple[str, str]], lang_of: dict[int, str], matcher: Matcher,
              min_class: int = 30, min_vote: float = 0.6, holdout: float = 0.1, seed: int = 42,
              tz: dict[int, tuple[float, float]] | None = None, tz_tol: float = 2.0, min_tz_score: float = 0.3):
    """Cities of unlabelled channels from their forwarding partners.

    labels: channel -> (country, city) for channels with exactly one direct city.
    The vote is restricted to the countries of the channel's language when it has a gazetteer entry.
    tz: optional {channel: (estimated UTC offset, score)}; when given, a channel whose profile is clear
    enough (score >= min_tz_score) can only receive a city whose UTC offset is within `tz_tol` hours.
    Returns (accuracy table, inferred table).
    """
    from scipy import sparse
    nodes = np.asarray(net.nodes)
    n = len(nodes)
    pos = {int(c): i for i, c in enumerate(nodes)}
    lab_idx = np.array([pos[c] for c in labels if c in pos], dtype=np.int64)
    lab_val = [labels[int(nodes[i])] for i in lab_idx]
    cnt = Counter(lab_val)
    classes = [k for k, v in cnt.items() if v >= min_class]
    if len(classes) < 2:
        return None, None
    cidx = {k: i for i, k in enumerate(classes)}
    cls = -np.ones(n, dtype=np.int64)
    for i, v in zip(lab_idx, lab_val):
        cls[i] = cidx.get(v, -1)
    A = sparse.coo_matrix((np.r_[net.w, net.w], (np.r_[net.src, net.dst], np.r_[net.dst, net.src])),
                          shape=(n, n)).tocsr()
    countries = np.array([k[0] for k in classes])
    class_off = np.array([offset_of(k[0], k[1]) for k in classes], dtype=float)
    allowed: dict[str, np.ndarray] = {}
    for lang in matcher.languages():
        cs = {c for c, _ in matcher.cities[lang]}
        allowed[lang] = np.isin(countries, list(cs))

    def predict(known_mask, rows):
        """(predicted class, vote share, total vote) for `rows`, chunked to bound memory."""
        kr = np.where(known_mask & (cls >= 0))[0]
        Y = sparse.csr_matrix((np.ones(len(kr)), (kr, cls[kr])), shape=(n, len(classes)))
        P, S, T = np.zeros(len(rows), int), np.zeros(len(rows)), np.zeros(len(rows))
        for lo in range(0, len(rows), 20000):
            r = rows[lo:lo + 20000]
            V = (A[r] @ Y).toarray()
            for j, i in enumerate(r):                       # restrict to the language's countries
                mask = allowed.get(lang_of.get(int(nodes[i]), ""), None)
                if mask is not None and mask.any():
                    V[j] = V[j] * mask
                if tz is not None and int(nodes[i]) in tz and tz[int(nodes[i])][1] >= min_tz_score:
                    off = tz[int(nodes[i])][0]
                    ok_tz = np.isnan(class_off) | (circ_dist(class_off, off) <= tz_tol)
                    V[j] = V[j] * ok_tz
            tot = V.sum(axis=1)
            has = tot > 0
            P[lo:lo + len(r)] = V.argmax(axis=1)
            T[lo:lo + len(r)] = tot
            S[lo:lo + len(r)] = np.where(has, V.max(axis=1) / np.where(has, tot, 1), 0)
        return P, S, T

    known = cls >= 0
    rng = np.random.default_rng(seed)
    kidx = np.where(known)[0]
    hold = rng.choice(kidx, size=max(1, int(len(kidx) * holdout)), replace=False)
    mask = known.copy()
    mask[hold] = False
    P, S, T = predict(mask, hold)
    ok = P == cls[hold]
    base = float((cls[hold] == np.bincount(cls[mask]).argmax()).mean()) if mask.any() else float("nan")
    has = T > 0
    rows = []
    for lo, hi in zip([0, 0.5, 0.6, 0.7, 0.8, 0.9], [0.5, 0.6, 0.7, 0.8, 0.9, 1.0001]):
        m = has & (S >= lo) & (S < hi)
        rows.append({"row": f"{lo:.1f}-{min(hi, 1.0):.1f}", "held_out_channels": int(m.sum()),
                     "accuracy": round(float(ok[m].mean()), 4) if m.any() else np.nan})
    sel = has & (S >= min_vote)
    rows.append({"row": f">= {min_vote} (rule used)", "held_out_channels": int(sel.sum()),
                 "accuracy": round(float(ok[sel].mean()), 4) if sel.any() else np.nan})
    acc = pd.DataFrame(rows)
    acc["baseline_majority_city"] = round(base, 4)
    acc["held_out_total"] = len(hold)
    acc["with_labelled_neighbour"] = int(has.sum())
    unk = np.where(~known)[0]
    unk = np.array([i for i in unk if int(nodes[i]) not in labels], dtype=np.int64)
    P2, S2, T2 = predict(known, unk)
    keep = (T2 > 0) & (S2 >= min_vote)
    inf = pd.DataFrame({"channel_id": nodes[unk][keep],
                        "country": [classes[i][0] for i in P2[keep]], "city": [classes[i][1] for i in P2[keep]],
                        "vote_share": S2[keep].round(4), "neighbour_forwards": T2[keep].astype(int)})
    return acc, inf


# ----------------------------------------------------------------- tables
def build_tables(cc, info, inferred, n_lang, n_city, matcher, seed=42, tz=None):
    """channel_geo (final), city_coverage, language_coverage, validation_sample."""
    cc = cc.copy()
    first = cc.sort_values(["channel_id", "n_cities"]).drop_duplicates("channel_id")
    geo = first[["channel_id", "language", "language_source", "country", "city", "field", "matched_text",
                 "n_cities"]].rename(columns={"field": "evidence", "language_source": "language_origin"})
    geo["method"] = "direct_" + geo.language_origin.map({"channel_language": "channel_language",
                                                         "title_language": "title_language"})
    geo["confidence"] = np.where(geo.n_cities == 1, 1.0, round(1.0 / geo.n_cities, 3))
    if inferred is not None and len(inferred):
        inf = inferred.assign(language=inferred.channel_id.map(lambda c: info.get(int(c), ("", ""))[0]),
                              language_origin=inferred.channel_id.map(lambda c: info.get(int(c), ("", ""))[1]),
                              evidence="neighbour vote", matched_text="", n_cities=1, method="neighbours",
                              confidence=inferred.vote_share)
        geo = pd.concat([geo, inf[geo.columns.tolist()]], ignore_index=True)
    if tz is not None:
        geo["city_utc_offset"] = [offset_of(a, b) for a, b in zip(geo.country, geo.city)]
        geo["tz_estimated_offset"] = geo.channel_id.map(lambda c: tz.get(int(c), (np.nan, np.nan))[0])
        geo["tz_score"] = geo.channel_id.map(lambda c: tz.get(int(c), (np.nan, np.nan))[1]).round(3)
        d = circ_dist(geo.city_utc_offset, geo.tz_estimated_offset)
        geo["tz_consistent"] = np.where(np.isnan(d), np.nan, (d <= 2).astype(float))
    cov = (geo.groupby(["language", "country", "city", "method"]).channel_id.nunique().rename("n_channels")
           .reset_index().sort_values("n_channels", ascending=False).reset_index(drop=True))
    tot = cov.groupby(["language", "country", "city"], as_index=False).n_channels.sum()
    lc = pd.DataFrame({"language": sorted(n_lang, key=lambda k: -n_lang[k])})
    lc["n_channels"] = lc.language.map(n_lang)
    by_lang = geo.groupby("language").channel_id.nunique()
    lc["n_with_city"] = lc.language.map(by_lang).fillna(0).astype(int)
    lc["share_with_city"] = (lc.n_with_city / lc.n_channels).round(4)
    lc["in_gazetteer"] = lc.language.isin(matcher.languages())
    parts = []
    for method, g in geo[geo.n_cities == 1].groupby("method"):
        parts.append(g.sample(min(70, len(g)), random_state=seed))
    sample = pd.concat(parts) if parts else geo.head(0)
    titles = cc.drop_duplicates("channel_id").set_index("channel_id").title
    sample = sample.assign(title=sample.channel_id.map(titles).fillna(""))
    sample = sample[["channel_id", "method", "language", "city", "evidence", "matched_text", "confidence", "title"]].copy()
    sample["correct"] = ""
    return geo, cov, lc, sample


def write_table(out: Path, name: str, df: pd.DataFrame) -> None:
    d = out / name
    d.mkdir(parents=True, exist_ok=True)
    df.to_csv(d / f"{name}.csv", index=False)


def charts(figdir: Path, cov: pd.DataFrame, lc: pd.DataFrame, summary: pd.DataFrame) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    figdir.mkdir(parents=True, exist_ok=True)
    top = lc[lc.in_gazetteer].head(25).iloc[::-1]
    if len(top):
        fig, ax = plt.subplots(figsize=(8, 0.35 * len(top) + 1.5))
        ax.barh(top.language, top.share_with_city * 100, color="#4c78a8")
        ax.set_xlabel("% of channels with a city (any method)")
        ax.set_title("City coverage by language (25 largest languages with a gazetteer)")
        fig.tight_layout(); fig.savefig(figdir / "city_coverage_by_language.png", dpi=150); plt.close(fig)
    c = cov.groupby(["city", "language"], as_index=False).n_channels.sum().sort_values("n_channels", ascending=False).head(30).iloc[::-1]
    if len(c):
        fig, ax = plt.subplots(figsize=(8, 0.32 * len(c) + 1.5))
        ax.barh([f"{a} ({b})" for a, b in zip(c.city, c.language)], c.n_channels, color="#e45756")
        ax.set_xlabel("channels"); ax.set_title("30 cities with the most channels")
        fig.tight_layout(); fig.savefig(figdir / "top_cities.png", dpi=150); plt.close(fig)
    m = cov.groupby("method").n_channels.sum()
    if len(m):
        fig, ax = plt.subplots(figsize=(7, 3))
        ax.barh(m.index, m.values, color="#54a24b")
        ax.set_xlabel("channels with a city"); ax.set_title("Channels with a city, by method")
        fig.tight_layout(); fig.savefig(figdir / "coverage_by_method.png", dpi=150); plt.close(fig)


README = """# Theme 4, step 1 - city of each channel

Methods (field `method` in channel_geo)
- direct_channel_language: a city of the channel's language (Channel_Language.csv) is named in its
  title, then description, then username. The first field with a match decides.
- direct_title_language: same search, but with the language the title is written in (script and
  distinctive letters), for channels without a language or with nothing found in their own language.
- neighbours: city taken from the forwarding partners (weighted vote on the forward graph, restricted
  to the countries of the channel's language when known). Accuracy: see propagation_accuracy.

Tables
- channel_geo: final table, one row per channel with a city; `confidence` is 1 for a single direct
  match, 1/n when n cities were found, and the vote share for neighbours.
- channel_city: direct matches, one row per (channel, city). channel_city_inferred: neighbour votes.
- city_coverage, language_coverage (share of channels with a city per language), geo_summary.
- validation_sample: up to 70 random single-city channels per method, to check by hand
  (fill `correct` with 1/0; precision of a method = mean of `correct`).

Timezone step (optional, only if the hours of Temporal_Channel_Metadata.csv are UTC)
- timezone_check: pooled daily peak per city; the file is UTC if the peak moves with the city's UTC offset.
  If the verdict is not UTC (local time, or not enough cities with different offsets) the whole step is skipped.
- When UTC: each channel gets an estimated UTC offset (calibrated on channels with a known city); channel_geo
  shows `tz_consistent` (city offset within 2 h of the estimate) - an independent check of the city; and the
  neighbour vote only considers cities in the channel's time zone (propagation_accuracy compares both variants).
  City offsets are standard time (no daylight saving), so +/-1 h of noise is normal.

Limits: a channel whose text names no city and has no labelled neighbour gets no city; a city name can be a
common word or a person; the language written in the title may differ from the channel's audience;
multi-country languages (en, es, pt, fr, ar) get cities from several countries.
"""


def run(args) -> dict:
    matcher = Matcher(load_gazetteer(args.gazetteer))
    langs = load_languages(args.languages)
    rows_out, n_lang, n_city, stats, info = assign_cities(args.metadata, langs, matcher, not args.no_text_language)
    cc = pd.DataFrame(rows_out, columns=["channel_id", "language", "language_source", "country", "city", "field",
                                         "matched_text", "n_cities", "title"])
    single = cc[cc.n_cities == 1].drop_duplicates("channel_id")
    # ---- step 0: are the hours of Temporal_Channel_Metadata UTC? If not (or unclear), the timezone step is skipped
    tz, tz_table, tz_verdict, tz_detail = None, None, "not run", {}
    if args.timezone_mode != "off" and args.temporal and Path(args.temporal).is_file() and len(single):
        tids, P = load_temporal(args.temporal, args.min_posts)
        tz_table, tz_verdict, tz_detail = timezone_check(single, tids, P)
        if args.timezone_mode == "utc":
            tz_verdict = "UTC"                                  # forced by the user
        if tz_verdict == "UTC":
            tz = estimate_offsets(single, tids, P)
            tz = tz or None
        print(f"timezone check: {tz_verdict} {tz_detail}" + ("" if tz else "  -> timezone step skipped"))
    acc, inferred = None, None
    if args.gold and len(cc):
        from community_detection_v2 import build_net, load_edges
        net = build_net(load_edges(args.gold), 1)
        labels = dict(zip(single.channel_id.astype(int), zip(single.country, single.city)))
        lang_of = {c: v[0] for c, v in info.items()}
        acc, inferred = propagate(net, labels, lang_of, matcher, args.min_class, args.min_vote)
        if acc is not None:
            acc.insert(0, "variant", "language only")
        if tz is not None and acc is not None:
            acc_tz, inferred = propagate(net, labels, lang_of, matcher, args.min_class, args.min_vote,
                                         tz=tz, tz_tol=args.tz_tol)
            acc_tz.insert(0, "variant", "language + timezone")
            acc = pd.concat([acc, acc_tz], ignore_index=True)
    geo, cov, lc, sample = build_tables(cc, info, inferred, n_lang, n_city, matcher, tz=tz)
    rows_s = [
        ("metadata channels", stats.get("metadata_rows", 0)),
        ("with a language in Channel_Language.csv", stats.get("with_language", 0)),
        ("language found from the title only", stats.get("language_from_title", 0)),
        ("direct city (channel language)", stats.get("direct_channel_language", 0)),
        ("direct city (title language)", stats.get("direct_title_language", 0)),
        ("city from neighbours", 0 if inferred is None else len(inferred)),
        ("channels with a city, any method", geo.channel_id.nunique()),
    ]
    if tz is not None:
        c = geo.dropna(subset=["tz_consistent"])
        rows_s += [("channels with a timezone estimate and a city", len(c)),
                   ("... of which city and timezone agree (within 2 h)", int(c.tz_consistent.sum()))]
    summary = pd.DataFrame(rows_s, columns=["metric", "value"])
    summary["share_of_metadata_channels"] = (summary.value / max(stats.get("metadata_rows", 1), 1)).round(4)
    out = Path(args.out)
    tables = [("channel_geo", geo), ("channel_city", cc), ("city_coverage", cov), ("language_coverage", lc),
              ("geo_summary", summary), ("validation_sample", sample)]
    if inferred is not None:
        tables += [("channel_city_inferred", inferred), ("propagation_accuracy", acc)]
    if tz_table is not None:
        tables.append(("timezone_check", tz_table.assign(verdict=tz_verdict)))
    for name, df in tables:
        write_table(out, name, df)
    (out / "README.md").write_text(README, encoding="utf-8")
    charts(Path(args.figdir), cov, lc, summary)
    return {"stats": dict(stats), "geo": geo, "coverage": cov, "languages": lc, "summary": summary,
            "accuracy": acc, "inferred": inferred, "tz": tz, "tz_verdict": tz_verdict, "tz_table": tz_table}


def export_gazetteer(path: str) -> None:
    pd.DataFrame(rows(), columns=["lang", "country", "city", "aliases"]).to_csv(path, index=False)
    print(f"gazetteer written to {path}")


# ----------------------------------------------------------------- self-test
def selftest() -> None:
    m = Matcher(rows())
    assert m.find("ru", norm("Новости Москвы"))[0][0] == "Moscow"
    assert m.find("ru", norm("Самарканд сегодня")) == []                    # not Samara
    assert {c for c, _, _ in m.find("ru", norm("Питер и Москва"))} == {"Saint Petersburg", "Moscow"}
    assert m.find("ru", norm("spb_news"))[0][0] == "Saint Petersburg"
    assert m.find("tr", norm("İstanbul'da bugün"))[0][0] == "Istanbul"
    assert m.find("zh-cn", norm("北京新闻"))[0][0] == "Beijing"
    assert m.find("ar", norm("أخبار أبوظبي"))[0][0] == "Abu Dhabi"
    assert m.find("de", norm("Köln aktuell"))[0][0] == "Cologne"
    d = detect_text_language
    assert d("Новости Казани") == "ru" and d("Київ сьогодні") == "uk" and d("Ақпарат Алматы") == "kk"
    assert d("اخبار تهران پیام") == "fa" and d("أخبار القاهرة") == "ar" and d("خبریں لاہور ٹی وی") == "ur"
    assert d("北京新闻") == "zh-cn" and d("東京ニュース") == "ja" and d("서울 뉴스") == "ko"
    assert d("İstanbul haberleri ğ") == "tr" and d("Madrid noticias ñ") == "es" and d("Berlin Nachrichten ü") == "de"
    assert d("The daily news") == "en" and d("xyz") is None and d("12 34") is None
    t = Path(tempfile.mkdtemp())
    meta = {1: "Новости Москвы", 2: "Kyiv Daily", 3: "Канал про жизнь", 4: "Moscow news", 5: "No city here",
            6: "北京新闻", 7: "Новости Казани", 8: "Новости Москвы 2"}
    for i in range(20, 100):                                           # 30 Moscow, 10 plain, 30 St Petersburg, 10 plain
        meta[i] = ("Москва сегодня" if i < 50 else f"Канал {i}") if i < 60 else ("Питер сегодня" if i < 90 else f"Канал {i}")
    with open(t / "meta.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["id", "updated_utc", "data"])
        for cid, title in meta.items():
            w.writerow([cid, 0, json.dumps({"title": title}, ensure_ascii=False)])
    langs = {1: "ru", 2: "uk", 3: "ru", 4: "uk", 6: "zh-cn", 8: "ru", **{i: "ru" for i in range(20, 100)}}
    pd.DataFrame({"File Names": [f"{i}.jsonl" for i in langs], "detected_language": list(langs.values())}).to_csv(
        t / "lang.csv", sep="\t")
    (t / "gold" / "edges_monthly_csv").mkdir(parents=True)
    rng = np.random.default_rng(0)
    ed = [(int(a), int(b), "2024-01", 5) for a in range(50, 60) for b in rng.choice(np.arange(20, 50), 4, replace=False)]
    ed += [(int(a), int(b), "2024-01", 5) for a in range(90, 100) for b in rng.choice(np.arange(60, 90), 4, replace=False)]
    ed += [(i, i + 1, "2024-01", 3) for i in range(20, 49)] + [(i, i + 1, "2024-01", 3) for i in range(60, 89)]   # chains inside each city
    ed.append((3, 20, "2024-01", 9))
    pd.DataFrame(ed, columns=["origin_channel", "dest_channel", "month", "n_forwards"]).to_csv(
        t / "gold" / "edges_monthly_csv" / "p.csv", index=False)
    args = argparse.Namespace(metadata=str(t / "meta.csv"), languages=str(t / "lang.csv"), gazetteer=None,
                              gold=str(t / "gold"), out=str(t / "out"), figdir=str(t / "fig"),
                              min_class=5, min_vote=0.6, no_text_language=False, temporal=None,
                              timezone_mode="off", min_posts=100, tz_tol=2.0)
    res = run(args)
    geo = res["geo"].set_index("channel_id")
    assert geo.loc[1, "city"] == "Moscow" and geo.loc[1, "method"] == "direct_channel_language"
    assert geo.loc[2, "city"] == "Kyiv"
    assert geo.loc[4, "city"] != "Moscow" if 4 in geo.index else True        # Moscow is not a Ukrainian-language city
    assert 5 not in geo.index
    assert geo.loc[7, "city"] == "Kazan" and geo.loc[7, "method"] == "direct_title_language"   # no known language
    assert geo.loc[6, "city"] == "Beijing"
    nb_m, nb_p = geo.reindex(range(50, 60)), geo.reindex(range(90, 100))
    assert (nb_m.method == "neighbours").all() and (nb_m.city == "Moscow").all()
    assert (nb_p.method == "neighbours").all() and (nb_p.city == "Saint Petersburg").all()
    assert geo.loc[3, "method"] == "neighbours" and geo.loc[3, "city"] == "Moscow"
    acc = res["accuracy"]
    assert acc is not None and acc.iloc[-1]["accuracy"] == 1.0
    for name in ("channel_geo", "channel_city", "channel_city_inferred", "propagation_accuracy", "city_coverage",
                 "language_coverage", "geo_summary", "validation_sample"):
        assert (t / "out" / name / f"{name}.csv").exists(), name
    for png in ("city_coverage_by_language", "top_cities", "coverage_by_method"):
        assert (t / "fig" / f"{png}.png").exists(), png
    selftest_timezone()
    print("selftest OK")


def _profiles(offsets: dict[int, float], utc: bool, seed: int = 0) -> pd.DataFrame:
    """Synthetic 24-hour profiles: activity peaks at 15:00 local time; stored in UTC or in local time."""
    rng = np.random.default_rng(seed)
    h = np.arange(24)
    base = np.exp(-(((h - 15 + 12) % 24 - 12) ** 2) / (2 * 3.0 ** 2)) + 0.05
    rows = []
    for cid, off in offsets.items():
        lam = base / base.sum() * 400
        prof = np.roll(lam, -int(off)) if utc else lam                    # utc[u] = local[(u + off) % 24]
        rows.append([cid] + list(rng.poisson(prof)))
    cols = ["filename"] + [f"{i}-{i + 1} hr" for i in range(24)]
    return pd.DataFrame(rows, columns=cols)


def selftest_timezone() -> None:
    t = Path(tempfile.mkdtemp())
    cities = {"Новости Москвы": 3, "Владивосток новости": 10, "Екатеринбург сегодня": 5}
    meta, langs, offs, edges, grp = {}, {}, {}, [], {}
    cid = 1000
    for title, off in cities.items():
        ids = list(range(cid, cid + 40)); cid += 40
        grp[title] = ids
        for i in ids:
            meta[i], langs[i], offs[i] = title, "ru", off
        edges += [(a, b, "2024-01", 3) for a, b in zip(ids[:-1], ids[1:])]
    U = list(range(5000, 5010)); W = list(range(5100, 5110))              # no city in the title
    msk, vlad = grp["Новости Москвы"], grp["Владивосток новости"]
    for i in U + W:
        meta[i], langs[i] = f"Канал {i}", "ru"
    offs.update({i: 10 for i in U}); offs.update({i: 3 for i in W})
    rng = np.random.default_rng(1)
    for i in U + W:                                                       # each unlabelled channel: 2 Moscow + 2 Vladivostok partners
        for j in list(rng.choice(msk, 2, replace=False)) + list(rng.choice(vlad, 2, replace=False)):
            edges.append((int(i), int(j), "2024-01", 5))
    with open(t / "meta.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["id", "updated_utc", "data"])
        for i, title in meta.items():
            w.writerow([i, 0, json.dumps({"title": title}, ensure_ascii=False)])
    pd.DataFrame({"File Names": [f"{i}.jsonl" for i in langs], "detected_language": list(langs.values())}).to_csv(
        t / "lang.csv", sep="\t")
    (t / "gold" / "edges_monthly_csv").mkdir(parents=True)
    pd.DataFrame(edges, columns=["origin_channel", "dest_channel", "month", "n_forwards"]).to_csv(
        t / "gold" / "edges_monthly_csv" / "p.csv", index=False)

    def go(utc: bool, mode: str = "auto"):
        _profiles(offs, utc).to_csv(t / "temporal.csv", index=False)
        a = argparse.Namespace(metadata=str(t / "meta.csv"), languages=str(t / "lang.csv"), gazetteer=None,
                               gold=str(t / "gold"), out=str(t / f"out_{utc}_{mode}"), figdir=str(t / "fig"),
                               min_class=5, min_vote=0.6, no_text_language=False, temporal=str(t / "temporal.csv"),
                               timezone_mode=mode, min_posts=100, tz_tol=2.0)
        return run(a)

    r = go(utc=True)                                                      # hours are UTC -> timezone step runs
    assert r["tz_verdict"] == "UTC", (r["tz_verdict"], r["tz_table"])
    assert r["tz"] is not None
    assert all(abs(r["tz"][i][0] - 10) <= 1 for i in U) and all(abs(r["tz"][i][0] - 3) <= 1 for i in W)
    geo = r["geo"].set_index("channel_id")
    assert (geo.reindex(U).city == "Vladivostok").all() and (geo.reindex(W).city == "Moscow").all()
    assert geo.loc[msk, "tz_consistent"].mean() > 0.95
    acc = r["accuracy"]
    assert set(acc.variant) == {"language only", "language + timezone"}
    rule = acc[acc.row.str.startswith(">=")].set_index("variant")
    assert rule.loc["language + timezone", "held_out_channels"] >= rule.loc["language only", "held_out_channels"]
    assert (t / f"out_True_auto" / "timezone_check" / "timezone_check.csv").exists()

    r2 = go(utc=False)                                                    # hours are local time -> step skipped
    assert r2["tz_verdict"] == "local" and r2["tz"] is None and "tz_consistent" not in r2["geo"].columns
    assert "city from neighbours" in set(r2["summary"].metric)

    r3 = go(utc=True, mode="off")                                         # switched off by the user
    assert r3["tz"] is None and r3["tz_table"] is None
    print("timezone selftest OK")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--metadata", default="telescope_files/Source_Channel_Metadata.csv")
    ap.add_argument("--languages", default="telescope_files/Channel_Language.csv")
    ap.add_argument("--gold", default=None, help="gold folder; enables the neighbour vote")
    ap.add_argument("--gazetteer", default=None, help="CSV (lang,country,city,aliases) replacing the built-in list")
    ap.add_argument("--export-gazetteer", default=None, help="write the built-in gazetteer to this CSV and exit")
    ap.add_argument("--no-text-language", action="store_true", help="do not use the language the title is written in")
    ap.add_argument("--temporal", default="telescope_files/Temporal_Channel_Metadata.csv",
                    help="24-hour activity per channel; used only if its hours are UTC")
    ap.add_argument("--timezone-mode", choices=["auto", "utc", "off"], default="auto",
                    help="auto: use the timezone only if the check says UTC; utc: force; off: skip")
    ap.add_argument("--min-posts", type=int, default=100, help="min posts for a channel profile to be used")
    ap.add_argument("--tz-tol", type=float, default=2.0, help="hours of tolerance between city and estimated offset")
    ap.add_argument("--min-class", type=int, default=30, help="min labelled channels for a city to take part in the vote")
    ap.add_argument("--min-vote", type=float, default=0.6, help="min vote share to assign a city from neighbours")
    ap.add_argument("--out", default="bigdata_pipeline/analysis/geo")
    ap.add_argument("--figdir", default="bigdata_pipeline/analysis/figures/geo")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        selftest(); return
    if args.export_gazetteer:
        export_gazetteer(args.export_gazetteer); return
    res = run(args)
    print(res["summary"].to_string(index=False))
    if res["tz_table"] is not None:
        print(f"\ntimezone check verdict: {res['tz_verdict']}")
    if res["accuracy"] is not None:
        print("\nneighbour vote, accuracy on hidden cities:\n" + res["accuracy"].to_string(index=False))
    print("\ntop cities:\n" + res["coverage"].groupby(["city", "language"], as_index=False).n_channels.sum()
          .sort_values("n_channels", ascending=False).head(15).to_string(index=False))
    print(f"\ntables in {args.out}, figures in {args.figdir}")


if __name__ == "__main__":
    main()