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
