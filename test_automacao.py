"""Testes da lógica que não depende do navegador.

Rodar com:  python -m unittest test_automacao -v
"""
import os
import tempfile
import unittest

import automacao


class LogEmArquivo(unittest.TestCase):
    def setUp(self):
        self.arquivo = os.path.join(tempfile.mkdtemp(), "teste.log")
        self._original = automacao.LOG_ARQUIVO
        automacao.LOG_ARQUIVO = self.arquivo
        self.janela = []
        self.a = automacao.Automacao(log_callback=self.janela.append)

    def tearDown(self):
        automacao.LOG_ARQUIVO = self._original

    def _conteudo(self):
        with open(self.arquivo, encoding="utf-8") as f:
            return f.read()

    def test_log_vai_para_janela_e_arquivo(self):
        self.a.log("mensagem de teste")
        self.assertEqual(len(self.janela), 1)
        self.assertIn("mensagem de teste", self.janela[0])
        self.assertIn("mensagem de teste", self._conteudo())

    def test_so_arquivo_nao_polui_a_janela(self):
        self.a.log("apenas no arquivo", so_arquivo=True)
        self.assertEqual(self.janela, [])
        self.assertIn("apenas no arquivo", self._conteudo())

    def test_arquivo_guarda_a_data_completa(self):
        self.a.log("com data")
        primeira = self._conteudo().splitlines()[0]
        # formato: AAAA-MM-DD [HH:MM:SS] mensagem
        self.assertRegex(primeira, r"^\d{4}-\d{2}-\d{2} \[\d{2}:\d{2}:\d{2}\] com data$")

    def test_falha_ao_gravar_nao_derruba_a_automacao(self):
        automacao.LOG_ARQUIVO = os.path.join(self.arquivo, "pasta", "inexistente.log")
        self.a.log("nao deve levantar excecao")
        self.assertIn("nao deve levantar excecao", self.janela[0])


class Cronometro(unittest.TestCase):
    """O decorador @_cronometrar mede as funções lentas do Selenium."""

    class Fake:
        def __init__(self):
            self.linhas = []

        def log(self, msg, so_arquivo=False):
            self.linhas.append((msg, so_arquivo))

        @automacao._cronometrar("operacao")
        def devolve(self, valor):
            return valor

        @automacao._cronometrar("operacao")
        def explode(self):
            raise ValueError("erro proposital")

    def test_preserva_o_retorno_e_registra_o_tempo(self):
        f = self.Fake()
        self.assertEqual(f.devolve(42), 42)
        msg, so_arquivo = f.linhas[0]
        self.assertRegex(msg, r"^\[tempo\] operacao: \d+\.\d{2}s$")
        self.assertTrue(so_arquivo, "tempo deve ir só para o arquivo, não para a janela")

    def test_registra_o_tempo_mesmo_quando_a_funcao_falha(self):
        f = self.Fake()
        with self.assertRaises(ValueError):
            f.explode()
        self.assertEqual(len(f.linhas), 1, "o tempo tem que ser registrado mesmo com exceção")
        self.assertIn("[tempo] operacao:", f.linhas[0][0])


if __name__ == "__main__":
    unittest.main()
