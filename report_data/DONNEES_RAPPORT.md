
# Données collectées pour le rapport

Généré automatiquement par collect_report_data.py : environnement, journaux de temps, volumes, tables de chaque thème (premières lignes), figures, extraits de code.


# Machine et environnement

```
date: 2026-11-26T12:47:29+03:00
os: Linux-6.12.111+deb13-amd64-x86_64-with-glibc2.41
cpu: Intel(R) Core(TM) i7-6600U CPU @ 2.60GHz ; coeurs: 4
ram: Mem:           7.6Gi       6.0Gi       570Mi       635Mi       2.0Gi       1.6Gi
disque projet: total,  libres
python: 3.13.5
java: openjdk version "21.0.12.1" 2026-08-18
docker: Docker version 26.1.5+dfsg1, build a72d7cd
pyspark: 4.3.0
---- .env ----
# Copy to .env and adapt (docker compose reads .env automatically). Never commit .env.
# Folder holding the raw messages (JSONL files or ZIP archives); mounted read-only.
RAW_DIR=/media/0EFC061CFC05FF29/telescope_raw
# Spark temporary files: internal disk, several tens of GB free.
SPARK_TMP=/home/dvopssl/spark_tmp
# Resources given to Spark (same defaults as the project: 3 cores, 4 GB).
TELESCOPE_CORES=3
TELESCOPE_SPARK_MEMORY=4g
# Must match `python3 --version` of the environment that produced requirements.lock (your .venv uses 3.13).
PYTHON_VERSION=3.13
# Your user and group ids (run `id -u` and `id -g`), so output files are yours. `make build` sets them for you.
HOST_UID=1000
HOST_GID=1000
```


# Pipeline : volumes et journaux (temps d'exécution)


### telescope_pipeline_files/clean_log.csv  (25 lignes, 7 colonnes)

| batch | files | messages_ok | bad_json | skipped | gb_read | seconds |
|---|---|---|---|---|---|---|
| 1625754907_to_1677378798 | 3974 | 8642185 | 0 | 10802 | 23.33 | 841 |
| 1677440310_to_1731205486 | 4277 | 8426538 | 0 | 12088 | 22.91 | 784 |
| 1731206105_to_1762981965 | 2768 | 8643330 | 0 | 23561 | 23.1 | 490 |
| 1762989759_to_1778345773 | 1776 | 9145881 | 0 | 65187 | 23.13 | 476 |
| 1778346527_to_1792456646 | 1606 | 8965931 | 0 | 34390 | 22.81 | 461 |
| 1792460600_to_1826619557 | 2468 | 9334834 | 0 | 59096 | 23.53 | 492 |
| 1826634808_to_1877649970 | 3199 | 10627237 | 0 | 80205 | 24.16 | 556 |
| 1877677892_to_1961731638 | 4194 | 9941023 | 0 | 58264 | 23.43 | 540 |
| 1961746451_to_2174838182 | 5975 | 6896230 | 0 | 43358 | 15.23 | 391 |
| 1000015666_to_1054523330 | 1428 | 8537649 | 0 | 12830 | 24.01 | 1193 |
| 1054549314_to_1092663584 | 1438 | 8615224 | 0 | 12492 | 23.26 | 1311 |
| 1092691131_to_1124443753 | 1794 | 7499655 | 0 | 22206 | 22.4 | 978 |
| 1124469578_to_1147333336 | 1632 | 8150899 | 0 | 14371 | 23.18 | 1215 |
| 1147336903_to_1180665618 | 2416 | 7916657 | 0 | 12677 | 22.97 | 1048 |
| 1180680018_to_1219762447 | 2866 | 8251132 | 0 | 18467 | 23.04 | 1259 |
| 1219766382_to_1255194806 | 2600 | 7791256 | 0 | 16602 | 23.23 | 1254 |
| 1255195746_to_1291104162 | 2678 | 7914642 | 0 | 11929 | 22.85 | 1237 |
| 1291116365_to_1325779356 | 2649 | 8084019 | 0 | 12403 | 23.13 | 1326 |
| 1325786124_to_1364416179 | 2859 | 8155201 | 0 | 21372 | 22.83 | 1218 |
| 1364421816_to_1397037295 | 2415 | 7344651 | 0 | 20645 | 23.33 | 1274 |
| 1397113490_to_1436310453 | 2763 | 7690834 | 0 | 16574 | 22.63 | 1233 |
| 1436320749_to_1469586346 | 2489 | 7116244 | 0 | 14520 | 22.56 | 1307 |
| 1469592192_to_1508140759 | 2756 | 7798725 | 0 | 14233 | 23.36 | 1161 |
| 1508149386_to_1568817860 | 4016 | 8647495 | 0 | 11429 | 22.97 | 1008 |
| 1568821876_to_1625726066 | 4038 | 8434418 | 0 | 12823 | 22.45 | 1375 |


### telescope_pipeline_files/clean_trial_log.csv  (1 lignes, 7 colonnes)

| batch | files | messages_ok | bad_json | skipped | gb_read | seconds |
|---|---|---|---|---|---|---|
| 1625754907_to_1677378798 | 50 | 403471 | 0 | 43 | 1.02 | 64 |


### telescope_pipeline_files/dedup_log.csv  (1 lignes, 3 colonnes)

| messages_before | messages_after | copies_removed |
|---|---|---|
| 208571890 | 185969648 | 22602242 |


### telescope_pipeline_files/dedup_report.csv  (10 lignes, 2 colonnes)

| measure | value |
|---|---|
| duplicated_keys | 11116377 |
| extra_copies | 22602242 |
| ts | 0 |
| views | 8318795 |
| forwards | 1011844 |
| kind | 0 |
| origin_channel | 0 |
| origin_post | 0 |
| origin_ts | 0 |
| batch | 0 |


## Tailles des dossiers de données

```
telescope_pipeline_files/clean  2.4G
telescope_pipeline_files/clean/batch=1000015666_to_1054523330  100M
telescope_pipeline_files/clean/batch=1054549314_to_1092663584  114M
telescope_pipeline_files/clean/batch=1092691131_to_1124443753  97M
telescope_pipeline_files/clean/batch=1124469578_to_1147333336  105M
telescope_pipeline_files/clean/batch=1147336903_to_1180665618  99M
telescope_pipeline_files/clean/batch=1180680018_to_1219762447  102M
telescope_pipeline_files/clean/batch=1219766382_to_1255194806  99M
telescope_pipeline_files/clean/batch=1255195746_to_1291104162  98M
telescope_pipeline_files/clean/batch=1291116365_to_1325779356  104M
telescope_pipeline_files/clean/batch=1325786124_to_1364416179  100M
telescope_pipeline_files/clean/batch=1364421816_to_1397037295  91M
telescope_pipeline_files/clean/batch=1397113490_to_1436310453  95M
telescope_pipeline_files/clean/batch=1436320749_to_1469586346  89M
telescope_pipeline_files/clean/batch=1469592192_to_1508140759  96M
telescope_pipeline_files/clean/batch=1508149386_to_1568817860  94M
telescope_pipeline_files/clean/batch=1568821876_to_1625726066  94M
telescope_pipeline_files/clean/batch=1625754907_to_1677378798  92M
telescope_pipeline_files/clean/batch=1677440310_to_1731205486  91M
telescope_pipeline_files/clean/batch=1731206105_to_1762981965  95M
telescope_pipeline_files/clean/batch=1762989759_to_1778345773  107M
telescope_pipeline_files/clean/batch=1778346527_to_1792456646  103M
telescope_pipeline_files/clean/batch=1792460600_to_1826619557  107M
telescope_pipeline_files/clean/batch=1826634808_to_1877649970  116M
telescope_pipeline_files/clean/batch=1877677892_to_1961731638  107M
telescope_pipeline_files/clean/batch=1961746451_to_2174838182  71M
telescope_pipeline_files/clean_dedup  2.9G
telescope_pipeline_files/clean_log.csv  0.0 MB
telescope_pipeline_files/clean_trial  4.4M
telescope_pipeline_files/clean_trial/batch=1625754907_to_1677378798  4.4M
telescope_pipeline_files/clean_trial_log.csv  0.0 MB
telescope_pipeline_files/dedup_log.csv  0.0 MB
telescope_pipeline_files/dedup_report.csv  0.0 MB
telescope_pipeline_files/gold  1.2G
telescope_pipeline_files/gold/cascades  3.2M
telescope_pipeline_files/gold/chains  896M
telescope_pipeline_files/gold/channel_behavior  5.0M
telescope_pipeline_files/gold/channel_hours  3.6M
telescope_pipeline_files/gold/channel_stats  2.9M
telescope_pipeline_files/gold/channel_stats_csv  5.1M
telescope_pipeline_files/gold/city_daily  1.6M
telescope_pipeline_files/gold/city_daily_csv  5.1M
telescope_pipeline_files/gold/city_hourly  9.3M
telescope_pipeline_files/gold/coordinated_pairs  636K
telescope_pipeline_files/gold/edges_monthly  45M
telescope_pipeline_files/gold/edges_monthly_csv  213M
telescope_pipeline_files/gold/forward_speed_monthly  40K
telescope_pipeline_files/gold_with_duplicates  1.2G
telescope_pipeline_files/gold_with_duplicates/chains  930M
telescope_pipeline_files/gold_with_duplicates/channel_stats  2.9M
telescope_pipeline_files/gold_with_duplicates/channel_stats_csv  5.2M
telescope_pipeline_files/gold_with_duplicates/edges_monthly  45M
telescope_pipeline_files/gold_with_duplicates/edges_monthly_csv  213M
```


## Fichiers sources (jeu de données d'origine)

```
telescope_files/Aggregated_User_Interactions.csv  1822.9 MB
telescope_files/Channel_Language.csv  1.5 MB
telescope_files/Message_Forwarding_Flows.csv  1573.1 MB
telescope_files/Source_Channel_Metadata.csv  518.6 MB
telescope_files/Temporal_Channel_Metadata.csv  5.8 MB
telescope_files/channel_to_channel_graph.csv  266.2 MB
```


## Tables gold et données nettoyées : schéma et nombre de lignes (Parquet)


### telescope_pipeline_files/clean  (Parquet, 208571890 lignes)

| colonne | type |
|---|---|
| dest_channel | int64 |
| msg_id | int64 |
| ts | int64 |
| views | int64 |
| forwards | int64 |
| kind | string |
| origin_channel | int64 |
| origin_post | int64 |
| origin_ts | int64 |


### telescope_pipeline_files/clean_dedup  (Parquet, 185969648 lignes)

| colonne | type |
|---|---|
| dest_channel | int64 |
| msg_id | int64 |
| ts | int64 |
| views | int64 |
| forwards | int64 |
| kind | string |
| origin_channel | int64 |
| origin_post | int64 |
| origin_ts | int64 |
| batch | string |


### telescope_pipeline_files/gold/cascades  (Parquet, 157483 lignes)

| colonne | type |
|---|---|
| origin_channel | int64 |
| origin_post | int64 |
| n_relays | int64 |
| n_channels | int64 |
| first_delay_s | int64 |
| n_first10min | int64 |
| span_s | int64 |
| month | string |


### telescope_pipeline_files/gold/chains  (Parquet, 31705915 lignes)

| colonne | type |
|---|---|
| origin_channel | int64 |
| origin_post | int64 |
| origin_date | string |
| rank | int32 |
| dest_channel | int64 |
| dest_msg | int64 |
| date | string |
| delay_s | int64 |
| n_relays | int64 |


### telescope_pipeline_files/gold/channel_behavior  (Parquet, 69909 lignes)

| colonne | type |
|---|---|
| channel_id | int64 |
| n_posts | int64 |
| views_mean | double |
| views_median | int64 |
| zero_view_share | double |
| forwards_mean | double |
| n_active_days | int64 |
| max_posts_day | int64 |
| median_posts_day | int64 |
| n_forwarded | int64 |
| n_origins | int64 |
| share_fast10 | double |
| share_fast60 | double |
| median_delay_s | int64 |
| delay_p25_s | int64 |
| delay_p75_s | int64 |
| top_origin_share | double |
| sec_mode_share | double |


### telescope_pipeline_files/gold/channel_hours  (Parquet, 1361450 lignes)

| colonne | type |
|---|---|
| channel_id | int64 |
| hour | int32 |
| n_posts | int64 |


### telescope_pipeline_files/gold/channel_stats  (Parquet, 70965 lignes)

| colonne | type |
|---|---|
| channel_id | int64 |
| n_messages | int64 |
| n_forwarded_in | int64 |
| n_forwarded_in_from_channels | int64 |
| total_views | int64 |
| total_forwards | int64 |
| first_date | string |
| last_date | string |


### telescope_pipeline_files/gold/city_daily  (Parquet, 123077 lignes)

| colonne | type |
|---|---|
| country | string |
| city | string |
| date | date32[day] |
| n_posts | int64 |
| n_forwarded_posts | int64 |
| views | int64 |
| n_channels | int64 |


### telescope_pipeline_files/gold/city_hourly  (Parquet, 1776492 lignes)

| colonne | type |
|---|---|
| country | string |
| city | string |
| hour | timestamp[ns] |
| n_posts | int64 |


### telescope_pipeline_files/gold/coordinated_pairs  (Parquet, 62989 lignes)

| colonne | type |
|---|---|
| channel_a | int64 |
| channel_b | int64 |
| n_shared | int64 |
| n_origins | int64 |
| median_dt_s | int64 |


### telescope_pipeline_files/gold/edges_monthly  (Parquet, 6880522 lignes)

| colonne | type |
|---|---|
| origin_channel | int64 |
| dest_channel | int64 |
| month | string |
| n_forwards | int64 |


### telescope_pipeline_files/gold/forward_speed_monthly  (Parquet, 110 lignes)

| colonne | type |
|---|---|
| month | string |
| n_forwards | int64 |
| n_fast10 | int64 |
| n_fast60 | int64 |
| median_delay_s | int64 |


### telescope_pipeline_files/gold/channel_stats_csv  (70965 lignes, 8 colonnes)

| channel_id | n_messages | n_forwarded_in | n_forwarded_in_from_channels | total_views | total_forwards | first_date | last_date |
|---|---|---|---|---|---|---|---|
| 1000015666 | 2768 | 566 | 566 | 1178789 | 798 | 2024-07-02T05:23:01 | 2024-09-27T13:05:26 |
| 1000080439 | 250 | 1 | 0 | 3098170 | 22045 | 2016-10-24T14:23:28 | 2020-05-25T13:54:18 |
| 1000123669 | 524 | 22 | 22 | 2893424 | 20394 | 2019-05-15T14:13:36 | 2024-09-26T09:53:36 |
| 1000876896 | 2118 | 3 | 3 | 1209114 | 2050 | 2024-06-23T18:04:31 | 2024-09-27T18:05:29 |
| 1001738793 | 750 | 23 | 20 | 3032625 | 176 | 2016-03-16T19:09:21 | 2018-11-02T14:20:37 |
| 1002660052 | 2153 | 38 | 38 | 85214659 | 1057873 | 2024-06-09T20:00:38 | 2024-09-27T17:51:21 |
| 1002765601 | 2250 | 213 | 213 | 2162166 | 9387 | 2024-07-23T19:20:24 | 2024-09-10T01:00:32 |
| 1002825301 | 421 | 1 | 1 | 268008 | 129 | 2024-03-11T10:56:22 | 2024-08-22T11:05:05 |
| 1003378850 | 504 | 1 | 1 | 5646345 | 4874 | 2021-11-24T16:15:43 | 2024-09-23T06:58:02 |
| 1003588092 | 313 | 307 | 307 | 567756 | 7897 | 2023-02-12T05:48:05 | 2024-09-21T19:00:42 |
| 1006323643 | 44970 | 527 | 527 | 111717824 | 572548 | 2015-12-28T14:19:56 | 2024-04-08T14:01:05 |
| 1007582771 | 1651 | 0 | 0 | 215989 | 876 | 2024-05-22T09:37:26 | 2024-09-27T16:14:14 |
| 1007587737 | 2142 | 15 | 15 | 7787751 | 12776 | 2024-07-05T21:05:31 | 2024-09-27T18:05:03 |
| 1007617710 | 250 | 13 | 13 | 194000 | 302 | 2021-06-08T17:29:26 | 2024-05-15T18:46:52 |
| 1008743674 | 506 | 43 | 41 | 1303651 | 8125 | 2018-08-29T13:35:52 | 2024-09-21T11:14:30 |
| 1010814885 | 750 | 283 | 277 | 1211726 | 7647 | 2022-02-20T06:12:18 | 2024-09-27T13:49:02 |
| 1012339614 | 99470 | 6475 | 6473 | 1985868117 | 2175305 | 2016-01-11T09:52:04 | 2024-04-07T17:45:58 |
| 1020003594 | 2847 | 36 | 36 | 21965216 | 22929 | 2024-07-04T18:08:47 | 2024-09-27T17:40:06 |
| 1020613602 | 1000 | 134 | 134 | 2449081 | 3037 | 2018-04-29T15:00:46 | 2022-11-20T10:42:17 |
| 1021334417 | 1032 | 0 | 0 | 9433 | 74 | 2023-04-02T01:58:07 | 2024-09-27T01:49:05 |
| 1021894537 | 250 | 12 | 12 | 84955 | 862 | 2024-09-23T06:59:45 | 2024-09-27T17:47:25 |
| 1025174067 | 72 | 56 | 56 | 174386 | 1442 | 2021-06-17T12:41:56 | 2022-08-05T06:49:15 |
| 1027159242 | 250 | 18 | 17 | 146843 | 1844 | 2018-11-27T09:37:55 | 2023-11-15T12:43:04 |
| 1029095426 | 34659 | 3101 | 3098 | 739215751 | 2435240 | 2016-02-08T09:46:04 | 2024-04-06T15:30:47 |
| 1036095159 | 1243 | 1 | 1 | 5700786 | 154476 | 2023-12-09T13:04:50 | 2024-09-27T16:01:48 |
| 1037792187 | 250 | 124 | 124 | 123146 | 1213 | 2022-04-19T05:30:28 | 2023-11-12T09:42:23 |
| 1040700943 | 1021 | 42 | 42 | 2044890 | 32694 | 2022-11-13T07:36:48 | 2024-09-25T04:14:10 |
| 1044269137 | 20846 | 113 | 113 | 59633091 | 115990 | 2021-03-23T10:25:53 | 2024-04-06T16:28:28 |
| 1044570878 | 704 | 368 | 358 | 1646809 | 1765 | 2022-03-11T15:19:04 | 2024-03-17T09:20:48 |
| 1044877601 | 254 | 46 | 36 | 190339 | 2208 | 2020-01-21T16:23:45 | 2024-09-06T10:04:04 |
| 1048137938 | 1097 | 1 | 1 | 1507968 | 6937 | 2023-03-03T02:55:22 | 2024-09-25T10:04:16 |
| 1050682391 | 751 | 302 | 302 | 75487 | 492 | 2022-07-21T09:38:40 | 2024-08-07T05:26:40 |
| 1052386677 | 1453 | 0 | 0 | 169118 | 536 | 2024-04-11T16:35:30 | 2024-09-24T02:08:45 |
| 1052528495 | 1203 | 1 | 1 | 227342 | 783 | 2023-07-20T15:25:55 | 2024-09-27T12:08:37 |
| 1052763639 | 500 | 25 | 25 | 592842 | 2027 | 2017-11-30T21:02:10 | 2021-06-30T21:50:00 |
| 1053968240 | 291 | 6 | 4 | 7421187 | 67905 | 2023-08-23T07:14:43 | 2024-09-27T11:05:33 |
| 1054019032 | 2058 | 126 | 126 | 588530 | 5137 | 2024-06-06T21:22:37 | 2024-09-27T16:53:42 |
| 1056371224 | 297 | 85 | 84 | 1166886 | 9352 | 2016-10-10T21:56:43 | 2023-12-21T07:23:54 |
| 1056710815 | 750 | 5 | 5 | 13671671 | 68119 | 2024-03-29T20:19:31 | 2024-07-31T10:26:20 |
| 1057650082 | 1223 | 74 | 72 | 4169427 | 34342 | 2023-04-19T05:39:06 | 2024-09-27T16:06:47 |


### telescope_pipeline_files/gold/city_daily_csv  (123077 lignes, 7 colonnes)

| country | city | date | n_posts | n_forwarded_posts | views | n_channels |
|---|---|---|---|---|---|---|
| Russia | Moscow | 2017-08-06 | 421 | 112 | 1442592 | 55 |
| Russia | Moscow | 2023-12-21 | 26469 | 5443 | 257767110 | 2346 |
| Iran | Tehran | 2021-07-27 | 1218 | 30 | 15965898 | 58 |
| Iran | Tehran | 2018-04-04 | 1203 | 43 | 29083350 | 50 |
| Russia | Saint Petersburg | 2021-03-11 | 1861 | 206 | 12363843 | 185 |
| Russia | Saint Petersburg | 2019-09-18 | 1087 | 138 | 5508175 | 110 |
| Russia | Saint Petersburg | 2019-11-16 | 560 | 112 | 1929687 | 89 |
| Iran | Tehran | 2020-03-10 | 1162 | 40 | 19369106 | 60 |
| Iran | Mashhad | 2024-07-06 | 348 | 52 | 1077973 | 23 |
| Iran | Mashhad | 2023-10-10 | 497 | 45 | 2549778 | 16 |
| Iran | Tehran | 2024-09-21 | 2753 | 65 | 15504413 | 75 |
| Ukraine | Kharkiv | 2021-09-02 | 1084 | 159 | 12377392 | 105 |
| Ukraine | Donetsk | 2022-11-25 | 12501 | 3371 | 115178549 | 537 |
| Russia | Moscow | 2024-02-01 | 23013 | 4113 | 299409576 | 2522 |
| Russia | Tyumen | 2021-06-04 | 482 | 44 | 898512 | 45 |
| Russia | Moscow | 2021-01-31 | 8265 | 2700 | 151862165 | 492 |
| Russia | Khabarovsk | 2024-07-29 | 4197 | 1100 | 8598557 | 304 |
| Russia | Krasnoyarsk | 2021-08-28 | 107 | 20 | 372250 | 18 |
| Russia | Krasnoyarsk | 2023-08-16 | 830 | 74 | 2691499 | 106 |
| Russia | Moscow | 2018-10-30 | 1835 | 590 | 12865819 | 225 |
| Russia | Moscow | 2022-04-08 | 14588 | 4088 | 291274081 | 1074 |
| Russia | Moscow | 2024-09-09 | 37704 | 13272 | 163161140 | 2551 |
| Russia | Yekaterinburg | 2022-05-16 | 607 | 39 | 5451610 | 57 |
| Russia | Yekaterinburg | 2022-10-08 | 633 | 115 | 7699019 | 50 |
| Ukraine | Kharkiv | 2018-02-11 | 184 | 4 | 410037 | 15 |
| Russia | Saint Petersburg | 2024-01-21 | 7616 | 1181 | 60102998 | 743 |
| Russia | Ufa | 2024-05-20 | 589 | 67 | 1429431 | 83 |
| Ukraine | Donetsk | 2022-10-06 | 11109 | 3953 | 135487298 | 506 |
| Russia | Moscow | 2020-02-21 | 2911 | 885 | 22518204 | 376 |
| Russia | Moscow | 2022-09-02 | 13142 | 3172 | 174952754 | 1234 |
| Russia | Moscow | 2023-01-01 | 8051 | 1612 | 129040578 | 926 |
| Russia | Omsk | 2020-06-25 | 38 | 5 | 37425 | 10 |
| Ukraine | Kyiv | 2020-06-30 | 126 | 11 | 2596358 | 24 |
| Iran | Mashhad | 2018-04-15 | 158 | 6 | 439342 | 8 |
| Russia | Moscow | 2022-06-16 | 13952 | 3576 | 191727856 | 1140 |
| Ukraine | Luhansk | 2024-08-05 | 1438 | 348 | 7503222 | 177 |
| Iran | Mashhad | 2024-09-23 | 1522 | 112 | 8177634 | 52 |
| Iran | Tehran | 2017-04-19 | 1099 | 23 | 42034841 | 33 |
| Russia | Saint Petersburg | 2019-03-29 | 834 | 109 | 2712413 | 90 |
| Iran | Tehran | 2020-01-05 | 1975 | 52 | 46460124 | 58 |


### telescope_pipeline_files/gold/edges_monthly_csv  (6880522 lignes, 4 colonnes)

| origin_channel | dest_channel | month | n_forwards |
|---|---|---|---|
| 2055342224 | 1000180159 | 2024-09 | 39 |
| 1819541792 | 1000180159 | 2024-09 | 2 |
| 1391701024 | 1000847502 | 2022-07 | 11 |
| 1341441879 | 1001433900 | 2019-09 | 10 |
| 1856903191 | 1002516083 | 2023-05 | 2 |
| 1856903191 | 1002516083 | 2023-10 | 3 |
| 1382979056 | 1003201003 | 2023-08 | 6 |
| 1700501351 | 1003740416 | 2024-07 | 22 |
| 1003921752 | 1003740416 | 2024-08 | 1 |
| 1522861284 | 1003747500 | 2024-08 | 1 |
| 2091285194 | 1004039699 | 2024-02 | 5 |
| 1005280116 | 1005280116 | 2019-10 | 28 |
| 1308311510 | 1005280116 | 2021-03 | 3 |
| 1258612234 | 1005280116 | 2021-10 | 116 |
| 1258612234 | 1005280116 | 2022-08 | 136 |
| 1391194796 | 1005280116 | 2024-03 | 94 |
| 1008358192 | 1005610235 | 2020-04 | 1 |
| 1158215714 | 1005634746 | 2020-01 | 1 |
| 1228673426 | 1006112008 | 2023-04 | 1 |
| 1330758823 | 1006263686 | 2024-09 | 1 |
| 1194855148 | 1006323643 | 2021-05 | 11 |
| 1006557879 | 1006557879 | 2020-05 | 268 |
| 1250840687 | 1006638490 | 2024-09 | 27 |
| 1119282611 | 1006869491 | 2018-05 | 13 |
| 1314897897 | 1006869491 | 2023-07 | 22 |
| 1007697751 | 1006939659 | 2024-04 | 9 |
| 1499831899 | 1007396605 | 2021-09 | 1 |
| 1047615605 | 1007714672 | 2016-07 | 21 |
| 1035079144 | 1007714672 | 2018-10 | 13 |
| 1008103361 | 1008103361 | 2024-04 | 89 |
| 1026938635 | 1010162768 | 2024-07 | 1 |
| 1023783438 | 1010320269 | 2018-06 | 1 |
| 1131389182 | 1010320269 | 2022-04 | 1 |
| 1012217642 | 1010576945 | 2022-09 | 78 |
| 1137457075 | 1011154118 | 2023-09 | 3 |
| 1098992160 | 1011882481 | 2017-05 | 2 |
| 1003740416 | 1012155781 | 2017-03 | 1 |
| 1100300699 | 1012155781 | 2018-01 | 1 |
| 1226431175 | 1012155781 | 2019-08 | 8 |
| 1760202057 | 1012155781 | 2022-03 | 1 |


# Thème 1 — Communautés


## Tables : analysis/communities_v2


### bigdata_pipeline/analysis/communities_v2/communities_infomap  (267518 lignes, 4 colonnes)

| channel_id | community | community_size | forwards_total |
|---|---|---|---|
| 1168759606 | 0 | 6782 | 10287 |
| 1333978197 | 0 | 6782 | 8488 |
| 1247534353 | 0 | 6782 | 6184 |
| 1167959099 | 0 | 6782 | 5401 |
| 1455775270 | 0 | 6782 | 4564 |
| 1440393212 | 0 | 6782 | 4241 |
| 1851529049 | 0 | 6782 | 4231 |
| 1387359927 | 0 | 6782 | 3614 |
| 1325174315 | 0 | 6782 | 3567 |
| 1355850750 | 0 | 6782 | 3554 |


### bigdata_pipeline/analysis/communities_v2/communities_leiden  (267518 lignes, 4 colonnes)

| channel_id | community | community_size | forwards_total |
|---|---|---|---|
| 1164999973 | 0 | 55655 | 236081 |
| 1600226044 | 0 | 55655 | 145099 |
| 1120669478 | 0 | 55655 | 86081 |
| 1767247409 | 0 | 55655 | 57200 |
| 1837498119 | 0 | 55655 | 55072 |
| 1322232546 | 0 | 55655 | 41012 |
| 1571907693 | 0 | 55655 | 38749 |
| 1946867637 | 0 | 55655 | 37754 |
| 1067810422 | 0 | 55655 | 37043 |
| 1035235678 | 0 | 55655 | 35211 |


### bigdata_pipeline/analysis/communities_v2/community_comparison  (2 lignes, 6 colonnes)

| pair | n_common | nmi | ari | homogeneity | completeness |
|---|---|---|---|---|---|
| leiden_vs_infomap | 267518 | 0.5754 | 0.0616 | 0.9306 | 0.4164 |
| leiden_seed_vs_leiden_seed+1 | 267518 | 0.9088 | 0.8624 | 0.9082 | 0.9093 |


### bigdata_pipeline/analysis/communities_v2/community_flows_leiden  (236 lignes, 4 colonnes)

| origin_community | dest_community | forwards | share_of_origin_out |
|---|---|---|---|
| 0 | 0 | 2051439.0 | 0.8192 |
| 0 | 1 | 203925.0 | 0.0814 |
| 0 | 2 | 109138.0 | 0.0436 |
| 0 | 3 | 6547.0 | 0.0026 |
| 0 | 4 | 7262.0 | 0.0029 |
| 0 | 5 | 14047.0 | 0.0056 |
| 0 | 6 | 31270.0 | 0.0125 |
| 0 | 7 | 14498.0 | 0.0058 |
| 0 | 8 | 3571.0 | 0.0014 |
| 0 | 9 | 150.0 | 0.0001 |


### bigdata_pipeline/analysis/communities_v2/community_names  (822 lignes, 6 colonnes)

| community | community_name | dominant_language | dominant_share | n_known | size |
|---|---|---|---|---|---|
| 0 | Russian (95%, n=10985/55655) | Russian | 0.9487 | 10985 | 55655 |
| 1 | Russian (98%, n=7627/19254) | Russian | 0.9771 | 7627 | 19254 |
| 2 | Russian (98%, n=5985/18784) | Russian | 0.9831 | 5985 | 18784 |
| 3 | English (68%, n=2289/16298) | English | 0.6824 | 2289 | 16298 |
| 4 | Russian (97%, n=5095/15164) | Russian | 0.9741 | 5095 | 15164 |
| 5 | Ukrainian (83%, n=3357/13763) | Ukrainian | 0.832 | 3357 | 13763 |
| 6 | Russian (94%, n=3305/12255) | Russian | 0.9404 | 3305 | 12255 |
| 7 | Russian (100%, n=3595/10409) | Russian | 0.9953 | 3595 | 10409 |
| 8 | Russian (100%, n=2365/8092) | Russian | 0.997 | 2365 | 8092 |
| 9 | German (91%, n=822/8065) | German | 0.9136 | 822 | 8065 |
| 10 | Russian (99%, n=1869/8010) | Russian | 0.9872 | 1869 | 8010 |
| 11 | Russian (100%, n=2422/7650) | Russian | 0.9959 | 2422 | 7650 |
| 12 | Persian (99%, n=1404/7022) | Persian | 0.9915 | 1404 | 7022 |
| 13 | Russian (100%, n=1493/6294) | Russian | 0.996 | 1493 | 6294 |
| 14 | Russian (99%, n=1495/5975) | Russian | 0.992 | 1495 | 5975 |
| 15 | Russian (81%, n=1072/3831) | Russian | 0.8088 | 1072 | 3831 |
| 16 | Russian (97%, n=1087/3648) | Russian | 0.9678 | 1087 | 3648 |
| 17 | Russian (100%, n=1356/3120) | Russian | 0.9963 | 1356 | 3120 |
| 18 | Russian (98%, n=909/2639) | Russian | 0.9791 | 909 | 2639 |
| 19 | Russian (84%, n=661/2591) | Russian | 0.8351 | 661 | 2591 |
| 20 | Russian (45%, n=271/2506) | Russian | 0.4465 | 271 | 2506 |
| 21 | Russian (100%, n=627/2490) | Russian | 1.0 | 627 | 2490 |
| 22 | Russian (100%, n=721/2463) | Russian | 0.9986 | 721 | 2463 |
| 23 | English (84%, n=289/2413) | English | 0.8443 | 289 | 2413 |
| 24 | Russian (100%, n=540/1944) | Russian | 0.9963 | 540 | 1944 |
| 25 | Russian (97%, n=144/1794) | Russian | 0.9653 | 144 | 1794 |
| 26 | Russian (99%, n=383/1425) | Russian | 0.9922 | 383 | 1425 |
| 27 | Russian (100%, n=491/1359) | Russian | 1.0 | 491 | 1359 |
| 28 | Russian (100%, n=412/1336) | Russian | 0.9976 | 412 | 1336 |
| 29 | Russian (99%, n=747/1336) | Russian | 0.9853 | 747 | 1336 |
| 30 | Russian (98%, n=359/1201) | Russian | 0.9805 | 359 | 1201 |
| 31 | Russian (89%, n=228/1165) | Russian | 0.8947 | 228 | 1165 |
| 32 | Russian (99%, n=162/1152) | Russian | 0.9877 | 162 | 1152 |
| 33 | Russian (100%, n=423/1099) | Russian | 1.0 | 423 | 1099 |
| 34 | Russian (100%, n=463/1051) | Russian | 0.9978 | 463 | 1051 |
| 35 | Russian (99%, n=166/1015) | Russian | 0.994 | 166 | 1015 |
| 36 | Russian (100%, n=296/977) | Russian | 1.0 | 296 | 977 |
| 37 | Russian (95%, n=387/864) | Russian | 0.9535 | 387 | 864 |
| 38 | Russian (100%, n=242/801) | Russian | 1.0 | 242 | 801 |
| 39 | Russian (100%, n=168/546) | Russian | 1.0 | 168 | 546 |


### bigdata_pipeline/analysis/communities_v2/community_profiles_leiden  (822 lignes, 7 colonnes)

| community | size | forwards_out | forwards_in | forwards_inside | inside_share_of_out | top_channels |
|---|---|---|---|---|---|---|
| 0 | 55655 | 2504287 | 2657225 | 2051439 | 0.8192 | 1164999973;1600226044;1120669478;1767247 |
| 1 | 19254 | 7681743 | 7183111 | 5540774 | 0.7213 | 1101170442;1119287642;1101806611;1069772 |
| 2 | 18784 | 3414166 | 3024938 | 2112773 | 0.6188 | 1082084045;1310493808;1394050290;1216878 |
| 3 | 16298 | 1003462 | 1009192 | 958048 | 0.9547 | 1857065732;1641520356;1765224391;1162074 |
| 4 | 15164 | 1595336 | 1329589 | 1077341 | 0.6753 | 1065276858;1074511071;1526452346;1182694 |
| 5 | 13763 | 899116 | 893212 | 828438 | 0.9214 | 1463721328;1470200990;1198299024;1351220 |
| 6 | 12255 | 992244 | 929540 | 688348 | 0.6937 | 1342724806;1262711722;1286559502;1106360 |
| 7 | 10409 | 1786809 | 1900574 | 1258762 | 0.7045 | 1099350027;1120151877;1254663237;1369020 |
| 8 | 8092 | 816636 | 908504 | 714889 | 0.8754 | 1212259149;1112362795;1378778396;1594869 |
| 9 | 8065 | 278486 | 280958 | 271788 | 0.9759 | 1168759606;1333978197;1247534353;1167959 |


### bigdata_pipeline/analysis/communities_v2/community_summary  (2 lignes, 13 colonnes)

| algorithm | n_nodes | n_edges_directed | total_forwards | n_communities | modularity | intra_share | largest_community | largest_share | top10_share | singletons | codelength | seconds |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| leiden | 267518 | 2733450 | 31540607 | 822 | 0.69 | 0.7805 | 55655 | 0.208 | 0.6644 | 0 |  | 102 |
| infomap | 267518 | 2733450 | 31540607 | 7867 | 0.5842 | 0.6032 | 6782 | 0.0254 | 0.1111 | 0 | 9.6813 | 96 |


### bigdata_pipeline/analysis/communities_v2/resolution_curve  (6 lignes, 6 colonnes)

| resolution | n_communities | modularity | intra_share | largest_share | seconds |
|---|---|---|---|---|---|
| 0.5 | 754 | 0.6669 | 0.8405 | 0.2175 | 114.0 |
| 0.8 | 809 | 0.6891 | 0.8004 | 0.1758 | 153.0 |
| 1.0 | 822 | 0.69 | 0.7805 | 0.208 |  |
| 1.2 | 732 | 0.6859 | 0.7564 | 0.1549 | 84.0 |
| 1.5 | 768 | 0.6798 | 0.7278 | 0.1665 | 111.0 |
| 2.0 | 817 | 0.6697 | 0.705 | 0.1567 | 124.0 |


### bigdata_pipeline/analysis/communities_v2/run_info.json

```
{
  "date": "2026-11-11",
  "tables": [
    "communities_leiden",
    "communities_infomap",
    "community_summary",
    "community_profiles_leiden",
    "community_flows_leiden",
    "community_comparison",
    "yearly_communities",
    "resolution_curve",
    "community_names"
  ],
  "seconds": 1066,
  "args": {
    "gold": "telescope_pipeline_files/gold",
    "out": "bigdata_pipeline/analysis/communities_v2",
    "figdir": "bigdata_pipeline/analysis/figures/community_detection",
    "resolution": "1.0",
    "seed": "42",
    "min_weight": "1",
    "infomap_trials": "1",
    "skip_infomap": "False",
    "reuse_leiden": "False",
    "seed_baseline": "True",
    "skip_yearly": "False",
    "resolution_curve": "True",
    "curve_resolutions": "0.5,0.8,1.0,1.2,1.5,2.0",
    "languages": "telescope_files/Channel_Language.csv",
    "top": "20",
    "meta_top": "50",
    "min_year_edges": "5000",
    "top_flows": "15",
    "no_charts": "False",
    "selftest": "False"
  }
}
```


### bigdata_pipeline/analysis/communities_v2/yearly_communities  (8 lignes, 11 colonnes)

| year | n_channels | n_edges | n_forwards | n_communities | modularity | largest_share | n_common_prev | nmi_prev | ari_prev | nmi_other_seed |
|---|---|---|---|---|---|---|---|---|---|---|
| 2017 | 5842 | 25027 | 169842 | 91 | 0.6008 | 0.1508 |  |  |  | 0.9991 |
| 2018 | 9979 | 54325 | 412005 | 150 | 0.6027 | 0.1438 | 3259.0 | 0.5151 | 0.3374 | 0.9834 |
| 2019 | 14638 | 101497 | 736492 | 160 | 0.6034 | 0.1159 | 5718.0 | 0.4909 | 0.325 | 0.9072 |
| 2020 | 25274 | 189785 | 1679368 | 248 | 0.5998 | 0.1588 | 9545.0 | 0.4875 | 0.3479 | 0.9499 |
| 2021 | 35763 | 247584 | 2222700 | 380 | 0.6737 | 0.1373 | 16050.0 | 0.513 | 0.346 | 0.8582 |
| 2022 | 78480 | 711778 | 7213361 | 791 | 0.6166 | 0.1307 | 23568.0 | 0.4844 | 0.2892 | 0.8451 |
| 2023 | 123665 | 927686 | 9338678 | 1042 | 0.7165 | 0.1606 | 52338.0 | 0.4913 | 0.2918 | 0.8478 |
| 2024 | 182621 | 1215694 | 9752388 | 1664 | 0.7988 | 0.1515 | 84622.0 | 0.5356 | 0.3501 | 0.8584 |


## Figures : analysis/figures/community_detection

![/home/dvopssl/Documents/telescope_data_analysis/bigdata_pipeline/analysis/figures/community_detection/community_size_distribution.png](/home/dvopssl/Documents/telescope_data_analysis/bigdata_pipeline/analysis/figures/community_detection/community_size_distribution.png)

![/home/dvopssl/Documents/telescope_data_analysis/bigdata_pipeline/analysis/figures/community_detection/community_size_rank.png](/home/dvopssl/Documents/telescope_data_analysis/bigdata_pipeline/analysis/figures/community_detection/community_size_rank.png)

![/home/dvopssl/Documents/telescope_data_analysis/bigdata_pipeline/analysis/figures/community_detection/degree_distribution.png](/home/dvopssl/Documents/telescope_data_analysis/bigdata_pipeline/analysis/figures/community_detection/degree_distribution.png)

![/home/dvopssl/Documents/telescope_data_analysis/bigdata_pipeline/analysis/figures/community_detection/flows_between_communities.png](/home/dvopssl/Documents/telescope_data_analysis/bigdata_pipeline/analysis/figures/community_detection/flows_between_communities.png)

![/home/dvopssl/Documents/telescope_data_analysis/bigdata_pipeline/analysis/figures/community_detection/resolution_curve.png](/home/dvopssl/Documents/telescope_data_analysis/bigdata_pipeline/analysis/figures/community_detection/resolution_curve.png)

![/home/dvopssl/Documents/telescope_data_analysis/bigdata_pipeline/analysis/figures/community_detection/top_20_communities.png](/home/dvopssl/Documents/telescope_data_analysis/bigdata_pipeline/analysis/figures/community_detection/top_20_communities.png)

![/home/dvopssl/Documents/telescope_data_analysis/bigdata_pipeline/analysis/figures/community_detection/yearly_stability.png](/home/dvopssl/Documents/telescope_data_analysis/bigdata_pipeline/analysis/figures/community_detection/yearly_stability.png)

![/home/dvopssl/Documents/telescope_data_analysis/bigdata_pipeline/analysis/figures/community_detection/yearly_structure.png](/home/dvopssl/Documents/telescope_data_analysis/bigdata_pipeline/analysis/figures/community_detection/yearly_structure.png)


# Thème 2 — Langues


## Tables : analysis/language_v2


### bigdata_pipeline/analysis/language_v2/channel_language_inferred  (191621 lignes, 5 colonnes)

| channel_id | inferred_language | vote_share | neighbour_forwards | source |
|---|---|---|---|---|
| 1000000881 | fa | 1.0 | 1 | inferred |
| 1000000882 | ru | 1.0 | 1 | inferred |
| 1000007034 | ru | 1.0 | 2 | inferred |
| 1000010324 | fa | 1.0 | 1 | inferred |
| 1000013724 | fa | 1.0 | 1 | inferred |
| 1000014928 | fa | 1.0 | 1 | inferred |
| 1000018574 | fa | 1.0 | 2 | inferred |
| 1000023755 | fa | 1.0 | 1 | inferred |
| 1000029537 | ru | 1.0 | 25 | inferred |
| 1000042194 | uk | 1.0 | 1 | inferred |


### bigdata_pipeline/analysis/language_v2/channel_language_votes  (4412 lignes, 10 colonnes)

| channel_id | n_voting_languages | language_1 | share_1 | language_2 | share_2 | language_3 | share_3 | share_other | neighbour_forwards |
|---|---|---|---|---|---|---|---|---|---|
| 1070053888 | 3 | uk | 0.5687 | ru | 0.4282 | en | 0.0031 | 0.0 | 1609 |
| 1661474564 | 3 | uk | 0.5848 | ru | 0.4145 | en | 0.0007 | 0.0 | 1527 |
| 1622683334 | 4 | en | 0.7423 | de | 0.2504 | ru | 0.0059 | 0.0015 | 1358 |
| 2045257525 | 2 | uk | 0.5473 | ru | 0.4527 |  | 0.0 | 0.0 | 1089 |
| 1779016252 | 6 | en | 0.6084 | tr | 0.2676 | es | 0.0654 | 0.0586 | 1024 |
| 1693714432 | 2 | uk | 0.6203 | ru | 0.3797 |  | 0.0 | 0.0 | 985 |
| 1471674681 | 3 | ru | 0.7885 | uk | 0.2104 | en | 0.0011 | 0.0 | 908 |
| 1917487180 | 2 | ru | 0.7151 | uk | 0.2849 |  | 0.0 | 0.0 | 895 |
| 1586387346 | 2 | ru | 0.5138 | uk | 0.4862 |  | 0.0 | 0.0 | 872 |
| 2006073887 | 3 | en | 0.7862 | fr | 0.2126 | ru | 0.0012 | 0.0 | 809 |


### bigdata_pipeline/analysis/language_v2/community_language_purity  (822 lignes, 9 colonnes)

| community | size | known_language | known_share | dominant_language | dominant_name | purity | entropy_bits | n_languages |
|---|---|---|---|---|---|---|---|---|
| 0 | 55655 | 10962 | 0.197 | ru | Russian | 0.9506 | 0.4112 | 36 |
| 1 | 19254 | 7626 | 0.3961 | ru | Russian | 0.9772 | 0.2142 | 24 |
| 2 | 18784 | 5982 | 0.3185 | ru | Russian | 0.9836 | 0.1654 | 19 |
| 3 | 16298 | 2284 | 0.1401 | en | English | 0.6839 | 1.8534 | 37 |
| 4 | 15164 | 5092 | 0.3358 | ru | Russian | 0.9747 | 0.2345 | 17 |
| 5 | 13763 | 3357 | 0.2439 | uk | Ukrainian | 0.832 | 0.7787 | 15 |
| 6 | 12255 | 3304 | 0.2696 | ru | Russian | 0.9407 | 0.4317 | 12 |
| 7 | 10409 | 3592 | 0.3451 | ru | Russian | 0.9961 | 0.0451 | 7 |
| 8 | 8092 | 2362 | 0.2919 | ru | Russian | 0.9983 | 0.0206 | 4 |
| 9 | 8065 | 822 | 0.1019 | de | German | 0.9136 | 0.551 | 12 |
| 10 | 8010 | 1868 | 0.2332 | ru | Russian | 0.9877 | 0.13 | 11 |
| 11 | 7650 | 2422 | 0.3166 | ru | Russian | 0.9959 | 0.046 | 6 |
| 12 | 7022 | 1404 | 0.1999 | fa | Persian | 0.9915 | 0.0888 | 6 |
| 13 | 6294 | 1493 | 0.2372 | ru | Russian | 0.996 | 0.0436 | 4 |
| 14 | 5975 | 1495 | 0.2502 | ru | Russian | 0.992 | 0.0866 | 7 |
| 15 | 3831 | 1072 | 0.2798 | ru | Russian | 0.8088 | 1.1443 | 14 |
| 16 | 3648 | 1087 | 0.298 | ru | Russian | 0.9678 | 0.2498 | 5 |
| 17 | 3120 | 1356 | 0.4346 | ru | Russian | 0.9963 | 0.0422 | 5 |
| 18 | 2639 | 904 | 0.3426 | ru | Russian | 0.9845 | 0.1402 | 5 |
| 19 | 2591 | 661 | 0.2551 | ru | Russian | 0.8351 | 0.8713 | 9 |
| 20 | 2506 | 271 | 0.1081 | ru | Russian | 0.4465 | 2.2602 | 11 |
| 21 | 2490 | 627 | 0.2518 | ru | Russian | 1.0 | 0.0 | 1 |
| 22 | 2463 | 721 | 0.2927 | ru | Russian | 0.9986 | 0.0152 | 2 |
| 23 | 2413 | 283 | 0.1173 | en | English | 0.8622 | 0.9416 | 10 |
| 24 | 1944 | 540 | 0.2778 | ru | Russian | 0.9963 | 0.039 | 3 |
| 25 | 1794 | 144 | 0.0803 | ru | Russian | 0.9653 | 0.2704 | 4 |
| 26 | 1425 | 382 | 0.2681 | ru | Russian | 0.9948 | 0.0472 | 2 |
| 27 | 1359 | 491 | 0.3613 | ru | Russian | 1.0 | 0.0 | 1 |
| 28 | 1336 | 412 | 0.3084 | ru | Russian | 0.9976 | 0.0246 | 2 |
| 29 | 1336 | 747 | 0.5591 | ru | Russian | 0.9853 | 0.1107 | 2 |
| 30 | 1201 | 359 | 0.2989 | ru | Russian | 0.9805 | 0.1502 | 3 |
| 31 | 1165 | 228 | 0.1957 | ru | Russian | 0.8947 | 0.6365 | 6 |
| 32 | 1152 | 162 | 0.1406 | ru | Russian | 0.9877 | 0.1083 | 3 |
| 33 | 1099 | 423 | 0.3849 | ru | Russian | 1.0 | 0.0 | 1 |
| 34 | 1051 | 462 | 0.4396 | ru | Russian | 1.0 | 0.0 | 1 |
| 35 | 1015 | 166 | 0.1635 | ru | Russian | 0.994 | 0.0531 | 2 |
| 36 | 977 | 296 | 0.303 | ru | Russian | 1.0 | 0.0 | 1 |
| 37 | 864 | 387 | 0.4479 | ru | Russian | 0.9535 | 0.2714 | 2 |
| 38 | 801 | 242 | 0.3021 | ru | Russian | 1.0 | 0.0 | 1 |
| 39 | 546 | 168 | 0.3077 | ru | Russian | 1.0 | 0.0 | 1 |


### bigdata_pipeline/analysis/language_v2/inference_accuracy  (7 lignes, 8 colonnes)

| row | vote_share_from | vote_share_to | held_out_channels | accuracy | baseline_majority_language | held_out_total | with_known_neighbour |
|---|---|---|---|---|---|---|---|
| 0.0-0.5 | 0.0 | 0.5 | 18 | 0.3889 | 0.8497 | 6888 | 6821 |
| 0.5-0.6 | 0.5 | 0.6 | 57 | 0.5614 | 0.8497 | 6888 | 6821 |
| 0.6-0.7 | 0.6 | 0.7 | 80 | 0.6875 | 0.8497 | 6888 | 6821 |
| 0.7-0.8 | 0.7 | 0.8 | 107 | 0.8037 | 0.8497 | 6888 | 6821 |
| 0.8-0.9 | 0.8 | 0.9 | 165 | 0.9091 | 0.8497 | 6888 | 6821 |
| 0.9-1.0 | 0.9 | 1.0 | 6394 | 0.9831 | 0.8497 | 6888 | 6821 |
| >= 0.8 (rule used) | 0.8 | 1.0 | 6559 | 0.9812 | 0.8497 | 6888 | 6821 |


### bigdata_pipeline/analysis/language_v2/language_activity  (47 lignes, 11 colonnes)

| language | language_name | channels | share_of_channels | times_forwarded | share_of_times_forwarded | influence_ratio | forwarded_per_channel | forwards_made | messages | messages_per_channel |
|---|---|---|---|---|---|---|---|---|---|---|
| ru | Russian | 58859 | 0.850404 | 24513403 | 0.923379 | 1.09 | 416.5 | 28454019 | 156260709.0 | 2654.8 |
| uk | Ukrainian | 3299 | 0.047664 | 709241 | 0.026716 | 0.56 | 215.0 | 833692 | 9118811.0 | 2764.1 |
| en | English | 2822 | 0.040773 | 649007 | 0.024447 | 0.6 | 230.0 | 1018924 | 6332551.0 | 2244.0 |
| fa | Persian | 1576 | 0.02277 | 199592 | 0.007518 | 0.33 | 126.6 | 275568 | 7222227.0 | 4582.6 |
| de | German | 788 | 0.011385 | 110028 | 0.004145 | 0.36 | 139.6 | 281290 | 1355189.0 | 1719.8 |
| bg | Bulgarian | 282 | 0.004074 | 35621 | 0.001342 | 0.33 | 126.3 | 72348 | 607426.0 | 2154.0 |
| es | Spanish | 233 | 0.003366 | 92136 | 0.003471 | 1.03 | 395.4 | 129525 | 634931.0 | 2725.0 |
| ar | Arabic | 201 | 0.002904 | 79293 | 0.002987 | 1.03 | 394.5 | 93760 | 635500.0 | 3161.7 |
| et | Estonian | 191 | 0.00276 | 20687 | 0.000779 | 0.28 | 108.3 | 25429 | 322199.0 | 1686.9 |
| it | Italian | 184 | 0.002658 | 47345 | 0.001783 | 0.67 | 257.3 | 90908 | 370751.0 | 2015.0 |
| fr | French | 183 | 0.002644 | 29392 | 0.001107 | 0.42 | 160.6 | 64106 | 451691.0 | 2468.3 |
| mk | Macedonian | 125 | 0.001806 | 15944 | 0.000601 | 0.33 | 127.6 | 24713 | 225973.0 | 1807.8 |
| tr | Turkish | 86 | 0.001243 | 5299 | 0.0002 | 0.16 | 61.6 | 9959 | 120554.0 | 1401.8 |
| he | Hebrew | 56 | 0.000809 | 7977 | 0.0003 | 0.37 | 142.4 | 13070 | 238471.0 | 4258.4 |
| id | Indonesian | 45 | 0.00065 | 464 | 1.7e-05 | 0.03 | 10.3 | 2814 | 44256.0 | 983.5 |
| ro | Romanian | 44 | 0.000636 | 4597 | 0.000173 | 0.27 | 104.5 | 5712 | 62647.0 | 1423.8 |
| pt | Portuguese | 36 | 0.00052 | 3757 | 0.000142 | 0.27 | 104.4 | 5227 | 36611.0 | 1017.0 |
| pl | Polish | 24 | 0.000347 | 729 | 2.7e-05 | 0.08 | 30.4 | 800 | 85727.0 | 3572.0 |
| hr | Croatian | 22 | 0.000318 | 962 | 3.6e-05 | 0.11 | 43.7 | 583 | 26248.0 | 1193.1 |
| cs | Czech | 13 | 0.000188 | 4132 | 0.000156 | 0.83 | 317.8 | 22798 | 193595.0 | 14891.9 |
| ca | Catalan | 12 | 0.000173 | 657 | 2.5e-05 | 0.14 | 54.8 | 671 | 8770.0 | 730.8 |
| sk | Slovak | 11 | 0.000159 | 10937 | 0.000412 | 2.59 | 994.3 | 43493 | 84365.0 | 7669.5 |
| el | Greek | 11 | 0.000159 | 861 | 3.2e-05 | 0.2 | 78.3 | 2619 | 16987.0 | 1544.3 |
| sv | Swedish | 9 | 0.00013 | 235 | 9e-06 | 0.07 | 26.1 | 917 | 13481.0 | 1497.9 |
| so | Somali | 9 | 0.00013 | 341 | 1.3e-05 | 0.1 | 37.9 | 828 | 21567.0 | 2396.3 |
| nl | Dutch | 9 | 0.00013 | 275 | 1e-05 | 0.08 | 30.6 | 2723 | 9406.0 | 1045.1 |
| hu | Hungarian | 9 | 0.00013 | 200 | 8e-06 | 0.06 | 22.2 | 226 | 9412.0 | 1045.8 |
| da | Danish | 8 | 0.000116 | 61 | 2e-06 | 0.02 | 7.6 | 561 | 8479.0 | 1059.9 |
| lt | Lithuanian | 7 | 0.000101 | 83 | 3e-06 | 0.03 | 11.9 | 136 | 8304.0 | 1186.3 |
| no | Norwegian | 7 | 0.000101 | 558 | 2.1e-05 | 0.21 | 79.7 | 437 | 10557.0 | 1508.1 |
| vi | Vietnamese | 6 | 8.7e-05 | 244 | 9e-06 | 0.11 | 40.7 | 1162 | 10275.0 | 1712.5 |
| zh-cn | Chinese | 6 | 8.7e-05 | 90 | 3e-06 | 0.04 | 15.0 | 147 | 17109.0 | 2851.5 |
| ja | Japanese | 5 | 7.2e-05 | 275 | 1e-05 | 0.14 | 55.0 | 2518 | 6289.0 | 1257.8 |
| sw | Swahili | 5 | 7.2e-05 | 155 | 6e-06 | 0.08 | 31.0 | 218 | 11880.0 | 2376.0 |
| af | Afrikaans | 4 | 5.8e-05 | 660 | 2.5e-05 | 0.43 | 165.0 | 278 | 5364.0 | 1341.0 |
| fi | Finnish | 4 | 5.8e-05 | 127 | 5e-06 | 0.08 | 31.8 | 11 | 6523.0 | 1630.8 |
| lv | Latvian | 4 | 5.8e-05 | 1131 | 4.3e-05 | 0.74 | 282.8 | 2762 | 10852.0 | 2713.0 |
| tl | Tagalog | 3 | 4.3e-05 | 510 | 1.9e-05 | 0.44 | 170.0 | 34 | 2522.0 | 840.7 |
| cy | Welsh | 3 | 4.3e-05 | 54 | 2e-06 | 0.05 | 18.0 | 20 | 2828.0 | 942.7 |
| ur | Urdu | 2 | 2.9e-05 | 3 | 0.0 | 0.0 | 1.5 | 194 | 1545.0 | 772.5 |


### bigdata_pipeline/analysis/language_v2/language_bridges  (60 lignes, 10 colonnes)

| direction | rank | channel_id | language | language_name | community | forwards_with_known_language | forwards_across_languages | cross_share | main_other_language |
|---|---|---|---|---|---|---|---|---|---|
| exports | 1 | 1074511071 | en | English | 4 | 38542 | 15717 | 0.4078 | Russian |
| exports | 2 | 1065276858 | ru | Russian | 4 | 72443 | 7599 | 0.1049 | English |
| exports | 3 | 1310984791 | en | English | 3 | 15234 | 7532 | 0.4944 | French |
| exports | 4 | 1671515228 | ru | Russian | 41 | 7268 | 7114 | 0.9788 | Slovak |
| exports | 5 | 1463721328 | uk | Ukrainian | 5 | 86978 | 6178 | 0.071 | Russian |
| exports | 6 | 1763984660 | ru | Russian | 41 | 5459 | 5431 | 0.9949 | Slovak |
| exports | 7 | 1101170442 | ru | Russian | 1 | 277989 | 4834 | 0.0174 | Slovak |
| exports | 8 | 1590534742 | en | English | 3 | 9838 | 3774 | 0.3836 | Russian |
| exports | 9 | 1547049625 | uk | Ukrainian | 1 | 3712 | 3694 | 0.9952 | Russian |
| exports | 10 | 1199360700 | uk | Ukrainian | 6 | 5063 | 3412 | 0.6739 | Russian |
| exports | 11 | 1453804949 | ru | Russian | 1 | 32651 | 3042 | 0.0932 | Bulgarian |
| exports | 12 | 1139528163 | ru | Russian | 15 | 5978 | 2852 | 0.4771 | Bulgarian |
| exports | 13 | 1457886470 | uk | Ukrainian | 1 | 3125 | 2488 | 0.7962 | Russian |
| exports | 14 | 1340904461 | de | German | 4 | 3002 | 2428 | 0.8088 | Russian |
| exports | 15 | 1453453123 | en | English | 3 | 2953 | 2424 | 0.8209 | Russian |
| exports | 16 | 1189306052 | sk | Slovak | 41 | 2618 | 2414 | 0.9221 | Czech |
| exports | 17 | 1155138955 | uk | Ukrainian | 1 | 2413 | 2408 | 0.9979 | Russian |
| exports | 18 | 1210945539 | ru | Russian | 6 | 6987 | 2256 | 0.3229 | Ukrainian |
| exports | 19 | 1197363285 | uk | Ukrainian | 5 | 5423 | 2233 | 0.4118 | Russian |
| exports | 20 | 1478095454 | et | Estonian | 0 | 2199 | 2198 | 0.9995 | Ukrainian |
| exports | 21 | 1792659030 | uk | Ukrainian | 5 | 2758 | 2197 | 0.7966 | Russian |
| exports | 22 | 1198589840 | uk | Ukrainian | 5 | 4340 | 2189 | 0.5044 | Russian |
| exports | 23 | 1715258620 | de | German | 9 | 3184 | 2132 | 0.6696 | Russian |
| exports | 24 | 1261833912 | uk | Ukrainian | 1 | 2309 | 2123 | 0.9194 | Russian |
| exports | 25 | 1222606634 | uk | Ukrainian | 6 | 2072 | 2018 | 0.9739 | Russian |
| exports | 26 | 1701685420 | ru | Russian | 41 | 3060 | 1920 | 0.6275 | Slovak |
| exports | 27 | 1490843052 | fr | French | 17 | 1949 | 1906 | 0.9779 | Russian |
| exports | 28 | 1694566316 | ru | Russian | 3 | 2435 | 1859 | 0.7634 | Italian |
| exports | 29 | 1062743165 | en | English | 2 | 1858 | 1858 | 1.0 | Russian |
| exports | 30 | 1252806852 | ru | Russian | 4 | 3022 | 1790 | 0.5923 | French |
| imports | 1 | 1792908769 | sk | Slovak | 41 | 27496 | 21125 | 0.7683 | Russian |
| imports | 2 | 1162074204 | fr | French | 3 | 24433 | 15111 | 0.6185 | English |
| imports | 3 | 1409172206 | bg | Bulgarian | 46 | 14729 | 10078 | 0.6842 | Russian |
| imports | 4 | 1765224391 | it | Italian | 3 | 22272 | 8753 | 0.393 | Russian |
| imports | 5 | 1834850708 | ru | Russian | 1 | 85795 | 5171 | 0.0603 | Ukrainian |
| imports | 6 | 1768246235 | es | Spanish | 3 | 14385 | 4265 | 0.2965 | Russian |
| imports | 7 | 1771781790 | ru | Russian | 5 | 4579 | 4109 | 0.8974 | Ukrainian |
| imports | 8 | 1600226044 | ru | Russian | 0 | 127500 | 4025 | 0.0316 | Ukrainian |
| imports | 9 | 1789080285 | es | Spanish | 3 | 18378 | 3978 | 0.2165 | English |
| imports | 10 | 1540552367 | uk | Ukrainian | 5 | 6224 | 3707 | 0.5956 | Russian |


### bigdata_pipeline/analysis/language_v2/language_flows  (30 lignes, 6 colonnes)

| src | src_name | dst | dst_name | forwards | share_of_source_out |
|---|---|---|---|---|---|
| ru | Russian | ru | Russian | 24296965.0 | 0.9924 |
| uk | Ukrainian | uk | Ukrainian | 578250.0 | 0.8171 |
| en | English | en | English | 527068.0 | 0.8143 |
| fa | Persian | fa | Persian | 197754.0 | 0.9917 |
| uk | Ukrainian | ru | Russian | 124663.0 | 0.1762 |
| de | German | de | German | 100914.0 | 0.9189 |
| es | Spanish | es | Spanish | 85910.0 | 0.9333 |
| ar | Arabic | ar | Arabic | 74759.0 | 0.9431 |
| en | English | ru | Russian | 71055.0 | 0.1098 |
| ru | Russian | uk | Ukrainian | 65972.0 | 0.0027 |
| it | Italian | it | Italian | 42303.0 | 0.8955 |
| ru | Russian | en | English | 36572.0 | 0.0015 |
| bg | Bulgarian | bg | Bulgarian | 27615.0 | 0.7763 |
| fr | French | fr | French | 24095.0 | 0.8215 |
| ru | Russian | sk | Slovak | 22588.0 | 0.0009 |
| en | English | fr | French | 17968.0 | 0.0278 |
| ru | Russian | bg | Bulgarian | 15515.0 | 0.0006 |
| mk | Macedonian | mk | Macedonian | 14261.0 | 0.8948 |
| et | Estonian | ru | Russian | 14223.0 | 0.69 |
| ru | Russian | it | Italian | 8759.0 | 0.0004 |
| ru | Russian | et | Estonian | 8041.0 | 0.0003 |
| he | Hebrew | he | Hebrew | 7305.0 | 0.9158 |
| sk | Slovak | sk | Slovak | 7224.0 | 0.6605 |
| en | English | es | Spanish | 7121.0 | 0.011 |
| bg | Bulgarian | ru | Russian | 7001.0 | 0.1968 |
| en | English | de | German | 6801.0 | 0.0105 |
| de | German | ru | Russian | 6470.0 | 0.0589 |
| ru | Russian | es | Spanish | 6228.0 | 0.0003 |
| ru | Russian | fr | French | 5168.0 | 0.0002 |
| en | English | it | Italian | 5061.0 | 0.0078 |


### bigdata_pipeline/analysis/language_v2/language_homophily  (47 lignes, 9 colonnes)

| language | language_name | forwards_out | forwards_in | same_language_share | expected_share | lift | audience_entropy_bits | audience_effective_languages |
|---|---|---|---|---|---|---|---|---|
| ru | Russian | 24483432 | 24545632 | 0.9924 | 0.9258 | 1.07 | 0.0876 | 1.06 |
| uk | Ukrainian | 707677 | 650715 | 0.8171 | 0.0245 | 33.29 | 0.7339 | 1.66 |
| en | English | 647299 | 580153 | 0.8143 | 0.0219 | 37.21 | 1.1047 | 2.15 |
| fa | Persian | 199404 | 200646 | 0.9917 | 0.0076 | 131.05 | 0.079 | 1.06 |
| de | German | 109818 | 111454 | 0.9189 | 0.0042 | 218.6 | 0.4924 | 1.41 |
| es | Spanish | 92054 | 99797 | 0.9333 | 0.0038 | 247.94 | 0.4684 | 1.38 |
| ar | Arabic | 79266 | 76135 | 0.9431 | 0.0029 | 328.44 | 0.4318 | 1.35 |
| it | Italian | 47237 | 57437 | 0.8955 | 0.0022 | 413.39 | 0.645 | 1.56 |
| bg | Bulgarian | 35574 | 44765 | 0.7763 | 0.0017 | 459.77 | 0.942 | 1.92 |
| fr | French | 29332 | 47482 | 0.8215 | 0.0018 | 458.69 | 0.9693 | 1.96 |
| et | Estonian | 20614 | 13339 | 0.1783 | 0.0005 | 354.35 | 1.398 | 2.64 |
| mk | Macedonian | 15938 | 18895 | 0.8948 | 0.0007 | 1255.55 | 0.5951 | 1.51 |
| sk | Slovak | 10937 | 30604 | 0.6605 | 0.0012 | 572.22 | 1.2319 | 2.35 |
| he | Hebrew | 7977 | 7844 | 0.9158 | 0.0003 | 3095.33 | 0.4553 | 1.37 |
| tr | Turkish | 5292 | 4900 | 0.559 | 0.0002 | 3024.45 | 1.3182 | 2.49 |
| ro | Romanian | 4523 | 1697 | 0.1826 | 0.0001 | 2853.23 | 1.0028 | 2.0 |
| cs | Czech | 4132 | 7338 | 0.8311 | 0.0003 | 3002.8 | 0.8548 | 1.81 |
| pt | Portuguese | 3756 | 2830 | 0.5916 | 0.0001 | 5542.38 | 1.6072 | 3.05 |
| lv | Latvian | 1130 | 2384 | 0.0027 | 0.0001 | 29.53 | 0.093 | 1.07 |
| hr | Croatian | 962 | 279 | 0.0146 | 0.0 | 1382.97 | 1.1476 | 2.22 |
| el | Greek | 861 | 1917 | 0.698 | 0.0001 | 9654.14 | 1.3468 | 2.54 |
| pl | Polish | 710 | 191 | 0.1394 | 0.0 | 19355.66 | 1.5189 | 2.87 |
| af | Afrikaans | 660 | 116 | 0.0 | 0.0 | 0.0 | 1.5836 | 3.0 |
| ca | Catalan | 657 | 272 | 0.0548 | 0.0 | 5341.12 | 0.6831 | 1.61 |
| no | Norwegian | 558 | 148 | 0.009 | 0.0 | 1605.23 | 0.656 | 1.58 |
| tl | Tagalog | 510 | 14 | 0.0 | 0.0 | 0.0 | 0.4027 | 1.32 |
| id | Indonesian | 463 | 239 | 0.324 | 0.0 | 35939.9 | 1.9512 | 3.87 |
| so | Somali | 341 | 166 | 0.0 | 0.0 | 0.0 | 0.9188 | 1.89 |
| nl | Dutch | 275 | 1220 | 0.0036 | 0.0 | 79.03 | 1.5602 | 2.95 |
| ja | Japanese | 275 | 2367 | 0.0582 | 0.0001 | 651.71 | 1.4297 | 2.69 |
| vi | Vietnamese | 244 | 1148 | 0.4139 | 0.0 | 9559.92 | 1.5585 | 2.95 |
| sv | Swedish | 235 | 476 | 0.1404 | 0.0 | 7821.74 | 1.3973 | 2.63 |
| sq | Albanian | 209 | 46 | 0.0 | 0.0 | 0.0 | 1.35 | 2.55 |
| hu | Hungarian | 200 | 89 | 0.275 | 0.0 | 81923.24 | 1.5024 | 2.83 |
| pa | Punjabi | 157 | 42 | 0.0 | 0.0 | 0.0 | 1.3794 | 2.6 |
| sw | Swahili | 152 | 192 | 0.3816 | 0.0 | 52692.36 | 0.9591 | 1.94 |
| fi | Finnish | 127 | 9 | 0.0 | 0.0 | 0.0 | 1.1364 | 2.2 |
| zh-cn | Chinese | 90 | 32 | 0.0 | 0.0 | 0.0 | 1.102 | 2.15 |
| lt | Lithuanian | 83 | 16 | 0.0964 | 0.0 | 159718.92 | 0.5497 | 1.46 |
| da | Danish | 61 | 314 | 0.0984 | 0.0 | 8305.32 | 1.1147 | 2.17 |


### bigdata_pipeline/analysis/language_v2/language_spread  (14 lignes, 7 colonnes)

| language | language_name | channels | communities | largest_community | share_in_largest | communities_for_80pct |
|---|---|---|---|---|---|---|
| ru | Russian | 58859 | 582 | 0 | 0.1771 | 13 |
| uk | Ukrainian | 3299 | 55 | 5 | 0.8466 | 1 |
| en | English | 2822 | 147 | 3 | 0.5535 | 5 |
| fa | Persian | 1576 | 63 | 12 | 0.8832 | 1 |
| de | German | 788 | 17 | 9 | 0.953 | 1 |
| bg | Bulgarian | 282 | 28 | 15 | 0.383 | 3 |
| es | Spanish | 233 | 8 | 3 | 0.9356 | 1 |
| ar | Arabic | 201 | 17 | 44 | 0.4378 | 4 |
| et | Estonian | 191 | 17 | 19 | 0.4346 | 3 |
| it | Italian | 184 | 8 | 3 | 0.8641 | 1 |
| fr | French | 183 | 14 | 3 | 0.7923 | 2 |
| mk | Macedonian | 125 | 10 | 43 | 0.832 | 1 |
| tr | Turkish | 86 | 16 | 6 | 0.2791 | 6 |
| he | Hebrew | 56 | 9 | 55 | 0.3571 | 3 |


### bigdata_pipeline/analysis/language_v2/language_summary  (21 lignes, 2 colonnes)

| measure | value |
|---|---|
| channels_in_graph | 267518.0 |
| channels_with_language | 69213.0 |
| coverage | 0.2587 |
| communities | 822.0 |
| languages | 47.0 |
| weighted_purity | 0.9521 |
| language_entropy_bits | 1.0413 |
| effective_languages | 2.06 |
| majority_language_share | 0.8504 |
| NMI | 0.2491 |
| ARI | 0.0358 |
| homogeneity | 0.6938 |
| completeness | 0.1518 |
| communities_with_3plus_known | 152.0 |
| median_purity | 1.0 |
| share_communities_purity_ge_0.8 | 0.9276 |
| forwards_between_known | 26513340.0 |
| forwards_same_language_share | 0.9806 |
| forwards_expected_same_language_share | 0.8562 |
| forwards_lift | 1.15 |
| forwards_assortativity | 0.865 |


### bigdata_pipeline/analysis/language_v2/language_top_channels  (120 lignes, 7 colonnes)

| language | language_name | rank | channel_id | community | times_forwarded | forwards_made |
|---|---|---|---|---|---|---|
| ru | Russian | 1 | 1101170442 | 1 | 278065 | 0 |
| ru | Russian | 2 | 1394050290 | 2 | 258381 | 0 |
| ru | Russian | 3 | 1101806611 | 1 | 165852 | 716 |
| ru | Russian | 4 | 1069772626 | 1 | 162612 | 211 |
| ru | Russian | 5 | 1355540894 | 1 | 128081 | 13 |
| ru | Russian | 6 | 1343623236 | 17 | 125768 | 118 |
| ru | Russian | 7 | 1050820672 | 1 | 124769 | 216 |
| ru | Russian | 8 | 1267862369 | 17 | 122339 | 14289 |
| ru | Russian | 9 | 1082968817 | 1 | 113914 | 189 |
| ru | Russian | 10 | 1754988582 | 17 | 112896 | 3330 |


### bigdata_pipeline/analysis/language_v2/language_yearly  (9 lignes, 12 colonnes)

| year | active_channels | active_with_language | languages | top_language | top_language_share | language_entropy_bits | effective_languages | forwards_between_known | same_language_share | expected_same_language_share | assortativity |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 2016 | 1647 | 604 | 10 | ru | 0.4983 | 1.2811 | 2.43 | 8805 | 0.9633 | 0.7345 | 0.8618 |
| 2017 | 5842 | 2268 | 12 | ru | 0.7945 | 0.9378 | 1.92 | 127707 | 0.9903 | 0.816 | 0.9474 |
| 2018 | 9979 | 4261 | 16 | ru | 0.8681 | 0.7785 | 1.72 | 322911 | 0.9928 | 0.9513 | 0.8524 |
| 2019 | 14638 | 7091 | 20 | ru | 0.8665 | 0.8337 | 1.78 | 603947 | 0.991 | 0.9413 | 0.8468 |
| 2020 | 25274 | 12844 | 25 | ru | 0.8616 | 0.9121 | 1.88 | 1436279 | 0.9899 | 0.9468 | 0.8106 |
| 2021 | 35763 | 18903 | 37 | ru | 0.8455 | 1.0207 | 2.03 | 1951127 | 0.9898 | 0.9255 | 0.8627 |
| 2022 | 78480 | 39048 | 43 | ru | 0.8628 | 0.9523 | 1.93 | 6473690 | 0.9783 | 0.8746 | 0.8266 |
| 2023 | 123665 | 55058 | 44 | ru | 0.8649 | 0.9524 | 1.94 | 8051397 | 0.9799 | 0.8649 | 0.851 |
| 2024 | 182621 | 57965 | 44 | ru | 0.853 | 1.0245 | 2.03 | 7537321 | 0.9777 | 0.7897 | 0.894 |


### bigdata_pipeline/analysis/language_v2/language_yearly_by_language  (65 lignes, 8 colonnes)

| year | language | language_name | active_channels | share_of_active | forwards_out | same_language_share | lift |
|---|---|---|---|---|---|---|---|
| 2016 | ar | Arabic | 2 | 0.0033 | 2 | 0.0 |  |
| 2017 | ar | Arabic | 1 | 0.0004 | 1 | 0.0 |  |
| 2018 | ar | Arabic | 4 | 0.0009 | 5 | 0.0 |  |
| 2019 | ar | Arabic | 3 | 0.0004 | 57 | 0.9825 | 10595.56 |
| 2020 | ar | Arabic | 37 | 0.0029 | 2996 | 0.9997 | 479.4 |
| 2021 | ar | Arabic | 51 | 0.0027 | 10328 | 0.997 | 188.77 |
| 2022 | ar | Arabic | 70 | 0.0018 | 21552 | 0.9117 | 297.14 |
| 2023 | ar | Arabic | 132 | 0.0024 | 23144 | 0.9133 | 338.42 |
| 2024 | ar | Arabic | 165 | 0.0028 | 21181 | 0.9738 | 346.4 |
| 2017 | de | German | 1 | 0.0004 | 1 | 0.0 |  |
| 2018 | de | German | 2 | 0.0005 | 2 | 0.0 |  |
| 2019 | de | German | 17 | 0.0024 | 39 | 0.0513 | 6194.33 |
| 2020 | de | German | 178 | 0.0139 | 1946 | 0.8546 | 667.43 |
| 2021 | de | German | 600 | 0.0317 | 14047 | 0.9649 | 131.61 |
| 2022 | de | German | 604 | 0.0155 | 14296 | 0.7801 | 382.84 |
| 2023 | de | German | 605 | 0.011 | 13869 | 0.8276 | 507.1 |
| 2024 | de | German | 646 | 0.0111 | 65618 | 0.9611 | 105.03 |
| 2016 | en | English | 11 | 0.0182 | 211 | 0.0095 | 41.73 |
| 2017 | en | English | 28 | 0.0123 | 819 | 0.0147 | 116.95 |
| 2018 | en | English | 77 | 0.0181 | 1296 | 0.1806 | 236.05 |
| 2019 | en | English | 169 | 0.0238 | 2727 | 0.5046 | 197.76 |
| 2020 | en | English | 308 | 0.024 | 4821 | 0.615 | 252.53 |
| 2021 | en | English | 709 | 0.0375 | 12331 | 0.6839 | 139.49 |
| 2022 | en | English | 1416 | 0.0363 | 100783 | 0.6784 | 54.64 |
| 2023 | en | English | 2234 | 0.0406 | 207283 | 0.8162 | 35.69 |
| 2024 | en | English | 2454 | 0.0423 | 317026 | 0.8722 | 21.85 |
| 2019 | es | Spanish | 3 | 0.0004 | 45 | 0.0 |  |
| 2020 | es | Spanish | 5 | 0.0004 | 20 | 0.0 |  |
| 2021 | es | Spanish | 9 | 0.0005 | 136 | 0.0368 | 14346.52 |
| 2022 | es | Spanish | 137 | 0.0035 | 18096 | 0.8968 | 280.26 |
| 2023 | es | Spanish | 202 | 0.0037 | 36766 | 0.9296 | 186.52 |
| 2024 | es | Spanish | 219 | 0.0038 | 36991 | 0.9597 | 185.71 |
| 2016 | fa | Persian | 280 | 0.4636 | 1176 | 0.9932 | 7.34 |
| 2017 | fa | Persian | 384 | 0.1693 | 12257 | 0.9966 | 10.38 |
| 2018 | fa | Persian | 350 | 0.0821 | 6490 | 0.9909 | 49.57 |
| 2019 | fa | Persian | 406 | 0.0573 | 12455 | 0.9935 | 48.25 |
| 2020 | fa | Persian | 434 | 0.0338 | 18546 | 0.9983 | 77.3 |
| 2021 | fa | Persian | 452 | 0.0239 | 21556 | 0.9917 | 90.51 |
| 2022 | fa | Persian | 452 | 0.0116 | 23229 | 0.9801 | 268.83 |
| 2023 | fa | Persian | 602 | 0.0109 | 34472 | 0.989 | 227.45 |


## Figures : analysis/figures/language_communities

![/home/dvopssl/Documents/telescope_data_analysis/bigdata_pipeline/analysis/figures/language_communities/assortativity_by_year.png](/home/dvopssl/Documents/telescope_data_analysis/bigdata_pipeline/analysis/figures/language_communities/assortativity_by_year.png)

![/home/dvopssl/Documents/telescope_data_analysis/bigdata_pipeline/analysis/figures/language_communities/community_purity.png](/home/dvopssl/Documents/telescope_data_analysis/bigdata_pipeline/analysis/figures/language_communities/community_purity.png)

![/home/dvopssl/Documents/telescope_data_analysis/bigdata_pipeline/analysis/figures/language_communities/homophily_by_year.png](/home/dvopssl/Documents/telescope_data_analysis/bigdata_pipeline/analysis/figures/language_communities/homophily_by_year.png)

![/home/dvopssl/Documents/telescope_data_analysis/bigdata_pipeline/analysis/figures/language_communities/language_activity.png](/home/dvopssl/Documents/telescope_data_analysis/bigdata_pipeline/analysis/figures/language_communities/language_activity.png)

![/home/dvopssl/Documents/telescope_data_analysis/bigdata_pipeline/analysis/figures/language_communities/language_bridges.png](/home/dvopssl/Documents/telescope_data_analysis/bigdata_pipeline/analysis/figures/language_communities/language_bridges.png)

![/home/dvopssl/Documents/telescope_data_analysis/bigdata_pipeline/analysis/figures/language_communities/language_distribution.png](/home/dvopssl/Documents/telescope_data_analysis/bigdata_pipeline/analysis/figures/language_communities/language_distribution.png)

![/home/dvopssl/Documents/telescope_data_analysis/bigdata_pipeline/analysis/figures/language_communities/language_diversity_entropy.png](/home/dvopssl/Documents/telescope_data_analysis/bigdata_pipeline/analysis/figures/language_communities/language_diversity_entropy.png)

![/home/dvopssl/Documents/telescope_data_analysis/bigdata_pipeline/analysis/figures/language_communities/language_flows_heatmap.png](/home/dvopssl/Documents/telescope_data_analysis/bigdata_pipeline/analysis/figures/language_communities/language_flows_heatmap.png)

![/home/dvopssl/Documents/telescope_data_analysis/bigdata_pipeline/analysis/figures/language_communities/language_homophily.png](/home/dvopssl/Documents/telescope_data_analysis/bigdata_pipeline/analysis/figures/language_communities/language_homophily.png)

![/home/dvopssl/Documents/telescope_data_analysis/bigdata_pipeline/analysis/figures/language_communities/language_inference_accuracy.png](/home/dvopssl/Documents/telescope_data_analysis/bigdata_pipeline/analysis/figures/language_communities/language_inference_accuracy.png)

![/home/dvopssl/Documents/telescope_data_analysis/bigdata_pipeline/analysis/figures/language_communities/language_neighbour_diversity.png](/home/dvopssl/Documents/telescope_data_analysis/bigdata_pipeline/analysis/figures/language_communities/language_neighbour_diversity.png)

![/home/dvopssl/Documents/telescope_data_analysis/bigdata_pipeline/analysis/figures/language_communities/language_share_by_year.png](/home/dvopssl/Documents/telescope_data_analysis/bigdata_pipeline/analysis/figures/language_communities/language_share_by_year.png)

![/home/dvopssl/Documents/telescope_data_analysis/bigdata_pipeline/analysis/figures/language_communities/language_yearly_cohesion.png](/home/dvopssl/Documents/telescope_data_analysis/bigdata_pipeline/analysis/figures/language_communities/language_yearly_cohesion.png)

![/home/dvopssl/Documents/telescope_data_analysis/bigdata_pipeline/analysis/figures/language_communities/language_yearly_diversity.png](/home/dvopssl/Documents/telescope_data_analysis/bigdata_pipeline/analysis/figures/language_communities/language_yearly_diversity.png)

![/home/dvopssl/Documents/telescope_data_analysis/bigdata_pipeline/analysis/figures/language_communities/language_yearly_homophily.png](/home/dvopssl/Documents/telescope_data_analysis/bigdata_pipeline/analysis/figures/language_communities/language_yearly_homophily.png)

![/home/dvopssl/Documents/telescope_data_analysis/bigdata_pipeline/analysis/figures/language_communities/language_yearly_shares.png](/home/dvopssl/Documents/telescope_data_analysis/bigdata_pipeline/analysis/figures/language_communities/language_yearly_shares.png)


# Thème 3 — Traçabilité


## Tables : analysis/tracing


### bigdata_pipeline/analysis/tracing/chain_size_distribution  (8 lignes, 5 colonnes)

| size_class | original_posts | relays | share_of_posts | share_of_relays |
|---|---|---|---|---|
| 1 relay | 15847775 | 15847775 | 0.7708 | 0.4998 |
| 2 relays | 2701920 | 5403840 | 0.1314 | 0.1704 |
| 3 to 5 | 1510705 | 5379539 | 0.0735 | 0.1697 |
| 6 to 10 | 373281 | 2698253 | 0.0182 | 0.0851 |
| 11 to 50 | 124117 | 2136330 | 0.006 | 0.0674 |
| 51 to 100 | 2776 | 180260 | 0.0001 | 0.0057 |
| 101 to 1000 | 351 | 52628 | 0.0 | 0.0017 |
| over 1000 | 3 | 7290 | 0.0 | 0.0002 |


### bigdata_pipeline/analysis/tracing/delay_by_year  (10 lignes, 5 colonnes)

| year | relays | median_delay_s | share_within_1h | share_within_1day |
|---|---|---|---|---|
| 2015 | 877 | 6096.0 | 0.4493 | 0.6784 |
| 2016 | 16566 | 3144.0 | 0.5156 | 0.856 |
| 2017 | 174080 | 1542.0 | 0.6084 | 0.8878 |
| 2018 | 418240 | 1468.0 | 0.6292 | 0.9376 |
| 2019 | 745079 | 1749.0 | 0.6057 | 0.9372 |
| 2020 | 1694537 | 1836.0 | 0.5998 | 0.9427 |
| 2021 | 2238910 | 2209.0 | 0.5695 | 0.9331 |
| 2022 | 7237603 | 2105.0 | 0.5768 | 0.9418 |
| 2023 | 9365093 | 3071.0 | 0.5213 | 0.9004 |
| 2024 | 9814930 | 3533.0 | 0.5025 | 0.8813 |


### bigdata_pipeline/analysis/tracing/delay_distribution  (8 lignes, 5 colonnes)

| delay_class | relays | share_of_relays | first_relays | share_of_first_relays |
|---|---|---|---|---|
| before the original (negative) | 0 | 0.0 | 0 | 0.0 |
| under 1 min | 4085461 | 0.1289 | 3279976 | 0.1595 |
| 1 to 10 min | 6080174 | 0.1918 | 4528123 | 0.2202 |
| 10 to 60 min | 6943860 | 0.219 | 4457848 | 0.2168 |
| 1 to 24 h | 11735829 | 0.3701 | 6655670 | 0.3237 |
| 1 to 7 days | 2011934 | 0.0635 | 1159221 | 0.0564 |
| 7 to 30 days | 379870 | 0.012 | 216043 | 0.0105 |
| over 30 days | 468787 | 0.0148 | 264047 | 0.0128 |


### bigdata_pipeline/analysis/tracing/source_concentration  (6 lignes, 3 colonnes)

| top_share_of_sources | sources | share_of_relays |
|---|---|---|
| 0.001 | 260 | 0.2707 |
| 0.01 | 2603 | 0.585 |
| 0.05 | 13013 | 0.8234 |
| 0.1 | 26026 | 0.9019 |
| 0.25 | 65064 | 0.9682 |
| 0.5 | 130128 | 0.9919 |


### bigdata_pipeline/analysis/tracing/source_verification  (7 lignes, 6 colonnes)

| measure | original_posts | share_of_posts | relays | share_of_relays | meaning |
|---|---|---|---|---|---|
| origin_channel_in_corpus | 16643874 | 0.8095 | 26964099 | 0.8504 | the source channel has messages in the d |
| origin_post_found | 8927592 | 0.4342 | 14922660 | 0.4707 | the original post itself is in the datas |
| origin_post_missing_channel_present | 7716282 | 0.3753 | 12041439 | 0.3798 | channel in the dataset but this post is  |
| origin_channel_not_in_corpus | 3917054 | 0.1905 | 4741816 | 0.1496 | the source channel was never collected:  |
| date_identical | 8927253 | 0.4342 | 14922235 | 0.4706 | the header date equals the date of the p |
| date_within_60s | 8927490 | 0.4342 | 14922528 | 0.4707 | the header date is within one minute of  |
| date_differs | 102 | 0.0 | 132 | 0.0 | header date and post date differ by more |


### bigdata_pipeline/analysis/tracing/top_origin_posts  (100 lignes, 5 colonnes)

| origin_channel | origin_post | relays | first_relay_delay_s | last_relay_delay_s |
|---|---|---|---|---|
| 1004069147 | 218585 | 4809 | 86186 | 143165081 |
| 1773308568 | 570 | 1327 | 998 | 29143152 |
| 1137311669 | 19236 | 1154 | 48772 | 124292287 |
| 1790907266 | 2015 | 708 | 7 | 434594 |
| 1883034066 | 11275 | 673 | 3 | 34478465 |
| 1790907266 | 3362 | 629 | 7 | 242991 |
| 1254642005 | 10040 | 535 | 30901 | 60605219 |
| 1254642005 | 83972 | 531 | 68626 | 25329664 |
| 1760203839 | 18 | 518 | 86767 | 65242306 |
| 1790907266 | 3308 | 497 | 6 | 89530 |


### bigdata_pipeline/analysis/tracing/top_sources  (50 lignes, 7 colonnes)

| origin_channel | original_posts | relays | relaying_channels | relays_per_post | share_of_relays | language |
|---|---|---|---|---|---|---|
| 1101170442 | 117655 | 278065 | 7366 | 2.36 | 0.00877 | ru |
| 1394050290 | 109248 | 258381 | 6516 | 2.37 | 0.00815 | ru |
| 1101806611 | 55160 | 165853 | 3610 | 3.01 | 0.00523 | ru |
| 1069772626 | 55208 | 162612 | 5035 | 2.95 | 0.00513 | ru |
| 1355540894 | 47798 | 128081 | 2735 | 2.68 | 0.00404 | ru |
| 1343623236 | 4607 | 125768 | 2114 | 27.3 | 0.00397 | ru |
| 1050820672 | 78062 | 124769 | 5187 | 1.6 | 0.00394 | ru |
| 1267862369 | 18539 | 122356 | 250 | 6.6 | 0.00386 | ru |
| 1082968817 | 25606 | 113914 | 3735 | 4.45 | 0.00359 | ru |
| 1754988582 | 19399 | 112909 | 514 | 5.82 | 0.00356 | ru |
| 1315735637 | 53342 | 102540 | 3629 | 1.92 | 0.00323 | ru |
| 1099350027 | 66287 | 99212 | 4653 | 1.5 | 0.00313 | ru |
| 1260622817 | 40025 | 96603 | 5341 | 2.41 | 0.00305 | ru |
| 1326223284 | 28041 | 92847 | 2880 | 3.31 | 0.00293 | ru |
| 1463721328 | 10321 | 87163 | 995 | 8.45 | 0.00275 | uk |
| 1109403194 | 19109 | 83793 | 3375 | 4.39 | 0.00264 | ru |
| 1252230500 | 24056 | 76472 | 178 | 3.18 | 0.00241 | ru |
| 1175084215 | 48942 | 75933 | 2483 | 1.55 | 0.00239 | ru |
| 1429994323 | 11792 | 74877 | 1331 | 6.35 | 0.00236 | ru |
| 1377658857 | 13190 | 73244 | 554 | 5.55 | 0.00231 | ru |
| 1074354585 | 34007 | 73241 | 2078 | 2.15 | 0.00231 | ru |
| 1065276858 | 14041 | 72482 | 2008 | 5.16 | 0.00229 | ru |
| 1111348665 | 40944 | 71568 | 2564 | 1.75 | 0.00226 | ru |
| 1647639783 | 17537 | 68289 | 2298 | 3.89 | 0.00215 | ru |
| 1410611019 | 24480 | 65557 | 518 | 2.68 | 0.00207 | ru |
| 1210987817 | 7789 | 64936 | 2478 | 8.34 | 0.00205 | ru |
| 1154016292 | 29633 | 60755 | 377 | 2.05 | 0.00192 | ru |
| 1012103617 | 23217 | 56396 | 2626 | 2.43 | 0.00178 | ru |
| 1133816508 | 24724 | 56392 | 513 | 2.28 | 0.00178 | ru |
| 1513431778 | 19791 | 55528 | 2642 | 2.81 | 0.00175 | ru |
| 1117628569 | 24977 | 54259 | 4517 | 2.17 | 0.00171 | ru |
| 1136723856 | 15570 | 52690 | 381 | 3.38 | 0.00166 | ru |
| 1736895964 | 12560 | 52221 | 2309 | 4.16 | 0.00165 | ru |
| 1633432371 | 10685 | 51822 | 451 | 4.85 | 0.00163 | ru |
| 1498939244 | 21920 | 51353 | 2228 | 2.34 | 0.00162 | ru |
| 1111072403 | 31499 | 51202 | 2025 | 1.63 | 0.00161 | ru |
| 1283359437 | 18640 | 50536 | 2161 | 2.71 | 0.00159 | ru |
| 1135021433 | 11974 | 48669 | 2508 | 4.06 | 0.00154 | ru |
| 1378813139 | 20015 | 47439 | 3465 | 2.37 | 0.0015 | ru |
| 1126629353 | 14886 | 45809 | 2032 | 3.08 | 0.00144 | ru |


### bigdata_pipeline/analysis/tracing/traceability_by_year  (33 lignes, 3 colonnes)

| year | level | messages |
|---|---|---|
| 2015 | A | 877 |
| 2015 | C | 2006 |
| 2016 | A | 16566 |
| 2016 | C | 14167 |
| 2017 | A | 174080 |
| 2017 | B | 1 |
| 2017 | C | 13010 |
| 2018 | A | 418240 |
| 2018 | C | 7087 |
| 2019 | A | 745079 |
| 2019 | B | 1 |
| 2019 | D | 925 |
| 2019 | C | 5683 |
| 2020 | A | 1694537 |
| 2020 | B | 254 |
| 2020 | D | 2962 |
| 2020 | C | 9788 |
| 2021 | A | 2238910 |
| 2021 | B | 1185 |
| 2021 | D | 6116 |
| 2021 | C | 14704 |
| 2022 | A | 7237603 |
| 2022 | B | 11682 |
| 2022 | D | 64955 |
| 2022 | C | 36512 |
| 2023 | A | 9365093 |
| 2023 | B | 47561 |
| 2023 | D | 226009 |
| 2023 | C | 244713 |
| 2024 | A | 9814930 |
| 2024 | B | 44241 |
| 2024 | D | 351990 |
| 2024 | C | 199378 |


### bigdata_pipeline/analysis/tracing/traceability_levels  (4 lignes, 4 colonnes)

| level | meaning | messages | share_of_forwards |
|---|---|---|---|
| A | forwarded from a channel, original post  | 31705915 | 0.96047 |
| B | forwarded from a channel, original post  | 104925 | 0.00318 |
| C | forwarded from a user (source is a perso | 547048 | 0.01657 |
| D | origin hidden by Telegram privacy (sourc | 652957 | 0.01978 |


### bigdata_pipeline/analysis/tracing/tracing_protocol.md

```
# Tracing protocol - theme 3

Generated by `source_tracing_v2.py` on 2026-11-11.

## What the data allows

Telegram stores only the **original author** in the header of a forward. Each relay therefore points directly to its source (channel, post id, date of the original post). Intermediate hops of a chain are not recorded: the chain of an original post is its list of relays ordered by time.

## Steps

1. Read the forward header: origin channel, origin post id, origin date.
2. Classify the traceability level:
   - **A** - forwarded from a channel, original post known (traceable to the post)
   - **B** - forwarded from a channel, original post id missing (traceable to the channel)
   - **C** - forwarded from a user (source is a person)
   - **D** - origin hidden by Telegram privacy (source unknown)
3. For level A, verify the source against the dataset: origin channel present, original post present, header date equal to the date of the post found.
4. Order the relays of each original post by time (rank) and compute the delay to the original post.
5. Report the sources (concentration, most relayed), the reach (relays per post) and the speed (delays).

## Measured on the dataset

- Relays read from chains: 31,705,915; duplicated relays removed: 0; relays kept: 31,705,915.
- Original posts: 20,560,928 from 260,256 source channels, relayed by 60,769 channels.
- Relays per post: mean 1.542, median 1, maximum 4,809; 77.1% of posts have a single relay.
- Median delay of the first relay: 1676 s; 54.0% of relays occur within one hour; 0 relays carry a date earlier than the original post (to inspect).

### Traceability levels (all forwarded messages)

| Level | Meaning | Messages | Share |
|---|---|---|---|
| A | forwarded from a channel, original post known (traceable to the post) | 31,705,915 | 96.05% |
| B | forwarded from a channel, original post id missing (traceable to the channel) | 104,925 | 0.32% |
| C | forwarded from a user (source is a person) | 547,048 | 1.66% |
| D | origin hidden by Telegram privacy (source unknown) | 652,957 | 1.98% |

### Source verification (level A)

| Check | Original posts | Relays | Share of relays |
|---|---|---|---|
| origin_channel_in_corpus | 16,643,874 | 26,964,099 | 85.0% |
| origin_post_found | 8,927,592 | 14,922,660 | 47.1% |
| origin_post_missing_channel_present | 7,716,282 | 12,041,439 | 38.0% |
| origin_channel_not_in_corpus | 3,917,054 | 4,741,816 | 15.0% |
| date_identical | 8,927,253 | 14,922,235 | 47.1% |
| date_within_60s | 8,927,490 | 14,922,528 | 47.1% |
| date_differs | 102 | 132 | 0.0% |

## Limits

- Hop-by-hop depth cannot be measured: only the original author is kept in a forward.
- A post missing from the dataset is not proof that it never existed (deleted, outside the collected period).
- Delays are measured in seconds between the date in the forward header and the date of the relay.
```


### bigdata_pipeline/analysis/tracing/tracing_summary  (13 lignes, 2 colonnes)

| measure | value |
|---|---|
| relays_after_deduplication | 31705915.0 |
| original_posts | 20560928.0 |
| origin_channels | 260256.0 |
| relaying_channels | 60769.0 |
| mean_relays_per_post | 1.542 |
| median_relays_per_post | 1.0 |
| max_relays_per_post | 4809.0 |
| posts_with_one_relay_share | 0.7708 |
| median_first_relay_delay_s | 1676.0 |
| relays_within_1h_share | 0.5396 |
| relays_before_original | 0.0 |
| raw_relays | 31705915.0 |
| duplicated_relays_removed | 0.0 |


## Figures : analysis/figures/traceability

![/home/dvopssl/Documents/telescope_data_analysis/bigdata_pipeline/analysis/figures/traceability/chain_size_distribution.png](/home/dvopssl/Documents/telescope_data_analysis/bigdata_pipeline/analysis/figures/traceability/chain_size_distribution.png)

![/home/dvopssl/Documents/telescope_data_analysis/bigdata_pipeline/analysis/figures/traceability/delay_by_year.png](/home/dvopssl/Documents/telescope_data_analysis/bigdata_pipeline/analysis/figures/traceability/delay_by_year.png)

![/home/dvopssl/Documents/telescope_data_analysis/bigdata_pipeline/analysis/figures/traceability/delay_distribution.png](/home/dvopssl/Documents/telescope_data_analysis/bigdata_pipeline/analysis/figures/traceability/delay_distribution.png)

![/home/dvopssl/Documents/telescope_data_analysis/bigdata_pipeline/analysis/figures/traceability/source_concentration.png](/home/dvopssl/Documents/telescope_data_analysis/bigdata_pipeline/analysis/figures/traceability/source_concentration.png)

![/home/dvopssl/Documents/telescope_data_analysis/bigdata_pipeline/analysis/figures/traceability/source_verification.png](/home/dvopssl/Documents/telescope_data_analysis/bigdata_pipeline/analysis/figures/traceability/source_verification.png)

![/home/dvopssl/Documents/telescope_data_analysis/bigdata_pipeline/analysis/figures/traceability/top_sources.png](/home/dvopssl/Documents/telescope_data_analysis/bigdata_pipeline/analysis/figures/traceability/top_sources.png)

![/home/dvopssl/Documents/telescope_data_analysis/bigdata_pipeline/analysis/figures/traceability/traceability_levels.png](/home/dvopssl/Documents/telescope_data_analysis/bigdata_pipeline/analysis/figures/traceability/traceability_levels.png)


# Thème 4 — Villes et pics d'activité


## Tables : analysis/geo_cities


### bigdata_pipeline/analysis/geo_cities/README.md

```
# Theme 4, step 1 - city of each channel

Language of a channel, in order: Channel_Language.csv, then the language inferred by theme 2
(channel_language_inferred), then the candidate languages of channel_language_votes, then the language the
title is written in.

Methods (field `method` in channel_geo)
- direct_inferred: same search with the language inferred by theme 2.
- direct_votes: channels that only have vote candidates (e.g. 55 % ru, 40 % uk). Every candidate language
  with at least 20 % of the votes is searched. If several find a city, `language_basis` tells how one was
  chosen: timezone (only its city fits the channel's estimated UTC offset), timezone+share, share, only candidate.
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
- city_coverage (per language and method), city_totals (one row per city, all languages and methods),
  language_coverage (share of channels with a city per language), geo_summary.
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
```


### bigdata_pipeline/analysis/geo_cities/channel_city  (5731 lignes, 10 colonnes)

| channel_id | language | language_source | language_basis | country | city | field | matched_text | n_cities | title |
|---|---|---|---|---|---|---|---|---|---|
| 1936122264 | ru | channel_language |  | Russia | Khabarovsk | title | хабаровского | 1 | Управление культуры, спорта и молодежной |
| 1899766563 | ru | channel_language |  | Russia | Vladivostok | title | владивосток | 1 | Кстати, Владивосток |
| 1158379858 | ru | channel_language |  | Russia | Moscow | title | москве | 1 | Посольство Великобритании в Москве |
| 1966374544 | ru | channel_language |  | Russia | Vladivostok | title | владивосток | 1 | Штаб Надеждина / Владивосток |
| 1241969517 | ru | channel_language |  | Russia | Saint Petersburg | title | петербург | 1 | КП Петербург |
| 1947858156 | ru | channel_language |  | Russia | Saint Petersburg | title | петербург | 1 | КРП-Петербург |
| 1717227894 | ru | channel_language |  | Russia | Moscow | username | moscow | 1 | БК «Александр Невский» |
| 1582261949 | ru | channel_language |  | Russia | Sevastopol | title | севастополь | 1 | НОВОСТИ КРЫМ СЕВАСТОПОЛЬ |
| 1879150483 | ru | channel_language |  | Russia | Nizhny Novgorod | title | нижнии новгород | 1 | Подкастная «Подслушано» / Нижний Новгоро |
| 1915158995 | ru | channel_language |  | Russia | Tyumen | title | тюменская | 1 | Центр «ВОИН»/Тюменская область |


### bigdata_pipeline/analysis/geo_cities/channel_city_inferred  (30995 lignes, 5 colonnes)

| channel_id | country | city | vote_share | neighbour_forwards |
|---|---|---|---|---|
| 1000018574 | Iran | Mashhad | 1.0 | 1 |
| 1000029537 | Russia | Saratov | 1.0 | 21 |
| 1000058135 | Russia | Tyumen | 1.0 | 6 |
| 1000154882 | Russia | Saint Petersburg | 1.0 | 14 |
| 1000170429 | Iran | Mashhad | 0.8333 | 54 |
| 1000292318 | Iran | Mashhad | 1.0 | 1 |
| 1000336172 | Russia | Khabarovsk | 0.8889 | 9 |
| 1000438780 | Iran | Mashhad | 1.0 | 1 |
| 1000465800 | Russia | Krasnoyarsk | 1.0 | 1 |
| 1000482467 | Russia | Moscow | 1.0 | 3 |


### bigdata_pipeline/analysis/geo_cities/channel_geo  (36671 lignes, 15 colonnes)

| channel_id | language | language_origin | language_basis | country | city | evidence | matched_text | n_cities | method | confidence | city_utc_offset | tz_estimated_offset | tz_score |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1000000881 | ar | title_language |  | Syria | Damascus | title | دمشق | 1 | direct_title_language | 1.0 | 3.0 |  |  |
| 1000397649 | ru | channel_language |  | Russia | Voronezh | title | воронеж | 1 | direct_channel_language | 1.0 | 3.0 | 3.0 | 0.905 |
| 1000429582 | fa | inferred |  | Iran | Tehran | title | تهران | 1 | direct_inferred | 1.0 | 3.5 |  |  |
| 1000665140 | fa | channel_language |  | Iran | Tehran | title | تهران | 1 | direct_channel_language | 1.0 | 3.5 | 4.0 | 0.878 |
| 1000775711 | fa | channel_language |  | Iran | Tehran | title | تهران | 1 | direct_channel_language | 1.0 | 3.5 | 0.0 | 0.711 |
| 1001105740 | fa | inferred |  | Iran | Tehran | title | tehran | 1 | direct_inferred | 1.0 | 3.5 |  |  |
| 1001240445 | fa | inferred |  | Iran | Karaj | title | کرج | 1 | direct_inferred | 1.0 | 3.5 |  |  |
| 1001295932 | fa | inferred |  | Iran | Mashhad | title | مشهد | 1 | direct_inferred | 1.0 | 3.5 |  |  |
| 1001444948 | ru | channel_language |  | Russia | Moscow | title | москва | 1 | direct_channel_language | 1.0 | 3.0 | 2.0 | 0.799 |
| 1001615420 | fa | inferred |  | Iran | Tehran | title | تهران | 1 | direct_inferred | 1.0 | 3.5 |  |  |


### bigdata_pipeline/analysis/geo_cities/city_coverage  (326 lignes, 5 colonnes)

| language | country | city | method | n_channels |
|---|---|---|---|---|
| ru | Russia | Moscow | neighbours | 5796 |
| ru | Russia | Saint Petersburg | neighbours | 2475 |
| ru | Ukraine | Donetsk | neighbours | 2104 |
|  | Russia | Moscow | neighbours | 1395 |
| ru | Ukraine | Kharkiv | neighbours | 1016 |
| ru | Russia | Krasnodar | neighbours | 834 |
|  | Russia | Saint Petersburg | neighbours | 814 |
| ru | Russia | Khabarovsk | neighbours | 781 |
|  | Russia | Khabarovsk | neighbours | 773 |
| ru | Russia | Sevastopol | neighbours | 739 |
| ru | Russia | Moscow | direct_channel_language | 676 |
| ru | Russia | Rostov-on-Don | neighbours | 630 |
|  | Ukraine | Donetsk | neighbours | 574 |
| ru | Belarus | Minsk | neighbours | 549 |
| ru | Ukraine | Luhansk | neighbours | 504 |
| ru | Russia | Vladivostok | neighbours | 486 |
| ru | Russia | Saint Petersburg | direct_channel_language | 481 |
|  | Russia | Krasnodar | neighbours | 460 |
| ru | Russia | Kazan | neighbours | 417 |
|  | Ukraine | Kharkiv | neighbours | 387 |
| uk | Ukraine | Kyiv | neighbours | 373 |
| ru | Russia | Yekaterinburg | neighbours | 373 |
| ru | Russia | Krasnoyarsk | neighbours | 355 |
|  | Russia | Irkutsk | neighbours | 353 |
| ru | Russia | Volgograd | neighbours | 341 |
| ru | Russia | Voronezh | neighbours | 339 |
| ru | Russia | Tyumen | neighbours | 335 |
| ru | Russia | Irkutsk | neighbours | 333 |
| fa | Iran | Tehran | neighbours | 332 |
| ru | Russia | Samara | neighbours | 294 |
|  | Russia | Omsk | neighbours | 291 |
|  | Russia | Vladivostok | neighbours | 267 |
| ru | Ukraine | Donetsk | direct_channel_language | 266 |
|  | Russia | Sevastopol | neighbours | 262 |
|  | Russia | Rostov-on-Don | neighbours | 260 |
|  | Russia | Tyumen | neighbours | 228 |
|  | Russia | Krasnoyarsk | neighbours | 225 |
|  | Iran | Tehran | neighbours | 214 |
|  | Russia | Voronezh | neighbours | 205 |
|  | Ukraine | Kyiv | neighbours | 203 |


### bigdata_pipeline/analysis/geo_cities/city_totals  (90 lignes, 8 colonnes)

| country | city | n_channels | direct_channel_language | direct_inferred | direct_title_language | direct_votes | neighbours |
|---|---|---|---|---|---|---|---|
| Russia | Moscow | 8116 | 676 | 197 | 23 | 0 | 7220 |
| Russia | Saint Petersburg | 3949 | 481 | 161 | 6 | 0 | 3301 |
| Ukraine | Donetsk | 3076 | 266 | 65 | 7 | 0 | 2738 |
| Russia | Khabarovsk | 1766 | 167 | 40 | 5 | 0 | 1554 |
| Ukraine | Kharkiv | 1699 | 96 | 14 | 3 | 2 | 1584 |
| Russia | Krasnodar | 1538 | 183 | 54 | 4 | 0 | 1297 |
| Russia | Sevastopol | 1233 | 176 | 51 | 4 | 0 | 1002 |
| Russia | Rostov-on-Don | 1079 | 137 | 44 | 5 | 0 | 893 |
| Russia | Vladivostok | 880 | 91 | 33 | 3 | 0 | 753 |
| Russia | Irkutsk | 846 | 125 | 33 | 2 | 0 | 686 |
| Ukraine | Luhansk | 844 | 101 | 22 | 3 | 0 | 718 |
| Belarus | Minsk | 803 | 59 | 14 | 0 | 0 | 730 |
| Ukraine | Kyiv | 794 | 88 | 28 | 8 | 2 | 668 |
| Russia | Krasnoyarsk | 753 | 120 | 51 | 2 | 0 | 580 |
| Russia | Voronezh | 716 | 123 | 43 | 5 | 0 | 545 |
| Russia | Tyumen | 690 | 97 | 28 | 1 | 0 | 564 |
| Russia | Kazan | 689 | 78 | 38 | 4 | 0 | 569 |
| Russia | Volgograd | 675 | 105 | 31 | 8 | 0 | 531 |
| Russia | Yekaterinburg | 668 | 85 | 31 | 1 | 0 | 551 |
| Iran | Tehran | 620 | 45 | 24 | 0 | 0 | 551 |
| Russia | Omsk | 609 | 100 | 37 | 2 | 0 | 470 |
| Russia | Samara | 534 | 74 | 24 | 2 | 0 | 434 |
| Russia | Saratov | 438 | 75 | 17 | 1 | 0 | 345 |
| Russia | Chelyabinsk | 425 | 90 | 24 | 3 | 0 | 308 |
| Ukraine | Lviv | 363 | 30 | 11 | 4 | 0 | 318 |
| Russia | Perm | 348 | 71 | 21 | 0 | 0 | 256 |
| Russia | Ufa | 345 | 54 | 19 | 2 | 0 | 270 |
| Russia | Novosibirsk | 327 | 79 | 15 | 3 | 0 | 230 |
| Iran | Mashhad | 278 | 22 | 15 | 0 | 0 | 241 |
| Russia | Nizhny Novgorod | 268 | 51 | 22 | 2 | 0 | 193 |
| Ukraine | Kherson | 201 | 28 | 2 | 1 | 0 | 170 |
| Ukraine | Mykolaiv | 183 | 26 | 1 | 7 | 0 | 149 |
| Russia | Simferopol | 162 | 32 | 10 | 1 | 0 | 119 |
| Ukraine | Odesa | 150 | 39 | 4 | 2 | 2 | 103 |
| Ukraine | Dnipro | 126 | 24 | 5 | 1 | 1 | 95 |
| Ukraine | Zaporizhzhia | 22 | 17 | 1 | 4 | 0 | 0 |
| Ukraine | Poltava | 19 | 17 | 0 | 2 | 0 | 0 |
| Ukraine | Vinnytsia | 19 | 18 | 0 | 1 | 0 | 0 |
| Iran | Isfahan | 14 | 10 | 4 | 0 | 0 | 0 |
| Ukraine | Mariupol | 14 | 11 | 0 | 1 | 2 | 0 |


### bigdata_pipeline/analysis/geo_cities/geo_summary  (14 lignes, 3 colonnes)

| metric | value | share_of_metadata_channels |
|---|---|---|
| metadata channels | 534136 | 1.0 |
| with a language in Channel_Language.csv | 70741 | 0.1324 |
| with a language inferred by theme 2 | 29537 | 0.0553 |
| with only a vote table entry (language c | 683 | 0.0013 |
| ... of which the language was chosen wit | 6 | 0.0 |
| language found from the title only | 161 | 0.0003 |
| direct city (channel language) | 4250 | 0.008 |
| direct city (inferred language) | 1262 | 0.0024 |
| direct city (vote language) | 11 | 0.0 |
| direct city (title language) | 153 | 0.0003 |
| city from neighbours | 30995 | 0.058 |
| channels with a city, any method | 36656 | 0.0686 |
| channels with a timezone estimate and a  | 22265 | 0.0417 |
| ... of which city and timezone agree (wi | 21641 | 0.0405 |


### bigdata_pipeline/analysis/geo_cities/language_coverage  (48 lignes, 5 colonnes)

| language | n_channels | n_with_city | share_with_city | in_gazetteer |
|---|---|---|---|---|
| ru | 85399 | 25069 | 0.2936 | True |
| uk | 4454 | 1472 | 0.3305 | True |
| en | 3703 | 77 | 0.0208 | True |
| fa | 2853 | 585 | 0.205 | True |
|  | 1404 | 0 | 0.0 | False |
| de | 945 | 31 | 0.0328 | True |
| bg | 355 | 15 | 0.0423 | True |
| es | 317 | 6 | 0.0189 | True |
| ar | 315 | 13 | 0.0413 | True |
| it | 247 | 14 | 0.0567 | True |
| fr | 228 | 9 | 0.0395 | True |
| et | 216 | 14 | 0.0648 | False |
| mk | 187 | 4 | 0.0214 | True |
| tr | 98 | 5 | 0.051 | True |
| he | 67 | 0 | 0.0 | True |
| id | 44 | 0 | 0.0 | True |
| ro | 44 | 1 | 0.0227 | True |
| pt | 37 | 4 | 0.1081 | True |
| pl | 24 | 2 | 0.0833 | True |
| hr | 22 | 0 | 0.0 | True |
| ca | 13 | 0 | 0.0 | True |
| cs | 13 | 1 | 0.0769 | True |
| sk | 12 | 1 | 0.0833 | True |
| el | 10 | 2 | 0.2 | True |
| sv | 10 | 1 | 0.1 | True |
| so | 9 | 0 | 0.0 | True |
| nl | 9 | 0 | 0.0 | True |
| hu | 9 | 0 | 0.0 | True |
| da | 8 | 0 | 0.0 | True |
| lt | 7 | 0 | 0.0 | False |
| no | 7 | 0 | 0.0 | True |
| vi | 6 | 0 | 0.0 | True |
| ja | 6 | 0 | 0.0 | True |
| zh-cn | 6 | 0 | 0.0 | True |
| sw | 5 | 0 | 0.0 | False |
| fi | 4 | 0 | 0.0 | True |
| tl | 4 | 0 | 0.0 | True |
| lv | 4 | 1 | 0.25 | False |
| af | 4 | 0 | 0.0 | True |
| ur | 3 | 0 | 0.0 | True |


### bigdata_pipeline/analysis/geo_cities/propagation_accuracy  (14 lignes, 7 colonnes)

| variant | row | held_out_channels | accuracy | baseline_majority_city | held_out_total | with_labelled_neighbour |
|---|---|---|---|---|---|---|
| language only | 0.0-0.5 | 9 | 0.1111 | 0.1571 | 541 | 395 |
| language only | 0.5-0.6 | 17 | 0.4118 | 0.1571 | 541 | 395 |
| language only | 0.6-0.7 | 6 | 0.5 | 0.1571 | 541 | 395 |
| language only | 0.7-0.8 | 3 | 0.6667 | 0.1571 | 541 | 395 |
| language only | 0.8-0.9 | 25 | 0.88 | 0.1571 | 541 | 395 |
| language only | 0.9-1.0 | 335 | 0.9463 | 0.1571 | 541 | 395 |
| language only | >= 0.6 (rule used) | 369 | 0.9322 | 0.1571 | 541 | 395 |
| language + timezone | 0.0-0.5 | 8 | 0.125 | 0.1571 | 541 | 372 |
| language + timezone | 0.5-0.6 | 12 | 0.4167 | 0.1571 | 541 | 372 |
| language + timezone | 0.6-0.7 | 6 | 0.3333 | 0.1571 | 541 | 372 |
| language + timezone | 0.7-0.8 | 4 | 0.5 | 0.1571 | 541 | 372 |
| language + timezone | 0.8-0.9 | 22 | 0.9091 | 0.1571 | 541 | 372 |
| language + timezone | 0.9-1.0 | 320 | 0.95 | 0.1571 | 541 | 372 |
| language + timezone | >= 0.6 (rule used) | 352 | 0.9318 | 0.1571 | 541 | 372 |


### bigdata_pipeline/analysis/geo_cities/timezone_check  (29 lignes, 8 colonnes)

| country | city | utc_offset | n_channels | peak_hour_in_file | peak_if_file_is_utc_local_ho | daily_cycle_strength | verdict |
|---|---|---|---|---|---|---|---|
| Belarus | Minsk | 3.0 | 59 | 12.45 | 15.45 | 0.475 | UTC |
| Iran | Tehran | 3.5 | 43 | 11.46 | 14.96 | 0.38 | UTC |
| Russia | Chelyabinsk | 5.0 | 93 | 10.09 | 15.09 | 0.515 | UTC |
| Russia | Irkutsk | 8.0 | 124 | 7.27 | 15.27 | 0.479 | UTC |
| Russia | Kazan | 3.0 | 81 | 11.51 | 14.51 | 0.543 | UTC |
| Russia | Khabarovsk | 10.0 | 171 | 4.77 | 14.77 | 0.482 | UTC |
| Russia | Krasnodar | 3.0 | 186 | 11.74 | 14.74 | 0.528 | UTC |
| Russia | Krasnoyarsk | 7.0 | 120 | 7.97 | 14.97 | 0.518 | UTC |
| Russia | Moscow | 3.0 | 683 | 12.03 | 15.03 | 0.507 | UTC |
| Russia | Nizhny Novgorod | 3.0 | 53 | 12.26 | 15.26 | 0.447 | UTC |
| Russia | Novosibirsk | 7.0 | 82 | 8.07 | 15.07 | 0.498 | UTC |
| Russia | Omsk | 6.0 | 101 | 9.22 | 15.22 | 0.497 | UTC |
| Russia | Perm | 5.0 | 70 | 10.29 | 15.29 | 0.504 | UTC |
| Russia | Rostov-on-Don | 3.0 | 133 | 11.84 | 14.84 | 0.496 | UTC |
| Russia | Saint Petersburg | 3.0 | 479 | 12.24 | 15.24 | 0.496 | UTC |
| Russia | Samara | 4.0 | 74 | 11.21 | 15.21 | 0.468 | UTC |
| Russia | Saratov | 4.0 | 73 | 11.03 | 15.03 | 0.478 | UTC |
| Russia | Sevastopol | 3.0 | 172 | 11.91 | 14.91 | 0.484 | UTC |
| Russia | Tyumen | 5.0 | 97 | 10.11 | 15.11 | 0.529 | UTC |
| Russia | Ufa | 5.0 | 54 | 10.78 | 15.78 | 0.469 | UTC |
| Russia | Vladivostok | 10.0 | 91 | 5.19 | 15.19 | 0.411 | UTC |
| Russia | Volgograd | 3.0 | 109 | 11.67 | 14.67 | 0.515 | UTC |
| Russia | Voronezh | 3.0 | 124 | 11.8 | 14.8 | 0.506 | UTC |
| Russia | Yekaterinburg | 5.0 | 86 | 10.27 | 15.27 | 0.472 | UTC |
| Ukraine | Donetsk | 2.0 | 262 | 11.85 | 13.85 | 0.469 | UTC |
| Ukraine | Kharkiv | 2.0 | 95 | 12.37 | 14.37 | 0.415 | UTC |
| Ukraine | Kyiv | 2.0 | 90 | 12.12 | 14.12 | 0.409 | UTC |
| Ukraine | Luhansk | 2.0 | 98 | 11.86 | 13.86 | 0.497 | UTC |
| Ukraine | Odesa | 2.0 | 38 | 12.03 | 14.03 | 0.428 | UTC |


### bigdata_pipeline/analysis/geo_cities/validation_sample  (291 lignes, 9 colonnes)

| channel_id | method | language | city | evidence | matched_text | confidence | title | correct |
|---|---|---|---|---|---|---|---|---|
| 1436420185 | direct_channel_language | ru | Krasnoyarsk | title | красноярскии | 1.0 | Красноярский театр кукол |  |
| 1773788981 | direct_channel_language | ru | Moscow | title | москвы | 1.0 | МГО ВОГ / Все новости Москвы |  |
| 1649736580 | direct_channel_language | ru | Vladivostok | title | владивосток | 1.0 | АФИША ПРИМОРЬЕ • АФИША ВЛАДИВОСТОК |  |
| 1475794804 | direct_channel_language | ru | Luhansk | title | луганск | 1.0 | MDK Луганск |  |
| 1794503732 | direct_channel_language | ru | Moscow | title | москва | 1.0 | Нежная Москва |  |
| 1167920420 | direct_channel_language | uk | Mykolaiv | title | николаев | 1.0 | Хуевый Николаев / Миколаїв |  |
| 1628235594 | direct_channel_language | ru | Kazan | title | казань | 1.0 | Коротко. Казань |  |
| 1344634505 | direct_channel_language | uk | Mykolaiv | title | николаевпост | 1.0 | НиколаевПОСТ |  |
| 1293062352 | direct_channel_language | uk | Dnipro | title | днепр | 1.0 | Днепр Сейчас: новости |  |
| 1825350617 | direct_channel_language | ru | Moscow | title | москвы | 1.0 | Новаторы Москвы |  |


## Tables : analysis/city_coordinates


### bigdata_pipeline/analysis/city_coordinates/city_coordinates.csv  (286 lignes, 4 colonnes)

| country | city | lat | lon |
|---|---|---|---|
| Afghanistan | Herat | 34.35 | 62.20 |
| Afghanistan | Kabul | 34.53 | 69.17 |
| Albania | Tirana | 41.33 | 19.82 |
| Algeria | Algiers | 36.75 | 3.06 |
| Angola | Luanda | -8.84 | 13.23 |
| Argentina | Buenos Aires | -34.60 | -58.38 |
| Armenia | Gyumri | 40.79 | 43.85 |
| Armenia | Yerevan | 40.18 | 44.51 |
| Australia | Melbourne | -37.81 | 144.96 |
| Australia | Sydney | -33.87 | 151.21 |
| Austria | Vienna | 48.21 | 16.37 |
| Azerbaijan | Baku | 40.41 | 49.87 |
| Bangladesh | Chittagong | 22.36 | 91.78 |
| Bangladesh | Dhaka | 23.81 | 90.41 |
| Belarus | Brest | 52.10 | 23.70 |
| Belarus | Gomel | 52.44 | 30.98 |
| Belarus | Minsk | 53.90 | 27.57 |
| Belarus | Vitebsk | 55.19 | 30.20 |
| Belgium | Antwerp | 51.22 | 4.40 |
| Belgium | Brussels | 50.85 | 4.35 |
| Brazil | Belo Horizonte | -19.92 | -43.94 |
| Brazil | Brasilia | -15.79 | -47.88 |
| Brazil | Curitiba | -25.43 | -49.27 |
| Brazil | Fortaleza | -3.73 | -38.53 |
| Brazil | Porto Alegre | -30.03 | -51.23 |
| Brazil | Rio de Janeiro | -22.91 | -43.17 |
| Brazil | Salvador | -12.97 | -38.50 |
| Brazil | Sao Paulo | -23.55 | -46.63 |
| Bulgaria | Burgas | 42.50 | 27.47 |
| Bulgaria | Plovdiv | 42.14 | 24.75 |
| Bulgaria | Sofia | 42.70 | 23.32 |
| Bulgaria | Varna | 43.21 | 27.91 |
| Canada | Montreal | 45.50 | -73.57 |
| Canada | Toronto | 43.65 | -79.38 |
| Chile | Santiago | -33.45 | -70.67 |
| China | Beijing | 39.90 | 116.40 |
| China | Chengdu | 30.57 | 104.07 |
| China | Guangzhou | 23.13 | 113.26 |
| China | Shanghai | 31.23 | 121.47 |
| China | Shenzhen | 22.54 | 114.06 |


## Tables : analysis/anomalies


### bigdata_pipeline/analysis/anomalies/anomaly_episodes  (604 lignes, 11 colonnes)

| city_key | start | end | n_days | peak_date | peak_count | expected_at_peak | peak_ratio | max_score | excess_posts | shape |
|---|---|---|---|---|---|---|---|---|---|---|
| Tehran (Iran) | 2015-12-01 | 2015-12-01 | 1 | 2015-12-01 | 186.0 | 62.7 | 2.97 | 4.75 | 123.3 | spike |
| Tehran (Iran) | 2015-12-04 | 2015-12-08 | 5 | 2015-12-07 | 384.0 | 62.9 | 6.1 | 6.25 | 1072.1 | short |
| Tehran (Iran) | 2015-12-14 | 2015-12-14 | 1 | 2015-12-14 | 243.0 | 64.7 | 3.75 | 4.13 | 178.3 | spike |
| Tyumen (Russia) | 2016-01-11 | 2016-01-22 | 12 | 2016-01-16 | 22.0 | 0.0 | 22.0 | 25.5 | 370.7 | sustained |
| Tyumen (Russia) | 2016-01-25 | 2016-01-26 | 2 | 2016-01-25 | 32.0 | 0.0 | 32.0 | 23.31 | 65.5 | spike |
| Donetsk (Ukraine) | 2016-02-02 | 2016-02-29 | 28 | 2016-02-07 | 81.0 | 0.0 | 81.0 | 31.58 | 1580.1 | sustained |
| Kharkiv (Ukraine) | 2016-02-11 | 2016-02-11 | 1 | 2016-02-11 | 31.0 | 0.1 | 31.0 | 22.48 | 30.9 | spike |
| Luhansk (Ukraine) | 2016-06-02 | 2016-06-02 | 1 | 2016-06-02 | 25.0 | 0.1 | 25.0 | 21.29 | 24.9 | spike |
| Donetsk (Ukraine) | 2016-06-11 | 2016-06-11 | 1 | 2016-06-11 | 181.0 | 96.1 | 1.88 | 4.19 | 84.9 | spike |
| Kyiv (Ukraine) | 2016-06-22 | 2016-07-01 | 10 | 2016-06-26 | 45.0 | 0.0 | 45.0 | 27.92 | 334.6 | sustained |
| Donetsk (Ukraine) | 2016-06-25 | 2016-06-25 | 1 | 2016-06-25 | 214.0 | 100.7 | 2.13 | 4.26 | 113.3 | spike |
| Saint Petersburg (Russia) | 2016-07-02 | 2016-07-03 | 2 | 2016-07-03 | 136.0 | 13.0 | 10.49 | 4.24 | 240.6 | spike |
| Kyiv (Ukraine) | 2016-07-04 | 2016-07-16 | 13 | 2016-07-04 | 63.0 | 0.0 | 63.0 | 27.57 | 630.5 | sustained |
| Mashhad (Iran) | 2016-07-09 | 2016-07-10 | 2 | 2016-07-10 | 236.0 | 29.0 | 8.14 | 4.54 | 359.5 | spike |
| Irkutsk (Russia) | 2016-09-02 | 2016-09-02 | 1 | 2016-09-02 | 36.0 | 0.0 | 36.0 | 24.07 | 36.0 | spike |
| Irkutsk (Russia) | 2016-09-05 | 2016-09-09 | 5 | 2016-09-05 | 37.0 | 0.0 | 37.0 | 24.25 | 199.7 | short |
| Irkutsk (Russia) | 2016-09-12 | 2016-09-16 | 5 | 2016-09-12 | 40.0 | 0.0 | 40.0 | 18.22 | 175.3 | short |
| Tyumen (Russia) | 2016-09-18 | 2016-09-18 | 1 | 2016-09-18 | 107.0 | 35.4 | 3.02 | 7.25 | 71.6 | spike |
| Sevastopol (Russia) | 2017-01-12 | 2017-01-12 | 1 | 2017-01-12 | 28.0 | 0.1 | 28.0 | 22.06 | 27.9 | spike |
| Mashhad (Iran) | 2017-01-19 | 2017-01-19 | 1 | 2017-01-19 | 376.0 | 131.5 | 2.86 | 6.33 | 244.5 | spike |
| Sevastopol (Russia) | 2017-01-19 | 2017-01-19 | 1 | 2017-01-19 | 27.0 | 0.2 | 27.0 | 13.13 | 26.8 | spike |
| Moscow (Russia) | 2017-01-25 | 2017-01-25 | 1 | 2017-01-25 | 757.0 | 216.3 | 3.5 | 4.92 | 540.7 | spike |
| Sevastopol (Russia) | 2017-01-26 | 2017-01-26 | 1 | 2017-01-26 | 21.0 | 0.2 | 21.0 | 8.09 | 20.8 | spike |
| Sevastopol (Russia) | 2017-01-30 | 2017-01-30 | 1 | 2017-01-30 | 23.0 | 0.4 | 23.0 | 6.02 | 22.6 | spike |
| Kharkiv (Ukraine) | 2017-03-04 | 2017-03-14 | 11 | 2017-03-11 | 136.0 | 7.5 | 18.14 | 5.3 | 1047.2 | sustained |
| Omsk (Russia) | 2017-03-13 | 2017-03-13 | 1 | 2017-03-13 | 113.0 | 8.1 | 13.94 | 5.05 | 104.9 | spike |
| Kharkiv (Ukraine) | 2017-03-18 | 2017-03-20 | 3 | 2017-03-18 | 143.0 | 8.7 | 16.52 | 4.26 | 460.9 | short |
| Kazan (Russia) | 2017-03-26 | 2017-03-26 | 1 | 2017-03-26 | 37.0 | 1.2 | 29.85 | 4.39 | 35.8 | spike |
| Saint Petersburg (Russia) | 2017-04-03 | 2017-04-03 | 1 | 2017-04-03 | 602.0 | 255.9 | 2.35 | 5.17 | 346.1 | spike |
| Tehran (Iran) | 2017-04-28 | 2017-04-28 | 1 | 2017-04-28 | 1600.0 | 728.4 | 2.2 | 5.24 | 871.6 | spike |
| Tehran (Iran) | 2017-05-05 | 2017-05-05 | 1 | 2017-05-05 | 1694.0 | 731.5 | 2.32 | 5.49 | 962.5 | spike |
| Mashhad (Iran) | 2017-05-19 | 2017-05-19 | 1 | 2017-05-19 | 377.0 | 120.2 | 3.14 | 4.29 | 256.8 | spike |
| Tehran (Iran) | 2017-05-19 | 2017-05-19 | 1 | 2017-05-19 | 1808.0 | 786.6 | 2.3 | 4.31 | 1021.4 | spike |
| Krasnodar (Russia) | 2017-05-26 | 2017-05-26 | 1 | 2017-05-26 | 80.0 | 22.4 | 3.58 | 4.78 | 57.6 | spike |
| Tehran (Iran) | 2017-06-07 | 2017-06-07 | 1 | 2017-06-07 | 2384.0 | 1079.2 | 2.21 | 5.28 | 1304.8 | spike |
| Rostov-on-Don (Russia) | 2017-06-12 | 2017-06-12 | 1 | 2017-06-12 | 149.0 | 33.3 | 4.47 | 4.39 | 115.7 | spike |
| Sevastopol (Russia) | 2017-08-18 | 2017-08-20 | 3 | 2017-08-18 | 86.0 | 15.5 | 5.54 | 4.61 | 156.4 | short |
| Moscow (Russia) | 2017-09-10 | 2017-09-10 | 1 | 2017-09-10 | 1715.0 | 471.6 | 3.64 | 7.92 | 1243.4 | spike |
| Perm (Russia) | 2017-09-10 | 2017-09-10 | 1 | 2017-09-10 | 22.0 | 0.6 | 22.0 | 4.77 | 21.4 | spike |
| Tyumen (Russia) | 2017-09-10 | 2017-09-10 | 1 | 2017-09-10 | 177.0 | 78.4 | 2.26 | 5.39 | 98.6 | spike |


### bigdata_pipeline/analysis/anomalies/anomaly_summary  (11 lignes, 2 colonnes)

| metric | value |
|---|---|
| cities analysed | 75 |
| days | 3295 |
| first day | 2015-09-22 |
| last day | 2024-09-28 |
| anomalous city-days | 1070 |
| episodes | 604 |
| ... spikes (1-2 days) | 538 |
| ... short (3-7 days) | 45 |
| ... sustained (> 7 days) | 21 |
| synchronized peaks (>= 3 cities together | 44 |
| ... flagged global | 0 |


### bigdata_pipeline/analysis/anomalies/city_pair_correlation  (403 lignes, 5 colonnes)

| city_a | city_b | corr_lag0 | best_lag_days | best_corr |
|---|---|---|---|---|
| Poltava (Ukraine) | Zhytomyr (Ukraine) | 0.776 | 3 | 0.857 |
| Voronezh (Russia) | Nizhny Novgorod (Russia) | 0.789 | 0 | 0.789 |
| Nizhny Novgorod (Russia) | Ufa (Russia) | 0.743 | 0 | 0.743 |
| Odesa (Ukraine) | Vinnytsia (Ukraine) | 0.709 | 0 | 0.709 |
| Voronezh (Russia) | Ufa (Russia) | 0.708 | 0 | 0.708 |
| Saint Petersburg (Russia) | Tyumen (Russia) | 0.69 | 0 | 0.69 |
| Kherson (Ukraine) | Vinnytsia (Ukraine) | 0.682 | 0 | 0.682 |
| Nizhny Novgorod (Russia) | Kherson (Ukraine) | 0.658 | 0 | 0.658 |
| Ufa (Russia) | Odesa (Ukraine) | 0.653 | 0 | 0.653 |
| Rostov-on-Don (Russia) | Irkutsk (Russia) | 0.649 | 0 | 0.649 |
| Ufa (Russia) | Vinnytsia (Ukraine) | 0.643 | 0 | 0.643 |
| Nizhny Novgorod (Russia) | Novosibirsk (Russia) | 0.643 | 0 | 0.643 |
| Nizhny Novgorod (Russia) | Odesa (Ukraine) | 0.615 | 0 | 0.615 |
| Kherson (Ukraine) | Perm (Russia) | 0.61 | 0 | 0.61 |
| Saratov (Russia) | Ufa (Russia) | 0.596 | 0 | 0.596 |
| Saratov (Russia) | Voronezh (Russia) | 0.596 | 0 | 0.596 |
| Ufa (Russia) | Lviv (Ukraine) | 0.596 | 0 | 0.596 |
| Voronezh (Russia) | Kherson (Ukraine) | 0.59 | 0 | 0.59 |
| Voronezh (Russia) | Odesa (Ukraine) | 0.581 | 0 | 0.581 |
| Ufa (Russia) | Kherson (Ukraine) | 0.581 | 0 | 0.581 |
| Nizhny Novgorod (Russia) | Vinnytsia (Ukraine) | 0.574 | 0 | 0.574 |
| Nizhny Novgorod (Russia) | Perm (Russia) | 0.567 | 0 | 0.567 |
| Kherson (Ukraine) | Odesa (Ukraine) | 0.567 | 0 | 0.567 |
| Saratov (Russia) | Nizhny Novgorod (Russia) | 0.565 | 0 | 0.565 |
| Ufa (Russia) | Novosibirsk (Russia) | 0.559 | 0 | 0.559 |
| Saratov (Russia) | Odesa (Ukraine) | 0.553 | 0 | 0.553 |
| Saratov (Russia) | Vinnytsia (Ukraine) | 0.552 | 0 | 0.552 |
| Ufa (Russia) | Perm (Russia) | 0.552 | 0 | 0.552 |
| Nizhny Novgorod (Russia) | Lviv (Ukraine) | 0.549 | 0 | 0.549 |
| Saratov (Russia) | Kherson (Ukraine) | 0.547 | 0 | 0.547 |
| Voronezh (Russia) | Vinnytsia (Ukraine) | 0.542 | 0 | 0.542 |
| Voronezh (Russia) | Novosibirsk (Russia) | 0.541 | 0 | 0.541 |
| Voronezh (Russia) | Perm (Russia) | 0.533 | 0 | 0.533 |
| Kherson (Ukraine) | Novosibirsk (Russia) | 0.52 | 0 | 0.52 |
| Voronezh (Russia) | Lviv (Ukraine) | 0.515 | 0 | 0.515 |
| Lviv (Ukraine) | Vinnytsia (Ukraine) | 0.515 | 0 | 0.515 |
| Rostov-on-Don (Russia) | Perm (Russia) | 0.503 | 0 | 0.503 |
| Irkutsk (Russia) | Perm (Russia) | 0.493 | 0 | 0.493 |
| Perm (Russia) | Vinnytsia (Ukraine) | 0.487 | 0 | 0.487 |
| Donetsk (Ukraine) | Kharkiv (Ukraine) | 0.484 | 0 | 0.484 |


### bigdata_pipeline/analysis/anomalies/lead_sensitivity  (44 lignes, 5 colonnes)

| sync_id | lead_k2.5 | lead_k3 | lead_k4 | stable |
|---|---|---|---|---|
| 1 | Moscow (Russia) | Moscow (Russia) | Moscow (Russia) | True |
| 2 | Volgograd (Russia) | Volgograd (Russia) | Khabarovsk (Russia) | False |
| 3 | Moscow (Russia) | Moscow (Russia) | Moscow (Russia) | True |
| 4 | Chelyabinsk (Russia) | Chelyabinsk (Russia) | Chelyabinsk (Russia) | True |
| 5 | Minsk (Belarus) | Minsk (Belarus) | Minsk (Belarus) | True |
| 6 | Minsk (Belarus) | Minsk (Belarus) | Simferopol (Russia) | False |
| 7 | Krasnodar (Russia) | Krasnodar (Russia) | Krasnodar (Russia) | True |
| 8 | Kharkiv (Ukraine) |  |  | False |
| 9 | Chelyabinsk (Russia) | Chelyabinsk (Russia) | Irkutsk (Russia) | False |
| 10 | Chelyabinsk (Russia) | Volgograd (Russia) | Yekaterinburg (Russia) | False |
| 11 | Yekaterinburg (Russia) | Rostov-on-Don (Russia) | Rostov-on-Don (Russia) | False |
| 12 | Saint Petersburg (Russia) | Volgograd (Russia) | Volgograd (Russia) | False |
| 13 | Luhansk (Ukraine) | Vladivostok (Russia) | Vladivostok (Russia) | False |
| 14 | Sevastopol (Russia) | Tehran (Iran) | Tehran (Iran) | False |
| 15 | Donetsk (Ukraine) | Donetsk (Ukraine) | Donetsk (Ukraine) | True |
| 16 | Luhansk (Ukraine) | Luhansk (Ukraine) | Donetsk (Ukraine) | False |
| 17 | Donetsk (Ukraine) | Donetsk (Ukraine) | Donetsk (Ukraine) | True |
| 18 | Luhansk (Ukraine) | Luhansk (Ukraine) | Luhansk (Ukraine) | True |
| 19 | Irkutsk (Russia) | Krasnodar (Russia) | Krasnodar (Russia) | False |
| 20 | Ufa (Russia) | Ufa (Russia) | Sydney (Australia) | False |
| 21 | Omsk (Russia) | Omsk (Russia) | Omsk (Russia) | True |
| 22 | Sevastopol (Russia) | Sevastopol (Russia) | Sevastopol (Russia) | True |
| 23 | Kyiv (Ukraine) | Kyiv (Ukraine) | Kyiv (Ukraine) | True |
| 24 | Perm (Russia) | Nizhny Novgorod (Russia) | Nizhny Novgorod (Russia) | False |
| 25 | Yekaterinburg (Russia) | Yekaterinburg (Russia) | Yekaterinburg (Russia) | True |
| 26 | Vladivostok (Russia) | Vladivostok (Russia) | Vladivostok (Russia) | True |
| 27 | Yekaterinburg (Russia) | Sydney (Australia) | Sydney (Australia) | False |
| 28 | Nizhny Novgorod (Russia) | Nizhny Novgorod (Russia) | Nizhny Novgorod (Russia) | True |
| 29 | Nizhny Novgorod (Russia) | Nizhny Novgorod (Russia) | Nizhny Novgorod (Russia) | True |
| 30 | Rivne (Ukraine) | Rivne (Ukraine) | Rivne (Ukraine) | True |
| 31 | Sydney (Australia) | Sydney (Australia) | Sydney (Australia) | True |
| 32 | Odesa (Ukraine) |  |  | False |
| 33 | Ufa (Russia) | Ufa (Russia) | Ufa (Russia) | True |
| 34 | Ufa (Russia) | Nizhny Novgorod (Russia) | Nizhny Novgorod (Russia) | False |
| 35 | Simferopol (Russia) | Simferopol (Russia) | Sydney (Australia) | False |
| 36 | Odesa (Ukraine) | Sydney (Australia) | Sydney (Australia) | False |
| 37 | Nizhny Novgorod (Russia) | Nizhny Novgorod (Russia) | Sydney (Australia) | False |
| 38 | Voronezh (Russia) | Perm (Russia) | Perm (Russia) | False |
| 39 | Odesa (Ukraine) | Minsk (Belarus) | Minsk (Belarus) | False |
| 40 | Simferopol (Russia) | Simferopol (Russia) |  | False |


### bigdata_pipeline/analysis/anomalies/sync_onsets  (223 lignes, 4 colonnes)

| sync_id | city_key | onset_utc | hours_after_first |
|---|---|---|---|
| 1 | Moscow (Russia) | 2017-09-10 03:00:00 | 0.0 |
| 2 | Volgograd (Russia) | 2018-03-17 17:00:00 | 0.0 |
| 2 | Khabarovsk (Russia) | 2018-03-18 00:00:00 | 7.0 |
| 2 | Moscow (Russia) | 2018-03-18 00:00:00 | 7.0 |
| 2 | Sevastopol (Russia) | 2018-03-18 04:00:00 | 11.0 |
| 2 | Tyumen (Russia) | 2018-03-18 04:00:00 | 11.0 |
| 2 | Saint Petersburg (Russia) | 2018-03-18 05:00:00 | 12.0 |
| 2 | Rostov-on-Don (Russia) | 2018-03-18 06:00:00 | 13.0 |
| 2 | Kazan (Russia) | 2018-03-18 13:00:00 | 20.0 |
| 3 | Moscow (Russia) | 2018-09-09 02:00:00 | 0.0 |
| 3 | Tyumen (Russia) | 2018-09-09 03:00:00 | 1.0 |
| 3 | Volgograd (Russia) | 2018-09-09 10:00:00 | 8.0 |
| 3 | Nizhny Novgorod (Russia) | 2018-09-09 11:00:00 | 9.0 |
| 3 | Saint Petersburg (Russia) | 2018-09-09 11:00:00 | 9.0 |
| 4 | Chelyabinsk (Russia) | 2019-09-07 05:00:00 | 0.0 |
| 4 | Khabarovsk (Russia) | 2019-09-07 20:00:00 | 15.0 |
| 4 | Saint Petersburg (Russia) | 2019-09-07 23:00:00 | 18.0 |
| 4 | Moscow (Russia) | 2019-09-08 02:00:00 | 21.0 |
| 4 | Irkutsk (Russia) | 2019-09-08 03:00:00 | 22.0 |
| 4 | Volgograd (Russia) | 2019-09-08 04:00:00 | 23.0 |
| 4 | Tyumen (Russia) | 2019-09-08 05:00:00 | 24.0 |
| 4 | Kazan (Russia) | 2019-09-08 06:00:00 | 25.0 |
| 5 | Minsk (Belarus) | 2020-08-09 05:00:00 | 0.0 |
| 5 | Chelyabinsk (Russia) | 2020-08-09 07:00:00 | 2.0 |
| 5 | Luhansk (Ukraine) | 2020-08-09 18:00:00 | 13.0 |
| 5 | Moscow (Russia) | 2020-08-09 19:00:00 | 14.0 |
| 6 | Minsk (Belarus) | 2020-08-22 12:00:00 | 0.0 |
| 6 | Simferopol (Russia) | 2020-08-22 13:00:00 | 1.0 |
| 7 | Krasnodar (Russia) | 2020-09-12 19:00:00 | 0.0 |
| 7 | Irkutsk (Russia) | 2020-09-13 03:00:00 | 8.0 |
| 7 | Chelyabinsk (Russia) | 2020-09-13 05:00:00 | 10.0 |
| 9 | Chelyabinsk (Russia) | 2021-01-17 13:00:00 | 0.0 |
| 9 | Irkutsk (Russia) | 2021-01-17 14:00:00 | 1.0 |
| 9 | Yekaterinburg (Russia) | 2021-01-17 15:00:00 | 2.0 |
| 10 | Volgograd (Russia) | 2021-01-22 15:00:00 | 0.0 |
| 10 | Yekaterinburg (Russia) | 2021-01-23 03:00:00 | 12.0 |
| 10 | Moscow (Russia) | 2021-01-23 04:00:00 | 13.0 |
| 10 | Saint Petersburg (Russia) | 2021-01-23 04:00:00 | 13.0 |
| 10 | Krasnoyarsk (Russia) | 2021-01-23 06:00:00 | 15.0 |
| 10 | Ufa (Russia) | 2021-01-23 07:00:00 | 16.0 |


### bigdata_pipeline/analysis/anomalies/synchronized_peaks  (44 lignes, 17 colonnes)

| sync_id | start | end | n_days | n_cities | max_share_of_cities | global | lead_city | n_lead_ties | lead_lag_days | excess_posts | top_cities | n_cities_with_onset | lead_city_hourly |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 2017-09-10 | 2017-09-10 | 1 | 3 | 0.04 | False | Moscow (Russia) | 3 | 0 | 1363.4 | Moscow (Russia); Tyumen (Russia); Perm ( | 1 | Moscow (Russia) |
| 2 | 2018-03-18 | 2018-03-18 | 1 | 8 | 0.107 | False | Tyumen (Russia) | 8 | 0 | 3697.3 | Moscow (Russia); Saint Petersburg (Russi | 8 | Volgograd (Russia) |
| 3 | 2018-09-09 | 2018-09-09 | 1 | 6 | 0.08 | False | Tyumen (Russia) | 6 | 0 | 3088.2 | Moscow (Russia); Saint Petersburg (Russi | 5 | Moscow (Russia) |
| 4 | 2019-09-08 | 2019-09-08 | 1 | 9 | 0.12 | False | Tyumen (Russia) | 9 | 0 | 4351.1 | Moscow (Russia); Saint Petersburg (Russi | 8 | Chelyabinsk (Russia) |
| 5 | 2020-08-09 | 2020-08-09 | 1 | 4 | 0.053 | False | Minsk (Belarus) | 4 | 0 | 10528.0 | Minsk (Belarus); Moscow (Russia); Chelya | 4 | Minsk (Belarus) |
| 6 | 2020-08-23 | 2020-08-23 | 1 | 3 | 0.04 | False | Simferopol (Russia) | 1 | 1 | 1472.0 | Minsk (Belarus); Simferopol (Russia); Lu | 2 | Minsk (Belarus) |
| 7 | 2020-09-13 | 2020-09-13 | 1 | 5 | 0.067 | False | Irkutsk (Russia) | 5 | 0 | 721.4 | Krasnodar (Russia); Irkutsk (Russia); Ch | 3 | Krasnodar (Russia) |
| 8 | 2020-10-25 | 2020-10-25 | 1 | 3 | 0.04 | False | Vinnytsia (Ukraine) | 3 | 0 | 600.8 | Kharkiv (Ukraine); Odesa (Ukraine); Vinn | 0 |  |
| 9 | 2021-01-17 | 2021-01-17 | 1 | 3 | 0.04 | False | Yekaterinburg (Russia) | 3 | 0 | 501.7 | Yekaterinburg (Russia); Irkutsk (Russia) | 3 | Chelyabinsk (Russia) |
| 10 | 2021-01-23 | 2021-01-23 | 1 | 9 | 0.12 | False | Yekaterinburg (Russia) | 9 | 0 | 10261.9 | Moscow (Russia); Saint Petersburg (Russi | 9 | Volgograd (Russia) |
| 11 | 2021-01-31 | 2021-01-31 | 1 | 10 | 0.133 | False | Yekaterinburg (Russia) | 10 | 0 | 10854.5 | Moscow (Russia); Saint Petersburg (Russi | 9 | Rostov-on-Don (Russia) |
| 12 | 2021-04-21 | 2021-04-21 | 1 | 4 | 0.053 | False | Yekaterinburg (Russia) | 4 | 0 | 3128.1 | Saint Petersburg (Russia); Yekaterinburg | 4 | Volgograd (Russia) |
| 13 | 2021-05-09 | 2021-05-09 | 1 | 10 | 0.133 | False | Volgograd (Russia) | 10 | 0 | 5013.8 | Donetsk (Ukraine); Minsk (Belarus); Kras | 9 | Vladivostok (Russia) |
| 14 | 2021-06-18 | 2021-06-18 | 1 | 3 | 0.04 | False | Mashhad (Iran) | 3 | 0 | 2917.3 | Sevastopol (Russia); Tehran (Iran); Mash | 3 | Tehran (Iran) |
| 15 | 2021-09-18 | 2021-09-19 | 2 | 18 | 0.24 | False | Volgograd (Russia) | 4 | 1 | 10128.4 | Moscow (Russia); Donetsk (Ukraine); Khab | 14 | Donetsk (Ukraine) |
| 16 | 2022-02-19 | 2022-02-21 | 3 | 5 | 0.053 | False | Luhansk (Ukraine) | 2 | 3 | 60384.8 | Donetsk (Ukraine); Luhansk (Ukraine); Mo | 5 | Luhansk (Ukraine) |
| 17 | 2022-02-24 | 2022-03-25 | 30 | 33 | 0.307 | False | Luhansk (Ukraine) | 1 | 24 | 480802.3 | Donetsk (Ukraine); Kharkiv (Ukraine); Mo | 28 | Donetsk (Ukraine) |
| 18 | 2022-06-12 | 2022-06-12 | 1 | 3 | 0.04 | False | Sao Paulo (Brazil) | 3 | 0 | 1017.5 | Luhansk (Ukraine); Simferopol (Russia);  | 3 | Luhansk (Ukraine) |
| 19 | 2022-09-11 | 2022-09-11 | 1 | 5 | 0.067 | False | Voronezh (Russia) | 5 | 0 | 1975.6 | Krasnodar (Russia); Yekaterinburg (Russi | 1 | Krasnodar (Russia) |
| 20 | 2022-09-24 | 2022-09-25 | 2 | 5 | 0.04 | False | Sydney (Australia) | 1 | 3 | 2182.2 | Luhansk (Ukraine); Krasnoyarsk (Russia); | 4 | Ufa (Russia) |
| 21 | 2022-10-01 | 2022-10-02 | 2 | 5 | 0.053 | False | Omsk (Russia) | 1 | 4 | 13970.9 | Omsk (Russia); Voronezh (Russia); Samara | 1 | Omsk (Russia) |
| 22 | 2022-10-08 | 2022-10-10 | 3 | 7 | 0.053 | False | Sevastopol (Russia) | 4 | 2 | 19538.8 | Donetsk (Ukraine); Kharkiv (Ukraine); Se | 6 | Sevastopol (Russia) |
| 23 | 2022-11-06 | 2022-11-06 | 1 | 4 | 0.053 | False | Almaty (Kazakhstan) | 1 | 8 | 1987.0 | Kyiv (Ukraine); Almaty (Kazakhstan); Vor | 2 | Kyiv (Ukraine) |
| 24 | 2023-05-06 | 2023-05-09 | 4 | 11 | 0.093 | False | Nizhny Novgorod (Russia) | 7 | 3 | 6974.5 | Tyumen (Russia); Yekaterinburg (Russia); | 8 | Nizhny Novgorod (Russia) |
| 25 | 2023-06-24 | 2023-06-24 | 1 | 24 | 0.32 | False | Voronezh (Russia) | 24 | 0 | 66037.3 | Moscow (Russia); Donetsk (Ukraine); Khar | 23 | Yekaterinburg (Russia) |
| 26 | 2023-08-12 | 2023-08-12 | 1 | 3 | 0.04 | False | Vladivostok (Russia) | 1 | 1 | 7283.3 | Vladivostok (Russia); Yekaterinburg (Rus | 3 | Vladivostok (Russia) |
| 27 | 2023-08-19 | 2023-08-19 | 1 | 3 | 0.04 | False | Sydney (Australia) | 3 | 0 | 1961.5 | Yekaterinburg (Russia); Nizhny Novgorod  | 3 | Sydney (Australia) |
| 28 | 2023-08-27 | 2023-08-27 | 1 | 3 | 0.04 | False | Nizhny Novgorod (Russia) | 2 | 1 | 942.9 | Nizhny Novgorod (Russia); Ufa (Russia);  | 1 | Nizhny Novgorod (Russia) |
| 29 | 2023-09-03 | 2023-09-03 | 1 | 3 | 0.04 | False | Nizhny Novgorod (Russia) | 2 | 1 | 1278.0 | Voronezh (Russia); Nizhny Novgorod (Russ | 1 | Nizhny Novgorod (Russia) |
| 30 | 2023-09-09 | 2023-09-10 | 2 | 11 | 0.133 | False | Rivne (Ukraine) | 1 | 6 | 7252.4 | Tyumen (Russia); Irkutsk (Russia); Volgo | 8 | Rivne (Ukraine) |
| 31 | 2023-09-23 | 2023-09-24 | 2 | 5 | 0.04 | False | Sydney (Australia) | 3 | 1 | 964.2 | Voronezh (Russia); Nizhny Novgorod (Russ | 1 | Sydney (Australia) |
| 32 | 2023-10-07 | 2023-10-07 | 1 | 3 | 0.04 | False | Saratov (Russia) | 3 | 0 | 1438.6 | Saratov (Russia); Nizhny Novgorod (Russi | 0 |  |
| 33 | 2023-10-14 | 2023-10-15 | 2 | 4 | 0.04 | False | Yekaterinburg (Russia) | 3 | 1 | 14377.7 | Yekaterinburg (Russia); Omsk (Russia); U | 4 | Ufa (Russia) |
| 34 | 2023-11-04 | 2023-11-05 | 2 | 7 | 0.053 | False | Sydney (Australia) | 3 | 1 | 2098.1 | Yekaterinburg (Russia); Omsk (Russia); N | 5 | Nizhny Novgorod (Russia) |
| 35 | 2023-11-19 | 2023-11-19 | 1 | 3 | 0.04 | False | Sydney (Australia) | 1 | 3 | 689.8 | Nizhny Novgorod (Russia); Simferopol (Ru | 2 | Simferopol (Russia) |
| 36 | 2023-11-26 | 2023-11-26 | 1 | 6 | 0.08 | False | Sydney (Australia) | 1 | 2 | 5693.2 | Sevastopol (Russia); Nizhny Novgorod (Ru | 4 | Sydney (Australia) |
| 37 | 2023-12-03 | 2023-12-03 | 1 | 4 | 0.053 | False | Sydney (Australia) | 1 | 2 | 893.3 | Nizhny Novgorod (Russia); Simferopol (Ru | 3 | Nizhny Novgorod (Russia) |
| 38 | 2023-12-31 | 2023-12-31 | 1 | 7 | 0.093 | False | Perm (Russia) | 7 | 0 | 2696.1 | Luhansk (Ukraine); Voronezh (Russia); Ch | 2 | Perm (Russia) |
| 39 | 2024-02-25 | 2024-02-25 | 1 | 3 | 0.04 | False | Odesa (Ukraine) | 1 | 1 | 2109.7 | Minsk (Belarus); Odesa (Ukraine); Kherso | 1 | Minsk (Belarus) |
| 40 | 2024-03-03 | 2024-03-03 | 1 | 3 | 0.04 | False | Odesa (Ukraine) | 1 | 1 | 1079.1 | Odesa (Ukraine); Nizhny Novgorod (Russia | 1 | Simferopol (Russia) |


## Figures : analysis/figures/geo_cities

![/home/dvopssl/Documents/telescope_data_analysis/bigdata_pipeline/analysis/figures/geo_cities/city_coverage_by_language.png](/home/dvopssl/Documents/telescope_data_analysis/bigdata_pipeline/analysis/figures/geo_cities/city_coverage_by_language.png)

![/home/dvopssl/Documents/telescope_data_analysis/bigdata_pipeline/analysis/figures/geo_cities/coverage_by_method.png](/home/dvopssl/Documents/telescope_data_analysis/bigdata_pipeline/analysis/figures/geo_cities/coverage_by_method.png)

![/home/dvopssl/Documents/telescope_data_analysis/bigdata_pipeline/analysis/figures/geo_cities/top_cities.png](/home/dvopssl/Documents/telescope_data_analysis/bigdata_pipeline/analysis/figures/geo_cities/top_cities.png)


## Figures : analysis/figures/anomalies

![/home/dvopssl/Documents/telescope_data_analysis/bigdata_pipeline/analysis/figures/anomalies/cities_anomalous_per_day.png](/home/dvopssl/Documents/telescope_data_analysis/bigdata_pipeline/analysis/figures/anomalies/cities_anomalous_per_day.png)

![/home/dvopssl/Documents/telescope_data_analysis/bigdata_pipeline/analysis/figures/anomalies/episodes_per_month.png](/home/dvopssl/Documents/telescope_data_analysis/bigdata_pipeline/analysis/figures/anomalies/episodes_per_month.png)

![/home/dvopssl/Documents/telescope_data_analysis/bigdata_pipeline/analysis/figures/anomalies/top_cities_series.png](/home/dvopssl/Documents/telescope_data_analysis/bigdata_pipeline/analysis/figures/anomalies/top_cities_series.png)


# Thème 5 — Tendances atypiques


## Tables : analysis/suspicious


### bigdata_pipeline/analysis/suspicious/coordinated_groups  (808 lignes, 9 colonnes)

| n_channels | n_pairs | shared_total | shared_max | median_dt_s | n_origins_max | density | min_shared_used | group_rank |
|---|---|---|---|---|---|---|---|---|
| 278 | 713 | 1046475 | 46531 | 12.0 | 1632 | 0.019 | 192.216796875 | 1 |
| 130 | 1464 | 1148855 | 17411 | 12.0 | 423 | 0.175 | 25.3125 | 2 |
| 87 | 732 | 25281 | 230 | 17.0 | 16 | 0.196 | 5.0 | 3 |
| 70 | 467 | 51694 | 891 | 1.0 | 153 | 0.193 | 5.0 | 4 |
| 61 | 333 | 40335 | 408 | 0.0 | 18 | 0.182 | 11.25 | 5 |
| 54 | 410 | 73628 | 1576 | 1.0 | 97 | 0.287 | 37.96875 | 6 |
| 49 | 214 | 36241 | 1511 | 22.0 | 23 | 0.182 | 56.953125 | 7 |
| 43 | 79 | 3232 | 799 | 9.0 | 61 | 0.087 | 5.0 | 8 |
| 42 | 170 | 1340 | 17 | 4.0 | 3 | 0.197 | 5.0 | 9 |
| 40 | 115 | 3010 | 72 | 27.0 | 4 | 0.147 | 16.875 | 10 |
| 37 | 556 | 95288 | 825 | 0.0 | 40 | 0.835 | 5.0 | 11 |
| 30 | 293 | 10164 | 135 | 1.0 | 36 | 0.674 | 5.0 | 12 |
| 30 | 72 | 3006 | 122 | 19.5 | 11 | 0.166 | 25.3125 | 13 |
| 29 | 31 | 8184 | 1648 | 3.0 | 137 | 0.076 | 56.953125 | 14 |
| 26 | 107 | 991 | 26 | 25.0 | 3 | 0.329 | 5.0 | 15 |
| 25 | 103 | 6688 | 1843 | 6.0 | 35 | 0.343 | 5.0 | 16 |
| 25 | 28 | 652 | 36 | 25.0 | 4 | 0.093 | 16.875 | 17 |
| 24 | 229 | 8694 | 150 | 2.0 | 28 | 0.83 | 5.0 | 18 |
| 23 | 67 | 8399 | 814 | 0.0 | 88 | 0.265 | 25.3125 | 19 |
| 23 | 71 | 864 | 43 | 13.0 | 11 | 0.281 | 7.5 | 20 |
| 22 | 33 | 2038 | 1501 | 23.0 | 80 | 0.143 | 7.5 | 21 |
| 22 | 46 | 965 | 44 | 28.0 | 9 | 0.199 | 11.25 | 22 |
| 21 | 43 | 45342 | 12564 | 19.0 | 424 | 0.205 | 192.216796875 | 23 |
| 20 | 68 | 20734 | 1496 | 5.0 | 48 | 0.358 | 11.25 | 24 |
| 20 | 34 | 3019 | 381 | 14.5 | 98 | 0.179 | 16.875 | 25 |
| 20 | 63 | 1537 | 66 | 0.0 | 16 | 0.332 | 7.5 | 26 |
| 19 | 108 | 4563 | 89 | 0.0 | 7 | 0.632 | 11.25 | 27 |
| 19 | 82 | 3548 | 228 | 24.0 | 21 | 0.48 | 7.5 | 28 |
| 19 | 103 | 2917 | 85 | 1.0 | 9 | 0.602 | 5.0 | 29 |
| 19 | 62 | 528 | 14 | 2.0 | 3 | 0.363 | 5.0 | 30 |
| 19 | 31 | 295 | 13 | 24.0 | 5 | 0.181 | 7.5 | 31 |
| 18 | 44 | 23828 | 12596 | 27.5 | 542 | 0.288 | 56.953125 | 32 |
| 18 | 63 | 12532 | 725 | 24.0 | 132 | 0.412 | 56.953125 | 33 |
| 18 | 17 | 9176 | 2697 | 5.0 | 178 | 0.111 | 128.14453125 | 34 |
| 18 | 43 | 5118 | 881 | 1.0 | 39 | 0.281 | 7.5 | 35 |
| 18 | 77 | 1817 | 60 | 19.0 | 7 | 0.503 | 11.25 | 36 |
| 17 | 65 | 10548 | 544 | 0.0 | 53 | 0.478 | 11.25 | 37 |
| 17 | 65 | 6949 | 330 | 11.0 | 61 | 0.478 | 11.25 | 38 |
| 16 | 60 | 1189 | 43 | 1.0 | 6 | 0.5 | 5.0 | 39 |
| 16 | 43 | 510 | 57 | 21.0 | 12 | 0.358 | 5.0 | 40 |


### bigdata_pipeline/analysis/suspicious/coordinated_members  (4979 lignes, 4 colonnes)

| channel_id | shared_total | group_rank | also_flagged |
|---|---|---|---|
| 1274585739 | 191046 | 1 | 0 |
| 1475762192 | 190998 | 1 | 0 |
| 1301574843 | 190171 | 1 | 0 |
| 1787216522 | 160769 | 1 | 1 |
| 1605558124 | 143713 | 1 | 0 |
| 1478603215 | 66731 | 1 | 0 |
| 1310493808 | 63053 | 1 | 0 |
| 1267862369 | 57649 | 1 | 0 |
| 1601929546 | 53695 | 1 | 0 |
| 1364207510 | 41737 | 1 | 1 |


### bigdata_pipeline/analysis/suspicious/indicator_summary  (12 lignes, 5 colonnes)

| category | indicator | n_flagged | share_of_channels_pct | threshold |
|---|---|---|---|---|
| behaviour | fast_relay | 394 | 0.564 | 0.4397650047385954 |
| behaviour | single_source | 1737 | 2.485 | 0.9 |
| behaviour | round_clock | 524 | 0.75 | 0.9865918801402875 |
| behaviour | fixed_second | 663 | 0.948 | 0.5060571517996874 |
| behaviour | daily_burst | 62 | 0.089 | 200.73249999999894 |
| behaviour | views_gap | 13 | 0.019 | 4.0 |
| behaviour | pure_relay | 242 | 0.346 | 0.99 |
| behaviour | broad_instant | 44 | 0.063 | 100.0 |
| behaviour | steady_delay | 173 | 0.247 | 10.0 |
| behaviour | high_throughput | 18 | 0.026 | 1000.0 |
| behaviour | abrupt_volume | 51 | 0.073 | 10000.0 |
| coordination | in_tight_group | 959 | 1.372 |  |


### bigdata_pipeline/analysis/suspicious/mirrors  (974 lignes, 32 colonnes)

| ﻿channel_id | n_posts | n_forwarded | share_fast10 | top_origin_share | sec_mode_share | top_source | n_from_source | delay_p25_s | delay_median_s | delay_p75_s | delay_iqr_s | share_from_source_within10s | first_month |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2017727373 | 1026 | 396.0 | 1.0 | 1.0 | 0.024366471734892786 | 2091881957 | 396 | 3.0 | 3.0 | 3.0 | 0.0 | 1.0 | 2024-06 |
| 1103623340 | 2172 | 378.0 | 1.0 | 1.0 | 0.02992633517495396 | 1422103669 | 378 | 0.0 | 0.0 | 1.0 | 1.0 | 1.0 | 2024-06 |
| 1472293081 | 1266 | 286.0 | 1.0 | 1.0 | 0.026066350710900472 | 1295892133 | 286 | 0.0 | 0.0 | 1.0 | 1.0 | 1.0 | 2024-07 |
| 1448036582 | 1122 | 192.0 | 1.0 | 1.0 | 0.027629233511586453 | 1370660430 | 192 | 3.0 | 3.0 | 3.0 | 0.0 | 1.0 | 2023-10 |
| 2129330874 | 1090 | 121.0 | 1.0 | 1.0 | 0.030275229357798167 | 1792493685 | 121 | 3.0 | 3.0 | 3.0 | 0.0 | 1.0 | 2024-07 |
| 1627525641 | 5235 | 86.0 | 1.0 | 1.0 | 0.021585482330468003 | 1747092651 | 86 | 3.0 | 3.0 | 3.0 | 0.0 | 1.0 | 2024-07 |
| 2145518983 | 172 | 78.0 | 1.0 | 1.0 | 0.06976744186046512 | 1811185364 | 78 | 3.0 | 3.0 | 3.0 | 0.0 | 1.0 | 2024-01 |
| 1454618612 | 1000 | 58.0 | 1.0 | 1.0 | 0.037 | 1492144658 | 58 | 0.0 | 0.0 | 0.0 | 0.0 | 1.0 | 2022-12 |
| 1321286654 | 1000 | 54.0 | 1.0 | 1.0 | 0.029 | 1662341055 | 54 | 3.0 | 3.0 | 3.0 | 0.0 | 1.0 | 2023-01 |
| 2139510839 | 41 | 40.0 | 1.0 | 1.0 | 0.17073170731707318 | 1807586880 | 40 | 3.0 | 3.0 | 3.0 | 0.0 | 1.0 | 2024-04 |
| 1818809412 | 271 | 38.0 | 1.0 | 1.0 | 0.04059040590405904 | 1977634199 | 38 | 3.0 | 3.0 | 3.0 | 0.0 | 1.0 | 2024-08 |
| 1224921902 | 1100 | 1100.0 | 0.9990909090909091 | 1.0 | 0.02909090909090909 | 1705782043 | 1100 | 3.0 | 3.0 | 3.0 | 0.0 | 0.9990909090909091 | 2024-06 |
| 1778227158 | 13225 | 689.0 | 0.9985486211901307 | 0.9985486211901307 | 0.02162570888468809 | 1766365025 | 688 | 3.0 | 3.0 | 3.0 | 0.0 | 1.0 | 2024-07 |
| 1678586031 | 9423 | 8972.0 | 0.9982166740971913 | 0.9995541685242978 | 0.0196328133290884 | 1478404564 | 8968 | 3.0 | 3.0 | 3.0 | 0.0 | 0.9986619090098127 | 2024-07 |
| 1692765425 | 4319 | 1473.0 | 0.9959266802443992 | 0.9959266802443992 | 0.028941884695531373 | 1779399663 | 1467 | 3.0 | 3.0 | 3.0 | 0.0 | 1.0 | 2024-07 |
| 1769723894 | 3427 | 437.0 | 0.9954233409610984 | 0.9954233409610984 | 0.023635833090166328 | 1681280122 | 435 | 3.0 | 3.0 | 3.0 | 0.0 | 1.0 | 2022-03 |
| 2134997489 | 898 | 826.0 | 0.9939467312348669 | 0.9939467312348669 | 0.32516703786191536 | 1782678596 | 821 | 3.0 | 3.0 | 3.0 | 0.0 | 1.0 | 2023-11 |
| 1584552466 | 1833 | 140.0 | 0.9928571428571429 | 0.9928571428571429 | 0.024004364429896344 | 1505706709 | 139 | 3.0 | 3.0 | 3.0 | 0.0 | 1.0 | 2024-06 |
| 1740956434 | 1000 | 113.0 | 0.9911504424778761 | 0.9911504424778761 | 0.028 | 1371637271 | 112 | 0.0 | 0.0 | 1.0 | 1.0 | 1.0 | 2024-07 |
| 1355831688 | 3226 | 1737.0 | 0.9902130109383995 | 0.9948186528497409 | 0.04277743335399876 | 1007432626 | 1728 | 1.0 | 1.0 | 2.0 | 1.0 | 0.9953703703703703 | 2024-07 |
| 1772049762 | 120878 | 23202.0 | 0.9889664684078958 | 0.9891388673390225 | 0.017612799682324327 | 1599088269 | 22950 | 3.0 | 3.0 | 3.0 | 0.0 | 0.9998257080610021 | 2022-03 |
| 1245958321 | 21456 | 2324.0 | 0.9858003442340791 | 0.9858003442340791 | 0.020320656226696494 | 1404657908 | 2291 | 3.0 | 3.0 | 3.0 | 0.0 | 1.0 | 2024-07 |
| 2112495548 | 809 | 492.0 | 0.9857723577235772 | 0.9857723577235772 | 0.030902348578491966 | 1829587738 | 485 | 3.0 | 3.0 | 4.0 | 1.0 | 1.0 | 2024-05 |
| 1952756501 | 1021 | 943.0 | 0.9830328738069989 | 1.0 | 0.03330068560235064 | 1911810944 | 943 | 3.0 | 3.0 | 3.0 | 0.0 | 0.9830328738069989 | 2024-02 |
| 1920775901 | 250 | 228.0 | 0.9824561403508771 | 0.9824561403508771 | 0.096 | 1872049105 | 224 | 3.0 | 3.0 | 3.0 | 0.0 | 1.0 | 2024-08 |
| 2080214578 | 308 | 169.0 | 0.9822485207100592 | 1.0 | 0.05194805194805195 | 2037751990 | 169 | 3.0 | 3.0 | 3.0 | 0.0 | 0.9822485207100592 | 2024-03 |
| 1730210953 | 2568 | 251.0 | 0.9800796812749004 | 0.9920318725099602 | 0.02219626168224299 | 1781143774 | 249 | 3.0 | 3.0 | 4.0 | 1.0 | 0.9879518072289156 | 2024-06 |
| 2105557041 | 677 | 48.0 | 0.9791666666666666 | 0.9791666666666666 | 0.0310192023633678 | 2107369412 | 47 | 3.0 | 3.0 | 3.0 | 0.0 | 1.0 | 2024-03 |
| 1219094968 | 22250 | 91.0 | 0.978021978021978 | 0.978021978021978 | 0.018426966292134833 | 1251217154 | 89 | 3.0 | 3.0 | 3.0 | 0.0 | 1.0 | 2024-07 |
| 1280236842 | 3921 | 719.0 | 0.9749652294853964 | 0.9624478442280946 | 0.022443254271869422 | 1203517764 | 692 | 0.0 | 0.0 | 1.0 | 1.0 | 1.0 | 2024-07 |
| 1968342124 | 4060 | 477.0 | 0.9748427672955975 | 0.9748427672955975 | 0.025123152709359605 | 1498303038 | 465 | 3.0 | 3.0 | 3.0 | 0.0 | 1.0 | 2024-07 |
| 1760916609 | 34320 | 8405.0 | 0.9721594289113623 | 0.9738251041046996 | 0.06756993006993008 | 1692972609 | 8185 | 3.0 | 3.0 | 3.0 | 0.0 | 0.9982895540623091 | 2022-10 |
| 1591609864 | 4094 | 2951.0 | 0.9705184683158251 | 0.9711962046763809 | 0.02149487054225696 | 1091293599 | 2866 | 3.0 | 4.0 | 5.0 | 2.0 | 0.9989532449406838 | 2024-07 |
| 2116355977 | 342 | 100.0 | 0.97 | 0.97 | 0.03216374269005848 | 1851913690 | 97 | 3.0 | 3.0 | 3.0 | 0.0 | 1.0 | 2023-11 |
| 1641066306 | 1834 | 920.0 | 0.9695652173913043 | 1.0 | 0.031079607415485277 | 1657259022 | 920 | 3.0 | 4.0 | 5.0 | 2.0 | 0.9695652173913043 | 2024-05 |
| 1757188865 | 6847 | 1986.0 | 0.9657603222557906 | 0.9657603222557906 | 0.02059296042062217 | 1383582274 | 1918 | 3.0 | 3.0 | 3.0 | 0.0 | 1.0 | 2022-01 |
| 1343887091 | 9651 | 5120.0 | 0.962890625 | 0.963671875 | 0.04113563361309709 | 1478603215 | 4934 | 3.0 | 3.0 | 3.0 | 0.0 | 0.999189298743413 | 2024-07 |
| 1529985281 | 6845 | 2367.0 | 0.9573299535276721 | 0.9569074778200254 | 0.053177501826150476 | 1716301978 | 2265 | 3.0 | 3.0 | 3.0 | 0.0 | 0.9995584988962473 | 2024-07 |
| 1890446224 | 15194 | 6886.0 | 0.955126343305257 | 0.9546906767354052 | 0.03422403580360669 | 1793975669 | 6574 | 3.0 | 3.0 | 3.0 | 0.0 | 1.0 | 2023-06 |
| 1341570220 | 250 | 171.0 | 0.9532163742690059 | 0.9941520467836257 | 0.072 | 1754270170 | 170 | 3.0 | 3.0 | 3.0 | 0.0 | 0.9588235294117647 | 2024-08 |


### bigdata_pipeline/analysis/suspicious/monthly_trend  (108 lignes, 9 colonnes)

| month | n_forwards | n_fast10 | n_fast60 | median_delay_s | fast10_pct | fast60_pct | n_cascades | n_tight |
|---|---|---|---|---|---|---|---|---|
| 2015-10 | 232 | 4 | 22 | 2907 | 1.72 | 9.48 |  |  |
| 2015-11 | 198 | 9 | 47 | 3208 | 4.55 | 23.74 |  |  |
| 2015-12 | 441 | 17 | 60 | 90032 | 3.85 | 13.61 | 1.0 | 0.0 |
| 2016-01 | 254 | 6 | 29 | 3870 | 2.36 | 11.42 | 1.0 | 0.0 |
| 2016-02 | 610 | 6 | 63 | 2488 | 0.98 | 10.33 |  |  |
| 2016-03 | 498 | 17 | 59 | 1491 | 3.41 | 11.85 | 2.0 | 0.0 |
| 2016-04 | 876 | 16 | 76 | 2771 | 1.83 | 8.68 | 2.0 | 0.0 |
| 2016-05 | 990 | 10 | 99 | 3883 | 1.01 | 10.0 |  |  |
| 2016-06 | 1086 | 12 | 101 | 1762 | 1.1 | 9.3 | 3.0 | 0.0 |
| 2016-07 | 1154 | 19 | 112 | 2082 | 1.65 | 9.71 | 1.0 | 0.0 |
| 2016-08 | 1439 | 24 | 148 | 3203 | 1.67 | 10.28 | 5.0 | 0.0 |
| 2016-09 | 1781 | 43 | 178 | 1914 | 2.41 | 9.99 |  |  |
| 2016-10 | 2449 | 25 | 161 | 4809 | 1.02 | 6.57 |  |  |
| 2016-11 | 2629 | 43 | 221 | 3143 | 1.64 | 8.41 |  |  |
| 2016-12 | 2800 | 34 | 175 | 5309 | 1.21 | 6.25 |  |  |
| 2017-01 | 4617 | 28 | 343 | 4190 | 0.61 | 7.43 | 2.0 | 0.0 |
| 2017-02 | 4960 | 36 | 349 | 2620 | 0.73 | 7.04 | 1.0 | 0.0 |
| 2017-03 | 7125 | 73 | 845 | 1391 | 1.02 | 11.86 | 1.0 | 0.0 |
| 2017-04 | 9754 | 149 | 1503 | 875 | 1.53 | 15.41 | 2.0 | 0.0 |
| 2017-05 | 10568 | 120 | 1293 | 1336 | 1.14 | 12.24 | 13.0 | 0.0 |
| 2017-06 | 12589 | 269 | 2098 | 779 | 2.14 | 16.67 | 17.0 | 1.0 |
| 2017-07 | 11544 | 159 | 1501 | 1346 | 1.38 | 13.0 | 18.0 | 1.0 |
| 2017-08 | 16665 | 251 | 2197 | 1287 | 1.51 | 13.18 | 24.0 | 0.0 |
| 2017-09 | 19109 | 288 | 2328 | 1479 | 1.51 | 12.18 | 16.0 | 0.0 |
| 2017-10 | 26243 | 401 | 2940 | 1632 | 1.53 | 11.2 | 28.0 | 1.0 |
| 2017-11 | 24848 | 413 | 2622 | 1965 | 1.66 | 10.55 | 27.0 | 1.0 |
| 2017-12 | 26059 | 437 | 2990 | 2022 | 1.68 | 11.47 | 29.0 | 1.0 |
| 2018-01 | 24806 | 416 | 2754 | 2223 | 1.68 | 11.1 | 23.0 | 0.0 |
| 2018-02 | 27185 | 544 | 3207 | 1841 | 2.0 | 11.8 | 18.0 | 1.0 |
| 2018-03 | 33033 | 579 | 4019 | 1500 | 1.75 | 12.17 | 25.0 | 1.0 |
| 2018-04 | 33757 | 564 | 3871 | 1483 | 1.67 | 11.47 | 34.0 | 3.0 |
| 2018-05 | 32851 | 520 | 3678 | 1599 | 1.58 | 11.2 | 20.0 | 0.0 |
| 2018-06 | 30736 | 555 | 3761 | 1555 | 1.81 | 12.24 | 8.0 | 0.0 |
| 2018-07 | 35756 | 693 | 4982 | 1175 | 1.94 | 13.93 | 13.0 | 1.0 |
| 2018-08 | 33781 | 452 | 3749 | 1538 | 1.34 | 11.1 | 15.0 | 0.0 |
| 2018-09 | 42007 | 621 | 5464 | 1121 | 1.48 | 13.01 | 33.0 | 4.0 |
| 2018-10 | 42519 | 659 | 5575 | 1166 | 1.55 | 13.11 | 35.0 | 2.0 |
| 2018-11 | 38611 | 482 | 4388 | 1600 | 1.25 | 11.36 | 27.0 | 1.0 |
| 2018-12 | 43198 | 717 | 5385 | 1564 | 1.66 | 12.47 | 33.0 | 1.0 |
| 2019-01 | 41936 | 572 | 4766 | 1741 | 1.36 | 11.36 | 27.0 | 1.0 |


### bigdata_pipeline/analysis/suspicious/review  (214 lignes, 28 colonnes)

| ﻿channel_id | title | username | participants_count | selection | kind | score_behaviour | score_coordination | reasons | n_posts | n_forwarded | n_origins | top_source | source_title |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1295312380 | 🗣 Ukraine Reality | ukrainereality |  | behaviour | not_selected | 6 | 0 | fast_relay, pure_relay, broad_instant, s | 60849 | 60739.0 | 492.0 | 1050820672.0 | ТАСС |
| 1770716048 | 🇷🇺 Твой Мелитополь ™ | t_mlt |  | behaviour+group | linked_discussion | 4 | 1 | fast_relay, single_source, broad_instant | 25234 | 23623.0 | 241.0 | 1899310737.0 | Мелитополь наш |
| 1772049762 | Чат - Информационный центр СК России | infocentrskrfchat |  | behaviour | linked_discussion | 4 | 0 | fast_relay, single_source, broad_instant | 120878 | 23202.0 | 127.0 | 1599088269.0 | Информационный центр СК России |
| 1219094968 | Сomments | fbchatik |  | behaviour | discussion_possible | 4 | 0 | fast_relay, single_source, high_throughp | 22250 | 91.0 | 3.0 | 1251217154.0 | Fighterbomber |
| 1245958321 | 🎭 Политический Юмор 🎭 Чат 💬 🔔 | Chat_Humor_and_Politics |  | behaviour | linked_discussion | 4 | 0 | fast_relay, single_source, steady_delay, | 21456 | 2324.0 | 11.0 | 1404657908.0 | 🎭 Политический Юмор 🎭 |
| 1778227158 | ТАКСИСТЫ РОССИИ / ЧАТ / ВЕСТИ ТАКСИ | TaxiDrivers_chat |  | behaviour | linked_discussion | 4 | 0 | fast_relay, single_source, steady_delay, | 13225 | 689.0 | 2.0 | 1766365025.0 | ВЕСТИ ТАКСИ / НОВОСТИ |
| 1678586031 | الخليل بلس | fromhebron |  | behaviour | discussion_possible | 4 | 0 | fast_relay, single_source, round_clock,  | 9423 | 8972.0 | 2.0 | 1478404564.0 |  |
| 1022928416 | قناة العهد | alahadch |  | behaviour | other | 4 | 0 | fast_relay, single_source, pure_relay, s | 6342 | 6300.0 | 3.0 | 1764926174.0 | ALAhad TV - قناة العهد |
| 1006136662 | تلخندسیاسی | Talkhand_Siyasi |  | behaviour | discussion_possible | 4 | 0 | fast_relay, single_source, pure_relay, s | 2875 | 2870.0 | 8.0 | 1106958042.0 | تَلخندسیاسی‌ اجتماعی |
| 1450985011 | General McInerne | GeneralMcInerne |  | behaviour | other | 4 | 0 | fast_relay, single_source, pure_relay, s | 1946 | 1944.0 | 1.0 | 1545383908.0 | The General |
| 1224921902 | Lagebericht | Lagebericht |  | behaviour | discussion_possible | 4 | 0 | fast_relay, single_source, pure_relay, s | 1100 | 1100.0 | 1.0 | 1705782043.0 |  |
| 1310284190 | 4Chan - /POL/HIS/INT/ | pol_4chan_bkp |  | behaviour | other | 4 | 0 | fast_relay, single_source, pure_relay, s | 1044 | 1042.0 | 9.0 | 1977936648.0 | 4Chan - /POL/HIS/INT/ |
| 1001262419 | 📷اخبار تصويري📷 | photoonline |  | behaviour | discussion_possible | 4 | 0 | fast_relay, single_source, pure_relay, s | 1000 | 998.0 | 3.0 | 1168372447.0 |  |
| 1852760554 | انتقال کرمانشاه | forwardfarsnewskermanshah |  | behaviour+group | other | 3 | 1 | fast_relay, single_source, steady_delay, | 3252 | 2865.0 | 6.0 | 1489936969.0 | اخبار کرمانشاه |
| 1865675263 | انتقال آذربایجان غربی | ForwardAzarbaijanGhFars |  | behaviour+group | linked_discussion | 3 | 1 | fast_relay, single_source, steady_delay, | 2218 | 2047.0 | 4.0 | 1967343316.0 | اخبار آذربایجان غربی |
| 2000615184 | Varzeshplus_gap | vaarzeshplus_gap |  | behaviour | not_selected | 3 | 0 | fast_relay, steady_delay, high_throughpu | 365311 | 4806.0 | 47.0 | 2046872658.0 | Varzesh+plus |
| 1799067832 | Эхо Москвы | venik_ru |  | behaviour | not_selected | 3 | 0 | fast_relay, round_clock, broad_instant | 160767 | 19543.0 | 287.0 | 1629263448.0 | КГБ-НКВД |
| 1850556859 | Болталка «Гум помощь Омск» | gumomsk_55 |  | behaviour | not_selected | 3 | 0 | fast_relay, broad_instant, steady_delay | 111376 | 11012.0 | 422.0 | 1271552977.0 | Гум помощь Омск |
| 1794778009 | АГЕНТУРА | agentura_ru |  | behaviour | not_selected | 3 | 0 | fast_relay, round_clock, broad_instant | 73128 | 14311.0 | 260.0 | 1345519782.0 | КОМПРОМАТ 1 |
| 1074492569 | New Ingress Portals | newportal |  | behaviour | not_selected | 3 | 0 | round_clock, high_throughput, abrupt_vol | 55179 |  |  |  |  |
| 1110839896 | ХабЧат 💬 | KhvChat |  | behaviour | not_selected | 3 | 0 | steady_delay, high_throughput, abrupt_vo | 45183 | 323.0 | 4.0 | 1119365436.0 | Хабаровск |
| 1313788595 | BTC Price | BTCprices |  | behaviour | not_selected | 3 | 0 | round_clock, high_throughput, abrupt_vol | 44207 |  |  |  |  |
| 1148195583 | Рандомач/Двач | rand2ch |  | behaviour | not_selected | 3 | 0 | single_source, round_clock, fixed_second | 40866 | 2310.0 | 10.0 | 1009232144.0 | Двач |
| 1760916609 | Аврора РнД | AuroraRnD |  | behaviour | linked_discussion | 3 | 0 | fast_relay, single_source, steady_delay | 34320 | 8405.0 | 42.0 | 1692972609.0 | Гражданский батальон "Аврора" |
| 1711273827 | AI ART - красивые и необычные картинки о | ai_wow_art |  | behaviour | not_selected | 3 | 0 | round_clock, high_throughput, abrupt_vol | 26011 |  |  |  |  |
| 1830833529 | Военный Ⓩ Донецк / Резервный | militarydonetsk_rezerv |  | behaviour | other | 3 | 0 | fast_relay, single_source, steady_delay | 21179 | 3544.0 | 10.0 | 1254642005.0 | Военный Ⓩ Донецк / ДНР / Сводки / СВО |
| 1522976570 | ZА НАШИХ🇷🇺КРЫМ ЧАТ | zanashih2022chat |  | behaviour | not_selected | 3 | 0 | fast_relay, broad_instant, steady_delay | 16736 | 3190.0 | 153.0 | 1795910562.0 | ZA НАШИХ🇷🇺КРЫМ |
| 1780659775 | 🔥SHAMAN-ЭПОХА чат | SHAMAN_EPOCH |  | behaviour | not_selected | 3 | 0 | fast_relay, broad_instant, abrupt_volume | 15819 | 3753.0 | 198.0 | 1952199376.0 | 🔥SHAMAN – ЭПОХА🔥 |
| 1529625613 | Отряд Ковпака Chat | kovpakchat1 |  | behaviour | not_selected | 3 | 0 | fast_relay, steady_delay, abrupt_volume | 15324 | 756.0 | 63.0 | 1739446698.0 | Отряд Ковпака |
| 1890446224 | Чат Vежливые и Zлые | chat_vezhlivye_zlye |  | behaviour | linked_discussion | 3 | 0 | fast_relay, single_source, steady_delay | 15194 | 6886.0 | 83.0 | 1793975669.0 | Vежливые и Zлые |
| 1986060137 | Чат Оперативного Севастополя | operativ_sevastopol_chat |  | behaviour | linked_discussion | 3 | 0 | fast_relay, single_source, steady_delay | 14680 | 3076.0 | 52.0 | 2134615365.0 | Оперативный Севастополь |
| 1532783740 | Achk 👁️ chat | ArmenianEyechat |  | behaviour | not_selected | 3 | 0 | fast_relay, steady_delay, abrupt_volume | 12502 | 759.0 | 63.0 | 1877692343.0 | HayAchk 👁 |
| 1085122724 | Политота - cбор! | politota_gathering |  | behaviour | not_selected | 3 | 0 | fast_relay, broad_instant, abrupt_volume | 10488 | 1207.0 | 165.0 | 1091268800.0 | Политота |
| 1343887091 | АГС_Русского_Донбасса Chat | ags_chat123 |  | behaviour | linked_discussion | 3 | 0 | fast_relay, single_source, steady_delay | 9651 | 5120.0 | 31.0 | 1478603215.0 | АГС_Русского_Донбасса |
| 1628635638 | Твои Герои,Саратов! Z Chat | ZovSAG |  | behaviour | linked_discussion | 3 | 0 | fast_relay, single_source, steady_delay | 7899 | 695.0 | 14.0 | 1681912898.0 | Твои Герои, Саратов! ZOV |
| 1780535847 | Закулисье Израиля | israel_topical |  | behaviour | instant_relay | 3 | 0 | fast_relay, single_source, steady_delay | 7220 | 536.0 | 14.0 | 1295892133.0 | Кумта - тревога - Cumta - Red Alert |
| 1757188865 | Быть русским (чат) | bytrusskim |  | behaviour | linked_discussion | 3 | 0 | fast_relay, single_source, steady_delay | 6847 | 1986.0 | 27.0 | 1383582274.0 | Быть русским |
| 1529985281 | СРОЧНО И ТОЧНО. ЧАТ. | srochno_chat |  | behaviour | linked_discussion | 3 | 0 | fast_relay, single_source, steady_delay | 6845 | 2367.0 | 24.0 | 1716301978.0 | СРОЧНО И ТОЧНО - дайджест новостей |
| 1201449520 | Дмитрий Навка | pescov_navka |  | behaviour | not_selected | 3 | 0 | fast_relay, round_clock, steady_delay | 6531 | 1517.0 | 21.0 | 1287556984.0 | Тайны Кремля |
| 1484513106 | Генерал Лебедь | lebed_general |  | behaviour | not_selected | 3 | 0 | fast_relay, round_clock, steady_delay | 6482 | 1515.0 | 22.0 | 1287556984.0 | Тайны Кремля |


### bigdata_pipeline/analysis/suspicious/suspicious_channels  (500 lignes, 19 colonnes)

| channel_id | score | score_behaviour | score_coordination | reasons | n_posts | n_forwarded | share_forwarded | n_origins | share_fast10 | top_origin_share | delay_iqr_s | hour_entropy | sec_mode_share |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1295312380 | 6 | 6 | 0 | fast_relay, pure_relay, broad_instant, s | 60849 | 60739.0 | 0.9982 | 492.0 | 0.7166 | 0.0322 | 5.0 | 0.9358 | 0.0433 |
| 1770716048 | 5 | 4 | 1 | fast_relay, single_source, broad_instant | 25234 | 23623.0 | 0.9362 | 241.0 | 0.9397 | 0.9395 | 1.0 | 0.8936 | 0.021 |
| 1224921902 | 4 | 4 | 0 | fast_relay, single_source, pure_relay, s | 1100 | 1100.0 | 1.0 | 1.0 | 0.9991 | 1.0 | 0.0 | 0.9565 | 0.0291 |
| 1450985011 | 4 | 4 | 0 | fast_relay, single_source, pure_relay, s | 1946 | 1944.0 | 0.999 | 1.0 | 0.5823 | 1.0 | 10.0 | 0.908 | 0.0247 |
| 1678586031 | 4 | 4 | 0 | fast_relay, single_source, round_clock,  | 9423 | 8972.0 | 0.9521 | 2.0 | 0.9982 | 0.9996 | 0.0 | 0.9893 | 0.0196 |
| 1778227158 | 4 | 4 | 0 | fast_relay, single_source, steady_delay, | 13225 | 689.0 | 0.0521 | 2.0 | 0.9985 | 0.9985 | 0.0 | 0.9763 | 0.0216 |
| 1006136662 | 4 | 4 | 0 | fast_relay, single_source, pure_relay, s | 2875 | 2870.0 | 0.9983 | 8.0 | 0.9456 | 0.9958 | 1.0 | 0.865 | 0.024 |
| 1772049762 | 4 | 4 | 0 | fast_relay, single_source, broad_instant | 120878 | 23202.0 | 0.1919 | 127.0 | 0.989 | 0.9891 | 0.0 | 0.9335 | 0.0176 |
| 1245958321 | 4 | 4 | 0 | fast_relay, single_source, steady_delay, | 21456 | 2324.0 | 0.1083 | 11.0 | 0.9858 | 0.9858 | 0.0 | 0.9744 | 0.0203 |
| 1865675263 | 4 | 3 | 1 | fast_relay, single_source, steady_delay, | 2218 | 2047.0 | 0.9229 | 4.0 | 0.7973 | 0.9936 | 4.0 | 0.8858 | 0.0234 |


### bigdata_pipeline/analysis/suspicious/suspicious_summary  (15 lignes, 2 colonnes)

| metric | value |
|---|---|
| channels evaluated | 69909 |
| channels with 1+ flag | 4322 |
| channels with 2+ flags | 419 |
| channels with 3+ flags | 121 |
| coordinated pairs kept | 62989 |
| channels with 2+ behaviour flags | 346 |
| channels with 3+ behaviour flags | 114 |
| channels in tight groups (coordination f | 959 |
| ... of which with 1+ behaviour flag | 83 |
| coordinated groups | 808 |
| channels in groups | 4979 |
| largest group (channels) | 278 |
| fast10 % first month | 1.72 |
| fast10 % last month | 9.71 |
| fast10 % max month | 2024-09 (9.7) |


## Figures : analysis/figures/suspicious

![/home/dvopssl/Documents/telescope_data_analysis/bigdata_pipeline/analysis/figures/suspicious/cascades_monthly.png](/home/dvopssl/Documents/telescope_data_analysis/bigdata_pipeline/analysis/figures/suspicious/cascades_monthly.png)

![/home/dvopssl/Documents/telescope_data_analysis/bigdata_pipeline/analysis/figures/suspicious/coordinated_groups.png](/home/dvopssl/Documents/telescope_data_analysis/bigdata_pipeline/analysis/figures/suspicious/coordinated_groups.png)

![/home/dvopssl/Documents/telescope_data_analysis/bigdata_pipeline/analysis/figures/suspicious/fast_share_monthly.png](/home/dvopssl/Documents/telescope_data_analysis/bigdata_pipeline/analysis/figures/suspicious/fast_share_monthly.png)

![/home/dvopssl/Documents/telescope_data_analysis/bigdata_pipeline/analysis/figures/suspicious/fast_trend_excluding.png](/home/dvopssl/Documents/telescope_data_analysis/bigdata_pipeline/analysis/figures/suspicious/fast_trend_excluding.png)

![/home/dvopssl/Documents/telescope_data_analysis/bigdata_pipeline/analysis/figures/suspicious/fast_vs_source.png](/home/dvopssl/Documents/telescope_data_analysis/bigdata_pipeline/analysis/figures/suspicious/fast_vs_source.png)

![/home/dvopssl/Documents/telescope_data_analysis/bigdata_pipeline/analysis/figures/suspicious/indicator_counts.png](/home/dvopssl/Documents/telescope_data_analysis/bigdata_pipeline/analysis/figures/suspicious/indicator_counts.png)

![/home/dvopssl/Documents/telescope_data_analysis/bigdata_pipeline/analysis/figures/suspicious/mirror_delay.png](/home/dvopssl/Documents/telescope_data_analysis/bigdata_pipeline/analysis/figures/suspicious/mirror_delay.png)

![/home/dvopssl/Documents/telescope_data_analysis/bigdata_pipeline/analysis/figures/suspicious/mirror_families.png](/home/dvopssl/Documents/telescope_data_analysis/bigdata_pipeline/analysis/figures/suspicious/mirror_families.png)

![/home/dvopssl/Documents/telescope_data_analysis/bigdata_pipeline/analysis/figures/suspicious/month_drivers_concentration.png](/home/dvopssl/Documents/telescope_data_analysis/bigdata_pipeline/analysis/figures/suspicious/month_drivers_concentration.png)

![/home/dvopssl/Documents/telescope_data_analysis/bigdata_pipeline/analysis/figures/suspicious/score_distribution.png](/home/dvopssl/Documents/telescope_data_analysis/bigdata_pipeline/analysis/figures/suspicious/score_distribution.png)


# Cartes et fichiers de figures non rattachés ci-dessus

```
bigdata_pipeline/analysis/figures/anomalies/map_anomaly_activity.html  0.0 MB
bigdata_pipeline/analysis/figures/anomalies/map_city_correlation.html  0.0 MB
bigdata_pipeline/analysis/figures/anomalies/map_city_links.html  0.2 MB
bigdata_pipeline/analysis/figures/anomalies/map_synchronized_peaks.html  0.1 MB
bigdata_pipeline/analysis/figures/community_detection/meta_graph.gexf  0.1 MB
```


# Extraits de code : seuils, règles, paramètres


### bigdata_pipeline/spark/spark_session.py

```
2: One place to configure Spark for a small machine (default: 3 cores, 8 GB RAM).
7:   TELESCOPE_CORES              cores used                       (default 3)
8:   TELESCOPE_SPARK_MEMORY       JVM memory                       (default 4g)
12: In local mode the "executors" live inside the driver JVM, so TELESCOPE_SPARK_MEMORY
13: is the whole Spark memory. With 8 GB total, 4g leaves room for the OS and the
14: Python workers. Raise it only if your machine has memory to spare.
26:     cores = int(os.environ.get("TELESCOPE_CORES", "3"))
27:     memory = os.environ.get("TELESCOPE_SPARK_MEMORY", "4g")
32:         SparkSession.builder.master(f"local[{cores}]").appName(app)
33:         .config("spark.driver.memory", memory)
36:         .config("spark.sql.shuffle.partitions", os.environ.get("TELESCOPE_SHUFFLE_PARTITIONS", "48"))
```


### bigdata_pipeline/spark/job1_clean.py

```
94:     ap.add_argument("--files-per-batch", type=int, default=12, help="Parquet files written per batch")
```


### bigdata_pipeline/spark/job1b_dedup.py

```
41:     from pyspark.sql import Window
50:     rank = Window.partitionBy(*KEY).orderBy(
71:         flags = [F.when(F.size(F.collect_set(F.coalesce(F.col(x).cast("string"), F.lit("<null>")))) > 1, 1)
```


### bigdata_pipeline/spark/job2_chains.py

```
45:     from pyspark.sql import Window
54:     ordered = Window.partitionBy(*key).orderBy("ts", "dest_channel", "msg_id")
55:     whole = Window.partitionBy(*key)
```


### bigdata_pipeline/spark/job3_edges.py

```
50:         res.coalesce(1).write.mode("overwrite").option("header", True).csv(str(csv_dir))
```


### bigdata_pipeline/spark/job4_stats.py

```
47:                 F.coalesce(F.sum("views"), F.lit(0)).alias("total_views"),
48:                 F.coalesce(F.sum("forwards"), F.lit(0)).alias("total_forwards"),
61:         res.coalesce(1).write.mode("overwrite").option("header", True).csv(str(csv_dir))
```


### bigdata_pipeline/spark/job5_city_daily.py

```
59:             .where((F.col("date") >= F.lit(args.min_date)) & (F.col("date") <= F.lit(args.max_date))))
65:                   F.coalesce(F.sum("views"), F.lit(0)).alias("views"),
83:         res.coalesce(1).write.mode("overwrite").option("header", True).csv(str(csv_dir))
```


### bigdata_pipeline/spark/job6_suspicious.py

```
9:                         n_posts, views_mean, views_median, zero_view_share, forwards_mean,
10:                         n_active_days, max_posts_day, median_posts_day,
12:                         share_fast10, share_fast60, median_delay_s, delay_p25_s, delay_p75_s, sec_mode_share
14:   coordinated_pairs     channel_a, channel_b, n_shared, n_origins, median_dt_s
15:                         = pairs of channels that relay the SAME original message within --window seconds
19:   forward_speed_monthly month, n_forwards, n_fast10, n_fast60, median_delay_s
26:   sec_mode_share      share of posts published on the most frequent second of the minute (baseline 1/60)
28:                       --neighbours relays when they follow within --window seconds (keeps the join bounded)
32: Usage: python3 job6_suspicious.py --out telescope_pipeline_files [--min-posts 30] [--window 60] [--csv]
45:     ap.add_argument("--min-posts", type=int, default=30, help="channels with fewer messages are ignored")
46:     ap.add_argument("--window", type=int, default=60, help="max seconds between two relays of the same message to pair them")
48:     ap.add_argument("--max-relays", type=int, default=500, help="skip original messages relayed more than this (viral posts)")
50:     ap.add_argument("--min-cascade", type=int, default=10, help="min relays to keep a cascade")
58:     from pyspark.sql import Window
69:             res.coalesce(1).write.mode("overwrite").option("header", True).csv(str(args.out / "gold" / f"{name}_csv"))
74:          .where((F.col("date") >= F.lit(args.min_date)) & (F.col("date") <= F.lit(args.max_date))))
84:                  F.percentile_approx("views", 0.5).alias("views_median"),
87:             .where(F.col("n_posts") >= args.min_posts))
92:                   F.max("count").alias("max_posts_day"),
93:                   F.percentile_approx("count", 0.5).alias("median_posts_day")))
98:                  F.avg(F.when(F.col("delay_s") <= 10, 1.0).otherwise(0.0)).alias("share_fast10"),
99:                  F.avg(F.when(F.col("delay_s") <= 60, 1.0).otherwise(0.0)).alias("share_fast60"),
100:                  F.percentile_approx("delay_s", 0.5).alias("median_delay_s"),
101:                  F.percentile_approx("delay_s", 0.25).alias("delay_p25_s"),
102:                  F.percentile_approx("delay_s", 0.75).alias("delay_p75_s")))
126:          .withColumn("n_relays", F.count(F.lit(1)).over(Window.partitionBy(*key)))
127:          .where((F.col("n_relays") >= 2) & (F.col("n_relays") <= args.max_relays)))
128:     ordered = Window.partitionBy(*key).orderBy("ts", "dest_channel", "msg_id")
138:     allp = allp.where(F.col("b").isNotNull() & (F.col("a") != F.col("b")) & (F.col("dt") <= args.window))
143:                   F.percentile_approx("dt", 0.5).alias("median_dt_s"))
144:              .where(F.col("n_shared") >= args.min_shared))
153:             .where(F.col("n_relays") >= args.min_cascade))
155:               .where(F.col("ts") - F.col("first_ts") <= 600)
167:                   F.sum(F.when(F.col("delay_s") <= 10, 1).otherwise(0)).alias("n_fast10"),
168:                   F.sum(F.when(F.col("delay_s") <= 60, 1).otherwise(0)).alias("n_fast60"),
169:                   F.percentile_approx("delay_s", 0.5).alias("median_delay_s")))
```


### bigdata_pipeline/analysis/community_detection_v2.py

```
16:   5. Optional: Leiden vs Infomap agreement, noise floor (--seed-baseline), number of communities vs
17:      resolution (--resolution-curve), communities named by dominant language (--languages).
27:   add --skip-infomap to go faster, --resolution 0.5 for fewer/larger communities
75: def build_net(df, min_weight=1):
78:     d = d[(d.origin_channel != d.dest_channel) & (d.n_forwards >= min_weight)]
94: def run_leiden(net, resolution=1.0, seed=42):
99:     random.seed(seed)
102:                             resolution=resolution, n_iterations=-1)
170: def flows_table(net, mem, top=15):
233:     ax.grid(True, which="major", linestyle="--", linewidth=0.8, color="#d9d9d9")
263:     fig.tight_layout(); fig.savefig(figdir / "community_size_rank.png", dpi=200); plt.close(fig)
273:             ax.set_xticks(yearly["year"]); ax.tick_params(axis="x", rotation=60)
274:         fig.tight_layout(); fig.savefig(figdir / "yearly_structure.png", dpi=200); plt.close(fig)
281:             if "nmi_other_seed" in yearly and yearly["nmi_other_seed"].notna().any():
282:                 ax.plot(yearly["year"], yearly["nmi_other_seed"], color=ORANGE, linewidth=2, marker="o",
284:                         label="Same year, different random seed")
289:             fig.tight_layout(); fig.savefig(figdir / "yearly_stability.png", dpi=200); plt.close(fig)
295:     ax.set_xticks(range(len(labels))); ax.set_xticklabels(labels, rotation=60, fontsize=8)
303:             if mat[i, j] >= 0.10:
306:     cb = fig.colorbar(im, ax=ax, fraction=0.04, pad=0.02); cb.ax.tick_params(labelsize=8)
308:     fig.tight_layout(); fig.savefig(figdir / "flows_between_communities.png", dpi=200); plt.close(fig)
316: def resolution_curve(net, resolutions, seed, base_res, base_stats):
317:     """Leiden at several resolutions (the base one is reused): communities and modularity."""
319:     for r in resolutions:
324:             st = partition_stats(net, relabel_by_size(run_leiden(net, r, seed)))
326:         rows.append({"resolution": r, "n_communities": st["n_communities"], "modularity": st["modularity"],
328:         print(f"  resolution {r}: {st['n_communities']:,} communities, Q={st['modularity']}")
368:     """The v1 chart types: size histogram, degree CCDF, number of communities vs resolution."""
378:     ax.hist(sizes, bins=40, color="#2F5597", edgecolor="white", rwidth=0.9)
383:     fig.tight_layout(); fig.savefig(figdir / "community_size_distribution.png", dpi=200); plt.close(fig)
396:     ax.grid(True, which="minor", linestyle="--", linewidth=0.5, color="#e6e6e6")
397:     fig.tight_layout(); fig.savefig(figdir / "degree_distribution.png", dpi=200); plt.close(fig)
399:     # number of communities vs. Leiden resolution
402:         ax.plot(curve["resolution"], curve["n_communities"], color="#E8A33D", linewidth=2, marker="o")
403:         ax.set_xlabel("Resolution parameter"); ax.set_ylabel("Number of communities")
404:         ax.set_title("Number of communities vs. resolution (Leiden)"); _style(ax)
405:         fig.tight_layout(); fig.savefig(figdir / "resolution_curve.png", dpi=200); plt.close(fig)
411:     "resolution_curve.png": "number of communities vs. Leiden resolution (needs --resolution-curve).",
416:     "yearly_stability.png": "NMI between consecutive years, with the same-year/other-seed noise floor when --seed-baseline is used.",
493: def top_communities_chart(figdir, mem, names, top=20):
510:     ax.set_xticks(range(k)); ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=7.5)
512:     ax.grid(True, axis="y", linestyle="--", linewidth=0.8, color="#d9d9d9"); ax.set_axisbelow(True)
514:     fig.tight_layout(); fig.savefig(Path(figdir) / "top_20_communities.png", dpi=200); plt.close(fig)
523:            f"{args.min_weight} forward(s) dropped.\n"
524:            f"- Leiden: modularity objective, resolution {args.resolution}, seed {args.seed}, weights = number of "
529:     net = build_net(edges, args.min_weight)
546:         leiden = relabel_by_size(run_leiden(net, args.resolution, args.seed))
609:     if args.seed_baseline:
611:         other = relabel_by_size(run_leiden(net, args.resolution, args.seed + 1))
612:         comp.append({"pair": "leiden_seed_vs_leiden_seed+1", **compare(net.nodes, leiden, net.nodes, other)})
613:         print(f"seed baseline (full graph): NMI {comp[-1]['nmi']} ({time.time()-t:.0f}s)")
621:                 "leiden_seed_vs_leiden_seed+1 is the same algorithm run twice with different random seeds: "
630:             if len(n_y.src) < args.min_year_edges:
633:             mem = relabel_by_size(run_leiden(n_y, args.resolution, args.seed))
638:             if args.seed_baseline:
639:                 alt = relabel_by_size(run_leiden(n_y, args.resolution, args.seed + 1))
640:                 r["nmi_other_seed"] = compare(n_y.nodes, mem, n_y.nodes, alt)["nmi"]
654:         if "nmi_other_seed" in yearly:
655:             yc["nmi_other_seed"] = "NMI between two Leiden runs of the SAME year with different random seeds (noise floor)"
661:     if args.resolution_curve:
662:         print("resolution curve ...")
663:         curve = resolution_curve(net, [float(x) for x in args.curve_resolutions.split(",")], args.seed,
664:                                  args.resolution, partition_stats(net, leiden))
665:         cc = {"resolution": "Leiden resolution parameter", "n_communities": "number of communities",
666:               "modularity": "modularity of the partition (standard definition, resolution 1)",
668:               "seconds": "run time (empty for the resolution already computed)"}
669:         W.table("resolution_curve", curve[list(cc)],
670:                 "Leiden run at several resolutions on the same graph: how the partition coarsens or splits.", cc)
707: def synthetic(seed=0, groups=6, size=50, years=(2020, 2021, 2022)):
709:     rng = np.random.default_rng(seed)
```


### bigdata_pipeline/analysis/language_analysis_v2.py

```
20:   6. inference_accuracy / channel_language_inferred / channel_language_votes
22:                                 with accuracy measured by hiding known labels (holdout)
120: def agreement(comm, lang, min_known=3, purity=None):
131:     out["majority_language_share"] = round(float(d.l.value_counts(normalize=True).iloc[0]), 4)
137:         big = purity[(purity.known_language >= min_known)]
138:         out[f"communities_with_{min_known}plus_known"] = len(big)
139:         out["median_purity"] = round(float(big.purity.median()), 4) if len(big) else np.nan
140:         out["share_communities_purity_ge_0.8"] = round(float((big.purity >= 0.8).mean()), 4) if len(big) else np.nan
199: def spread_table(comm, lang, min_channels=50):
203:         if len(g) < min_channels:
213: def infer_languages(net, lang_by_node, min_class=50, holdout=0.1, min_vote=0.6, seed=42):
214:     """Neighbour vote on the forward graph (both directions, weighted). Accuracy measured by holdout."""
219:     classes = counts[counts >= min_class].index.tolist()
226:     def votes(known_mask):
227:         rows = np.where(known_mask & (cls >= 0))[0]
232:     rng = np.random.default_rng(seed)
234:     hold = rng.choice(idx, size=max(1, int(len(idx) * holdout)), replace=False)
235:     mask = known.copy()
236:     mask[hold] = False
237:     V = votes(mask)[hold]
239:     base_class = int(np.bincount(cls[mask & (cls >= 0)], minlength=len(classes)).argmax())
240:     baseline = float((cls[hold] == base_class).mean())
249:         rows.append({"vote_share_from": lo, "vote_share_to": min(hi, 1.0), "held_out_channels": int(m.sum()),
250:                      "accuracy": round(float(ok[m].mean()), 4) if m.any() else np.nan})
251:     sel = has & (share >= min_vote)
252:     rows.append({"vote_share_from": min_vote, "vote_share_to": 1.0, "held_out_channels": int(sel.sum()),
253:                  "accuracy": round(float(ok[sel].mean()), 4) if sel.any() else np.nan})
255:     acc["row"] = [f"{a:.1f}-{b:.1f}" for a, b in zip(acc.vote_share_from, acc.vote_share_to)]
256:     acc.loc[acc.index[-1], "row"] = f">= {min_vote} (rule used)"
257:     acc["baseline_majority_language"] = round(baseline, 4)
261:     V2 = votes(known)
266:     keep = h2 & (sh2 >= min_vote)
268:                         "vote_share": sh2[keep].round(4), "neighbour_forwards": t2[keep].astype(int), "source": "inferred"})
269:     # unresolved channels: some neighbours have a known language but no language reaches min_vote
284:     votes = pd.DataFrame(data).sort_values("neighbour_forwards", ascending=False).reset_index(drop=True)
285:     return acc, inf, votes
289: def yearly_tables(edges, lang, keep_ids, min_forwards=5000, top_n=8):
298:         if tot < min_forwards:
326: def bridges_table(net, lang_by_node, comm_by_node, top=30, min_forwards=50):
340:         t = t[t.total >= min_forwards].sort_values("cross", ascending=False).head(top)
383: def activity_tables(net, lang_by_node, comm_by_node, stats=None, top_langs=12, top_channels=10):
431:     ax.grid(True, axis=axis, linestyle="--", linewidth=0.8, color="#d9d9d9")
436: def charts(figdir, lang, pur, hom, flow, acc, top=15):
447:     ax.set_xticks(range(len(vc))); ax.set_xticklabels([lname(i) for i in vc.index], rotation=45, ha="right")
450:     fig.tight_layout(); fig.savefig(fd / "language_distribution.png", dpi=200); plt.close(fig)
462:                            rotation=45, ha="right", fontsize=7.5)
466:         fig.tight_layout(); fig.savefig(fd / "community_purity.png", dpi=200); plt.close(fig)
475:         ax.set_xticks(x); ax.set_xticklabels(h.language_name, rotation=45, ha="right")
478:         fig.tight_layout(); fig.savefig(fd / "language_homophily.png", dpi=200); plt.close(fig)
496:                 if np.isfinite(v) and v >= 0.01:
499:         ax.set_xticks(range(len(order))); ax.set_xticklabels(lab, rotation=45, ha="right")
504:         fig.colorbar(im, ax=ax, fraction=0.04, pad=0.02)
505:         fig.tight_layout(); fig.savefig(fd / "language_flows_heatmap.png", dpi=200); plt.close(fig)
507:     # 5. inference accuracy
512:         ax.bar(range(len(a)), a.accuracy, color="#5B8DD9")
513:         for x, (v, n) in enumerate(zip(a.accuracy, a.held_out_channels)):
515:         ax.axhline(float(acc.baseline_majority_language.iloc[0]), color="#E8A33D", linestyle="--",
518:         ax.set_ylim(0, 1.15); ax.set_xlabel("Share of neighbour votes won by the winning language")
519:         ax.set_ylabel("Accuracy on hidden known channels")
521:         fig.tight_layout(); fig.savefig(fd / "language_inference_accuracy.png", dpi=200); plt.close(fig)
539:         _grid(ax); fig.tight_layout(); fig.savefig(fd / "language_yearly_homophily.png", dpi=200); plt.close(fig)
547:         _grid(ax); fig.tight_layout(); fig.savefig(fd / "language_yearly_diversity.png", dpi=200); plt.close(fig)
558:         _grid(ax); fig.tight_layout(); fig.savefig(fd / "language_yearly_shares.png", dpi=200); plt.close(fig)
567:         _grid(ax); fig.tight_layout(); fig.savefig(fd / "language_yearly_cohesion.png", dpi=200); plt.close(fig)
579:             ax.set_xlabel("Forwards across a language boundary"); ax.set_title(title, fontsize=10)
580:             ax.grid(True, axis="x", linestyle="--", linewidth=0.8, color="#d9d9d9"); ax.set_axisbelow(True)
582:         fig.tight_layout(); fig.savefig(fd / "language_bridges.png", dpi=200); plt.close(fig)
593:         ax.set_yscale("log"); ax.set_xticks(x); ax.set_xticklabels(a.language_name, rotation=45, ha="right")
596:         ax.legend(frameon=False); _grid(ax); fig.tight_layout(); fig.savefig(fd / "language_activity.png", dpi=200); plt.close(fig)
608:         "| language_inference_accuracy.png | accuracy of the neighbour-vote language guess on hidden known channels |\n"
```


### bigdata_pipeline/analysis/source_tracing.py

```
56: SHIFT = 32
57: MASK = (1 << SHIFT) - 1
58: SH, MASK_U = np.uint64(SHIFT), np.uint64(MASK)
71:     return (key & MASK_U).astype(np.int64)
173:     if max(r["oc"].max(), r["dc"].max()) > MASK or max(r["op"].max(), r["dm"].max()) > MASK or min(r["oc"].min(), r["dc"].min()) < 0:
185:     """Yield batches of the cleaned messages: dest_channel, msg_id, ts, and one boolean mask per traceability level."""
190:         def mask(b, value):
193:             ch = mask(b, "channel")
198:                     "user": mask(b, "user"), "hidden": mask(b, "hidden")})
262:     by_year = yd.groupby("year").agg(relays=("delay", "size"), median_delay_s=("delay", "median"),
292:             "median_relays_per_post": float(np.median(cnt)), "max_relays_per_post": int(cnt.max()),
294:             "median_first_relay_delay_s": float(np.median(first_delay)),
308:     near = found & (np.abs(found_ts - o_ts) <= 60)
338:     ax.grid(True, axis=axis, linestyle="--", linewidth=0.8, color="#d9d9d9")
354:     ax.set_xticks(range(len(s))); ax.set_xticklabels(s.size_class, rotation=30, ha="right")
357:     fig.tight_layout(); fig.savefig(fd / "chain_size_distribution.png", dpi=200); plt.close(fig)
364:     ax.set_xticks(x); ax.set_xticklabels(d.delay_class, rotation=30, ha="right")
367:     fig.tight_layout(); fig.savefig(fd / "delay_distribution.png", dpi=200); plt.close(fig)
376:         fig.tight_layout(); fig.savefig(fd / "delay_by_year.png", dpi=200); plt.close(fig)
385:     fig.tight_layout(); fig.savefig(fd / "source_concentration.png", dpi=200); plt.close(fig)
397:     fig.tight_layout(); fig.savefig(fd / "top_sources.png", dpi=200); plt.close(fig)
411:         fig.tight_layout(); fig.savefig(fd / "traceability_levels.png", dpi=200, bbox_inches="tight"); plt.close(fig)
419:         ax.set_xticks(range(len(a))); ax.set_xticklabels([m.replace("_", " ") for m in a.measure], rotation=20, ha="right")
422:         fig.tight_layout(); fig.savefig(fd / "source_verification.png", dpi=200); plt.close(fig)
460:     L.append(f"- Relays per post: mean {summ['mean_relays_per_post']}, median {summ['median_relays_per_post']:g}, maximum "
461:              f"{summ['max_relays_per_post']:,}; {summ['posts_with_one_relay_share'] * 100:.1f}% of posts have a single relay.")
462:     L.append(f"- Median delay of the first relay: {summ['median_first_relay_delay_s']:g} s; "
511:             {"year": "year of the relay", "relays": "relays", "median_delay_s": "median delay in seconds",
560: def synthetic(root, seed=0):
561:     rng = np.random.default_rng(seed)
619:     assert r["duplicates"] == 40, r["duplicates"]
622:     assert s["origin_channels"] <= 52
648:                                    figdir=str(t / f"fig_{tag}"), top=20, no_charts=False)
667:     ap.add_argument("--top", type=int, default=50, help="source channels listed in top_sources")
```


### bigdata_pipeline/analysis/geo_cities_th4-2stp.py

```
10:               have (weighted vote on the forward graph, restricted to the countries of its
11:               language when known). Accuracy is measured by hiding known cities (holdout).
17:   channel_city_inferred/      neighbour-vote cities with their vote share
18:   propagation_accuracy/       holdout accuracy of the neighbour vote, by vote share
29: The neighbour vote needs community_detection_v2.py in the same folder (it reuses its edge reader).
435:     """channel id -> language inferred by the theme 2 neighbour vote (channel_language_inferred.csv)."""
442: def load_votes(path: str | None, min_share: float = 0.2, min_forwards: int = 3) -> dict[int, list[tuple[str, float]]]:
443:     """channel id -> candidate languages [(language, share)], best first (channel_language_votes.csv).
445:     Keeps the languages whose vote share is at least `min_share` (the best one is always kept) and drops
446:     channels backed by fewer than `min_forwards` forwards, which say too little.
451:     df = df[df.neighbour_forwards >= min_forwards]
455:         keep = [(str(l).lower(), sh) for i, (l, sh) in enumerate(cands) if l and (i == 0 or sh >= min_share)]
582: def circ_dist(a, b, period=24.0):
588: def load_temporal(path: str, min_posts: int = 100):
593:     ok = ids.notna().to_numpy() & (vals.sum(axis=1) >= min_posts)
605: def timezone_check(single: pd.DataFrame, tids: np.ndarray, P: np.ndarray, min_channels: int = 30):
619:         if np.isnan(off) or len(idx) < min_channels:
628:         return t, "inconclusive", {"reason": "need cities with offsets at least 2 h apart (>= min_channels channels each)"}
646:     elif sd_loc <= 1.5 and sd_utc >= 2 * sd_loc and abs(slope) <= 0.4:
653: def estimate_offsets(single: pd.DataFrame, tids: np.ndarray, P: np.ndarray, seed: int = 42):
686:     rng = np.random.default_rng(seed)
704:                   inferred: dict[int, str] | None = None, votes: dict | None = None):
708:     is found) the language the title is written in. Channels that only have a vote table entry are held back
711:     inferred, votes = inferred or {}, votes or {}
724:         elif cid in votes:
764: def resolve_votes(held: dict[int, dict], votes: dict, matcher: Matcher, tz=None, tz_tol: float = 2.0,
765:                   min_tz_score: float = 0.3):
766:     """Choose the language of channels that only have a vote table entry, then search their cities.
768:     Every candidate language (best vote first) is searched. If several give a city, the timezone keeps
770:     best-voted language wins. Without a timezone the best-voted language that finds a city wins. A channel
771:     with no city still gets a language (for the neighbour vote): the best-voted one whose country has
778:         cands = votes[cid]
782:         use_tz = est is not None and est[1] >= min_tz_score
809:                 rows_out.append({"channel_id": cid, "language": chosen, "language_source": "votes",
812:             info[cid] = (chosen, "votes")
813:             stats["direct_votes"] += 1
816:                 stats["votes_language_by_timezone"] += 1
818:         # no usable city: still choose a language for the neighbour vote
824:                 stats["votes_language_by_timezone"] += 1
825:         info[cid] = (pick, "votes")
826:     stats["votes_channels"] = len(held)
830: # ----------------------------------------------------------------- neighbour vote
832:               min_class: int = 30, min_vote: float = 0.6, holdout: float = 0.1, seed: int = 42,
833:               tz: dict[int, tuple[float, float]] | None = None, tz_tol: float = 2.0, min_tz_score: float = 0.3):
837:     The vote is restricted to the countries of the channel's language when it has a gazetteer entry.
839:     enough (score >= min_tz_score) can only receive a city whose UTC offset is within `tz_tol` hours.
840:     Returns (accuracy table, inferred table).
849:     classes = [k for k, v in cnt.items() if v >= min_class]
865:     def predict(known_mask, rows):
866:         """(predicted class, vote share, total vote) for `rows`, chunked to bound memory."""
867:         kr = np.where(known_mask & (cls >= 0))[0]
874:                 mask = allowed.get(lang_of.get(int(nodes[i]), ""), None)
875:                 if mask is not None and mask.any():
876:                     V[j] = V[j] * mask
877:                 if tz is not None and int(nodes[i]) in tz and tz[int(nodes[i])][1] >= min_tz_score:
889:     rng = np.random.default_rng(seed)
891:     hold = rng.choice(kidx, size=max(1, int(len(kidx) * holdout)), replace=False)
892:     mask = known.copy()
893:     mask[hold] = False
894:     P, S, T = predict(mask, hold)
896:     base = float((cls[hold] == np.bincount(cls[mask]).argmax()).mean()) if mask.any() else float("nan")
902:                      "accuracy": round(float(ok[m].mean()), 4) if m.any() else np.nan})
903:     sel = has & (S >= min_vote)
904:     rows.append({"row": f">= {min_vote} (rule used)", "held_out_channels": int(sel.sum()),
905:                  "accuracy": round(float(ok[sel].mean()), 4) if sel.any() else np.nan})
907:     acc["baseline_majority_city"] = round(base, 4)
913:     keep = (T2 > 0) & (S2 >= min_vote)
916:                         "vote_share": S2[keep].round(4), "neighbour_forwards": T2[keep].astype(int)})
921: def build_tables(cc, info, inferred, n_lang, n_city, matcher, seed=42, tz=None):
932:                               evidence="neighbour vote", matched_text="", n_cities=1, method="neighbours", language_basis="",
```


### bigdata_pipeline/analysis/anomaly_peaks_th4-4stp.py

```
8:   2. Anomaly score per city and day: log1p(count) minus its weekday effect, compared with the median of
9:      the previous `--window` days, divided by a robust spread (1.4826 * MAD of the previous deviations, with
16:      (b) lagged correlation of the positive anomaly scores between the busiest cities.
35: SIGMA_FLOOR = 0.15          # minimum spread on the log scale (about 16 % of day-to-day change)
58: def daily_matrix(df: pd.DataFrame, metric: str = "n_posts", min_days: int = 90, min_total: int = 500) -> pd.DataFrame:
62:     keep = ((m > 0).sum() >= min_days) & (m.sum() >= min_total)
67: def anomaly_scores(m: pd.DataFrame, window: int = 56, min_periods: int = 28):
68:     """Robust score per city and day, plus the expected (baseline) count. Both are days x cities."""
70:     weekday = y.groupby(y.index.dayofweek).transform("median") - y.median()
72:     base = y.shift(1).rolling(window, min_periods=min_periods).median()
74:     sigma = (1.4826 * dev.shift(1).rolling(window, min_periods=min_periods).median()).clip(lower=SIGMA_FLOOR)
80: def anomaly_mask(m: pd.DataFrame, z: pd.DataFrame, z_thr: float = 4.0, min_count: float = 20.0) -> pd.DataFrame:
81:     return (z >= z_thr) & (m >= min_count)
89: def episodes(m: pd.DataFrame, z: pd.DataFrame, expected: pd.DataFrame, mask: pd.DataFrame, gap: int = 1) -> pd.DataFrame:
93:         days = np.flatnonzero(mask[city].to_numpy())
107:                 "peak_ratio": round(float(cnt[k]) / max(peak_exp, 1.0), 2), "max_score": round(float(zz[k]), 2),
111:             "max_score", "excess_posts", "shape"]
116: def synchronized_peaks(mask: pd.DataFrame, eps: pd.DataFrame, min_cities: int = 3, gap: int = 1,
117:                global_share: float = 0.5) -> pd.DataFrame:
119:     n = mask.sum(axis=1).to_numpy()
120:     days = np.flatnonzero(n >= min_cities)
121:     cols = ["sync_id", "start", "end", "n_days", "n_cities", "max_share_of_cities", "global", "lead_city",
128:         start, end = mask.index[grp[0]], mask.index[grp[-1]]
129:         sub = mask.iloc[grp[0]:grp[-1] + 1]
133:         score = e.groupby("city_key").max_score.max()
144:             "n_cities": len(active), "max_share_of_cities": round(float(n[grp].max() / mask.shape[1]), 3),
145:             "global": bool(n[grp].max() / mask.shape[1] > global_share), "lead_city": lead, "n_lead_ties": n_ties, "lead_lag_days": lag,
178: def onset_hour(s: pd.Series, start: pd.Timestamp, end: pd.Timestamp, k: float = 3.0, min_extra: float = 5.0,
180:     """First hour of the synchronized peak window where the city is above its usual level for two hours in a row.
181:     The usual level of an hour is the median of the same weekday and hour in the 4 previous weeks.
183:     base = pd.concat([s.shift(24 * 7 * j) for j in range(1, 5)], axis=1).median(axis=1)
184:     thr = np.maximum(k * base, base + min_extra)
186:     hi = min(end, start + pd.Timedelta(days=after_days)) + pd.Timedelta(hours=23)
193: def sync_onsets(sync: pd.DataFrame, hdf: pd.DataFrame, k: float = 3.0, min_extra: float = 5.0) -> pd.DataFrame:
206:                 t = onset_hour(H[c], e.start, e.end, k, min_extra)
233: def lagged_correlation(z: pd.DataFrame, top: int = 40, max_lag: int = 3, min_corr: float = 0.2) -> pd.DataFrame:
234:     """Correlation of the positive anomaly scores between the `top` busiest cities, for lags -max_lag..max_lag.
245:             for lag in range(-max_lag, max_lag + 1):
251:             if best >= min_corr:
265: def charts(figdir: Path, m: pd.DataFrame, mask: pd.DataFrame, sync: pd.DataFrame, eps: pd.DataFrame) -> None:
272:     ax.plot(mask.index, mask.sum(axis=1), color="#1f77b4", linewidth=0.8)
274:         ax.axvspan(e.start, e.end + pd.Timedelta(days=1), color="#d62728" if e["global"] else "#ff7f0e", alpha=0.25)
278:     fig.savefig(figdir / "cities_anomalous_per_day.png", dpi=140)
284:         ax.plot(m.index, m[c], color="#555555", linewidth=0.7)
285:         hit = mask[c]
286:         ax.scatter(m.index[hit], m[c][hit], color="#d62728", s=10, zorder=3)
290:     fig.savefig(figdir / "top_cities_series.png", dpi=140)
296:         t.plot.bar(stacked=True, ax=ax, width=0.9)
298:         ax.set_xticklabels([d.strftime("%Y-%m") for d in t.index[::max(1, len(t) // 12)]], rotation=45, ha="right")
301:         fig.savefig(figdir / "episodes_per_month.png", dpi=140)
307:     m = daily_matrix(df, args.metric, args.min_days, args.min_total)
310:     z, expected = anomaly_scores(m, args.window)
311:     mask = anomaly_mask(m, z, args.z, args.min_count)
312:     eps = episodes(m, z, expected, mask, args.gap)
313:     ev = synchronized_peaks(mask, eps, args.min_cities, args.gap, args.global_share)
321:             # does the lead city survive a stricter and a looser onset threshold?
333:     corr = lagged_correlation(z[order], args.top_corr, args.max_lag)
336:         ("anomalous city-days", int(mask.values.sum())), ("episodes", len(eps)),
340:         (f"synchronized peaks (>= {args.min_cities} cities together)", len(ev)),
349:     res = {"onsets": onsets, "matrix": m, "z": z, "mask": mask, "episodes": eps, "sync": ev, "corr": corr, "summary": summary}
353:         charts(Path(args.figdir), m, mask, ev, eps)
370:     idx = pd.date_range("2022-01-01", periods=240, freq="D")
371:     hours = pd.date_range(idx[0], periods=240 * 24, freq="h")
375:         lam = 60 + 40 * i
379:             d0 = 149 if i == 0 else 150
380:             h[d0 * 24 + onset_hour_of[i]: (d0 + 1) * 24] *= 10
395:                               min_days=30, min_total=100, window=56, z=4.0, min_count=20, gap=1, min_cities=3,
396:                               global_share=0.5, top_corr=8, max_lag=3,
408:     assert on.loc["C0 (X)", "onset_utc"] == idx[149] + pd.Timedelta(hours=10)
409:     assert on.loc["C1 (X)", "hours_after_first"] == 28.0 and e.lead_gap_hours == 28.0 and e.onset_spread_hours == 30.0
```


### bigdata_pipeline/analysis/suspicious_trends_th5-1stp.py

```
10: Channel indicators (a flag is raised when the value passes the threshold; thresholds come from the
11: population quantile --q, with a floor so that a quantile of a quiet population cannot flag normal values):
16:   daily_burst    max_posts_day / median day     huge one-day burst compared with its usual day
19: Behaviour indicators 7-11 use fixed parameters (round numbers, not quantiles; not validated):
20:   pure_relay       >= 99 % of the messages are forwards, >= 1000 messages
21:   broad_instant    fast_relay AND >= 100 distinct sources (multi-source instant aggregator)
22:   steady_delay     IQR of the delay <= 10 s over >= 200 relays (needs delay_p25_s / delay_p75_s from job6)
23:   high_throughput  median >= 1000 messages per active day
24:   abrupt_volume    >= 10000 messages within <= 30 observed active days (observation window, not channel age)
26:   in_tight_group   member of a coordinated group with density >= 0.5 and >= 5 channels
28: mean percentile of the flagged quantile-based indicators.
87:     med = np.nanmedian(x)
88:     mad = np.nanmedian(np.abs(x - med))
89:     return (x - med) / (1.4826 * mad if mad > 0 else np.nan)
105: def flag_channels(beh, hours, stats, q=0.99, min_forwarded=30, min_posts_round=500, min_posts_sec=200,
106:                   min_day_burst=100, src_max=0.9, fast_floor=0.3, entropy_floor=0.97, sec_floor=0.1,
107:                   burst_floor=20.0, z_views=4.0, pure_share=0.99, pure_min_posts=1000, broad_origins=100,
108:                   steady_iqr=10.0, steady_min_relays=200, throughput=1000, abrupt_posts=10000, abrupt_days=30,
113:     d["burst_ratio"] = d["max_posts_day"] / d["median_posts_day"].clip(lower=1)
117:     def cut(col, mask, floor):
118:         """Boolean flag: above the population quantile (strictly, so that ties never flag everyone)
119:         and at least `floor`; a quantile below the floor falls back to the floor itself."""
120:         v = d.loc[mask, col].dropna()
121:         qv = float(v.quantile(q)) if len(v) else floor
123:         return mask & ((d[col] > qv) & (d[col] >= floor) if qv >= floor else (d[col] >= floor))
125:     el_f = d["n_forwarded"].fillna(0) >= min_forwarded
129:     el_r = d["n_posts"] >= min_posts_round
131:     el_s = d["n_posts"] >= min_posts_sec
133:     el_b = d["max_posts_day"] >= min_day_burst
143:     d["pure_relay"] = (d["n_posts"] >= pure_min_posts) & (d["share_forwarded"] >= pure_share)
145:     d["steady_delay"] = (d["n_forwarded"].fillna(0) >= steady_min_relays) & (d["delay_iqr_s"] <= steady_iqr)
146:     d["high_throughput"] = (col("median_posts_day") >= throughput) & (col("n_active_days") >= 3)
150:                 "median_posts_day": throughput, "n_posts_abrupt": abrupt_posts})
173:            "high_throughput": "median_posts_day", "abrupt_volume": "n_posts_abrupt"}
174:     out["threshold"] = [thr.get(key.get(k, ""), np.nan) for k in INDICATORS]
191: def split_groups(p, min_shared, min_size, max_size, factor=1.5):
192:     """Groups of channels linked by pairs with n_shared >= threshold. A component larger than max_size is
193:     chained together by a few very popular channels, not a real group: its threshold is raised (x factor)
194:     until it falls apart into components of at most max_size channels. Returns [(edges, threshold)]."""
195:     out, todo = [], [(p[p["n_shared"] >= min_shared], float(min_shared))]
202:             if n < min_size:
204:             if n <= max_size:
212: def coordinated_groups(pairs, min_shared=5, max_median_dt=60, min_size=3, max_size=300):
214:     p = pairs[(pairs["n_shared"] >= min_shared) & (pairs["median_dt_s"] <= max_median_dt)]
217:     parts = split_groups(p, min_shared, min_size, max_size)
225:                      "shared_max": int(g["n_shared"].max()), "median_dt_s": float(g["median_dt_s"].median()),
227:                      "min_shared_used": thr})
243: def monthly_trend(speed, casc, min_forwards=100):
245:     s = s[s["n_forwards"] >= min_forwards]
249:         c = casc.assign(tight=(casc["n_first10min"] / casc["n_relays"]) >= 0.8).groupby("month") \
270:     fig.savefig(figdir / "indicator_counts.png", dpi=150)
281:     fig.savefig(figdir / "score_distribution.png", dpi=150)
287:     ax.scatter(x[ok], y[ok], s=4, alpha=0.25, color="#888888", label="all")
289:     ax.scatter(x[hi], y[hi], s=14, color="#C0392B", label="2+ flags")
295:     fig.savefig(figdir / "fast_vs_source.png", dpi=150)
307:         fig.savefig(figdir / "fast_share_monthly.png", dpi=150)
312:             ax.bar(pd.to_datetime(t["month"] + "-01"), t["n_cascades"], width=25, color="#BBBBBB", label="cascades >= 10 relays")
313:             ax.bar(pd.to_datetime(t["month"] + "-01"), t["n_tight"], width=25, color="#C0392B", label="80%+ of relays in first 10 min")
317:             fig.savefig(figdir / "cascades_monthly.png", dpi=150)
329:         fig.savefig(figdir / "coordinated_groups.png", dpi=150)
340:     grp, members = (coordinated_groups(pairs, a.min_shared, a.max_median_dt, a.min_group, a.max_group)
346:     d, thr = flag_channels(beh, hours, stats, q=a.q, min_forwarded=a.min_forwarded, src_max=a.src_max,
347:                            z_views=a.z_views, min_day_burst=a.min_day_burst, pure_share=a.pure_share,
348:                            pure_min_posts=a.pure_min_posts, broad_origins=a.broad_origins, steady_iqr=a.steady_iqr,
349:                            steady_min_relays=a.steady_min_relays, throughput=a.throughput, abrupt_posts=a.abrupt_posts,
356:                         "sec_mode_share", "max_posts_day", "median_posts_day", "n_active_days", "burst_ratio", "views_z"] if c in d]
370:             ("coordinated pairs kept", 0 if pairs is None else int(((pairs["n_shared"] >= a.min_shared) & (pairs["median_dt_s"] <= a.max_median_dt)).sum())),
397:     n = 3000
399:                         "views_mean": rng.lognormal(6, 1, n), "max_posts_day": rng.integers(5, 40, n),
400:                         "median_posts_day": rng.integers(2, 10, n), "n_forwarded": rng.integers(0, 400, n),
```


### bigdata_pipeline/analysis/fast_mirror_channels_th5-2stp.py

```
71:     q = c.groupby("dest_channel")["delay_s"].quantile([0.25, 0.5, 0.75]).unstack()
72:     q.columns = ["delay_p25_s", "delay_median_s", "delay_p75_s"]
74:     q["share_from_source_within10s"] = c.assign(f=c["delay_s"] <= 10).groupby("dest_channel")["f"].mean()
93:             size //= 10
155: def classify(d, words, max_delay, max_iqr, instant_delay, min_sim=0.5):
159:       discussion_possible  same lag signature (<= max_delay s, IQR <= max_iqr s) without word or similar title
160:       instant_relay        median delay <= instant_delay s (same second): alert/news relays and cross-posting tools
168:     similar = sim >= min_sim
169:     steady = (d["delay_median_s"] <= max_delay) & (d["delay_iqr_s"] <= max_iqr)
170:     kind = np.select([(has_word | similar) & steady & (d["delay_median_s"] > instant_delay),
171:                       steady & (d["delay_median_s"] > instant_delay), d["delay_median_s"] <= instant_delay],
177: def families(d, min_members):
180:               delay_median_s=("delay_median_s", "median"), delay_iqr_median_s=("delay_iqr_s", "median"),
183:     f = f[f["n_followers"] >= min_members].sort_values(["n_followers", "relays_total"], ascending=False).reset_index(drop=True)
195:     ax.hist(d["delay_median_s"].clip(upper=120), bins=40, color="#1F4E79")
196:     ax.set(xlabel="median delay to the top source, s (capped at 120)", ylabel="channels",
199:     fig.savefig(figdir / "mirror_delay.png", dpi=150)
205:         for i, (n, m) in enumerate(zip(g["n_followers"][::-1], g["delay_median_s"][::-1])):
206:             ax.text(n, i, f" {n} channels, median {m:.0f}s", va="center", fontsize=8)
210:         fig.savefig(figdir / "mirror_families.png", dpi=150)
218:     sel = beh[(beh["share_fast10"] >= a.fast_min) & (beh["top_origin_share"] >= a.src_min) & (beh["n_forwarded"] >= a.min_forwarded)]
219:     print(f"selected channels: {len(sel):,} of {len(beh):,} (fast >= {a.fast_min}, one source >= {a.src_min}, >= {a.min_forwarded} forwards)")
230:     d["kind"], d["discussion_reason"], d["title_similarity"] = classify(d, a.discussion_words, a.disc_max_delay, a.regular_iqr, a.instant_delay, a.title_sim)
231:     fam = families(d, a.min_members)
242:         (f"families with >= {a.min_members} followers", len(fam)),
244:         ("median delay to source (s)", float(d["delay_median_s"].median())),
255:     show = ["family_rank", "top_source", "n_followers", "relays_total", "delay_median_s", "delay_iqr_median_s", "first_month", "last_month"]
257:     cols = [c for c in ["channel_id", "title", "source_title", "kind", "delay_median_s", "delay_iqr_s", "n_relays", "first_month", "last_month"] if c in review]
276:     beh["n_posts"], beh["n_forwarded"], beh["sec_mode_share"] = 100, 60, 0.02
279:     a = argparse.Namespace(fast_min=0.44, src_min=0.9, min_forwarded=30)
284:     assert (prof[prof.channel_id <= 8].delay_iqr_s <= 1).all() and prof[prof.channel_id <= 8].delay_median_s.between(3, 4).all()
288:     assert len(f) == 1 and f.loc[0, "top_source"] == 900 and f.loc[0, "n_followers"] == 8, f
289:     assert prof.first_month.eq("2024-03").sum() == 8 and prof.loc[prof.channel_id == 20, "first_month"].iloc[0] == "2023-01"
292:                       "delay_median_s": [3, 3, 0, 3, 8, 3, 3, 0], "delay_iqr_s": [0, 0, 1, 0, 1, 40, 1, 1]})
310:     ap.add_argument("--fast-min", type=float, default=0.44, help="min share of forwards relayed within 10 s")
311:     ap.add_argument("--src-min", type=float, default=0.9, help="min share of forwards from the single top source")
312:     ap.add_argument("--min-forwarded", type=int, default=30)
316:     ap.add_argument("--disc-max-delay", type=float, default=5.0, help="max median delay (s) of a linked discussion group")
317:     ap.add_argument("--title-sim", type=float, default=0.5, help="min word overlap between title and source title to call a channel a discussion group")
318:     ap.add_argument("--instant-delay", type=float, default=1.0, help="median delay (s) at or under which a relay is called instant (same second)")
```


### bigdata_pipeline/analysis/fast_trend_excluding_th5-3stp.py

```
11: Reads gold/chains in batches (columns dest_channel, delay_s, date), so memory stays small.
45:         f10, f60 = d["delay_s"] <= 10, d["delay_s"] <= 60
75:     fig.savefig(Path(figdir) / "fast_trend_excluding.png", dpi=150)
```


### bigdata_pipeline/analysis/fast_month_drivers_th5-4stp.py

```
6:   * how concentrated the fast relays (<= 10 s after the original post) are: share of the top 1, 10, 50, 100
32:     return f"{y + (mo == 12)}-{(mo % 12) + 1:02d}"
130:         fig.savefig(a.figdir / "month_drivers_concentration.png", dpi=150)
151:     assert pm.loc[900, "n_fast"] == 4000 and pm.loc[900, "top_source"] == 8000 and 900 not in pr.index
164:     ap.add_argument("--fast", type=int, default=10, help="seconds after the original post")
165:     ap.add_argument("--top", type=int, default=500)
```


### bigdata_pipeline/analysis/review_candidates.py

```
30: def select(sus, min_behaviour):
32:     a = sus["score_behaviour"] >= min_behaviour
43:     g = groups[["group_rank", "n_channels", "density", "median_dt_s"]].rename(
44:         columns={"n_channels": "group_size", "density": "group_density", "median_dt_s": "group_median_dt_s"})
55:     d = select(sus, a.min_behaviour)
58:           f"({int((d['selection'] != 'group+behaviour').sum())} with {a.min_behaviour}+ behaviour indicators, "
80:             "delay_p25_s", "delay_median_s", "delay_p75_s", "first_month", "last_month", "n_active_months",
81:             "group_rank", "group_size", "group_density", "group_median_dt_s", "community", "language", "city_key",
99:                         "delay_median_s", "group_rank"] if c in d]
112:     grp = pd.DataFrame({"group_rank": [1, 2], "n_channels": [10, 5], "density": [0.9, 0.6], "median_dt_s": [1, 2]})
```
