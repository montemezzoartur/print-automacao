# Graph Report - Print  (2026-07-30)

## Corpus Check
- 6 files · ~53,667 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 66 nodes · 146 edges · 10 communities (6 shown, 4 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 1 edges (avg confidence: 0.5)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `f1f8afe0`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- ._checar_ids_aguardando
- Automacao
- App
- ._checar_ct_aguardando
- CLAUDE.md
- Base de trabalho

## God Nodes (most connected - your core abstractions)
1. `Automacao` - 35 edges
2. `App` - 9 edges
3. `Base de trabalho` - 9 edges
4. `Fluxo da automação (`automacao.py`)` - 4 edges
5. `Percorre a tabela uma vez. Para cada ID em ids_passo2 encontrado:         - Conv` - 1 edges
6. `Percorre a tabela uma vez. Para cada ID em ids_passo2_ct (CT crânio):         -` - 1 edges
7. `O que é este projeto` - 1 edges
8. `Estrutura dos arquivos` - 1 edges
9. `Como executar` - 1 edges
10. `Configuração` - 1 edges

## Surprising Connections (you probably didn't know these)
- `App` --uses--> `Automacao`  [INFERRED]
  main.py → automacao.py

## Import Cycles
- None detected.

## Communities (10 total, 4 thin omitted)

### Community 7 - "CLAUDE.md"
Cohesion: 0.17
Nodes (10): Atualizar repositório GitHub após mudanças, Como a checagem decide, Como executar, Configuração, Conjuntos de controle, Dependências, Estrutura dos arquivos, Fluxo da automação (`automacao.py`) (+2 more)

### Community 8 - "Base de trabalho"
Cohesion: 0.22
Nodes (9): Base de trabalho, Como se comunicar comigo, Design, Fluxo de trabalho com Git (branches e merge), graphify, Prioridade das diretrizes, Qualidade de código, Registro de progresso (+1 more)

## Knowledge Gaps
- **17 isolated node(s):** `O que é este projeto`, `Estrutura dos arquivos`, `Como executar`, `Configuração`, `Dependências` (+12 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **4 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Automacao` connect `Automacao` to `._checar_ids_aguardando`, `App`, `.iniciar`, `._checar_ct_aguardando`, `._clicar_buscar_exames`, `.log`?**
  _High betweenness centrality (0.291) - this node is a cross-community bridge._
- **Why does `App` connect `App` to `Automacao`?**
  _High betweenness centrality (0.103) - this node is a cross-community bridge._
- **Why does `Base de trabalho` connect `Base de trabalho` to `CLAUDE.md`?**
  _High betweenness centrality (0.060) - this node is a cross-community bridge._
- **What connects `O que é este projeto`, `Estrutura dos arquivos`, `Como executar` to the rest of the system?**
  _17 weakly-connected nodes found - possible documentation gaps or missing edges._