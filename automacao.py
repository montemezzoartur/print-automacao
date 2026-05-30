import re
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException, NoSuchElementException,
    NoAlertPresentException, StaleElementReferenceException,
)
import config


class Automacao:
    def __init__(self, log_callback=None):
        self.driver = None
        self.rodando = False
        self._log_fn = log_callback or print
        self.ids_passo2 = set()
        self.ids_passo3 = set()
        self.modo = "AMBOS"

    def log(self, msg):
        hora = datetime.now().strftime("%H:%M:%S")
        self._log_fn(f"[{hora}] {msg}")

    def iniciar(self, modo="AMBOS"):
        self.modo = modo if modo in ("AMBOS", "CT", "DX") else "AMBOS"
        self.rodando = True
        try:
            if not self.driver:
                self._abrir_navegador()
                self._fazer_login()
                self.log(f"Login realizado. Modo: {self.modo}.")
            else:
                self.log(f"Retomando sessão existente. Modo: {self.modo}.")
            self._loop_principal()
        except Exception as e:
            self.log(f"Erro fatal: {e}")
            self._fechar_navegador()

    def parar(self):
        self.rodando = False
        self.log("Automação pausada. Navegador mantido aberto.")

    def _fechar_navegador(self):
        if self.driver:
            try:
                self.driver.quit()
            except Exception:
                pass
            self.driver = None
        self.log("Automação encerrada.")

    def _abrir_navegador(self):
        options = Options()
        self.driver = webdriver.Chrome(options=options)
        self.driver.maximize_window()
        self.driver.get(config.URL)
        self.log("Navegador aberto.")

    def _fazer_login(self):
        self.log("Realizando login automático...")
        wait = WebDriverWait(self.driver, 20)

        campo_usuario = self._encontrar_elemento(wait, [
            (By.XPATH, "//input[@placeholder='Usuário' or @placeholder='Usuario']"),
            (By.XPATH, "//input[@name='usuario' or @name='username' or @name='user']"),
            (By.XPATH, "//input[@id='usuario' or @id='username' or @id='user']"),
            (By.XPATH, "//input[@type='text']"),
        ])
        if not campo_usuario:
            raise Exception("Campo de usuário não encontrado na tela de login.")

        campo_senha = self._encontrar_elemento(wait, [
            (By.XPATH, "//input[@type='password']"),
            (By.XPATH, "//input[@placeholder='Senha']"),
            (By.XPATH, "//input[@name='senha' or @name='password']"),
        ])
        if not campo_senha:
            raise Exception("Campo de senha não encontrado na tela de login.")

        campo_usuario.clear()
        campo_usuario.send_keys(config.USUARIO)
        campo_senha.clear()
        campo_senha.send_keys(config.SENHA)

        botao = self._encontrar_elemento(wait, [
            (By.XPATH, "//button[contains(normalize-space(.),'Acessar sua conta')]"),
            (By.XPATH, "//button[contains(normalize-space(.),'Acessar')]"),
            (By.XPATH, "//button[@type='submit']"),
            (By.XPATH, "//input[@type='submit']"),
        ], clicavel=True)
        if not botao:
            raise Exception("Botão 'Acessar sua conta' não encontrado.")

        try:
            botao.click()
        except Exception:
            self.driver.execute_script("arguments[0].click();", botao)

        try:
            WebDriverWait(self.driver, 30).until(lambda d: "login" not in d.current_url.lower())
        except TimeoutException:
            raise Exception("Login não foi concluído (URL ainda contém 'login' após 30s).")

    def _loop_principal(self):
        if self.modo == "CT":
            self._loop_ct_only()
            return
        while self.rodando:
            try:
                self._etapa_reconciliacao()
            except Exception as e:
                self.log(f"Erro na etapa de reconciliação: {e}")
            if not self.rodando:
                return
            try:
                self._etapa_varredura()
            except Exception as e:
                self.log(f"Erro na etapa de varredura: {e}")
            if not self.rodando:
                return
            try:
                self._etapa_checagem()
            except Exception as e:
                self.log(f"Erro na etapa de checagem: {e}")

    def _loop_ct_only(self):
        self.log("=== MODO CT — varredura contínua (10s ou após cada ação) ===")
        while self.rodando:
            try:
                if not self._clicar_buscar_exames():
                    self._aguardar_ate(time.time() + 10)
                    continue
                agiu = self._executar_passo1_uma_acao()
                if not self.rodando:
                    return
                if not agiu:
                    self._aguardar_ate(time.time() + 10)
            except Exception as e:
                self.log(f"Erro no loop CT: {e}")
                self._aguardar_ate(time.time() + 10)

    # ---------- ETAPAS ----------

    def _etapa_reconciliacao(self):
        max_acoes = 10
        self.log("=== ETAPA DE RECONCILIAÇÃO (órfãos de sessões anteriores) ===")
        if not self._clicar_buscar_exames():
            return
        acoes = 0
        while self.rodando and acoes < max_acoes:
            if not self._reconciliar_uma_acao():
                break
            acoes += 1
        if acoes == 0:
            self.log("  Nenhum exame órfão encontrado.")
        else:
            self.log(f"  Reconciliação concluída — {acoes} exame(s) regularizado(s).")

    def _reconciliar_uma_acao(self):
        cols = self._detectar_colunas()
        if cols is None:
            return False
        if cols.get("realizante", -1) < 0:
            self.log("  Coluna Realizante não localizada — reconciliação abortada.")
            return False
        if cols.get("laudo", -1) < 0:
            self.log("  Coluna Laudo não localizada — reconciliação abortada.")
            return False

        linhas = self._linhas_seguras()
        if linhas is None:
            return False

        alvo_realizante = config.REALIZANTE_NOME.upper()

        for i, linha in enumerate(linhas):
            try:
                colunas = linha.find_elements(By.TAG_NAME, "td")
                if not self._cols_validas(colunas, cols):
                    continue

                mod = self._txt(colunas, cols["mod"])
                if "DX" not in mod:
                    continue

                realizante = self._txt(colunas, cols["realizante"])
                if alvo_realizante not in realizante:
                    continue

                convenio = self._txt(colunas, cols["convenio"])
                if not convenio.strip():
                    continue

                descricao = self._txt(colunas, cols["descricao"])
                if self._convenio_bate_dx(convenio, descricao):
                    continue

                nome = self._txt(colunas, cols["nome"], upper=False)
                data_exame = self._txt(colunas, cols["data_exame"], upper=False)
                rotulo = f"{nome} ({data_exame})"

                laudo = self._txt(colunas, cols["laudo"], upper=False)
                if laudo.strip():
                    self.log(f"[Reconciliação] '{rotulo}' — Laudo preenchido ('{laudo}'). Ignorado.")
                    continue

                self.log(f"[Reconciliação] '{rotulo}' — Conv='{convenio}' NÃO bate parâmetros DX. Removendo realizante órfão.")
                ok = self._executar_passo3(linha, colunas, cols)
                if ok:
                    chave = (nome, data_exame)
                    self.ids_passo2.discard(chave)
                    self.ids_passo3.add(chave)
                    return True
                else:
                    self.log(f"  Reconciliação falhou para '{rotulo}'.")

            except StaleElementReferenceException:
                self.log("  Tabela mudou durante reconciliação — reiniciando.")
                return self._reconciliar_uma_acao()
            except Exception as e:
                self.log(f"  Erro reconciliação linha {i+1}: {e}")
                continue

        return False

    def _etapa_varredura(self):
        duracao = config.VARREDURA_DURACAO_SEG
        n_verif = config.VARREDURA_VERIFICACOES
        slot = duracao / n_verif

        self.log(f"=== ETAPA DE VARREDURA ({duracao}s, {n_verif} verificações) ===")
        inicio = time.time()
        fim = inicio + duracao

        for i in range(n_verif):
            if not self.rodando or time.time() >= fim:
                break
            self.log(f"-- Verificação {i+1}/{n_verif} --")
            slot_fim = inicio + (i + 1) * slot

            self._executar_passo1_ate_esgotar(fim)
            if not self.rodando or time.time() >= fim:
                break
            self._executar_passo2_ate_esgotar(fim)

            self._aguardar_ate(min(slot_fim, fim))

    def _etapa_checagem(self):
        duracao = config.CHECAGEM_DURACAO_SEG
        max_acoes = config.CHECAGEM_MAX_ACOES

        if not self.ids_passo2:
            self.log("=== ETAPA DE CHECAGEM — nenhum exame em espera, encerrando imediatamente ===")
            return

        self.log(f"=== ETAPA DE CHECAGEM (limite {duracao}s e {max_acoes} ações, exames em espera: {sorted(self.ids_passo2)}) ===")
        inicio = time.time()
        fim = inicio + duracao
        acoes = 0

        while self.rodando and acoes < max_acoes and time.time() < fim:
            if not self._clicar_buscar_exames():
                break
            agiu, removidos = self._checar_ids_aguardando()
            if removidos:
                self.log(f"  Exames encerrados sem ação (Conv. bateu parâmetros): {removidos}")
            if agiu:
                acoes += 1
                self.log(f"  Ações na checagem: {acoes}/{max_acoes}")
            if not self.ids_passo2:
                self.log("  Sem exames em espera — encerrando checagem antecipadamente.")
                break
            if not agiu and not removidos:
                self.log("  Nenhum exame cumpre critérios — encerrando checagem antecipadamente.")
                break

    # ---------- PASSO 1 ----------

    def _executar_passo1_ate_esgotar(self, deadline):
        while self.rodando and time.time() < deadline:
            if not self._clicar_buscar_exames():
                return
            if not self._executar_passo1_uma_acao():
                return
            time.sleep(1)

    def _executar_passo1_uma_acao(self):
        cols = self._detectar_colunas()
        if cols is None:
            return False

        linhas = self._linhas_seguras()
        if linhas is None:
            return False

        if self.modo == "CT":
            mods_filtro = ["CT"]
        elif self.modo == "DX":
            mods_filtro = ["DX"]
        else:
            mods_filtro = config.MODS_ALVO

        for i, linha in enumerate(linhas):
            try:
                colunas = linha.find_elements(By.TAG_NAME, "td")
                if not self._cols_validas(colunas, cols):
                    continue

                mod = self._txt(colunas, cols["mod"])
                convenio = self._txt(colunas, cols["convenio"])
                descricao = self._txt(colunas, cols["descricao"])
                realizante = self._txt(colunas, cols["realizante"], upper=False)
                nome = self._txt(colunas, cols["nome"], upper=False)
                data_exame = self._txt(colunas, cols["data_exame"], upper=False)

                mod_ok = any(m in mod for m in mods_filtro)
                if not mod_ok:
                    continue

                idade = self._extrair_idade(nome)
                if "CT" in mod and ("CRANIO" in descricao or "CRÂNIO" in descricao) and idade is not None and idade <= 45:
                    elegivel = True
                    motivo = f"CT crânio, idade {idade} <= 45"
                elif "ANGIO" in descricao:
                    elegivel = "UNIMED" not in convenio
                    motivo = f"ANGIO (Conv: {convenio or 'vazio'})"
                elif "CT" in mod and any(t in descricao for t in ("TEP", "CAROTIDA", "CARÓTIDA")):
                    elegivel = "UNIMED" not in convenio
                    motivo = f"CT especial (Conv: {convenio or 'vazio'})"
                else:
                    conv_ok = any(c.upper() in convenio for c in config.CONVENIOS_ALVO)
                    if conv_ok and "SAS" in convenio and "CT" in mod:
                        conv_ok = False
                    if conv_ok and "FLIP" in convenio and "CT" in mod:
                        conv_ok = False
                    if conv_ok and "ARAMART" in convenio and "CT" in mod:
                        conv_ok = False
                    if conv_ok and "AVICOLA" in convenio and "CT" in mod:
                        conv_ok = False
                    if conv_ok and "HI-MIX" in convenio and "CT" in mod:
                        conv_ok = False
                    elegivel = conv_ok
                    motivo = f"Conv: {convenio}"

                if not elegivel:
                    continue

                if realizante.strip():
                    continue

                self.log(f"[Passo 1] {nome} ({data_exame}) — Mod {mod} | {motivo}")
                self._clicar_icone_l(linha, colunas, cols["acoes"])
                return True

            except StaleElementReferenceException:
                self.log("  Tabela mudou durante Passo 1 — reiniciando.")
                return self._executar_passo1_uma_acao()
            except Exception as e:
                self.log(f"  Erro Passo 1 linha {i+1}: {e}")
                continue

        return False

    # ---------- PASSO 2 ----------

    def _executar_passo2_ate_esgotar(self, deadline):
        while self.rodando and time.time() < deadline:
            if not self._clicar_buscar_exames():
                return
            if not self._executar_passo2_uma_acao():
                return
            time.sleep(1)

    def _executar_passo2_uma_acao(self):
        cols = self._detectar_colunas()
        if cols is None:
            return False

        linhas = self._linhas_seguras()
        if linhas is None:
            return False

        for i, linha in enumerate(linhas):
            try:
                colunas = linha.find_elements(By.TAG_NAME, "td")
                if not self._cols_validas(colunas, cols):
                    continue

                mod = self._txt(colunas, cols["mod"])
                convenio = self._txt(colunas, cols["convenio"])
                realizante = self._txt(colunas, cols["realizante"], upper=False)
                nome = self._txt(colunas, cols["nome"], upper=False)
                data_exame = self._txt(colunas, cols["data_exame"], upper=False)
                chave = (nome, data_exame)

                if "DX" not in mod:
                    continue
                if convenio.strip():
                    continue
                if realizante.strip():
                    continue
                if (nome or data_exame) and chave in self.ids_passo3:
                    continue

                self.log(f"[Passo 2] '{nome} ({data_exame})' — Mod {mod} (Conv. e Realizante vazios)")
                self._clicar_icone_l(linha, colunas, cols["acoes"])
                if nome or data_exame:
                    self.ids_passo2.add(chave)
                    self.log(f"  '{nome} ({data_exame})' gravado. ids_passo2 agora: {sorted(self.ids_passo2)}")
                else:
                    self.log("  ATENÇÃO: Nome/Data do exame vazios — não foi possível gravar para checagem.")
                return True

            except StaleElementReferenceException:
                self.log("  Tabela mudou durante Passo 2 — reiniciando.")
                return self._executar_passo2_uma_acao()
            except Exception as e:
                self.log(f"  Erro Passo 2 linha {i+1}: {e}")
                continue

        return False

    # ---------- PASSO 3 (CHECAGEM) ----------

    def _checar_ids_aguardando(self):
        """Percorre a tabela uma vez. Para cada ID em ids_passo2 encontrado:
        - Convênio vazio: mantém em espera.
        - Convênio bate Passo 1: remove da espera.
        - Convênio NÃO bate: executa Passo 3, move para ids_passo3.
        Retorna (agiu_bool, lista_de_ids_removidos_sem_acao)."""
        cols = self._detectar_colunas()
        if cols is None:
            return False, []

        linhas = self._linhas_seguras()
        if linhas is None:
            return False, []

        ids_alvo = set(self.ids_passo2)
        ids_vistos = set()
        removidos = []
        for i, linha in enumerate(linhas):
            try:
                colunas = linha.find_elements(By.TAG_NAME, "td")
                if not self._cols_validas(colunas, cols):
                    continue

                nome = self._txt(colunas, cols["nome"], upper=False)
                data_exame = self._txt(colunas, cols["data_exame"], upper=False)
                chave = (nome, data_exame)
                if not (nome or data_exame) or chave not in ids_alvo:
                    continue
                ids_vistos.add(chave)
                rotulo = f"{nome} ({data_exame})"

                mod = self._txt(colunas, cols["mod"])
                convenio = self._txt(colunas, cols["convenio"])
                descricao = self._txt(colunas, cols["descricao"])

                if not convenio.strip():
                    self.log(f"  '{rotulo}': Conv. ainda vazio → mantém em espera.")
                    continue

                if self._convenio_bate_dx(convenio, descricao):
                    self.log(f"  '{rotulo}': Conv='{convenio}' bate parâmetros DX → encerrado sem ação.")
                    self.ids_passo2.discard(chave)
                    removidos.append(rotulo)
                    continue

                self.log(f"[Passo 3] '{rotulo}' — Conv='{convenio}' NÃO bate parâmetros. Removendo realizante.")
                ok = self._executar_passo3(linha, colunas, cols)
                if ok:
                    self.ids_passo2.discard(chave)
                    self.ids_passo3.add(chave)
                    return True, removidos
                else:
                    self.log(f"  Passo 3 falhou para '{rotulo}' — manterá em espera.")

            except StaleElementReferenceException:
                self.log("  Tabela mudou durante checagem — reiniciando.")
                return self._checar_ids_aguardando()
            except Exception as e:
                self.log(f"  Erro checagem linha {i+1}: {e}")
                continue

        nao_encontrados = ids_alvo - ids_vistos
        if nao_encontrados:
            self.log(f"  Exames em espera não encontrados na tabela: {sorted(nao_encontrados)}")
        return False, removidos

    def _convenio_bate_dx(self, convenio, descricao):
        if "ANGIO" in descricao:
            return "UNIMED" not in convenio
        return any(c.upper() in convenio for c in config.CONVENIOS_ALVO)

    def _executar_passo3(self, linha, colunas, cols):
        try:
            col_realizante = cols["realizante"]
            if col_realizante < 0 or col_realizante >= len(colunas):
                self.log("  Coluna Realizante não encontrada.")
                return False

            celula = colunas[col_realizante]
            alvo_clique = None
            for sel in [
                f".//a[contains(normalize-space(.),'{config.REALIZANTE_NOME}')]",
                f".//span[contains(normalize-space(.),'{config.REALIZANTE_NOME}')]",
                f".//*[contains(normalize-space(.),'{config.REALIZANTE_NOME}')]",
            ]:
                try:
                    alvo_clique = celula.find_element(By.XPATH, sel)
                    break
                except NoSuchElementException:
                    continue

            if alvo_clique is None:
                alvo_clique = celula

            self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", alvo_clique)
            time.sleep(0.3)
            self.driver.execute_script("arguments[0].click();", alvo_clique)

            wait = WebDriverWait(self.driver, 8)
            modal = None
            for sel in [
                "//div[contains(@class,'modal') and (contains(.,'Editar realizante') or contains(.,'realizante'))]",
                "//div[contains(@class,'modal-content')]",
                "//div[@role='dialog']",
                "//div[contains(@class,'modal')]",
            ]:
                try:
                    modal = wait.until(EC.visibility_of_element_located((By.XPATH, sel)))
                    break
                except TimeoutException:
                    continue

            if modal is None:
                self.log("  Popup 'Editar realizante' não apareceu.")
                return False

            checkbox = None
            for sel in [
                ".//label[contains(normalize-space(.),'Realizante')]//input[@type='checkbox']",
                ".//input[@type='checkbox' and following-sibling::*[contains(normalize-space(.),'Realizante')]]",
                ".//input[@type='checkbox' and preceding-sibling::*[contains(normalize-space(.),'Realizante')]]",
                ".//input[@type='checkbox']",
            ]:
                try:
                    checkbox = modal.find_element(By.XPATH, sel)
                    break
                except NoSuchElementException:
                    continue

            if checkbox is None:
                self.log("  Checkbox 'Realizante' não encontrado no popup.")
                return False

            if checkbox.is_selected():
                try:
                    checkbox.click()
                except Exception:
                    self.driver.execute_script("arguments[0].click();", checkbox)
                time.sleep(0.3)

            salvar = None
            for sel in [
                ".//button[normalize-space(.)='Salvar']",
                ".//button[contains(normalize-space(.),'Salvar')]",
                ".//input[@type='submit' and (@value='Salvar' or contains(@value,'Salvar'))]",
                ".//a[normalize-space(.)='Salvar']",
            ]:
                try:
                    salvar = modal.find_element(By.XPATH, sel)
                    break
                except NoSuchElementException:
                    continue

            if salvar is None:
                self.log("  Botão 'Salvar' não encontrado no popup.")
                return False

            try:
                salvar.click()
            except Exception:
                self.driver.execute_script("arguments[0].click();", salvar)
            time.sleep(1)
            self.log("  Realizante removido e salvo.")
            return True

        except Exception as e:
            self.log(f"  Erro no Passo 3: {e}")
            return False

    # ---------- AUXILIARES ----------

    def _detectar_colunas(self):
        headers = self.driver.find_elements(By.XPATH, "//table//th")
        cols = {"nome": -1, "data_exame": -1, "mod": -1, "convenio": -1, "acoes": -1, "realizante": -1, "descricao": -1, "laudo": -1}
        for i, h in enumerate(headers):
            t = h.text.strip().upper()
            if "NOME" in t:
                cols["nome"] = i
            elif "DATA" in t and "EXAME" in t:
                cols["data_exame"] = i
            elif "MOD" in t:
                cols["mod"] = i
            elif "CONV" in t:
                cols["convenio"] = i
            elif "AÇ" in t or t == "ACOES" or t == "AÇÕES":
                cols["acoes"] = i
            elif "REALIZ" in t:
                cols["realizante"] = i
            elif "DESCR" in t:
                cols["descricao"] = i
            elif "LAUDO" in t:
                cols["laudo"] = i

        if cols["mod"] == -1 or cols["convenio"] == -1:
            self.log("Colunas Mod./Convênio não identificadas.")
            return None
        if cols["nome"] == -1 or cols["data_exame"] == -1:
            self.log("Colunas Nome do paciente / Data do exame não identificadas — checagem fica limitada.")
        return cols

    def _linhas_seguras(self):
        try:
            return self.driver.find_elements(By.XPATH, "//table//tbody//tr")
        except Exception as e:
            self.log(f"Erro ao ler linhas: {e}")
            return None

    def _cols_validas(self, colunas, cols):
        indices = [v for v in cols.values() if v >= 0]
        if not indices:
            return False
        return len(colunas) > max(indices)

    def _txt(self, colunas, idx, upper=True):
        if idx < 0 or idx >= len(colunas):
            return ""
        t = colunas[idx].text.strip()
        return t.upper() if upper else t

    def _extrair_idade(self, nome):
        nums = re.findall(r"\d+", nome)
        if not nums:
            return None
        return int(nums[-1])

    def _aguardar_ate(self, ts_alvo):
        while self.rodando and time.time() < ts_alvo:
            time.sleep(0.5)

    def _clicar_buscar_exames(self):
        wait = WebDriverWait(self.driver, 10)
        botao = self._encontrar_elemento(wait, [
            (By.XPATH, "//button[contains(translate(.,'abcdefghijklmnopqrstuvwxyz','ABCDEFGHIJKLMNOPQRSTUVWXYZ'),'BUSCAR EXAME')]"),
            (By.XPATH, "//a[contains(translate(.,'abcdefghijklmnopqrstuvwxyz','ABCDEFGHIJKLMNOPQRSTUVWXYZ'),'BUSCAR EXAME')]"),
            (By.XPATH, "//*[contains(@id,'buscar') or contains(@name,'buscar')]"),
        ], clicavel=True)

        if not botao:
            self.log("Botão 'Buscar Exames' não encontrado.")
            return False

        try:
            botao.click()
        except Exception:
            self.driver.execute_script("arguments[0].click();", botao)
        time.sleep(2)
        return True

    def _clicar_icone_l(self, linha, colunas, col_acoes):
        try:
            alvo = colunas[col_acoes] if col_acoes >= 0 and col_acoes < len(colunas) else linha

            icone = None
            for sel in [
                ".//a[.//img[contains(@title,'Laudo') or contains(@title,'laudo')]]",
                ".//a[contains(@title,'Laudo') or contains(@title,'laudo')]",
                ".//a[normalize-space(text())='L']",
                ".//button[normalize-space(text())='L']",
                ".//img[contains(@title,'Laudo') or contains(@title,'laudo')]",
                ".//span[normalize-space(text())='L']",
            ]:
                try:
                    icone = alvo.find_element(By.XPATH, sel)
                    break
                except NoSuchElementException:
                    continue

            if not icone:
                self.log("Ícone 'L' não encontrado nesta linha.")
                return

            janelas_antes = set(self.driver.window_handles)
            self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", icone)
            time.sleep(0.3)
            self.driver.execute_script("arguments[0].click();", icone)
            time.sleep(1)

            self._confirmar_popup()
            time.sleep(1)

            novas = set(self.driver.window_handles) - janelas_antes
            for janela in novas:
                self.driver.switch_to.window(janela)
                self.driver.close()
                self.log("Aba extra fechada.")

            self.driver.switch_to.window(list(janelas_antes)[0])
            self.log("  Ação L concluída.")

        except Exception as e:
            self.log(f"Erro ao processar ícone L: {e}")

    def _confirmar_popup(self):
        try:
            alert = self.driver.switch_to.alert
            alert.accept()
            self.log("  Alerta confirmado.")
            return
        except NoAlertPresentException:
            pass

        wait = WebDriverWait(self.driver, 5)
        for by, sel in [
            (By.XPATH, "//button[normalize-space(text())='Sim']"),
            (By.XPATH, "//button[contains(text(),'Sim')]"),
            (By.XPATH, "//a[normalize-space(text())='Sim']"),
            (By.XPATH, "//input[@value='Sim']"),
        ]:
            try:
                btn = wait.until(EC.element_to_be_clickable((by, sel)))
                btn.click()
                self.log("  Popup confirmado com 'Sim'.")
                return
            except TimeoutException:
                continue

        self.log("  Popup não encontrado (pode ter fechado sozinho).")

    def _encontrar_elemento(self, wait, seletores, clicavel=False):
        for by, sel in seletores:
            try:
                cond = EC.element_to_be_clickable if clicavel else EC.presence_of_element_located
                return wait.until(cond((by, sel)))
            except TimeoutException:
                continue
        return None
