import calendar
from datetime import date, datetime, timedelta

MESES_VALIDADE = 12
DIAS_ALERTA = 30


def br_para_iso(texto):
    """Converte '14/10/2026' em '2026-10-14'. Devolve None se for inválida."""
    if len(texto) != 10:
        return None
    try:
        return datetime.strptime(texto, "%d/%m/%Y").date().isoformat()
    except ValueError:
        return None


def iso_para_br(iso):
    """Converte '2026-10-14' em '14/10/2026'."""
    if not iso:
        return ""
    return date.fromisoformat(iso).strftime("%d/%m/%Y")


def somar_meses(data, meses):
    indice = data.month - 1 + meses
    ano = data.year + indice // 12
    mes = indice % 12 + 1
    dia = min(data.day, calendar.monthrange(ano, mes)[1])
    return date(ano, mes, dia)


def calcular_vencimento(data_referencia_iso):
    return somar_meses(date.fromisoformat(data_referencia_iso), MESES_VALIDADE)


def situacao(vencimento, hoje=None):
    hoje = hoje or date.today()
    if vencimento < hoje:
        return "Vencido"
    if vencimento <= hoje + timedelta(days=DIAS_ALERTA):
        return "Vence em breve"
    return "Em dia"