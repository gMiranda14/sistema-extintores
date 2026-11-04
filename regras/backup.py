import json
import re
import sqlite3
from datetime import date, datetime
from pathlib import Path

from banco.conexao import CAMINHO

# O arquivo de configuração fica na pasta do projeto (e está no .gitignore)
CONFIG = Path(__file__).resolve().parent.parent / "config.json"
PADRAO_NOME = re.compile(r"^dados_(\d{4}-\d{2}-\d{2})_(\d{6})\.db$")
MANTER = 30  # quantidade de backups guardados na pasta


def carregar_config():
    try:
        return json.loads(CONFIG.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def salvar_config(config):
    CONFIG.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")


def pasta_de_backup():
    pasta = carregar_config().get("pasta_backup")
    return Path(pasta) if pasta else None


def definir_pasta(pasta):
    config = carregar_config()
    config["pasta_backup"] = str(pasta)
    salvar_config(config)


def backup_automatico_ligado():
    return bool(carregar_config().get("backup_automatico", False))


def definir_backup_automatico(ligado):
    config = carregar_config()
    config["backup_automatico"] = bool(ligado)
    salvar_config(config)


def _arquivos_de_backup(pasta):
    arquivos = [a for a in Path(pasta).glob("dados_*.db") if PADRAO_NOME.match(a.name)]
    return sorted(arquivos, key=lambda a: a.name)


def fazer_backup(pasta, manter=MANTER):
    """Copia o banco para a pasta, com data e hora no nome. Devolve o caminho do arquivo."""
    pasta = Path(pasta)
    pasta.mkdir(parents=True, exist_ok=True)
    destino = pasta / f"dados_{datetime.now():%Y-%m-%d_%H%M%S}.db"

    origem = sqlite3.connect(CAMINHO)
    copia = sqlite3.connect(destino)
    try:
        origem.backup(copia)  # cópia segura, mesmo com o programa aberto
    finally:
        copia.close()
        origem.close()

    if not _copia_integra(destino):
        destino.unlink(missing_ok=True)
        raise RuntimeError("A cópia do banco não passou na verificação e foi descartada.")

    for antigo in _arquivos_de_backup(pasta)[:-manter]:
        antigo.unlink(missing_ok=True)
    return destino


def _copia_integra(arquivo):
    conn = sqlite3.connect(arquivo)
    try:
        return conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    finally:
        conn.close()


def ultimo_backup(pasta):
    """Devolve a data e hora do backup mais recente da pasta, ou None."""
    if pasta is None or not Path(pasta).exists():
        return None
    arquivos = _arquivos_de_backup(pasta)
    if not arquivos:
        return None
    dia, hora = PADRAO_NOME.match(arquivos[-1].name).groups()
    return datetime.strptime(f"{dia} {hora}", "%Y-%m-%d %H%M%S")


def backup_automatico():
    """Chamado ao fechar o programa. Faz no máximo um backup por dia.

    Devolve uma mensagem de erro, ou None se deu tudo certo (ou não era necessário)."""
    try:
        if not backup_automatico_ligado():
            return None
        pasta = pasta_de_backup()
        if pasta is None:
            return None
        ultimo = ultimo_backup(pasta)
        if ultimo is not None and ultimo.date() == date.today():
            return None
        fazer_backup(pasta)
        return None
    except Exception as erro:
        return str(erro)