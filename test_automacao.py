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


CABECALHOS = ["Nome do paciente", "Data do exame", "Mod.", "Convênio",
              "Descrição", "Realizante", "Laudo", "Ações"]


class SemNavegador(unittest.TestCase):
    """Base para testar a lógica pura, que não abre o Chrome."""

    def setUp(self):
        self._log_original = automacao.LOG_ARQUIVO
        automacao.LOG_ARQUIVO = os.path.join(tempfile.mkdtemp(), "teste.log")
        self.a = automacao.Automacao(log_callback=lambda _: None)

    def tearDown(self):
        automacao.LOG_ARQUIVO = self._log_original


class DetectarColunas(SemNavegador):
    def test_cabecalho_tipico_do_pacs(self):
        cols = self.a._detectar_colunas(CABECALHOS)
        self.assertEqual(cols, {"nome": 0, "data_exame": 1, "mod": 2, "convenio": 3,
                                "descricao": 4, "realizante": 5, "laudo": 6, "acoes": 7})

    def test_sem_coluna_mod_desiste(self):
        self.assertIsNone(self.a._detectar_colunas(["Nome", "Convênio"]))

    def test_sem_coluna_convenio_desiste(self):
        self.assertIsNone(self.a._detectar_colunas(["Nome", "Mod."]))

    def test_sem_nome_prossegue_com_aviso(self):
        cols = self.a._detectar_colunas(["Mod.", "Convênio"])
        self.assertIsNotNone(cols, "faltar Nome limita a checagem mas não impede marcar")
        self.assertEqual(cols["nome"], -1)

    def test_descricao_nao_e_confundida_com_acoes(self):
        # "DESCRIÇÃO" tem cedilha mas não contém "AÇ" — a ordem dos elif importa
        cols = self.a._detectar_colunas(["Mod.", "Convênio", "Descrição", "Ações"])
        self.assertEqual(cols["descricao"], 2)
        self.assertEqual(cols["acoes"], 3)


class LeituraDeCelulas(SemNavegador):
    def test_texto_normal_vem_em_maiuscula(self):
        self.assertEqual(self.a._txt(["joão silva"], 0), "JOÃO SILVA")

    def test_upper_false_preserva(self):
        self.assertEqual(self.a._txt(["joão silva"], 0, upper=False), "joão silva")

    def test_indice_fora_da_linha_devolve_vazio(self):
        self.assertEqual(self.a._txt(["a", "b"], 5), "")

    def test_coluna_inexistente_devolve_vazio(self):
        self.assertEqual(self.a._txt(["a"], -1), "")

    def test_linha_curta_demais_e_descartada(self):
        cols = self.a._detectar_colunas(CABECALHOS)
        self.assertTrue(self.a._cols_validas(["a"] * 8, cols))
        self.assertFalse(self.a._cols_validas(["a"] * 3, cols))

    def test_idade_e_o_ultimo_numero_do_nome(self):
        self.assertEqual(self.a._extrair_idade("MARIA SOUZA 37"), 37)
        self.assertEqual(self.a._extrair_idade("JOSE 2 SILVA 61"), 61)
        self.assertIsNone(self.a._extrair_idade("SEM NUMERO"))


class RegrasDoPasso1(SemNavegador):
    """As regras de elegibilidade — a lógica de negócio mais mexida do projeto."""

    def setUp(self):
        super().setUp()
        self._convenios = automacao.config.CONVENIOS_ALVO
        automacao.config.CONVENIOS_ALVO = ["CCEST", "PARTICULAR", "SAS", "HI-MIX"]

    def tearDown(self):
        automacao.config.CONVENIOS_ALVO = self._convenios
        super().tearDown()

    def avaliar(self, mod, convenio, descricao, nome="PACIENTE 30", ja_desmarcado=False):
        return self.a._avaliar_passo1(mod, convenio, descricao, nome, ja_desmarcado)

    # --- CT crânio ---
    def test_ct_cranio_ate_45_e_marcado(self):
        elegivel, ct, _ = self.avaliar("CT", "", "CRANIO SIMPLES", nome="ANA 45")
        self.assertTrue(elegivel)
        self.assertTrue(ct, "precisa entrar na fila de verificação de CT")

    def test_ct_cranio_com_acento_tambem_conta(self):
        elegivel, ct, _ = self.avaliar("CT", "", "CRÂNIO", nome="ANA 30")
        self.assertTrue(elegivel)
        self.assertTrue(ct)

    def test_ct_cranio_unimed_nao_age(self):
        elegivel, ct, _ = self.avaliar("CT", "UNIMED", "CRANIO", nome="ANA 30")
        self.assertFalse(elegivel)
        self.assertFalse(ct)

    def test_ct_cranio_ja_desmarcado_nao_remarca(self):
        elegivel, _, _ = self.avaliar("CT", "", "CRANIO", nome="ANA 30", ja_desmarcado=True)
        self.assertFalse(elegivel)

    def test_ct_cranio_acima_de_45_cai_na_regra_geral(self):
        # 46 anos: sai da regra de crânio e passa a depender do convênio
        self.assertFalse(self.avaliar("CT", "", "CRANIO", nome="ANA 46")[0])
        self.assertTrue(self.avaliar("CT", "CCEST", "CRANIO", nome="ANA 46")[0])

    def test_ct_cranio_sem_idade_no_nome_cai_na_regra_geral(self):
        self.assertFalse(self.avaliar("CT", "", "CRANIO", nome="SEM IDADE")[0])

    # --- ANGIO e CT especial ---
    def test_angio_vale_para_qualquer_convenio_menos_unimed(self):
        self.assertTrue(self.avaliar("DX", "QUALQUER COISA", "ANGIO TORAX")[0])
        self.assertFalse(self.avaliar("DX", "UNIMED", "ANGIO TORAX")[0])

    def test_ct_tep_e_carotida(self):
        for termo in ("TEP", "CAROTIDA", "CARÓTIDA"):
            self.assertTrue(self.avaliar("CT", "OUTRO", termo)[0], termo)
            self.assertFalse(self.avaliar("CT", "UNIMED", termo)[0], termo)

    def test_tep_so_vale_para_ct_nao_para_dx(self):
        self.assertFalse(self.avaliar("DX", "OUTRO", "TEP")[0])

    # --- regra geral de convênio ---
    def test_convenio_da_lista_e_marcado(self):
        self.assertTrue(self.avaliar("DX", "CCEST", "TORAX")[0])

    def test_convenio_fora_da_lista_nao_e_marcado(self):
        self.assertFalse(self.avaliar("DX", "OUTRO PLANO", "TORAX")[0])

    def test_convenio_vazio_nao_e_marcado_no_passo1(self):
        self.assertFalse(self.avaliar("DX", "", "TORAX")[0])

    def test_excecoes_valem_para_dx_mas_nao_para_ct(self):
        # Lista escrita à mão de propósito: se o teste tirasse os nomes da própria
        # constante, esvaziar a constante faria o laço não rodar e o teste passaria
        # sem testar nada.
        excecoes = ["SAS", "FLIP", "ARAMART", "AVICOLA", "HI-MIX"]
        self.assertCountEqual(excecoes, automacao.CONVENIOS_SEM_CT,
                              "a lista de exceções mudou — atualize este teste de propósito")
        automacao.config.CONVENIOS_ALVO = list(excecoes)
        for conv in excecoes:
            self.assertTrue(self.avaliar("DX", conv, "TORAX")[0], f"{conv} deve valer em DX")
            self.assertFalse(self.avaliar("CT", conv, "TORAX")[0], f"{conv} não pode valer em CT")


class RegraDeConvenioDX(SemNavegador):
    """_convenio_bate_dx decide se a marcação do Passo 2 estava certa."""

    def setUp(self):
        super().setUp()
        self._convenios = automacao.config.CONVENIOS_ALVO
        automacao.config.CONVENIOS_ALVO = ["CCEST", "PARTICULAR"]

    def tearDown(self):
        automacao.config.CONVENIOS_ALVO = self._convenios
        super().tearDown()

    def test_convenio_da_lista_bate(self):
        self.assertTrue(self.a._convenio_bate_dx("CCEST", "TORAX"))

    def test_convenio_fora_da_lista_nao_bate(self):
        self.assertFalse(self.a._convenio_bate_dx("OUTRO", "TORAX"))

    def test_angio_bate_para_qualquer_convenio_menos_unimed(self):
        self.assertTrue(self.a._convenio_bate_dx("OUTRO", "ANGIO"))
        self.assertFalse(self.a._convenio_bate_dx("UNIMED", "ANGIO"))


if __name__ == "__main__":
    unittest.main()
