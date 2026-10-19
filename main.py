import customtkinter as ctk
from banco.conexao import criar_tabelas
from telas.tela_clientes import TelaClientes

criar_tabelas()
ctk.set_appearance_mode("dark")

app = ctk.CTk()
app.title("Sistema de Extintores")
app.geometry("1000x650")

tela = TelaClientes(app)
tela.pack(fill="both", expand=True, padx=10, pady=10)

app.mainloop
