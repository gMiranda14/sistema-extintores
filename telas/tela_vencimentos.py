import unicodedata
from datetime import date
from tkinter import ttk
import customtkinter as ctk
from modelos import equipamento
from regras import vencimentos

NOMES_TIPO = {"extintor": "Extintor", "mangueira": "Mangueira"}
FILTROS = ["Todos", "Vencidos", "Vencem em breve"]
COR_VENCIDO = "#ff6b6b"
COR_BREVE = "#ffb347"
COR_EM_DIA = "#6bcb77"


def _normalizar(texto):
    decomposto = unicodedata.normalize("NFD", texto)
    sem_acento = "".join(c for c in decomposto if unicodedata.category(c) != "Mn")
    return sem_acento.lower()


class TelaVencimentos(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        self.itens = []
        self._montar_cabecalho()
        self._montar_filtros()
        self._montar_tabela()
        self.atualizar()

    # ---------- Montagem da tela ----------
    def _montar_cabecalho(self):
        topo = ctk.CTkFrame(self, fg_color="transparent")
        topo.pack(fill="x", padx=15, pady=(15, 5))
        ctk.CTkLabel(topo, text="Vencimentos", font=("Arial", 20, "bold")).pack(side="left")
        self.data_hoje = ctk.CTkLabel(topo, text="", text_color="gray")
        self.data_hoje.pack(side="right")

        quadro = ctk.CTkFrame(self, fg_color="transparent")
        quadro.pack(fill="x", padx=10)
        quadro.columnconfigure((0, 1, 2), weight=1)

        self.contadores = {}
        cartoes = [
            ("vencidos", "Vencidos", COR_VENCIDO),
            ("breve", f"Vencem em até {vencimentos.DIAS_ALERTA} dias", COR_BREVE),
            ("em_dia", "Em dia", COR_EM_DIA),
        ]
        for coluna, (chave, texto, cor) in enumerate(cartoes):
            cartao = ctk.CTkFrame(quadro)
            cartao.grid(row=0, column=coluna, sticky="ew", padx=5)
            numero = ctk.CTkLabel(
                cartao, text="0", font=("Arial", 32, "bold"), text_color=cor
            )
            numero.pack(pady=(10, 0))
            ctk.CTkLabel(cartao, text=texto).pack(pady=(0, 10))
            self.contadores[chave] = numero

    def _montar_filtros(self):
        barra = ctk.CTkFrame(self, fg_color="transparent")
        barra.pack(fill="x", padx=15, pady=(15, 5))
        barra.columnconfigure(1, weight=1)

        self.filtro = ctk.CTkSegmentedButton(
            barra, values=FILTROS, command=lambda valor: self.carregar_lista()
        )
        self.filtro.set("Todos")
        self.filtro.grid(row=0, column=0, padx=(0, 10))

        self.busca = ctk.CTkEntry(
            barra, placeholder_text="Buscar por cliente ou nº de série..."
        )
        self.busca.grid(row=0, column=1, sticky="ew")
        self.busca.bind("<KeyRelease>", lambda evento: self.carregar_lista())

    def _montar_tabela(self):
        self.aviso = ctk.CTkLabel(self, text="", text_color="gray")
        self.aviso.pack(side="bottom", pady=(0, 10))

        quadro = ctk.CTkFrame(self)
        quadro.pack(fill="both", expand=True, padx=15, pady=(0, 10))

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

        colunas = {
            "cliente": ("Cliente", 160),
            "telefone": ("Telefone", 110),
            "equipamento": ("Equipamento", 230),
            "serie": ("Nº de série", 90),
            "vencimento": ("Vencimento", 90),
            "prazo": ("Prazo", 130),
            "situacao": ("Situação", 110),
        }
        self.tabela = ttk.Treeview(
            quadro, columns=list(colunas), show="headings", selectmode="browse"
        )
        for chave, (texto, largura) in colunas.items():
            self.tabela.heading(chave, text=texto)
            self.tabela.column(chave, width=largura, minwidth=60)

        self.tabela.tag_configure("vencido", foreground=COR_VENCIDO)
        self.tabela.tag_configure("breve", foreground=COR_BREVE)

        barra = ttk.Scrollbar(quadro, orient="vertical", command=self.tabela.yview)
        self.tabela.configure(yscrollcommand=barra.set)
        self.tabela.pack(side="left", fill="both", expand=True)
        barra.pack(side="right", fill="y")

    # ---------- Dados ----------
    def atualizar(self):
        """Lê o banco de novo. O menu chama isto sempre que a tela é aberta."""
        hoje = date.today()
        self.data_hoje.configure(text=f"Hoje: {hoje.strftime('%d/%m/%Y')}")

        contagem = {"vencidos": 0, "breve": 0, "em_dia": 0}
        self.itens = []

        for (id_, cliente, telefone, tipo, descricao, capacidade,
             serie, data_iso) in equipamento.listar_com_contato():
            vencimento = vencimentos.calcular_vencimento(data_iso)
            situacao = vencimentos.situacao(vencimento, hoje)

            if situacao == "Em dia":
                contagem["em_dia"] += 1
                continue
            contagem["vencidos" if situacao == "Vencido" else "breve"] += 1

            partes = [p for p in (descricao, capacidade) if p]
            nome_tipo = NOMES_TIPO.get(tipo, tipo)
            texto_equipamento = nome_tipo
            if partes:
                texto_equipamento += " - " + " ".join(partes)

            dias = vencimentos.dias_restantes(vencimento, hoje)
            self.itens.append({
                "id": id_,
                "vencimento": vencimento,
                "situacao": situacao,
                "busca": _normalizar(f"{cliente} {serie or ''}"),
                "valores": (
                    cliente, telefone or "", texto_equipamento, serie or "",
                    vencimento.strftime("%d/%m/%Y"),
                    vencimentos.texto_prazo(dias), situacao,
                ),
            })

        self.itens.sort(key=lambda item: item["vencimento"])
        for chave, rotulo in self.contadores.items():
            rotulo.configure(text=str(contagem[chave]))
        self.carregar_lista()

    def carregar_lista(self):
        filtro = self.filtro.get()
        busca = _normalizar(self.busca.get().strip())

        for linha in self.tabela.get_children():
            self.tabela.delete(linha)

        mostrados = 0
        for item in self.itens:
            if filtro == "Vencidos" and item["situacao"] != "Vencido":
                continue
            if filtro == "Vencem em breve" and item["situacao"] != "Vence em breve":
                continue
            if busca and busca not in item["busca"]:
                continue
            etiqueta = "vencido" if item["situacao"] == "Vencido" else "breve"
            self.tabela.insert(
                "", "end", iid=str(item["id"]), tags=(etiqueta,), values=item["valores"]
            )
            mostrados += 1

        if mostrados:
            self.aviso.configure(text="")
        elif self.itens:
            self.aviso.configure(text="Nenhum equipamento encontrado com esse filtro.")
        else:
            self.aviso.configure(text="Nenhum equipamento vencido ou perto de vencer.")