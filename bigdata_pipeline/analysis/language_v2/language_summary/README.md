# language_summary

Global agreement between the communities and the languages, and how much forwarding stays inside a language. NMI/ARI close to 1 mean the partition recovers the languages; homogeneity = a community holds one language; completeness = a language is kept in one community. assortativity: 0 = language ignored, 1 = forwards never cross languages.

## How it was generated

`language_analysis_v2.py`, run on 2026-11-11.

Partition: `bigdata_pipeline/analysis/communities_v2/communities_leiden/communities_leiden.csv` (Leiden, detected without language). Language: `telescope_files/Channel_Language.csv`. Forwards: `telescope_pipeline_files/gold` (all months summed, self-loops removed, minimum weight 1).

## Content (21 rows)

| Column | Meaning |
|---|---|
| `measure` | name of the measure |
| `value` | value |
