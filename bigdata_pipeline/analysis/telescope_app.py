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
THEMES = {   # page id -> folders under the analysis directory
    "theme1": {"tables": "communities_v2", "figures": "figures/community_detection"},
    "theme2": {"tables": "language_v2", "figures": "figures/language_communities"},
    "theme3": {"tables": "tracing", "figures": "figures/traceability"},
}
# figures checked during the analyses (after deduplication): label key -> value
PIPELINE_KPI = [
    ("kpi_rows", "208 571 890"), ("kpi_dups", "22 602 242 (10.8 %)"),
    ("kpi_msgs", "185 969 648"), ("kpi_fwd", "33 010 845"),
    ("kpi_relays", "31 705 915"), ("kpi_nodes", "267 518"),
    ("kpi_pairs", "2 733 450"), ("kpi_lots", "25"),
]
MAX_ROWS_SHOWN = 2000
TIME_HINTS = re.compile(r"year|annee|month|mois|date|period|quarter", re.I)
ID_HINTS = re.compile(r"(^id$|_id$|^channel|^source$|^name$|^file|community|cluster|^rank|^index)", re.I)

# ----------------------------------------------------------------- translations
LANGS = {"ru": "Русский", "en": "English", "fr": "Français"}
TEXT = {
    "analysis_dir": {"fr": "Dossier d'analyse", "en": "Analysis folder", "ru": "Папка анализа"},
    "language": {"fr": "Langue", "en": "Language", "ru": "Язык"},
    "page": {"fr": "Page", "en": "Page", "ru": "Страница"},
    "page_pipeline": {"fr": "Pipeline", "en": "Pipeline", "ru": "Конвейер"},
    "theme1_title": {"fr": "Thème 1 — Communautés de diffusion", "en": "Theme 1 — Diffusion communities",
                     "ru": "Тема 1 — Сообщества распространения"},
    "theme2_title": {"fr": "Thème 2 — Communautés et langues", "en": "Theme 2 — Communities and languages",
                     "ru": "Тема 2 — Сообщества и языки"},
    "theme3_title": {"fr": "Thème 3 — Traçabilité jusqu'à la source", "en": "Theme 3 — Traceability to the source",
                     "ru": "Тема 3 — Прослеживаемость до источника"},
    "theme1_intro": {
        "fr": "Leiden (méthode principale) et Infomap (comparaison) sur le graphe de transferts entre canaux, "
              "avec stabilité, courbe de résolution et évolution annuelle.",
        "en": "Leiden (main method) and Infomap (comparison) on the channel-to-channel forwarding graph, "
              "with stability, resolution curve and yearly evolution.",
        "ru": "Leiden (основной метод) и Infomap (для сравнения) на графе пересылок между каналами: "
              "устойчивость, кривая разрешения и динамика по годам."},
    "theme2_intro": {
        "fr": "Pureté, homophilie, flux entre langues, canaux-ponts, activité et inférence de la langue "
              "des canaux inconnus.",
        "en": "Purity, homophily, flows between languages, bridge channels, activity and inference of the "
              "language of unknown channels.",
        "ru": "Чистота, гомофилия, потоки между языками, каналы-мосты, активность и вывод языка "
              "неизвестных каналов."},
    "theme3_intro": {
        "fr": "Niveaux de traçabilité A/B/C/D, vérification de la source dans le corpus, tailles de chaînes, "
              "délais et concentration des sources.",
        "en": "Traceability levels A/B/C/D, source verification in the corpus, chain sizes, delays and "
              "concentration of sources.",
        "ru": "Уровни прослеживаемости A/B/C/D, проверка источника по корпусу, размеры цепочек, "
              "задержки и концентрация источников."},
    "pipeline_header": {"fr": "Pipeline Big Data (PySpark)", "en": "Big Data pipeline (PySpark)",
                        "ru": "Big Data конвейер (PySpark)"},
    "pipeline_text": {
        "fr": "Traitement par lots de 25 archives de messages Telegram : nettoyage → déduplication → "
              "tables `gold/` (chaînes de relais, arêtes mensuelles, statistiques par canal).",
        "en": "Batch processing of 25 archives of Telegram messages: cleaning → deduplication → "
              "`gold/` tables (relay chains, monthly edges, per-channel statistics).",
        "ru": "Пакетная обработка 25 архивов сообщений Telegram: очистка → дедупликация → "
              "таблицы `gold/` (цепочки ретрансляций, месячные рёбра, статистика по каналам)."},
    "pipeline_note": {
        "fr": "Les copies supprimées ne diffèrent que par les vues et les transferts "
              "(probablement des re-collectes du même message).",
        "en": "The removed copies differ only in views and forwards "
              "(probably re-collections of the same message).",
        "ru": "Удалённые копии отличаются только просмотрами и пересылками "
              "(вероятно, повторные сборы того же сообщения)."},
    "kpi_rows": {"fr": "Lignes lues", "en": "Rows read", "ru": "Прочитано строк"},
    "kpi_dups": {"fr": "Copies supprimées", "en": "Copies removed", "ru": "Удалено копий"},
    "kpi_msgs": {"fr": "Messages distincts", "en": "Distinct messages", "ru": "Уникальных сообщений"},
    "kpi_fwd": {"fr": "Transferts détectés", "en": "Forwards detected", "ru": "Найдено пересылок"},
    "kpi_relays": {"fr": "Relais distincts", "en": "Distinct relays", "ru": "Уникальных ретрансляций"},
    "kpi_nodes": {"fr": "Canaux (nœuds)", "en": "Channels (nodes)", "ru": "Каналов (узлов)"},
    "kpi_pairs": {"fr": "Paires orientées", "en": "Directed pairs", "ru": "Ориентированных пар"},
    "kpi_lots": {"fr": "Lots traités", "en": "Batches processed", "ru": "Обработано партий"},
    "table": {"fr": "Tableau", "en": "Table", "ru": "Таблица"},
    "readme_cols": {"fr": "Description des colonnes (README)", "en": "Column description (README)",
                    "ru": "Описание столбцов (README)"},
    "rows_cols": {"fr": "{rows} lignes × {cols} colonnes", "en": "{rows} rows × {cols} columns",
                  "ru": "{rows} строк × {cols} столбцов"},
    "search": {"fr": "Rechercher (toutes colonnes)", "en": "Search (all columns)", "ru": "Поиск (по всем столбцам)"},
    "sort_by": {"fr": "Trier par", "en": "Sort by", "ru": "Сортировать по"},
    "descending": {"fr": "Décroissant", "en": "Descending", "ru": "По убыванию"},
    "matching": {"fr": "{n} lignes correspondantes", "en": "{n} matching rows", "ru": "Найдено строк: {n}"},
    "showing": {"fr": " (affichage des {m})", "en": " (showing the first {m})", "ru": " (показаны первые {m})"},
    "download": {"fr": "Télécharger la sélection (CSV)", "en": "Download the selection (CSV)",
                 "ru": "Скачать выборку (CSV)"},
    "chart_expander": {"fr": "Graphique interactif de ce tableau", "en": "Interactive chart of this table",
                       "ru": "Интерактивный график этой таблицы"},
    "no_numeric": {"fr": "Pas de colonne numérique à représenter dans ce tableau.",
                   "en": "This table has no numeric column to plot.",
                   "ru": "В этой таблице нет числовых столбцов для графика."},
    "chart_type": {"fr": "Type", "en": "Type", "ru": "Тип"},
    "bars": {"fr": "Barres", "en": "Bars", "ru": "Столбцы"},
    "line": {"fr": "Courbe", "en": "Line", "ru": "Линия"},
    "x_axis": {"fr": "Axe x", "en": "x axis", "ru": "Ось x"},
    "y_axis": {"fr": "Axe y", "en": "y axis", "ru": "Ось y"},
    "n_bars": {"fr": "Nombre de barres", "en": "Number of bars", "ru": "Число столбцов"},
    "nothing_to_plot": {"fr": "Aucune donnée à tracer avec ces colonnes.",
                        "en": "No data to plot with these columns.",
                        "ru": "Нет данных для графика с этими столбцами."},
    "no_png": {"fr": "Aucun graphe PNG trouvé dans `{path}`.", "en": "No PNG chart found in `{path}`.",
               "ru": "В `{path}` не найдено PNG-графиков."},
    "readme_figs": {"fr": "Description des graphes (README)", "en": "Chart description (README)",
                    "ru": "Описание графиков (README)"},
    "run_info": {"fr": "Paramètres et résultats du calcul (run_info.json)",
                 "en": "Run parameters and results (run_info.json)",
                 "ru": "Параметры и результаты расчёта (run_info.json)"},
    "protocol": {"fr": "Protocole de traçabilité", "en": "Traceability protocol",
                 "ru": "Протокол прослеживаемости"},
    "tab_tables": {"fr": "Tableaux", "en": "Tables", "ru": "Таблицы"},
    "tab_figs": {"fr": "Graphes (PNG)", "en": "Charts (PNG)", "ru": "Графики (PNG)"},
    "n_tables": {"fr": "{n} tableaux trouvés dans `{path}`", "en": "{n} tables found in `{path}`",
                 "ru": "Найдено таблиц: {n} в `{path}`"},
    "no_csv": {
        "fr": "Aucun fichier CSV trouvé dans `{path}`. Vérifiez le dossier d'analyse dans la barre latérale "
              "ou lancez le script de ce thème.",
        "en": "No CSV file found in `{path}`. Check the analysis folder in the sidebar "
              "or run this theme's script.",
        "ru": "В `{path}` не найдено CSV-файлов. Проверьте папку анализа в боковой панели "
              "или запустите скрипт этой темы."},
    "no_dir": {
        "fr": "Dossier introuvable : `{path}`. Lancez l'application depuis la racine du projet "
              "ou indiquez le bon chemin dans la barre latérale.",
        "en": "Folder not found: `{path}`. Run the app from the project root "
              "or enter the right path in the sidebar.",
        "ru": "Папка не найдена: `{path}`. Запустите приложение из корня проекта "
              "или укажите верный путь в боковой панели."},
    "loading": {"fr": "Lecture du tableau…", "en": "Reading the table…", "ru": "Чтение таблицы…"},
}
LANG = "fr"    # current UI language, set in main()


def tr(key: str, **kw) -> str:
    """Text for `key` in the current UI language."""
    return TEXT[key][LANG].format(**kw) if kw else TEXT[key][LANG]


def fmt_int(n: int) -> str:
    """Integer with a space as thousands separator."""
    return f"{n:,}".replace(",", " ")


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
    if kind == "bars":
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
@st.cache_data(show_spinner=False)
def load_csv(path: str, mtime: float) -> pd.DataFrame:      # mtime invalidates the cache when the file changes
    return pd.read_csv(path, low_memory=False)


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


# ----------------------------------------------------------------- pages
def page_pipeline() -> None:
    st.header(tr("pipeline_header"))
    st.write(tr("pipeline_text"))
    for i in range(0, len(PIPELINE_KPI), 4):
        cols = st.columns(4)
        for col, (label_key, value) in zip(cols, PIPELINE_KPI[i:i + 4]):
            col.metric(tr(label_key), value)
    st.caption(tr("pipeline_note"))


def table_view(files: dict[str, Path], key: str) -> None:
    name = st.selectbox(tr("table"), list(files), key=f"{key}_table")
    path = files[name]
    readme = next((p for p in (path.parent / "README.md", path.with_suffix(".md")) if p.is_file()), None)
    if readme is not None:
        with st.expander(tr("readme_cols")):
            st.markdown(read_text(readme))
    df = load_csv(str(path), path.stat().st_mtime)
    st.caption(tr("rows_cols", rows=fmt_int(len(df)), cols=len(df.columns)) + f" — `{path}`")

    none_label = "—"
    c1, c2, c3 = st.columns([3, 2, 1])
    q = c1.text_input(tr("search"), key=f"{key}_q")
    sort_col = c2.selectbox(tr("sort_by"), [none_label] + list(df.columns), key=f"{key}_sort")
    desc = c3.checkbox(tr("descending"), value=True, key=f"{key}_desc")
    view = apply_search(df, q)
    if sort_col != none_label:
        view = view.sort_values(sort_col, ascending=not desc)
    st.write(tr("matching", n=fmt_int(len(view)))
             + (tr("showing", m=MAX_ROWS_SHOWN) if len(view) > MAX_ROWS_SHOWN else ""))
    st.dataframe(view.head(MAX_ROWS_SHOWN))
    st.download_button(tr("download"), view.to_csv(index=False).encode("utf-8"),
                       file_name=f"{name}_selection.csv", mime="text/csv", key=f"{key}_dl")

    with st.expander(tr("chart_expander")):
        x0, y0 = guess_xy(view)
        if not len(view.columns) or y0 is None:
            st.info(tr("no_numeric"))
            return
        cols = list(view.columns)
        nums = [c for c in cols if pd.api.types.is_numeric_dtype(view[c])]
        g1, g2, g3, g4 = st.columns(4)
        kind = g1.selectbox(tr("chart_type"), ["bars", "line"], key=f"{key}_kind", format_func=tr,
                            index=1 if x0 and TIME_HINTS.search(str(x0)) else 0)
        x = g2.selectbox(tr("x_axis"), cols, index=cols.index(x0) if x0 in cols else 0, key=f"{key}_x")
        y = g3.selectbox(tr("y_axis"), nums, index=nums.index(y0) if y0 in nums else 0, key=f"{key}_y")
        top_n = g4.slider(tr("n_bars"), 5, 100, 30, key=f"{key}_n")
        data = prepare_chart(view, x, y, kind, top_n)
        if data.empty:
            st.info(tr("nothing_to_plot"))
        elif kind == "bars":
            st.bar_chart(data)
        else:
            st.line_chart(data)


def figures_view(fig_dir: Path) -> None:
    pngs = sorted(fig_dir.glob("*.png")) if fig_dir.is_dir() else []
    if not pngs:
        st.warning(tr("no_png", path=fig_dir))
        return
    readme = fig_dir / "README.md"
    if readme.is_file():
        with st.expander(tr("readme_figs")):
            st.markdown(read_text(readme))
    for p in pngs:
        st.image(str(p), caption=p.name, width=1000)


def page_theme(page_id: str, analysis: Path) -> None:
    cfg = THEMES[page_id]
    st.header(tr(f"{page_id}_title"))
    st.write(tr(f"{page_id}_intro"))
    tdir, fdir = analysis / cfg["tables"], analysis / cfg["figures"]
    files = discover_tables(tdir)
    key = cfg["tables"]

    info = tdir / "run_info.json"
    if info.is_file():
        with st.expander(tr("run_info")):
            st.code(read_text(info), language="json")
    protocol = tdir / "tracing_protocol.md"
    if protocol.is_file():
        with st.expander(tr("protocol")):
            st.markdown(read_text(protocol))

    tab_tables, tab_figs = st.tabs([tr("tab_tables"), tr("tab_figs")])
    with tab_tables:
        if files:
            st.caption(tr("n_tables", n=len(files), path=tdir))
            table_view(files, key)
        else:
            st.warning(tr("no_csv", path=tdir))
    with tab_figs:
        figures_view(fdir)


def main() -> None:
    global LANG
    st.set_page_config(page_title="TeleScope v2", layout="wide")
    args = parse_args()
    st.sidebar.title("TeleScope v2")
    LANG = st.sidebar.selectbox("Language / Langue / Язык", list(LANGS), format_func=LANGS.get)
    analysis = Path(st.sidebar.text_input(tr("analysis_dir"), args.analysis)).expanduser()
    page_ids = ["pipeline"] + list(THEMES)
    page = st.sidebar.radio(tr("page"), page_ids,
                            format_func=lambda p: tr("page_pipeline") if p == "pipeline" else tr(f"{p}_title"))
    if not analysis.is_dir() and page != "pipeline":
        st.error(tr("no_dir", path=analysis))
        return
    if page == "pipeline":
        page_pipeline()
    else:
        page_theme(page, analysis)


if __name__ == "__main__":
    main()