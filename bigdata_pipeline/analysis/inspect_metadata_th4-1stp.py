"""Inspect Source_Channel_Metadata.csv: which keys exist and which look like a location.
Usage: python3 inspect_metadata.py telescope_files/Source_Channel_Metadata.csv [max_rows]"""
import csv, json, sys, re
from collections import Counter
csv.field_size_limit(10**9)
path = sys.argv[1]; limit = int(sys.argv[2]) if len(sys.argv) > 2 else 100000
GEO = re.compile(r"geo|loc|city|town|address|country|lat|lon|place|region|timezone|tz", re.I)
top, nested, ex, n, bad = Counter(), Counter(), {}, 0, 0
def walk(prefix, v, depth=0):
    if isinstance(v, dict) and depth < 3:
        for k, x in v.items():
            p = f"{prefix}.{k}" if prefix else k
            nested[p] += 1
            walk(p, x, depth + 1)
    elif prefix and GEO.search(prefix.split(".")[-1]) and v not in (None, "", [], {}):
        ex.setdefault(prefix, [])
        if len(ex[prefix]) < 4: ex[prefix].append(str(v)[:120])
with open(path, newline="", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        n += 1
        if n > limit: n -= 1; break
        try: d = json.loads(row["data"])
        except Exception: bad += 1; continue
        walk("", d)
print(f"lignes lues: {n}  json invalides: {bad}\n")
print("== cles (part des canaux, profondeur<=3) ==")
for k, c in sorted(nested.items(), key=lambda x: -x[1]):
    print(f"{c/max(n-bad,1):6.1%}  {k}")
print("\n== cles ressemblant a un lieu, avec exemples non vides ==")
for k, v in ex.items(): print(k, "->", v)
if not ex: print("aucune valeur non vide")