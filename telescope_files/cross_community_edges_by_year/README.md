# Cross-community edges by year (dated cascades)

One row per (year, unordered community pair) with at least
one dated cascade touching BOTH communities during that
year — this is the edge list of the yearly diffusion maps.

Only pairs whose two communities are both in the TOP_N
largest communities (by total channel count) are included.

- `year` — calendar year (2015-2024).
- `community_a`, `community_b` — the two community IDs,
  always ordered so that `community_a < community_b`
  (each unordered pair appears once per year).
- `n_cascades` — number of dated cascades touching both
  communities during that year.

Note: ~68% of cascades have a known date; counts here are
over the dated subset only.

## File
- `cross_community_edges_by_year.csv` — 401 rows, 4 columns.

## Columns
- `year` (int64) — e.g. `2016`
- `community_a` (str) — e.g. `0`
- `community_b` (str) — e.g. `1`
- `n_cascades` (int64) — e.g. `1226`
