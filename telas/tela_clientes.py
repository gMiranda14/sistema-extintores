import re
import sqlite3
from tkinter import ttk, messagebox
import customtkinter as ctk
from modelos import cliente
from regras import validadores

CAMPOS = [
    ("nome", "Nome *"),
    ("cpf_cnpj", "Documento"),
    ("endereco", "Endereço"),
    ("telefone", "Telefone"),
    ("email", "E-mail"),
    ("forma_pagamento", "Forma de pagamento"),
    ("ultimo_valor", "Último valor cobrado (R$)"),
]
CHAVES = [chave for chave, _ in CAMPOS]
FORMAS = ["Dinheiro", "PIX", "Boleto", "Cartão de débito", "Cartão de crédito"]
PLACEHOLDERS = {"CPF": "000.000.000-00", "CNPJ": "00.000.000/0000-00"}


class FormularioCliente(ctk.CTkFrame):
    """Formulário reutilizado no cadastro novo e na janela de edição."""

    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        self.entradas = {}
        self.columnconfigure((0, 1), weight=1)

        for i, (chave, rotulo) in enumerate(CAMPOS):
            linha = (i // 2) * 2
            coluna = i % 2
            ctk.CTkLabel(self, text=rotulo).grid(
                row=linha, column=coluna, sticky="w", padx=5, pady=(8, 0)
            )
            if chave == "cpf_cnpj":
                campo = self._criar_campo_documento()
            elif chave == "forma_pagamento":
                campo = ctk.CTkComboBox(self, values=FORMAS, state="readonly")
                campo.set("")
            else:
                campo = ctk.CTkEntry(self)
            campo.grid(row=linha + 1, column=coluna, sticky="ew", padx=5)
            self.entradas[chave] = self.doc if chave == "cpf_cnpj" else campo

    # ---------- Campo de documento ----------
    def _criar_campo_documento(self):
        quadro = ctk.CTkFrame(self, fg_color="transparent")
        quadro.columnconfigure(1, weight=1)
        self.tipo = ctk.CTkSegmentedButton(
            quadro, values=["CPF", "CNPJ"], command=self._mudar_tipo, width=110
        )
        self.tipo.set("CPF")
        self.tipo.grid(row=0, column=0, padx=(0, 6))
        self.doc = ctk.CTkEntry(quadro, placeholder_text=PLACEHOLDERS["CPF"])
        self.doc.grid(row=0, column=1, sticky="ew")
        self.doc.bind("<KeyRelease>", self._mascarar)
        return quadro

    def _mudar_tipo(self, tipo):
        self.doc.delete(0, "end")
        self.doc.configure(placeholder_text=PLACEHOLDERS[tipo])

    def _mascarar(self, evento=None):
        texto = self.doc.get()
        novo = validadores.mascarar_documento(texto, self.tipo.get())
        if novo != texto:
            self.doc.delete(0, "end")
            self.doc.insert(0, novo)
            self.doc.icursor("end")

    # ---------- Preencher, limpar e ler ----------
    def preencher(self, linha):
        self.limpar()
        for chave, valor in zip(CHAVES, linha):
            if valor is None:
                continue
            if chave == "forma_pagamento":
                self.entradas[chave].set(valor)
            elif chave == "cpf_cnpj":
                limpo = re.sub(r"[^0-9A-Za-z]", "", valor)
                tipo = "CNPJ" if len(limpo) == 14 else "CPF"
                self.tipo.set(tipo)
                self._mudar_tipo(tipo)
                self.doc.insert(0, valor)
            elif chave == "ultimo_valor":
                self.entradas[chave].insert(0, f"{valor:.2f}".replace(".", ","))
            else:
                self.entradas[chave].insert(0, valor)

    def limpar(self):
        for chave, campo in self.entradas.items():
            if chave == "forma_pagamento":
                campo.set("")
            else:
                campo.delete(0, "end")
        self.tipo.set("CPF")
        self.doc.configure(placeholder_text=PLACEHOLDERS["CPF"])

    def ler(self):
        """Valida e devolve a tupla para o banco, ou None se houver erro."""
        janela = self.winfo_toplevel()
        valores = {chave: self.entradas[chave].get().strip() for chave in CHAVES}

        if not valores["nome"]:
            messagebox.showwarning("Atenção", "O nome é obrigatório.", parent=janela)
            return None

        if valores["cpf_cnpj"]:
            documento = validadores.normalizar_documento(valores["cpf_cnpj"])
            if documento is None:
                messagebox.showwarning(
                    "Atenção", f"{self.tipo.get()} inválido.", parent=janela
                )
                return None
            valores["cpf_cnpj"] = documento

        if valores["telefone"]:
            telefone = validadores.normalizar_telefone(valores["telefone"])
            if telefone is None:
                messagebox.showwarning(
                    "Atenção", "Telefone inválido. Use DDD + número.", parent=janela
                )
                return None
            valores["telefone"] = telefone

        if valores["email"] and not validadores.email_valido(valores["email"]):
            messagebox.showwarning("Atenção", "E-mail inválido.", parent=janela)
            return None

        if valores["endereco"] and len(valores["endereco"]) < 5:
            messagebox.showwarning(
                "Atenção", "O endereço está muito curto.", parent=janela
            )
            return None

        texto_valor = valores["ultimo_valor"].replace(",", ".")
        if texto_valor:
            try:
                valor = float(texto_valor)
            except ValueError:
                messagebox.showwarning(
                    "Atenção", "O último valor deve ser um número.", parent=janela
                )
                return None
        else:
            valor = None

        return (
            valores["nome"], valores["cpf_cnpj"], valores["endereco"],
            valores["telefone"], valores["email"], valores["forma_pagamento"],
            valor,
        )


class JanelaEdicao(ctk.CTkToplevel):
    """Janela que abre ao clicar num cliente da lista."""

    def __init__(self, master, id_cliente, ao_concluir):
        super().__init__(master)
        self.id_cliente = id_cliente
        self.ao_concluir = ao_concluir
        self.title("Editar cliente")
        self.geometry("720x420")
        self.transient(master.winfo_toplevel())

        ctk.CTkLabel(
            self, text="Editar cliente", font=("Arial", 20, "bold")
        ).pack(anchor="w", padx=15, pady=(15, 0))

        self.formulario = FormularioCliente(self)
        self.formulario.pack(fill="x", padx=10)
        self.formulario.preencher(cliente.buscar_por_id(id_cliente)[1:])

        botoes = ctk.CTkFrame(self, fg_color="transparent")
        botoes.pack(fill="x", padx=15, pady=15)
        ctk.CTkButton(botoes, text="Atualizar", command=self.atualizar).pack(
            side="left", padx=5
        )
        ctk.CTkButton(
            botoes, text="Cancelar", command=self.destroy, fg_color="gray"
        ).pack(side="left", padx=5)
        ctk.CTkButton(
            botoes, text="Excluir", command=self.excluir,
            fg_color="#b33a3a", hover_color="#8f2d2d",
        ).pack(side="right", padx=5)

        self.after(150, self._focar)

    def _focar(self):
        if self.winfo_exists():
            self.lift()
            self.focus()
            self.grab_set()

    def atualizar(self):
        dados = self.formulario.ler()
        if dados is None:
            return
        cliente.atualizar(self.id_cliente, dados)
        self.ao_concluir()
        self.destroy()

    def excluir(self):
        if not messagebox.askyesno("Confirmar", "Excluir este cliente?", parent=self):
            return
        try:
            cliente.excluir(self.id_cliente)
        except sqlite3.IntegrityError:
            messagebox.showerror(
                "Não foi possível excluir",
                "Este cliente tem equipamentos ou pagamentos cadastrados.",
                parent=self,
            )
            return
        self.ao_concluir()
        self.destroy()


class TelaClientes(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        self._montar_cadastro()
        self._montar_lista()
        self.carregar_lista()

    def _montar_cadastro(self):
        ctk.CTkLabel(
            self, text="Novo cliente", font=("Arial", 20, "bold")
        ).pack(anchor="w", padx=15, pady=(15, 0))

        self.formulario = FormularioCliente(self)
        self.formulario.pack(fill="x", padx=10)

        botoes = ctk.CTkFrame(self, fg_color="transparent")
        botoes.pack(fill="x", padx=15, pady=15)
        ctk.CTkButton(botoes, text="Salvar", command=self.salvar).pack(
            side="left", padx=5
        )
        ctk.CTkButton(
            botoes, text="Limpar", command=self.formulario.limpar, fg_color="gray"
        ).pack(side="left", padx=5)

    def _montar_lista(self):
        ctk.CTkLabel(
            self,
            text="Clientes cadastrados (clique em um cliente para editar)",
            font=("Arial", 16, "bold"),
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
        id_cliente = int(selecao[0])
        self.tabela.selection_remove(selecao)
        JanelaEdicao(self, id_cliente, self.carregar_lista)

    def salvar(self):
        dados = self.formulario.ler()
        if dados is None:
            return
        cliente.inserir(dados)
        self.formulario.limpar()
        self.carregar_lista()