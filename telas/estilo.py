import tkinter as tk
from tkinter import ttk

import customtkinter as ctk
from regras import preferencias

# Para aumentar ou diminuir a letra das tabelas, mude só estes números:
TAMANHO_FONTE = 10
ALTURA_LINHA = 32  # em geral, cerca de 2,8 vezes o tamanho da fonte
TAMANHO_FONTE_LISTA = 12 # letra da lista que abre no campo Cliente

ESCURO = {
    "fundo": "#2b2b2b", "texto": "#ffffff", "cabecalho": "#3a3a3a",
    "borda": "#565b5e", "selecao": "#1f6aa5", "texto_selecao": "#ffffff",
}
CLARO = {
    "fundo": "#ffffff", "texto": "#1a1a1a", "cabecalho": "#cfcfcf",
    "borda": "#a8a8a8", "selecao": "#1f6aa5", "texto_selecao": "#ffffff",
}

# Cores de situação das linhas das tabelas: (modo claro, modo escuro)
CORES_SITUACAO = {
    "vencido": ("#c0392b", "#ff6b6b"),
    "atrasado": ("#c0392b", "#ff6b6b"),
    "breve": ("#b35c00", "#ffb347"),
    "pendente": ("#b35c00", "#ffb347"),
    "pago": ("#2e7d4f", "#6bcb77"),
}
# Cores que as telas já usam nos números e rótulos (versão para fundo escuro),
# trocadas por um par (claro, escuro) para ficarem legíveis nos dois modos
TRADUCAO_TEXTO = {
    "#ff6b6b": ("#c0392b", "#ff6b6b"),
    "#ffb347": ("#b35c00", "#ffb347"),
    "#6bcb77": ("#2e7d4f", "#6bcb77"),
    "#6fb1ff": ("#1f6aa5", "#6fb1ff"),
}


def modo_claro():
    return ctk.get_appearance_mode() == "Light"


def paleta():
    return CLARO if modo_claro() else ESCURO


def definir_modo(modo, salvar=True):
    """modo = 'claro' ou 'escuro'."""
    ctk.set_appearance_mode("light" if modo == "claro" else "dark")
    if salvar:
        preferencias.definir("modo", modo)


def trocar_modo(modo, raiz=None):
    """Troca o modo, guarda a escolha e refaz as cores do que já está na tela."""
    definir_modo(modo)
    aplicar_estilo_tabelas(raiz)


def aplicar_estilo_tabelas(raiz=None):
    """Estilo único de todas as tabelas do sistema (Treeview).

    Com a janela principal em 'raiz', também acerta as cores de situação das linhas
    e dos números que já foram criados."""
    cores = paleta()
    estilo = ttk.Style()
    estilo.theme_use("default")
    estilo.configure(
        "Treeview", background=cores["fundo"], foreground=cores["texto"],
        fieldbackground=cores["fundo"], rowheight=ALTURA_LINHA, borderwidth=0,
        font=("Arial", TAMANHO_FONTE),
    )
    estilo.configure(
        "Treeview.Heading", background=cores["cabecalho"], foreground=cores["texto"],
        relief="flat", font=("Arial", TAMANHO_FONTE, "bold"),
    )
    estilo.map(
        "Treeview",
        background=[("selected", cores["selecao"])],
        foreground=[("selected", cores["texto_selecao"])],
    )
    if raiz is not None:
        _acertar_cores(raiz)


def _acertar_cores(widget):
    indice = 0 if modo_claro() else 1
    if isinstance(widget, ttk.Treeview):
        for etiqueta, par in CORES_SITUACAO.items():
            widget.tag_configure(etiqueta, foreground=par[indice])
    elif isinstance(widget, ctk.CTkLabel):
        atual = widget.cget("text_color")
        if isinstance(atual, str) and atual.lower() in TRADUCAO_TEXTO:
            widget.configure(text_color=TRADUCAO_TEXTO[atual.lower()])
    for filho in widget.winfo_children():
        _acertar_cores(filho)