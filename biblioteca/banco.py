from contextlib import contextmanager
from pathlib import Path
import sqlite3
from typing import Iterator


class BancoDados:
    #Gerencia conexão, estrutura e transações do banco SQLite.

    def __init__(self, caminho: str | Path = "biblioteca.db") -> None:
        self.caminho = str(caminho)
        self.conexao = sqlite3.connect(self.caminho, isolation_level=None)
        self.conexao.row_factory = sqlite3.Row
        self.conexao.execute("PRAGMA foreign_keys = ON")
        self.conexao.execute("PRAGMA busy_timeout = 5000")
        self._criar_estrutura()

    def _criar_estrutura(self) -> None:
        #Cria as tabelas e índices caso ainda não existam.
        self.conexao.executescript(
            """
            CREATE TABLE IF NOT EXISTS livros (
                id_livro INTEGER PRIMARY KEY AUTOINCREMENT,
                titulo TEXT NOT NULL CHECK (trim(titulo) <> ''),
                autor TEXT NOT NULL CHECK (trim(autor) <> ''),
                ano_publicacao INTEGER NOT NULL CHECK (ano_publicacao > 0),
                total_copias INTEGER NOT NULL CHECK (total_copias > 0),
                copias_disponiveis INTEGER NOT NULL,
                CHECK (
                    copias_disponiveis >= 0
                    AND copias_disponiveis <= total_copias
                )
            );

            CREATE TABLE IF NOT EXISTS usuarios (
                identificacao TEXT PRIMARY KEY,
                nome TEXT NOT NULL CHECK (trim(nome) <> ''),
                contato TEXT NOT NULL CHECK (trim(contato) <> '')
            );

            CREATE TABLE IF NOT EXISTS emprestimos (
                id_emprestimo INTEGER PRIMARY KEY AUTOINCREMENT,
                id_livro INTEGER NOT NULL,
                id_usuario TEXT NOT NULL,
                data_emprestimo TEXT NOT NULL,
                devolvido INTEGER NOT NULL DEFAULT 0 CHECK (devolvido IN (0, 1)),
                data_devolucao TEXT,
                FOREIGN KEY (id_livro) REFERENCES livros(id_livro),
                FOREIGN KEY (id_usuario) REFERENCES usuarios(identificacao)
            );

            CREATE INDEX IF NOT EXISTS idx_livros_titulo
                ON livros(titulo);
            CREATE INDEX IF NOT EXISTS idx_livros_autor
                ON livros(autor);
            CREATE INDEX IF NOT EXISTS idx_emprestimos_ativos
                ON emprestimos(id_livro, id_usuario, devolvido);
            """
        )

    @contextmanager
    def transacao(self) -> Iterator[None]:
        #Executa um conjunto de alterações de forma atômica.
        self.conexao.execute("BEGIN IMMEDIATE")
        try:
            yield
        except Exception:
            self.conexao.rollback()
            raise
        else:
            self.conexao.commit()

    def chaves_estrangeiras_ativas(self) -> bool:
        #Informa se o SQLite está aplicando as restrições de chave estrangeira.
        valor = self.conexao.execute("PRAGMA foreign_keys").fetchone()[0]
        return bool(valor)

    def fechar(self) -> None:
        #Fecha a conexão com o banco de dados.
        self.conexao.close()
