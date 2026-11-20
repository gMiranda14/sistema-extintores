import sqlite3
from pathlib import Path

CAMINHO = Path(__file__).parent / "dados.db"


def conectar():
    conn = sqlite3.connect(CAMINHO)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def criar_tabelas():
    with conectar() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS cliente (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            cpf_cnpj TEXT,
            endereco TEXT,
            telefone TEXT,
            email TEXT,
            forma_pagamento TEXT,
            ultimo_valor REAL
        );

        CREATE TABLE IF NOT EXISTS equipamento (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id INTEGER NOT NULL REFERENCES cliente(id),
            tipo TEXT NOT NULL,
            descricao TEXT,
            capacidade TEXT,
            numero_serie TEXT,
            data_referencia TEXT
        );

        CREATE TABLE IF NOT EXISTS pagamento (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id INTEGER NOT NULL REFERENCES cliente(id),
            forma TEXT,
            data_servico TEXT,
            data_vencimento TEXT,
            data_pagamento TEXT,
            numero_nf TEXT
        );

        CREATE TABLE IF NOT EXISTS item_pagamento (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pagamento_id INTEGER NOT NULL REFERENCES pagamento(id),
            equipamento_id INTEGER REFERENCES equipamento(id),
            tipo_servico TEXT NOT NULL,
            descricao TEXT,
            quantidade INTEGER DEFAULT 1,
            valor_unitario REAL NOT NULL
        );

        CREATE TABLE IF NOT EXISTS usuario (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome_usuario TEXT NOT NULL UNIQUE COLLATE NOCASE,
            senha_hash TEXT NOT NULL,
            codigo_recuperacao_hash TEXT,
            criado_em TEXT
        );
        """)

        # Bancos criados antes desta versão não têm a coluna data_servico
        colunas = [linha[1] for linha in conn.execute("PRAGMA table_info(pagamento)")]
        if "data_servico" not in colunas:
            conn.execute("ALTER TABLE pagamento ADD COLUMN data_servico TEXT")