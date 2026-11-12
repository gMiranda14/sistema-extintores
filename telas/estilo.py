from tkinter import ttk

# Para aumentar ou diminuir a letra das tabelas, mude só estes dois números:
TAMANHO_FONTE = 12
ALTURA_LINHA = 34  # em geral, cerca de 2,8 vezes o tamanho da fonte
TAMANHO_FONTE_LISTA = 14  # letra da lista que abre no campo Cliente


def aplicar_estilo_tabelas():
    """Estilo único de todas as tabelas do sistema (Treeview)."""
    estilo = ttk.Style()
    estilo.theme_use("default")
    estilo.configure(
        "Treeview", background="#2b2b2b", foreground="white",
        fieldbackground="#2b2b2b", rowheight=ALTURA_LINHA, borderwidth=0,
        font=("Arial", TAMANHO_FONTE),
    )
    estilo.configure(
        "Treeview.Heading", background="#3a3a3a", foreground="white",
        relief="flat", font=("Arial", TAMANHO_FONTE, "bold"),
    )
    estilo.map("Treeview", background=[("selected", "#1f6aa5")])