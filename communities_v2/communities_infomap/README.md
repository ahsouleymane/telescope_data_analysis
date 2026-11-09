# communities_infomap

Community of every channel that has at least one forward link, from Infomap. Community 0 is the largest.

## How it was generated

`community_detection_v2.py`, run on 2026-11-10.

- Input: monthly edges `telescope_pipeline_files/gold` (6,880,522 (origin, destination, month) rows).
- Graph: forwards summed over all months, self-loops removed, pairs with fewer than 1 forward(s) dropped.
- Leiden: modularity objective, resolution 1.0, seed 42, weights = number of forwards, A->B and B->A summed (undirected).
- Infomap: directed, weights = number of forwards, 1 trial(s).

## Content (267,518 rows)

| Column | Meaning |
|---|---|
| `channel_id` | Telegram channel id |
| `community` | community number (0 = largest) |
| `community_size` | number of channels in that community |
| `forwards_total` | forwards in + out of the channel in the graph |
