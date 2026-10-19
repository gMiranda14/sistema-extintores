from banco.conexao import conectar

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
    with conectar() as conn:
        cursor = conn.execute(
            """SELECT id, nome, cpf_cnpj, telefone, forma_pagamento, ultimo_valor
               FROM cliente
               WHERE nome LIKE ?
               ORDER BY nome""",
            (f"%{busca}%",),
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