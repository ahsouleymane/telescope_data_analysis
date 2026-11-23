"""TeleScope v2 - Streamlit viewer and general report of the analysis (themes 1 to 5).

Read-only: the app reads the CSV / PNG / README files already written in
bigdata_pipeline/analysis/ and the Parquet datasets of telescope_pipeline_files/, and recomputes nothing.
Every figure shown is read from those files; nothing is typed by hand.

Run (from the project root, venv active):
    pip install streamlit
    streamlit run bigdata_pipeline/analysis/app/telescope_app.py
Other analysis folder:
    streamlit run bigdata_pipeline/analysis/app/telescope_app.py -- --analysis path/to/analysis --data path/to/pipeline_files
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from telescope_captions import HEADLINES, describe, generic_caption, title_of
from telescope_catalog import (FORMULAS, GLOBAL_LIMITS, LEVEL_NAMES, flagged_channels, PARQUET_INFO, REFERENCES, TABLE_INFO, THEME_TEXT, describe_parquet, describe_table,
                               discover_parquets, fmt_bytes, parquet_info, parquet_preview)

# ----------------------------------------------------------------- configuration
THEMES = {   # page id -> folders under the analysis directory (fixed layout, no search) and Parquet datasets used
    "theme1": {"tables": ["communities_v2"], "figures": ["figures/community_detection"],
               "parquets": ["edges_monthly", "channel_stats"]},
    "theme2": {"tables": ["language_v2"], "figures": ["figures/language_communities"],
               "parquets": ["channel_stats", "edges_monthly"]},
    "theme3": {"tables": ["tracing"], "figures": ["figures/traceability"], "parquets": ["chains"]},
    "theme4": {"tables": ["geo", "anomalies"], "figures": ["figures/geo", "figures/anomalies"],
               "maps": "figures/anomalies", "parquets": ["city_daily", "city_hourly"]},
    "theme5": {"tables": ["suspicious"], "figures": ["figures/suspicious"],
               "parquets": ["channel_behavior", "channel_hours", "coordinated_pairs", "cascades",
                            "forward_speed_monthly", "chains"]},
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
    "theme5_title": {"fr": "Thème 5 — Tendances suspectes de diffusion", "en": "Theme 5 — Suspicious broadcasting trends",
                     "ru": "Тема 5 — Подозрительные тенденции распространения"},
    "theme5_intro": {
        "fr": "Comportements de diffusion atypiques : relais instantanés, source unique, groupes de chaînes coordonnées, "
              "et hausse des relais rapides. Ces mesures décrivent des comportements, pas des intentions.",
        "en": "Atypical broadcasting behaviour: instant relays, single source, coordinated groups of channels, "
              "and the rise of fast relays. These measures describe behaviour, not intent.",
        "ru": "Нетипичное поведение распространения: мгновенные пересылки, один источник, координированные группы каналов "
              "и рост быстрых пересылок. Эти меры описывают поведение, а не намерения."},
    "page_report": {"fr": "Rapport général", "en": "General report", "ru": "Общий отчёт"},
    "page_catalog": {"fr": "Catalogue des fichiers", "en": "File catalogue", "ru": "Каталог файлов"},
    "report_title": {"fr": "TeleScope v2 — Rapport général", "en": "TeleScope v2 — General report",
                     "ru": "TeleScope v2 — Общий отчёт"},
    "report_intro": {
        "fr": "Cette application est le rapport du projet : elle présente, thème par thème, ce qui a été cherché, comment, "
              "ce qui en ressort (chiffres lus dans les fichiers produits) et jusqu'où on peut s'y fier. "
              "Chaque graphe, chaque carte, chaque tableau CSV et chaque jeu de données Parquet est décrit.",
        "en": "This application is the project report: for each theme it shows what was looked for, how, what comes out of it "
              "(figures read from the files produced) and how far it can be trusted. "
              "Every chart, map, CSV table and Parquet dataset is described.",
        "ru": "Это приложение — отчёт по проекту: по каждой теме показано, что искали, как, что получилось "
              "(цифры читаются из созданных файлов) и насколько этому можно доверять. "
              "Описан каждый график, карта, CSV-таблица и набор данных Parquet."},
    "report_howto": {
        "fr": "Chaque page thème a cinq onglets : **Synthèse** (objectif, méthode, résultats chiffrés, limites), **Graphes**, "
              "**Tableaux**, **Cartes** (thème 4) et **Fichiers** (pourquoi chaque fichier existe et ce qu'il contient).",
        "en": "Each theme page has five tabs: **Summary** (goal, method, figures, limits), **Charts**, **Tables**, "
              "**Maps** (theme 4) and **Files** (why each file exists and what it holds).",
        "ru": "На странице каждой темы пять вкладок: **Сводка** (цель, метод, цифры, ограничения), **Графики**, "
              "**Таблицы**, **Карты** (тема 4) и **Файлы** (зачем создан каждый файл и что в нём)."},
    "tab_summary": {"fr": "Synthèse", "en": "Summary", "ru": "Сводка"},
    "tab_files": {"fr": "Fichiers", "en": "Files", "ru": "Файлы"},
    "formulas": {"fr": "Formules et explications", "en": "Formulas and explanations", "ru": "Формулы и пояснения"},
    "formulas_note": {"fr": "Les valeurs numériques citées (seuils, fenêtres) sont les valeurs par défaut des scripts ; "
                            "celles réellement utilisées figurent dans les tableaux de résultats.",
                      "en": "The numerical values quoted (thresholds, windows) are the scripts' defaults; "
                            "the ones really used are in the result tables.",
                      "ru": "Приведённые числа (пороги, окна) — значения скриптов по умолчанию; "
                            "реально использованные указаны в таблицах результатов."},
    "flagged_title": {"fr": "Chaînes signalées et niveau de suspicion", "en": "Flagged channels and level of suspicion",
                      "ru": "Отмеченные каналы и уровень подозрительности"},
    "flagged_note": {
        "fr": "Une tendance suspecte est un comportement atypique de diffusion, pas forcément malveillant. Le niveau de suspicion "
              "vient du nombre d'indicateurs déclenchés : **élevé** = 3 indicateurs ou plus, **moyen** = 2, **faible** = 1. "
              "Les indicateurs se recoupent : le niveau sert à trier, il ne prouve rien sur l'intention de la chaîne.",
        "en": "A suspicious trend is atypical broadcasting behaviour, not necessarily malicious. The level of suspicion "
              "comes from the number of indicators triggered: **high** = 3 or more, **medium** = 2, **low** = 1. "
              "Indicators overlap: the level sorts, it proves nothing about the channel's intent.",
        "ru": "Подозрительная тенденция — это нетипичное поведение распространения, не обязательно злонамеренное. Уровень "
              "определяется числом сработавших индикаторов: **высокий** — 3 и более, **средний** — 2, **низкий** — 1. "
              "Индикаторы пересекаются: уровень нужен для сортировки и ничего не доказывает о намерениях канала."},
    "flagged_counts": {"fr": "{n} chaînes dans la liste : {high} de niveau élevé, {medium} moyen, {low} faible.",
                       "en": "{n} channels in the list: {high} high, {medium} medium, {low} low.",
                       "ru": "{n} каналов в списке: высокий — {high}, средний — {medium}, низкий — {low}."},
    "level_filter": {"fr": "Niveau de suspicion", "en": "Level of suspicion", "ru": "Уровень подозрительности"},
    "level_all": {"fr": "Tous", "en": "All", "ru": "Все"},
    "flagged_top": {"fr": "Chaînes affichées", "en": "Channels shown", "ru": "Показано каналов"},
    "flagged_missing": {"fr": "Le tableau suspicious_channels est introuvable : lancez suspicious_trends.py.",
                        "en": "The suspicious_channels table was not found: run suspicious_trends.py.",
                        "ru": "Таблица suspicious_channels не найдена: запустите suspicious_trends.py."},
    "goal": {"fr": "Objectif", "en": "Goal", "ru": "Цель"},
    "method": {"fr": "Méthode", "en": "Method", "ru": "Метод"},
    "limits": {"fr": "Limites", "en": "Limits", "ru": "Ограничения"},
    "results": {"fr": "Résultats chiffrés", "en": "Figures", "ru": "Цифры"},
    "no_figures": {"fr": "Aucun chiffre disponible : les tableaux de ce thème sont introuvables. Lancez les scripts du thème.",
                   "en": "No figure available: the tables of this theme were not found. Run the theme's scripts.",
                   "ru": "Цифр нет: таблицы этой темы не найдены. Запустите скрипты темы."},
    "no_caption": {"fr": "Description non renseignée pour ce graphe.", "en": "No description for this chart.",
                   "ru": "Для этого графика нет описания."},
    "global_limits": {"fr": "Limites générales", "en": "General limits", "ru": "Общие ограничения"},
    "references": {"fr": "Références des méthodes", "en": "Method references", "ru": "Источники методов"},
    "data_dir": {"fr": "Dossier des données du pipeline", "en": "Pipeline data folder", "ru": "Папка данных конвейера"},
    "files_intro": {"fr": "Pourquoi chaque fichier a été produit et ce qu'il contient. Choisissez un fichier pour le détail.",
                    "en": "Why each file was produced and what it holds. Pick a file for details.",
                    "ru": "Зачем создан каждый файл и что в нём. Выберите файл для подробностей."},
    "catalog_intro": {"fr": "Tous les CSV du dossier d'analyse et tous les jeux de données Parquet du pipeline.",
                      "en": "Every CSV of the analysis folder and every Parquet dataset of the pipeline.",
                      "ru": "Все CSV папки анализа и все наборы данных Parquet конвейера."},
    "csv_files": {"fr": "Tableaux CSV", "en": "CSV tables", "ru": "CSV-таблицы"},
    "parquet_files": {"fr": "Jeux de données Parquet", "en": "Parquet datasets", "ru": "Наборы данных Parquet"},
    "pick_file": {"fr": "Fichier", "en": "File", "ru": "Файл"},
    "purpose": {"fr": "Pourquoi", "en": "Why", "ru": "Зачем"},
    "result": {"fr": "Résultat", "en": "Result", "ru": "Результат"},
    "undocumented": {"fr": "Description non renseignée : seuls les chiffres lus dans le fichier sont donnés.",
                     "en": "No description recorded: only the figures read from the file are given.",
                     "ru": "Описание не записано: даны только цифры, прочитанные из файла."},
    "col_file": {"fr": "Fichier", "en": "File", "ru": "Файл"},
    "col_folder": {"fr": "Dossier", "en": "Folder", "ru": "Папка"},
    "col_size": {"fr": "Taille", "en": "Size", "ru": "Размер"},
    "col_purpose": {"fr": "Pourquoi", "en": "Why", "ru": "Зачем"},
    "col_name": {"fr": "Colonne", "en": "Column", "ru": "Столбец"},
    "col_type": {"fr": "Type", "en": "Type", "ru": "Тип"},
    "columns_title": {"fr": "Colonnes", "en": "Columns", "ru": "Столбцы"},
    "preview": {"fr": "Aperçu (premières lignes)", "en": "Preview (first rows)", "ru": "Просмотр (первые строки)"},
    "n_parts": {"fr": "{n} fichiers Parquet, {size}", "en": "{n} Parquet files, {size}", "ru": "Файлов Parquet: {n}, {size}"},
    "no_parquet": {"fr": "Aucun jeu de données Parquet trouvé dans `{path}` (clean, clean_dedup, gold/). "
                         "Indiquez le dossier des données du pipeline dans la barre latérale.",
                   "en": "No Parquet dataset found in `{path}` (clean, clean_dedup, gold/). "
                         "Set the pipeline data folder in the sidebar.",
                   "ru": "В `{path}` не найдено наборов Parquet (clean, clean_dedup, gold/). "
                         "Укажите папку данных конвейера в боковой панели."},
    "parquet_error": {"fr": "Lecture Parquet impossible : {e}. Installez pyarrow.", "en": "Cannot read Parquet: {e}. Install pyarrow.",
                      "ru": "Не удаётся прочитать Parquet: {e}. Установите pyarrow."},
    "theme4_title": {"fr": "Thème 4 — Pics d'activité géolocalisés", "en": "Theme 4 — Geolocated activity peaks",
                     "ru": "Тема 4 — Геолокализованные пики активности"},
    "theme4_intro": {
        "fr": "Identification, segmentation et corrélation des anomalies temporelles (pics d'activité géolocalisés) "
              "dans les zones urbaines cibles, et ordre de réaction des villes.",
        "en": "Identification, segmentation and correlation of temporal anomalies (geolocated activity peaks) "
              "in the target urban areas, and the order in which cities react.",
        "ru": "Выявление, сегментация и корреляция временных аномалий (геолокализованных пиков активности) "
              "в целевых городских зонах и порядок реакции городов."},
    "tab_maps": {"fr": "Cartes interactives", "en": "Interactive maps", "ru": "Интерактивные карты"},
    "map_choice": {"fr": "Carte", "en": "Map", "ru": "Карта"},
    "map_note": {
        "fr": "Les cartes se chargent depuis Internet (fond de carte). Utilisez les menus au-dessus de la carte.",
        "en": "The maps load their base map from the Internet. Use the menus above the map.",
        "ru": "Карты подгружают подложку из Интернета. Используйте меню над картой."},
    "no_maps": {"fr": "Aucune carte (map_*.html) dans `{path}`. Lancez anomaly_maps.py.",
                "en": "No map (map_*.html) in `{path}`. Run anomaly_maps.py.",
                "ru": "В `{path}` нет карт (map_*.html). Запустите anomaly_maps.py."},
    "dl_map": {"fr": "Télécharger la carte (HTML)", "en": "Download the map (HTML)", "ru": "Скачать карту (HTML)"},
    "key_figures": {"fr": "Chiffres clés", "en": "Key figures", "ru": "Ключевые цифры"},
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
    "tab_figs": {"fr": "Graphes", "en": "Charts", "ru": "Графики"},
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
    ap.add_argument("--data", default="telescope_pipeline_files")
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
    file_card(path.stem, get_table_factory(files))

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


def get_table_factory(files: dict[str, Path]):
    """Function name -> DataFrame (or None) over the tables of a page, used by the captions."""
    by_stem = {p.stem: p for p in files.values()}

    def get(name: str):
        p = by_stem.get(name)
        return load_csv(str(p), p.stat().st_mtime) if p is not None else None
    return get


def caption_block(stem: str, get_table) -> None:
    """Short description and key figures of a chart or map (Markdown lines); never empty."""
    what, facts = describe(stem, LANG, get_table)
    if what:
        st.markdown(f"- {what}")
    figures = facts or generic_caption(stem, LANG, get_table)
    if figures:
        st.markdown(f"- **{tr('key_figures')} :** {figures}" if LANG == "fr" else f"- **{tr('key_figures')}:** {figures}")
    if not what and not figures:
        st.markdown(f"- _{tr('no_caption')}_")


def file_card(stem: str, get_table) -> None:
    """Why a CSV table was produced and its key figures."""
    why, facts, documented = describe_table(stem, LANG, get_table)
    if why:
        st.markdown(f"**{tr('purpose')} :** {why}" if LANG == "fr" else f"**{tr('purpose')}:** {why}")
    if facts:
        st.markdown(f"**{tr('result')} :** {facts}" if LANG == "fr" else f"**{tr('result')}:** {facts}")
    if not documented:
        st.caption(tr("undocumented"))


def figures_view(fig_dirs: list[Path], get_table) -> None:
    pngs = [(d, p) for d in fig_dirs if d.is_dir() for p in sorted(d.glob("*.png"))]
    if not pngs:
        st.warning(tr("no_png", path=", ".join(str(d) for d in fig_dirs)))
        return
    for d in fig_dirs:
        readme = d / "README.md"
        if readme.is_file():
            with st.expander(f"{tr('readme_figs')} — {d.name}"):
                st.markdown(read_text(readme))
    for _, p in pngs:
        st.markdown(f"#### {title_of(p.stem, LANG)}")
        caption_block(p.stem, get_table)
        st.image(str(p), width=1000)


def maps_view(map_dir: Path, get_table) -> None:
    maps = sorted(map_dir.glob("map_*.html")) if map_dir.is_dir() else []
    if not maps:
        st.warning(tr("no_maps", path=map_dir))
        return
    st.caption(tr("map_note"))
    names = {p.stem: p for p in maps}
    choice = st.selectbox(tr("map_choice"), list(names), format_func=lambda k: title_of(k, LANG), key="map_choice")
    path = names[choice]
    caption_block(choice, get_table)
    html = read_text(path)
    components.html(html, height=800, scrolling=False)
    st.download_button(tr("dl_map"), html.encode("utf-8"), file_name=path.name, mime="text/html", key="map_dl")


# ----------------------------------------------------------------- Parquet access (cached)
@st.cache_data(show_spinner=False)
def load_parquet_info(path: str, mtime: float) -> dict:
    return parquet_info(Path(path))


@st.cache_data(show_spinner=False)
def load_parquet_preview(path: str, mtime: float, n: int) -> pd.DataFrame:
    return parquet_preview(Path(path), n)


def parquet_card(name: str, path: Path, key: str) -> None:
    """Why a Parquet dataset was produced, how big it is, its columns and (on request) its first rows."""
    try:
        info = load_parquet_info(str(path), path.stat().st_mtime)
    except Exception as e:                                   # pyarrow missing or unreadable files
        st.warning(tr("parquet_error", e=e))
        info = None
    why, res, documented = describe_parquet(name, LANG, info["rows"] if info else None)
    if why:
        st.markdown(f"**{tr('purpose')} :** {why}" if LANG == "fr" else f"**{tr('purpose')}:** {why}")
    if res:
        st.markdown(f"**{tr('result')} :** {res}" if LANG == "fr" else f"**{tr('result')}:** {res}")
    if not documented:
        st.caption(tr("undocumented"))
    if info is None:
        return
    st.caption(tr("n_parts", n=info["n_files"], size=fmt_bytes(info["size"])) + f" — `{path}`")
    st.markdown(f"**{tr('columns_title')}**")
    st.dataframe(pd.DataFrame(info["columns"], columns=[tr("col_name"), tr("col_type")]))
    if st.checkbox(tr("preview"), key=f"{key}_pv_{name}"):
        try:
            st.dataframe(load_parquet_preview(str(path), path.stat().st_mtime, 20))
        except Exception as e:
            st.warning(tr("parquet_error", e=e))


def csv_card(name: str, path: Path, get_table, key: str) -> None:
    """Details of one CSV: purpose, figures, columns and first rows."""
    file_card(path.stem, get_table)
    df = load_csv(str(path), path.stat().st_mtime)
    st.caption(tr("rows_cols", rows=fmt_int(len(df)), cols=len(df.columns)) + f" — `{path}`")
    st.markdown(f"**{tr('columns_title')}**")
    st.dataframe(pd.DataFrame({tr("col_name"): df.columns, tr("col_type"): [str(t) for t in df.dtypes]}))
    st.markdown(f"**{tr('preview')}**")
    st.dataframe(df.head(10))


def files_view(files: dict[str, Path], parquets: dict[str, Path], key: str) -> None:
    """Catalogue of the CSV tables and Parquet datasets: summary list, then one card per chosen file."""
    st.write(tr("files_intro"))
    get_table = get_table_factory(files)
    if files:
        st.markdown(f"#### {tr('csv_files')} ({len(files)})")
        rows = []
        for k, p in files.items():
            e = TABLE_INFO.get(p.stem)
            rows.append({tr("col_file"): k, tr("col_folder"): p.parent.name, tr("col_size"): fmt_bytes(p.stat().st_size),
                         tr("col_purpose"): e["why"][LANG] if e else "—"})
        st.dataframe(pd.DataFrame(rows))
        pick = st.selectbox(tr("pick_file"), list(files), key=f"{key}_csvpick")
        csv_card(pick, files[pick], get_table, key)
    if parquets:
        st.markdown(f"#### {tr('parquet_files')} ({len(parquets)})")
        rows = []
        for k, p in parquets.items():
            e = PARQUET_INFO.get(k)
            size = sum(f.stat().st_size for f in p.rglob("*.parquet"))
            rows.append({tr("col_file"): k, tr("col_folder"): p.parent.name, tr("col_size"): fmt_bytes(size),
                         tr("col_purpose"): e["why"][LANG] if e else "—"})
        st.dataframe(pd.DataFrame(rows))
        pick = st.selectbox(tr("pick_file"), list(parquets), key=f"{key}_pqpick")
        parquet_card(pick, parquets[pick], key)


def theme_files(page_id: str, analysis: Path) -> tuple[list[Path], dict[str, Path]]:
    """Table folders of a theme and the CSV files found in them (key = file stem, or folder/stem when several folders)."""
    tdirs = [analysis / t for t in THEMES[page_id]["tables"]]
    files: dict[str, Path] = {}
    for tdir in tdirs:
        files.update({(f"{tdir.name}/{k}" if len(tdirs) > 1 else k): v for k, v in discover_tables(tdir).items()})
    return tdirs, files


def headline_block(page_id: str, get_table) -> None:
    """Key figures of a theme: one line per headline chart or table, computed from the files."""
    n = 0
    for stem in HEADLINES.get(page_id, []):
        what, facts = describe(stem, LANG, get_table)
        if facts:
            st.markdown(f"- {facts}")
            n += 1
    if not n:
        st.info(tr("no_figures"))


def formulas_block(page_id: str) -> None:
    """Mathematical formulas of the theme's methods, each with its symbols and its meaning."""
    items = FORMULAS.get(page_id, [])
    if not items:
        return
    st.markdown(f"#### {tr('formulas')}")
    st.caption(tr("formulas_note"))
    for f in items:
        st.markdown(f"**{f['name'][LANG]}**")
        st.latex(f["tex"])
        st.markdown(f["text"][LANG])


def flagged_block(files: dict[str, Path], key: str) -> None:
    """Theme 5: the flagged channels with their level of suspicion and the indicators that fired."""
    st.markdown(f"#### {tr('flagged_title')}")
    st.markdown(tr("flagged_note"))
    p = next((v for k, v in files.items() if v.stem == "suspicious_channels"), None)
    if p is None:
        st.info(tr("flagged_missing"))
        return
    sus = load_csv(str(p), p.stat().st_mtime)
    rp = next((v for k, v in files.items() if v.stem == "review_candidates"), None)
    review = load_csv(str(rp), rp.stat().st_mtime) if rp is not None else None
    d = flagged_channels(sus, review, LANG)
    n = d["level_key"].value_counts()
    st.markdown(tr("flagged_counts", n=fmt_int(len(d)), high=fmt_int(int(n.get("high", 0))),
                   medium=fmt_int(int(n.get("medium", 0))), low=fmt_int(int(n.get("low", 0)))))
    c1, c2 = st.columns(2)
    names = [tr("level_all")] + [LEVEL_NAMES[LANG][k] for k in ("high", "medium", "low")]
    lvl = c1.selectbox(tr("level_filter"), names, key=f"{key}_level")
    top = c2.slider(tr("flagged_top"), 10, 200, 30, key=f"{key}_flagged_n")
    view = d if lvl == tr("level_all") else d[d["level"] == lvl]
    st.dataframe(view.drop(columns="level_key").head(top))


def text_block(page_id: str) -> None:
    t = THEME_TEXT[page_id]
    st.markdown(f"**{tr('goal')}.** {t['goal'][LANG]}")
    st.markdown(f"**{tr('method')}.** {t['method'][LANG]}")


def page_theme(page_id: str, analysis: Path, data_dir: Path) -> None:
    cfg = THEMES[page_id]
    st.header(tr(f"{page_id}_title"))
    st.write(tr(f"{page_id}_intro"))
    tdirs, files = theme_files(page_id, analysis)
    fdirs = [analysis / f for f in cfg["figures"]]
    key = page_id
    get_table = get_table_factory(files)
    all_pq = discover_parquets(data_dir)
    parquets = {k: v for k, v in all_pq.items() if k in cfg.get("parquets", [])}

    labels = [tr("tab_summary"), tr("tab_figs"), tr("tab_tables")] + ([tr("tab_maps")] if "maps" in cfg else []) + [tr("tab_files")]
    tabs = st.tabs(labels)
    with tabs[0]:
        text_block(page_id)
        formulas_block(page_id)
        st.markdown(f"#### {tr('results')}")
        headline_block(page_id, get_table)
        if page_id == "theme5":
            flagged_block(files, key)
        st.markdown(f"**{tr('limits')}.** {THEME_TEXT[page_id]['limits'][LANG]}")
        info = tdirs[0] / "run_info.json"
        if info.is_file():
            with st.expander(tr("run_info")):
                st.code(read_text(info), language="json")
        protocol = tdirs[0] / "tracing_protocol.md"
        if protocol.is_file():
            with st.expander(tr("protocol")):
                st.markdown(read_text(protocol))
    with tabs[1]:
        figures_view(fdirs, get_table)
    with tabs[2]:
        if files:
            st.caption(tr("n_tables", n=len(files), path=", ".join(str(d) for d in tdirs)))
            table_view(files, key)
        else:
            st.warning(tr("no_csv", path=", ".join(str(d) for d in tdirs)))
    if "maps" in cfg:
        with tabs[3]:
            maps_view(analysis / cfg["maps"], get_table)
    with tabs[-1]:
        files_view(files, parquets, key)


def page_report(analysis: Path, data_dir: Path) -> None:
    st.title(tr("report_title"))
    st.write(tr("report_intro"))
    st.markdown(tr("report_howto"))
    page_pipeline()
    for pid in THEMES:
        st.header(tr(f"{pid}_title"))
        text_block(pid)
        with st.expander(tr("formulas")):
            formulas_block(pid)
        _, files = theme_files(pid, analysis)
        headline_block(pid, get_table_factory(files))
        st.markdown(f"**{tr('limits')}.** {THEME_TEXT[pid]['limits'][LANG]}")
    st.header(tr("global_limits"))
    st.write(GLOBAL_LIMITS[LANG])
    st.header(tr("references"))
    for r in REFERENCES:
        st.markdown(f"- {r}")


def page_catalog(analysis: Path, data_dir: Path) -> None:
    st.header(tr("page_catalog"))
    st.write(tr("catalog_intro"))
    files = discover_tables(analysis)
    parquets = discover_parquets(data_dir)
    if not parquets:
        st.warning(tr("no_parquet", path=data_dir))
    files_view(files, parquets, "catalog")


def main() -> None:
    global LANG
    st.set_page_config(page_title="TeleScope v2", layout="wide")
    args = parse_args()
    st.sidebar.title("TeleScope v2")
    LANG = st.sidebar.selectbox("Language / Langue / Язык", list(LANGS), format_func=LANGS.get)
    analysis = Path(st.sidebar.text_input(tr("analysis_dir"), args.analysis)).expanduser()
    data_dir = Path(st.sidebar.text_input(tr("data_dir"), args.data)).expanduser()
    page_ids = ["report", "pipeline"] + list(THEMES) + ["catalog"]
    names = {"report": tr("page_report"), "pipeline": tr("page_pipeline"), "catalog": tr("page_catalog")}
    page = st.sidebar.radio(tr("page"), page_ids, format_func=lambda p: names.get(p) or tr(f"{p}_title"))
    if not analysis.is_dir() and page not in ("pipeline",):
        st.error(tr("no_dir", path=analysis))
        return
    if page == "report":
        page_report(analysis, data_dir)
    elif page == "pipeline":
        page_pipeline()
        parquets = discover_parquets(data_dir)
        if parquets:
            files_view({}, parquets, "pipeline")
        else:
            st.warning(tr("no_parquet", path=data_dir))
    elif page == "catalog":
        page_catalog(analysis, data_dir)
    else:
        page_theme(page, analysis, data_dir)


if __name__ == "__main__":
    main()