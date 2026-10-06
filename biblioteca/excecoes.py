#Exceções de domínio utilizadas pelo sistema da biblioteca.


class BibliotecaError(Exception):
    """Classe-base para erros esperados nas regras da biblioteca."""


class DadosInvalidosError(BibliotecaError):
    """Indica que um dado informado não atende às regras de validação."""


class LivroNaoEncontradoError(BibliotecaError):
    """Indica tentativa de utilizar um livro inexistente."""


class UsuarioNaoEncontradoError(BibliotecaError):
    """Indica tentativa de utilizar um usuário inexistente."""


class LivroIndisponivelError(BibliotecaError):
    """Indica que não há cópias disponíveis para empréstimo."""


class EmprestimoNaoEncontradoError(BibliotecaError):
    """Indica que não existe empréstimo ativo compatível com a devolução."""


class RegistroDuplicadoError(BibliotecaError):
    """Indica tentativa de cadastrar um identificador já utilizado."""
