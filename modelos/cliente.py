from banco.conexao import conectar
import re
def inserir(dados):
    with conectar() as conn:
        conn.execute(
            """
            INSERT INTO cliente
            (nome, cpf_cnpj, endereco, telefone, email, forma_pagamento, ultimo_valor)
            VALUES (?, ?, ?, ?, ?, ?, ?)""",
            dados,
        )

def atualizar(id_cliente, dados):
    with conectar() as conn:
        conn.execute(
            """
            UPDATE cliente
            SET nome=?, cpf_cnpj=?, endereco=?, telefone=?, email=?, forma_pagamento=?, ultimo_valor=?
            where id=?""",
            dados + (id_cliente,),
        )

def excluir(id_cliente):
    with conectar() as conn:
        conn.execute("DELETE FROM cliente WHERE id=?", (id_cliente,))


def listar(busca=""):
    busca_documento = re.sub(r"[.\-/\s]", "", busca)
    with conectar() as conn:
        cursor = conn.execute(
            """SELECT id, nome, cpf_cnpj, telefone, forma_pagamento, ultimo_valor
               FROM cliente
               WHERE nome LIKE ?
                  OR REPLACE(REPLACE(REPLACE(COALESCE(cpf_cnpj, ''), '.', ''), '-', ''), '/', '') LIKE ?
               ORDER BY nome""",
            (f"%{busca}%", f"%{busca_documento}%"),
        )
        return cursor.fetchall()

def buscar_por_id(id_cliente):
    with conectar() as conn:
        cursor = conn.execute(
              """SELECT id, nome, cpf_cnpj, endereco, telefone, email,
                      forma_pagamento, ultimo_valor
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