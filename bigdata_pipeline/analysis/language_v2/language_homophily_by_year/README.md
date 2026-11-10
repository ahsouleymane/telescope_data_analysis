# language_homophily_by_year

Same-language share of forwards and language assortativity, year by year.

## How it was generated

`language_analysis_v2.py`, run on 2026-11-11.

Partition: `bigdata_pipeline/analysis/communities_v2/communities_leiden/communities_leiden.csv` (Leiden, detected without language). Language: `telescope_files/Channel_Language.csv`. Forwards: `telescope_pipeline_files/gold` (all months summed, self-loops removed, minimum weight 1).

## Content (10 rows)

| Column | Meaning |
|---|---|
| `year` | year |
| `forwards_between_known` | n |
| `same_language_share` | same |
| `expected_same_language_share` | chance |
| `lift` | lift |
| `assortativity` | r |
