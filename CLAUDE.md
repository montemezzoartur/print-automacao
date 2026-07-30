# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## O que é este projeto

Automação para o sistema PACS da Print Imagem (`https://pacs.printimagem.com.br`). O app abre o Google Chrome, faz login automaticamente e percorre a lista de exames marcando e desmarcando o campo **Realizante**, conforme regras de modalidade (CT/DX), convênio, descrição do exame e idade do paciente.

A interface tem três botões — **CT e DX**, **CT** e **DX** — que escolhem o modo de operação. Só um modo fica ativo por vez; ao desativar, o navegador continua aberto.

## Estrutura dos arquivos

| Arquivo | Papel |
|---|---|
| `main.py` | Interface gráfica (Tkinter) e ponto de entrada |
| `automacao.py` | Lógica Selenium: login, busca, análise da tabela, cliques |
| `config.py` | Credenciais e parâmetros — **não commitado** (ver `.gitignore`) |
| `config.exemplo.py` | Template de `config.py` com valores fictícios |
| `instalar.bat` | Instalador completo: acha ou instala o Python, instala as dependências, cria o `config.py` e o atalho na área de trabalho |
| `iniciar.bat` | Lançador — duplo clique para abrir o app (gerado pelo `instalar.bat`, fora do Git) |
| `*.png` | Capturas de tela do PACS, guardadas como referência |

## Como executar

```
# Primeira vez: duplo clique em instalar.bat
# (instala Python, dependências, cria config.py e o atalho)

# Ou manualmente:
pip install -r requirements.txt
python main.py

# No dia a dia: duplo clique em iniciar.bat
```

## Configuração

Copiar `config.exemplo.py` para `config.py` e preencher — o `instalar.bat` já faz isso e abre o arquivo no Bloco de Notas.

| Parâmetro | Para que serve |
|---|---|
| `URL` | Endereço da tela de login do PACS |
| `USUARIO` / `SENHA` | Credenciais do PACS |
| `REALIZANTE_NOME` | Nome procurado na coluna Realizante |
| `MODS_ALVO` | Modalidades consideradas no modo "CT e DX" |
| `CONVENIOS_ALVO` | Convênios que autorizam marcar o realizante |
| `VARREDURA_DURACAO_SEG` / `VARREDURA_VERIFICACOES` | Duração da etapa de varredura e em quantas fatias ela é dividida |
| `CHECAGEM_DURACAO_SEG` / `CHECAGEM_MAX_ACOES` | Limites da etapa de checagem |

`config.py` está no `.gitignore` e nunca deve ser commitado.

## Dependências

- Python 3.12+
- `selenium` 4.21 — controla o Chrome
- `tkinter` — interface gráfica (incluso no Python)
- Google Chrome instalado no sistema (o Selenium baixa o driver sozinho)

## Fluxo da automação (`automacao.py`)

**Entrada:** `main.py` chama `Automacao.iniciar(modo)` numa thread separada. O `iniciar()` interrompe qualquer loop anterior (via `_loop_lock`), abre o Chrome, faz `_fazer_login()` e entra em `_loop_principal()`.

**Modo CT** → `_loop_ct_only()`: laço contínuo — clica em Buscar Exames, executa uma ação do Passo 1 e uma verificação de CT crânio. Se nada aconteceu, espera 10s e repete.

**Modos "CT e DX" e "DX"** → `_loop_principal()` repete três etapas em ciclo:

| Etapa | O que faz |
|---|---|
| 1. Reconciliação (`_etapa_reconciliacao`) | Limpa sobras de sessões anteriores. Só age em exames **DX** que reúnam todas estas condições: realizante preenchido com `REALIZANTE_NOME`, convênio já preenchido, convênio que **não** bate as regras DX, e coluna **Laudo vazia** — exame já laudado nunca é tocado. Então executa o Passo 3. Máximo de 10 ações. |
| 2. Varredura (`_etapa_varredura`) | Alterna Passo 1 e Passo 2 até esgotar. Dura `VARREDURA_DURACAO_SEG`, dividido em `VARREDURA_VERIFICACOES` fatias. |
| 3. Checagem (`_etapa_checagem`) | Revisita os exames deixados em espera. Limitada por `CHECAGEM_DURACAO_SEG` e `CHECAGEM_MAX_ACOES`. Se não há ninguém em espera, encerra na hora. |

### Os três passos

**Passo 1 — marcar** (`_executar_passo1_uma_acao`). Só age se a coluna Realizante estiver **vazia**. Marca (clica no ícone "L", confirma o popup com "Sim" e fecha a aba extra) quando:

- **CT de crânio** com idade ≤ 45 e convênio **não** UNIMED → marca e guarda em `ids_passo2_ct` para verificar depois
- Descrição com **ANGIO** e convênio não UNIMED
- **CT** com TEP ou CARÓTIDA e convênio não UNIMED
- Caso geral: convênio presente em `CONVENIOS_ALVO` — exceto SAS, FLIP, ARAMART, AVICOLA e HI-MIX, que não valem quando a modalidade é CT

**Passo 2 — marcar e esperar** (`_executar_passo2_uma_acao`). Exames **DX** com Convênio **e** Realizante vazios: marca o "L" e guarda em `ids_passo2`. O convênio ainda vai aparecer no sistema; a checagem decide depois se a marcação valeu.

**Passo 3 — desmarcar** (`_executar_passo3`). Abre o popup "Editar realizante", desmarca o checkbox e salva. É o que desfaz uma marcação indevida.

### Como a checagem decide

`_checar_ids_aguardando()` — os DX do Passo 2:

| Situação | Ação |
|---|---|
| Convênio ainda vazio | Mantém em espera |
| Convênio bate as regras DX (`_convenio_bate_dx`) | Encerra sem ação — a marcação estava certa |
| Convênio não bate | Passo 3 — desmarca |

`_checar_ct_aguardando()` — os CT crânio do Passo 1:

| Situação | Ação |
|---|---|
| Convênio ainda vazio | Mantém em espera |
| Convênio é UNIMED | Passo 3 — desmarca |
| Outro convênio | Mantém marcado e tira da espera |

### Conjuntos de controle

Cada exame é identificado pelo par `(nome, data do exame)`.

- `ids_passo2` — DX marcados no Passo 2, esperando o convênio aparecer
- `ids_passo2_ct` — CT crânio marcados no Passo 1, esperando o convênio
- `ids_passo3` — exames já desmarcados. O Passo 2 e a regra de CT crânio do Passo 1 consultam essa lista para não remarcar; as demais regras do Passo 1 (ANGIO, CT especial, convênio da lista) **não** a consultam

## Atualizar repositório GitHub após mudanças

**Normalmente não é preciso fazer nada.** Existe um hook `Stop` em `.claude/settings.json` que roda `git add .`, `git commit` e `git push` automaticamente ao fim de cada resposta do Claude Code, com a mensagem `auto: atualizacao via Claude Code`.

Para commitar manualmente com uma mensagem descritiva:

```
cd <pasta do projeto>
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
