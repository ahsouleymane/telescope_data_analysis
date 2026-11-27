#!/usr/bin/env python3
"""Collect everything needed for the report into ONE Word file (tables, figures, logs, code excerpts).
Run from the project root:   python3 collect_report_data.py
Needs:  pip install python-docx pillow   (pyarrow is optional: gives exact Parquet row counts and schemas)
Output: report_data/DONNEES_RAPPORT.docx  (+ .md fallback)
"""
import csv, glob, json, os, platform, re, shutil, subprocess, sys
from pathlib import Path

ROOT = Path.cwd()
AN = ROOT / "bigdata_pipeline" / "analysis"
PF = ROOT / "telescope_pipeline_files"
SRC = ROOT / "bigdata_pipeline"
OUT = ROOT / "report_data"; OUT.mkdir(exist_ok=True)
ROWS_SMALL, ROWS_BIG = 40, 10
BIG = ("communities_", "channel_city", "channel_geo", "channel_language", "coordinated_members", "validation_sample",
       "suspicious_channels", "top_origin_posts", "language_top_channels", "channel_language_votes", "community_profiles", "community_flows")

# theme -> (title, table folders under analysis/, figure folders under analysis/figures/, extra files)
THEMES = [
    ("Thème 1 — Communautés", ["communities_v2"], ["community_detection"]),
    ("Thème 2 — Langues", ["language_v2"], ["language_communities"]),
    ("Thème 3 — Traçabilité", ["tracing"], ["traceability"]),
    ("Thème 4 — Villes et pics d'activité", ["geo_cities", "city_coordinates", "anomalies"], ["geo_cities", "anomalies"]),
    ("Thème 5 — Tendances atypiques", ["suspicious"], ["suspicious"]),
]
# scripts searched for thresholds / rules / parameters
CODE = ["spark/spark_session.py", "spark/job1_clean.py", "spark/job1b_dedup.py", "spark/job2_chains.py", "spark/job3_edges.py",
        "spark/job4_stats.py", "spark/job5_city_daily.py", "spark/job6_suspicious.py", "analysis/community_detection_v2.py",
        "analysis/language_analysis_v2.py", "analysis/source_tracing.py", "analysis/geo_cities_th4-2stp.py",
        "analysis/anomaly_peaks_th4-4stp.py", "analysis/suspicious_trends_th5-1stp.py", "analysis/fast_mirror_channels_th5-2stp.py",
        "analysis/fast_trend_excluding_th5-3stp.py", "analysis/fast_month_drivers_th5-4stp.py", "analysis/review_candidates.py"]
KEY = re.compile(r"quantile|percentile|thresh|window|baseline|rolling|median|\bmad\b|z_?score|min_|MIN_|MAX_|vote|majority|resolution|seed|"
                 r"accuracy|holdout|mask|shuffle\.partitions|master|memory|cores|coalesce|repartition|=\s*0\.\d+|=\s*\d{2,}", re.I)

try:
    import docx
    from docx.shared import Cm, Pt
except ImportError:
    docx = None
try:
    from PIL import Image
except ImportError:
    Image = None
try:
    import pyarrow.parquet as pq
except ImportError:
    pq = None

md, doc = [], (docx.Document() if docx else None)
if doc: doc.styles["Normal"].font.size = Pt(10)

def h(t, lvl=1):
    md.append("\n" + "#" * (lvl or 1) + " " + t + "\n")
    if doc: doc.add_heading(t, lvl)
def para(t):
    md.append(t + "\n")
    if doc: doc.add_paragraph(t)
def mono(t, maxlines=120):
    L = t.splitlines()
    if len(L) > maxlines: L = L[:maxlines] + [f"... ({len(L) - maxlines} lignes de plus)"]
    t = "\n".join(L); md.append("```\n" + t + "\n```\n")
    if doc:
        r = doc.add_paragraph().add_run(t); r.font.name = "Courier New"; r.font.size = Pt(7.5)
def table(head, data):
    md.append("| " + " | ".join(head) + " |\n|" + "---|" * len(head)); md.extend("| " + " | ".join(r) + " |" for r in data); md.append("")
    if doc:
        t = doc.add_table(rows=1, cols=len(head)); t.style = "Table Grid"
        for i, c in enumerate(head): t.rows[0].cells[i].text = c
        for r in data:
            cells = t.add_row().cells
            for i, c in enumerate(r[:len(head)]): cells[i].text = c
        for row in t.rows:
            for c in row.cells:
                for p in c.paragraphs:
                    for run in p.runs: run.font.size = Pt(7)
        doc.add_paragraph()
def image(p: Path):
    if p.stat().st_size > 8_000_000: para(f"[image trop grosse, ignorée : {p}]"); return
    show = p
    if Image:
        try:
            im = Image.open(p)
            if im.width > 1600:
                show = OUT / f"_img_{abs(hash(str(p)))}.png"; im.convert("RGB").resize((1600, int(im.height * 1600 / im.width))).save(show)
        except Exception: show = p
    md.append(f"![{p}]({p})\n")
    if doc:
        try:
            doc.add_picture(str(show), width=Cm(15)); doc.add_paragraph(str(p.relative_to(ROOT))).runs[0].font.size = Pt(8)
        except Exception as e: para(f"[image illisible : {p} ({e})]")

def delim_of(line): return ";" if line.count(";") > line.count(",") else ("\t" if line.count("\t") > line.count(",") else ",")

def show_csv_files(files, name, maxrows):
    """Several part-*.csv files form ONE table: header once, rows counted over all parts."""
    head, body, n = None, [], 0
    for f in files:
        with open(f, newline="", encoding="utf-8", errors="replace") as fh:
            first = fh.readline(); fh.seek(0)
            rd = csv.reader(fh, delimiter=delim_of(first)); hd = next(rd, None)
            if hd is None: continue
            head = head or hd
            for r in rd:
                n += 1
                if len(body) < maxrows: body.append([c[:40].replace("|", "/") for c in r[:14]])
    if head is None: return
    h(f"{name}  ({n} lignes, {len(head)} colonnes)", 3); table([c[:28] for c in head][:14], body)

def show_parquet(d: Path, name):
    if not pq: para(f"[pyarrow absent : {name} non lu]"); return
    files = sorted(d.rglob("*.parquet")) if d.is_dir() else [d]
    if not files: return
    n = sum(pq.ParquetFile(f).metadata.num_rows for f in files)
    schema = pq.ParquetFile(files[0]).schema_arrow
    h(f"{name}  (Parquet, {n} lignes)", 3)
    table(["colonne", "type"], [[f.name, str(f.type)] for f in schema])

def show_table_dir(d: Path, label):
    maxrows = ROWS_BIG if any(k in d.name for k in BIG) else ROWS_SMALL
    csvs = sorted(f for f in d.rglob("*.csv") if not f.name.startswith("."))
    if csvs: show_csv_files(csvs, label, maxrows); return
    if any(d.rglob("*.parquet")): show_parquet(d, label); return
    for f in sorted(d.rglob("*")):
        if f.is_file() and f.suffix in (".json", ".md", ".txt"): show_text(f)

def show_text(f: Path):
    h(str(f.relative_to(ROOT)), 3); mono(f.read_text(encoding="utf-8", errors="replace"), 150)

def show_entry(p: Path):
    rel = str(p.relative_to(ROOT))
    if p.is_dir(): show_table_dir(p, rel)
    elif p.suffix == ".csv": show_csv_files([p], rel, ROWS_SMALL)
    elif p.suffix in (".json", ".md", ".txt"): show_text(p)
    elif p.suffix == ".png": image(p)

def sh(cmd):
    try: return subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60).stdout.strip()
    except Exception as e: return f"({e})"

# ---------------------------------------------------------------- 0. header, machine, environment
h("Données collectées pour le rapport", 0)
para("Généré automatiquement par collect_report_data.py : environnement, journaux de temps, volumes, tables de chaque thème (premières lignes), figures, extraits de code.")
h("Machine et environnement", 1)
info = [f"date: {sh('date -Is')}", f"os: {platform.platform()}", f"cpu: {sh('grep -m1 \"model name\" /proc/cpuinfo | cut -d: -f2')} ; coeurs: {os.cpu_count()}",
        f"ram: {sh('free -h | awk \"/Mem/{print $2}\"')}", f"disque projet: {sh('df -h . | awk \"NR==2{print $2\\\" total, \\\"$4\\\" libres\\\"}\"')}",
        f"python: {sys.version.split()[0]}", f"java: {sh('java -version 2>&1 | grep -v JAVA_TOOL | head -1')}", f"docker: {sh('docker --version')}",
        f"pyspark: {sh('python3 -c \"import pyspark;print(pyspark.__version__)\" 2>&1 | tail -1')}"]
for f in (".env", "ENVIRONMENT.txt"):
    if (ROOT / f).exists(): info += [f"---- {f} ----"] + [l for l in (ROOT / f).read_text(errors="replace").splitlines() if not re.search("PASS|TOKEN|SECRET|KEY", l)]
mono("\n".join(info))

# ---------------------------------------------------------------- 1. pipeline: volumes, logs, gold schemas
h("Pipeline : volumes et journaux (temps d'exécution)", 1)
for name in ("clean_log.csv", "clean_trial_log.csv", "dedup_log.csv", "dedup_report.csv"):
    if (PF / name).exists(): show_csv_files([PF / name], f"telescope_pipeline_files/{name}", 80)
sizes = []
for d in sorted(PF.glob("*")) if PF.exists() else []:
    if d.is_dir():
        for sub in [d] + sorted(x for x in d.iterdir() if x.is_dir())[:60]:
            sizes.append(f"{sub.relative_to(ROOT)}  {sh(f'du -sh \"{sub}\" | cut -f1')}")
    elif d.is_file(): sizes.append(f"{d.relative_to(ROOT)}  {d.stat().st_size/1e6:.1f} MB")
h("Tailles des dossiers de données", 2); mono("\n".join(sizes) or "(rien)", 250)
src = ROOT / "telescope_files"
if src.exists():
    h("Fichiers sources (jeu de données d'origine)", 2)
    mono("\n".join(f"{f.relative_to(ROOT)}  {f.stat().st_size/1e6:.1f} MB" for f in sorted(src.glob("*.csv"))) or "(rien)")
h("Tables gold et données nettoyées : schéma et nombre de lignes (Parquet)", 2)
for d in [PF / "clean", PF / "clean_dedup"] + sorted((PF / "gold").glob("*")):
    if d.is_dir() and any(d.rglob("*.parquet")): show_parquet(d, str(d.relative_to(ROOT)))
for d in sorted((PF / "gold").glob("*_csv")): show_table_dir(d, str(d.relative_to(ROOT)))

# ---------------------------------------------------------------- 2. themes
for title, tables, figs in THEMES:
    h(title, 1)
    for t in tables:
        base = AN / t
        if not base.exists(): para(f"[dossier absent : {base}]"); continue
        h(f"Tables : analysis/{t}", 2)
        for p in sorted(base.iterdir()):
            if not p.name.startswith("."): show_entry(p)
    for fg in figs:
        fd = AN / "figures" / fg
        if fd.exists():
            h(f"Figures : analysis/figures/{fg}", 2)
            for p in sorted(fd.rglob("*.png")): image(p)
        else: para(f"[dossier de figures absent : {fd}]")

# ---------------------------------------------------------------- 2b. safety net: any figure / map not yet shown
shown = {str(p) for p in OUT.parent.rglob("*.png")} if False else set()
h("Cartes et fichiers de figures non rattachés ci-dessus", 1)
done_dirs = [AN / "figures" / f for t in THEMES for f in t[2]]
extra_png = [p for p in AN.rglob("*.png") if not any(d in p.parents for d in done_dirs)]
for p in sorted(extra_png): image(p)
other = [p for p in (AN / "figures").rglob("*") if p.is_file() and p.suffix.lower() in (".html", ".svg", ".pdf", ".gexf", ".jpg", ".jpeg")] if (AN / "figures").exists() else []
other += [p for p in AN.rglob("*") if p.is_file() and p.suffix.lower() in (".html", ".svg", ".jpg", ".jpeg") and p not in other]
mono("\n".join(f"{p.relative_to(ROOT)}  {p.stat().st_size/1e6:.1f} MB" for p in sorted(set(other))) or "(aucun fichier HTML/SVG/JPG)")

# ---------------------------------------------------------------- 3. code excerpts (rules, thresholds, parameters)
h("Extraits de code : seuils, règles, paramètres", 1)
for rel in CODE:
    f = next(iter(SRC.rglob(Path(rel).name)), None)
    if not f: para(f"[script introuvable : {rel}]"); continue
    lines = f.read_text(encoding="utf-8", errors="replace").splitlines()
    hits = [f"{i+1}: {l.rstrip()[:160]}" for i, l in enumerate(lines) if KEY.search(l)]
    h(str(f.relative_to(ROOT)), 3); mono("\n".join(hits[:70]) or "(aucune ligne repérée)", 70)

# ---------------------------------------------------------------- 4. other logs anywhere in the project
logs = [p for p in ROOT.rglob("*.log") if not any(x in p.parts for x in (".git", ".venv", "venv", "node_modules")) and p.stat().st_size < 5e6]
if logs:
    h("Autres journaux (lignes de durée)", 1)
    for p in sorted(logs)[:30]:
        ls = [l for l in p.read_text(errors="replace").splitlines() if re.search(r"elapsed|seconds|duration|took|finished|done in|\b\d+(\.\d+)? ?(s|sec|min)\b", l, re.I)]
        h(str(p.relative_to(ROOT)), 3); mono("\n".join(ls[-40:]) or "(rien)", 40)

(OUT / "DONNEES_RAPPORT.md").write_text("\n".join(md), encoding="utf-8")
if doc:
    doc.save(OUT / "DONNEES_RAPPORT.docx"); print("OK -> report_data/DONNEES_RAPPORT.docx")
else:
    print("python-docx absent : pip install python-docx puis relancer (ou pandoc report_data/DONNEES_RAPPORT.md -o report_data/DONNEES_RAPPORT.docx)")
for f in OUT.glob("_img_*.png"): f.unlink()