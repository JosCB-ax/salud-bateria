"""Ventana del programa Salud de la batería.

Es lo que abre el acceso directo del instalador. Hace el mismo análisis que
`salud_bateria.py`, pero lo muestra en una ventana normal de escritorio.
"""

from __future__ import annotations

import os
import sys
import platform
import subprocess
import threading
import tkinter as tk
import webbrowser
from tkinter import filedialog, messagebox, ttk

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import configuracion  # noqa: E402
from configuracion import recurso  # noqa: E402
from autonomia import calcular, horas_texto, sin_datos_texto  # noqa: E402
from informe import COLORES, _filas, html_informe  # noqa: E402
from salud_bateria import analizar  # noqa: E402

VERSION = "1.2.0"
NOMBRES_NIVEL = {"excelente": "Excelente", "buena": "Buena", "desgastada": "Desgastada",
                 "mala": "Mala", "desconocida": "Sin datos"}


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
        if not demo and configuracion.cargar().get("avisos"):
            iniciar_bandeja()

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

        # Autonomía e historial
        f = ttk.Frame(self.nb, padding=12)
        ttk.Label(f, text="Autonomía real con la configuración de este equipo",
                  font=("Segoe UI", 12, "bold")).pack(anchor="w")
        self.lbl_autonomia = ttk.Label(f, text="", wraplength=840, justify="left", font=("Segoe UI", 11))
        self.lbl_autonomia.pack(anchor="w", pady=(6, 12))
        ttk.Label(f, text="Evolución de la salud", font=("Segoe UI", 12, "bold")).pack(anchor="w")
        self.grafica = tk.Canvas(f, height=220, bg="white", highlightthickness=1,
                                 highlightbackground="#e4e6ea")
        self.grafica.pack(fill="both", expand=True, pady=(6, 0))
        self.grafica.bind("<Configure>", lambda _e: self._dibujar_historial())
        self.nb.add(f, text="Autonomía e historial")

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
        if platform.system() == "Windows":
            fila = ttk.Frame(f)
            fila.pack(anchor="w", pady=(8, 0))
            self.btn_exacto = ttk.Button(fila, text="Medir consumo exacto (24 h)…", command=self.consumo_exacto)
            self.btn_exacto.pack(side="left")
            self.lbl_exacto = ttk.Label(fila, text="Usa el registro de energía de Windows; pide permiso de administrador.",
                                        foreground="#666", wraplength=600, justify="left")
            self.lbl_exacto.pack(side="left", padx=10)
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
        ttk.Button(b, text="Exportar PDF…", command=self.exportar_pdf).pack(side="left", padx=(8, 0))
        ttk.Button(b, text="Guardar informe…", command=self.guardar).pack(side="left", padx=8)
        ttk.Button(b, text="Ajustes", command=self.ajustes).pack(side="right", padx=(0, 8))
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

        self._mostrar_autonomia(r["baterias"][0] if r["baterias"] else None)
        self._dibujar_historial()

    def _mostrar_autonomia(self, b):
        if b is None:
            self.lbl_autonomia.config(text="No hay batería.")
            return
        escenarios = calcular(b)
        if not escenarios:
            self.lbl_autonomia.config(text=sin_datos_texto(b))
            return
        lineas = []
        for e in escenarios:
            lineas.append(f"{e.titulo} ({e.vatios:.1f} W, {e.detalle}):")
            linea = f"    Carga completa hoy: {horas_texto(e.horas_hoy)}"
            if e.horas_nueva:
                linea += f"   ·   cuando era nueva: {horas_texto(e.horas_nueva)}"
            if e.horas_carga_actual and not b.enchufado:
                linea += f"   ·   con la carga actual: {horas_texto(e.horas_carga_actual)}"
            lineas.append(linea)
        if escenarios[0].horas_nueva:
            perdido = escenarios[0].horas_nueva - escenarios[0].horas_hoy
            lineas.append(f"\nEl desgaste te cuesta {horas_texto(perdido)} de autonomía por carga.")
        self.lbl_autonomia.config(text="\n".join(lineas))

    def _dibujar_historial(self):
        c = self.grafica
        c.delete("all")
        b = self.resultado["baterias"][0] if self.resultado and self.resultado["baterias"] else None
        datos = b.historial if b else []
        w, h = c.winfo_width(), c.winfo_height()
        if len(datos) < 2:
            c.create_text(w / 2, h / 2, fill="#888", font=("Segoe UI", 10), text=(
                "Windows aún no tiene historial suficiente de esta batería." if b else ""))
            return
        izq, der, arr, abj = 48, 16, 14, 28
        vals = [v for _, v in datos]
        y_min = min(70, int(min(vals) // 10 * 10))
        y_max = max(100, int(-(-max(vals) // 10) * 10))
        x = lambda i: izq + (w - izq - der) * i / (len(datos) - 1)  # noqa: E731
        y = lambda v: arr + (h - arr - abj) * (y_max - v) / (y_max - y_min)  # noqa: E731
        for v in range(y_min, y_max + 1, 10):
            c.create_line(izq, y(v), w - der, y(v), fill="#eef0f3")
            c.create_text(izq - 6, y(v), text=f"{v} %", anchor="e", fill="#888", font=("Segoe UI", 8))
        c.create_line(izq, y(80), w - der, y(80), fill="#e6a100", dash=(4, 3))
        c.create_text(izq + 6, y(80) + 8, text="80 %: límite de desgaste normal", anchor="w",
                      fill="#e6a100", font=("Segoe UI", 8))
        puntos = [(x(i), y(v)) for i, (_, v) in enumerate(datos)]
        c.create_line(*[p for xy in puntos for p in xy], fill="#2f6fed", width=2)
        for px, py in (puntos[0], puntos[-1]):
            c.create_oval(px - 3, py - 3, px + 3, py + 3, fill="#2f6fed", outline="")
        c.create_text(izq, h - 10, text=datos[0][0], anchor="w", fill="#666", font=("Segoe UI", 8))
        c.create_text(w - der, h - 10, text=f"{datos[-1][0]}  ·  {datos[-1][1]:.0f} %",
                      anchor="e", fill="#666", font=("Segoe UI", 8))

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

    def exportar_pdf(self):
        if not self.resultado:
            return
        ruta = filedialog.asksaveasfilename(
            title="Exportar a PDF", defaultextension=".pdf", initialfile="salud_bateria.pdf",
            filetypes=[("PDF", "*.pdf")])
        if not ruta:
            return
        from pdf import exportar_pdf
        try:
            exportar_pdf(self.resultado, ruta)
        except Exception as e:  # noqa: BLE001 - se muestra al usuario
            messagebox.showerror("Exportar PDF", f"No se pudo crear el PDF:\n{e}")
            return
        webbrowser.open("file:///" + os.path.abspath(ruta).replace("\\", "/"))

    def consumo_exacto(self):
        self.btn_exacto.state(["disabled"])
        self.lbl_exacto.config(text="Acepta el permiso de Windows y espera unos segundos…")

        def trabajo():
            from consumo import consumo_exacto_windows
            datos = consumo_exacto_windows()
            self.after(0, mostrar, datos)

        def mostrar(datos):
            self.btn_exacto.state(["!disabled"])
            if datos is None:
                texto = "No se pudo leer: hace falta aceptar el permiso de administrador."
            elif not datos:
                texto = "Windows no tiene datos de energía por programa de las últimas 24 h."
            else:
                texto = "Energía gastada en las últimas 24 h:  " + "   ·   ".join(
                    f"{n} {pc:.0f} %" for n, pc in datos[:8])
            self.lbl_exacto.config(text=texto, foreground="#1d2330")

        threading.Thread(target=trabajo, daemon=True).start()

    def ajustes(self):
        cfg = configuracion.cargar()
        v = tk.Toplevel(self)
        v.title("Ajustes")
        v.resizable(False, False)
        v.transient(self)
        f = ttk.Frame(v, padding=16)
        f.pack()
        avisos = tk.BooleanVar(value=cfg["avisos"])
        alto = tk.IntVar(value=cfg["umbral_alto"])
        bajo = tk.IntVar(value=cfg["umbral_bajo"])
        try:
            arranque = tk.BooleanVar(value=configuracion.arranque_activado())
        except OSError:
            arranque = tk.BooleanVar(value=False)
        ttk.Checkbutton(f, text="Avisarme desde la bandeja del sistema", variable=avisos).grid(
            row=0, column=0, columnspan=2, sticky="w")
        ttk.Label(f, text="Avisar para desenchufar al llegar a (%):").grid(row=1, column=0, sticky="w", pady=(8, 0))
        ttk.Spinbox(f, from_=50, to=100, increment=5, textvariable=alto, width=5).grid(row=1, column=1, pady=(8, 0))
        ttk.Label(f, text="Avisar para enchufar al bajar de (%):").grid(row=2, column=0, sticky="w", pady=(4, 0))
        ttk.Spinbox(f, from_=5, to=50, increment=5, textvariable=bajo, width=5).grid(row=2, column=1, pady=(4, 0))
        ttk.Checkbutton(f, text="Iniciar con el ordenador (solo el icono de la bandeja)", variable=arranque).grid(
            row=3, column=0, columnspan=2, sticky="w", pady=(12, 0))

        def aceptar():
            try:
                cfg.update(avisos=avisos.get(), umbral_alto=int(alto.get()), umbral_bajo=int(bajo.get()))
            except (tk.TclError, ValueError):
                messagebox.showerror("Ajustes", "Los porcentajes deben ser números.", parent=v)
                return
            if cfg["umbral_bajo"] >= cfg["umbral_alto"]:
                messagebox.showerror("Ajustes", "El aviso para enchufar debe ser menor que el de desenchufar.",
                                     parent=v)
                return
            configuracion.guardar(cfg)
            try:
                configuracion.fijar_arranque(arranque.get())
            except OSError as e:
                messagebox.showwarning("Ajustes", f"No se pudo cambiar el inicio automático:\n{e}", parent=v)
            if cfg["avisos"]:
                iniciar_bandeja()
            v.destroy()

        botones = ttk.Frame(f)
        botones.grid(row=4, column=0, columnspan=2, sticky="e", pady=(16, 0))
        ttk.Button(botones, text="Cancelar", command=v.destroy).pack(side="right")
        ttk.Button(botones, text="Guardar", command=aceptar).pack(side="right", padx=8)

    def acerca(self):
        messagebox.showinfo("Acerca de", f"Salud de la batería {VERSION}\n\n"
                            "Mide el desgaste real de la batería con los datos que su firmware "
                            "da al sistema operativo, por eso funciona con cualquier marca de portátil.")


def iniciar_bandeja():
    """Arranca el icono de la bandeja si no está ya funcionando (él mismo lo comprueba)."""
    extra = {"creationflags": subprocess.CREATE_NO_WINDOW} if os.name == "nt" else {}
    try:
        subprocess.Popen(configuracion.orden_bandeja(), **extra)
    except OSError:
        pass


def main():
    if "--bandeja" in sys.argv:
        import bandeja
        bandeja.main()
        return
    App(demo="--demo" in sys.argv).mainloop()


if __name__ == "__main__":
    main()
