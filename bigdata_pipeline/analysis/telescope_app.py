"""TeleScope v2 - Streamlit viewer for the analysis results (themes 1 to 3).

Read-only: the app reads the CSV / PNG / README files already written in
bigdata_pipeline/analysis/ and recomputes nothing.

Run (from the project root, venv active):
    pip install streamlit
    streamlit run bigdata_pipeline/analysis/telescope_app.py
Other analysis folder:
    streamlit run bigdata_pipeline/analysis/telescope_app.py -- --analysis path/to/analysis
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

import pandas as pd
import streamlit as st

# ----------------------------------------------------------------- configuration
THEMES = {
    "Thème 1 — Communautés de diffusion": {
        "tables": "communities_v2", "figures": "figures/community_detection",
        "intro": "Leiden (méthode principale) et Infomap (comparaison) sur le graphe de transferts entre canaux, "
                 "avec stabilité, courbe de résolution et évolution annuelle."},
    "Thème 2 — Communautés et langues": {
        "tables": "language_v2", "figures": "figures/language_communities",
        "intro": "Pureté, homophilie, flux entre langues, canaux-ponts, activité et inférence de la langue "
                 "des canaux inconnus."},
    "Thème 3 — Traçabilité jusqu'à la source": {
        "tables": "tracing", "figures": "figures/traceability",
        "intro": "Niveaux de traçabilité A/B/C/D, vérification de la source dans le corpus, tailles de chaînes, "
                 "délais et concentration des sources."},
}
# figures checked during the analyses (after deduplication)
PIPELINE_KPI = [
    ("Lignes lues", "208 571 890"), ("Copies supprimées", "22 602 242 (10,8 %)"),
    ("Messages distincts", "185 969 648"), ("Transferts détectés", "33 010 845"),
    ("Relais distincts", "31 705 915"), ("Canaux (nœuds)", "267 518"),
    ("Paires orientées", "2 733 450"), ("Lots traités", "25"),
]
MAX_ROWS_SHOWN = 2000
TIME_HINTS = re.compile(r"year|annee|month|mois|date|period|quarter", re.I)
ID_HINTS = re.compile(r"(^id$|_id$|^channel|^source$|^name$|^file|community|cluster|^rank|^index)", re.I)


# ----------------------------------------------------------------- pure functions
def discover_tables(root: Path) -> dict[str, Path]:
    """Find every CSV under `root`, at any depth (e.g. <name>/<name>.csv or a flat layout).

    The key is the path relative to `root` without the extension, shortened to the
    file stem when it is unique.
    """
    if not root.is_dir():
        return {}
    paths = sorted(root.rglob("*.csv"))
    stems = [p.stem for p in paths]
    found: dict[str, Path] = {}
    for p, stem in zip(paths, stems):
        key = stem if stems.count(stem) == 1 else str(p.relative_to(root).with_suffix(""))
        found[key] = p
    return found


def guess_xy(df: pd.DataFrame) -> tuple[str | None, str | None]:
    """Reasonable default x and y columns for a chart."""
    cols = list(df.columns)
    nums = [c for c in cols if pd.api.types.is_numeric_dtype(df[c])]
    time_cols = [c for c in cols if TIME_HINTS.search(str(c))]
    cats = [c for c in cols if c not in nums]
    x = (time_cols or cats or cols or [None])[0]
    ys = [c for c in nums if c != x and not ID_HINTS.search(str(c))] or [c for c in nums if c != x]
    return x, (ys[0] if ys else None)


def apply_search(df: pd.DataFrame, text: str) -> pd.DataFrame:
    """Keep the rows where any column contains `text` (case-insensitive)."""
    text = text.strip().lower()
    if not text:
        return df
    mask = pd.Series(False, index=df.index)
    for c in df.columns:
        mask |= df[c].astype(str).str.lower().str.contains(text, regex=False, na=False)
    return df[mask]


def prepare_chart(df: pd.DataFrame, x: str, y: str, kind: str, top_n: int) -> pd.DataFrame:
    """Table (index = x, one y column) ready for st.bar_chart / st.line_chart."""
    d = df[[x, y]].dropna()
    if kind == "Barres":
        d = d.sort_values(y, ascending=False).head(top_n)
    else:
        d = d.sort_values(x).head(max(top_n, 5000))
    d = d.groupby(x, sort=False)[y].sum().to_frame()
    return d


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser()
    ap.add_argument("--analysis", default="bigdata_pipeline/analysis")
    args, _ = ap.parse_known_args()
    return args


# ----------------------------------------------------------------- disk access (cached)
@st.cache_data(show_spinner="Lecture du tableau…")
def load_csv(path: str, mtime: float) -> pd.DataFrame:      # mtime invalidates the cache when the file changes
    return pd.read_csv(path, low_memory=False)


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


# ----------------------------------------------------------------- pages
def page_pipeline() -> None:
    st.header("Pipeline Big Data (PySpark)")
    st.write("Traitement par lots de 25 archives de messages Telegram : nettoyage → déduplication → "
             "tables `gold/` (chaînes de relais, arêtes mensuelles, statistiques par canal).")
    for i in range(0, len(PIPELINE_KPI), 4):
        cols = st.columns(4)
        for col, (label, value) in zip(cols, PIPELINE_KPI[i:i + 4]):
            col.metric(label, value)
    st.caption("Les copies supprimées ne diffèrent que par les vues et les transferts "
               "(probablement des re-collectes du même message).")


def table_view(files: dict[str, Path], key: str) -> None:
    name = st.selectbox("Tableau", list(files), key=f"{key}_table")
    path = files[name]
    readme = next((p for p in (path.parent / "README.md", path.with_suffix(".md")) if p.is_file()), None)
    if readme is not None:
        with st.expander("Description des colonnes (README)"):
            st.markdown(read_text(readme))
    df = load_csv(str(path), path.stat().st_mtime)
    st.caption(f"{len(df):,} lignes × {len(df.columns)} colonnes — `{path}`".replace(",", " "))

    c1, c2, c3 = st.columns([3, 2, 1])
    q = c1.text_input("Rechercher (toutes colonnes)", key=f"{key}_q")
    sort_col = c2.selectbox("Trier par", ["—"] + list(df.columns), key=f"{key}_sort")
    desc = c3.checkbox("Décroissant", value=True, key=f"{key}_desc")
    view = apply_search(df, q)
    if sort_col != "—":
        view = view.sort_values(sort_col, ascending=not desc)
    st.write(f"{len(view):,} lignes correspondantes".replace(",", " ")
             + (f" (affichage des {MAX_ROWS_SHOWN})" if len(view) > MAX_ROWS_SHOWN else ""))
    st.dataframe(view.head(MAX_ROWS_SHOWN))
    st.download_button("Télécharger la sélection (CSV)", view.to_csv(index=False).encode("utf-8"),
                       file_name=f"{name}_selection.csv", mime="text/csv", key=f"{key}_dl")

    with st.expander("Graphique interactif de ce tableau"):
        x0, y0 = guess_xy(view)
        if not len(view.columns) or y0 is None:
            st.info("Pas de colonne numérique à représenter dans ce tableau.")
            return
        cols = list(view.columns)
        nums = [c for c in cols if pd.api.types.is_numeric_dtype(view[c])]
        g1, g2, g3, g4 = st.columns(4)
        kind = g1.selectbox("Type", ["Barres", "Courbe"], key=f"{key}_kind",
                            index=1 if x0 and TIME_HINTS.search(str(x0)) else 0)
        x = g2.selectbox("Axe x", cols, index=cols.index(x0) if x0 in cols else 0, key=f"{key}_x")
        y = g3.selectbox("Axe y", nums, index=nums.index(y0) if y0 in nums else 0, key=f"{key}_y")
        top_n = g4.slider("Nombre de barres", 5, 100, 30, key=f"{key}_n")
        data = prepare_chart(view, x, y, kind, top_n)
        if data.empty:
            st.info("Aucune donnée à tracer avec ces colonnes.")
        elif kind == "Barres":
            st.bar_chart(data)
        else:
            st.line_chart(data)


def figures_view(fig_dir: Path) -> None:
    pngs = sorted(fig_dir.glob("*.png")) if fig_dir.is_dir() else []
    if not pngs:
        st.warning(f"Aucun graphe PNG trouvé dans `{fig_dir}`.")
        return
    readme = fig_dir / "README.md"
    if readme.is_file():
        with st.expander("Description des graphes (README)"):
            st.markdown(read_text(readme))
    for p in pngs:
        st.image(str(p), caption=p.name, width=1000)


def page_theme(title: str, analysis: Path) -> None:
    cfg = THEMES[title]
    st.header(title)
    st.write(cfg["intro"])
    tdir, fdir = analysis / cfg["tables"], analysis / cfg["figures"]
    files = discover_tables(tdir)
    key = cfg["tables"]

    info = tdir / "run_info.json"
    if info.is_file():
        with st.expander("Paramètres et résultats du calcul (run_info.json)"):
            st.code(read_text(info), language="json")
    protocol = tdir / "tracing_protocol.md"
    if protocol.is_file():
        with st.expander("Protocole de traçabilité"):
            st.markdown(read_text(protocol))

    tab_tables, tab_figs = st.tabs(["Tableaux", "Graphes (PNG)"])
    with tab_tables:
        if files:
            st.caption(f"{len(files)} tableaux trouvés dans `{tdir}`")
            table_view(files, key)
        else:
            st.warning(f"Aucun fichier CSV trouvé dans `{tdir}`. "
                       "Vérifiez le dossier d'analyse dans la barre latérale ou lancez le script de ce thème.")
    with tab_figs:
        figures_view(fdir)


def main() -> None:
    st.set_page_config(page_title="TeleScope v2", layout="wide")
    args = parse_args()
    st.sidebar.title("TeleScope v2")
    analysis = Path(st.sidebar.text_input("Dossier d'analyse", args.analysis)).expanduser()
    page = st.sidebar.radio("Page", ["Pipeline"] + list(THEMES))
    if not analysis.is_dir() and page != "Pipeline":
        st.error(f"Dossier introuvable : `{analysis}`. Lancez l'application depuis la racine du projet "
                 "ou indiquez le bon chemin dans la barre latérale.")
        return
    if page == "Pipeline":
        page_pipeline()
    else:
        page_theme(page, analysis)


if __name__ == "__main__":
    main()