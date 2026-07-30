# Graph Report - C:\Users\artur\Desktop\Projetos\Print  (2026-07-30)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 44 nodes · 126 edges · 7 communities (4 shown, 3 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 1 edges (avg confidence: 0.5)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `16c78370`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Community 0
- Community 1
- Community 2

## God Nodes (most connected - your core abstractions)
1. `Automacao` - 35 edges
2. `App` - 9 edges
3. `Percorre a tabela uma vez. Para cada ID em ids_passo2 encontrado:         - Conv` - 2 edges

## Surprising Connections (you probably didn't know these)
- `App` --uses--> `Automacao`  [INFERRED]
  main.py → automacao.py

## Import Cycles
- None detected.

## Communities (7 total, 3 thin omitted)

## Knowledge Gaps
- **3 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Automacao` connect `Community 1` to `Community 0`, `Community 2`, `Community 3`, `Community 4`, `Community 5`?**
  _High betweenness centrality (0.646) - this node is a cross-community bridge._
- **Why does `App` connect `Community 2` to `Community 1`?**
  _High betweenness centrality (0.231) - this node is a cross-community bridge._