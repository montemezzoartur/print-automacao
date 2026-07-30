# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## O que é este projeto

Automação para o sistema PACS da Print Imagem (`https://pacs.printimagem.com.br`). O app abre o Microsoft Edge, faz login automaticamente e a cada 30 segundos clica em "Buscar Exames". Para exames com modalidade CT ou DX e convênios específicos, clica no ícone "L" da coluna Ações, confirma o popup com "Sim" e fecha a aba aberta.

Possui interface gráfica com botão ATIVAR/DESATIVAR para controlar a automação.

## Estrutura dos arquivos

| Arquivo | Papel |
|---|---|
| `main.py` | Interface gráfica (Tkinter) e ponto de entrada |
| `automacao.py` | Lógica Selenium: login, busca, análise da tabela, cliques |
| `config.py` | Credenciais e parâmetros — **não commitado** (ver `.gitignore`) |
| `config.exemplo.py` | Template de `config.py` com valores fictícios |
| `iniciar.bat` | Lançador — duplo clique para abrir o app |
| `Print Automação.lnk` | Atalho do Windows na pasta do projeto |

## Como executar

```
# Instalar dependências (apenas na primeira vez)
pip install -r requirements.txt

# Iniciar o app
python main.py
# ou duplo clique em: iniciar.bat
```

## Configuração

Copiar `config.exemplo.py` para `config.py` e preencher:

```python
USUARIO = "seu_usuario"
SENHA   = "sua_senha"
```

`config.py` está no `.gitignore` e nunca deve ser commitado.

## Dependências

- Python 3.12+
- `selenium` 4.21 — controla o Edge
- `webdriver-manager` 4.0 — baixa o driver correto do Edge automaticamente
- `tkinter` — interface gráfica (incluso no Python)
- Microsoft Edge instalado no sistema

## Fluxo da automação (`automacao.py`)

1. `iniciar()` → abre Edge → chama `_fazer_login()` → entra em `_loop_principal()`
2. A cada 30s: `_buscar_e_processar()` → clica no botão → `_processar_tabela()`
3. Para cada linha: verifica coluna **Mod.** (CT/DX) e coluna **Convênio** (lista em `config.py`)
4. Se ambas batem: `_clicar_icone_l()` → `_confirmar_popup()` → fecha aba extra

## Atualizar repositório GitHub após mudanças

```
cd C:\Users\artur\Desktop\Projetos\Print
git add .
git commit -m "descrição da mudança"
git push
```

---

# Base de trabalho

Esta parte define como devemos trabalhar juntos. Ela complementa o CLAUDE.md global — as orientações globais continuam valendo sempre. Em caso de conflito, vale a ordem de prioridade descrita no final deste documento.

## Como se comunicar comigo

- Sempre responder em português, de forma clara e simples.
- Sou um desenvolvedor **não técnico** → evitar jargão. Quando um termo técnico for inevitável, explicá-lo em uma frase.
- Quando eu precisar fazer algo manualmente, fornecer sempre um **passo a passo numerado**, simples e na ordem certa.
- Continuar levantando dúvidas e suposições: se algo estiver ambíguo, perguntar antes de implementar.

## Skills e plugins

- Sempre usar as skills e plugins instalados quando forem úteis, em vez de fazer "na mão".
- Ênfase no plugin **superpowers**, em especial:
  - `brainstorming` → antes de criar/projetar algo novo.
  - `test-driven-development` → ao escrever código (teste antes da implementação).
  - `systematic-debugging` → ao investigar erros/bugs.
- Usar as demais skills do superpowers e das outras skills instaladas conforme a situação pedir.

## Qualidade de código

- Revisar e testar o código após cada alteração. Não dar uma etapa por concluída sem evidência de que funciona.
- Code review é **OBRIGATÓRIO** após TODA implementação nova ou modificação, ANTES do merge na branch principal (usar a skill de code review / `superpowers:requesting-code-review`). Não é opcional: rodar testes não substitui a revisão — a revisão já pegou bug crítico que os testes não pegaram. Verificar os apontamentos antes de aplicar e corrigir os críticos/importantes.
- **SEMPRE perguntar COMO fazer a revisão ANTES de lançá-la** — decidir juntos. A revisão via workflow (`/code-review`) dispara muitos subagentes e gasta muitos tokens (nível `xhigh` ≈ 15–30× uma revisão inline). Antes de disparar, apresentar as opções (inline leve · workflow em nível menor · workflow `xhigh`) e o custo, e esperar a escolha. Regra de bolso: inline/leve para mudanças pequenas ou de UI; `xhigh` só para mudanças grandes, de lógica ou arriscadas.
- Seguir boas práticas: código simples, claro, sem duplicação desnecessária.

## Fluxo de trabalho com Git (branches e merge)

- Desenvolver cada etapa/tarefa em uma **branch separada** e, depois de revisada e testada, mesclar na branch principal.
- **Nunca** desenvolver direto na branch principal.
- Commits pequenos e descritivos por etapa.

## Design

- Não usar a skill `frontend-design` — exceto se for explicitamente pedida.
- Se o projeto tiver arquivos de referência de design (ex.: `PRODUCT.md` para o "quem/o quê/porquê" e `DESIGN.md` para o sistema visual — tokens, paleta, tipografia, componentes), ler e partir deles antes de qualquer trabalho de interface, respeitando as regras neles definidas.

## Registro de progresso

- Manter um arquivo `memory.md` atualizado a cada passo, avanço ou evolução do projeto.

## Prioridade das diretrizes

1. Instruções diretas suas (no chat).
2. Este arquivo (CLAUDE.md do projeto).
3. CLAUDE.md global.
4. Comportamento padrão.

## graphify

This project has a knowledge graph at graphify-out/ with god nodes, community structure, and cross-file relationships.

Rules:
- For codebase questions, first run `graphify query "<question>"` when graphify-out/graph.json exists. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts. These return a scoped subgraph, usually much smaller than GRAPH_REPORT.md or raw grep output.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).
