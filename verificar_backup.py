import os
import shutil
import sqlite3
import sys
import tempfile

BANCO_ATUAL = os.path.join("banco", "dados.db")


def contar_linhas(caminho):
    """Devolve (resultado do integrity_check, {tabela: linhas})."""
    con = sqlite3.connect(caminho)
    try:
        integridade = con.execute("PRAGMA integrity_check").fetchone()[0]
        tabelas = [
            r[0]
            for r in con.execute(
                "SELECT name FROM sqlite_master "
                "WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"
            )
        ]
        contagem = {}
        for nome in tabelas:
            contagem[nome] = con.execute(
                f'SELECT COUNT(*) FROM "{nome}"'
            ).fetchone()[0]
        return integridade, contagem
    finally:
        con.close()


def main():
    if len(sys.argv) != 2:
        print("Uso: python verificar_backup.py CAMINHO_DO_BACKUP.db")
        return

    backup = sys.argv[1]
    if not os.path.isfile(backup):
        print("Arquivo de backup não encontrado:", backup)
        return

    # Trabalha numa cópia, para não alterar o backup original.
    pasta_temp = tempfile.mkdtemp()
    copia = os.path.join(pasta_temp, "restaurado.db")
    shutil.copy2(backup, copia)

    integridade, no_backup = contar_linhas(copia)
    print("Integridade da cópia restaurada:", integridade)

    if not os.path.isfile(BANCO_ATUAL):
        print("Banco atual não encontrado em", BANCO_ATUAL)
        return
    _, no_atual = contar_linhas(BANCO_ATUAL)

    print()
    print(f"{'Tabela':<18}{'Backup':>8}{'Atual':>8}")
    for nome in sorted(set(no_backup) | set(no_atual)):
        b = no_backup.get(nome, "-")
        a = no_atual.get(nome, "-")
        aviso = "" if b == a else "  <- diferente"
        print(f"{nome:<18}{b!s:>8}{a!s:>8}{aviso}")

    shutil.rmtree(pasta_temp, ignore_errors=True)


main()