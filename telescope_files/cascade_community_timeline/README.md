# Cascade → communities timeline

One row per message-forwarding cascade (connected component of
the forwarding graph), with its date, engagement and the set of
communities it touches.

## Source files
- `Message_Forwarding_Flows.csv` — one row per cascade, with the
  list of `(channel_id, message_id)` pairs in
  `connected_component_nodes`.
- `Aggregated_User_Interactions.csv` — one row per cascade with
  a known date and engagement (`views`, `forwards`), inside
  `filtered_message_info`. This is the only file with real
  calendar timestamps.
- `communities.csv` — `channel_id → community_id` (produced by
  `community_detection.py`).

## File
- `cascade_community_timeline.csv` — 20,538,309 rows.
- Cascades with a known date: 13,972,042 (68.0% of all cascades).
- Cross-community cascades (>= 2 communities): 4,484,024 (21.8% of all cascades).

## Columns
- `connected_component_id` (str) — cascade identifier; unique
  per row. Join key with `Aggregated_User_Interactions.csv`.
- `n_channels` (int) — number of distinct channels that took
  part in the cascade (any instance of the propagated message
  across channels counts once).
- `n_communities` (int) — number of distinct communities among
  those channels, using `communities.csv`. Cascades with
  `n_communities >= 2` are the ones relevant for cross-community
  propagation analysis.
- `communities` (str) — `;`-joined community IDs touched by the
  cascade (sorted, deduplicated). Empty if no channel of the
  cascade is in `communities.csv`.
- `date` (datetime, UTC) — cascade date, taken from
  `Aggregated_User_Interactions.csv`. `NaN` when the cascade has
  no entry in that file (~32% of cascades).
- `views` (int) — total views reported for the cascade in
  `Aggregated_User_Interactions.csv`. 0 when unknown.
- `forwards` (int) — total forwards reported for the cascade in
  `Aggregated_User_Interactions.csv`. 0 when unknown.

## Coverage note
`Aggregated_User_Interactions.csv` is a strict subset of
`Message_Forwarding_Flows.csv` (every `connected_component_id`
in the former also appears in the latter, and the ID is unique
in both). About 68% of cascades therefore have a known date;
the remaining 32% have `date = NaN` but are kept so that
structural statistics (`n_channels`, `n_communities`) remain
complete over the full cascade set.

## Notes
- The CSV is written incrementally (chunk by chunk) by
  `build_cascade_timeline`, so a partial run leaves a usable
  partial file rather than nothing.
- Row order follows the source file order of
  `Message_Forwarding_Flows.csv`.
