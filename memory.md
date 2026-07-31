# memory.md — registro do projeto

Histórico de tudo que foi feito: avanços, decisões, e também os erros e as
reversões. Ordem: o que vale agora primeiro, o histórico depois.

---

## ▶ COMEÇAR POR AQUI — próxima sessão (definido em 31/07/2026, fim do dia)

**Tarefa: rodar mais 2 ou 3 sessões com o código atual, sem mexer em nada.**

Motivo: os `stale element` caíram de 8 para 2, mas **2 eventos não sustentam
conclusão nenhuma**. Precisamos de amostra antes de atacá-los, e as sessões
extras também confirmam que a troca do `sleep(2)` é estável. Não custa nada.

**Não alterar código enquanto isso.** Se surgir vontade de reduzir o teto de
2,0s: é adivinhação. Quando o conteúdo é idêntico a assinatura não muda, então
não existe medição de quanto o PACS realmente leva nesse caso.

### Passo a passo para o Artur

1. `cd C:\Users\artur\Desktop\Projetos\Print`
2. `git branch --show-current` → **tem que responder `otimiza-marcacao`**.
   Se responder `master`, rodar `git checkout otimiza-marcacao`.
   A `master` não tem log, nem cronômetro, nem `[tabela]`, nem `estado.json` —
   rodar nela não gera dado nenhum e ainda perde a correção do "marcado para sempre".
3. `python main.py`, ativar no modo de sempre, deixar rodar, fechar.
4. Repetir 2–3 vezes, **em horários diferentes** (manhã, meio-dia, fim de tarde).
5. **Não renomear nada entre as sessões** — o log abre em modo append
   (`automacao.py:76`) e acumula sozinho. As sessões se separam pelos intervalos
   de tempo na análise.
6. Só no fim, gerar o resumo uma vez (comando na seção "LOG COLETADO" abaixo).

O `automacao.log` já contém a sessão de 11:04–11:26. As novas entram por cima.

### O que analisar quando os dados chegarem

| Pergunta | Como responder |
|---|---|
| Os `stale element` mantêm ~0,094/min ou os 2 foram sorte? | Taxa por minuto de cada sessão, não o total |
| A proporção de 6,8% de buscas rápidas se confirma? | Contar `[tabela]` teto vs mudou |
| A tabela alguma vez renderiza em etapas? | Procurar `[tabela]` com contagem de linha diferente do normal (43) ou muito baixa |
| O agrupamento dos stale num segundo fixo é real? | Antes caíam aos `:11`, depois aos `:27` — ver se há padrão com mais amostra |

**Só depois disso** decidir entre: mesclar na `master`, atacar os `stale element`,
ou outra coisa. A branch segue **sem merge**.

---

## ESTADO ATUAL (atualizado em 31/07/2026)

**Branch de trabalho:** `otimiza-marcacao` — enviada ao GitHub, **não mesclada** na `master`.
**`master`:** intacta, exatamente como estava antes de começarmos.

> ⚠️ A tabela abaixo descrevia a branch em 30/07, quando ela era só "o núcleo
> seguro" sem ganho de velocidade. **Isso mudou em 31/07**: a troca do `sleep(2)`
> foi feita, revisada e validada em produção. Ver as seções seguintes.
> O que continua valendo: as duas tentativas de otimização *anteriores* (leitura
> por JavaScript e orçamento de tempo) seguem desfeitas, e por bom motivo.

Além do que está na tabela, a branch hoje tem: `_esperar_tabela_pronta()` no lugar
do `sleep(2)`, `_assinatura_tabela()`, `JS_ASSINATURA_TABELA`, o diagnóstico
`[tabela]` no log e **53 testes** (eram 45).

| O que a branch tem | Para que serve |
|---|---|
| Log em `automacao.log`, com data completa | O app só escrevia numa janelinha de 6 linhas que sumia ao fechar. Sem isso não dá para diagnosticar nada. |
| Cronômetro (`[tempo] ...`) em `buscar_exames`, `clicar_L_marcar` e `passo3_desmarcar` | Mede onde os segundos vão de verdade. Só vai para o arquivo, não polui a janela. |
| Lista de espera em `estado.json` | Resolve a causa principal dos exames marcados para sempre: a lista vivia só na memória e sumia ao fechar o app. Gravação atômica (`.tmp` + `os.replace`). |
| `_avaliar_passo1` como função pura | As regras de convênio/CT viraram testáveis fora do navegador. |
| `_detectar_colunas` puro + `_ler_cabecalhos` | Mesma ideia: detecção de coluna testável. |
| Avisos de coluna ausente e de falha repetida do Passo 3 | Torna visível o que antes falhava calado. |
| `test_automacao.py` | 45 testes, sem dependência nova (usa `unittest`, que vem no Python). |

**O que a branch NÃO tem** *(situação de 30/07 — parcialmente superada)*: os
`sleep(1)` originais continuam lá. O `sleep(2)` **foi substituído em 31/07**. O
problema 1 (perder marcações) melhorou ~1,6s no caminho crítico, mas não foi
resolvido — ver a seção de validação em produção.

---

## ✅ VALIDAÇÃO EM PRODUÇÃO DA TROCA DO `sleep(2)` — 31/07/2026, 11:04 às 11:26

Segunda coleta, com o código novo. Comparação contra `resumo_antes.txt`.

| | ANTES (36,6 min) | DEPOIS (21,3 min) |
|---|---|---|
| `buscar_exames` — média | 2,06s | **1,94s** |
| `buscar_exames` — mínimo | 2,04s | **0,47s** |
| Ciclo entre buscas | 3,43s | **3,00s** |
| Buscas | 640 | 426 |
| `stale element` por minuto | 0,218 | 0,094 |

### O ganho é pequeno no total e grande onde importa

**93,2% das buscas (397 de 426) foram até o teto** — a tabela não mudou. Só
**6,8% (29)** pegaram o caminho rápido. Foi exatamente o previsto ao projetar, e
está registrado acima que seria assim.

Economia total: ~0,12s × 426 ≈ **51s numa sessão de 21 min (~4%)**. Modesto.

Mas na busca que **detecta a mudança** — a que decide se o exame novo é pego —
o tempo caiu de 2,06s para **~0,47s**, ou seja **1,6s a menos no caminho
crítico**. Nas 3 marcações da sessão, a busca que detectou a mudança rodou em
0,48s / 0,49s / 0,48s. Em 2 das 3 ela veio imediatamente antes da marcação.

### O risco em aberto (Important #2) NÃO se materializou

Era a dúvida que sobrou do code review: a janela de estabilidade poderia soltar
num estado intermediário se o PACS renderizasse a tabela em etapas.

**As 29 liberações antecipadas tiveram 43 linhas antes e 43 linhas depois, todas.**
Nenhuma contagem parcial, nenhuma tabela vazia. O que mudou foi só o volume de
texto (dezenas de caracteres — convênio preenchido, realizante, status de laudo).
Os tempos ficaram agrupados em 0,43–0,51s, coerente com 0,1–0,2s até a mudança
aparecer mais os 0,3s de estabilidade.

**Conclusão: este PACS não monta a tabela em etapas.** Risco encerrado — foi a
instrumentação `[tabela]` que permitiu fechar essa questão, não raciocínio.

### O caminho do Critical #1 não foi exercitado

Zero ocorrências de `sem assinatura prévia` — a leitura pré-clique funcionou nas
426 buscas. A guarda continua necessária (o revisor demonstrou em Chrome real que
o estado é alcançável), mas nesta sessão não foi acionada.

### `stale element`: caiu, mas a amostra é pequena demais

8 em 36,6 min → 2 em 21,3 min (0,218/min → 0,094/min, −57%). **Com n=2 isso não
sustenta conclusão** — pode ser variação normal. O que dá para afirmar é que
**não piorou**, que era o risco levantado no review.

Detalhe curioso: o agrupamento num segundo fixo do minuto persistiu, mas mudou de
fase — antes 5 de 6 caíam aos `:11`, agora os 2 caíram aos `:27`. Consistente com
re-renderização periódica do PACS, mas indistinguível de acaso com 2 eventos.

### Ressalva de comparabilidade

As sessões não são gêmeas: horários diferentes (08:24 vs 11:04), durações
diferentes (36,6 vs 21,3 min) e movimento diferente (0,19 vs 0,14 marcações/min).
As médias por busca e as taxas por minuto são comparáveis; os totais absolutos não.

---

## TROCA DO `sleep(2)` — 31/07/2026 (feita, aguardando validação em produção)

Primeira otimização de velocidade do projeto feita **em cima de medição**, e não
de leitura de código. As duas anteriores foram revertidas; esta nasceu do log da
seção seguinte.

**O que mudou** (`automacao.py`, 4 pontos):

| Onde | O quê |
|---|---|
| `JS_ASSINATURA_TABELA` (novo) | `linhas.length + ':' + soma dos textContent`. Impressão digital barata da tabela. |
| `_assinatura_tabela()` (novo) | Lê a assinatura; devolve `None` em qualquer falha. |
| `_esperar_tabela_pronta()` (novo) | Substitui o `sleep(2)`. Libera quando a assinatura **muda** e depois **fica parada** por 0,3s. Teto de 2,0s. |
| `_clicar_buscar_exames()` | Uma linha: `time.sleep(2)` → `self._esperar_tabela_pronta(antes)`. |

**Por que exige que a assinatura MUDE:** é exatamente o que faltava em `ea52da4`.
Lá bastava ficar parada, e o código liberava com a tabela antiga.

**Expectativa realista, para não repetir o erro de projetar no escuro:** o ganho
só aparece quando a busca traz conteúdo **diferente**. Busca com resultado
idêntico continua custando o teto de 2,0s de propósito. Como a grade mostra 25
linhas cobrindo ~2h de exames e as buscas são a cada 3,4s, boa parte delas
provavelmente não muda nada. **Portanto: o tempo total da sessão deve mudar
pouco.** O ganho se concentra na busca que importa — aquela em que o exame novo
apareceu, que é o problema 1.

### Code review — 8 achados, 1 crítico

O crítico era real e **verificado por execução** pelo revisor:

> Com `antes = None` (a leitura pré-clique falhou), a comparação `agora == antes`
> é falsa para qualquer assinatura válida — então a **primeira leitura boa**
> passava por "a tabela mudou", sendo ela a tabela **antiga**. Medido: liberava em
> 0,35s com a tabela pré-busca. Era o defeito de `ea52da4` entrando por outra
> porta, no ponto de maior severidade do projeto.

Corrigido com uma guarda no topo: `antes is None` → dorme o teto e sai.

Também corrigidos: teto estourando até +85,8ms (agora limitado ao custo de uma
chamada JS, medido entre +0,4ms e +40,9ms); `innerText` → `textContent` (o
primeiro força recálculo de layout a cada uma das ~40 leituras por busca); duas
asserções frouxas demais para morder; e a classe de teste nova passou a herdar de
`SemNavegador` — sem isso ela **escrevia nome de paciente no `automacao.log`
real**, justamente o arquivo usado para medir esta mudança.

### Teste de mutação — 6 mutantes

| Mutante | Resultado |
|---|---|
| Remove a guarda `antes is None` | pego |
| Libera na primeira mudança, sem estabilizar | pego |
| Remove a guarda `agora is None` | pego |
| Teto padrão 2.0 → 5.0 | pego |
| `ea52da4` completo (init errado + guarda de mudança removida) | pego |
| Só `ultima = antes`, mantendo a guarda | **sobreviveu — e está certo** |

O último é um **mutante equivalente**: sozinho ele não muda o comportamento,
porque a guarda `agora == antes` continua barrando a tabela antiga. O bug de
`ea52da4` precisava das duas coisas juntas. Sobreviver aqui não é falha de teste.

### O que ficou em aberto (Important #2 do review)

A janela de estabilidade de 0,3s **não distingue** "terminou de renderizar" de
"parou no meio". Se o PACS renderiza em etapas (um placeholder, depois os dados),
a espera pode soltar no estado intermediário. O revisor demonstrou o mecanismo em
código, mas **se o PACS faz isso ou não é hipótese** — só a sessão real diz.

Por isso `_esperar_tabela_pronta` grava uma linha `[tabela] antes -> depois em Ns`
no `automacao.log` (só no arquivo, não na janela). **Na próxima coleta, procurar
assinaturas de liberação pequenas demais** (ex.: `1:12` quando a grade tem 25
linhas) — seria a prova de que renderiza em etapas.

**Linha de base guardada em 31/07/2026:** o log e o resumo da sessão do `sleep(2)`
foram renomeados para `automacao_antes.log` (78381 bytes, 1372 linhas) e
`resumo_antes.txt`, para o log novo nascer zerado e a comparação ficar limpa.

Ao renomear, os padrões do `.gitignore` foram alargados de `automacao.log` e
`resumo.txt` para `automacao*.log` e `resumo*.txt`. **Motivo:** os padrões eram
nomes exatos, então `automacao_antes.log` — que contém nome de paciente — teria
escapado da regra e o hook `Stop` (`git add .` + `push`) o mandaria para um
repositório público. Mesmo tipo de falha do comando de extração corrigido mais
acima. Regra a manter: **qualquer arquivo derivado do log entra no `.gitignore`
antes de ser criado, nunca depois.**

Comando para extrair, sem dado de paciente:

```powershell
Get-Content automacao.log -Encoding UTF8 |
  Select-String -Pattern "\[tempo\]|\[tabela\]|PROBLEMA|ATEN|Erro" |
  ForEach-Object { $_.Line -replace "'[^']*\([0-9/]+\)'", "'[paciente oculto]'" } |
  Set-Content resumo.txt -Encoding UTF8
```

Hipótese adicional do revisor, **não confirmada**: 5 dos 6 `stale element` da
varredura caíram exatamente aos `:11` de cada minuto, sugerindo re-renderização
periódica do PACS num ponto fixo do ciclo de 60s. Se for isso, adiantar a
varredura em ~1,65s muda quais buscas colidem com ela — direção imprevisível sem
medir. Mais um motivo para comparar os dois logs.

---

## ✅ LOG COLETADO — 31/07/2026, 08:24 às 09:00 (36,6 min)

**Este era o objetivo do dia e está cumprido.** O que o log disse, medido sobre
640 buscas e 7 marcações reais:

| Operação | Vezes | Total | Média | Mín | Máx |
|---|---|---|---|---|---|
| `buscar_exames` | 640 | **1320,1s** | 2,06s | 2,04s | 2,25s |
| `clicar_L_marcar` | 7 | 20,1s | 2,87s | 2,69s | 3,35s |
| `passo3_desmarcar` | 2 | 2,6s | 1,30s | 0,33s | 2,28s |

Sessão inteira: 2198s. Cronometrado: 1342,8s (61%).

### As duas suspeitas principais foram REFUTADAS

| Suspeita registrada em 30/07 | Medição real |
|---|---|
| `clicar_L_marcar` perto de **20s** (popup "Sim" não aparece e queima 4 seletores de 5s) | **2,87s de média, máximo 3,35s.** O popup aparece sempre: 7 marcações → 7 "Popup confirmado" → 7 "Ação L concluída". Nenhum seletor estourou o tempo limite. |
| `passo3_desmarcar` perto de **30s** (estouraria o orçamento da checagem) | **1,30s de média, máximo 2,28s.** Longe dos 30s. |
| `PROBLEMA GRAVE: coluna não encontrada` | **Nunca aconteceu.** A reconciliação rodou 37 vezes sem abortar. |

**Lição:** as três hipóteses vinham de ler o código e contar tempos limite no
papel. Nenhuma se confirmou. Reforça o aprendizado de 30/07 — sem medir, não
otimizar. Só que agora vale nos dois sentidos: sem medir também não se sabe onde
**não** está o problema.

### O custo real: o `sleep(2)` do `buscar_exames`

`automacao.py:873` — `time.sleep(2)` fixo depois de clicar em Buscar Exames.

- 640 chamadas × ~2,06s = **1320s = 60% da sessão inteira**, e **98% de todo o
  tempo cronometrado**.
- A variação é de apenas 0,21s (2,04 a 2,25). Ou seja: o trabalho de verdade
  leva ~0,05s e o `sleep` responde por 2,0s. É espera pura.
- Ritmo do laço: uma busca a cada **3,43s** (359 intervalos de 3s, 259 de 4s).

**Ligação com o problema 1 (perder marcações):** da hora em que um DX aparece
até ele ficar marcado passam-se ~3,4s de espera pela próxima busca (média ~1,7s)
somados a ~2,9s do `clicar_L_marcar` — cerca de **4,6s em média, ~6,3s no pior
caso**. Tirar o `sleep(2)` derrubaria o ciclo de busca de 3,43s para ~1,4s.

### Problema novo, não previsto: `stale element reference` (8 ocorrências)

Não estava em nenhuma hipótese de 30/07. Chrome 150.0.7871.187.

| Onde | Vezes |
|---|---|
| `Erro na etapa de varredura` | 6 |
| `Erro no Passo 3` | 1 |
| `Reconciliação falhou` / `Tabela mudou durante reconciliação` | 1 |

Cada uma **mata a etapa inteira** e joga para o ciclo seguinte. Uma delas
derrubou um Passo 3 — ou seja, é um caminho a mais para "fica marcado para
sempre", independente da lista de espera já corrigida.

### Atividade da sessão (para dimensionar)

6 marcações pelo Passo 2 (DX), 1 pelo Passo 1, 2 desmarcações pela reconciliação
(órfãos de sessão anterior — a persistência em `estado.json` funcionou).
27 das 37 checagens encerraram na hora por não haver ninguém em espera.

### Cuidado descoberto ao analisar

A ocultação de nome do `resumo.txt` depende das aspas em `'nome (data)'`. A linha
do Passo 1 (`automacao.py:480` e vizinhas) escreve `[Passo 1] NOME (data) — Mod...`
**sem aspas**. Hoje ela não entra no `resumo.txt` (não casa com o filtro), mas
qualquer mudança no filtro pode vazá-la. Ao analisar o `automacao.log` completo,
agregar com cuidado — foi assim que um nome apareceu na conversa em 31/07.

---

## O QUE FAZER AMANHÃ (31/07/2026) — outro computador

> **Concluído.** Ver a seção do log acima. Mantido por registrar o procedimento.

O objetivo é **coletar o log real**. Sem ele, qualquer otimização é chute — foi
o que já custou duas rodadas de defeitos.

1. Instalar **Git** e **Google Chrome**, se ainda não tiver.
2. No Prompt de Comando:
   ```
   git clone https://github.com/montemezzoartur/print-automacao.git
   cd print-automacao
   git checkout otimiza-marcacao
   ```
3. **Conferir**: rodar `git branch` e ver o asterisco em `otimiza-marcacao`.
   Um clone novo cai na `master` por padrão, e a `master` não tem o log — se
   rodar na `master`, o dia é perdido.
4. Duplo clique em **`instalar.bat`**.
5. Preencher usuário e senha do PACS no Bloco de Notas que abrir, e salvar.
6. Usar o atalho **"Print Automacao"** da área de trabalho, ativar no modo mais
   usado e deixar rodar **15–20 minutos em horário de movimento**.
7. Fechar o app.

### Estado verificado em 31/07/2026 — `C:\Users\artur\Desktop\Projetos\Print`

Os passos 1 a 5 **já estão feitos** nesta máquina. Conferido por execução:

| Item | Situação |
|---|---|
| Python | 3.12.10 instalado |
| selenium | 4.21.0 instalado |
| `config.py` | existe, com `USUARIO='Artur'` e senha preenchida |
| Branch | `otimiza-marcacao` ativa |
| `test_automacao.py` | 45 testes, todos passaram |
| `iniciar.bat` | **não existe** (é gerado pelo `instalar.bat` e está no `.gitignore`) |
| `automacao.log` / `estado.json` | ainda não existem — vão nascer na primeira execução |

Como não há `iniciar.bat`, o jeito direto de abrir é `python main.py` na pasta
do projeto. Rodar o `instalar.bat` também funciona e é seguro — ele só cria o
`config.py` `if not exist`, então não sobrescreve as credenciais.

Vai aparecer o `automacao.log` na pasta.

**Cuidado com esse arquivo:** ele contém nome de paciente e data de exame. Está
no `.gitignore` de propósito e **não pode ir para o GitHub** (o repositório é
acessível pela internet). Para extrair só o que interessa, sem dado de paciente,
rodar no PowerShell dentro da pasta do projeto:

```powershell
Get-Content automacao.log -Encoding UTF8 |
  Select-String -Pattern "\[tempo\]|PROBLEMA|ATEN|Erro" |
  ForEach-Object { $_.Line -replace "'[^']*\([0-9/]+\)'", "'[paciente oculto]'" } |
  Set-Content resumo.txt -Encoding UTF8
```

É o `resumo.txt` que interessa analisar.

> **Correção de 31/07/2026 — o comando anterior vazava nome de paciente.**
> A versão que estava aqui era
> `Select-String automacao.log -Pattern "..." | ForEach-Object { $_.Line } | Set-Content resumo.txt`.
> Testada com um log de exemplo, ela copiava a linha
> `ATENÇÃO: desmarcação falhou 3x seguidas em 'MARIA DA SILVA SANTOS (30/07/2026)'`
> inteira para o `resumo.txt` — porque `rotulo = f"{nome} ({data_exame})"`
> (`automacao.py:333`) carrega o nome do paciente. Somado a isso, `resumo.txt`
> **não estava no `.gitignore`** e o hook `Stop` roda `git add .` + `push`
> sozinho: o nome iria para um repositório público sem ninguém perceber.
> Duas correções: `resumo.txt` entrou no `.gitignore`, e o comando agora
> substitui `'nome (data)'` por `'[paciente oculto]'`.
> Os outros dois ajustes do comando: `Get-Content -Encoding UTF8` (o log é UTF-8
> sem BOM e o `Select-String` do PowerShell 5.1 assume ANSI) e `ATEN` no lugar de
> `ATENÇÃO` no padrão, para não depender de acento na comparação.

**Se der problema:** `git checkout master` volta ao código antigo. Nada foi mesclado.

### O que procurar no log

| Linha | O que significa |
|---|---|
| `[tempo] clicar_L_marcar` perto de **20s** | Confirmaria a maior suspeita: o popup "Sim" não aparece e o código queima 4 seletores de 5s cada. Seria a maior parte do problema de velocidade, com correção pequena e dirigida. |
| `[tempo] passo3_desmarcar` perto de **30s** | Explicaria a desmarcação falhando: a etapa de checagem inteira só tem 30s de orçamento. |
| `[tempo] buscar_exames` | O piso era 2,0s por causa de um `sleep` fixo. Ver quanto é de verdade. |
| `PROBLEMA GRAVE: coluna ... não encontrada` | A reconciliação (única rede de segurança contra exames órfãos) nunca rodou. |
| `ATENÇÃO: desmarcação falhou 3x` | Denuncia o exame específico que está travado. |

---

## PROBLEMAS RELATADOS PELO USUÁRIO (ainda em aberto)

1. **Perdendo marcações.** Quando surge um DX novo, o app tenta marcar mas
   alguém já pegou. O app *vê* o exame; é lento no clique. Suspeita de que
   outra pessoa usa um script mais rápido.
2. **Desmarcação não funciona.** Exames marcados pelo Passo 2 cujo convênio
   depois não bate ficam com o nome do usuário **para sempre**.

O problema 2 teve sua causa principal atacada (a lista sumia ao fechar o app).
O problema 1 continua intocado, por decisão consciente — ver histórico.

---

## HISTÓRICO DA SESSÃO (30/07/2026)

### Parte 1 — arrumação do repositório

- **`CLAUDE.md` reescrito.** Estava com erros graves: dizia que o app usava
  Microsoft Edge (usa **Chrome**, `webdriver.Chrome`), falava em "a cada 30
  segundos" (não existe esse intervalo), citava um botão ATIVAR/DESATIVAR
  (são **três** botões: CT e DX, CT, DX) e descrevia funções que não existem
  mais (`_buscar_e_processar`, `_processar_tabela`). A seção "Fluxo da
  automação" foi reescrita do zero e cada afirmação verificada contra o código.
- **Removida a cópia do CLAUDE.md global** que estava colada no fim do arquivo
  do projeto (era carregada duas vezes).
- **Limpeza do repositório:** 59 arquivos de skills de ferramentas de IA
  (`.agents/`, `.claude/skills/`, `.cursor/`, `.windsurf/`) saíram do controle
  do Git e entraram no `.gitignore`. Continuam no disco.
- **Código morto apagado:** `instalar_driver.bat` (baixava driver do Edge),
  `INTERVALO_SEGUNDOS` no `config.py` (nunca lido) e `webdriver-manager` no
  `requirements.txt` (nunca importado — o Selenium 4.21 já traz o Selenium
  Manager, que baixa o driver sozinho).
- **Skills instaladas no escopo do projeto:** `ponytail`, `ponytail-audit`,
  `ponytail-review` (versionadas, viajam com o repositório) e `graphify`
  (não versionada — o instalador dele coloca a skill no lugar).
- **Repositório tornado portável**, porque o projeto vai ser usado em dois
  computadores:
  - hooks do `.claude/settings.json` deixaram de ter caminho fixo desta
    máquina; o de commit automático descobre a raiz com
    `git rev-parse --show-toplevel`, e os do graphify usam `%USERPROFILE%`
    com `Test-Path` (se o graphify não existir no outro PC, o hook sai limpo
    em vez de quebrar toda leitura de arquivo)
  - `iniciar.bat` saiu do Git (é gerado pelo `instalar.bat` com o caminho do
    Python de cada máquina; se ficasse versionado, os dois PCs ficariam
    sobrescrevendo o arquivo um do outro)
  - `Print Automação.lnk` saiu do Git (atalho com caminho absoluto)
  - `graphify-out/cache/` saiu do Git

**Descoberta importante:** existe um hook `Stop` no `.claude/settings.json` que
roda `git add . / commit / push` automaticamente ao fim de cada resposta do
Claude Code. É a origem dos commits "auto: atualizacao via Claude Code".

### Parte 2 — diagnóstico dos dois problemas

Feito lendo o `automacao.py` inteiro (722 linhas na época).

**Problema 1 — custo garantido de ~7 segundos por marcação de DX:**

| Custo | Onde | Tempo |
|---|---|---|
| Espera fixa após Buscar Exames | `_clicar_buscar_exames` | 2,0s |
| Esperas fixas no clique do "L" | `_clicar_icone_l` | 2,3s |
| Espera fixa entre ações | laços `_ate_esgotar` | 1,0s |
| Leitura da tabela célula a célula | `_txt` | ~1–3s |

Cada `.text` do Selenium é uma ida e volta ao navegador: ~210 por varredura.

**Risco não confirmado:** as buscas por elemento tentam seletores em fila e
**cada um que falha gasta o tempo limite inteiro**. `_confirmar_popup` tem 4
seletores de 5s = até **20s parados por marcação** se o popup não aparecer.
`_executar_passo3` tem 4 de 8s = até **32s**, mais que os 30s de toda a etapa
de checagem. **Isso continua não confirmado — é o que o log de amanhã vai dizer.**

**Problema 2 — quatro causas possíveis para "fica marcado para sempre":**
1. A lista de espera vivia só na memória — fechar o app apagava tudo. *(corrigido)*
2. A reconciliação aborta inteira e **calada** se faltar a coluna Laudo ou
   Realizante — e ela é a única rede de segurança contra órfãos. *(agora avisa)*
3. A checagem desistia na primeira passada vazia, empurrando a desmarcação para
   o ciclo seguinte (~90s depois). *(revertido — ver abaixo)*
4. Uma falha do Passo 3 pode estourar o orçamento de 30s da etapa inteira. *(não atacado)*

### Parte 3 — as duas tentativas de otimização, e por que foram desfeitas

**Tentativa 1** (commits `f1e91ce`, `48998db`, `07d8c92`, `f4d9998`):
- Fase 0: log em arquivo + cronômetros
- Fase 1.1: ler a tabela inteira numa chamada JavaScript e reencontrar a linha
  por índice na hora de clicar
- Fase 1.2/1.3: orçamento de tempo total nas buscas, fim das esperas fixas
- Fase 2: persistência das listas, checagem sem desistir cedo

**Revisão encontrou 12 defeitos, 4 críticos.** Quatro foram verificados por
execução direta do código:
- a "guarda de identidade" (criada pela Fase 1.1) **liberava qualquer linha**
  quando faltavam as colunas Nome/Data — a comparação virava `('','')` dos dois
  lados. Risco real de clicar no **paciente errado**.
- cabeçalho duplicado (tabela oculta na página) **sobrescrevia** o índice da
  coluna, porque o `innerText` do JavaScript lê tabelas ocultas e o `.text` do
  Selenium devolvia vazio
- `innerText` e `.text` discordam num `&nbsp;` interno — travaria o app inteiro
- o `teto` do `_esperar_tabela_pronta` era código morto

**7 dos 12 defeitos vinham da Fase 1.1**, que rendia só ~2s dos ~7s de ganho.

**Tentativa 2** (commit `ea52da4`): desfez a Fase 1.1 e corrigiu os 5 restantes.

**Nova revisão encontrou 23 achados, 8 críticos** — pior que antes. Dois
verificados por execução:
- o `_esperar_tabela_pronta` que eu reescrevi ficou **pior** que o que ele veio
  corrigir: eu inicializava `ultima = antes` e nunca exigia que a assinatura
  mudasse, então ele liberava com a **tabela antiga** sempre que o PACS
  demorasse mais de 0,4s
- a correção do "laço quente" criou um caminho novo para "marcado para sempre":
  se o clique no "L" desse certo mas fechar a aba falhasse, `_clicar_icone_l`
  devolvia `False` e o chamador abortava **antes** de gravar a chave na lista.
  Para CT crânio não há rede de segurança (a reconciliação só olha DX).

**Decisão (commit `ac1131d`): reduzir ao núcleo seguro.** O `automacao.py` foi
reconstruído a partir da `master` e só as partes comprovadamente seguras foram
reaplicadas.

**Motivo da decisão, para não repetir:** duas rodadas, e nas duas os defeitos
críticos nasceram nos **mesmos dois lugares** — a lógica de tempo e o tratamento
do clique. Escrever otimização de tempo sem nunca ter visto um número real do
app rodando não funcionou. A velocidade volta ao assunto **depois** do log.

### Parte 4 — correções que sobreviveram, apontadas pela revisão

- `_salvar_estado` grava num `.tmp` e usa `os.replace` (atômico). Gravar direto
  truncaria o arquivo antes de preenchê-lo, e uma falha nesse instante apagaria
  a lista — o oposto do objetivo.
- `_carregar_estado` recusa JSON que não seja dicionário, em vez de estourar
  `AttributeError` dentro do `__init__` e deixar o app "ATIVO" sem rodar nada.
- O filtro de pares exige lista: antes a string `"ab"` tinha tamanho 2 e virava
  o par `("a","b")` dentro da lista de espera.

---

## ITENS EM ABERTO

*(Lista de 30/07, com o estado de 31/07 anotado. Ordem de prioridade sugerida ao
fim do dia 31/07: primeiro acumular sessões — ver "COMEÇAR POR AQUI" no topo —
depois item 6, depois item 4.)*

1. **Velocidade (problema 1)** — ~~nada foi feito~~ **parcialmente atacado em
   31/07**: o `sleep(2)` virou espera adaptativa, economia de ~1,6s na busca que
   detecta a mudança (o caminho crítico). Restam 93% das buscas custando o teto
   de 2,0s, mas **reduzir esse teto é adivinhação** — quando o conteúdo é
   idêntico a assinatura não muda e não há medição possível do tempo real.
   O problema não está resolvido, só melhorado.
2. **Colisão de chave.** A identidade de um exame é `(nome, data do exame)`.
   Dois exames do mesmo paciente na mesma data ficam indistinguíveis. Como a
   lista agora persiste em disco, o bloqueio virou permanente onde antes sumia
   ao reabrir o app. Solução provável: usar a coluna ID da grade.
3. **`_avisar_uma_vez` engole o aviso** se o mesmo problema reaparecer na mesma
   sessão, e a reconciliação ainda anuncia "nenhum exame órfão encontrado"
   mesmo tendo abortado.
4. **Falha do Passo 3 pode estourar o orçamento da checagem** (causa 4 do
   problema 2) — não atacada.
5. **Ideia registrada para o futuro:** falar direto com a API do PACS em vez de
   passar pelo navegador. Sairia de segundos para milissegundos. Investigação:
   abrir o PACS no Chrome, F12, aba **Network**, clicar no "L" e observar a
   requisição; repetir para o "Salvar" do popup. Depois reaproveitar os cookies
   da sessão do Selenium com a biblioteca `requests`. **Riscos a pesar:** é API
   interna e não documentada, pode mudar sem aviso; e vale confirmar se esse uso
   é aceitável nas regras da Print Imagem.
6. **`stale element reference`** *(novo, descoberto em 31/07)*. 8 ocorrências na
   1ª sessão, 2 na 2ª. Cada uma **mata a etapa inteira** — 6 derrubaram a
   varredura, 1 derrubou um Passo 3 (mais um caminho para "marcado para sempre"),
   1 derrubou a reconciliação. É o alvo com melhor retorno depois da coleta,
   **mas 2 eventos não bastam para atacar.** Daí as sessões extras do topo.

---

## APRENDIZADOS DE 31/07/2026

- **Medir também serve para saber onde o problema NÃO está.** As três hipóteses
  de 30/07 (popup queimando 20s, Passo 3 queimando 30s, coluna não encontrada)
  vieram de ler código e somar tempos limite no papel. **Nenhuma se confirmou.**
  Otimizar em cima delas teria sido a terceira rodada perdida.
- **O code review pegou um defeito crítico que 53 testes verdes não pegaram.**
  Com `antes=None`, a guarda de mudança virava letra morta e a espera liberava
  com a tabela pré-busca — o mesmo defeito de `ea52da4` entrando por outra porta.
  Rodar teste **não substitui** revisão. Confirma a regra do CLAUDE.md do projeto.
- **Instrumentar responde o que raciocinar não responde.** O risco "a tabela pode
  renderizar em etapas" era indecidível na discussão. Uma linha de log
  (`[tabela] antes -> depois`) fechou a questão numa sessão: 29 liberações, todas
  com 43 linhas antes e 43 depois. Quando uma dúvida travar a decisão, medir sai
  mais barato que debater.
- **Mutante que sobrevive nem sempre é falha de teste.** `ultima = antes` sozinho
  sobreviveu à bateria — e está certo, porque a guarda `agora == antes` continua
  barrando a tabela antiga. É um *mutante equivalente*. Antes de escrever teste
  novo, checar se a mutação realmente muda o comportamento.
- **Arquivo derivado do log entra no `.gitignore` ANTES de ser criado.** O mesmo
  descuido apareceu três vezes num dia: o comando de extração copiava nome de
  paciente para o `resumo.txt`; a classe de teste nova escrevia no `automacao.log`
  real por não herdar `SemNavegador`; e `automacao_antes.log` ia escapar do
  padrão de nome exato. Com o hook `Stop` fazendo `git add .` num repositório
  público, cada um desses era um vazamento a um passo de acontecer.
- **Declarar a expectativa antes de medir evita autoengano depois.** Ficou
  registrado, antes da coleta, que o ganho seria pequeno no total porque busca com
  resultado idêntico continuaria custando o teto. Deu 6,8% de buscas rápidas e ~4%
  de economia total. Sem esse registro prévio, seria fácil vender os 1,6s do
  caminho crítico como se fossem ganho geral.

---

## APRENDIZADOS DA SESSÃO DE 30/07/2026

- **Sem medição, não otimizar.** Duas rodadas de defeitos críticos vieram de
  escrever otimização de tempo no escuro.
- **Teste de mutação vale a pena.** Quebrar a lógica de propósito e conferir se
  a suíte reprova pegou, **duas vezes**, testes meus que passavam sem testar
  nada. O padrão do erro: o teste tirava os dados da própria constante que
  deveria estar verificando; alterada a constante, o laço rodava em vazio. Na
  segunda vez o laço virou um bilhão de voltas e travou o processo. **Regra:
  usar valor literal no teste e comparar com a constante numa asserção
  explícita.**
- **Revisão xhigh com 84 agentes morreu no limite de sessão** — 47 falharam,
  inclusive todos os céticos, e o resultado veio rotulado como "confirmado" sem
  que ninguém tivesse verificado. Revisão média com 6–8 agentes terminou sem
  erro e produziu achados comprovados por execução. **Preferir o formato médio.**
- **Não confiar em veredicto de agente sem verificar.** A rodada xhigh
  "refutou" um defeito que eu provei verdadeiro rodando o código.
- **A garantia que o Selenium dá de graça:** segurar o `WebElement` da linha
  desde a leitura até o clique faz o próprio Selenium avisar (com
  `StaleElementReferenceException`) quando a tabela muda. Trocar isso por
  "reencontrar a linha pelo índice" transferiu para o código uma
  responsabilidade que ele não conseguiu cumprir.
