import tkinter as tk
from tkinter import scrolledtext
import threading
from automacao import Automacao


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Print Automação")
        self.root.geometry("360x270")
        self.root.resizable(False, False)
        self.root.configure(bg="#1e1e2e")

        self.ativo = False
        self.automacao = None

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

        self.botao = tk.Button(
            self.root,
            text="ATIVAR",
            font=("Arial", 15, "bold"),
            width=16,
            height=2,
            bg="#a6e3a1",
            fg="#1e1e2e",
            activebackground="#94d49a",
            relief="flat",
            cursor="hand2",
            command=self.toggle,
        )
        self.botao.pack(pady=(0, 10))

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
        self.log_area.pack(padx=12, pady=(0, 12))

    def toggle(self):
        if self.ativo:
            self._desativar()
        else:
            self._ativar()

    def _ativar(self):
        self.ativo = True
        self.label_status.config(text="● ATIVO", fg="#a6e3a1")
        self.botao.config(text="DESATIVAR", bg="#f38ba8", activebackground="#e07a96")
        if not self.automacao:
            self.automacao = Automacao(log_callback=self._log)
        threading.Thread(target=self.automacao.iniciar, daemon=True).start()

    def _desativar(self):
        self.ativo = False
        self.label_status.config(text="● INATIVO", fg="#f38ba8")
        self.botao.config(text="ATIVAR", bg="#a6e3a1", activebackground="#94d49a")
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
