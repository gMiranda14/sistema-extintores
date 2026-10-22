import ctypes
from pathlib import Path

import customtkinter as ctk
from banco.conexao import criar_tabelas
from telas.tela_clientes import TelaClientes
from telas.tela_equipamentos import TelaEquipamentos

criar_tabelas()
ctk.set_appearance_mode("dark")

COR_ATIVA = "#1f6aa5"
ICONE = Path(__file__).parent / "assets" / "logo.ico"

# Faz a barra de tarefas mostrar o ícone do sistema, e não o do Python
try:
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("sistema.extintores.app")
except Exception:
    pass


class Aplicativo(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Sistema de Extintores")
        self.geometry("1150x720")
        if ICONE.exists():
            self.after(250, lambda: self.iconbitmap(str(ICONE)))
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        menu = ctk.CTkFrame(self, width=180, corner_radius=0)
        menu.grid(row=0, column=0, sticky="ns")
        ctk.CTkLabel(menu, text="Extintores", font=("Arial", 20, "bold")).pack(
            padx=20, pady=(20, 25)
        )

        self.area = ctk.CTkFrame(self, fg_color="transparent")
        self.area.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        self.area.columnconfigure(0, weight=1)
        self.area.rowconfigure(0, weight=1)

        self.telas = {
            "Clientes": TelaClientes(self.area),
            "Equipamentos": TelaEquipamentos(self.area),
        }
        self.botoes = {}
        for nome, tela in self.telas.items():
            tela.grid(row=0, column=0, sticky="nsew")
            botao = ctk.CTkButton(
                menu, text=nome, anchor="w", width=150,
                fg_color="transparent", hover_color="#2d4f6e",
                command=lambda n=nome: self.mostrar(n),
            )
            botao.pack(padx=15, pady=4)
            self.botoes[nome] = botao

        self.mostrar("Clientes")

    def mostrar(self, nome):
        for n, botao in self.botoes.items():
            botao.configure(fg_color=COR_ATIVA if n == nome else "transparent")
        tela = self.telas[nome]
        tela.tkraise()
        if hasattr(tela, "atualizar"):
            tela.atualizar()


Aplicativo().mainloop()