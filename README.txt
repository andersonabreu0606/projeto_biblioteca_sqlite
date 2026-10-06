PROJETO INTEGRADO SÍNTESE - DADOS

SISTEMA DE GERENCIAMENTO DE BIBLIOTECA COM SQLITE

Executar o sistema
------------------
python main.py

Executar os testes
------------------
python -m unittest discover -s tests -v

Estrutura
---------
main.py                         ponto de entrada
biblioteca/entidades.py         classes Livro, Usuario e Emprestimo
biblioteca/excecoes.py          exceções específicas do domínio
biblioteca/banco.py             conexão, esquema e transações SQLite
biblioteca/repositorio.py       comandos SQL e persistência
biblioteca/servico.py           regras de negócio
biblioteca/cli.py               menu de console
tests/test_servico.py           testes automatizados

Google Colab
------------
1. Entre na pasta do projeto.
2. Execute os testes.
3. Execute o sistema.

Exemplo:
%cd /content/projeto_biblioteca_sqlite
!python -m unittest discover -s tests -v
!python main.py
