# Community assignments (channel -> community)

One row per channel in the Channel-to-Channel graph.

Each channel is assigned to exactly one Leiden community
(resolution=1.0, seed=42, on the undirected version of the graph).

- `channel_id`: the channel's numeric ID (as a string).
- `community_id`: the Leiden community ID (integer).

## File
- `communities.csv` — 261,172 rows, 2 columns.

## Columns
- `channel_id` (str) — e.g. `2225415125`
- `community_id` (int64) — e.g. `6`
