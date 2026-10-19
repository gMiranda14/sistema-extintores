import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
import customtkinter as ctk
from modelos import cliente
from regras import validadores

CAMPOS = [
    ("nome", "Nome *"),
    ("cpf_cnpj", "CPF/CNPJ"),
    ("endereco", "Endereço"),
    ("telefone", "Telefone"),
    ("email", "E-mail"),
    ("forma_pagamento", "Forma de pagamento"),
    ("ultimo_valor", "Último valor cobrado (R$)"),
]
CHAVES = [chave for chave, _ in CAMPOS]
FORMAS = ["", "Dinheiro", "PIX", "Boleto", "Cartão de débito", "Cartão de crédito"]


class TelaClientes(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        self.id_selecionado = None
        self.entradas = {}
        self._montar_formulario()
        self._montar_lista()
        self.carregar_lista()

    # ---------- Montagem da tela ----------
    def _montar_formulario(self):
        self.titulo = ctk.CTkLabel(self, text="Novo cliente", font=("Arial", 20, "bold"))
        self.titulo.pack(anchor="w", padx=15, pady=(15, 5))

        form = ctk.CTkFrame(self, fg_color="transparent")
        form.pack(fill="x", padx=15)
        form.columnconfigure((0, 1), weight=1)

        for i, (chave, rotulo) in enumerate(CAMPOS):
            linha = (i // 2) * 2
            coluna = i % 2
            ctk.CTkLabel(form, text=rotulo).grid(
                row=linha, column=coluna, sticky="w", padx=5, pady=(8, 0)
            )
            if chave == "forma_pagamento":
                campo = ctk.CTkComboBox(form, values=FORMAS)
                campo.set("")
            else:
                campo = ctk.CTkEntry(form)
            campo.grid(row=linha + 1, column=coluna, sticky="ew", padx=5)
            self.entradas[chave] = campo

        botoes = ctk.CTkFrame(self, fg_color="transparent")
        botoes.pack(fill="x", padx=15, pady=15)
        self.btn_salvar = ctk.CTkButton(botoes, text="Salvar", command=self.salvar)
        self.btn_salvar.pack(side="left", padx=5)
        ctk.CTkButton(
            botoes, text="Limpar", command=self.limpar, fg_color="gray"
        ).pack(side="left", padx=5)
        ctk.CTkButton(
            botoes, text="Excluir", command=self.excluir,
            fg_color="#b33a3a", hover_color="#8f2d2d",
        ).pack(side="left", padx=5)

    def _montar_lista(self):
        ctk.CTkLabel(
            self, text="Clientes cadastrados", font=("Arial", 16, "bold")
        ).pack(anchor="w", padx=15)

        self.busca = ctk.CTkEntry(self, placeholder_text="Buscar por nome...")
        self.busca.pack(fill="x", padx=15, pady=5)
        self.busca.bind("<KeyRelease>", lambda evento: self.carregar_lista())

        quadro = ctk.CTkFrame(self)
        quadro.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        estilo = ttk.Style()
        estilo.theme_use("default")
        estilo.configure(
            "Treeview", background="#2b2b2b", foreground="white",
            fieldbackground="#2b2b2b", rowheight=26, borderwidth=0,
        )
        estilo.configure(
            "Treeview.Heading", background="#3a3a3a", foreground="white", relief="flat"
        )
        estilo.map("Treeview", background=[("selected", "#1f6aa5")])

        titulos = {
            "nome": "Nome",
            "cpf_cnpj": "CPF/CNPJ",
            "telefone": "Telefone",
            "forma": "Forma de pagamento",
            "valor": "Último valor",
        }
        self.tabela = ttk.Treeview(
            quadro, columns=list(titulos), show="headings", selectmode="browse"
        )
        for coluna, texto in titulos.items():
            self.tabela.heading(coluna, text=texto)
            self.tabela.column(coluna, width=150)

        barra = ttk.Scrollbar(quadro, orient="vertical", command=self.tabela.yview)
        self.tabela.configure(yscrollcommand=barra.set)
        self.tabela.pack(side="left", fill="both", expand=True)
        barra.pack(side="right", fill="y")
        self.tabela.bind("<<TreeviewSelect>>", self._ao_selecionar)

    # ---------- Lista ----------
    def carregar_lista(self):
        for item in self.tabela.get_children():
            self.tabela.delete(item)
        for id_, nome, cpf, telefone, forma, valor in cliente.listar(self.busca.get().strip()):
            valor_txt = f"R$ {valor:.2f}".replace(".", ",") if valor is not None else ""
            self.tabela.insert(
                "", "end", iid=str(id_),
                values=(nome, cpf, telefone, forma, valor_txt),
            )

    def _ao_selecionar(self, evento=None):
        selecao = self.tabela.selection()
        if not selecao:
            return
        self.id_selecionado = int(selecao[0])
        linha = cliente.buscar_por_id(self.id_selecionado)
        for chave, valor in zip(CHAVES, linha[1:]):
            self._preencher(chave, valor)
        self.titulo.configure(text="Editando cliente")
        self.btn_salvar.configure(text="Atualizar")

    def _preencher(self, chave, valor):
        campo = self.entradas[chave]
        if chave == "forma_pagamento":
            campo.set(valor or "")
            return
        campo.delete(0, "end")
        if valor is None:
            return
        if chave == "ultimo_valor":
            valor = f"{valor:.2f}".replace(".", ",")
        campo.insert(0, valor)

    # ---------- Ações dos botões ----------
    def _ler_formulario(self):
        valores = {chave: self.entradas[chave].get().strip() for chave in CHAVES}

        if not valores["nome"]:
            messagebox.showwarning("Atenção", "O nome é obrigatório.")
            return None

        if valores["cpf_cnpj"]:
            documento = validadores.normalizar_documento(valores["cpf_cnpj"])
            if documento is None:
                messagebox.showwarning("Atenção", "CPF ou CNPJ inválido.")
                return None
            valores["cpf_cnpj"] = documento

        if valores["telefone"]:
            telefone = validadores.normalizar_telefone(valores["telefone"])
            if telefone is None:
                messagebox.showwarning(
                    "Atenção", "Telefone inválido. Use DDD + número."
                )
                return None
            valores["telefone"] = telefone

        if valores["email"] and not validadores.email_valido(valores["email"]):
            messagebox.showwarning("Atenção", "E-mail inválido.")
            return None

        if valores["endereco"] and len(valores["endereco"]) < 5:
            messagebox.showwarning("Atenção", "O endereço está muito curto.")
            return None

        texto_valor = valores["ultimo_valor"].replace(",", ".")
        if texto_valor:
            try:
                valor = float(texto_valor)
            except ValueError:
                messagebox.showwarning("Atenção", "O último valor deve ser um número.")
                return None
        else:
            valor = None

        return (
            valores["nome"], valores["cpf_cnpj"], valores["endereco"],
            valores["telefone"], valores["email"], valores["forma_pagamento"],
            valor,
        )

    def salvar(self):
        dados = self._ler_formulario()
        if dados is None:
            return
        if self.id_selecionado is None:
            cliente.inserir(dados)
        else:
            cliente.atualizar(self.id_selecionado, dados)
        self.limpar()
        self.carregar_lista()

    def excluir(self):
        if self.id_selecionado is None:
            messagebox.showwarning("Atenção", "Selecione um cliente na lista.")
            return
        if not messagebox.askyesno("Confirmar", "Excluir este cliente?"):
            return
        try:
            cliente.excluir(self.id_selecionado)
        except sqlite3.IntegrityError:
            messagebox.showerror(
                "Não foi possível excluir",
                "Este cliente tem equipamentos ou pagamentos cadastrados.",
            )
            return
        self.limpar()
        self.carregar_lista()

    def limpar(self):
        self.id_selecionado = None
        for chave, campo in self.entradas.items():
            if chave == "forma_pagamento":
                campo.set("")
            else:
                campo.delete(0, "end")
        self.tabela.selection_remove(self.tabela.selection())
        self.titulo.configure(text="Novo cliente")
        self.btn_salvar.configure(text="Salvar")