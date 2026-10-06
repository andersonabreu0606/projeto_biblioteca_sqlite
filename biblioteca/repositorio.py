#Camada de persistência responsável pelo acesso ao SQLite.

from datetime import datetime
import sqlite3

from .banco import BancoDados
from .entidades import Emprestimo, Livro, Usuario


class BibliotecaRepositorio:
    #Centraliza comandos SQL e converte linhas do banco em objetos de domínio.

    def __init__(self, banco: BancoDados) -> None:
        self.banco = banco
        self.conexao = banco.conexao

    @staticmethod
    def _linha_para_livro(linha: sqlite3.Row) -> Livro:
        return Livro(
            id_livro=linha["id_livro"],
            titulo=linha["titulo"],
            autor=linha["autor"],
            ano_publicacao=linha["ano_publicacao"],
            total_copias=linha["total_copias"],
            copias_disponiveis=linha["copias_disponiveis"],
        )

    @staticmethod
    def _linha_para_usuario(linha: sqlite3.Row) -> Usuario:
        return Usuario(
            nome=linha["nome"],
            identificacao=linha["identificacao"],
            contato=linha["contato"],
        )

    @staticmethod
    def _linha_para_emprestimo(linha: sqlite3.Row) -> Emprestimo:
        data_devolucao = linha["data_devolucao"]
        return Emprestimo(
            id_emprestimo=linha["id_emprestimo"],
            id_livro=linha["id_livro"],
            id_usuario=linha["id_usuario"],
            data_emprestimo=datetime.fromisoformat(linha["data_emprestimo"]),
            devolvido=bool(linha["devolvido"]),
            data_devolucao=(
                datetime.fromisoformat(data_devolucao)
                if data_devolucao
                else None
            ),
        )

    def inserir_livro(self, livro: Livro) -> Livro:
        cursor = self.conexao.execute(
            """
            INSERT INTO livros (
                titulo, autor, ano_publicacao, total_copias, copias_disponiveis
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (
                livro.titulo,
                livro.autor,
                livro.ano_publicacao,
                livro.total_copias,
                livro.copias_disponiveis,
            ),
        )
        livro.id_livro = int(cursor.lastrowid)
        return livro

    def inserir_usuario(self, usuario: Usuario) -> Usuario:
        self.conexao.execute(
            """
            INSERT INTO usuarios (identificacao, nome, contato)
            VALUES (?, ?, ?)
            """,
            (usuario.identificacao, usuario.nome, usuario.contato),
        )
        return usuario

    def obter_livro(self, id_livro: int) -> Livro | None:
        linha = self.conexao.execute(
            "SELECT * FROM livros WHERE id_livro = ?", (id_livro,)
        ).fetchone()
        return self._linha_para_livro(linha) if linha else None

    def obter_usuario(self, identificacao: str) -> Usuario | None:
        linha = self.conexao.execute(
            "SELECT * FROM usuarios WHERE identificacao = ?",
            (identificacao,),
        ).fetchone()
        return self._linha_para_usuario(linha) if linha else None

    def atualizar_copias_disponiveis(self, livro: Livro) -> None:
        self.conexao.execute(
            """
            UPDATE livros
               SET copias_disponiveis = ?
             WHERE id_livro = ?
            """,
            (livro.copias_disponiveis, livro.id_livro),
        )

    def inserir_emprestimo(self, emprestimo: Emprestimo) -> Emprestimo:
        cursor = self.conexao.execute(
            """
            INSERT INTO emprestimos (
                id_livro, id_usuario, data_emprestimo, devolvido, data_devolucao
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (
                emprestimo.id_livro,
                emprestimo.id_usuario,
                emprestimo.data_emprestimo.isoformat(timespec="seconds"),
                int(emprestimo.devolvido),
                None,
            ),
        )
        emprestimo.id_emprestimo = int(cursor.lastrowid)
        return emprestimo

    def obter_emprestimo_ativo(
        self, id_livro: int, id_usuario: str
    ) -> Emprestimo | None:
        linha = self.conexao.execute(
            """
            SELECT *
              FROM emprestimos
             WHERE id_livro = ?
               AND id_usuario = ?
               AND devolvido = 0
             ORDER BY id_emprestimo
             LIMIT 1
            """,
            (id_livro, id_usuario),
        ).fetchone()
        return self._linha_para_emprestimo(linha) if linha else None

    def finalizar_emprestimo(self, emprestimo: Emprestimo) -> None:
        self.conexao.execute(
            """
            UPDATE emprestimos
               SET devolvido = 1,
                   data_devolucao = ?
             WHERE id_emprestimo = ?
            """,
            (
                emprestimo.data_devolucao.isoformat(timespec="seconds")
                if emprestimo.data_devolucao
                else None,
                emprestimo.id_emprestimo,
            ),
        )

    def consultar_livros(
        self,
        titulo: str | None = None,
        autor: str | None = None,
        ano_publicacao: int | None = None,
    ) -> list[Livro]:
        sql = "SELECT * FROM livros WHERE 1 = 1"
        parametros: list[object] = []

        if titulo:
            sql += " AND titulo LIKE ? COLLATE NOCASE"
            parametros.append(f"%{titulo.strip()}%")
        if autor:
            sql += " AND autor LIKE ? COLLATE NOCASE"
            parametros.append(f"%{autor.strip()}%")
        if ano_publicacao is not None:
            sql += " AND ano_publicacao = ?"
            parametros.append(ano_publicacao)

        sql += " ORDER BY titulo, autor"
        linhas = self.conexao.execute(sql, parametros).fetchall()
        return [self._linha_para_livro(linha) for linha in linhas]

    def listar_livros_disponiveis(self) -> list[Livro]:
        linhas = self.conexao.execute(
            """
            SELECT *
              FROM livros
             WHERE copias_disponiveis > 0
             ORDER BY titulo, autor
            """
        ).fetchall()
        return [self._linha_para_livro(linha) for linha in linhas]

    def listar_usuarios(self) -> list[Usuario]:
        linhas = self.conexao.execute(
            "SELECT * FROM usuarios ORDER BY nome, identificacao"
        ).fetchall()
        return [self._linha_para_usuario(linha) for linha in linhas]

    def listar_emprestimos_ativos(self) -> list[dict[str, object]]:
        linhas = self.conexao.execute(
            """
            SELECT e.id_emprestimo,
                   e.data_emprestimo,
                   l.id_livro,
                   l.titulo AS livro,
                   u.nome AS usuario,
                   u.identificacao
              FROM emprestimos e
              JOIN livros l ON l.id_livro = e.id_livro
              JOIN usuarios u ON u.identificacao = e.id_usuario
             WHERE e.devolvido = 0
             ORDER BY e.data_emprestimo, e.id_emprestimo
            """
        ).fetchall()
        return [
            {
                "id_emprestimo": linha["id_emprestimo"],
                "id_livro": linha["id_livro"],
                "livro": linha["livro"],
                "usuario": linha["usuario"],
                "identificacao": linha["identificacao"],
                "data_emprestimo": datetime.fromisoformat(
                    linha["data_emprestimo"]
                ),
            }
            for linha in linhas
        ]
