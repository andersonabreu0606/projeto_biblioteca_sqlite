#Entidades de domínio do sistema de gerenciamento de biblioteca.

from dataclasses import dataclass
from datetime import datetime

from .excecoes import DadosInvalidosError, LivroIndisponivelError


@dataclass
class Livro:
    #Representa um livro e o controle dos seus exemplares.

    id_livro: int | None
    titulo: str
    autor: str
    ano_publicacao: int
    total_copias: int
    copias_disponiveis: int

    def __post_init__(self) -> None:
        ano_atual = datetime.now().year
        self.titulo = self.titulo.strip()
        self.autor = self.autor.strip()

        if not self.titulo or not self.autor:
            raise DadosInvalidosError("Título e autor são obrigatórios.")
        if self.ano_publicacao <= 0 or self.ano_publicacao > ano_atual:
            raise DadosInvalidosError("Ano de publicação inválido.")
        if self.total_copias <= 0:
            raise DadosInvalidosError(
                "O número de cópias deve ser maior que zero."
            )
        if not 0 <= self.copias_disponiveis <= self.total_copias:
            raise DadosInvalidosError(
                "Quantidade de cópias disponíveis inválida."
            )

    def emprestar(self) -> None:
        #Reduz uma cópia disponível depois de validar o estoque.
        if self.copias_disponiveis == 0:
            raise LivroIndisponivelError(
                f'O livro "{self.titulo}" não possui cópias disponíveis.'
            )
        self.copias_disponiveis -= 1

    def registrar_devolucao(self) -> None:
        #Recoloca uma cópia no estoque sem ultrapassar o total cadastrado.
        if self.copias_disponiveis >= self.total_copias:
            raise DadosInvalidosError(
                "Não é possível registrar mais devoluções do que o total de cópias."
            )
        self.copias_disponiveis += 1


@dataclass(frozen=True)
class Usuario:
    #Representa uma pessoa cadastrada na biblioteca.

    nome: str
    identificacao: str
    contato: str

    def __post_init__(self) -> None:
        if not self.nome.strip():
            raise DadosInvalidosError("O nome do usuário é obrigatório.")
        if not self.identificacao.strip():
            raise DadosInvalidosError("A identificação do usuário é obrigatória.")
        if not self.contato.strip():
            raise DadosInvalidosError("O contato do usuário é obrigatório.")


@dataclass
class Emprestimo:
    #Registra um empréstimo persistido no banco de dados.

    id_emprestimo: int | None
    id_livro: int
    id_usuario: str
    data_emprestimo: datetime
    devolvido: bool = False
    data_devolucao: datetime | None = None

    def finalizar(self) -> None:
        #Marca o empréstimo como devolvido e registra a data da operação.
        self.devolvido = True
        self.data_devolucao = datetime.now()
