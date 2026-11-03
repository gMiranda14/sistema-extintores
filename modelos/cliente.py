import re

from banco.conexao import conectar


def inserir(dados):
    # dados = (nome, cpf_cnpj, endereco, telefone, email)
    with conectar() as conn:
        conn.execute(
            """INSERT INTO cliente (nome, cpf_cnpj, endereco, telefone, email)
               VALUES (?, ?, ?, ?, ?)""",
            dados,
        )


def atualizar(id_cliente, dados):
    with conectar() as conn:
        conn.execute(
            """UPDATE cliente
               SET nome=?, cpf_cnpj=?, endereco=?, telefone=?, email=?
               WHERE id=?""",
            dados + (id_cliente,),
        )


def excluir(id_cliente):
    with conectar() as conn:
        conn.execute("DELETE FROM cliente WHERE id=?", (id_cliente,))


# Pagamento mais recente do cliente: o de data de serviço mais nova (desempata pelo id)
_ULTIMO_PAGAMENTO = """(SELECT p.id FROM pagamento p
                        WHERE p.cliente_id = c.id
                        ORDER BY COALESCE(p.data_servico, '') DESC, p.id DESC
                        LIMIT 1)"""


def listar(busca=""):
    """Devolve (id, nome, cpf_cnpj, telefone, última forma de pagamento, último valor).

    A forma e o valor não são digitados: vêm do pagamento mais recente do cliente."""
    busca_documento = re.sub(r"[.\-/\s]", "", busca)
    with conectar() as conn:
        cursor = conn.execute(
            f"""SELECT c.id, c.nome, c.cpf_cnpj, c.telefone,
                       (SELECT forma FROM pagamento WHERE id = {_ULTIMO_PAGAMENTO}),
                       (SELECT SUM(quantidade * valor_unitario) FROM item_pagamento
                        WHERE pagamento_id = {_ULTIMO_PAGAMENTO})
                FROM cliente c
                WHERE c.nome LIKE ?
                   OR REPLACE(REPLACE(REPLACE(COALESCE(c.cpf_cnpj, ''), '.', ''), '-', ''), '/', '') LIKE ?
                ORDER BY c.nome""",
            (f"%{busca}%", f"%{busca_documento}%"),
        )
        return cursor.fetchall()


def buscar_por_id(id_cliente):
    with conectar() as conn:
        cursor = conn.execute(
            """SELECT id, nome, cpf_cnpj, endereco, telefone, email
               FROM cliente WHERE id=?""",
            (id_cliente,),
        )
        return cursor.fetchone()


def listar_nomes():
    with conectar() as conn:
        return conn.execute("SELECT id, nome FROM cliente ORDER BY nome").fetchall()


def listar_para_selecao():
    with conectar() as conn:
        return conn.execute(
            "SELECT id, nome, cpf_cnpj FROM cliente ORDER BY nome"
        ).fetchall()