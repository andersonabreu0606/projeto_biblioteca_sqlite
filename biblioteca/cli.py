#Interface de console do sistema de biblioteca.

from pathlib import Path

from .excecoes import BibliotecaError
from .servico import Biblioteca


def _ler_inteiro(mensagem: str) -> int:
    #Lê um número inteiro e apresenta erro claro quando a entrada é inválida.
    valor = input(mensagem).strip()
    try:
        return int(valor)
    except ValueError as exc:
        raise ValueError("Informe um número inteiro válido.") from exc


def _mostrar_livros(livros: list) -> None:
    if not livros:
        print("Nenhum livro encontrado.")
        return

    for livro in livros:
        print(
            f"[{livro.id_livro}] {livro.titulo} - {livro.autor} "
            f"({livro.ano_publicacao}) | Disponíveis: "
            f"{livro.copias_disponiveis}/{livro.total_copias}"
        )


def executar_menu() -> None:
    #Mantém o menu em execução até o usuário escolher sair.
    caminho_banco = Path("biblioteca.db")

    with Biblioteca(caminho_banco) as biblioteca:
        print(f"Banco de dados: {caminho_banco.resolve()}")

        while True:
            print("\n...: SISTEMA DA BIBLIOTECA :...\n")
            print("1 - Cadastrar livro")
            print("2 - Cadastrar usuário")
            print("3 - Emprestar livro")
            print("4 - Devolver livro")
            print("5 - Consultar livros")
            print("6 - Relatórios")
            print("0 - Sair")

            opcao = input("Escolha uma opção: ").strip()

            try:
                if opcao == "1":
                    titulo = input("Título: ")
                    autor = input("Autor: ")
                    ano = _ler_inteiro("Ano de publicação: ")
                    copias = _ler_inteiro("Número de cópias: ")
                    livro = biblioteca.cadastrar_livro(
                        titulo, autor, ano, copias
                    )
                    print(f"Livro cadastrado com o código {livro.id_livro}.")

                elif opcao == "2":
                    nome = input("Nome: ")
                    identificacao = input("Número de identificação: ")
                    contato = input("Contato: ")
                    biblioteca.cadastrar_usuario(nome, identificacao, contato)
                    print("Usuário cadastrado com sucesso.")

                elif opcao == "3":
                    id_livro = _ler_inteiro("Código do livro: ")
                    id_usuario = input("Identificação do usuário: ")
                    biblioteca.emprestar_livro(id_livro, id_usuario)
                    print("Empréstimo realizado com sucesso.")

                elif opcao == "4":
                    id_livro = _ler_inteiro("Código do livro: ")
                    id_usuario = input("Identificação do usuário: ")
                    biblioteca.devolver_livro(id_livro, id_usuario)
                    print("Devolução registrada com sucesso.")

                elif opcao == "5":
                    titulo = input("Título (Enter para ignorar): ").strip() or None
                    autor = input("Autor (Enter para ignorar): ").strip() or None
                    ano_texto = input("Ano (Enter para ignorar): ").strip()
                    ano = int(ano_texto) if ano_texto else None
                    _mostrar_livros(
                        biblioteca.consultar_livros(titulo, autor, ano)
                    )

                elif opcao == "6":
                    print("\nLivros disponíveis:")
                    _mostrar_livros(
                        biblioteca.relatorio_livros_disponiveis()
                    )

                    print("\nEmpréstimos ativos:")
                    ativos = biblioteca.relatorio_livros_emprestados()
                    if not ativos:
                        print("Nenhum empréstimo ativo.")
                    else:
                        for item in ativos:
                            print(
                                f'{item["livro"]} | {item["usuario"]} '
                                f'({item["identificacao"]}) | '
                                f'{item["data_emprestimo"]:%d/%m/%Y %H:%M}'
                            )

                    print("\nUsuários cadastrados:")
                    usuarios = biblioteca.relatorio_usuarios()
                    if not usuarios:
                        print("Nenhum usuário cadastrado.")
                    else:
                        for usuario in usuarios:
                            print(
                                f"{usuario.identificacao} - {usuario.nome} - "
                                f"{usuario.contato}"
                            )

                elif opcao == "0":
                    print("Sistema encerrado. Os dados permanecem no SQLite.")
                    break
                else:
                    print("Opção inválida. Tente novamente.")

            except (BibliotecaError, ValueError) as erro:
                print(f"Não foi possível concluir a operação: {erro}")
