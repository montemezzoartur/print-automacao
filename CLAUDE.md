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
cd C:\Users\artur\OneDrive\Controle\Projetos\Print
git add .
git commit -m "descrição da mudança"
git push
```

# CLAUDE.md

Behavioral guidelines to reduce common LLM coding mistakes. Merge with project-specific instructions as needed.

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

## 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

## 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

---

**These guidelines are working if:** fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, and clarifying questions come before implementation rather than after mistakes.
