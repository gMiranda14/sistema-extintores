import json
from pathlib import Path

# Mesmo arquivo da configuração do backup: cada parte guarda só as suas chaves
ARQUIVO = Path(__file__).resolve().parent.parent / "config.json"


def _carregar():
    try:
        return json.loads(ARQUIVO.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def obter(chave, padrao=None):
    return _carregar().get(chave, padrao)


def definir(chave, valor):
    """Guarda a preferência (ou apaga, se o valor for None). Nunca levanta erro."""
    dados = _carregar()
    if valor is None:
        dados.pop(chave, None)
    else:
        dados[chave] = valor
    try:
        ARQUIVO.write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError:
        pass  # lembrar o usuário é só uma comodidade