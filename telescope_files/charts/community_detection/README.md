# Charts — Community detection (igraph + Leiden)

All outputs produced by `community_detection.py`.

## Matplotlib PNG
- `community_size_distribution.png` — histogram of community sizes (log y).
- `top_20_communities.png` — 20 largest communities, named by dominant language.
- `degree_distribution.png` — CCDF of node degree (log-log).
- `resolution_curve.png` — number of communities vs. Leiden resolution.

## Gephi
- `meta_graph.gexf` — community-level meta-graph to open in Gephi.
  Node size = channel count, edge width = inter-community links.
