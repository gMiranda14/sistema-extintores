from banco.conexao import conectar


def inserir(dados):
    # dados = (cliente_id, tipo, descricao, capacidade, numero_serie, data_referencia)
    with conectar() as conn:
        conn.execute(
            """INSERT INTO equipamento
               (cliente_id, tipo, descricao, capacidade, numero_serie, data_referencia)
               VALUES (?, ?, ?, ?, ?, ?)""",
            dados,
        )


def atualizar(id_equipamento, dados):
    with conectar() as conn:
        conn.execute(
            """UPDATE equipamento
               SET cliente_id=?, tipo=?, descricao=?, capacidade=?,
                   numero_serie=?, data_referencia=?
               WHERE id=?""",
            dados + (id_equipamento,),
        )


def excluir(id_equipamento):
    with conectar() as conn:
        conn.execute("DELETE FROM equipamento WHERE id=?", (id_equipamento,))


def listar(busca=""):
    with conectar() as conn:
        cursor = conn.execute(
            """SELECT e.id, c.nome, e.tipo, e.descricao, e.capacidade,
                      e.numero_serie, e.data_referencia
               FROM equipamento e
               JOIN cliente c ON c.id = e.cliente_id
               WHERE c.nome LIKE ?
                  OR COALESCE(e.numero_serie, '') LIKE ?
               ORDER BY c.nome, e.tipo""",
            (f"%{busca}%", f"%{busca}%"),
        )
        return cursor.fetchall()


def buscar_por_id(id_equipamento):
    with conectar() as conn:
        cursor = conn.execute(
            """SELECT cliente_id, tipo, descricao, capacidade,
                      numero_serie, data_referencia
               FROM equipamento WHERE id=?""",
            (id_equipamento,),
        )
        return cursor.fetchone()