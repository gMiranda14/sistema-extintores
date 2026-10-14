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
        CREATE TABLE IF NOT EXISTS extintor (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id INTEGER NOT NULL REFERENCES cliente(id),
            tipo TEXT,
            capacidade TEXT,
            numero_serie TEXT,
            ultima_manutencao TEXT
        );
        CREATE TABLE IF NOT EXISTS pagamento (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id INTEGER NOT NULL REFERENCES cliente(id),
            valor REAL NOT NULL,
            forma TEXT,
            data_vencimento TEXT,
            data_pagamento TEXT,
            status TEXT DEFAULT 'pendente',
            numero_nf TEXT
        );
        """)