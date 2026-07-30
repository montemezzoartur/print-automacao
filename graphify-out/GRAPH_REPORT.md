# Graph Report - Print  (2026-07-30)

## Corpus Check
- 10 files · ~57,426 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 196 nodes · 343 edges · 14 communities (11 shown, 3 thin omitted)
- Extraction: 100% EXTRACTED · 0% INFERRED · 0% AMBIGUOUS · INFERRED: 1 edges (avg confidence: 0.5)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `f4d99983`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- ._checar_ids_aguardando
- Automacao
- App
- .iniciar
- ._checar_ct_aguardando
- ._clicar_buscar_exames
- CLAUDE.md
- Base de trabalho
- .log
- ponytail-audit/SKILL.md
- ponytail-review/SKILL.md
- ._assinatura_tabela
- ._carregar_estado

## God Nodes (most connected - your core abstractions)
1. `Automacao` - 46 edges
2. `RegrasDoPasso1` - 19 edges
3. `SemNavegador` - 11 edges
4. `App` - 9 edges
5. `NavegadorFalso` - 9 edges
6. `Base de trabalho` - 9 edges
7. `LogEmArquivo` - 8 edges
8. `LeituraDeCelulas` - 8 edges
9. `RegraDeConvenioDX` - 8 edges
10. `OrcamentoDeTempo` - 8 edges

## Surprising Connections (you probably didn't know these)
- `App` --uses--> `Automacao`  [INFERRED]
  main.py → automacao.py

## Import Cycles
- None detected.

## Communities (14 total, 3 thin omitted)

### Community 0 - "._checar_ids_aguardando"
Cohesion: 0.08
Nodes (8): AvisosDeProblema, DetectarColunas, EstadoEmDisco, LeituraDeCelulas, Testes da lógica que não depende do navegador.  Rodar com:  python -m unittest t, A causa mais provável de 'fica marcado para sempre': fechar o app     apagava a, Base para testar a lógica pura, que não abre o Chrome., SemNavegador

### Community 2 - "App"
Cohesion: 0.23
Nodes (3): _cronometrar(), Grava a duração da função no arquivo de log (não na janela do app)., App

### Community 3 - ".iniciar"
Cohesion: 0.13
Nodes (4): As regras de elegibilidade — a lógica de negócio mais mexida do projeto., _convenio_bate_dx decide se a marcação do Passo 2 estava certa., RegraDeConvenioDX, RegrasDoPasso1

### Community 4 - "._checar_ct_aguardando"
Cohesion: 0.19
Nodes (4): Cronometro, Fake, LogEmArquivo, O decorador @_cronometrar mede as funções lentas do Selenium.

### Community 5 - "._clicar_buscar_exames"
Cohesion: 0.14
Nodes (10): Automacao, Procura o primeiro seletor que casar, com orçamento de tempo TOTAL.          Ant, Registra um aviso grave só na primeira vez, para não inundar o log., Espera a aba extra abrir depois do clique no 'L'. Antes era sleep(1) fixo., Conta falhas seguidas de desmarcação no mesmo exame.          Um exame que falha, Percorre a tabela uma vez. Para cada ID em ids_passo2 encontrado:         - Conv, Percorre a tabela uma vez. Para cada ID em ids_passo2_ct (CT crânio):         -, Lê cabeçalhos e células da tabela inteira numa única chamada ao navegador. (+2 more)

### Community 7 - "CLAUDE.md"
Cohesion: 0.10
Nodes (19): Atualizar repositório GitHub após mudanças, Base de trabalho, Como a checagem decide, Como executar, Como se comunicar comigo, Configuração, Conjuntos de controle, Dependências (+11 more)

### Community 8 - "Base de trabalho"
Cohesion: 0.17
Nodes (5): ElementoFalso, NavegadorFalso, OrcamentoDeTempo, Só o suficiente para exercitar _encontrar_elemento sem abrir o Chrome., O defeito central da versão antiga: cada seletor gastava o tempo inteiro.

### Community 9 - ".log"
Cohesion: 0.22
Nodes (8): Boundaries, Intensity, Output, Persistence, Ponytail, Rules, The ladder, When NOT to be lazy

### Community 10 - "ponytail-audit/SKILL.md"
Cohesion: 0.40
Nodes (4): Boundaries, Hunt, Output, Tags

### Community 11 - "ponytail-review/SKILL.md"
Cohesion: 0.40
Nodes (4): Boundaries, Examples, Format, Scoring

## Knowledge Gaps
- **32 isolated node(s):** `Tags`, `Hunt`, `Output`, `Boundaries`, `Format` (+27 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **3 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Automacao` connect `._clicar_buscar_exames` to `Automacao`, `App`, `._assinatura_tabela`, `._carregar_estado`?**
  _High betweenness centrality (0.359) - this node is a cross-community bridge._
- **Why does `RegrasDoPasso1` connect `.iniciar` to `._checar_ids_aguardando`?**
  _High betweenness centrality (0.127) - this node is a cross-community bridge._
- **Why does `LogEmArquivo` connect `._checar_ct_aguardando` to `._checar_ids_aguardando`?**
  _High betweenness centrality (0.059) - this node is a cross-community bridge._
- **What connects `Tags`, `Hunt`, `Output` to the rest of the system?**
  _32 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `._checar_ids_aguardando` be split into smaller, more focused modules?**
  _Cohesion score 0.07586206896551724 - nodes in this community are weakly interconnected._
- **Should `.iniciar` be split into smaller, more focused modules?**
  _Cohesion score 0.12666666666666668 - nodes in this community are weakly interconnected._
- **Should `._clicar_buscar_exames` be split into smaller, more focused modules?**
  _Cohesion score 0.14009661835748793 - nodes in this community are weakly interconnected._