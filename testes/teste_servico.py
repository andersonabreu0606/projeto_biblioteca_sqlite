#Testes das regras de negócio usando um banco SQLite temporário.

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from biblioteca.excecoes import (
    DadosInvalidosError,
    EmprestimoNaoEncontradoError,
    LivroIndisponivelError,
    LivroNaoEncontradoError,
    RegistroDuplicadoError,
    UsuarioNaoEncontradoError,
)
from biblioteca.servico import Biblioteca


class BibliotecaTestCase(unittest.TestCase):
    #Valida fluxos normais e situações de erro da biblioteca.

    def setUp(self) -> None:
        self.pasta_temporaria = TemporaryDirectory()
        self.caminho_banco = Path(self.pasta_temporaria.name) / "teste.db"
        self.biblioteca = Biblioteca(self.caminho_banco)
        self.livro_python = self.biblioteca.cadastrar_livro(
            "Introdução ao Python", "Ana Souza", 2024, 2
        )
        self.livro_dados = self.biblioteca.cadastrar_livro(
            "Arquitetura de Dados", "Carlos Lima", 2023, 1
        )
        self.usuario = self.biblioteca.cadastrar_usuario(
            "Marina Costa", "U001", "marina@example.com"
        )

    def tearDown(self) -> None:
        self.biblioteca.fechar()
        self.pasta_temporaria.cleanup()

    def test_banco_sqlite_e_criado(self) -> None:
        self.assertTrue(self.caminho_banco.exists())

    def test_chaves_estrangeiras_estao_ativas(self) -> None:
        self.assertTrue(self.biblioteca.banco.chaves_estrangeiras_ativas())

    def test_cadastrar_livro_define_copias_disponiveis(self) -> None:
        livro = self.biblioteca.cadastrar_livro(
            "Banco de Dados", "Paula", 2022, 3
        )
        self.assertEqual(livro.copias_disponiveis, 3)
        self.assertEqual(livro.total_copias, 3)
        self.assertIsNotNone(livro.id_livro)

    def test_cadastro_rejeita_numero_de_copias_invalido(self) -> None:
        with self.assertRaises(DadosInvalidosError):
            self.biblioteca.cadastrar_livro(
                "Livro inválido", "Autor", 2020, 0
            )

    def test_cadastro_rejeita_ano_futuro(self) -> None:
        with self.assertRaises(DadosInvalidosError):
            self.biblioteca.cadastrar_livro("Livro futuro", "Autor", 9999, 1)

    def test_cadastrar_usuario(self) -> None:
        usuario = self.biblioteca.cadastrar_usuario(
            "João", "U002", "9999-0000"
        )
        self.assertEqual(usuario.identificacao, "U002")

    def test_cadastro_rejeita_usuario_duplicado(self) -> None:
        with self.assertRaises(RegistroDuplicadoError):
            self.biblioteca.cadastrar_usuario(
                "Outra pessoa", "U001", "x@y.com"
            )

    def test_emprestimo_reduz_copia_disponivel(self) -> None:
        self.biblioteca.emprestar_livro(self.livro_python.id_livro, "U001")
        livro_atualizado = self.biblioteca.obter_livro(
            self.livro_python.id_livro
        )
        self.assertEqual(livro_atualizado.copias_disponiveis, 1)

    def test_emprestimo_rejeita_livro_indisponivel(self) -> None:
        self.biblioteca.emprestar_livro(self.livro_dados.id_livro, "U001")
        with self.assertRaises(LivroIndisponivelError):
            self.biblioteca.emprestar_livro(
                self.livro_dados.id_livro, "U001"
            )

    def test_emprestimo_rejeita_livro_inexistente(self) -> None:
        with self.assertRaises(LivroNaoEncontradoError):
            self.biblioteca.emprestar_livro(999, "U001")

    def test_emprestimo_rejeita_usuario_inexistente(self) -> None:
        with self.assertRaises(UsuarioNaoEncontradoError):
            self.biblioteca.emprestar_livro(
                self.livro_python.id_livro, "U999"
            )

    def test_falha_de_emprestimo_nao_altera_estoque(self) -> None:
        with self.assertRaises(UsuarioNaoEncontradoError):
            self.biblioteca.emprestar_livro(
                self.livro_python.id_livro, "U999"
            )
        livro = self.biblioteca.obter_livro(self.livro_python.id_livro)
        self.assertEqual(livro.copias_disponiveis, 2)

    def test_devolucao_restaura_copia_disponivel(self) -> None:
        self.biblioteca.emprestar_livro(self.livro_python.id_livro, "U001")
        self.biblioteca.devolver_livro(self.livro_python.id_livro, "U001")
        livro = self.biblioteca.obter_livro(self.livro_python.id_livro)
        self.assertEqual(livro.copias_disponiveis, 2)

    def test_devolucao_rejeita_emprestimo_inexistente(self) -> None:
        with self.assertRaises(EmprestimoNaoEncontradoError):
            self.biblioteca.devolver_livro(
                self.livro_python.id_livro, "U001"
            )

    def test_consulta_por_titulo_ignora_maiusculas(self) -> None:
        resultado = self.biblioteca.consultar_livros(titulo="PYTHON")
        self.assertEqual(
            [item.id_livro for item in resultado],
            [self.livro_python.id_livro],
        )

    def test_consulta_por_autor(self) -> None:
        resultado = self.biblioteca.consultar_livros(autor="Carlos")
        self.assertEqual(
            [item.id_livro for item in resultado],
            [self.livro_dados.id_livro],
        )

    def test_consulta_por_ano(self) -> None:
        resultado = self.biblioteca.consultar_livros(ano_publicacao=2023)
        self.assertEqual(
            [item.id_livro for item in resultado],
            [self.livro_dados.id_livro],
        )

    def test_relatorio_disponiveis_exclui_livro_sem_copias(self) -> None:
        self.biblioteca.emprestar_livro(self.livro_dados.id_livro, "U001")
        ids = [
            livro.id_livro
            for livro in self.biblioteca.relatorio_livros_disponiveis()
        ]
        self.assertNotIn(self.livro_dados.id_livro, ids)

    def test_relatorio_emprestados_exibe_apenas_ativos(self) -> None:
        self.biblioteca.emprestar_livro(self.livro_python.id_livro, "U001")
        self.assertEqual(
            len(self.biblioteca.relatorio_livros_emprestados()), 1
        )
        self.biblioteca.devolver_livro(self.livro_python.id_livro, "U001")
        self.assertEqual(self.biblioteca.relatorio_livros_emprestados(), [])

    def test_relatorio_usuarios(self) -> None:
        usuarios = self.biblioteca.relatorio_usuarios()
        self.assertEqual(len(usuarios), 1)
        self.assertEqual(usuarios[0].nome, "Marina Costa")

    def test_dados_persistem_apos_reabrir_banco(self) -> None:
        id_livro = self.livro_python.id_livro
        self.biblioteca.fechar()
        self.biblioteca = Biblioteca(self.caminho_banco)
        livro = self.biblioteca.obter_livro(id_livro)
        usuario = self.biblioteca.obter_usuario("U001")
        self.assertEqual(livro.titulo, "Introdução ao Python")
        self.assertEqual(usuario.nome, "Marina Costa")

    def test_emprestimo_persiste_apos_reabrir_banco(self) -> None:
        self.biblioteca.emprestar_livro(self.livro_python.id_livro, "U001")
        self.biblioteca.fechar()
        self.biblioteca = Biblioteca(self.caminho_banco)
        ativos = self.biblioteca.relatorio_livros_emprestados()
        livro = self.biblioteca.obter_livro(self.livro_python.id_livro)
        self.assertEqual(len(ativos), 1)
        self.assertEqual(livro.copias_disponiveis, 1)


if __name__ == "__main__":
    unittest.main()
