from banco.conexao import conectar

# Serviços que "renovam" o equipamento: a data do serviço vira a nova data de referência
TIPOS_QUE_RENOVAM = ("manutencao", "venda_extintor", "venda_mangueira", "teste_mangueira")


def _gravar_itens(conn, id_pagamento, itens):
    conn.executemany(
        """INSERT INTO item_pagamento
           (pagamento_id, equipamento_id, tipo_servico, descricao, quantidade, valor_unitario)
           VALUES (?, ?, ?, ?, ?, ?)""",
        [
            (id_pagamento, i["equipamento_id"], i["tipo_servico"], i["descricao"],
             i["quantidade"], i["valor_unitario"])
            for i in itens
        ],
    )


def _renovar_equipamentos(conn, itens, data_servico):
    for item in itens:
        if item["equipamento_id"] and item["tipo_servico"] in TIPOS_QUE_RENOVAM:
            conn.execute(
                """UPDATE equipamento SET data_referencia = ?
                   WHERE id = ? AND (data_referencia IS NULL OR data_referencia < ?)""",
                (data_servico, item["equipamento_id"], data_servico),
            )


def inserir(dados, itens):
    # dados = (cliente_id, forma, data_servico, data_vencimento, data_pagamento, numero_nf)
    with conectar() as conn:
        cursor = conn.execute(
            """INSERT INTO pagamento
               (cliente_id, forma, data_servico, data_vencimento, data_pagamento, numero_nf)
               VALUES (?, ?, ?, ?, ?, ?)""",
            dados,
        )
        id_pagamento = cursor.lastrowid
        _gravar_itens(conn, id_pagamento, itens)
        _renovar_equipamentos(conn, itens, dados[2])
        total = sum(round(i["quantidade"] * i["valor_unitario"], 2) for i in itens)
        conn.execute("UPDATE cliente SET ultimo_valor=? WHERE id=?", (total, dados[0]))
        return id_pagamento


def atualizar(id_pagamento, dados, itens):
    with conectar() as conn:
        conn.execute(
            """UPDATE pagamento
               SET cliente_id=?, forma=?, data_servico=?, data_vencimento=?,
                   data_pagamento=?, numero_nf=?
               WHERE id=?""",
            dados + (id_pagamento,),
        )
        conn.execute("DELETE FROM item_pagamento WHERE pagamento_id=?", (id_pagamento,))
        _gravar_itens(conn, id_pagamento, itens)
        _renovar_equipamentos(conn, itens, dados[2])


def excluir(id_pagamento):
    with conectar() as conn:
        conn.execute("DELETE FROM item_pagamento WHERE pagamento_id=?", (id_pagamento,))
        conn.execute("DELETE FROM pagamento WHERE id=?", (id_pagamento,))


def marcar_pago(id_pagamento, data_iso):
    with conectar() as conn:
        conn.execute(
            "UPDATE pagamento SET data_pagamento=? WHERE id=?", (data_iso, id_pagamento)
        )


def listar():
    with conectar() as conn:
        cursor = conn.execute(
            """SELECT p.id, c.nome, p.forma, p.data_servico, p.data_vencimento,
                      p.data_pagamento, p.numero_nf,
                      COALESCE(SUM(i.quantidade * i.valor_unitario), 0)
               FROM pagamento p
               JOIN cliente c ON c.id = p.cliente_id
               LEFT JOIN item_pagamento i ON i.pagamento_id = p.id
               GROUP BY p.id"""
        )
        return cursor.fetchall()


def buscar(id_pagamento):
    with conectar() as conn:
        dados = conn.execute(
            """SELECT cliente_id, forma, data_servico, data_vencimento,
                      data_pagamento, numero_nf
               FROM pagamento WHERE id=?""",
            (id_pagamento,),
        ).fetchone()
        itens = conn.execute(
            """SELECT equipamento_id, tipo_servico, descricao, quantidade, valor_unitario
               FROM item_pagamento WHERE pagamento_id=? ORDER BY id""",
            (id_pagamento,),
        ).fetchall()
        return dados, itens