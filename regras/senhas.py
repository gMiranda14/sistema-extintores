import hashlib
import hmac
import secrets

ITERACOES = 600_000
TAMANHO_MINIMO = 8
# Alfabeto do código de recuperação, sem 0, O, 1 e I, que se confundem na hora de anotar
ALFABETO_CODIGO = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
SENHAS_COMUNS = {
    "12345678", "123456789", "1234567890", "senha123", "senha1234", "password",
    "password1", "qwerty123", "admin123", "11111111", "00000000", "abc12345",
}


def gerar_hash(texto):
    """Transforma a senha (ou o código) num texto que não permite descobrir o original."""
    sal = secrets.token_bytes(16)
    resultado = hashlib.pbkdf2_hmac("sha256", texto.encode("utf-8"), sal, ITERACOES)
    return f"pbkdf2_sha256${ITERACOES}${sal.hex()}${resultado.hex()}"


def verificar(texto, armazenado):
    try:
        algoritmo, iteracoes, sal, esperado = armazenado.split("$")
        if algoritmo != "pbkdf2_sha256":
            return False
        calculado = hashlib.pbkdf2_hmac(
            "sha256", texto.encode("utf-8"), bytes.fromhex(sal), int(iteracoes)
        )
    except (ValueError, AttributeError):
        return False
    return hmac.compare_digest(calculado.hex(), esperado)


def gerar_codigo_recuperacao():
    """Código no formato XXXX-XXXX-XXXX-XXXX."""
    letras = [secrets.choice(ALFABETO_CODIGO) for _ in range(16)]
    return "-".join("".join(letras[i:i + 4]) for i in range(0, 16, 4))


def normalizar_codigo(texto):
    """Ignora hífens, espaços e maiúsculas ou minúsculas ao digitar o código."""
    return "".join(c for c in texto.upper() if c.isalnum())


def validar_senha(senha, nome_usuario):
    """Devolve a mensagem de erro, ou None se a senha for aceitável."""
    if len(senha) < TAMANHO_MINIMO:
        return f"A senha deve ter pelo menos {TAMANHO_MINIMO} caracteres."
    if senha.isdigit():
        return "A senha não pode ter só números."
    if senha.lower() == nome_usuario.strip().lower():
        return "A senha não pode ser igual ao usuário."
    if senha.lower() in SENHAS_COMUNS:
        return "Essa senha é muito comum. Escolha outra."
    return None