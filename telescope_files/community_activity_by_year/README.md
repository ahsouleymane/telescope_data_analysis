# Community activity by year (dated cascades)

One row per (year, community) pair, giving the number of
dated cascades that touch that community during that year.

Only the TOP_N largest communities (by total channel count,
from `community_sizes.csv`) are included — the map figures
track exactly these communities.

- `year` — calendar year (2015-2024). 2015 and 2024 are
  partial years in the source data.
- `community_id` — Leiden community ID.
- `n_cascades` — number of dated cascades (from
  `cascade_community_timeline.csv`) touching this community
  during that year.

Note: ~68% of cascades have a known date; counts here are
over the dated subset only.

## File
- `community_activity_by_year.csv` — 109 rows, 3 columns.

## Columns
- `year` (int64) — e.g. `2015`
- `community_id` (str) — e.g. `6`
- `n_cascades` (int64) — e.g. `479`
