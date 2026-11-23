"""Report texts and file catalogue of the TeleScope v2 viewer (fr / en / ru).

No Streamlit here, so everything can be tested with pandas alone:
  THEME_TEXT   goal, method and limits of each theme (what was done and how far it can be trusted);
  TABLE_INFO   why each CSV table was produced and which chart caption gives its key figures;
  PARQUET_INFO why each Parquet dataset (clean, clean_dedup, gold/*) was produced and what one row is;
  REFERENCES   the published methods the analyses rely on;
  describe_table / parquet_* / table_stats   figures computed from the files themselves (nothing typed by hand).
"""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

from telescope_captions import REGISTRY, L3, dec, num


# ----------------------------------------------------------------- theme texts
THEME_TEXT: dict[str, dict] = {
    "theme1": dict(
        goal=L3("Repérer des groupes de canaux qui se relaient entre eux (communautés) à partir des transferts de messages.",
                "Find groups of channels that forward one another (communities) from message forwards.",
                "Найти группы каналов, которые пересылают друг друга (сообщества), по пересылкам сообщений."),
        method=L3("Graphe orienté canal → canal, pondéré par le nombre de transferts. Leiden (méthode principale, résolution choisie "
                  "sur la courbe de modularité) et Infomap (comparaison). Stabilité d'une année à l'autre mesurée par le NMI. "
                  "Profil de chaque communauté : taille, transferts émis, part qui reste à l'intérieur.",
                  "Directed channel → channel graph weighted by the number of forwards. Leiden (main method, resolution chosen on the "
                  "modularity curve) and Infomap (comparison). Year-to-year stability measured with NMI. "
                  "Profile of each community: size, forwards sent, share that stays inside.",
                  "Ориентированный граф канал → канал с весом по числу пересылок. Leiden (основной метод, резолюция выбрана по кривой "
                  "модулярности) и Infomap (для сравнения). Устойчивость от года к году измерена по NMI. "
                  "Профиль сообщества: размер, отправленные пересылки, доля внутри."),
        limits=L3("Une communauté dit qui relaie qui, pas pourquoi. Le découpage dépend de la résolution : on regarde la courbe "
                  "et la stabilité plutôt qu'un seul résultat.",
                  "A community says who forwards whom, not why. The split depends on the resolution: we look at the curve and "
                  "the stability rather than a single result.",
                  "Сообщество показывает, кто кого пересылает, но не почему. Разбиение зависит от резолюции: смотрим на кривую "
                  "и устойчивость, а не на один результат.")),
    "theme2": dict(
        goal=L3("Savoir si les communautés suivent les langues et comment l'information passe d'une langue à l'autre.",
                "Find out whether communities follow languages and how information moves between languages.",
                "Выяснить, совпадают ли сообщества с языками и как информация переходит между языками."),
        method=L3("Langue détectée par canal. Pureté : part de la langue dominante dans chaque communauté. Homophilie : part des "
                  "transferts dans la même langue, comparée à ce que donnerait le hasard. Flux entre langues, canaux-ponts, activité "
                  "par langue. La langue des canaux inconnus est déduite par vote des voisins et vérifiée sur des canaux cachés.",
                  "Language detected per channel. Purity: share of the dominant language in each community. Homophily: share of "
                  "forwards in the same language, compared with what chance would give. Flows between languages, bridge channels, "
                  "activity by language. The language of unknown channels is inferred by neighbour vote and checked on hidden channels.",
                  "Язык определён для каждого канала. Чистота: доля преобладающего языка в сообществе. Гомофилия: доля пересылок "
                  "внутри языка в сравнении со случайным ожиданием. Потоки между языками, каналы-мосты, активность по языкам. "
                  "Язык неизвестных каналов выводится голосованием соседей и проверяется на скрытых каналах."),
        limits=L3("La langue vient d'une détection automatique : c'est une estimation. Les canaux sans langue sont laissés de côté "
                  "dans les mesures ; la langue déduite est elle aussi une estimation.",
                  "The language comes from automatic detection: it is an estimate. Channels without a language are left out of the "
                  "measures; the inferred language is an estimate too.",
                  "Язык определяется автоматически, это оценка. Каналы без языка исключены из измерений; выведенный язык — тоже оценка.")),
    "theme3": dict(
        goal=L3("Remonter jusqu'à la source d'un message transféré, et mesurer la rapidité et la concentration des relais.",
                "Trace a forwarded message back to its source, and measure the speed and concentration of relays.",
                "Проследить пересланное сообщение до источника и измерить скорость и концентрацию ретрансляций."),
        method=L3("Chaînes de relais reconstruites à partir de l'origine déclarée (canal, publication, date). Niveaux de traçabilité "
                  "A/B/C/D selon jusqu'où la source est retrouvée ; vérification que la source figure dans le corpus ; "
                  "tailles de chaînes, délais, concentration des sources.",
                  "Relay chains rebuilt from the declared origin (channel, post, date). Traceability levels A/B/C/D depending on how "
                  "far the source is found; check that the source is in the corpus; chain sizes, delays, source concentration.",
                  "Цепочки ретрансляций восстановлены по заявленному источнику (канал, пост, дата). Уровни прослеживаемости A/B/C/D "
                  "по тому, насколько найден источник; проверка наличия источника в корпусе; размеры цепочек, задержки, концентрация."),
        limits=L3("Seule l'origine déclarée par Telegram est connue. Une source absente du corpus ne peut pas être vérifiée. "
                  "Les copies supprimées à la déduplication ne diffèrent que par les vues et les transferts.",
                  "Only the origin declared by Telegram is known. A source missing from the corpus cannot be checked. "
                  "The copies removed at deduplication differ only in views and forwards.",
                  "Известен только источник, заявленный Telegram. Источник вне корпуса проверить нельзя. "
                  "Копии, удалённые при дедупликации, отличаются лишь просмотрами и пересылками.")),
    "theme4": dict(
        goal=L3("Détecter les pics d'activité des villes ciblées, voir lesquels sont synchronisés et quelle ville réagit la première.",
                "Detect activity peaks in the target cities, see which are synchronized and which city reacts first.",
                "Обнаружить пики активности в целевых городах, понять, какие синхронны и какой город реагирует первым."),
        method=L3("Une ville est attribuée aux canaux (texte du canal ou vote des canaux voisins). Séries quotidiennes de messages par "
                  "ville ; jours anormaux regroupés en épisodes (brefs, courts, prolongés) ; corrélation entre villes avec décalage "
                  "de quelques jours ; pics synchronisés quand plusieurs villes sont en pic ensemble ; ordre de réaction en heures.",
                  "A city is assigned to channels (the channel's text or the vote of neighbouring channels). Daily message series per "
                  "city; abnormal days grouped into episodes (spikes, short, sustained); correlation between cities with a lag of a "
                  "few days; synchronized peaks when several cities peak together; order of reaction in hours.",
                  "Каналам присваивается город (по тексту канала или голосованием соседей). Ежедневные ряды сообщений по городам; "
                  "аномальные дни объединены в эпизоды (краткие, короткие, затяжные); корреляция городов со сдвигом в несколько дней; "
                  "синхронные пики — когда несколько городов в пике одновременно; порядок реакции в часах."),
        limits=L3("Seule une partie des canaux a une ville. Un pic montre de l'activité, pas sa cause. "
                  "L'ordre de réaction dépend de la finesse horaire des données.",
                  "Only part of the channels has a city. A peak shows activity, not its cause. "
                  "The order of reaction depends on the hourly detail of the data.",
                  "Город есть лишь у части каналов. Пик показывает активность, но не причину. "
                  "Порядок реакции зависит от почасовой детализации данных.")),
    "theme5": dict(
        goal=L3("Repérer des comportements de diffusion atypiques (rapidité, source unique, régularité, volume, coordination) "
                "et comprendre la hausse des relais instantanés au fil des années.",
                "Find atypical broadcasting behaviour (speed, single source, regularity, volume, coordination) "
                "and understand the rise of instant relays over the years.",
                "Выявить нетипичное поведение распространения (скорость, один источник, регулярность, объём, координация) "
                "и понять рост мгновенных пересылок по годам."),
        method=L3("Tables de comportement par chaîne calculées avec Spark. Indicateurs en deux catégories : comportement individuel "
                  "(relais rapide, source unique, rythme horaire, seconde fixe, rafales, écart de vues, relais pur, grand nombre de "
                  "sources, délai régulier, débit, volume brutal) et coordination (appartenance à un groupe serré). Paires de chaînes "
                  "qui relaient le même message à quelques secondes d'écart, regroupées en groupes ; groupes serrés quand leur densité "
                  "est élevée. Les discussions liées de Telegram, qui relaient tout par construction, sont identifiées à part. "
                  "Tendance mensuelle recalculée avec et sans les chaînes sélectionnées ; recherche de qui produit la hausse d'un mois ; "
                  "liste de chaînes à relire à la main. Les seuils sont dans la colonne « threshold » du tableau des indicateurs.",
                  "Per-channel behaviour tables computed with Spark. Indicators in two categories: individual behaviour (fast relay, "
                  "single source, hourly rhythm, fixed second, bursts, views gap, pure relay, many sources, regular delay, throughput, "
                  "abrupt volume) and coordination (membership of a tight group). Pairs of channels relaying the same message seconds "
                  "apart, merged into groups; groups are tight when their density is high. Telegram linked discussion groups, which "
                  "relay everything by design, are identified separately. Monthly trend recomputed with and without the selected "
                  "channels; search for who produces a month's rise; list of channels to review by hand. "
                  "The thresholds are in the 'threshold' column of the indicator table.",
                  "Таблицы поведения по каналам посчитаны в Spark. Индикаторы двух категорий: индивидуальное поведение (быстрая "
                  "пересылка, один источник, суточный ритм, фиксированная секунда, всплески, разрыв просмотров, чистая пересылка, "
                  "много источников, ровная задержка, пропускная способность, резкий объём) и координация (участие в плотной группе). "
                  "Пары каналов, пересылающих одно сообщение с разницей в секунды, объединены в группы; группа плотная при высокой "
                  "плотности. Связанные группы обсуждения Telegram, которые пересылают всё по устройству, выделены отдельно. "
                  "Месячный тренд пересчитан с отобранными каналами и без них; поиск тех, кто даёт рост месяца; список каналов для "
                  "ручной проверки. Пороги указаны в столбце «threshold» таблицы индикаторов."),
        limits=L3("Aucun texte de message n'est disponible : on mesure des comportements, pas des intentions. « Suspect » veut dire "
                  "atypique, pas forcément malveillant ; ce n'est pas la preuve d'un robot ni d'une campagne. Les indicateurs se recoupent (un relais très rapide a "
                  "mécaniquement un délai régulier) : le score sert à trier, pas à mesurer une gravité. Les seuils ne sont pas validés "
                  "et la relecture manuelle ne porte que sur les titres et noms publics.",
                  "No message text is available: we measure behaviour, not intent. 'Suspicious' means atypical, not necessarily "
                  "malicious; it is not proof of a bot or a campaign. The indicators overlap (a very fast relay mechanically has a regular delay): the score sorts, it does not "
                  "measure seriousness. The thresholds are not validated and the manual review only relies on titles and public names.",
                  "Текстов сообщений нет: измеряется поведение, а не намерения. «Подозрительное» значит нетипичное, не обязательно "
                  "злонамеренное; это не доказывает ни бота, ни кампанию. Индикаторы пересекаются (очень быстрая пересылка по определению даёт ровную задержку): балл служит для "
                  "сортировки, а не для оценки серьёзности. Пороги не проверены, ручная проверка опирается только на названия и "
                  "публичные имена.")),
}

GLOBAL_LIMITS = L3(
    "Le jeu de données ne contient pas le texte des messages : toutes les analyses reposent sur les liens de transfert, les dates, "
    "les vues et les métadonnées des canaux. Les chiffres de cette application sont lus dans les fichiers produits par les scripts, "
    "jamais saisis à la main ; si un fichier manque, la ligne correspondante disparaît.",
    "The dataset has no message text: every analysis relies on forwarding links, dates, views and channel metadata. "
    "The figures in this application are read from the files written by the scripts, never typed by hand; "
    "if a file is missing, the matching line disappears.",
    "В данных нет текста сообщений: все анализы опираются на ссылки пересылок, даты, просмотры и метаданные каналов. "
    "Цифры в приложении читаются из файлов, созданных скриптами, и не вводятся вручную; "
    "если файла нет, соответствующая строка исчезает.")

REFERENCES = [
    "Traag, V. A., Waltman, L., van Eck, N. J. (2019). From Louvain to Leiden: guaranteeing well-connected communities. "
    "Scientific Reports 9, 5233.",
    "Rosvall, M., Bergstrom, C. T. (2008). Maps of random walks on complex networks reveal community structure. PNAS 105(4).",
    "Newman, M. E. J. (2006). Modularity and community structure in networks. PNAS 103(23).",
    "Strehl, A., Ghosh, J. (2002). Cluster ensembles — a knowledge reuse framework for combining multiple partitions "
    "(normalized mutual information). Journal of Machine Learning Research 3.",
    "Pacheco, D., Hui, P.-M., Torres-Lugo, C., Truong, B. T., Flammini, A., Menczer, F. (2021). Uncovering coordinated networks "
    "on social media: methods and case studies. ICWSM 15.",
    "Giglietto, F., Righetti, N., Rossi, L., Marino, G. (2020). It takes a village to manipulate the media: coordinated link "
    "sharing behavior during 2018 and 2019 Italian elections. Information, Communication & Society 23(6).",
]


# ----------------------------------------------------------------- CSV tables: why, and where the figures come from
def _t(fr, en, ru, facts=None):
    return dict(why=L3(fr, en, ru), facts=facts)


TABLE_INFO: dict[str, dict] = {
    # theme 1
    "community_profiles_leiden": _t("Une ligne par communauté (Leiden) : taille, transferts émis et part restée à l'intérieur. Sert à décrire et comparer les communautés.",
                                    "One row per community (Leiden): size, forwards sent and share kept inside. Used to describe and compare communities.",
                                    "Строка на сообщество (Leiden): размер, отправленные пересылки и доля внутри. Для описания и сравнения сообществ.",
                                    "community_size_distribution"),
    "community_summary": _t("Résumé par algorithme : nœuds, liens, nombre de communautés, modularité. Sert à comparer Leiden et Infomap.",
                            "Summary per algorithm: nodes, links, number of communities, modularity. Used to compare Leiden and Infomap.",
                            "Сводка по алгоритму: узлы, связи, число сообществ, модулярность. Для сравнения Leiden и Infomap.", "degree_distribution"),
    "resolution_curve": _t("Nombre de communautés et modularité pour chaque résolution testée. Sert à choisir la résolution de Leiden.",
                           "Number of communities and modularity for each tested resolution. Used to choose Leiden's resolution.",
                           "Число сообществ и модулярность для каждой проверенной резолюции. Для выбора резолюции Leiden.", "resolution_curve"),
    "yearly_communities": _t("Communautés, modularité et stabilité (NMI) année par année. Sert à voir si la structure évolue.",
                             "Communities, modularity and stability (NMI) year by year. Used to see whether the structure changes.",
                             "Сообщества, модулярность и устойчивость (NMI) по годам. Чтобы видеть, меняется ли структура.", "yearly_structure"),
    # theme 2
    "community_language_purity": _t("Pureté linguistique de chaque communauté. Sert à savoir si une communauté est monolingue.",
                                    "Language purity of each community. Used to tell whether a community is single-language.",
                                    "Языковая чистота каждого сообщества. Чтобы понять, одноязычно ли оно.", "community_purity"),
    "language_spread": _t("Nombre de canaux par langue. Sert de base à toutes les mesures par langue.",
                          "Number of channels per language. The base of every per-language measure.",
                          "Число каналов по языкам. Основа всех измерений по языкам.", "language_distribution"),
    "language_homophily": _t("Part des transferts dans la même langue, comparée à l'attendu au hasard, par langue.",
                             "Share of forwards in the same language, compared with chance, per language.",
                             "Доля пересылок внутри языка в сравнении со случайной, по языкам.", "language_homophily"),
    "language_flows": _t("Nombre de transferts de chaque langue vers chaque autre. Sert à voir où l'information change de langue.",
                         "Number of forwards from each language to each other. Used to see where information changes language.",
                         "Число пересылок из каждого языка в каждый другой. Чтобы видеть, где информация меняет язык.", "language_flows_heatmap"),
    "language_bridges": _t("Canaux dont les transferts traversent le plus les langues. Sert à repérer les intermédiaires.",
                           "Channels whose forwards cross languages the most. Used to spot intermediaries.",
                           "Каналы, чьи пересылки чаще всего пересекают языки. Чтобы находить посредников.", "language_bridges"),
    "language_activity": _t("Activité relayée par langue rapportée au nombre de canaux.",
                            "Relayed activity per language relative to the number of channels.",
                            "Пересылаемая активность по языкам относительно числа каналов.", "language_activity"),
    "inference_accuracy": _t("Exactitude de la langue déduite des canaux inconnus, testée sur des canaux dont la langue est cachée.",
                             "Accuracy of the inferred language of unknown channels, tested on channels whose language is hidden.",
                             "Точность выведенного языка неизвестных каналов, проверенная на каналах со скрытым языком.", "language_inference_accuracy"),
    "language_yearly": _t("Cohésion, diversité et assortativité linguistiques année par année.",
                          "Language cohesion, diversity and assortativity year by year.",
                          "Языковая сплочённость, разнообразие и ассортативность по годам.", "language_yearly_cohesion"),
    # theme 3
    "chain_size_distribution": _t("Nombre de relais par publication d'origine, par classe de taille.",
                                  "Number of relays per original post, by size class.",
                                  "Число пересылок на исходный пост по классам размера.", "chain_size_distribution"),
    "delay_distribution": _t("Délai entre la publication d'origine et ses relais, par classe.",
                             "Delay between the original post and its relays, by class.",
                             "Задержка между исходным постом и пересылками по классам.", "delay_distribution"),
    "delay_by_year": _t("Délai médian et part relayée en moins d'un jour, par année.",
                        "Median delay and share relayed within a day, by year.",
                        "Медианная задержка и доля в пределах суток по годам.", "delay_by_year"),
    "source_concentration": _t("Part des relais détenue par les sources les plus relayées.",
                               "Share of relays held by the most relayed sources.",
                               "Доля пересылок у самых пересылаемых источников.", "source_concentration"),
    "source_verification": _t("Part des publications et relais dont la source est retrouvée dans le corpus.",
                              "Share of posts and relays whose source is found in the corpus.",
                              "Доля постов и пересылок, чей источник найден в корпусе.", "source_verification"),
    "top_sources": _t("Les canaux sources les plus relayés.", "The most relayed source channels.",
                      "Самые пересылаемые каналы-источники.", "top_sources"),
    "traceability_levels": _t("Part des transferts par niveau de traçabilité A/B/C/D.",
                              "Share of forwards by traceability level A/B/C/D.",
                              "Доля пересылок по уровням прослеживаемости A/B/C/D.", "traceability_levels"),
    # theme 4
    "geo_summary": _t("Résumé de la géolocalisation des canaux : combien ont une ville et par quelle méthode.",
                      "Summary of channel geolocation: how many have a city and by which method.",
                      "Сводка геолокации каналов: у скольких есть город и каким методом.", "city_coverage_by_language"),
    "channel_geo": _t("Ville attribuée à chaque canal. Sert à relier les canaux aux séries par ville.",
                      "City assigned to each channel. Used to link channels to the per-city series.",
                      "Город, присвоенный каждому каналу. Связывает каналы с рядами по городам.", None),
    "city_totals": _t("Nombre de canaux par ville.", "Number of channels per city.", "Число каналов по городам.", "top_cities"),
    "anomaly_summary": _t("Paramètres et totaux de la détection de pics : villes, jours, épisodes.",
                          "Parameters and totals of the peak detection: cities, days, episodes.",
                          "Параметры и итоги обнаружения пиков: города, дни, эпизоды.", "top_cities_series"),
    "anomaly_episodes": _t("Un épisode de pic par ligne : ville, dates, forme (bref, court, prolongé), messages en excès.",
                           "One peak episode per row: city, dates, shape (spike, short, sustained), excess posts.",
                           "Эпизод пика в строке: город, даты, форма (краткий, короткий, затяжной), избыточные сообщения.", "episodes_per_month"),
    "city_pair_correlation": _t("Corrélation entre villes (meilleur décalage en jours). Sert à voir quelles villes évoluent ensemble.",
                                "Correlation between cities (best lag in days). Used to see which cities move together.",
                                "Корреляция городов (лучший сдвиг в днях). Чтобы видеть, какие города меняются вместе.", "map_city_correlation"),
    "synchronized_peaks": _t("Pics synchronisés : période, villes concernées, première ville à réagir, écart en heures.",
                             "Synchronized peaks: period, cities involved, first city to react, gap in hours.",
                             "Синхронные пики: период, города, первый город, разрыв в часах.", "cities_anomalous_per_day"),
    # theme 5
    "suspicious_channels": _t("Chaînes ayant au moins un indicateur, avec leur score et les raisons. Sert à trier les chaînes à examiner.",
                              "Channels with at least one indicator, with their score and reasons. Used to sort the channels to examine.",
                              "Каналы хотя бы с одним индикатором, с баллом и причинами. Для сортировки каналов к проверке.", "score_distribution"),
    "indicator_summary": _t("Chaque indicateur : catégorie, seuil, nombre et part de chaînes signalées. Sert à justifier les seuils.",
                            "Each indicator: category, threshold, number and share of flagged channels. Used to justify the thresholds.",
                            "Каждый индикатор: категория, порог, число и доля отмеченных каналов. Для обоснования порогов.", "indicator_counts"),
    "suspicious_summary": _t("Totaux de l'analyse : chaînes évaluées, chaînes signalées, groupes, tendance.",
                             "Totals of the analysis: channels evaluated, channels flagged, groups, trend.",
                             "Итоги анализа: оценено каналов, отмечено каналов, группы, тренд.", "score_distribution"),
    "coordinated_groups": _t("Un groupe de chaînes par ligne : taille, paires, messages communs, écart typique, densité.",
                             "One group of channels per row: size, pairs, shared messages, typical gap, density.",
                             "Группа каналов в строке: размер, пары, общие сообщения, типичный разрыв, плотность.", "coordinated_groups"),
    "coordinated_members": _t("Membres de chaque groupe, avec le score de chaque chaîne.",
                              "Members of each group, with each channel's score.",
                              "Участники каждой группы с баллом каждого канала.", "behaviour_vs_group"),
    "monthly_trend": _t("Rapidité des relais et cascades concentrées, mois par mois. Sert à voir la hausse des relais instantanés.",
                        "Relay speed and concentrated cascades, month by month. Used to see the rise of instant relays.",
                        "Скорость пересылок и концентрированные каскады по месяцам. Чтобы видеть рост мгновенных пересылок.", "fast_share_monthly"),
    "fast_mirror_channels": _t("Chaînes qui relaient presque instantanément depuis une seule source, classées (discussion liée, relais instantané…).",
                               "Channels relaying almost instantly from a single source, classified (linked discussion, instant relay…).",
                               "Каналы, пересылающие почти мгновенно из одного источника, с классификацией (связанная дискуссия, мгновенная пересылка…).", "mirror_delay"),
    "fast_mirror_families": _t("Sources suivies par plusieurs chaînes miroirs.", "Sources followed by several mirror channels.",
                               "Источники, за которыми следуют несколько зеркальных каналов.", "mirror_families"),
    "fast_mirror_review": _t("Échantillon de chaînes miroirs à relire.", "Sample of mirror channels to review.",
                             "Выборка зеркальных каналов для проверки.", None),
    "fast_mirror_summary": _t("Totaux de la sélection de chaînes miroirs.", "Totals of the mirror-channel selection.",
                              "Итоги отбора зеркальных каналов.", "mirror_delay"),
    "fast_trend_excluding": _t("Part des relais en moins de 10 s avec et sans les chaînes sélectionnées. Sert à savoir si la hausse vient d'elles.",
                               "Share of relays within 10 s with and without the selected channels. Used to tell whether the rise comes from them.",
                               "Доля пересылок в течение 10 с с отобранными каналами и без них. Чтобы понять, связан ли рост с ними.", "fast_trend_excluding"),
    "month_drivers_channels": _t("Chaînes qui expliquent la hausse d'un mois par rapport au mois de référence.",
                                 "Channels that explain a month's rise compared with the reference month.",
                                 "Каналы, объясняющие рост месяца по сравнению с эталонным.", "month_drivers_concentration"),
    "month_drivers_sources": _t("Sources qui reçoivent le plus de relais rapides pendant le mois étudié.",
                                "Sources receiving the most fast relays during the studied month.",
                                "Источники, получающие больше всего быстрых пересылок в изучаемом месяце.", "month_drivers_concentration"),
    "month_drivers_summary": _t("Concentration des relais rapides du mois : part des premières chaînes, nombre de chaînes pour la moitié.",
                                "Concentration of the month's fast relays: share of the top channels, number of channels making half.",
                                "Концентрация быстрых пересылок месяца: доля первых каналов, число каналов для половины.", "month_drivers_concentration"),
    "review_candidates": _t("Chaînes à relire à la main, avec titre, source principale, délai, groupe, type, et deux colonnes à remplir.",
                            "Channels to review by hand, with title, top source, delay, group, type, and two columns to fill in.",
                            "Каналы для ручной проверки: название, главный источник, задержка, группа, тип и два столбца для заполнения.", "review_overview"),
    "review_summary": _t("Répartition des chaînes à relire par type et par indicateur.",
                         "Breakdown of the channels to review by type and by indicator.",
                         "Распределение каналов для проверки по типам и индикаторам.", "review_overview"),
}


# ----------------------------------------------------------------- Parquet datasets
def _p(fr, en, ru, unit_fr, unit_en, unit_ru):
    return dict(why=L3(fr, en, ru), unit=L3(unit_fr, unit_en, unit_ru))


PARQUET_INFO: dict[str, dict] = {
    "clean": _p("Messages après nettoyage (types, dates, identifiants). Première étape du pipeline.",
                "Messages after cleaning (types, dates, identifiers). First step of the pipeline.",
                "Сообщения после очистки (типы, даты, идентификаторы). Первый этап конвейера.", "messages", "messages", "сообщений"),
    "clean_dedup": _p("Messages sans doublons : les copies supprimées ne diffèrent que par les vues et les transferts. Base de toutes les tables gold.",
                      "Messages without duplicates: removed copies differ only in views and forwards. Base of every gold table.",
                      "Сообщения без дубликатов: удалённые копии отличаются только просмотрами и пересылками. Основа всех таблиц gold.",
                      "messages", "messages", "сообщений"),
    "chains": _p("Une ligne par relais (origine, destinataire, date, délai, taille de la chaîne). Base des thèmes 1, 3 et 5.",
                 "One row per relay (origin, destination, date, delay, chain size). Base of themes 1, 3 and 5.",
                 "Строка на ретрансляцию (источник, получатель, дата, задержка, размер цепочки). Основа тем 1, 3 и 5.",
                 "relais", "relays", "ретрансляций"),
    "edges_monthly": _p("Transferts canal → canal agrégés par mois. Sert à construire le graphe du thème 1 (communautés).",
                        "Channel → channel forwards aggregated by month. Used to build the theme 1 graph (communities).",
                        "Пересылки канал → канал по месяцам. Для построения графа темы 1 (сообщества).", "arêtes mensuelles", "monthly edges", "месячных рёбер"),
    "channel_stats": _p("Statistiques par canal (transferts reçus, émis…). Sert aux profils et aux thèmes 1 à 3.",
                        "Per-channel statistics (forwards in and out…). Used for profiles and themes 1 to 3.",
                        "Статистика по каналам (входящие и исходящие пересылки…). Для профилей и тем 1–3.", "canaux", "channels", "каналов"),
    "city_daily": _p("Messages par ville et par jour. Sert à détecter les pics du thème 4.",
                     "Messages per city per day. Used to detect the theme 4 peaks.",
                     "Сообщения по городам и дням. Для обнаружения пиков темы 4.", "lignes ville-jour", "city-day rows", "строк город-день"),
    "city_hourly": _p("Messages par ville et par heure. Sert à ordonner la réaction des villes lors d'un pic synchronisé.",
                      "Messages per city per hour. Used to order the cities' reaction during a synchronized peak.",
                      "Сообщения по городам и часам. Для порядка реакции городов при синхронном пике.", "lignes ville-heure", "city-hour rows", "строк город-час"),
    "channel_behavior": _p("Une ligne par chaîne : volume, vues, part de transferts, rapidité, source principale, régularité. Base des indicateurs du thème 5.",
                           "One row per channel: volume, views, share of forwards, speed, top source, regularity. Base of the theme 5 indicators.",
                           "Строка на канал: объём, просмотры, доля пересылок, скорость, главный источник, регулярность. Основа индикаторов темы 5.",
                           "chaînes", "channels", "каналов"),
    "channel_hours": _p("Messages par chaîne et par heure du jour. Sert à l'indicateur de rythme horaire (activité sans pause).",
                        "Messages per channel and hour of day. Used for the hourly-rhythm indicator (activity without a break).",
                        "Сообщения по каналам и часам суток. Для индикатора суточного ритма (активность без пауз).", "lignes chaîne-heure", "channel-hour rows", "строк канал-час"),
    "coordinated_pairs": _p("Paires de chaînes qui relaient le même message à quelques secondes d'écart, avec le nombre de messages communs. Base des groupes coordonnés.",
                            "Pairs of channels relaying the same message seconds apart, with the number of shared messages. Base of the coordinated groups.",
                            "Пары каналов, пересылающих одно сообщение с разницей в секунды, с числом общих сообщений. Основа координированных групп.",
                            "paires", "pairs", "пар"),
    "cascades": _p("Messages d'origine très relayés : nombre de relais, de chaînes, rapidité, relais dans les 10 premières minutes.",
                   "Widely relayed original messages: relays, channels, speed, relays within the first 10 minutes.",
                   "Часто пересылаемые исходные сообщения: число пересылок, каналов, скорость, пересылки в первые 10 минут.", "cascades", "cascades", "каскадов"),
    "forward_speed_monthly": _p("Rapidité des transferts par mois (part en moins de 10 s et 60 s, délai médian). Source de la tendance du thème 5.",
                                "Forwarding speed per month (share within 10 s and 60 s, median delay). Source of the theme 5 trend.",
                                "Скорость пересылок по месяцам (доля за 10 и 60 с, медианная задержка). Источник тренда темы 5.", "mois", "months", "месяцев"),
}


# ----------------------------------------------------------------- figures read from the files
def fmt_bytes(n: float) -> str:
    for u in ("o", "Ko", "Mo", "Go"):
        if n < 1024 or u == "Go":
            return f"{n:.0f} {u}" if u == "o" else f"{n:.1f} {u}"
        n /= 1024
    return ""


def table_stats(d: pd.DataFrame, lang: str, k: int = 3) -> str:
    """Generic result line: rows, columns and the range of the first numeric columns."""
    if d is None or d.empty:
        return ""
    out = [{"fr": f"{num(len(d), lang)} lignes × {len(d.columns)} colonnes",
            "en": f"{num(len(d), lang)} rows × {len(d.columns)} columns",
            "ru": f"{num(len(d), lang)} строк × {len(d.columns)} столбцов"}[lang]]
    nums = [c for c in d.columns if pd.api.types.is_numeric_dtype(d[c]) and not re.search(r"(_id$|^id$|rank|index|group)", str(c), re.I)]
    med = {"fr": "médiane", "en": "median", "ru": "медиана"}[lang]
    for c in nums[:k]:
        v = d[c].dropna().astype(float)
        if len(v):
            out.append(f"{c}: min {dec(v.min(), lang, 2)}, {med} {dec(v.median(), lang, 2)}, max {dec(v.max(), lang, 2)}")
    return " ; ".join(out)


def describe_table(stem: str, lang: str, get_table) -> tuple[str, str, bool]:
    """(why the table was produced, its key figures, documented?) for a CSV stem."""
    info = TABLE_INFO.get(stem)
    d = get_table(stem)
    why = info["why"][lang] if info else ""
    facts = ""
    if info and info.get("facts") and info["facts"] in REGISTRY:
        e = REGISTRY[info["facts"]]
        try:
            facts = e["tpl"][lang].format(**e["facts"](get_table, lang))
        except Exception:
            facts = ""
    return why, facts or table_stats(d, lang), info is not None


def describe_parquet(name: str, lang: str, rows: int | None) -> tuple[str, str, bool]:
    info = PARQUET_INFO.get(name)
    why = info["why"][lang] if info else ""
    res = f"{num(rows, lang)} {info['unit'][lang]}" if (info and rows is not None) else (f"{num(rows, lang)}" if rows is not None else "")
    return why, res, info is not None


# ----------------------------------------------------------------- Parquet access (pyarrow, read lazily)
def discover_parquets(data_dir: Path) -> dict[str, Path]:
    """clean, clean_dedup and every dataset under gold/ that holds Parquet files; key = name shown to the user."""
    found: dict[str, Path] = {}
    if not data_dir.is_dir():
        return found
    cands = [data_dir / "clean", data_dir / "clean_dedup"]
    gold = data_dir / "gold"
    if gold.is_dir():
        cands += sorted(p for p in gold.iterdir() if p.is_dir())
    for p in cands:
        if p.is_dir() and any(p.rglob("*.parquet")):
            found[p.name] = p
    return found


def parquet_info(path: Path) -> dict:
    import pyarrow.dataset as ds
    d = ds.dataset(str(path), format="parquet")
    files = list(d.files)
    return dict(rows=d.count_rows(), columns=[(f.name, str(f.type)) for f in d.schema], n_files=len(files),
                size=sum(Path(f).stat().st_size for f in files))


def parquet_preview(path: Path, n: int = 20) -> pd.DataFrame:
    import pyarrow.dataset as ds
    return ds.dataset(str(path), format="parquet").head(n).to_pandas()


# ----------------------------------------------------------------- formulas of the methods (LaTeX + explanation)
def _f(name, tex, fr, en, ru):
    return dict(name=name, tex=tex, text=L3(fr, en, ru))


def _n(fr, en, ru):
    return L3(fr, en, ru)


FORMULAS: dict[str, list[dict]] = {
    "theme1": [
        dict(name=_n("Modularité (Leiden)", "Modularity (Leiden)", "Модулярность (Leiden)"),
             tex=r"Q=\sum_{c}\left[\frac{w_c}{m}-\gamma\left(\frac{S_c}{2m}\right)^{2}\right]",
             text=_n("Q mesure à quel point les liens restent à l'intérieur des communautés par rapport à un graphe aléatoire de mêmes degrés. "
                     "w_c : poids des liens entre deux canaux de la communauté c ; m : poids total des liens ; S_c : somme des poids des liens "
                     "touchant les canaux de c ; γ : résolution (1 par défaut ; plus γ est grand, plus les communautés sont petites). "
                     "Les poids sont des nombres de transferts, les deux sens étant additionnés. Q proche de 0 : aucune structure ; plus Q est haut, plus les communautés sont nettes.",
                     "Q measures how much links stay inside communities compared with a random graph with the same degrees. "
                     "w_c: weight of links between two channels of community c; m: total link weight; S_c: sum of the weights of links touching "
                     "the channels of c; γ: resolution (1 by default; the larger γ, the smaller the communities). "
                     "Weights are numbers of forwards, both directions added. Q near 0: no structure; the higher Q, the sharper the communities.",
                     "Q показывает, насколько связи остаются внутри сообществ по сравнению со случайным графом с теми же степенями. "
                     "w_c — вес связей между каналами сообщества c; m — общий вес связей; S_c — сумма весов связей каналов c; "
                     "γ — резолюция (по умолчанию 1; чем больше γ, тем мельче сообщества). "
                     "Вес — число пересылок, оба направления суммируются. Q около 0 — структуры нет; чем выше Q, тем чётче сообщества.")),
        dict(name=_n("Part des transferts restée à l'intérieur", "Share of forwards kept inside", "Доля пересылок внутри"),
             tex=r"\text{part interne}=\frac{\text{forwards\_inside}}{\text{forwards\_out}}",
             text=_n("Pour une communauté : transferts émis par ses canaux qui arrivent dans des canaux de la même communauté, divisés par tous ses transferts émis.",
                     "For a community: forwards sent by its channels that land in channels of the same community, divided by all the forwards it sends.",
                     "Для сообщества: пересылки его каналов, попавшие в каналы того же сообщества, делённые на все его исходящие пересылки.")),
        dict(name=_n("Information mutuelle normalisée (NMI)", "Normalized mutual information (NMI)", "Нормализованная взаимная информация (NMI)"),
             tex=r"\mathrm{NMI}(U,V)=\frac{2\,I(U;V)}{H(U)+H(V)},\quad I(U;V)=\sum_{u,v}p(u,v)\log\frac{p(u,v)}{p(u)\,p(v)},\quad H(U)=-\sum_u p(u)\log p(u)",
             text=_n("Compare deux découpages U et V des mêmes canaux (deux années, ou deux graines). 1 = découpages identiques, 0 = indépendants. "
                     "p(u,v) : part des canaux qui sont dans la communauté u de U et v de V ; H : entropie ; I : information partagée.",
                     "Compares two partitions U and V of the same channels (two years, or two seeds). 1 = identical, 0 = independent. "
                     "p(u,v): share of channels in community u of U and v of V; H: entropy; I: shared information.",
                     "Сравнивает два разбиения U и V одних и тех же каналов (два года или два зерна). 1 — одинаковые, 0 — независимые. "
                     "p(u,v) — доля каналов в сообществе u из U и v из V; H — энтропия; I — общая информация.")),
        dict(name=_n("Équation de la carte (Infomap)", "Map equation (Infomap)", "Уравнение карты (Infomap)"),
             tex=r"L(M)=q_{\curvearrowright}H(\mathcal{Q})+\sum_{i}p^{i}_{\circlearrowright}H(\mathcal{P}^{i})",
             text=_n("Longueur moyenne du code décrivant une marche aléatoire sur le graphe orienté : on cherche le découpage M qui la rend la plus courte. "
                     "q : probabilité de changer de communauté ; H(Q) : entropie des communautés visitées ; H(P^i) : entropie des canaux visités dans la communauté i.",
                     "Average code length describing a random walk on the directed graph: we look for the partition M that makes it shortest. "
                     "q: probability of leaving a community; H(Q): entropy of the visited communities; H(P^i): entropy of the channels visited inside community i.",
                     "Средняя длина кода, описывающего случайное блуждание по ориентированному графу: ищем разбиение M, при котором она минимальна. "
                     "q — вероятность выхода из сообщества; H(Q) — энтропия посещаемых сообществ; H(P^i) — энтропия каналов внутри сообщества i.")),
    ],
    "theme2": [
        dict(name=_n("Pureté linguistique d'une communauté", "Language purity of a community", "Языковая чистота сообщества"),
             tex=r"\text{pureté}_c=\frac{\max_{\ell}\,n_{c,\ell}}{k_c}",
             text=_n("n_{c,ℓ} : nombre de canaux de la communauté c dont la langue est ℓ ; k_c : canaux de c dont la langue est connue. "
                     "1 = communauté entièrement dans une langue ; seuls les canaux à langue connue comptent.",
                     "n_{c,ℓ}: number of channels of community c whose language is ℓ; k_c: channels of c with a known language. "
                     "1 = community entirely in one language; only channels with a known language count.",
                     "n_{c,ℓ} — число каналов сообщества c с языком ℓ; k_c — каналы c с известным языком. "
                     "1 — сообщество целиком на одном языке; учитываются только каналы с известным языком.")),
        dict(name=_n("Entropie et nombre effectif de langues", "Entropy and effective number of languages", "Энтропия и эффективное число языков"),
             tex=r"H=-\sum_{\ell}p_\ell\log_2 p_\ell,\qquad N_{\text{eff}}=2^{H}",
             text=_n("p_ℓ : part de la langue ℓ. H est en bits ; N_eff est le nombre de langues d'égal poids qui donnerait la même diversité "
                     "(une seule langue : 1 ; quatre langues à parts égales : 4).",
                     "p_ℓ: share of language ℓ. H is in bits; N_eff is the number of equally weighted languages giving the same diversity "
                     "(one language: 1; four equal languages: 4).",
                     "p_ℓ — доля языка ℓ. H в битах; N_eff — число равноправных языков с тем же разнообразием "
                     "(один язык: 1; четыре равных: 4).")),
        dict(name=_n("Homophilie linguistique et lift", "Language homophily and lift", "Языковая гомофилия и lift"),
             tex=r"h_\ell=\frac{W_{\ell\ell}}{\sum_{m}W_{\ell m}},\qquad e_\ell=\frac{\sum_{m}W_{m\ell}}{W},\qquad \text{lift}_\ell=\frac{h_\ell}{e_\ell}",
             text=_n("W_{ℓm} : transferts d'un canal de langue ℓ vers un canal de langue m ; W : total. h_ℓ : part des transferts de ℓ qui restent en ℓ ; "
                     "e_ℓ : part des transferts qui arrivent en ℓ, soit ce qu'on aurait si la langue du destinataire ne comptait pas ; "
                     "lift > 1 : la langue attire les transferts vers elle-même plus que le hasard.",
                     "W_{ℓm}: forwards from a channel of language ℓ to a channel of language m; W: total. h_ℓ: share of ℓ's forwards that stay in ℓ; "
                     "e_ℓ: share of all forwards landing in ℓ, i.e. what we would get if the receiver's language did not matter; "
                     "lift > 1: forwards stay in their own language more than chance.",
                     "W_{ℓm} — пересылки из канала языка ℓ в канал языка m; W — всего. h_ℓ — доля пересылок ℓ, оставшихся в ℓ; "
                     "e_ℓ — доля всех пересылок, приходящих в ℓ, то есть ожидание, если бы язык получателя не имел значения; "
                     "lift > 1 — пересылки остаются в своём языке чаще, чем случайно.")),
        dict(name=_n("Assortativité par langue", "Language assortativity", "Ассортативность по языку"),
             tex=r"r=\frac{\sum_\ell W_{\ell\ell}/W-\sum_\ell a_\ell b_\ell}{1-\sum_\ell a_\ell b_\ell}",
             text=_n("a_ℓ : part des transferts émis par ℓ ; b_ℓ : part reçue par ℓ. Le numérateur compare la part réellement restée dans la même langue "
                     "à celle attendue au hasard. r = 0 : la langue est ignorée ; r = 1 : les canaux ne relaient que leur propre langue.",
                     "a_ℓ: share of forwards sent by ℓ; b_ℓ: share received by ℓ. The numerator compares the share that really stayed in the same language "
                     "with the share expected by chance. r = 0: language is ignored; r = 1: channels only relay their own language.",
                     "a_ℓ — доля пересылок, отправленных ℓ; b_ℓ — доля полученных ℓ. Числитель сравнивает реальную долю внутри языка "
                     "с ожидаемой случайно. r = 0 — язык игнорируется; r = 1 — каналы пересылают только свой язык.")),
        dict(name=_n("Canaux-ponts", "Bridge channels", "Каналы-мосты"),
             tex=r"\text{cross\_share}=\frac{\text{transferts vers une autre langue}}{\text{transferts avec langues connues}}",
             text=_n("Part des transferts d'un canal qui franchissent une frontière de langue, parmi ceux dont les deux langues sont connues.",
                     "Share of a channel's forwards that cross a language boundary, among those whose two languages are known.",
                     "Доля пересылок канала, пересекающих языковую границу, среди тех, где известны оба языка.")),
        dict(name=_n("Langue déduite par vote des voisins", "Language inferred by neighbour vote", "Язык по голосованию соседей"),
             tex=r"V_{i,\ell}=\sum_{j}\left(A_{ij}+A_{ji}\right)\mathbf{1}\left[\text{langue}(j)=\ell\right],\quad \hat\ell_i=\arg\max_\ell V_{i,\ell},\quad s_i=\frac{\max_\ell V_{i,\ell}}{\sum_\ell V_{i,\ell}}",
             text=_n("A_{ij} : transferts du canal i vers j. Chaque voisin à langue connue vote pour sa langue avec le poids des transferts échangés ; "
                     "on retient la langue gagnante si sa part s_i atteint le seuil (0,6 par défaut). L'exactitude est mesurée en cachant 10 % des langues connues.",
                     "A_{ij}: forwards from channel i to j. Each neighbour with a known language votes for its language with the weight of forwards exchanged; "
                     "the winning language is kept when its share s_i reaches the threshold (0.6 by default). Accuracy is measured by hiding 10% of known languages.",
                     "A_{ij} — пересылки из канала i в j. Каждый сосед с известным языком голосует за свой язык с весом обменянных пересылок; "
                     "побеждающий язык принимается, если его доля s_i достигает порога (по умолчанию 0,6). Точность измеряется скрытием 10 % известных языков.")),
    ],
    "theme3": [
        dict(name=_n("Délai de relais", "Relay delay", "Задержка пересылки"),
             tex=r"\Delta=t_{\text{relais}}-t_{\text{origine}}",
             text=_n("Secondes entre la publication d'origine et le relais ; seuls les délais positifs ou nuls sont gardés. "
                     "Les classes de délai et la médiane par année sont calculées sur Δ.",
                     "Seconds between the original post and the relay; only delays that are zero or positive are kept. "
                     "Delay classes and the yearly median are computed on Δ.",
                     "Секунды между исходным постом и пересылкой; сохраняются только неотрицательные задержки. "
                     "Классы задержек и медиана по годам считаются по Δ.")),
        dict(name=_n("Concentration des sources", "Source concentration", "Концентрация источников"),
             tex=r"C(k)=\frac{\sum_{i=1}^{k}r_{(i)}}{\sum_i r_i}",
             text=_n("r_i : nombre de relais obtenus par la source i ; r_(1) ≥ r_(2) ≥ … : sources classées de la plus à la moins relayée. "
                     "C(k) est la part des relais détenue par les k premières sources ; plus la courbe monte vite, plus les relais sont concentrés.",
                     "r_i: number of relays obtained by source i; r_(1) ≥ r_(2) ≥ …: sources ranked from most to least relayed. "
                     "C(k) is the share of relays held by the top k sources; the faster the curve rises, the more concentrated the relays.",
                     "r_i — число пересылок источника i; r_(1) ≥ r_(2) ≥ … — источники от самого пересылаемого. "
                     "C(k) — доля пересылок у k первых источников; чем быстрее растёт кривая, тем выше концентрация.")),
        dict(name=_n("Part de relais dans un délai donné", "Share of relays within a given delay", "Доля пересылок в пределах задержки"),
             tex=r"P(\Delta\le d)=\frac{\#\{\text{relais avec }\Delta\le d\}}{\#\{\text{relais}\}}",
             text=_n("Par exemple d = 1 jour pour la part « en moins d'un jour » de l'évolution par année.",
                     "For example d = 1 day for the 'within a day' share of the yearly evolution.",
                     "Например, d = 1 день для доли «в пределах суток» в динамике по годам.")),
    ],
    "theme4": [
        dict(name=_n("Score d'anomalie d'une ville un jour donné", "Anomaly score of a city on a given day", "Показатель аномальности города за день"),
             tex=r"y_t=\log(1+n_t)-w_{d(t)},\qquad z_t=\frac{y_t-b_t}{\sigma_t},\qquad b_t=\operatorname{med}(y_{t-56..t-1}),\qquad \sigma_t=\max\!\big(1.4826\cdot\operatorname{med}|y_s-b_s|_{s=t-56..t-1},\;0.15\big)",
             text=_n("n_t : messages de la ville le jour t. On passe au log pour que les grandes villes ne dominent pas, puis on retire l'effet du jour de la semaine w_d "
                     "(médiane du jour de semaine moins médiane globale). b_t est le niveau habituel (médiane des 56 jours précédents) et σ_t l'écart habituel "
                     "(1,4826 × écart absolu médian, avec un plancher de 0,15 pour ne pas diviser par presque zéro). Un jour est en pic quand z_t ≥ 4 et qu'il y a "
                     "au moins 20 messages (valeurs par défaut du script).",
                     "n_t: the city's messages on day t. We take the log so that big cities do not dominate, then remove the weekday effect w_d "
                     "(weekday median minus overall median). b_t is the usual level (median of the previous 56 days) and σ_t the usual spread "
                     "(1.4826 × median absolute deviation, floored at 0.15 to avoid dividing by almost zero). A day is a peak when z_t ≥ 4 and there are "
                     "at least 20 messages (script defaults).",
                     "n_t — сообщения города в день t. Берётся логарифм, чтобы крупные города не доминировали, затем убирается эффект дня недели w_d "
                     "(медиана дня недели минус общая медиана). b_t — обычный уровень (медиана 56 предыдущих дней), σ_t — обычный разброс "
                     "(1,4826 × медианное абсолютное отклонение, не ниже 0,15, чтобы не делить почти на ноль). День — пик, если z_t ≥ 4 и сообщений "
                     "не меньше 20 (значения по умолчанию).")),
        dict(name=_n("Épisodes et forme", "Episodes and shape", "Эпизоды и форма"),
             tex=r"\text{forme}=\begin{cases}\text{bref}&n\le 2\\ \text{court}&3\le n\le 7\\ \text{prolongé}&n>7\end{cases}",
             text=_n("Des jours de pic consécutifs (un trou d'un jour est toléré) forment un épisode de n jours ; sa forme dépend de sa durée.",
                     "Consecutive peak days (a one-day gap is tolerated) form an episode of n days; its shape depends on its duration.",
                     "Подряд идущие дни пика (допускается пропуск в один день) образуют эпизод из n дней; его форма зависит от длительности.")),
        dict(name=_n("Pic synchronisé et pic « global »", "Synchronized peak and 'global' peak", "Синхронный пик и «глобальный» пик"),
             tex=r"\#\{\text{villes en pic le jour }t\}\ge 3\quad\Rightarrow\quad\text{pic synchronisé};\qquad \frac{\max_t\#\{\text{villes en pic}\}}{\#\{\text{villes}\}}>s\quad\Rightarrow\quad\text{global}",
             text=_n("Un pic synchronisé regroupe les jours où au moins 3 villes sont en pic ensemble. Il est marqué « global » quand la part de villes en pic dépasse un seuil s : "
                     "c'est souvent une lacune de collecte ou un effet de toute la plateforme, pas un phénomène de ville.",
                     "A synchronized peak groups the days when at least 3 cities peak together. It is flagged 'global' when the share of cities in a peak exceeds a threshold s: "
                     "this is often a collection gap or a platform-wide effect, not a city-level phenomenon.",
                     "Синхронный пик объединяет дни, когда в пике одновременно не менее 3 городов. Он помечается «глобальным», если доля городов в пике превышает порог s: "
                     "чаще всего это пропуск в сборе или эффект всей платформы, а не городское явление.")),
        dict(name=_n("Heure de début dans une ville", "Onset hour in a city", "Час начала в городе"),
             tex=r"\text{seuil}_h=\max\!\big(3\,\beta_h,\;\beta_h+5\big),\qquad \beta_h=\operatorname{med}\{n_{h-168j}\}_{j=1..4}",
             text=_n("n_h : messages de l'heure h. β_h est le niveau habituel : médiane de la même heure du même jour de semaine des 4 semaines précédentes. "
                     "L'heure de début d'une ville est la première heure où le seuil est dépassé deux heures de suite ; "
                     "la ville au début le plus tôt est la première à réagir, et l'écart entre villes se mesure en heures.",
                     "n_h: messages in hour h. β_h is the usual level: median of the same hour of the same weekday over the 4 previous weeks. "
                     "A city's onset is the first hour where the threshold is exceeded two hours in a row; "
                     "the city with the earliest onset reacts first, and the gap between cities is measured in hours.",
                     "n_h — сообщения в час h. β_h — обычный уровень: медиана того же часа того же дня недели за 4 предыдущие недели. "
                     "Начало в городе — первый час, когда порог превышен два часа подряд; "
                     "город с самым ранним началом реагирует первым, разрыв между городами измеряется в часах.")),
        dict(name=_n("Corrélation décalée entre villes", "Lagged correlation between cities", "Корреляция городов со сдвигом"),
             tex=r"\rho_{ab}(\ell)=\frac{1}{T-|\ell|}\sum_t \tilde z_a(t)\,\tilde z_b(t+\ell),\qquad \ell\in\{-3,\dots,3\},\qquad \ell^{*}=\arg\max_\ell\rho_{ab}(\ell)",
             text=_n("z̃ : score d'anomalie positif (borné à 10) puis centré et réduit. ρ est la corrélation entre les villes a et b quand b est décalée de ℓ jours ; "
                     "ℓ* > 0 signifie que b réagit ℓ jours après a. Une paire n'est gardée que si ρ(ℓ*) ≥ 0,2.",
                     "z̃: positive anomaly score (capped at 10), then centred and scaled. ρ is the correlation between cities a and b when b is shifted by ℓ days; "
                     "ℓ* > 0 means b reacts ℓ days after a. A pair is kept only if ρ(ℓ*) ≥ 0.2.",
                     "z̃ — положительный показатель аномальности (не выше 10), центрированный и нормированный. ρ — корреляция городов a и b при сдвиге b на ℓ дней; "
                     "ℓ* > 0 означает, что b реагирует через ℓ дней после a. Пара сохраняется только при ρ(ℓ*) ≥ 0,2.")),
    ],
    "theme5": [
        dict(name=_n("Délai et part de relais instantanés", "Delay and share of instant relays", "Задержка и доля мгновенных пересылок"),
             tex=r"\Delta=t-t_{\text{origine}},\qquad f_{10}=\frac{\#\{\Delta\le 10\ \text{s}\}}{n_{\text{transferts}}}",
             text=_n("f_10 : part des transferts d'une chaîne relayés moins de 10 secondes après le message d'origine. "
                     "Le même calcul sur tous les transferts d'un mois donne la tendance mensuelle.",
                     "f_10: share of a channel's forwards relayed less than 10 seconds after the original message. "
                     "The same computation over all forwards of a month gives the monthly trend.",
                     "f_10 — доля пересылок канала менее чем через 10 секунд после исходного сообщения. "
                     "Тот же расчёт по всем пересылкам месяца даёт месячный тренд.")),
        dict(name=_n("Source unique", "Single source", "Единственный источник"),
             tex=r"\text{top\_origin\_share}=\frac{\max_o n_o}{n_{\text{transferts}}}\ \ge 0{,}9",
             text=_n("n_o : transferts de la chaîne venant de la source o. Une valeur proche de 1 : la chaîne ne relaie presque qu'un seul canal.",
                     "n_o: the channel's forwards coming from source o. A value near 1: the channel relays almost a single channel.",
                     "n_o — пересылки канала из источника o. Значение около 1: канал пересылает почти один канал.")),
        dict(name=_n("Régularité du rythme horaire", "Regularity of the hourly rhythm", "Равномерность суточного ритма"),
             tex=r"H_{24}=-\frac{1}{\ln 24}\sum_{h=0}^{23}p_h\ln p_h",
             text=_n("p_h : part des messages publiés à l'heure h (UTC). H_24 vaut 1 si la chaîne publie autant à toutes les heures (activité sans pause, comme une machine) "
                     "et se rapproche de 0 si elle publie à quelques heures seulement.",
                     "p_h: share of messages posted in hour h (UTC). H_24 equals 1 if the channel posts equally in every hour (activity without a break, like a machine) "
                     "and approaches 0 if it posts in only a few hours.",
                     "p_h — доля сообщений в час h (UTC). H_24 равна 1, если канал публикует поровну во все часы (активность без пауз, как у машины), "
                     "и близка к 0, если публикации только в несколько часов.")),
        dict(name=_n("Seconde fixe et rafales", "Fixed second and bursts", "Фиксированная секунда и всплески"),
             tex=r"\text{sec\_mode\_share}=\frac{\max_{s\in[0,59]}n_s}{n_{\text{messages}}},\qquad \text{burst}=\frac{\max_j n_j}{\max(1,\operatorname{med}_j n_j)}",
             text=_n("n_s : messages publiés à la seconde s de la minute (attendu : environ 1/60 si les secondes sont aléatoires). "
                     "n_j : messages du jour j ; un rapport élevé entre le jour le plus chargé et le jour médian signale des rafales.",
                     "n_s: messages posted at second s of the minute (expected: about 1/60 if seconds are random). "
                     "n_j: messages of day j; a high ratio between the busiest day and the median day signals bursts.",
                     "n_s — сообщения, опубликованные на секунде s минуты (ожидаемо около 1/60 при случайных секундах). "
                     "n_j — сообщения дня j; большое отношение самого загруженного дня к медианному означает всплески.")),
        dict(name=_n("Écart de vues (z robuste)", "Views gap (robust z)", "Разрыв просмотров (робастный z)"),
             tex=r"z=\frac{x-\operatorname{med}(x)}{1.4826\cdot\operatorname{MAD}(x)},\qquad \log(1+\bar v)=\beta_0+\beta_1\log(1+n_{\text{reçus}})+\beta_2\log(1+n_{\text{posts}})+\varepsilon",
             text=_n("On explique les vues moyennes par la portée de la chaîne (transferts reçus) et son volume de messages, puis on calcule le z robuste du résidu ε "
                     "(MAD : écart absolu médian ; 1,4826 le rend comparable à un écart-type). |z| ≥ 4 : les vues sont très éloignées de ce que prévoient portée et volume.",
                     "Mean views are explained by the channel's reach (forwards received) and its message volume, then the robust z of the residual ε is computed "
                     "(MAD: median absolute deviation; 1.4826 makes it comparable to a standard deviation). |z| ≥ 4: views are far from what reach and volume predict.",
                     "Средние просмотры объясняются охватом канала (полученные пересылки) и числом сообщений, затем считается робастный z остатка ε "
                     "(MAD — медианное абсолютное отклонение; 1,4826 делает его сопоставимым со стандартным отклонением). |z| ≥ 4: просмотры сильно отличаются от ожидаемых по охвату и объёму.")),
        dict(name=_n("Règle de seuil par quantile", "Quantile threshold rule", "Правило порога по квантилю"),
             tex=r"\text{indicateur}=\mathbf{1}\!\left[x>Q_{0.99}(x)\ \wedge\ x\ge x_{\min}\right]",
             text=_n("Pour les mesures continues, une chaîne est signalée si sa valeur dépasse strictement le quantile 99 % de la population éligible ET un plancher x_min. "
                     "Le « strictement » évite de signaler tout le monde quand beaucoup de chaînes ont la même valeur. "
                     "Le seuil réellement utilisé est dans la colonne « threshold » du tableau des indicateurs.",
                     "For continuous measures, a channel is flagged if its value strictly exceeds the 99% quantile of the eligible population AND a floor x_min. "
                     "'Strictly' prevents flagging everybody when many channels share the same value. "
                     "The threshold really used is in the 'threshold' column of the indicator table.",
                     "Для непрерывных показателей канал отмечается, если значение строго выше 99-го процентиля допустимой совокупности И выше нижней границы x_min. "
                     "«Строго» не даёт отметить всех, когда у многих каналов одинаковое значение. "
                     "Реально использованный порог указан в столбце «threshold» таблицы индикаторов.")),
        dict(name=_n("Indicateurs à seuil fixe", "Fixed-threshold indicators", "Индикаторы с фиксированным порогом"),
             tex=r"\text{relais pur}:\ \frac{n_{\text{transferts}}}{n_{\text{posts}}}\ge 0{,}99;\quad \text{délai régulier}:\ P_{75}(\Delta)-P_{25}(\Delta)\le 10\ \text{s};\quad \text{débit}:\ \operatorname{med}_j n_j\ge 1000",
             text=_n("Seuils ronds, pas des quantiles, et non validés. Relais pur : presque tout ce que publie la chaîne est un transfert. "
                     "Délai régulier : l'écart interquartile du délai est très petit (le relais suit toujours la source au même rythme). "
                     "Débit : plus de 1 000 messages par jour actif (médiane). Valeurs par défaut modifiables par option du script.",
                     "Round thresholds, not quantiles, and not validated. Pure relay: almost everything the channel posts is a forward. "
                     "Regular delay: the interquartile range of the delay is very small (the relay always follows the source at the same pace). "
                     "Throughput: more than 1,000 messages per active day (median). Default values can be changed with a script option.",
                     "Круглые пороги, а не квантили, и не проверены. Чистая пересылка: почти всё, что публикует канал, — пересылки. "
                     "Ровная задержка: межквартильный размах задержки очень мал (пересылка всегда следует за источником в одном ритме). "
                     "Пропускная способность: более 1000 сообщений в активный день (медиана). Значения по умолчанию меняются опцией скрипта.")),
        dict(name=_n("Paires et groupes coordonnés", "Coordinated pairs and groups", "Координированные пары и группы"),
             tex=r"|t_a-t_b|\le 60\ \text{s}\ \text{sur}\ \ge 5\ \text{messages d'origine distincts}\;\Rightarrow\;\text{paire},\qquad \text{densité}=\frac{2E}{n(n-1)}",
             text=_n("Pour chaque message d'origine, les relais sont triés par heure ; chaque relais est apparié aux 5 suivants s'ils le suivent de 60 secondes au plus. "
                     "Une paire est gardée si elle porte sur au moins 5 messages d'origine distincts. Les groupes sont les composantes connexes de ces paires, "
                     "découpées en relevant le seuil quand elles sont trop grandes. La densité compare le nombre de paires E d'un groupe de n chaînes au maximum possible : "
                     "1 = toutes les chaînes du groupe sont coordonnées deux à deux ; un groupe est dit serré quand sa densité est élevée (0,5 par défaut).",
                     "For each original message, relays are sorted by time; each relay is paired with the next 5 if they follow within 60 seconds. "
                     "A pair is kept if it covers at least 5 distinct original messages. Groups are the connected components of these pairs, "
                     "split by raising the threshold when they are too large. Density compares the number of pairs E of a group of n channels with the maximum possible: "
                     "1 = every channel of the group is coordinated with every other; a group is tight when its density is high (0.5 by default).",
                     "Для каждого исходного сообщения пересылки сортируются по времени; каждая пересылка сопоставляется со следующими 5, если они идут не позже чем через 60 секунд. "
                     "Пара сохраняется, если охватывает не менее 5 различных исходных сообщений. Группы — компоненты связности этих пар, "
                     "разделяемые повышением порога, когда они слишком велики. Плотность сравнивает число пар E в группе из n каналов с максимально возможным: "
                     "1 — каждый канал группы скоординирован с каждым; группа плотная при высокой плотности (по умолчанию 0,5).")),
        dict(name=_n("Score", "Score", "Балл"),
             tex=r"\text{score}=\sum_{k}\mathbf{1}[\text{indicateur}_k]=\text{score}_{\text{comportement}}+\text{score}_{\text{coordination}}",
             text=_n("Nombre d'indicateurs déclenchés par une chaîne. Les indicateurs se recoupent (un relais très rapide a presque toujours un délai régulier) : "
                     "le score sert à trier les chaînes à relire, pas à mesurer une gravité.",
                     "Number of indicators triggered by a channel. The indicators overlap (a very fast relay almost always has a regular delay): "
                     "the score sorts the channels to review, it does not measure seriousness.",
                     "Число сработавших индикаторов канала. Индикаторы пересекаются (очень быстрая пересылка почти всегда имеет ровную задержку): "
                     "балл служит для сортировки каналов к проверке, а не для оценки серьёзности.")),
        dict(name=_n("Cascade concentrée", "Concentrated cascade", "Концентрированный каскад"),
             tex=r"\frac{n_{\text{relais dans les 10 premières minutes}}}{n_{\text{relais}}}\ge 0{,}8",
             text=_n("Un message d'origine avec au moins 10 relais est une cascade ; elle est concentrée si au moins 80 % de ses relais arrivent dans les 10 minutes qui suivent le premier.",
                     "An original message with at least 10 relays is a cascade; it is concentrated if at least 80% of its relays arrive within 10 minutes of the first.",
                     "Исходное сообщение с не менее чем 10 пересылками — каскад; он концентрированный, если не менее 80 % пересылок приходится на 10 минут после первой.")),
        dict(name=_n("Origine de la hausse d'un mois", "Source of a month's rise", "Источник роста за месяц"),
             tex=r"e_c=F_c(\text{mois})-F_c(\text{référence}),\qquad S(k)=\frac{\sum_{i=1}^{k}F_{(i)}}{\sum_c F_c}",
             text=_n("F_c : nombre de relais rapides (≤ 10 s) produits par la chaîne c. e_c est l'excédent de c par rapport au mois de référence ; "
                     "S(k) est la part des relais rapides du mois produite par les k chaînes les plus actives, et l'on cherche le plus petit k qui atteint 50 %.",
                     "F_c: number of fast relays (≤ 10 s) made by channel c. e_c is c's excess over the reference month; "
                     "S(k) is the share of the month's fast relays made by the k most active channels, and we look for the smallest k reaching 50%.",
                     "F_c — число быстрых пересылок (≤ 10 с) канала c. e_c — превышение c над эталонным месяцем; "
                     "S(k) — доля быстрых пересылок месяца, приходящаяся на k самых активных каналов; ищется наименьшее k, дающее 50 %.")),
    ],
}


# ----------------------------------------------------------------- suspicion levels (theme 5)
LEVEL_NAMES = {"fr": {"high": "élevé", "medium": "moyen", "low": "faible"},
               "en": {"high": "high", "medium": "medium", "low": "low"},
               "ru": {"high": "высокий", "medium": "средний", "low": "низкий"}}


def suspicion_level(score, medium: int = 2, high: int = 3) -> str:
    """Level of suspicion from the number of triggered indicators: 'high' from `high`, 'medium' from `medium`, else 'low'."""
    s = 0 if pd.isna(score) else float(score)
    return "high" if s >= high else ("medium" if s >= medium else "low")


def flagged_channels(sus: pd.DataFrame, review: pd.DataFrame | None, lang: str, medium: int = 2, high: int = 3) -> pd.DataFrame:
    """Flagged channels with their level of suspicion, the indicators that fired and, when known, title and type."""
    d = sus.copy()
    d["level_key"] = d["score"].map(lambda s: suspicion_level(s, medium, high))
    d["level"] = d["level_key"].map(LEVEL_NAMES[lang])
    if review is not None and "channel_id" in review:
        extra = [c for c in ("title", "username", "kind") if c in review.columns]
        d = d.merge(review[["channel_id"] + extra].drop_duplicates("channel_id"), on="channel_id", how="left")
    order = {"high": 0, "medium": 1, "low": 2}
    d = d.assign(_o=d["level_key"].map(order)).sort_values(["_o", "score"], ascending=[True, False]).drop(columns="_o")
    cols = [c for c in ("channel_id", "title", "username", "level", "score", "score_behaviour", "score_coordination",
                        "reasons", "n_posts", "n_forwarded", "kind", "level_key") if c in d.columns]
    return d[cols].reset_index(drop=True)