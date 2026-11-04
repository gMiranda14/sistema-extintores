from tkinter import filedialog, messagebox
import customtkinter as ctk
from regras import backup


class TelaBackup(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        ctk.CTkLabel(self, text="Backup", font=("Arial", 20, "bold")).pack(
            anchor="w", padx=15, pady=(15, 0)
        )
        ctk.CTkLabel(
            self, justify="left", anchor="w", wraplength=760,
            text=(
                "O backup é uma cópia de segurança de todos os dados do sistema. "
                "Escolha uma pasta que esteja no Dropbox (ou num pen drive) para a cópia "
                "ficar fora deste computador. Cada backup tem a data e a hora no nome, "
                f"e os {backup.MANTER} mais recentes são guardados."
            ),
        ).pack(anchor="w", padx=15, pady=(8, 15))

        ctk.CTkLabel(self, text="Pasta de backup", font=("Arial", 14, "bold")).pack(
            anchor="w", padx=15
        )
        linha = ctk.CTkFrame(self, fg_color="transparent")
        linha.pack(fill="x", padx=15, pady=(5, 15))
        self.pasta = ctk.CTkLabel(linha, text="", anchor="w")
        self.pasta.pack(side="left", fill="x", expand=True)
        ctk.CTkButton(
            linha, text="Escolher pasta...", width=140, command=self._escolher_pasta
        ).pack(side="right")

        self.automatico = ctk.CTkSwitch(
            self, text="Fazer backup automático ao fechar o programa (no máximo um por dia)",
            command=self._alternar_automatico,
        )
        self.automatico.pack(anchor="w", padx=15, pady=(0, 15))

        ctk.CTkButton(self, text="Fazer backup agora", command=self._fazer_agora).pack(
            anchor="w", padx=15
        )
        self.status = ctk.CTkLabel(self, text="", anchor="w", justify="left")
        self.status.pack(anchor="w", padx=15, pady=(15, 0))

        ctk.CTkLabel(self, text="Como restaurar", font=("Arial", 14, "bold")).pack(
            anchor="w", padx=15, pady=(30, 0)
        )
        ctk.CTkLabel(
            self, justify="left", anchor="w", wraplength=760,
            text=(
                "1. Feche o programa.\n"
                "2. Copie o backup que você quer recuperar para a pasta \"banco\" do sistema.\n"
                "3. Renomeie o arquivo atual \"dados.db\" (por exemplo, para \"dados_antigo.db\") "
                "e renomeie a cópia para \"dados.db\".\n"
                "4. Abra o programa de novo."
            ),
        ).pack(anchor="w", padx=15, pady=(5, 0))

        self.atualizar()

    def atualizar(self):
        """Chamada pelo menu sempre que a tela é aberta."""
        pasta = backup.pasta_de_backup()
        self.pasta.configure(text=str(pasta) if pasta else "Nenhuma pasta escolhida ainda.")
        if backup.backup_automatico_ligado():
            self.automatico.select()
        else:
            self.automatico.deselect()

        ultimo = backup.ultimo_backup(pasta)
        if pasta is None:
            self.status.configure(text="Escolha uma pasta para começar a fazer backups.")
        elif ultimo is None:
            self.status.configure(text="Ainda não há nenhum backup nesta pasta.")
        else:
            self.status.configure(text=f"Último backup: {ultimo:%d/%m/%Y às %H:%M}")

    def _escolher_pasta(self):
        pasta = filedialog.askdirectory(title="Escolha a pasta de backup")
        if pasta:
            backup.definir_pasta(pasta)
            self.atualizar()

    def _alternar_automatico(self):
        ligado = bool(self.automatico.get())
        if ligado and backup.pasta_de_backup() is None:
            messagebox.showwarning("Atenção", "Escolha primeiro a pasta de backup.")
            self.automatico.deselect()
            return
        backup.definir_backup_automatico(ligado)

    def _fazer_agora(self):
        pasta = backup.pasta_de_backup()
        if pasta is None:
            messagebox.showwarning("Atenção", "Escolha primeiro a pasta de backup.")
            return
        try:
            arquivo = backup.fazer_backup(pasta)
        except Exception as erro:
            messagebox.showerror("Não foi possível fazer o backup", str(erro))
            return
        self.atualizar()
        messagebox.showinfo("Backup concluído", f"Backup salvo em:\n{arquivo}")