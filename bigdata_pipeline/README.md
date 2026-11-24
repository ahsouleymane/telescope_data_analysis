# TeleScope - Big Data pipeline (v2, PySpark)

Message-level processing of the TeleScope Telegram dataset (about 345 GB of JSONL
for the 15 batches extracted so far, about 120 M messages in total). The pre-aggregated
channel graph of the dataset is in `telescope_files/`; this pipeline rebuilds the same
information from the messages, with dates and weights, then runs the five analysis themes on it.

The raw data stays where it is, read-only. Only reduced tables are written to the
internal disk. Spark runs in LOCAL mode (one JVM, no cluster).

## Contents

1. [Overview](#overview)
2. [Prerequisites by operating system](#prerequisites-by-operating-system)
3. [Environment (Docker)](#environment-docker)
4. [Run everything: one command per step](#run-everything-one-command-per-step)
5. [Spark pipeline (jobs 1-6)](#spark-pipeline-jobs-1-6)
6. [Analyses by theme](#analyses-by-theme)
7. [Report application (Streamlit)](#report-application-streamlit)
8. [Orchestration (Airflow)](#orchestration-airflow)
9. [Check that results are reproducible](#check-that-results-are-reproducible)
10. [Install without Docker](#install-without-docker)
11. [Things to know](#things-to-know)

## Overview

```
raw JSONL / ZIP (external disk, read-only)
   |  job 1  CLEAN        job1_clean.py      typed Parquet, one folder per batch
   |  job 1b DEDUP        job1b_dedup.py     removes duplicated messages
   v
telescope_pipeline_files/clean/  clean_dedup/
   |  job 2  CHAINS       job2_chains.py     |  job 3  EDGES   job3_edges.py     |  job 4  STATS   job4_stats.py
   v
telescope_pipeline_files/gold/                (chains, edges_monthly, channel_stats ...)
   |  analyses (igraph, pandas), one script per step, in order:
   |  theme 1 communities -> theme 2 languages -> theme 3 source tracing
   |  -> theme 4 (th4-1 ... th4-5, with job 5 between th4-3 and th4-4)
   |  -> job 6, then theme 5 (th5-1 ... th5-4, then the review list)
   v
bigdata_pipeline/analysis/<theme folders>/    figures in analysis/figures/
   |
   v
Streamlit report (analysis/app/)
```

Layout of the repository:

| Folder | Content |
|---|---|
| `bigdata_pipeline/spark/` | jobs 1 to 6, `run_pipeline.sh` (jobs 1-4), Spark session settings, input reader |
| `bigdata_pipeline/analysis/` | analysis scripts, their results (CSV folders) and the Streamlit application |
| `bigdata_pipeline/tests/` | unit tests, Spark check, `results_digest.py` (reproducibility) |
| `bigdata_pipeline/airflow/dags/` | the Airflow DAG (optional) |
| `telescope_files/` | pre-aggregated files of the dataset (inputs of the analyses) |
| `telescope_pipeline_files/` | pipeline outputs: `clean/`, `clean_dedup/`, `gold/` (not versioned) |
| root | `Dockerfile`, `docker-compose.yml`, `Makefile`, `requirements.txt`, `requirements.lock`, `.env.example` |

## Prerequisites by operating system

You need either Docker (recommended: same environment everywhere) or Java 17 + Python 3.13 installed by hand.
The commands `make` and `bash` are used everywhere, so on Windows work inside WSL2.

### With Docker (recommended)

| System | Install |
|---|---|
| Debian 12/13 | official repository, see below |
| Ubuntu 22.04 / 24.04 | same as Debian with `ubuntu` instead of `debian` in the repository line, or `sudo apt install docker.io docker-compose-v2` |
| Fedora / RHEL | `sudo dnf install docker docker-compose-plugin` (or the official repository), then `sudo systemctl enable --now docker` |
| Arch | `sudo pacman -S docker docker-compose`, then `sudo systemctl enable --now docker` |
| macOS (Intel or Apple Silicon) | install Docker Desktop (or `brew install --cask docker`), start it once. Give it at least 6 GB of RAM in its settings. On Apple Silicon the image is built for arm64: results can differ in the last decimals from an amd64 machine |
| Windows 10/11 | install WSL2 (`wsl --install` in PowerShell) and Docker Desktop with the WSL2 backend, then work in the Ubuntu terminal and keep the project inside the WSL filesystem (`~/...`), not on `C:\`: it is much faster |

Debian / Ubuntu, official Docker repository (for Ubuntu replace `debian` by `ubuntu` in both places):

```bash
sudo apt update && sudo apt install -y ca-certificates curl make
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/debian/gpg -o /etc/apt/keyrings/docker.asc
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/debian $(. /etc/os-release && echo $VERSION_CODENAME) stable" | sudo tee /etc/apt/sources.list.d/docker.list
sudo apt update && sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

On Linux, then allow your user to use Docker (log out and in afterwards, or run `newgrp docker`):

```bash
sudo usermod -aG docker $USER
docker run --rm hello-world && docker compose version
```

Common errors: `'compose' is not a docker command` = the compose plugin is missing;
`permission denied ... docker.sock` = your session is not yet in the `docker` group.

### Without Docker

Needed: Java 17 or newer (for PySpark), Python 3.11 to 3.13, `make`, and the libraries of `requirements.lock`.

| System | Java 17, Python, make |
|---|---|
| Debian / Ubuntu | `sudo apt install openjdk-17-jre-headless python3 python3-venv python3-pip make` |
| Fedora / RHEL | `sudo dnf install java-17-openjdk-headless python3 python3-pip make` |
| Arch | `sudo pacman -S jre17-openjdk python python-pip make` |
| macOS | `brew install openjdk@17 python make` (then follow the `brew` message to link Java, and use `gmake` for `make`) |
| Windows | use WSL2 (Ubuntu) and the Debian / Ubuntu line |

Then, in the project folder (same on every system):

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.lock        # or requirements.txt if you have not frozen the versions yet
java -version && python3 -c "import pyspark, igraph; print(pyspark.__version__)"
```

`python-igraph` ships binary wheels for Linux, macOS and Windows; if `pip` tries to compile it, upgrade pip first (`pip install -U pip`).
The `Makefile` runs its steps inside Docker. Without Docker, run the scripts of the table "Run everything" directly with `python3` and the paths shown at the top of the `Makefile`.

## Environment (Docker)

The image holds Python 3.13, Java 17 (needed by PySpark) and all the libraries. The code, the
data and the results stay on your machine (mounted folders), and the files written belong to
your user, not to root. The results are never stored in the image: everything is recomputed from the raw data.

Once:

```bash
# Docker installed (see "Prerequisites by operating system")
cp .env.example .env                                             # edit RAW_DIR and SPARK_TMP
mkdir -p "$(grep SPARK_TMP .env | cut -d= -f2)"
make build
```

Settings in `.env`:

| Variable | Meaning |
|---|---|
| `RAW_DIR` | folder of the raw messages (JSONL files or ZIP archives), mounted read-only on `/raw` |
| `SPARK_TMP` | Spark shuffle / spill folder: internal disk, a few tens of GB free |
| `TELESCOPE_CORES`, `TELESCOPE_SPARK_MEMORY` | resources given to Spark (default 3 cores, 4 GB) |
| `PYTHON_VERSION` | Python of the image (3.13) |

Check the environment before any computation:

```bash
make shell                  # a shell inside the container
java -version; python3 --version; ls /raw | head; ls bigdata_pipeline; exit
make test                   # unit tests of the cleaning step
make selftest               # selftest of each analysis script
make lock                   # freeze exact versions into requirements.lock, then: make build
make versions               # ENVIRONMENT.txt: python, java and library versions
```

Commit `requirements.lock`: with it, `make build` installs the same versions on any machine.

To move the image to another machine without Internet:
`docker save telescope:v2 | gzip > telescope_v2.tar.gz`, then `gunzip -c telescope_v2.tar.gz | docker load`.
The project folder and the data must be copied too. If the user id differs, run `make build` there.

## Run everything: one command per step

`make help` lists all commands. Steps must run in this order (each one needs the outputs of the previous ones):

| Order | Command | Script | Output |
|---|---|---|---|
| 1 | `make pipeline` | `spark/run_pipeline.sh` (jobs 1, 1b, 2, 3, 4) from the raw data | `telescope_pipeline_files/{clean,clean_dedup,gold}` |
| 1' | `make from-clean` | jobs 1b, 2, 3, 4 | same outputs, starting from `clean/` (no raw data needed) |
| 2 | `make theme1` | `community_detection_v2.py` | `analysis/communities_v2/` |
| 3 | `make theme2` | `language_analysis_v2.py` | `analysis/language_v2/` |
| 4 | `make theme3` | `source_tracing.py` | `analysis/tracing/` |
| 5 | `make th4-1` | `inspect_metadata_th4-1stp.py` | metadata inspection |
| 6 | `make th4-2` | `geo_cities_th4-2stp.py` | `analysis/geo_cities/` |
| 7 | `make th4-3` | `profiles_diagnostic_th4-3stp.py` | profile diagnostic |
| 8 | `make job5` | `spark/job5_city_daily.py` | `gold/city_daily`, `gold/city_hourly` (needs th4-2) |
| 9 | `make th4-4` | `anomaly_peaks_th4-4stp.py` | `analysis/anomalies/` (needs job 5) |
| 10 | `make th4-5` | `anomaly_maps_th4-5stp.py` | interactive maps (HTML) |
| 11 | `make job6` | `spark/job6_suspicious.py` | per-channel indicator tables in `gold/` |
| 12 | `make th5-1` | `suspicious_trends_th5-1stp.py` | `analysis/suspicious/` (needs job 6) |
| 13 | `make th5-2` | `fast_mirror_channels_th5-2stp.py` | instant-relay channels |
| 14 | `make th5-3` | `fast_trend_excluding_th5-3stp.py` | trend without these channels |
| 15 | `make th5-4` | `fast_month_drivers_th5-4stp.py` | drivers of the peak months |
| 16 | `make th5-5` | `review_candidates.py` | `analysis/suspicious/review/` |

The suffix of a script name gives its place: `th4` = theme 4, `th5` = theme 5, `3stp` = step 3.

Shortcuts: `make theme4` runs steps 5 to 10 in order, `make theme5` runs steps 11 to 16,
`make all` runs the whole project from the raw data, and `make all-from-clean` from the cleaned data (several hours).

## Spark pipeline (jobs 1-6)

| Job | What it computes | Output columns / tables |
|---|---|---|
| 1 clean | one typed row per message (9 columns, see `clean_records.py`) | dest_channel, msg_id, ts, views, forwards, kind, origin_channel, origin_post, origin_ts |
| 1b dedup | removes duplicated messages, writes `dedup_report.csv` | `clean_dedup/` |
| 2 chains | all relays of each original message, ordered by time | origin_channel, origin_post, origin_date, rank, dest_channel, dest_msg, date, delay_s, n_relays |
| 3 edges | monthly weighted edges A -> B (B forwarded A's messages) | origin_channel, dest_channel, month, n_forwards |
| 4 stats | activity of each channel | channel_id, n_messages, n_forwarded_in, n_forwarded_in_from_channels, total_views, total_forwards, first_date, last_date |
| 5 city_daily | activity per city and day (and hour), from the cities of `th4-2` | `gold/city_daily`, `gold/city_hourly` |
| 6 suspicious | per-channel behaviour tables used by theme 5 | `gold/channel_behavior`, `channel_hours`, `forward_speed_monthly`, `coordinated_pairs`, `cascades` |

Inputs: `--raw` accepts a `.zip`, a folder of `.zip`, a folder of `.jsonl`, or a mix. The `.jsonl`
files inside a zip are read straight from the archive, nothing is extracted. A batch is skipped when it is
already done with the same number of files (or use `--force`).

Without `make`, a trial on 50 files and the full run:

```bash
python3 bigdata_pipeline/spark/job1_clean.py --raw /path/to/raw --out telescope_pipeline_files --limit 50   # written to clean_trial/
bash bigdata_pipeline/spark/run_pipeline.sh /path/to/raw telescope_pipeline_files                         # jobs 1-4
```

Job 1 prints, for each batch, the messages kept and the read speed; `clean_log.csv` keeps one line per batch.

Machine settings (default: 3 cores, 8 GB RAM):

| Variable | Default | Meaning |
|---|---|---|
| `TELESCOPE_CORES` | 3 | cores used by Spark |
| `TELESCOPE_SPARK_MEMORY` | 4g | JVM memory (in local mode this is all of Spark's memory) |
| `TELESCOPE_SPARK_TMP` | `~/spark_tmp` (`/spark_tmp` in Docker) | shuffle/spill folder: internal disk, a few tens of GB free |
| `TELESCOPE_SHUFFLE_PARTITIONS` | 48 | raise it (96, 200) if a job runs out of memory in a shuffle |

Reading the results:

```python
import pandas as pd
edges = pd.read_parquet("telescope_pipeline_files/gold/edges_monthly")   # a folder of Parquet files
stats = pd.read_parquet("telescope_pipeline_files/gold/channel_stats")
```
`--csv` on jobs 3 and 4 also writes a single CSV (`gold/edges_monthly_csv/`, `gold/channel_stats_csv/`).

## Analyses by theme

Each analysis script writes one folder per table (`<table>/<table>.csv`), figures in `analysis/figures/`.
Every script has a `--selftest` (`make selftest` runs them all) and fixed random seeds.

| Theme | Question | Scripts | Main results |
|---|---|---|---|
| 1 | Communities of channels (Leiden, Infomap), their evolution | `community_detection_v2.py` | `communities_v2/` (partitions, profiles, flows, yearly, resolution curve, names) |
| 2 | Languages and their role in the communities (homophily, bridges, purity) | `language_analysis_v2.py` | `language_v2/` |
| 3 | Source tracing and traceability of forwards (levels A-D, delays, concentration) | `source_tracing.py` | `tracing/` (+ `tracing_protocol.md`) |
| 4 | Geography and synchronized anomalies between cities | `th4-1` to `th4-5`, job 5 | `geo_cities/`, `anomalies/`, maps in `figures/` |
| 5 | Broadcast and interaction data: atypical (suspicious) trends | job 6, `th5-1` to `th5-4`, `review_candidates.py` | `suspicious/` |

Theme 5 means atypical trends, not proof of malicious behaviour. Twelve indicators (eleven of behaviour,
one of coordination) are computed per channel with 99 % quantile thresholds. The suspicion level is
the number of indicators triggered: low = 1, medium = 2, high = 3 or more (a presentation choice, not
validated). Many flagged channels are linked discussion groups, automated feeds or aggregators, so
the list in `suspicious/review/` is a list to read by hand (columns `manual_label` and `note` are empty on purpose).

## Report application (Streamlit)

A general report that explains the whole work: figures and key numbers of each theme, the method and its formulas,
the limits, references, and a catalogue of every CSV and Parquet file with the reason it was produced.
All figures are read from the files, so it shows what the last run produced.

```bash
make app            # http://localhost:8501
```

Files of `app/`: `telescope_app.py` (pages), `telescope_captions.py` (texts computed from the tables),
`telescope_catalog.py` (descriptions, formulas, references). A file missing from the catalogue is shown as
"Description non renseignée": add it to `TABLE_INFO` or `PARQUET_INFO` in `telescope_catalog.py`.

## Orchestration (Airflow)

Optional. The DAG `telescope_full` (`bigdata_pipeline/airflow/dags/telescope_dag.py`) runs each `make` step above in the
`telescope:v2` image, one task at a time (a pool of one slot, so two Spark jobs never run together).

```bash
make airflow-build
make airflow-up        # http://localhost:8080, user admin
make airflow-run       # triggers the whole project
make airflow-down
```

## Check that results are reproducible

The reference is the CLEANED data (`telescope_pipeline_files/clean/`, a few GB), not the raw data (345 GB, job 1):
the same cleaned data is copied to each machine and everything after it is recomputed.
The image fixes the Python hash seed, the time zone (UTC), the number of cores and of shuffle partitions,
and `requirements.lock` fixes the library versions.

Run the same commands on each machine, with the same `telescope_pipeline_files/clean/` and `telescope_files/`.
`RUN_ID` is only a name for the fingerprint file (`digest_<RUN_ID>.tsv`): use `machine1` on the first machine and
`machine2` on the second. A fingerprint is saved after each stage, to see where a difference appears.

```bash
make digest-clean RUN_ID=machine1                     # fingerprint of the INPUT (cleaned data) -> digest_clean_machine1.tsv
make from-clean && make digest RUN_ID=machine1_gold   # jobs 1b, 2, 3, 4, then fingerprint of the tables
make theme1 theme2 theme3 && make digest RUN_ID=machine1_themes123
make theme4 && make digest RUN_ID=machine1_theme4
make theme5 && make digest RUN_ID=machine1_theme5
```
(`make all-from-clean` runs all the stages in one go, then one `make digest`: simpler, but the difference is not localised.)

Copy the `digest_*.tsv` files of one machine next to those of the other, then compare stage by stage:

```bash
make compare A=clean_machine1       B=clean_machine2        # same input data?
make compare A=machine1_gold        B=machine2_gold         # same gold tables?
make compare A=machine1_themes123   B=machine2_themes123
make compare A=machine1_theme4      B=machine2_theme4
make compare A=machine1_theme5      B=machine2_theme5
```

If the input fingerprints differ, the data copy is not the same and nothing after it can be compared.
The first stage that differs shows where to look. The last line of `make compare` gives the number of identical and different tables.

`results_digest.py` ignores the order of the rows and the names of the Spark `part-*` files, but it detects
any change of value, down to the last decimal. Images, logs and run reports are ignored.
Differences can still come from the order of floating-point sums in Spark or from ties in the deduplication.
Run the cleaning from the raw data (`make pipeline`) only to check job 1 itself.

## Install without Docker

See "Prerequisites by operating system" above. Checks once the libraries are installed:

```bash
python3 -m unittest bigdata_pipeline/tests/test_clean_records.py -v                  # no Spark needed
python3 bigdata_pipeline/tests/verify_spark.py /path/to/1961746451.jsonl             # runs jobs 1-4 on one channel
```
`verify_spark.py` ends with `ALL CHECKS PASSED`.

## Things to know

- Dates are stored as epoch seconds (UTC) in the clean data, and converted in Spark with the session time zone fixed to UTC.
- Service messages (joins, pins...) are skipped and counted in `clean_log.csv`.
- A forward whose origin is a user, or hidden by Telegram privacy, is kept (`kind` = `user` / `hidden`) but cannot become an edge or a chain.
- A forward from a channel without the original post id counts as an edge, but cannot be grouped into a chain (about 0.1 % in the sample channel).
- Telegram keeps the ORIGINAL author in every forward header, so intermediate hops are not stored: order and delay come from the dates.
- Spark has no zip reader, so job 1 hands the files to Spark tasks as a list and parses them with plain Python (`clean_records.py`); Spark builds the typed DataFrame and writes the Parquet. The other jobs are ordinary Spark DataFrame code.
- The message text is not part of the dataset.
- The dataset is licensed CC BY-NC-SA 4.0 (research use, cite DOI 10.7802/2825).