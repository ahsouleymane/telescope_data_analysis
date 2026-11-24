# TeleScope v2 - one command per step, all executed inside the Docker image (Java 17 + pinned libraries).
# Usage: make help
# Scripts are located with `find` so the Makefile works whatever the sub-folder layout of bigdata_pipeline/.

SHELL      := /bin/bash
export HOST_UID := $(shell id -u)
export HOST_GID := $(shell id -g)
RUN        ?= docker compose run --rm telescope   # emptied by Airflow: `make RUN= theme1` runs inside the container

GOLD       := telescope_pipeline_files/gold
OUT        := telescope_pipeline_files
AN         := bigdata_pipeline/analysis
FIG        := $(AN)/figures
META       := telescope_files/Source_Channel_Metadata.csv
LANGS      := telescope_files/Channel_Language.csv
GEO        := $(AN)/geo_cities
GEO_CSV    := $(GEO)/channel_geo/channel_geo.csv
MIRROR_MOD := fast_mirror_channels_th5-2stp   # module name (without .py) used by review_candidates.py

# path of a script by file name (first match in the project)
script = $(shell find bigdata_pipeline -name '$(1)' -not -path '*/__pycache__/*' | sort | head -1)
PY         := python3

.DEFAULT_GOAL := help
.PHONY: all help build shell lock versions test selftest pipeline job1 job2 job3 job4 job5 job6 \
        theme1 theme2 theme3 theme4 theme5 th4-1 th4-2 th4-3 th4-4 th4-5 th5-1 th5-2 th5-3 th5-4 th5-5 digest compare app clean-spark

help:  ## list the commands
	@grep -hE '^[a-zA-Z0-9_-]+:.*##' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  make %-14s %s\n", $$1, $$2}'

# ---------------------------------------------------------------- environment
build:  ## build the image (once, and after any change of requirements)
	@test -f .env || cp .env.example .env
	docker compose build

shell:  ## interactive shell in the environment
	$(RUN) bash

lock:  ## freeze the exact versions of the image into requirements.lock (then commit it, rebuild)
	$(RUN) bash -c "pip freeze --exclude-editable" > requirements.lock
	@echo "requirements.lock written: commit it, then run 'make build'"

versions:  ## write ENVIRONMENT.txt (python, java, spark, libraries) to attach to the report
	$(RUN) bash -c "{ python3 --version; java -version 2>&1 | head -1; cat /etc/pip-freeze.txt; } > ENVIRONMENT.txt"
	@echo "ENVIRONMENT.txt written"

test:  ## unit tests of the cleaning step
	$(RUN) bash -c "cd $$(dirname $$(find bigdata_pipeline -name test_clean_records.py | head -1))/.. && $(PY) -m unittest discover -s tests -v"

selftest:  ## selftest of every analysis script that has one
	@for s in community_detection_v2 source_tracing geo_cities anomaly_maps suspicious_trends review_candidates results_digest; do \
	  f=$$(find bigdata_pipeline -name "$$s*.py" | sort | head -1); echo "== $$s ($$f)"; $(RUN) $(PY) $$f --selftest || exit 1; done

# ---------------------------------------------------------------- Spark pipeline (raw -> clean -> gold)
pipeline:  ## jobs 1 to 4: raw (/raw) -> clean, clean_dedup, chains, edges, stats
	$(RUN) bash $(call script,run_pipeline.sh) /raw $(OUT)

job5:  ## city x day aggregation (needs `make geo` first)
	$(RUN) $(PY) $(call script,job5_city_daily*.py) --out $(OUT) --geo $(GEO_CSV) --csv

job6:  ## per-channel indicators for theme 5
	$(RUN) $(PY) $(call script,job6_suspicious*.py) --out $(OUT) --csv

# ---------------------------------------------------------------- analyses by theme
theme1:  ## communities (Leiden, Infomap, ...)
	$(RUN) $(PY) $(call script,community_detection_v2*.py) --gold $(GOLD) --out $(AN)/communities_v2 --figdir $(FIG)/community_detection --languages $(LANGS)

theme2:  ## languages
	$(RUN) $(PY) $(call script,language_analysis_v2*.py)

theme3:  ## source tracing
	$(RUN) $(PY) $(call script,source_tracing*.py) --chains $(GOLD)/chains --clean $(OUT)/clean_dedup --languages $(LANGS) --out $(AN)/tracing --figdir $(FIG)/traceability

# theme 4: steps th4-1 .. th4-5 (job5 sits between step 3 and step 4: it needs the cities of step 2)
th4-1:  ## theme 4, step 1: inspect the channel metadata
	$(RUN) $(PY) $(call script,inspect_metadata_th4-1stp.py)

th4-2:  ## theme 4, step 2: city of each channel
	$(RUN) $(PY) $(call script,geo_cities_th4-2stp.py) --metadata $(META) --languages $(LANGS) --gold $(GOLD) --out $(GEO) --figdir $(FIG)/geo_cities

th4-3:  ## theme 4, step 3: profile diagnostic
	$(RUN) $(PY) $(call script,profiles_diagnostic_th4-3stp.py)

th4-4:  ## theme 4, step 4: anomaly peaks (needs job5)
	$(RUN) $(PY) $(call script,anomaly_peaks_th4-4stp.py)

th4-5:  ## theme 4, step 5: anomaly maps
	$(RUN) $(PY) $(call script,anomaly_maps_th4-5stp.py)

theme4:  ## theme 4 complete, in order: th4-1, th4-2, th4-3, job5, th4-4, th4-5
	$(MAKE) th4-1 th4-2 th4-3 job5 th4-4 th4-5

# theme 5: job6 first, then steps th5-1 .. th5-4, then the review list
th5-1:  ## theme 5, step 1: indicators, coordinated groups, figures (needs job6)
	$(RUN) $(PY) $(call script,suspicious_trends_th5-1stp.py) --gold $(GOLD) --out $(AN)/suspicious --figdir $(FIG)/suspicious

th5-2:  ## theme 5, step 2: instant-relay channels
	$(RUN) $(PY) $(call script,fast_mirror_channels_th5-2stp.py)

th5-3:  ## theme 5, step 3: trend without the instant-relay channels
	$(RUN) $(PY) $(call script,fast_trend_excluding_th5-3stp.py)

th5-4:  ## theme 5, step 4: drivers of the peak months
	$(RUN) $(PY) $(call script,fast_month_drivers_th5-4stp.py)

th5-5:  ## theme 5: list of channels to read by hand
	$(RUN) $(PY) $(call script,review_candidates.py) --module $(MIRROR_MOD) --geo $(GEO_CSV)

theme5:  ## theme 5 complete, in order: job6, th5-1 ... th5-4, review
	$(MAKE) job6 th5-1 th5-2 th5-3 th5-4 th5-5

all:  ## WHOLE project, one step after the other (several hours)
	$(MAKE) pipeline theme1 theme2 theme3 theme4 theme5

# ---------------------------------------------------------------- reproducibility check
RUN_ID ?= run1
digest:  ## fingerprint of all results -> digest_$(RUN_ID).tsv   (make digest RUN_ID=run2 after a second run)
	$(RUN) $(PY) $(call script,results_digest.py) --out digest_$(RUN_ID).tsv

compare:  ## compare two fingerprints: make compare A=run1 B=run2  (exit code 1 if anything differs)
	$(RUN) $(PY) $(call script,results_digest.py) --compare digest_$(A).tsv digest_$(B).tsv

# ---------------------------------------------------------------- report application
app:  ## Streamlit report on http://localhost:8501
	docker compose --profile app up app

clean-spark:  ## empty the Spark temporary folder
	$(RUN) bash -c "rm -rf /spark_tmp/*"

# ---------------------------------------------------------------- Airflow (optional orchestration, UI on http://localhost:8080)
.PHONY: airflow-build airflow-up airflow-down airflow-run
airflow-build:  ## build the Airflow image
	docker compose -f docker-compose.airflow.yml build
airflow-up:  ## start Airflow (login admin / admin)
	PROJECT_DIR=$(CURDIR) docker compose --env-file .env -f docker-compose.airflow.yml up -d
airflow-down:  ## stop Airflow
	docker compose -f docker-compose.airflow.yml down
airflow-run:  ## run the WHOLE project through Airflow (follow it on http://localhost:8080)
	docker compose -f docker-compose.airflow.yml exec airflow bash -c "airflow pools set spark 1 'one Spark job at a time' && airflow dags unpause telescope_full && airflow dags trigger telescope_full"