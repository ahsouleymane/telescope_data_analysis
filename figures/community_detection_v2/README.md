# Charts - Community detection (igraph + Leiden), v2

All outputs produced by `community_detection_v2.py`.

## Matplotlib PNG
- `community_size_distribution.png` - histogram of community sizes (log y).
- `degree_distribution.png` - CCDF of node degree (log-log).
- `resolution_curve.png` - number of communities vs. Leiden resolution (needs --resolution-curve).
- `top_20_communities.png` - the largest communities, named by dominant language when --languages is given.
- `community_size_rank.png` - community size against rank, log-log, one line per algorithm.
- `flows_between_communities.png` - share of each community's outgoing forwards that go to each community (15 largest + other).
- `yearly_structure.png` - active channels, communities and modularity per year.
- `yearly_stability.png` - NMI between consecutive years, with the same-year/other-seed noise floor when --seed-baseline is used.

## Gephi
- `meta_graph.gexf` - community-level meta-graph to open in Gephi. Node size = channel count, edge weight = forwards between the two communities (attribute `links` = distinct channel pairs).
