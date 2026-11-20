import re

from modelos import usuario
from regras import senhas

MENSAGEM_LOGIN = "Usuário ou senha incorretos."
MENSAGEM_CODIGO = "Usuário ou código de recuperação incorretos."
_hash_falso = None


def _gastar_tempo(senha):
    """Quando o usuário não existe, gasta o mesmo tempo de uma conferência de verdade."""
    global _hash_falso
    if _hash_falso is None:
        _hash_falso = senhas.gerar_hash("texto-qualquer")
    senhas.verificar(senha, _hash_falso)


def existe_usuario():
    return usuario.existe()


def _validar_nome(nome):
    if not 3 <= len(nome) <= 30:
        return "O usuário deve ter entre 3 e 30 caracteres."
    if not re.fullmatch(r"[A-Za-z0-9._-]+", nome):
        return "Use no usuário só letras sem acento, números, ponto, traço ou sublinhado."
    return None


def _validar_nova_senha(nome, nova, confirmacao):
    erro = senhas.validar_senha(nova, nome)
    if erro:
        return erro
    if nova != confirmacao:
        return "A confirmação da senha não confere."
    return None


def cadastrar_primeiro_usuario(nome, senha, confirmacao):
    """Devolve (usuário, código de recuperação, erro)."""
    nome = nome.strip()
    if usuario.existe():
        return None, None, "Já existe um usuário cadastrado."
    erro = _validar_nome(nome) or _validar_nova_senha(nome, senha, confirmacao)
    if erro:
        return None, None, erro
    codigo = senhas.gerar_codigo_recuperacao()
    id_usuario = usuario.criar(
        nome,
        senhas.gerar_hash(senha),
        senhas.gerar_hash(senhas.normalizar_codigo(codigo)),
    )
    return {"id": id_usuario, "nome": nome}, codigo, None


def entrar(nome, senha):
    """Devolve (usuário, erro)."""
    linha = usuario.buscar(nome.strip())
    if linha is None:
        _gastar_tempo(senha)
        return None, MENSAGEM_LOGIN
    id_usuario, nome_cadastrado, senha_hash, _ = linha
    if not senhas.verificar(senha, senha_hash):
        return None, MENSAGEM_LOGIN
    return {"id": id_usuario, "nome": nome_cadastrado}, None


def redefinir_senha(nome, codigo, nova, confirmacao):
    """Troca a senha usando o código de recuperação. Devolve (novo código, erro).

    O código vale uma vez só: ao usá-lo, um novo é gerado."""
    linha = usuario.buscar(nome.strip())
    if linha is None:
        _gastar_tempo(codigo)
        return None, MENSAGEM_CODIGO
    id_usuario, nome_cadastrado, _, codigo_hash = linha
    if not senhas.verificar(senhas.normalizar_codigo(codigo), codigo_hash):
        return None, MENSAGEM_CODIGO
    erro = _validar_nova_senha(nome_cadastrado, nova, confirmacao)
    if erro:
        return None, erro
    novo_codigo = senhas.gerar_codigo_recuperacao()
    usuario.atualizar_senha_e_codigo(
        id_usuario,
        senhas.gerar_hash(nova),
        senhas.gerar_hash(senhas.normalizar_codigo(novo_codigo)),
    )
    return novo_codigo, None


def alterar_senha(nome, atual, nova, confirmacao):
    """Troca a senha de quem já está logado. Devolve a mensagem de erro ou None."""
    linha = usuario.buscar(nome.strip())
    if linha is None or not senhas.verificar(atual, linha[2]):
        return "A senha atual está incorreta."
    erro = _validar_nova_senha(linha[1], nova, confirmacao)
    if erro:
        return erro
    if senhas.verificar(nova, linha[2]):
        return "A nova senha deve ser diferente da atual."
    usuario.atualizar_senha(linha[0], senhas.gerar_hash(nova))
    return None