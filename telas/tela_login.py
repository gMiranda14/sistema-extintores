from pathlib import Path
from tkinter import messagebox

import customtkinter as ctk
from regras import acesso, preferencias

ICONE = Path(__file__).resolve().parent.parent / "assets" / "logo.ico"
TENTATIVAS_MAXIMAS = 5
SEGUNDOS_DE_ESPERA = 30
COR_ERRO = ("#c0392b", "#ff6b6b")
COR_OK = ("#2e7d4f", "#6bcb77")
COR_LINK = ("#1f6aa5", "#6fb1ff")


def _aplicar_icone(janela):
    """Coloca o ícone da empresa. O CustomTkinter troca o das janelas secundárias
    cerca de 200 ms depois de abrir, por isso o ícone é aplicado de novo logo depois."""
    if not ICONE.exists():
        return

    def definir():
        try:
            if janela.winfo_exists():
                janela.iconbitmap(str(ICONE))
        except Exception:
            pass  # sem ícone a janela funciona do mesmo jeito

    definir()
    janela.after(250, definir)


class _JanelaBase(ctk.CTkToplevel):
    """Base das janelas de acesso: centraliza na tela, põe o ícone e monta os campos."""

    def __init__(self, master, titulo, largura, altura):
        super().__init__(master)
        self._campos_senha = []
        self.title(titulo)
        self.resizable(False, False)
        x = (self.winfo_screenwidth() - largura) // 2
        y = (self.winfo_screenheight() - altura) // 3
        self.geometry(f"{largura}x{altura}+{x}+{y}")
        _aplicar_icone(self)
        self.after(150, self._focar)

    def _focar(self):
        if self.winfo_exists():
            self.lift()
            self.focus_force()

    def _campo(self, rotulo, senha=False):
        ctk.CTkLabel(self, text=rotulo, anchor="w").pack(fill="x", padx=30, pady=(10, 0))
        campo = ctk.CTkEntry(self, show="•" if senha else "")
        campo.pack(fill="x", padx=30, pady=(2, 0))
        if senha:
            self._campos_senha.append(campo)
        return campo

    def _opcao_mostrar_senha(self):
        def alternar():
            simbolo = "" if opcao.get() else "•"
            for campo in self._campos_senha:
                campo.configure(show=simbolo)

        opcao = ctk.CTkCheckBox(self, text="Mostrar senha", command=alternar)
        opcao.pack(anchor="w", padx=30, pady=(10, 0))

    def _criar_mensagem(self):
        self.mensagem = ctk.CTkLabel(self, text="", text_color=COR_ERRO, wraplength=370)
        self.mensagem.pack(padx=30, pady=(10, 0))

    def _mensagem(self, texto, cor=COR_ERRO):
        self.mensagem.configure(text=texto, text_color=cor)

    @staticmethod
    def _ligar_enter(campos, acao):
        for campo in campos:
            campo.bind("<Return>", lambda evento: acao())


class JanelaLogin(_JanelaBase):
    """Primeira janela do programa. No primeiro acesso, pede para criar o usuário."""

    def __init__(self, master, ao_entrar, ao_cancelar):
        primeiro_acesso = not acesso.existe_usuario()
        super().__init__(
            master, "Primeiro acesso" if primeiro_acesso else "Entrar",
            440, 600 if primeiro_acesso else 540,
        )
        self.ao_entrar = ao_entrar
        self.ao_cancelar = ao_cancelar
        self.falhas = 0
        self.bloqueado = False
        self.protocol("WM_DELETE_WINDOW", self._cancelar)
        if primeiro_acesso:
            self._montar_primeiro_acesso()
        else:
            self._montar_login()

    # ---------- Entrar ----------
    def _montar_login(self):
        ctk.CTkLabel(self, text="Sistema de Extintores", font=("Arial", 22, "bold")).pack(
            pady=(30, 2)
        )
        ctk.CTkLabel(self, text="Entre para continuar", text_color="gray").pack()
        self.campo_usuario = self._campo("Usuário")
        self.campo_senha = self._campo("Senha", senha=True)
        self._opcao_mostrar_senha()
        self.lembrar = ctk.CTkCheckBox(self, text="Lembrar meu usuário")
        self.lembrar.pack(anchor="w", padx=30, pady=(8, 0))
        lembrado = preferencias.obter("ultimo_usuario")
        if lembrado:
            self.campo_usuario.insert(0, lembrado)
            self.lembrar.select()
        self._criar_mensagem()
        self.botao = ctk.CTkButton(self, text="Entrar", command=self._entrar)
        self.botao.pack(fill="x", padx=30, pady=(12, 6))
        ctk.CTkButton(
            self, text="Esqueci minha senha", fg_color="transparent",
            text_color=COR_LINK, hover=False, command=self._esqueci,
        ).pack()
        self._ligar_enter([self.campo_usuario, self.campo_senha], self._entrar)
        # com o usuário já preenchido, o cursor vai direto para a senha
        self.after(250, (self.campo_senha if lembrado else self.campo_usuario).focus_set)

    def _entrar(self):
        if self.bloqueado:
            return
        nome = self.campo_usuario.get().strip()
        senha = self.campo_senha.get()
        if not nome or not senha:
            self._mensagem("Informe o usuário e a senha.")
            return

        self._mensagem("")
        self.botao.configure(state="disabled", text="Verificando...")
        self.update_idletasks()
        usuario, erro = acesso.entrar(nome, senha)
        if erro is None:
            preferencias.definir("ultimo_usuario", usuario["nome"] if self.lembrar.get() else None)
            self._concluir(usuario)
            return

        self.falhas += 1
        self.campo_senha.delete(0, "end")
        if self.falhas >= TENTATIVAS_MAXIMAS:
            self.bloqueado = True
            self._contagem(SEGUNDOS_DE_ESPERA)
            return
        restantes = TENTATIVAS_MAXIMAS - self.falhas
        self.botao.configure(state="normal", text="Entrar")
        plural = "s" if restantes != 1 else ""
        self._mensagem(f"{erro} Restam {restantes} tentativa{plural}.")

    def _contagem(self, segundos):
        if not self.winfo_exists():
            return
        if segundos <= 0:
            self.bloqueado = False
            self.falhas = 0
            self.botao.configure(state="normal", text="Entrar")
            self._mensagem("")
            return
        self.botao.configure(state="disabled", text=f"Aguarde {segundos} s")
        self._mensagem("Muitas tentativas incorretas. Aguarde para tentar de novo.")
        self.after(1000, lambda: self._contagem(segundos - 1))

    def _esqueci(self):
        JanelaRecuperacao(self, ao_concluir=self._senha_recuperada)

    def _senha_recuperada(self):
        self.falhas = 0
        self._mensagem("Senha alterada. Entre com a nova senha.", COR_OK)
        self.campo_senha.focus_set()

    # ---------- Primeiro acesso ----------
    def _montar_primeiro_acesso(self):
        ctk.CTkLabel(self, text="Primeiro acesso", font=("Arial", 22, "bold")).pack(pady=(26, 2))
        ctk.CTkLabel(
            self, text="Crie o usuário e a senha que serão usados\npara entrar no sistema.",
            text_color="gray",
        ).pack()
        self.campo_usuario = self._campo("Usuário")
        self.campo_senha = self._campo("Senha (mínimo de 8 caracteres, não só números)", senha=True)
        self.campo_confirmacao = self._campo("Confirme a senha", senha=True)
        self._opcao_mostrar_senha()
        self._criar_mensagem()
        self.botao = ctk.CTkButton(self, text="Criar acesso", command=self._criar)
        self.botao.pack(fill="x", padx=30, pady=(12, 0))
        self._ligar_enter(
            [self.campo_usuario, self.campo_senha, self.campo_confirmacao], self._criar
        )
        self.after(250, self.campo_usuario.focus_set)

    def _criar(self):
        self._mensagem("")
        self.botao.configure(state="disabled", text="Criando...")
        self.update_idletasks()
        usuario, codigo, erro = acesso.cadastrar_primeiro_usuario(
            self.campo_usuario.get(), self.campo_senha.get(), self.campo_confirmacao.get()
        )
        self.botao.configure(state="normal", text="Criar acesso")
        if erro:
            self._mensagem(erro)
            return
        JanelaCodigo(self, codigo, ao_confirmar=lambda: self._concluir(usuario))

    # ---------- Saída ----------
    def _concluir(self, usuario):
        self.destroy()
        self.ao_entrar(usuario)

    def _cancelar(self):
        self.destroy()
        self.ao_cancelar()


class JanelaCodigo(_JanelaBase):
    """Mostra o código de recuperação uma única vez."""

    def __init__(self, master, codigo, ao_confirmar):
        super().__init__(master, "Código de recuperação", 480, 440)
        self.transient(master)
        self.codigo = codigo
        self.ao_confirmar = ao_confirmar
        self.protocol("WM_DELETE_WINDOW", lambda: None)  # só fecha pelo botão Continuar

        ctk.CTkLabel(self, text="Guarde este código", font=("Arial", 20, "bold")).pack(pady=(24, 6))
        ctk.CTkLabel(
            self, wraplength=420, justify="left",
            text=(
                "Ele é a única forma de recuperar o acesso se você esquecer a senha. "
                "Anote em papel e guarde em um lugar seguro. Ele aparece só agora e "
                "vale uma vez: ao usá-lo, o sistema gera um novo."
            ),
        ).pack(padx=30)
        ctk.CTkLabel(self, text=codigo, font=("Consolas", 26, "bold")).pack(pady=(18, 4))
        self.aviso_copia = ctk.CTkLabel(self, text="", text_color=COR_OK)
        self.aviso_copia.pack()
        ctk.CTkButton(
            self, text="Copiar código", width=160, fg_color="gray", command=self._copiar
        ).pack(pady=(4, 12))
        self.confirmacao = ctk.CTkCheckBox(
            self, text="Anotei o código em um lugar seguro", command=self._alternar
        )
        self.confirmacao.pack(pady=(4, 12))
        self.botao = ctk.CTkButton(self, text="Continuar", state="disabled", command=self._continuar)
        self.botao.pack(fill="x", padx=30)

    def _copiar(self):
        self.clipboard_clear()
        self.clipboard_append(self.codigo)
        self.aviso_copia.configure(text="Copiado. Prefira anotar em papel.")

    def _alternar(self):
        self.botao.configure(state="normal" if self.confirmacao.get() else "disabled")

    def _continuar(self):
        self.destroy()
        self.ao_confirmar()


class JanelaRecuperacao(_JanelaBase):
    """Define uma senha nova usando o código de recuperação."""

    def __init__(self, master, ao_concluir):
        super().__init__(master, "Recuperar acesso", 440, 620)
        self.transient(master)
        self.ao_concluir = ao_concluir

        ctk.CTkLabel(self, text="Recuperar acesso", font=("Arial", 22, "bold")).pack(pady=(26, 2))
        ctk.CTkLabel(
            self, text="Informe o usuário e o código de recuperação\nguardado no primeiro acesso.",
            text_color="gray",
        ).pack()
        self.campo_usuario = self._campo("Usuário")
        self.campo_codigo = self._campo("Código de recuperação (XXXX-XXXX-XXXX-XXXX)")
        self.campo_senha = self._campo("Nova senha", senha=True)
        self.campo_confirmacao = self._campo("Confirme a nova senha", senha=True)
        self._opcao_mostrar_senha()
        self._criar_mensagem()
        self.botao = ctk.CTkButton(self, text="Redefinir senha", command=self._redefinir)
        self.botao.pack(fill="x", padx=30, pady=(12, 0))
        self._ligar_enter(
            [self.campo_usuario, self.campo_codigo, self.campo_senha, self.campo_confirmacao],
            self._redefinir,
        )

    def _redefinir(self):
        self._mensagem("")
        self.botao.configure(state="disabled", text="Verificando...")
        self.update_idletasks()
        novo_codigo, erro = acesso.redefinir_senha(
            self.campo_usuario.get(), self.campo_codigo.get(),
            self.campo_senha.get(), self.campo_confirmacao.get(),
        )
        self.botao.configure(state="normal", text="Redefinir senha")
        if erro:
            self._mensagem(erro)
            return
        JanelaCodigo(self, novo_codigo, ao_confirmar=self._finalizar)

    def _finalizar(self):
        self.destroy()
        self.ao_concluir()


class JanelaAlterarSenha(_JanelaBase):
    """Troca a senha de quem já entrou no sistema."""

    def __init__(self, master, nome_usuario):
        super().__init__(master, "Alterar senha", 440, 520)
        self.transient(master)
        self.nome_usuario = nome_usuario

        ctk.CTkLabel(self, text="Alterar senha", font=("Arial", 22, "bold")).pack(pady=(26, 2))
        self.campo_atual = self._campo("Senha atual", senha=True)
        self.campo_senha = self._campo("Nova senha (mínimo de 8 caracteres, não só números)", senha=True)
        self.campo_confirmacao = self._campo("Confirme a nova senha", senha=True)
        self._opcao_mostrar_senha()
        self._criar_mensagem()
        self.botao = ctk.CTkButton(self, text="Salvar nova senha", command=self._salvar)
        self.botao.pack(fill="x", padx=30, pady=(12, 6))
        ctk.CTkButton(
            self, text="Cancelar", fg_color="gray", command=self.destroy
        ).pack(fill="x", padx=30)
        self._ligar_enter(
            [self.campo_atual, self.campo_senha, self.campo_confirmacao], self._salvar
        )
        self.after(200, self._prender_foco)

    def _prender_foco(self):
        if self.winfo_exists():
            self.grab_set()
            self.campo_atual.focus_set()

    def _salvar(self):
        self._mensagem("")
        self.botao.configure(state="disabled", text="Verificando...")
        self.update_idletasks()
        erro = acesso.alterar_senha(
            self.nome_usuario, self.campo_atual.get(),
            self.campo_senha.get(), self.campo_confirmacao.get(),
        )
        self.botao.configure(state="normal", text="Salvar nova senha")
        if erro:
            self._mensagem(erro)
            return
        messagebox.showinfo("Senha alterada", "A senha foi alterada com sucesso.", parent=self)
        self.destroy()