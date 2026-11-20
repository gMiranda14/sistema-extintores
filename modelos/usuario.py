from datetime import datetime

from banco.conexao import conectar


def existe():
    with conectar() as conn:
        return conn.execute("SELECT COUNT(*) FROM usuario").fetchone()[0] > 0


def criar(nome_usuario, senha_hash, codigo_hash):
    with conectar() as conn:
        cursor = conn.execute(
            """INSERT INTO usuario (nome_usuario, senha_hash, codigo_recuperacao_hash, criado_em)
               VALUES (?, ?, ?, ?)""",
            (nome_usuario, senha_hash, codigo_hash, datetime.now().isoformat(timespec="seconds")),
        )
        return cursor.lastrowid


def buscar(nome_usuario):
    """Devolve (id, nome_usuario, senha_hash, codigo_recuperacao_hash) ou None."""
    with conectar() as conn:
        return conn.execute(
            """SELECT id, nome_usuario, senha_hash, codigo_recuperacao_hash
               FROM usuario WHERE nome_usuario = ?""",
            (nome_usuario,),
        ).fetchone()


def atualizar_senha(id_usuario, senha_hash):
    with conectar() as conn:
        conn.execute(
            "UPDATE usuario SET senha_hash = ? WHERE id = ?", (senha_hash, id_usuario)
        )


def atualizar_senha_e_codigo(id_usuario, senha_hash, codigo_hash):
    with conectar() as conn:
        conn.execute(
            """UPDATE usuario SET senha_hash = ?, codigo_recuperacao_hash = ?
               WHERE id = ?""",
            (senha_hash, codigo_hash, id_usuario),
        )