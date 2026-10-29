import unicodedata
from datetime import date
from tkinter import ttk, messagebox
import customtkinter as ctk
from modelos import cliente, equipamento, pagamento
from regras import financeiro, validadores, vencimentos
from telas.tela_equipamentos import SeletorCliente

FORMAS = ["Dinheiro", "PIX", "Boleto", "Cartão de débito", "Cartão de crédito"]
SERVICOS = {
    "Manutenção": "manutencao",
    "Venda de extintor": "venda_extintor",
    "Venda de mangueira": "venda_mangueira",
    "Teste de mangueira": "teste_mangueira",
    "Venda de placa": "venda_placa",
}
NOMES_SERVICO = {valor: nome for nome, valor in SERVICOS.items()}
COM_EQUIPAMENTO = {"manutencao", "venda_extintor", "venda_mangueira", "teste_mangueira"}
NOMES_TIPO = {"extintor": "Extintor", "mangueira": "Mangueira"}
FILTROS = ["Todos", "Pendentes", "Atrasados", "Pagos"]
COR_ATRASADO = "#ff6b6b"
COR_PENDENTE = "#ffb347"
COR_PAGO = "#6bcb77"


def _normalizar(texto):
    decomposto = unicodedata.normalize("NFD", texto)
    sem_acento = "".join(c for c in decomposto if unicodedata.category(c) != "Mn")
    return sem_acento.lower()


def _ligar_mascara_data(entrada):
    def mascarar(evento=None):
        texto = entrada.get()
        novo = validadores.mascarar_data(texto)
        if novo != texto:
            entrada.delete(0, "end")
            entrada.insert(0, novo)
            entrada.icursor("end")

    entrada.bind("<KeyRelease>", mascarar)


def _texto_equipamento(tipo, descricao, capacidade, serie):
    partes = [p for p in (descricao, capacidade) if p]
    texto = NOMES_TIPO.get(tipo, tipo)
    if partes:
        texto += " - " + " ".join(partes)
    if serie:
        texto += f" [{serie}]"
    return texto


class SeletorClienteAviso(SeletorCliente):
    """O mesmo campo de busca de cliente, mas avisa quando uma escolha é feita."""

    def __init__(self, master, ao_escolher):
        super().__init__(master)
        self.ao_escolher = ao_escolher

    def _escolher(self, rotulo):
        super()._escolher(rotulo)
        self.ao_escolher()


class JanelaPagamento(ctk.CTkToplevel):
    """Janela para cadastrar ou editar um pagamento, com os itens cobrados."""

    def __init__(self, master, ao_concluir, id_pagamento=None):
        super().__init__(master)
        self.ao_concluir = ao_concluir
        self.id_pagamento = id_pagamento
        self.itens = []
        self.rotulo_para_id = {}
        self.id_para_rotulo = {}
        self.equipamentos = {}
        self.rotulo_do_equipamento = {}

        self.title("Editar pagamento" if id_pagamento else "Novo pagamento")
        self.geometry("920x700")
        self.transient(master.winfo_toplevel())

        self._montar_dados()
        self._montar_itens()
        self._montar_rodape()

        self._carregar_clientes()
        if id_pagamento:
            self._preencher()
        else:
            self.campo_data.insert(0, date.today().strftime("%d/%m/%Y"))
        self._servico_mudou()
        self.after(150, self._focar)

    def _focar(self):
        if self.winfo_exists():
            self.lift()
            self.focus()
            self.grab_set()

    # ---------- Montagem ----------
    def _rotulo(self, pai, texto, linha, coluna, largura=1):
        ctk.CTkLabel(pai, text=texto).grid(
            row=linha, column=coluna, columnspan=largura,
            sticky="w", padx=5, pady=(8, 0),
        )

    def _campo_data(self, pai, texto, coluna):
        self._rotulo(pai, texto, 2, coluna)
        campo = ctk.CTkEntry(pai, placeholder_text="dd/mm/aaaa")
        campo.grid(row=3, column=coluna, sticky="ew", padx=5)
        _ligar_mascara_data(campo)
        return campo

    def _montar_dados(self):
        quadro = ctk.CTkFrame(self, fg_color="transparent")
        quadro.pack(fill="x", padx=15, pady=(15, 0))
        quadro.columnconfigure((0, 1, 2, 3), weight=1, uniform="col")

        self._rotulo(quadro, "Cliente *", 0, 0, 2)
        self.campo_cliente = SeletorClienteAviso(quadro, self._recarregar_equipamentos)
        self.campo_cliente.grid(row=1, column=0, columnspan=2, sticky="ew", padx=5)

        self._rotulo(quadro, "Forma de pagamento *", 0, 2, 2)
        self.campo_forma = ctk.CTkComboBox(quadro, values=FORMAS, state="readonly")
        self.campo_forma.set("")
        self.campo_forma.grid(row=1, column=2, columnspan=2, sticky="ew", padx=5)

        self.campo_data = self._campo_data(quadro, "Data do serviço *", 0)
        self.campo_venc = self._campo_data(quadro, "Vencimento", 1)
        self.campo_pago = self._campo_data(quadro, "Pago em", 2)

        self._rotulo(quadro, "Nº da nota fiscal", 2, 3)
        self.campo_nf = ctk.CTkEntry(quadro)
        self.campo_nf.grid(row=3, column=3, sticky="ew", padx=5)

    def _montar_itens(self):
        ctk.CTkLabel(
            self, text="Itens do pagamento", font=("Arial", 16, "bold")
        ).pack(anchor="w", padx=15, pady=(18, 0))

        linha = ctk.CTkFrame(self, fg_color="transparent")
        linha.pack(fill="x", padx=15)
        linha.columnconfigure(1, weight=3)
        linha.columnconfigure(2, weight=2)

        self._rotulo(linha, "Serviço", 0, 0)
        self.campo_servico = ctk.CTkComboBox(
            linha, values=list(SERVICOS), state="readonly",
            width=170, command=self._servico_mudou,
        )
        self.campo_servico.set("Manutenção")
        self.campo_servico.grid(row=1, column=0, padx=5)

        self._rotulo(linha, "Equipamento", 0, 1)
        self.campo_equip = ctk.CTkComboBox(linha, values=[], state="readonly")
        self.campo_equip.set("")
        self.campo_equip.grid(row=1, column=1, sticky="ew", padx=5)

        self._rotulo(linha, "Descrição (opcional)", 0, 2)
        self.campo_desc = ctk.CTkEntry(linha)
        self.campo_desc.grid(row=1, column=2, sticky="ew", padx=5)

        self._rotulo(linha, "Qtd", 0, 3)
        self.campo_qtd = ctk.CTkEntry(linha, width=55)
        self.campo_qtd.grid(row=1, column=3, padx=5)

        self._rotulo(linha, "Valor unitário", 0, 4)
        self.campo_valor = ctk.CTkEntry(linha, width=110, placeholder_text="0,00")
        self.campo_valor.grid(row=1, column=4, padx=5)

        ctk.CTkButton(
            linha, text="Adicionar", width=90, command=self._adicionar_item
        ).grid(row=1, column=5, padx=5)

        quadro = ctk.CTkFrame(self)
        quadro.pack(fill="both", expand=True, padx=15, pady=(10, 0))
        colunas = {
            "servico": ("Serviço", 140, "w"),
            "detalhe": ("Equipamento / descrição", 330, "w"),
            "qtd": ("Qtd", 50, "e"),
            "unitario": ("Valor unit.", 100, "e"),
            "subtotal": ("Subtotal", 100, "e"),
        }
        self.tabela_itens = ttk.Treeview(
            quadro, columns=list(colunas), show="headings", height=6, selectmode="browse"
        )
        for chave, (texto, largura, ancora) in colunas.items():
            self.tabela_itens.heading(chave, text=texto)
            self.tabela_itens.column(chave, width=largura, minwidth=40, anchor=ancora)
        barra = ttk.Scrollbar(quadro, orient="vertical", command=self.tabela_itens.yview)
        self.tabela_itens.configure(yscrollcommand=barra.set)
        self.tabela_itens.pack(side="left", fill="both", expand=True)
        barra.pack(side="right", fill="y")

    def _montar_rodape(self):
        faixa = ctk.CTkFrame(self, fg_color="transparent")
        faixa.pack(fill="x", padx=15, pady=(10, 0))
        ctk.CTkButton(
            faixa, text="Remover item selecionado", fg_color="gray",
            command=self._remover_item,
        ).pack(side="left")
        self.total = ctk.CTkLabel(
            faixa, text="Total: R$ 0,00", font=("Arial", 18, "bold")
        )
        self.total.pack(side="right")

        botoes = ctk.CTkFrame(self, fg_color="transparent")
        botoes.pack(fill="x", padx=15, pady=15)
        ctk.CTkButton(botoes, text="Salvar", command=self._salvar).pack(
            side="left", padx=(0, 10)
        )
        ctk.CTkButton(
            botoes, text="Cancelar", fg_color="gray", command=self.destroy
        ).pack(side="left")

    # ---------- Clientes e equipamentos ----------
    def _carregar_clientes(self):
        clientes = cliente.listar_para_selecao()
        rotulos = [f"{nome} - {doc}" if doc else nome for _, nome, doc in clientes]
        itens = []
        for (id_, nome, doc), rotulo in zip(clientes, rotulos):
            if rotulos.count(rotulo) > 1:
                rotulo = f"{rotulo} (nº {id_})"
            self.rotulo_para_id[rotulo] = id_
            self.id_para_rotulo[id_] = rotulo
            itens.append((rotulo, nome, doc or ""))
        self.campo_cliente.carregar(itens)

    def _cliente_escolhido(self):
        return self.rotulo_para_id.get(self.campo_cliente.get())

    def _recarregar_equipamentos(self):
        self.equipamentos = {}
        self.rotulo_do_equipamento = {}
        cliente_id = self._cliente_escolhido()
        if cliente_id is not None:
            linhas = equipamento.listar_do_cliente(cliente_id)
            rotulos = [_texto_equipamento(l[1], l[2], l[3], l[4]) for l in linhas]
            for linha, rotulo in zip(linhas, rotulos):
                if rotulos.count(rotulo) > 1:
                    rotulo += f" (nº {linha[0]})"
                self.equipamentos[rotulo] = linha[0]
                self.rotulo_do_equipamento[linha[0]] = rotulo
        self.campo_equip.configure(values=list(self.equipamentos))
        self.campo_equip.set("")

    def _servico_mudou(self, _valor=None):
        tipo = SERVICOS.get(self.campo_servico.get())
        usa_equipamento = tipo in COM_EQUIPAMENTO
        self.campo_equip.configure(state="readonly" if usa_equipamento else "disabled")
        if not usa_equipamento:
            self.campo_equip.set("")
        self.campo_qtd.configure(state="normal")
        self.campo_qtd.delete(0, "end")
        self.campo_qtd.insert(0, "1")
        if usa_equipamento:
            # cada equipamento tem o seu preço: a quantidade é sempre 1
            self.campo_qtd.configure(state="disabled")

    # ---------- Itens ----------
    def _aviso(self, texto):
        messagebox.showwarning("Atenção", texto, parent=self)

    def _adicionar_item(self):
        tipo = SERVICOS.get(self.campo_servico.get())
        if tipo is None:
            self._aviso("Escolha o serviço.")
            return

        equipamento_id = None
        if tipo in COM_EQUIPAMENTO:
            if self._cliente_escolhido() is None:
                self._aviso("Escolha o cliente antes de adicionar itens.")
                return
            equipamento_id = self.equipamentos.get(self.campo_equip.get())
            if equipamento_id is None:
                if not self.equipamentos:
                    self._aviso(
                        "Este cliente não tem equipamento cadastrado. "
                        "Cadastre antes na tela Equipamentos."
                    )
                else:
                    self._aviso("Escolha o equipamento.")
                return
            if any(i["equipamento_id"] == equipamento_id and i["tipo_servico"] == tipo
                   for i in self.itens):
                self._aviso("Este equipamento já foi adicionado com esse serviço.")
                return

        descricao = self.campo_desc.get().strip()
        if tipo == "venda_placa" and not descricao:
            self._aviso("Descreva a placa vendida.")
            return

        try:
            quantidade = int(self.campo_qtd.get())
            if quantidade < 1:
                raise ValueError
        except ValueError:
            self._aviso("A quantidade deve ser um número inteiro maior que zero.")
            return

        valor = financeiro.converter_valor(self.campo_valor.get().strip())
        if valor is None:
            self._aviso("Informe o valor unitário, por exemplo 80,00.")
            return

        self.itens.append({
            "equipamento_id": equipamento_id,
            "tipo_servico": tipo,
            "descricao": descricao,
            "quantidade": quantidade,
            "valor_unitario": valor,
        })
        self.campo_desc.delete(0, "end")
        self.campo_valor.delete(0, "end")
        self.campo_equip.set("")
        self._atualizar_itens()

    def _remover_item(self):
        selecao = self.tabela_itens.selection()
        if not selecao:
            self._aviso("Selecione um item na lista.")
            return
        del self.itens[int(selecao[0])]
        self._atualizar_itens()

    def _atualizar_itens(self):
        for linha in self.tabela_itens.get_children():
            self.tabela_itens.delete(linha)
        total = 0.0
        for posicao, item in enumerate(self.itens):
            subtotal = round(item["quantidade"] * item["valor_unitario"], 2)
            total += subtotal
            detalhe = self.rotulo_do_equipamento.get(item["equipamento_id"], "")
            if item["descricao"]:
                detalhe = f"{detalhe} - {item['descricao']}" if detalhe else item["descricao"]
            self.tabela_itens.insert(
                "", "end", iid=str(posicao),
                values=(
                    NOMES_SERVICO.get(item["tipo_servico"], item["tipo_servico"]),
                    detalhe, item["quantidade"],
                    financeiro.formatar_moeda(item["valor_unitario"]),
                    financeiro.formatar_moeda(subtotal),
                ),
            )
        self.total.configure(text=f"Total: {financeiro.formatar_moeda(round(total, 2))}")

    # ---------- Edição ----------
    def _preencher(self):
        dados, itens = pagamento.buscar(self.id_pagamento)
        cliente_id, forma, data_servico, vencimento, pago, nf = dados
        self.campo_cliente.set(self.id_para_rotulo.get(cliente_id, ""))
        self._recarregar_equipamentos()
        self.campo_forma.set(forma or "")
        self.campo_data.insert(0, vencimentos.iso_para_br(data_servico))
        self.campo_venc.insert(0, vencimentos.iso_para_br(vencimento))
        self.campo_pago.insert(0, vencimentos.iso_para_br(pago))
        self.campo_nf.insert(0, nf or "")
        for equipamento_id, tipo, descricao, quantidade, valor in itens:
            self.itens.append({
                "equipamento_id": equipamento_id,
                "tipo_servico": tipo,
                "descricao": descricao or "",
                "quantidade": quantidade,
                "valor_unitario": valor,
            })
        self._atualizar_itens()

    # ---------- Salvar ----------
    def _ler_data(self, campo, rotulo, obrigatoria, permitir_futuro):
        texto = campo.get().strip()
        if not texto:
            if obrigatoria:
                self._aviso(f"Preencha o campo '{rotulo}'.")
                return False, None
            return True, None
        iso = vencimentos.br_para_iso(texto)
        if iso is None:
            self._aviso(f"O campo '{rotulo}' tem uma data inválida. Use o formato dd/mm/aaaa.")
            return False, None
        if not permitir_futuro and date.fromisoformat(iso) > date.today():
            self._aviso(f"O campo '{rotulo}' não pode ter uma data futura.")
            return False, None
        return True, iso

    def _salvar(self):
        cliente_id = self._cliente_escolhido()
        if cliente_id is None:
            self._aviso("Escolha o cliente na lista.")
            return
        forma = self.campo_forma.get()
        if forma not in FORMAS:
            self._aviso("Escolha a forma de pagamento.")
            return

        ok, data_servico = self._ler_data(self.campo_data, "Data do serviço", True, False)
        if not ok:
            return
        ok, vencimento = self._ler_data(self.campo_venc, "Vencimento", False, True)
        if not ok:
            return
        ok, pago = self._ler_data(self.campo_pago, "Pago em", False, False)
        if not ok:
            return

        if forma == "Boleto" and not pago and not vencimento:
            self._aviso("Para um boleto em aberto, informe o vencimento.")
            return
        if not self.itens:
            self._aviso("Adicione pelo menos um item ao pagamento.")
            return

        ids_do_cliente = {linha[0] for linha in equipamento.listar_do_cliente(cliente_id)}
        for item in self.itens:
            if item["equipamento_id"] and item["equipamento_id"] not in ids_do_cliente:
                self._aviso(
                    "Há itens de outro cliente. Remova-os ou escolha o cliente certo."
                )
                return

        dados = (cliente_id, forma, data_servico, vencimento, pago,
                 self.campo_nf.get().strip() or None)
        if self.id_pagamento:
            pagamento.atualizar(self.id_pagamento, dados, self.itens)
        else:
            pagamento.inserir(dados, self.itens)
        self.ao_concluir()
        self.destroy()


class TelaPagamentos(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        self.registros = []
        self.mapa = {}
        self.janela = None
        self._montar_cabecalho()
        self._montar_filtros()
        self._montar_acoes()
        self._montar_tabela()
        self.atualizar()

    # ---------- Montagem ----------
    def _montar_cabecalho(self):
        topo = ctk.CTkFrame(self, fg_color="transparent")
        topo.pack(fill="x", padx=15, pady=(15, 5))
        ctk.CTkLabel(topo, text="Pagamentos", font=("Arial", 20, "bold")).pack(side="left")
        ctk.CTkButton(topo, text="+ Novo pagamento", command=self._novo).pack(side="right")

        quadro = ctk.CTkFrame(self, fg_color="transparent")
        quadro.pack(fill="x", padx=10)
        quadro.columnconfigure((0, 1, 2), weight=1)

        self.cartoes = {}
        for coluna, (chave, cor) in enumerate([
            ("pendente", COR_PENDENTE), ("atrasado", COR_ATRASADO), ("recebido", COR_PAGO),
        ]):
            cartao = ctk.CTkFrame(quadro)
            cartao.grid(row=0, column=coluna, sticky="ew", padx=5)
            valor = ctk.CTkLabel(cartao, text="", font=("Arial", 24, "bold"), text_color=cor)
            valor.pack(pady=(10, 0))
            legenda = ctk.CTkLabel(cartao, text="")
            legenda.pack(pady=(0, 10))
            self.cartoes[chave] = (valor, legenda)

    def _montar_filtros(self):
        barra = ctk.CTkFrame(self, fg_color="transparent")
        barra.pack(fill="x", padx=15, pady=(15, 5))
        barra.columnconfigure(1, weight=1)

        self.filtro = ctk.CTkSegmentedButton(
            barra, values=FILTROS, command=lambda valor: self.carregar_lista()
        )
        self.filtro.set("Todos")
        self.filtro.grid(row=0, column=0, padx=(0, 10))

        self.busca = ctk.CTkEntry(barra, placeholder_text="Buscar por cliente ou nº da nota...")
        self.busca.grid(row=0, column=1, sticky="ew")
        self.busca.bind("<KeyRelease>", lambda evento: self.carregar_lista())

    def _montar_acoes(self):
        barra = ctk.CTkFrame(self, fg_color="transparent")
        barra.pack(side="bottom", fill="x", padx=15, pady=(0, 15))
        ctk.CTkButton(
            barra, text="Marcar como pago", fg_color="#2e7d4f", hover_color="#256640",
            command=self._marcar_pago,
        ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(barra, text="Editar", command=self._editar).pack(side="left", padx=(0, 8))
        ctk.CTkButton(
            barra, text="Excluir", fg_color="#b33a3a", hover_color="#8f2d2d",
            command=self._excluir,
        ).pack(side="left")

        self.aviso = ctk.CTkLabel(self, text="", text_color="gray")
        self.aviso.pack(side="bottom", pady=(0, 5))

    def _montar_tabela(self):
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
            "cliente": ("Cliente", 170, "w"),
            "servico": ("Data do serviço", 100, "center"),
            "forma": ("Forma", 120, "w"),
            "vencimento": ("Vencimento", 90, "center"),
            "pago": ("Pago em", 90, "center"),
            "total": ("Total", 100, "e"),
            "nf": ("Nº NF", 80, "w"),
            "situacao": ("Situação", 90, "center"),
        }
        self.tabela = ttk.Treeview(
            quadro, columns=list(colunas), show="headings", selectmode="browse"
        )
        for chave, (texto, largura, ancora) in colunas.items():
            self.tabela.heading(chave, text=texto)
            self.tabela.column(chave, width=largura, minwidth=60, anchor=ancora)

        self.tabela.tag_configure("atrasado", foreground=COR_ATRASADO)
        self.tabela.tag_configure("pendente", foreground=COR_PENDENTE)
        self.tabela.tag_configure("pago", foreground=COR_PAGO)

        barra = ttk.Scrollbar(quadro, orient="vertical", command=self.tabela.yview)
        self.tabela.configure(yscrollcommand=barra.set)
        self.tabela.pack(side="left", fill="both", expand=True)
        barra.pack(side="right", fill="y")
        self.tabela.bind("<Double-1>", lambda evento: self._editar())

    # ---------- Dados ----------
    def atualizar(self):
        """Lê o banco de novo. O menu chama isto sempre que a tela é aberta."""
        selecao = self.tabela.selection()
        hoje = date.today()
        mes_atual = hoje.isoformat()[:7]
        totais = {"Pendente": [0, 0.0], "Atrasado": [0, 0.0]}
        recebido_no_mes = 0.0
        self.registros = []

        for (id_, nome, forma, data_servico, vencimento, pago,
             nf, total) in pagamento.listar():
            total = round(total, 2)
            status = financeiro.status_pagamento(vencimento, pago, hoje)
            if status == "Pago":
                if pago and pago[:7] == mes_atual:
                    recebido_no_mes += total
            else:
                totais[status][0] += 1
                totais[status][1] += total

            self.registros.append({
                "id": id_,
                "cliente": nome,
                "status": status,
                "total": total,
                "ordem": (data_servico or "", id_),
                "busca": _normalizar(f"{nome} {nf or ''}"),
                "valores": (
                    nome, vencimentos.iso_para_br(data_servico), forma or "",
                    vencimentos.iso_para_br(vencimento), vencimentos.iso_para_br(pago),
                    financeiro.formatar_moeda(total), nf or "", status,
                ),
            })

        self.registros.sort(key=lambda r: r["ordem"], reverse=True)
        self.mapa = {r["id"]: r for r in self.registros}

        pend, atras = totais["Pendente"], totais["Atrasado"]
        self._cartao("pendente", pend[1], f"A receber - pendentes ({pend[0]})")
        self._cartao("atrasado", atras[1], f"Atrasados ({atras[0]})")
        self._cartao("recebido", recebido_no_mes, "Recebido neste mês")
        self.carregar_lista()
        for iid in selecao:
            if self.tabela.exists(iid):
                self.tabela.selection_set(iid)

    def _cartao(self, chave, valor, legenda):
        rotulo_valor, rotulo_legenda = self.cartoes[chave]
        rotulo_valor.configure(text=financeiro.formatar_moeda(valor))
        rotulo_legenda.configure(text=legenda)

    def carregar_lista(self):
        filtro = self.filtro.get()
        busca = _normalizar(self.busca.get().strip())
        status_do_filtro = {"Pendentes": "Pendente", "Atrasados": "Atrasado", "Pagos": "Pago"}

        for linha in self.tabela.get_children():
            self.tabela.delete(linha)

        mostrados = 0
        for registro in self.registros:
            if filtro != "Todos" and registro["status"] != status_do_filtro[filtro]:
                continue
            if busca and busca not in registro["busca"]:
                continue
            self.tabela.insert(
                "", "end", iid=str(registro["id"]),
                tags=(registro["status"].lower(),), values=registro["valores"],
            )
            mostrados += 1

        if mostrados:
            self.aviso.configure(text="")
        elif self.registros:
            self.aviso.configure(text="Nenhum pagamento encontrado com esse filtro.")
        else:
            self.aviso.configure(text="Nenhum pagamento cadastrado. Clique em \"+ Novo pagamento\".")

    # ---------- Ações ----------
    def _selecionado(self):
        selecao = self.tabela.selection()
        if not selecao:
            messagebox.showwarning("Atenção", "Selecione um pagamento na lista.")
            return None
        return int(selecao[0])

    def _abrir_janela(self, id_pagamento=None):
        if self.janela is not None and self.janela.winfo_exists():
            return
        self.janela = JanelaPagamento(self, self.atualizar, id_pagamento)

    def _novo(self):
        self._abrir_janela()

    def _editar(self):
        id_pagamento = self._selecionado()
        if id_pagamento is not None:
            self._abrir_janela(id_pagamento)

    def _marcar_pago(self):
        id_pagamento = self._selecionado()
        if id_pagamento is None:
            return
        registro = self.mapa[id_pagamento]
        if registro["status"] == "Pago":
            messagebox.showinfo("Pagamento", "Este pagamento já está marcado como pago.")
            return
        hoje = date.today()
        pergunta = (
            f"Marcar como pago o pagamento de '{registro['cliente']}' "
            f"({financeiro.formatar_moeda(registro['total'])}) com a data de hoje, "
            f"{hoje.strftime('%d/%m/%Y')}?"
        )
        if messagebox.askyesno("Confirmar", pergunta):
            pagamento.marcar_pago(id_pagamento, hoje.isoformat())
            self.atualizar()

    def _excluir(self):
        id_pagamento = self._selecionado()
        if id_pagamento is None:
            return
        registro = self.mapa[id_pagamento]
        pergunta = (
            f"Excluir o pagamento de '{registro['cliente']}' "
            f"({financeiro.formatar_moeda(registro['total'])})?"
        )
        if messagebox.askyesno("Confirmar", pergunta):
            pagamento.excluir(id_pagamento)
            self.atualizar()