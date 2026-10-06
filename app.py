"""Ventana del programa Salud de la batería.

Es lo que abre el acceso directo del instalador. Hace el mismo análisis que
`salud_bateria.py`, pero lo muestra en una ventana normal de escritorio.
"""

from __future__ import annotations

import os
import sys
import threading
import tkinter as tk
import webbrowser
from tkinter import filedialog, messagebox, ttk

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from informe import COLORES, _filas, html_informe  # noqa: E402
from salud_bateria import analizar  # noqa: E402

VERSION = "1.0.0"
NOMBRES_NIVEL = {"excelente": "Excelente", "buena": "Buena", "desgastada": "Desgastada",
                 "mala": "Mala", "desconocida": "Sin datos"}


def recurso(nombre: str) -> str:
    """Ruta a un archivo incluido en el programa (también dentro del .exe)."""
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, nombre)


class App(tk.Tk):
    def __init__(self, demo: bool = False):
        super().__init__()
        self.demo = demo
        self.resultado = None
        self.title("Salud de la batería")
        self.geometry("920x680")
        self.minsize(760, 560)
        try:
            self.iconbitmap(recurso("icono.ico"))
        except tk.TclError:
            pass

        estilo = ttk.Style(self)
        if "vista" in estilo.theme_names():
            estilo.theme_use("vista")
        estilo.configure("Treeview", rowheight=26)
        estilo.configure("Titulo.TLabel", font=("Segoe UI", 16, "bold"))
        estilo.configure("Diag.TLabel", font=("Segoe UI", 11))

        self._cabecera()
        self._barra()  # antes que las pestañas, para que siempre quede visible abajo
        self._pestanas()
        self.after(100, self.actualizar)

    # ------------------------------------------------------------ interfaz

    def _cabecera(self):
        top = ttk.Frame(self, padding=(16, 16, 16, 8))
        top.pack(fill="x")
        self.lienzo = tk.Canvas(top, width=140, height=140, highlightthickness=0,
                                bg=self.cget("bg"))
        self.lienzo.pack(side="left")
        texto = ttk.Frame(top, padding=(16, 8, 0, 0))
        texto.pack(side="left", fill="both", expand=True)
        self.lbl_titulo = ttk.Label(texto, text="Analizando la batería…", style="Titulo.TLabel")
        self.lbl_titulo.pack(anchor="w")
        self.lbl_diag = ttk.Label(texto, text="", style="Diag.TLabel", wraplength=640, justify="left")
        self.lbl_diag.pack(anchor="w", pady=(6, 0))
        self.lbl_resumen = ttk.Label(texto, text="", foreground="#666", wraplength=640, justify="left")
        self.lbl_resumen.pack(anchor="w", pady=(8, 0))
        self._dibujar_indicador(None, "desconocida")

    def _pestanas(self):
        self.nb = ttk.Notebook(self)
        self.nb.pack(fill="both", expand=True, padx=16)

        # Batería
        f = ttk.Frame(self.nb, padding=8)
        self.tabla_bat = ttk.Treeview(f, columns=("dato", "valor"), show="headings")
        self.tabla_bat.heading("dato", text="Dato")
        self.tabla_bat.heading("valor", text="Valor")
        self.tabla_bat.column("dato", width=280, anchor="w")
        self.tabla_bat.column("valor", width=400, anchor="w")
        self.tabla_bat.pack(fill="both", expand=True)
        self.nb.add(f, text="Batería")

        # Consumo
        f = ttk.Frame(self.nb, padding=8)
        cols = ("programa", "cpu", "memoria", "instancias")
        self.tabla_proc = ttk.Treeview(f, columns=cols, show="headings", height=10)
        for c, t, w, a in (("programa", "Programa", 260, "w"), ("cpu", "CPU", 90, "e"),
                           ("memoria", "Memoria", 110, "e"), ("instancias", "Procesos", 90, "e")):
            self.tabla_proc.heading(c, text=t)
            self.tabla_proc.column(c, width=w, anchor=a)
        self.tabla_proc.pack(fill="both", expand=True)
        self.tabla_proc.bind("<<TreeviewSelect>>", self._consejo_proceso)
        self.lbl_consejo_proc = ttk.Label(f, text="Selecciona un programa para ver cómo reducir su consumo.",
                                          wraplength=820, justify="left", foreground="#555")
        self.lbl_consejo_proc.pack(anchor="w", pady=(8, 0))
        self.lbl_ajustes = ttk.Label(f, text="", wraplength=820, justify="left")
        self.lbl_ajustes.pack(anchor="w", pady=(8, 0))
        self.nb.add(f, text="Qué consume más")

        # Consejos
        f = ttk.Frame(self.nb, padding=8)
        self.txt_consejos = tk.Text(f, wrap="word", relief="flat", font=("Segoe UI", 11),
                                    padx=8, pady=8, cursor="arrow")
        sb = ttk.Scrollbar(f, command=self.txt_consejos.yview)
        self.txt_consejos.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.txt_consejos.pack(fill="both", expand=True)
        self.nb.add(f, text="Consejos")

    def _barra(self):
        b = ttk.Frame(self, padding=16)
        b.pack(side="bottom", fill="x")
        self.btn_actualizar = ttk.Button(b, text="Actualizar", command=self.actualizar)
        self.btn_actualizar.pack(side="left")
        ttk.Button(b, text="Guardar informe…", command=self.guardar).pack(side="left", padx=8)
        ttk.Button(b, text="Acerca de", command=self.acerca).pack(side="right")
        self.lbl_estado = ttk.Label(b, text="", foreground="#666")
        self.lbl_estado.pack(side="left", padx=12)

    def _dibujar_indicador(self, salud, nivel):
        c = self.lienzo
        c.delete("all")
        color = COLORES[nivel]
        c.create_oval(10, 10, 130, 130, outline="#e4e6ea", width=14)
        if salud:
            c.create_arc(10, 10, 130, 130, start=90, extent=-3.6 * min(salud, 100),
                         style="arc", outline=color, width=14)
        c.create_text(70, 62, text=f"{salud:.0f} %" if salud is not None else "?",
                      font=("Segoe UI", 22, "bold"), fill=color)
        c.create_text(70, 90, text="salud", font=("Segoe UI", 10), fill="#666")

    # ------------------------------------------------------------- acciones

    def actualizar(self):
        self.btn_actualizar.state(["disabled"])
        self.lbl_estado.config(text="Midiendo el consumo durante 3 segundos…")
        threading.Thread(target=self._analizar, daemon=True).start()

    def _analizar(self):
        try:
            r = analizar(3, self.demo)
            self.after(0, self._mostrar, r)
        except Exception as e:  # noqa: BLE001 - se muestra al usuario
            self.after(0, self._error, e)

    def _error(self, e):
        self.btn_actualizar.state(["!disabled"])
        self.lbl_estado.config(text="")
        messagebox.showerror("Salud de la batería", f"No se pudo analizar la batería:\n{e}")

    def _mostrar(self, r):
        self.resultado = r
        self.btn_actualizar.state(["!disabled"])
        self.lbl_estado.config(text=f"Actualizado: {r['fecha']}")

        if r["baterias"]:
            b = r["baterias"][0]
            nivel, diag = r["diagnosticos"][0]
            self._dibujar_indicador(b.salud, nivel)
            self.lbl_titulo.config(text=f"Salud de la batería: {NOMBRES_NIVEL[nivel]}")
            self.lbl_diag.config(text=diag)
            partes = []
            if b.ciclos:
                partes.append(f"{b.ciclos} ciclos")
            if b.porcentaje is not None:
                partes.append(f"carga al {b.porcentaje:.0f} %")
            if b.estado:
                partes.append(b.estado)
            if b.minutos_restantes:
                partes.append(f"quedan {b.minutos_restantes // 60} h {b.minutos_restantes % 60} min")
            self.lbl_resumen.config(text=" · ".join(partes))
        else:
            self._dibujar_indicador(None, "desconocida")
            self.lbl_titulo.config(text="No se ha encontrado ninguna batería")
            self.lbl_diag.config(text="¿Es un ordenador de sobremesa? El resto del análisis sigue disponible.")
            self.lbl_resumen.config(text="")

        self.tabla_bat.delete(*self.tabla_bat.get_children())
        for i, b in enumerate(r["baterias"]):
            if len(r["baterias"]) > 1:
                self.tabla_bat.insert("", "end", values=(f"— {b.nombre} —", ""))
            for k, v in _filas(b):
                if v != "—":
                    self.tabla_bat.insert("", "end", values=(k, v))

        self.tabla_proc.delete(*self.tabla_proc.get_children())
        self._procesos = {}
        for p in r["procesos"]:
            iid = self.tabla_proc.insert("", "end", values=(
                p.nombre, f"{p.cpu:.1f} %", f"{p.memoria_mb:.0f} MB", p.instancias))
            self._procesos[iid] = p
        ajustes = "   ·   ".join(f"{k}: {v}" for k, v in r["ajustes"].items())
        self.lbl_ajustes.config(text=f"Ajustes de energía:  {ajustes}" if ajustes else "")

        t = self.txt_consejos
        t.config(state="normal")
        t.delete("1.0", "end")
        for i, c in enumerate(r["consejos"], 1):
            t.insert("end", f"{i}.  {c}\n\n")
        t.config(state="disabled")

    def _consejo_proceso(self, _evento):
        sel = self.tabla_proc.selection()
        if not sel:
            return
        p = self._procesos.get(sel[0])
        texto = p.consejo if p and p.consejo else (
            f"{p.nombre}: si no lo estás usando, ciérralo para ahorrar batería." if p else "")
        self.lbl_consejo_proc.config(text=texto)

    def guardar(self):
        if not self.resultado:
            return
        ruta = filedialog.asksaveasfilename(
            title="Guardar informe", defaultextension=".html", initialfile="salud_bateria.html",
            filetypes=[("Informe HTML", "*.html")])
        if not ruta:
            return
        with open(ruta, "w", encoding="utf-8") as f:
            f.write(html_informe(self.resultado))
        webbrowser.open("file:///" + os.path.abspath(ruta).replace("\\", "/"))

    def acerca(self):
        messagebox.showinfo("Acerca de", f"Salud de la batería {VERSION}\n\n"
                            "Mide el desgaste real de la batería con los datos que su firmware "
                            "da al sistema operativo, por eso funciona con cualquier marca de portátil.")


def main():
    App(demo="--demo" in sys.argv).mainloop()


if __name__ == "__main__":
    main()
