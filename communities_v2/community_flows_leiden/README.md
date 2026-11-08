# community_flows_leiden

Forwards between the 15 largest Leiden communities (the others grouped as 'other').

## How it was generated

`community_detection_v2.py`, run on 2026-11-08.

- Input: monthly edges `telescope_pipeline_files/gold` (6,880,522 (origin, destination, month) rows).
- Graph: forwards summed over all months, self-loops removed, pairs with fewer than 1 forward(s) dropped.
- Leiden: modularity objective, resolution 1.0, seed 42, weights = number of forwards, A->B and B->A summed (undirected).
- Infomap: directed, weights = number of forwards, 1 trial(s).

## Content (236 rows)

| Column | Meaning |
|---|---|
| `origin_community` | community of the channel that wrote the message |
| `dest_community` | community of the channel that forwarded it |
| `forwards` | number of forwards |
| `share_of_origin_out` | forwards / all forwards of messages written in origin_community |
