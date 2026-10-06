#Camada de serviço com as regras de negócio da biblioteca.

from datetime import datetime
from pathlib import Path
import sqlite3

from .banco import BancoDados
from .entidades import Emprestimo, Livro, Usuario
from .excecoes import (
    EmprestimoNaoEncontradoError,
    LivroNaoEncontradoError,
    RegistroDuplicadoError,
    UsuarioNaoEncontradoError,
)
from .repositorio import BibliotecaRepositorio


class Biblioteca:
    #Coordena regras de negócio e persistência da biblioteca.

    def __init__(self, caminho_banco: str | Path = "biblioteca.db") -> None:
        self.banco = BancoDados(caminho_banco)
        self.repositorio = BibliotecaRepositorio(self.banco)

    def __enter__(self) -> "Biblioteca":
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.fechar()

    def fechar(self) -> None:
        #Libera a conexão aberta com o banco.
        self.banco.fechar()

    def cadastrar_livro(
        self, titulo: str, autor: str, ano_publicacao: int, numero_copias: int
    ) -> Livro:
        #Valida e persiste um novo livro.
        livro = Livro(
            id_livro=None,
            titulo=titulo,
            autor=autor,
            ano_publicacao=ano_publicacao,
            total_copias=numero_copias,
            copias_disponiveis=numero_copias,
        )
        with self.banco.transacao():
            return self.repositorio.inserir_livro(livro)

    def cadastrar_usuario(
        self, nome: str, identificacao: str, contato: str
    ) -> Usuario:
        #Valida e persiste um usuário com identificação única.
        usuario = Usuario(
            nome=nome.strip(),
            identificacao=identificacao.strip(),
            contato=contato.strip(),
        )
        try:
            with self.banco.transacao():
                return self.repositorio.inserir_usuario(usuario)
        except sqlite3.IntegrityError as exc:
            raise RegistroDuplicadoError(
                f'O usuário com identificação "{usuario.identificacao}" '
                "já está cadastrado."
            ) from exc

    def obter_livro(self, id_livro: int) -> Livro:
        #Obtém um livro pelo identificador ou sinaliza ausência.
        livro = self.repositorio.obter_livro(id_livro)
        if livro is None:
            raise LivroNaoEncontradoError(
                f"Livro de código {id_livro} não encontrado."
            )
        return livro

    def obter_usuario(self, identificacao: str) -> Usuario:
        #Obtém um usuário pela identificação ou sinaliza ausência.
        chave = identificacao.strip()
        usuario = self.repositorio.obter_usuario(chave)
        if usuario is None:
            raise UsuarioNaoEncontradoError(
                f'Usuário "{identificacao}" não encontrado.'
            )
        return usuario

    def emprestar_livro(self, id_livro: int, id_usuario: str) -> Emprestimo:
        #Realiza o empréstimo e atualiza o estoque numa única transação.
        chave_usuario = id_usuario.strip()
        with self.banco.transacao():
            livro = self.obter_livro(id_livro)
            self.obter_usuario(chave_usuario)
            livro.emprestar()
            self.repositorio.atualizar_copias_disponiveis(livro)

            emprestimo = Emprestimo(
                id_emprestimo=None,
                id_livro=id_livro,
                id_usuario=chave_usuario,
                data_emprestimo=datetime.now(),
            )
            return self.repositorio.inserir_emprestimo(emprestimo)

    def devolver_livro(self, id_livro: int, id_usuario: str) -> Emprestimo:
        #Finaliza um empréstimo e restaura o estoque numa única transação.
        chave_usuario = id_usuario.strip()
        with self.banco.transacao():
            livro = self.obter_livro(id_livro)
            self.obter_usuario(chave_usuario)
            emprestimo = self.repositorio.obter_emprestimo_ativo(
                id_livro, chave_usuario
            )
            if emprestimo is None:
                raise EmprestimoNaoEncontradoError(
                    "Não existe empréstimo ativo desse livro para o usuário informado."
                )

            emprestimo.finalizar()
            livro.registrar_devolucao()
            self.repositorio.finalizar_emprestimo(emprestimo)
            self.repositorio.atualizar_copias_disponiveis(livro)
            return emprestimo

    def consultar_livros(
        self,
        titulo: str | None = None,
        autor: str | None = None,
        ano_publicacao: int | None = None,
    ) -> list[Livro]:
        #Consulta livros por título, autor e/ou ano de publicação.
        return self.repositorio.consultar_livros(
            titulo=titulo,
            autor=autor,
            ano_publicacao=ano_publicacao,
        )

    def relatorio_livros_disponiveis(self) -> list[Livro]:
        #Lista livros que possuem ao menos uma cópia disponível.
        return self.repositorio.listar_livros_disponiveis()

    def relatorio_livros_emprestados(self) -> list[dict[str, object]]:
        #Lista os empréstimos ainda ativos.
        return self.repositorio.listar_emprestimos_ativos()

    def relatorio_usuarios(self) -> list[Usuario]:
        #Lista todos os usuários cadastrados.
        return self.repositorio.listar_usuarios()
