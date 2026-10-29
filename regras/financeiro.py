import math
import re
from datetime import date


def converter_valor(texto):
    """Converte '1.234,56', '150,5' ou '150.50' em número. Devolve None se inválido."""
    t = texto.replace("R$", "").replace(" ", "")
    if not t:
        return None
    if "," in t:
        t = t.replace(".", "").replace(",", ".")
    elif re.fullmatch(r"\d{1,3}(\.\d{3})+", t):
        t = t.replace(".", "")
    try:
        valor = float(t)
    except ValueError:
        return None
    if not math.isfinite(valor) or valor < 0:
        return None
    return round(valor, 2)


def formatar_moeda(valor):
    texto = f"{valor:,.2f}"
    return "R$ " + texto.replace(",", "X").replace(".", ",").replace("X", ".")


def status_pagamento(data_vencimento_iso, data_pagamento_iso, hoje=None):
    if data_pagamento_iso:
        return "Pago"
    hoje = hoje or date.today()
    if data_vencimento_iso and date.fromisoformat(data_vencimento_iso) < hoje:
        return "Atrasado"
    return "Pendente"