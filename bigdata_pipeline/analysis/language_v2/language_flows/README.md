# language_flows

The 30 largest language-to-language flows (both channels with a known language).

## How it was generated

`language_analysis_v2.py`, run on 2026-11-14.

Partition: `bigdata_pipeline/analysis/communities_v2/communities_leiden/communities_leiden.csv` (Leiden, detected without language). Language: `telescope_files/Channel_Language.csv`. Forwards: `telescope_pipeline_files/gold` (all months summed, self-loops removed, minimum weight 1).

## Content (30 rows)

| Column | Meaning |
|---|---|
| `src` | origin language |
| `src_name` | name |
| `dst` | forwarding language |
| `dst_name` | name |
| `forwards` | number of forwards |
| `share_of_source_out` | share of the origin language's forwards |
