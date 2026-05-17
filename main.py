import tkinter as tk
from tkinter import scrolledtext
import threading
from automacao import Automacao


MODOS = [
    ("AMBOS", "CT e DX"),
    ("CT", "CT"),
    ("DX", "DX"),
]


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Print Automação")
        self.root.geometry("360x400")
        self.root.resizable(False, False)
        self.root.configure(bg="#1e1e2e")

        self.modo_ativo = None
        self.automacao = None
        self.botoes = {}

        self._construir_interface()

    def _construir_interface(self):
        tk.Label(
            self.root,
            text="PRINT AUTOMAÇÃO",
            font=("Arial", 13, "bold"),
            bg="#1e1e2e",
            fg="#cdd6f4",
        ).pack(pady=(18, 4))

        self.label_status = tk.Label(
            self.root,
            text="● INATIVO",
            font=("Arial", 12, "bold"),
            bg="#1e1e2e",
            fg="#f38ba8",
        )
        self.label_status.pack(pady=(0, 10))

        for chave, rotulo in MODOS:
            botao = tk.Button(
                self.root,
                text=f"ATIVAR {rotulo}",
                font=("Arial", 12, "bold"),
                width=20,
                height=1,
                bg="#a6e3a1",
                fg="#1e1e2e",
                activebackground="#94d49a",
                disabledforeground="#6c7086",
                relief="flat",
                cursor="hand2",
                command=lambda m=chave: self.toggle(m),
            )
            botao.pack(pady=4)
            self.botoes[chave] = botao

        self.log_area = scrolledtext.ScrolledText(
            self.root,
            height=6,
            width=44,
            font=("Consolas", 8),
            bg="#181825",
            fg="#cdd6f4",
            insertbackground="white",
            state="disabled",
            relief="flat",
        )
        self.log_area.pack(padx=12, pady=(10, 12))

    def toggle(self, modo):
        if self.modo_ativo == modo:
            self._desativar()
        elif self.modo_ativo is None:
            self._ativar(modo)

    def _ativar(self, modo):
        self.modo_ativo = modo
        rotulo = dict(MODOS)[modo]
        self.label_status.config(text=f"● ATIVO ({rotulo})", fg="#a6e3a1")
        for chave, botao in self.botoes.items():
            rotulo_chave = dict(MODOS)[chave]
            if chave == modo:
                botao.config(
                    text=f"DESATIVAR {rotulo_chave}",
                    bg="#f38ba8",
                    activebackground="#e07a96",
                    state="normal",
                )
            else:
                botao.config(state="disabled")
        if not self.automacao:
            self.automacao = Automacao(log_callback=self._log)
        threading.Thread(
            target=self.automacao.iniciar, args=(modo,), daemon=True
        ).start()

    def _desativar(self):
        self.modo_ativo = None
        self.label_status.config(text="● INATIVO", fg="#f38ba8")
        for chave, botao in self.botoes.items():
            rotulo_chave = dict(MODOS)[chave]
            botao.config(
                text=f"ATIVAR {rotulo_chave}",
                bg="#a6e3a1",
                activebackground="#94d49a",
                state="normal",
            )
        if self.automacao:
            threading.Thread(target=self.automacao.parar, daemon=True).start()

    def _log(self, mensagem):
        self.root.after(0, self._inserir_log, mensagem)

    def _inserir_log(self, mensagem):
        self.log_area.config(state="normal")
        self.log_area.insert(tk.END, mensagem + "\n")
        self.log_area.see(tk.END)
        self.log_area.config(state="disabled")


if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
