import re
import sqlite3
import tkinter as tk
import unicodedata
from datetime import date
from tkinter import ttk, messagebox
import customtkinter as ctk
from modelos import cliente, equipamento
from regras import validadores, vencimentos

TIPOS = {"Extintor": "extintor", "Mangueira": "mangueira"}
NOMES_TIPO = {valor: nome for nome, valor in TIPOS.items()}
ICONES_TEXTO = "✎        🗑"

def _normalizar(texto):
    decomposto = unicodedata.normalize("NFD", texto)
    sem_acento = "".join(c for c in decomposto if unicodedata.category(c) != "Mn")
    return sem_acento.lower()


class SeletorCliente(ctk.CTkFrame):
    """Campo com busca: digite parte do nome ou do CPF/CNPJ e escolha na lista."""

    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        self.itens = []  # (rótulo, nome sem acento, documento só com números)
        self.popup = None
        self.lista = None
        self.columnconfigure(0, weight=1)

        self.entrada = ctk.CTkEntry(
            self, placeholder_text="Digite o nome ou o CPF/CNPJ..."
        )
        self.entrada.grid(row=0, column=0, sticky="ew")
        self.botao = ctk.CTkButton(
            self, text="▼", width=32, command=self._alternar_lista
        )
        self.botao.grid(row=0, column=1, padx=(4, 0))

        self.entrada.bind("<KeyRelease>", self._ao_digitar)
        self.entrada.bind("<Down>", lambda e: self._mover(1))
        self.entrada.bind("<Up>", lambda e: self._mover(-1))
        self.entrada.bind("<Return>", self._confirmar)
        self.entrada.bind("<Escape>", lambda e: self._fechar())
        self.entrada.bind("<FocusOut>", lambda e: self.after(200, self._fechar_sem_foco))

        janela = self.winfo_toplevel()
        janela.bind("<Button-1>", self._clique_fora, add="+")
        janela.bind("<Configure>", self._janela_mexeu, add="+")

    # ---------- Interface usada pelo formulário ----------
    def carregar(self, itens):
        """itens = lista de (rótulo, nome, documento)."""
        self.itens = [
            (rotulo, _normalizar(nome), re.sub(r"[^0-9a-z]", "", doc.lower()))
            for rotulo, nome, doc in itens
        ]

    def get(self):
        return self.entrada.get()

    def set(self, texto):
        self.entrada.delete(0, "end")
        if texto:
            self.entrada.insert(0, texto)
        self._fechar()

    # ---------- Filtro ----------
    def _todos(self):
        return [rotulo for rotulo, _, _ in self.itens]

    def _filtrar(self, texto):
        texto = texto.strip()
        if not texto or texto in self._todos():
            return self._todos()
        busca = _normalizar(texto)
        busca_doc = re.sub(r"[^0-9a-z]", "", busca)
        achados = []
        for rotulo, nome, doc in self.itens:
            if busca in nome or (busca_doc and busca_doc in doc):
                achados.append(rotulo)
        return achados

    # ---------- Lista suspensa ----------
    def _popup_aberto(self):
        return self.popup is not None and self.popup.winfo_exists()

    def _abrir(self, rotulos):
        if not rotulos:
            self._fechar()
            return
        if not self._popup_aberto():
            self.popup = tk.Toplevel(self.winfo_toplevel())
            self.popup.overrideredirect(True)
            self.popup.attributes("-topmost", True)
            self.lista = tk.Listbox(
                self.popup, activestyle="none", exportselection=False,
                bg="#2b2b2b", fg="white", selectbackground="#1f6aa5",
                selectforeground="white", highlightthickness=1,
                highlightbackground="#565b5e", highlightcolor="#565b5e",
                borderwidth=0, font=("Arial", 11),
            )
            self.lista.pack(fill="both", expand=True)
            self.lista.bind("<Button-1>", self._clicar_na_lista)

        self.lista.delete(0, "end")
        for rotulo in rotulos:
            self.lista.insert("end", rotulo)
        self.lista.configure(height=min(len(rotulos), 8))
        self.popup.update_idletasks()

        x = self.entrada.winfo_rootx()
        y = self.entrada.winfo_rooty() + self.entrada.winfo_height() + 2
        largura = self.entrada.winfo_width() + self.botao.winfo_width() + 4
        altura = self.lista.winfo_reqheight()
        self.popup.geometry(f"{largura}x{altura}+{x}+{y}")
        self.popup.lift()

    def _fechar(self):
        if self._popup_aberto():
            self.popup.destroy()
        self.popup = None
        self.lista = None

    def _alternar_lista(self):
        if self._popup_aberto():
            self._fechar()
            return
        self.entrada.focus_set()
        self._abrir(self._filtrar(self.entrada.get()))

    def _escolher(self, rotulo):
        self.set(rotulo)
        self.entrada.focus_set()

    # ---------- Eventos ----------
    def _ao_digitar(self, evento):
        if evento.keysym in ("Down", "Up", "Return", "Escape", "Tab",
                             "Left", "Right", "Home", "End",
                             "Shift_L", "Shift_R", "Control_L", "Control_R"):
            return
        self._abrir(self._filtrar(self.entrada.get()))

    def _mover(self, passo):
        if not self._popup_aberto():
            self._abrir(self._filtrar(self.entrada.get()))
        if not self._popup_aberto():
            return "break"
        total = self.lista.size()
        atual = self.lista.curselection()
        if atual:
            novo = atual[0] + passo
        else:
            novo = 0 if passo > 0 else total - 1
        novo = max(0, min(novo, total - 1))
        self.lista.selection_clear(0, "end")
        self.lista.selection_set(novo)
        self.lista.see(novo)
        return "break"

    def _confirmar(self, evento=None):
        if not self._popup_aberto():
            return
        selecionado = self.lista.curselection()
        if selecionado:
            self._escolher(self.lista.get(selecionado[0]))
        elif self.lista.size() == 1:
            self._escolher(self.lista.get(0))
        return "break"

    def _clicar_na_lista(self, evento):
        indice = self.lista.nearest(evento.y)
        if 0 <= indice < self.lista.size():
            self._escolher(self.lista.get(indice))
        return "break"

    def _clique_fora(self, evento):
        if not self._popup_aberto():
            return
        alvo = self.winfo_containing(evento.x_root, evento.y_root)
        if alvo is not None and str(alvo).startswith(str(self)):
            return
        self._fechar()

    def _janela_mexeu(self, evento):
        if evento.widget is self.winfo_toplevel():
            self._fechar()

    def _fechar_sem_foco(self):
        try:
            if not self.winfo_exists():
                return
            foco = self.focus_get()
            if foco is not None and (foco is self.lista or str(foco).startswith(str(self))):
                return
        except Exception:
            pass
        self._fechar()

class FormularioEquipamento(ctk.CTkFrame):
    """Formulário usado no cadastro novo e na janela de edição."""

    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        self.rotulo_para_id = {}
        self.id_para_rotulo = {}
        self.columnconfigure((0, 1), weight=1)

        self._rotulo("Cliente *", 0, 0)
        self.campo_cliente = SeletorCliente(self)
        self.campo_cliente.grid(row=1, column=0, sticky="ew", padx=5)

        self._rotulo("Tipo *", 0, 1)
        self.campo_tipo = ctk.CTkComboBox(self, values=list(TIPOS), state="readonly")
        self.campo_tipo.grid(row=1, column=1, sticky="ew", padx=5)

        self._rotulo("Descrição (ex.: pó químico ABC)", 2, 0)
        self.descricao = ctk.CTkEntry(self)
        self.descricao.grid(row=3, column=0, sticky="ew", padx=5)

        self._rotulo("Capacidade (ex.: 6 kg)", 2, 1)
        self.capacidade = ctk.CTkEntry(self)
        self.capacidade.grid(row=3, column=1, sticky="ew", padx=5)

        self._rotulo("Número de série", 4, 0)
        self.numero_serie = ctk.CTkEntry(self)
        self.numero_serie.grid(row=5, column=0, sticky="ew", padx=5)

        self._rotulo("Data da última manutenção, venda ou teste *", 4, 1)
        self.data = ctk.CTkEntry(self, placeholder_text="dd/mm/aaaa")
        self.data.grid(row=5, column=1, sticky="ew", padx=5)
        self.data.bind("<KeyRelease>", self._mascarar_data)

        self.recarregar_clientes()
        self.limpar()

    def _rotulo(self, texto, linha, coluna):
        ctk.CTkLabel(self, text=texto).grid(
            row=linha, column=coluna, sticky="w", padx=5, pady=(8, 0)
        )

    def _mascarar_data(self, evento=None):
        texto = self.data.get()
        novo = validadores.mascarar_data(texto)
        if novo != texto:
            self.data.delete(0, "end")
            self.data.insert(0, novo)
            self.data.icursor("end")

    # ---------- Clientes da lista de escolha ----------
    def recarregar_clientes(self):
        atual = self.campo_cliente.get()
        self.rotulo_para_id = {}
        self.id_para_rotulo = {}
        itens = []

        clientes = cliente.listar_para_selecao()
        rotulos = [f"{nome} - {doc}" if doc else nome for _, nome, doc in clientes]

        for (id_, nome, doc), rotulo in zip(clientes, rotulos):
            if rotulos.count(rotulo) > 1:
                rotulo = f"{rotulo} (nº {id_})"
            self.rotulo_para_id[rotulo] = id_
            self.id_para_rotulo[id_] = rotulo
            itens.append((rotulo, nome, doc or ""))

        self.campo_cliente.carregar(itens)
        if atual not in self.rotulo_para_id:
            self.campo_cliente.set("")

    # ---------- Preencher, limpar e ler ----------
    def preencher(self, linha):
        cliente_id, tipo, descricao, capacidade, serie, data_iso = linha
        self.limpar()
        self.campo_cliente.set(self.id_para_rotulo.get(cliente_id, ""))
        self.campo_tipo.set(NOMES_TIPO.get(tipo, "Extintor"))
        self.descricao.insert(0, descricao or "")
        self.capacidade.insert(0, capacidade or "")
        self.numero_serie.insert(0, serie or "")
        self.data.insert(0, vencimentos.iso_para_br(data_iso))

    def limpar(self):
        self.campo_cliente.set("")
        self.campo_tipo.set("Extintor")
        for campo in (self.descricao, self.capacidade, self.numero_serie, self.data):
            campo.delete(0, "end")

    def ler(self):
        """Valida e devolve a tupla para o banco, ou None se houver erro."""
        janela = self.winfo_toplevel()

        rotulo = self.campo_cliente.get()
        if rotulo not in self.rotulo_para_id:
            messagebox.showwarning("Atenção", "Escolha o cliente.", parent=janela)
            return None

        data_iso = vencimentos.br_para_iso(self.data.get().strip())
        if data_iso is None:
            messagebox.showwarning(
                "Atenção", "Data inválida. Use o formato dd/mm/aaaa.", parent=janela
            )
            return None
        if date.fromisoformat(data_iso) > date.today():
            messagebox.showwarning(
                "Atenção", "A data não pode estar no futuro.", parent=janela
            )
            return None

        return (
            self.rotulo_para_id[rotulo],
            TIPOS[self.campo_tipo.get()],
            self.descricao.get().strip(),
            self.capacidade.get().strip(),
            self.numero_serie.get().strip(),
            data_iso,
        )


class JanelaEdicaoEquipamento(ctk.CTkToplevel):
    def __init__(self, master, id_equipamento, ao_concluir):
        super().__init__(master)
        self.id_equipamento = id_equipamento
        self.ao_concluir = ao_concluir
        self.title("Editar equipamento")
        self.geometry("720x340")
        self.transient(master.winfo_toplevel())

        ctk.CTkLabel(
            self, text="Editar equipamento", font=("Arial", 20, "bold")
        ).pack(anchor="w", padx=15, pady=(15, 0))

        self.formulario = FormularioEquipamento(self)
        self.formulario.pack(fill="x", padx=10)
        self.formulario.preencher(equipamento.buscar_por_id(id_equipamento))

        botoes = ctk.CTkFrame(self, fg_color="transparent")
        botoes.pack(fill="x", padx=15, pady=15)
        ctk.CTkButton(botoes, text="Atualizar", command=self.atualizar).pack(
            side="left", padx=5
        )
        ctk.CTkButton(
            botoes, text="Cancelar", command=self.destroy, fg_color="gray"
        ).pack(side="left", padx=5)

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
        equipamento.atualizar(self.id_equipamento, dados)
        self.ao_concluir()
        self.destroy()


class TelaEquipamentos(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        self.janela_edicao = None
        self._montar_cadastro()
        self._montar_lista()
        self.carregar_lista()

    def atualizar(self):
        """Chamada pelo menu sempre que a tela é aberta."""
        self.formulario.recarregar_clientes()
        self.carregar_lista()

    def _montar_cadastro(self):
        ctk.CTkLabel(
            self, text="Novo equipamento", font=("Arial", 20, "bold")
        ).pack(anchor="w", padx=15, pady=(15, 0))

        self.formulario = FormularioEquipamento(self)
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
            self, text="Equipamentos cadastrados", font=("Arial", 16, "bold")
        ).pack(anchor="w", padx=15)

        self.busca = ctk.CTkEntry(self, placeholder_text="Buscar por cliente ou nº de série...")
        self.busca.pack(fill="x", padx=15, pady=5)
        self.busca.bind("<KeyRelease>", lambda evento: self.carregar_lista())

        quadro = ctk.CTkFrame(self)
        quadro.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        estilo = ttk.Style()
        estilo.theme_use("default")
        estilo.configure(
            "Treeview", background="#2b2b2b", foreground="white",
            fieldbackground="#2b2b2b", rowheight=28, borderwidth=0,
        )
        estilo.configure(
            "Treeview.Heading", background="#3a3a3a", foreground="white", relief="flat"
        )
        estilo.map("Treeview", background=[("selected", "#1f6aa5")])

        titulos = {
            "cliente": "Cliente",
            "tipo": "Tipo",
            "descricao": "Descrição",
            "capacidade": "Capacidade",
            "serie": "Nº de série",
            "data": "Última data",
            "vencimento": "Vencimento",
            "situacao": "Situação",
            "acoes": "Ações",
        }
        self.tabela = ttk.Treeview(
            quadro, columns=list(titulos), show="headings", selectmode="browse"
        )
        for coluna, texto in titulos.items():
            self.tabela.heading(coluna, text=texto)
            self.tabela.column(coluna, width=95, minwidth=60)
        self.tabela.column("acoes", width=90, minwidth=90, anchor="center", stretch=False)

        self.tabela.tag_configure("vencido", foreground="#ff6b6b")
        self.tabela.tag_configure("breve", foreground="#ffb347")

        barra = ttk.Scrollbar(quadro, orient="vertical", command=self.tabela.yview)
        self.tabela.configure(yscrollcommand=barra.set)
        self.tabela.pack(side="left", fill="both", expand=True)
        barra.pack(side="right", fill="y")

        self.tabela.bind("<Button-1>", self._ao_clicar)
        self.tabela.bind("<Motion>", self._ao_mover)
        self.tabela.bind("<Double-1>", self._ao_duplo_clique)

    # ---------- Lista ----------
    def carregar_lista(self):
        for item in self.tabela.get_children():
            self.tabela.delete(item)
        for id_, nome, tipo, descricao, capacidade, serie, data_iso in equipamento.listar(
            self.busca.get().strip()
        ):
            vencimento_txt, situacao, tags = "", "", ()
            if data_iso:
                vencimento = vencimentos.calcular_vencimento(data_iso)
                vencimento_txt = vencimento.strftime("%d/%m/%Y")
                situacao = vencimentos.situacao(vencimento)
                if situacao == "Vencido":
                    tags = ("vencido",)
                elif situacao == "Vence em breve":
                    tags = ("breve",)
            self.tabela.insert(
                "", "end", iid=str(id_), tags=tags,
                values=(
                    nome, NOMES_TIPO.get(tipo, tipo), descricao or "",
                    capacidade or "", serie or "",
                    vencimentos.iso_para_br(data_iso), vencimento_txt,
                    situacao, ICONES_TEXTO,
                ),
            )

    # ---------- Cliques na tabela ----------
    def _celula_acao(self, evento):
        if self.tabela.identify_region(evento.x, evento.y) != "cell":
            return None
        coluna = self.tabela.identify_column(evento.x)
        if coluna != f"#{len(self.tabela['columns'])}":
            return None
        iid = self.tabela.identify_row(evento.y)
        if not iid:
            return None
        caixa = self.tabela.bbox(iid, coluna)
        if not caixa:
            return None
        x0, _, largura, _ = caixa
        lado = "editar" if evento.x < x0 + largura / 2 else "excluir"
        return iid, lado

    def _ao_clicar(self, evento):
        acao = self._celula_acao(evento)
        if acao is None:
            return
        iid, lado = acao
        if lado == "editar":
            self._abrir_edicao(int(iid))
        else:
            self._excluir(int(iid))

    def _ao_mover(self, evento):
        self.tabela.configure(cursor="hand2" if self._celula_acao(evento) else "")

    def _ao_duplo_clique(self, evento):
        if self._celula_acao(evento) is not None:
            return
        iid = self.tabela.identify_row(evento.y)
        if iid:
            self._abrir_edicao(int(iid))

    # ---------- Ações ----------
    def _abrir_edicao(self, id_equipamento):
        if self.janela_edicao is not None and self.janela_edicao.winfo_exists():
            return
        self.janela_edicao = JanelaEdicaoEquipamento(
            self, id_equipamento, self.carregar_lista
        )

    def _excluir(self, id_equipamento):
        valores = self.tabela.item(str(id_equipamento))["values"]
        pergunta = f"Excluir {str(valores[1]).lower()} de '{valores[0]}'?"
        if not messagebox.askyesno("Confirmar", pergunta):
            return
        try:
            equipamento.excluir(id_equipamento)
        except sqlite3.IntegrityError:
            messagebox.showerror(
                "Não foi possível excluir",
                "Este equipamento já aparece em pagamentos.",
            )
            return
        self.carregar_lista()

    def salvar(self):
        dados = self.formulario.ler()
        if dados is None:
            return
        rotulo = self.formulario.campo_cliente.get()
        equipamento.inserir(dados)
        self.formulario.limpar()
        self.formulario.campo_cliente.set(rotulo)
        self.carregar_lista()