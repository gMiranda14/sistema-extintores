import re


def _limpar_documento(texto):
    return re.sub(r"[.\-/\s]", "", texto).upper()

def cpf_valido(cpf):
    if len (cpf) != 11 or not cpf.isdigit() or cpf == cpf[0] * 11:
        return False
    for posicao in (9,10):
        soma = sum(int(cpf[n]) * (posicao + 1 - n) for n in range(posicao))
        digito = (soma * 10 % 11) % 10
        if digito != int(cpf[posicao]):
            return False
    return True

def cnpj_valido(cnpj):
    if not re.fullmatch(r"[0-9A-Z]{12}[0-9]{2}", cnpj) or cnpj == cnpj[0] * 14:
        return False
    pesos1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    pesos2 = [6] + pesos1
    for pesos, posicao in ((pesos1, 12), (pesos2, 13)):
        soma = sum((ord(c) - 48) * p for c, p in zip(cnpj, pesos))
        resto = soma % 11
        digito = 0 if resto < 2 else 11 - resto
        if digito != int(cnpj[posicao]):
            return False
    return True


def normalizar_documento(texto):
    """Devolve o CPF/CNPJ formatado, ou None se for inválido."""
    d = _limpar_documento(texto)
    if len(d) == 11 and cpf_valido(d):
        return f"{d[:3]}.{d[3:6]}.{d[6:9]}-{d[9:]}"
    if len(d) == 14 and cnpj_valido(d):
        return f"{d[:2]}.{d[2:5]}.{d[5:8]}/{d[8:12]}-{d[12:]}"
    return None


def normalizar_telefone(texto):
    """Devolve o telefone formatado, ou None se for inválido."""
    d = re.sub(r"\D", "", texto)
    if d.startswith("55") and len(d) in (12, 13):
        d = d[2:]
    if len(d) not in (10, 11) or d[0] == "0" or d[1] == "0":
        return None
    if len(d) == 11:
        if d[2] != "9":
            return None
        return f"({d[:2]}) {d[2:7]}-{d[7:]}"
    return f"({d[:2]}) {d[2:6]}-{d[6:]}"


def email_valido(texto):
    return re.fullmatch(r"[\w.+-]+@[\w-]+(\.[\w-]+)+", texto) is not None

MASCARA_CPF = "###.###.###-##"
MASCARA_CNPJ = "##.###.###/####-##"


def aplicar_mascara(valor, modelo):
    saida = ""
    i = 0
    for caractere in modelo:
        if i >= len(valor):
            break
        if caractere == "#":
            saida += valor[i]
            i += 1
        else:
            saida += caractere
    return saida


def mascarar_documento(texto, tipo):
    if tipo == "CPF":
        limpo = re.sub(r"\D", "", texto)[:11]
        return aplicar_mascara(limpo, MASCARA_CPF)
    limpo = re.sub(r"[^0-9A-Za-z]", "", texto).upper()[:14]
    return aplicar_mascara(limpo, MASCARA_CNPJ)