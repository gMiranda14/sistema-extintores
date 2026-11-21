import ctypes
from pathlib import Path
from tkinter import messagebox

import customtkinter as ctk
from banco.conexao import criar_tabelas
from regras import backup, preferencias
from telas import estilo
from telas.tela_backup import TelaBackup
from telas.tela_clientes import TelaClientes
from telas.tela_equipamentos import TelaEquipamentos
from telas.tela_login import JanelaAlterarSenha, JanelaLogin
from telas.tela_pagamentos import TelaPagamentos
from telas.tela_vencimentos import TelaVencimentos

COR_ATIVA = "#1f6aa5"
TEXTO_MENU = ("#1a1a1a", "#DCE4EE")  # (modo claro, modo escuro)
HOVER_MENU = ("#cfe0f3", "#2d4f6e")
ICONE = Path(__file__).parent / "assets" / "logo.ico"

# Faz a barra de tarefas mostrar o ícone do sistema, e não o do Python
try:
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("sistema.extintores.app")
except Exception:
    pass


class Aplicativo(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.withdraw()  # a janela principal só aparece depois do login
        self.title("Sistema de Extintores")
        self.geometry("1150x720")
        self.protocol("WM_DELETE_WINDOW", self._ao_fechar)
        if ICONE.exists():
            self.after(250, lambda: self.iconbitmap(str(ICONE)))
        self.usuario = None
        self.interface_pronta = False
        self.tela_cheia = False
        self.bind("<F11>", self._alternar_tela_cheia)
        self.bind("<Escape>", self._sair_da_tela_cheia)
        self.after(100, self._pedir_login)

    # ---------- Acesso ----------
    def _pedir_login(self):
        self.withdraw()
        JanelaLogin(self, ao_entrar=self._entrou, ao_cancelar=self._ao_fechar)

    def _entrou(self, usuario):
        self.usuario = usuario
        if not self.interface_pronta:
            self._montar_interface()
            self.interface_pronta = True
        self.rotulo_usuario.configure(text=f"Usuário: {usuario['nome']}")
        self.mostrar("Vencimentos")
        self.deiconify()
        if not self.tela_cheia:
            self._maximizar()
            self.after(150, self._maximizar)
        self.lift()
        self.focus_force()

    # ---------- Tamanho da janela ----------
    def _maximizar(self):
        try:
            self.state("zoomed")  # Windows
        except Exception:
            try:
                self.attributes("-zoomed", True)  # Linux
            except Exception:
                pass

    def _alternar_tela_cheia(self, evento=None):
        """F11: alterna entre janela maximizada e tela cheia de verdade."""
        self.tela_cheia = not self.tela_cheia
        self.attributes("-fullscreen", self.tela_cheia)
        if not self.tela_cheia:
            self._maximizar()
        return "break"

    def _sair_da_tela_cheia(self, evento=None):
        if self.tela_cheia:
            self._alternar_tela_cheia()

    def _bloquear(self):
        self._pedir_login()

    def _alterar_senha(self):
        JanelaAlterarSenha(self, self.usuario["nome"])

    # ---------- Interface ----------
    def _montar_interface(self):
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        menu = ctk.CTkFrame(self, width=180, corner_radius=0)
        menu.grid(row=0, column=0, sticky="ns")
        ctk.CTkLabel(menu, text="Extintores", font=("Arial", 20, "bold")).pack(
            padx=20, pady=(20, 25)
        )

        # parte de baixo do menu: usuário, alterar senha e bloquear
        ctk.CTkButton(
            menu, text="Bloquear", width=150, fg_color="gray", command=self._bloquear
        ).pack(side="bottom", padx=15, pady=(4, 15))
        ctk.CTkButton(
            menu, text="Alterar senha", width=150, fg_color="transparent",
            text_color=TEXTO_MENU, border_width=1, command=self._alterar_senha,
        ).pack(side="bottom", padx=15, pady=4)
        self.rotulo_usuario = ctk.CTkLabel(menu, text="", text_color="gray")
        self.rotulo_usuario.pack(side="bottom", pady=(0, 6))

        self.area = ctk.CTkFrame(self, fg_color="transparent")
        self.area.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        self.area.columnconfigure(0, weight=1)
        self.area.rowconfigure(0, weight=1)

        self.telas = {
            "Vencimentos": TelaVencimentos(self.area),
            "Clientes": TelaClientes(self.area),
            "Equipamentos": TelaEquipamentos(self.area),
            "Pagamentos": TelaPagamentos(self.area),
            "Backup": TelaBackup(self.area),
        }
        self.botoes = {}
        for nome, tela in self.telas.items():
            tela.grid(row=0, column=0, sticky="nsew")
            botao = ctk.CTkButton(
                menu, text=nome, anchor="w", width=150,
                fg_color="transparent", hover_color=HOVER_MENU, text_color=TEXTO_MENU,
                command=lambda n=nome: self.mostrar(n),
            )
            botao.pack(padx=15, pady=4)
            self.botoes[nome] = botao

        estilo.aplicar_estilo_tabelas(self)

    def mostrar(self, nome):
        for n, botao in self.botoes.items():
            ativo = n == nome
            botao.configure(
                fg_color=COR_ATIVA if ativo else "transparent",
                text_color="white" if ativo else TEXTO_MENU,
            )
        tela = self.telas[nome]
        tela.tkraise()
        if hasattr(tela, "atualizar"):
            tela.atualizar()

    def _ao_fechar(self):
        try:
            erro = backup.backup_automatico()
        except Exception as falha:
            erro = str(falha)
        if erro:
            messagebox.showwarning(
                "Backup automático",
                f"Não foi possível fazer o backup automático:\n{erro}\n\n"
                "O programa será fechado mesmo assim.",
            )
        self.destroy()


def principal():
    criar_tabelas()
    estilo.definir_modo(preferencias.obter("modo", "escuro"), salvar=False)
    Aplicativo().mainloop()


if __name__ == "__main__":
    principal()