# Charts - language analysis

All outputs produced by `language_analysis.py` (matplotlib PNG, English labels).

- `language_distribution.png` - channels per language (top 15, log scale).
- `community_purity_hist.png` - purity of communities weighted by size, with the NMI between language and community partitions in the title.
- `language_mixing_matrix.png` - share of each language's outgoing edges going to each language (each row sums to 1).
- `language_homophily.png` - observed / expected share of edges that stay inside the language (above 1 = more inward than chance).
- `language_graph_structure.png` - reciprocity, clustering, giant component and hub concentration of the sub-graph of each language.
