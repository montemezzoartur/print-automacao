import time
import threading
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

    def log(self, msg):
        hora = datetime.now().strftime("%H:%M:%S")
        self._log_fn(f"[{hora}] {msg}")

    def iniciar(self):
        self.rodando = True
        try:
            if not self.driver:
                self._abrir_navegador()
                self._aguardar_login_manual()
                self.log("Login detectado. Monitorando a cada 30s...")
            else:
                self.log("Retomando sessão existente. Monitorando a cada 30s...")
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

    def _aguardar_login_manual(self):
        self.log("Faça login manualmente no Chrome. Aguardando...")
        wait = WebDriverWait(self.driver, 300)
        try:
            wait.until(lambda d: "login" not in d.current_url.lower())
        except TimeoutException:
            raise Exception("Tempo de espera para login manual esgotado (5 min).")

    def _fazer_login(self):
        wait = WebDriverWait(self.driver, 15)

        campo_usuario = self._encontrar_elemento(wait, [
            (By.ID, "input-captchaems"),
            (By.NAME, "captchaems"),
            (By.NAME, "username"),
            (By.NAME, "user"),
            (By.NAME, "login"),
            (By.ID, "username"),
            (By.ID, "user"),
            (By.ID, "login"),
            (By.XPATH, "//input[@type='text']"),
            (By.XPATH, "//input[not(@type) or @type='email']"),
        ])
        if not campo_usuario:
            raise Exception("Campo de usuário não encontrado na página de login.")
        campo_usuario.clear()
        campo_usuario.send_keys(config.USUARIO)

        campo_senha = self._encontrar_elemento(wait, [
            (By.ID, "password1"),
            (By.XPATH, "//input[@type='password']"),
            (By.NAME, "password"),
            (By.NAME, "senha"),
            (By.ID, "password"),
            (By.ID, "senha"),
        ])
        if not campo_senha:
            raise Exception("Campo de senha não encontrado na página de login.")
        campo_senha.clear()
        campo_senha.send_keys(config.SENHA)

        botao_login = self._encontrar_elemento(wait, [
            (By.XPATH, "//button[@type='submit']"),
            (By.XPATH, "//input[@type='submit']"),
            (By.XPATH, "//button[contains(translate(text(),'abcdefghijklmnopqrstuvwxyz','ABCDEFGHIJKLMNOPQRSTUVWXYZ'),'ENTRAR')]"),
            (By.XPATH, "//button[contains(translate(text(),'abcdefghijklmnopqrstuvwxyz','ABCDEFGHIJKLMNOPQRSTUVWXYZ'),'LOGIN')]"),
            (By.XPATH, "//button[contains(translate(text(),'abcdefghijklmnopqrstuvwxyz','ABCDEFGHIJKLMNOPQRSTUVWXYZ'),'ACESSAR')]"),
        ], clicavel=True)

        if botao_login:
            botao_login.click()
        else:
            from selenium.webdriver.common.keys import Keys
            campo_senha.send_keys(Keys.RETURN)

        time.sleep(3)
        self.log("Login enviado.")

    def _loop_principal(self):
        while self.rodando:
            try:
                self._buscar_e_processar()
            except Exception as e:
                self.log(f"Erro no ciclo: {e}")
            for _ in range(config.INTERVALO_SEGUNDOS):
                if not self.rodando:
                    return
                time.sleep(1)

    def _buscar_e_processar(self):
        wait = WebDriverWait(self.driver, 10)

        botao = self._encontrar_elemento(wait, [
            (By.XPATH, "//button[contains(translate(.,'abcdefghijklmnopqrstuvwxyz','ABCDEFGHIJKLMNOPQRSTUVWXYZ'),'BUSCAR EXAME')]"),
            (By.XPATH, "//a[contains(translate(.,'abcdefghijklmnopqrstuvwxyz','ABCDEFGHIJKLMNOPQRSTUVWXYZ'),'BUSCAR EXAME')]"),
            (By.XPATH, "//*[contains(@id,'buscar') or contains(@name,'buscar')]"),
        ], clicavel=True)

        if not botao:
            self.log("Botão 'Buscar Exames' não encontrado.")
            return

        botao.click()
        self.log("Buscando exames...")
        time.sleep(2)
        self._processar_tabela()

    def _processar_tabela(self):
        headers = self.driver.find_elements(By.XPATH, "//table//th")
        col_mod, col_convenio, col_acoes, col_realizante = -1, -1, -1, -1

        for i, h in enumerate(headers):
            t = h.text.strip().upper()
            if "MOD" in t:
                col_mod = i
            elif "CONV" in t:
                col_convenio = i
            elif "AÇ" in t or t == "ACOES" or t == "AÇÕES":
                col_acoes = i
            elif "REALIZ" in t:
                col_realizante = i

        if col_mod == -1 or col_convenio == -1:
            self.log("Colunas 'Mod.' ou 'Convênio' não identificadas na tabela.")
            return

        processados = 0

        linhas = self.driver.find_elements(By.XPATH, "//table//tbody//tr")

        for linha in linhas:
            try:
                colunas = linha.find_elements(By.TAG_NAME, "td")
                if len(colunas) <= max(col_mod, col_convenio):
                    continue

                mod = colunas[col_mod].text.strip().upper()
                convenio = colunas[col_convenio].text.strip().upper()

                mod_ok = any(m in mod for m in config.MODS_ALVO)
                conv_ok = any(c.upper() in convenio for c in config.CONVENIOS_ALVO)

                if mod_ok and conv_ok:
                    if col_realizante >= 0 and col_realizante < len(colunas):
                        realizante = colunas[col_realizante].text.strip()
                        if realizante:
                            continue

                    self.log(f"Exame encontrado — Mod: {mod} | Convênio: {convenio}")
                    self._clicar_icone_l(linha, colunas, col_acoes)
                    processados += 1
                    time.sleep(1)

            except StaleElementReferenceException:
                break
            except Exception as e:
                self.log(f"Erro ao analisar linha: {e}")

        if processados == 0:
            self.log("Nenhum exame com os critérios definidos encontrado.")

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
            self.log("Ação concluída com sucesso.")

        except Exception as e:
            self.log(f"Erro ao processar ícone L: {e}")

    def _confirmar_popup(self):
        try:
            alert = self.driver.switch_to.alert
            alert.accept()
            self.log("Alerta do navegador confirmado.")
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
                self.log("Popup confirmado com 'Sim'.")
                return
            except TimeoutException:
                continue

        self.log("Popup não encontrado (pode já ter fechado automaticamente).")

    def _encontrar_elemento(self, wait, seletores, clicavel=False):
        for by, sel in seletores:
            try:
                cond = EC.element_to_be_clickable if clicavel else EC.presence_of_element_located
                return wait.until(cond((by, sel)))
            except TimeoutException:
                continue
        return None
