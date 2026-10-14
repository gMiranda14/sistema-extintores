import customtkinter as ctk
from banco.conexao import criar_tabelas

criar_tabelas()

app = ctk.CTk()
app.title("Sistema de Extintores")
app.geometry("900x600")

ctk.CTkLabel(app, text="Sistema de Extintores",
             font=("Arial", 24)).pack(pady=40)

app.mainloop()