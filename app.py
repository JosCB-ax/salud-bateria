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
import time
import tkinter as tk
import webbrowser
from tkinter import filedialog, messagebox, ttk

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import actualizaciones  # noqa: E402
import ahorro  # noqa: E402
import configuracion  # noqa: E402
import historial  # noqa: E402
import legal  # noqa: E402
import prediccion  # noqa: E402
from configuracion import recurso  # noqa: E402
import tema  # noqa: E402
import idioma  # noqa: E402
from idioma import t as tr  # noqa: E402
from autonomia import calcular, horas_texto, sin_datos_texto  # noqa: E402
from informe import COLORES, _filas, html_informe  # noqa: E402
from salud_bateria import analizar  # noqa: E402

VERSION = "1.6.0"
NOMBRES_NIVEL = {"excelente": "Excelente", "buena": "Buena", "desgastada": "Desgastada",
                 "mala": "Mala", "desconocida": "Sin datos"}


def _traducir_tk():
    """Traduce al idioma elegido los textos de todos los widgets al crearlos o cambiarlos."""
    import tkinter.messagebox as mb
    original_options = tk.Misc._options

    def _options(self, cnf, kw=None):
        if isinstance(cnf, dict) and isinstance(cnf.get("text"), str):
            cnf = dict(cnf, text=tr(cnf["text"]))
        if isinstance(kw, dict) and isinstance(kw.get("text"), str):
            kw = dict(kw, text=tr(kw["text"]))
        return original_options(self, cnf, kw)

    tk.Misc._options = _options
    for clase, metodo in ((ttk.Notebook, "add"), (ttk.Treeview, "heading")):
        def nuevo(self, *args, _orig=getattr(clase, metodo), **kw):
            if isinstance(kw.get("text"), str):
                kw["text"] = tr(kw["text"])
            return _orig(self, *args, **kw)
        setattr(clase, metodo, nuevo)
    original_insert = ttk.Treeview.insert

    def insert(self, parent, index, iid=None, **kw):
        if "values" in kw:
            kw["values"] = tuple(tr(v) if isinstance(v, str) else v for v in kw["values"])
        return original_insert(self, parent, index, iid, **kw)

    ttk.Treeview.insert = insert
    original_title = tk.Wm.wm_title

    def wm_title(self, string=None):
        return original_title(self, tr(string) if string else string)

    tk.Wm.wm_title = tk.Wm.title = wm_title
    original_show = mb._show

    def _show(title=None, message=None, *args, **kw):
        return original_show(tr(title), tr(message), *args, **kw)

    mb._show = _show


_traducir_tk()


class App(tk.Tk):
    def __init__(self, demo: bool = False):
        super().__init__()
        self.demo = demo
        self.resultado = None
        self._n_analisis = 0
        self.geometry("920x680")
        self.minsize(760, 560)
        try:
            self.iconbitmap(recurso("icono.ico"))
        except tk.TclError:
            pass

        self._construir()
        self.after(100, self.actualizar)
        if not demo and configuracion.cargar().get("avisos"):
            iniciar_bandeja()
        if not demo:
            self.after(3000, self.buscar_actualizacion)

    # ------------------------------------------------------------ interfaz

    def _construir(self):
        """Crea toda la interfaz con el tema elegido (se repite al cambiar de tema)."""
        for w in self.winfo_children():
            w.destroy()
        idioma.fijar(configuracion.cargar().get("idioma", "es"))
        self.title("Salud de la batería")
        self.p = tema.aplicar(self, tema.elegir(configuracion.cargar().get("tema", "automatico")))
        estilo = ttk.Style(self)
        estilo.configure("Titulo.TLabel", font=("Segoe UI", 16, "bold"))
        estilo.configure("Diag.TLabel", font=("Segoe UI", 11))
        self._cabecera()
        self._barra()  # antes que las pestañas, para que siempre quede visible abajo
        self._pestanas()
        if self.resultado:
            self._mostrar(self.resultado)

    def _cabecera(self):
        top = ttk.Frame(self, padding=(16, 16, 16, 8))
        top.pack(fill="x")
        self.lienzo = tk.Canvas(top, width=140, height=140, highlightthickness=0,
                                bg=self.p["bg"])
        self.lienzo.pack(side="left")
        texto = ttk.Frame(top, padding=(16, 8, 0, 0))
        texto.pack(side="left", fill="both", expand=True)
        self.lbl_titulo = ttk.Label(texto, text="Analizando la batería…", style="Titulo.TLabel")
        self.lbl_titulo.pack(anchor="w")
        self.lbl_diag = ttk.Label(texto, text="", style="Diag.TLabel", wraplength=640, justify="left")
        self.lbl_diag.pack(anchor="w", pady=(6, 0))
        self.lbl_resumen = ttk.Label(texto, text="", foreground=self.p["mut"], wraplength=640, justify="left")
        self.lbl_resumen.pack(anchor="w", pady=(8, 0))
        self.lbl_estado = ttk.Label(texto, text="", foreground=self.p["mut"], font=("Segoe UI", 9))
        self.lbl_estado.pack(anchor="w", pady=(4, 0))
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
        ttk.Button(f, text="Calibrar la batería…", command=self.calibracion).pack(anchor="w", pady=(8, 0))
        self.nb.add(f, text="Batería")

        # Autonomía e historial
        f = ttk.Frame(self.nb, padding=12)
        ttk.Label(f, text="Autonomía real con la configuración de este equipo",
                  font=("Segoe UI", 12, "bold")).pack(anchor="w")
        self.lbl_autonomia = ttk.Label(f, text="", wraplength=840, justify="left", font=("Segoe UI", 11))
        self.lbl_autonomia.pack(anchor="w", pady=(6, 12))
        ttk.Label(f, text="Evolución de la salud", font=("Segoe UI", 12, "bold")).pack(anchor="w")
        self.lbl_prediccion = ttk.Label(f, text="", wraplength=840, justify="left")
        self.lbl_prediccion.pack(anchor="w", pady=(4, 0))
        self.grafica = tk.Canvas(f, height=220, bg=self.p["panel"], highlightthickness=1,
                                 highlightbackground=self.p["linea"])
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
                                          wraplength=820, justify="left", foreground=self.p["mut"])
        self.lbl_consejo_proc.pack(anchor="w", pady=(8, 0))
        if platform.system() == "Windows":
            fila = ttk.Frame(f)
            fila.pack(anchor="w", pady=(8, 0))
            self.btn_exacto = ttk.Button(fila, text="Medir consumo exacto (24 h)…", command=self.consumo_exacto)
            self.btn_exacto.pack(side="left")
            self.lbl_exacto = ttk.Label(fila, text="Usa el registro de energía de Windows; pide permiso de administrador.",
                                        foreground=self.p["mut"], wraplength=600, justify="left")
            self.lbl_exacto.pack(side="left", padx=10)
        self.lbl_ajustes = ttk.Label(f, text="", wraplength=820, justify="left")
        self.lbl_ajustes.pack(anchor="w", pady=(8, 0))
        fila = ttk.Frame(f)
        fila.pack(anchor="w", pady=(8, 0))
        self.btn_ahorro = ttk.Button(fila, command=self.alternar_ahorro)
        self.btn_ahorro.pack(side="left")
        self.lbl_ahorro = ttk.Label(fila, text="", foreground=self.p["mut"], wraplength=600, justify="left")
        self.lbl_ahorro.pack(side="left", padx=10)
        self._pintar_ahorro()
        self.nb.add(f, text="Qué consume más")

        # Consejos
        f = ttk.Frame(self.nb, padding=8)
        self.txt_consejos = tk.Text(f, wrap="word", relief="flat", font=("Segoe UI", 11),
                                    padx=8, pady=8, cursor="arrow", bg=self.p["panel"], fg=self.p["fg"])
        sb = ttk.Scrollbar(f, command=self.txt_consejos.yview)
        self.txt_consejos.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.txt_consejos.pack(fill="both", expand=True)
        self.nb.add(f, text="Consejos")

    def _barra(self):
        ttk.Label(self, text=legal.pie(), foreground=self.p["mut"],
                  font=("Segoe UI", 8)).pack(side="bottom", pady=(0, 6))
        b = ttk.Frame(self, padding=(16, 16, 16, 6))
        b.pack(side="bottom", fill="x")
        self.btn_actualizar = ttk.Button(b, text="Actualizar", command=self.actualizar)
        self.btn_actualizar.pack(side="left")
        ttk.Button(b, text="Exportar PDF…", command=self.exportar_pdf).pack(side="left", padx=(8, 0))
        ttk.Button(b, text="Guardar informe…", command=self.guardar).pack(side="left", padx=8)
        ttk.Button(b, text="Ajustes", command=self.ajustes).pack(side="right", padx=(0, 8))
        ttk.Button(b, text="Acerca de", command=self.acerca).pack(side="right")
        ttk.Button(b, text="Prueba de autonomía…", command=self.prueba_autonomia).pack(side="right", padx=(0, 8))

    def _dibujar_indicador(self, salud, nivel):
        c = self.lienzo
        c.delete("all")
        color = COLORES[nivel]
        c.create_oval(10, 10, 130, 130, outline=self.p["linea"], width=14)
        if salud:
            c.create_arc(10, 10, 130, 130, start=90, extent=-3.6 * min(salud, 100),
                         style="arc", outline=color, width=14)
        c.create_text(70, 62, text=f"{salud:.0f} %" if salud is not None else "?",
                      font=("Segoe UI", 22, "bold"), fill=color)
        c.create_text(70, 90, text="salud", font=("Segoe UI", 10), fill=self.p["mut"])

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
        self._n_analisis += 1
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
            t.insert("end", f"{i}.  {tr(c)}\n\n")
        t.config(state="disabled")

        self._mostrar_autonomia(r["baterias"][0] if r["baterias"] else None)
        b0 = r["baterias"][0] if r["baterias"] else None
        self.lbl_prediccion.config(text=prediccion.texto(prediccion.predecir(b0.salud, b0.historial)) if b0 else "")
        self._dibujar_historial()

    def _mostrar_autonomia(self, b):
        if b is None:
            self.lbl_autonomia.config(text="No hay batería.")
            return
        escenarios = calcular(b)
        lineas = [] if escenarios else [sin_datos_texto(b)]
        for e in escenarios:
            lineas.append(f"{e.titulo} ({e.vatios:.1f} W, {e.detalle}):")
            linea = f"    Carga completa hoy: {horas_texto(e.horas_hoy)}"
            if e.horas_nueva:
                linea += f"   ·   cuando era nueva: {horas_texto(e.horas_nueva)}"
            if e.horas_carga_actual and not b.enchufado:
                linea += f"   ·   con la carga actual: {horas_texto(e.horas_carga_actual)}"
            lineas.append(linea)
        try:
            pruebas = historial.cargar()["pruebas"]
        except OSError:
            pruebas = []
        if pruebas:
            u = pruebas[-1]
            lineas.append(f"Última prueba guiada ({u['fecha']}, uso {u.get('uso', 'ligero')}): "
                          f"{u['vatios']} W, carga completa {horas_texto(u['horas_hoy'])}.")
        if escenarios and escenarios[0].horas_nueva:
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
            c.create_text(w / 2, h / 2, fill=self.p["mut"], font=("Segoe UI", 10), text=(
                "Windows aún no tiene historial suficiente de esta batería." if b else ""))
            return
        izq, der, arr, abj = 48, 16, 14, 28
        vals = [v for _, v in datos]
        y_min = min(70, int(min(vals) // 10 * 10))
        y_max = max(100, int(-(-max(vals) // 10) * 10))
        x = lambda i: izq + (w - izq - der) * i / (len(datos) - 1)  # noqa: E731
        y = lambda v: arr + (h - arr - abj) * (y_max - v) / (y_max - y_min)  # noqa: E731
        for v in range(y_min, y_max + 1, 10):
            c.create_line(izq, y(v), w - der, y(v), fill=self.p["rejilla"])
            c.create_text(izq - 6, y(v), text=f"{v} %", anchor="e", fill=self.p["mut"], font=("Segoe UI", 8))
        c.create_line(izq, y(80), w - der, y(80), fill="#e6a100", dash=(4, 3))
        c.create_text(izq + 6, y(80) + 8, text="80 %: límite de desgaste normal", anchor="w",
                      fill="#e6a100", font=("Segoe UI", 8))
        puntos = [(x(i), y(v)) for i, (_, v) in enumerate(datos)]
        c.create_line(*[p for xy in puntos for p in xy], fill=self.p["acc"], width=2)
        for px, py in (puntos[0], puntos[-1]):
            c.create_oval(px - 3, py - 3, px + 3, py + 3, fill=self.p["acc"], outline="")
        c.create_text(izq, h - 10, text=datos[0][0], anchor="w", fill=self.p["mut"], font=("Segoe UI", 8))
        c.create_text(w - der, h - 10, text=f"{datos[-1][0]}  ·  {datos[-1][1]:.0f} %",
                      anchor="e", fill=self.p["mut"], font=("Segoe UI", 8))

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
            title=tr("Guardar informe"), defaultextension=".html", initialfile="salud_bateria.html",
            filetypes=[(tr("Informe HTML"), "*.html")])
        if not ruta:
            return
        with open(ruta, "w", encoding="utf-8") as f:
            f.write(html_informe(self.resultado))
        webbrowser.open("file:///" + os.path.abspath(ruta).replace("\\", "/"))

    def exportar_pdf(self):
        if not self.resultado:
            return
        ruta = filedialog.asksaveasfilename(
            title=tr("Exportar a PDF"), defaultextension=".pdf", initialfile="salud_bateria.pdf",
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
            self.lbl_exacto.config(text=texto, foreground=self.p["fg"])

        threading.Thread(target=trabajo, daemon=True).start()

    def ajustes(self):
        cfg = configuracion.cargar()
        v = tk.Toplevel(self)
        v.title("Ajustes")
        v.resizable(False, False)
        v.transient(self)
        f = ttk.Frame(v, padding=16)
        f.pack()
        rec = configuracion.POR_DEFECTO
        avisos = tk.BooleanVar(value=cfg["avisos"])
        alto = tk.IntVar(value=cfg["umbral_alto"])
        bajo = tk.IntVar(value=cfg["umbral_bajo"])
        temas = {k: tr(x) for k, x in {"automatico": "Automático (como el sistema)", "claro": "Claro",
                                        "oscuro": "Oscuro"}.items()}
        tema_var = tk.StringVar(value=temas.get(cfg.get("tema", "automatico"), temas["automatico"]))
        try:
            arranque = tk.BooleanVar(value=configuracion.arranque_activado())
        except OSError:
            arranque = tk.BooleanVar(value=False)
        buscar_act = tk.BooleanVar(value=cfg.get("buscar_actualizaciones", True))

        ttk.Label(f, text="Avisos de carga", font=("Segoe UI", 11, "bold")).grid(row=0, column=0, sticky="w")
        ttk.Checkbutton(f, text="Avisarme desde la bandeja del sistema", variable=avisos).grid(
            row=1, column=0, columnspan=3, sticky="w", pady=(4, 0))
        ttk.Label(f, text="Avisar para desenchufar al llegar a:").grid(row=2, column=0, sticky="w", pady=(8, 0))
        ttk.Spinbox(f, from_=50, to=100, increment=5, textvariable=alto, width=5).grid(row=2, column=1, pady=(8, 0))
        ttk.Label(f, text=f"%  (recomendado: {rec['umbral_alto']})", foreground=self.p["mut"]).grid(
            row=2, column=2, sticky="w", pady=(8, 0))
        ttk.Label(f, text="Avisar para enchufar al bajar de:").grid(row=3, column=0, sticky="w", pady=(4, 0))
        ttk.Spinbox(f, from_=5, to=50, increment=5, textvariable=bajo, width=5).grid(row=3, column=1, pady=(4, 0))
        ttk.Label(f, text=f"%  (recomendado: {rec['umbral_bajo']})", foreground=self.p["mut"]).grid(
            row=3, column=2, sticky="w", pady=(4, 0))
        ttk.Button(f, text="Restaurar recomendados",
                   command=lambda: (alto.set(rec["umbral_alto"]), bajo.set(rec["umbral_bajo"]),
                                    umbral_temp.set(rec["umbral_temp"]))).grid(
            row=4, column=0, sticky="w", pady=(8, 0))
        ttk.Checkbutton(f, text="Iniciar con el ordenador (solo el icono de la bandeja)", variable=arranque).grid(
            row=5, column=0, columnspan=3, sticky="w", pady=(8, 0))
        aviso_temp = tk.BooleanVar(value=cfg.get("aviso_temperatura", True))
        umbral_temp = tk.IntVar(value=cfg.get("umbral_temp", rec["umbral_temp"]))
        ttk.Checkbutton(f, text="Avisar si la batería pasa de", variable=aviso_temp).grid(
            row=6, column=0, sticky="w", pady=(8, 0))
        ttk.Spinbox(f, from_=30, to=60, increment=1, textvariable=umbral_temp, width=5).grid(
            row=6, column=1, pady=(8, 0))
        ttk.Label(f, text=f"°C  (recomendado: {rec['umbral_temp']})", foreground=self.p["mut"]).grid(
            row=6, column=2, sticky="w", pady=(8, 0))
        idiomas = {"es": "Español", "en": "English"}
        idioma_var = tk.StringVar(value=idiomas.get(cfg.get("idioma", "es"), "Español"))
        ttk.Label(f, text="Idioma:").grid(row=10, column=0, sticky="w", pady=(6, 0))
        ttk.Combobox(f, textvariable=idioma_var, values=list(idiomas.values()), state="readonly", width=28).grid(
            row=10, column=1, columnspan=2, sticky="w", pady=(6, 0))

        ttk.Label(f, text="Aspecto y actualizaciones", font=("Segoe UI", 11, "bold")).grid(
            row=8, column=0, sticky="w", pady=(16, 0))
        ttk.Label(f, text="Tema:").grid(row=9, column=0, sticky="w", pady=(6, 0))
        ttk.Combobox(f, textvariable=tema_var, values=list(temas.values()), state="readonly", width=28).grid(
            row=9, column=1, columnspan=2, sticky="w", pady=(6, 0))
        ttk.Checkbutton(f, text="Buscar versiones nuevas al abrir el programa", variable=buscar_act).grid(
            row=11, column=0, columnspan=3, sticky="w", pady=(8, 0))

        def aceptar():
            try:
                cfg.update(avisos=avisos.get(), umbral_alto=int(alto.get()), umbral_bajo=int(bajo.get()),
                           aviso_temperatura=aviso_temp.get(), umbral_temp=int(umbral_temp.get()))
            except (tk.TclError, ValueError):
                messagebox.showerror("Ajustes", "Los porcentajes deben ser números.", parent=v)
                return
            if not (0 < cfg["umbral_bajo"] < cfg["umbral_alto"] <= 100):
                messagebox.showerror("Ajustes", "El aviso para enchufar debe ser menor que el de desenchufar.",
                                     parent=v)
                return
            tema_antes = (cfg.get("tema", "automatico"), cfg.get("idioma", "es"))
            cfg["idioma"] = next(k for k, t in idiomas.items() if t == idioma_var.get())
            cfg["tema"] = next(k for k, t in temas.items() if t == tema_var.get())
            cfg["buscar_actualizaciones"] = buscar_act.get()
            configuracion.guardar(cfg)
            try:
                configuracion.fijar_arranque(arranque.get())
            except OSError as e:
                messagebox.showwarning("Ajustes", f"No se pudo cambiar el inicio automático:\n{e}", parent=v)
            if cfg["avisos"]:
                iniciar_bandeja()
            v.destroy()
            if (cfg["tema"], cfg["idioma"]) != tema_antes:
                self._construir()

        ttk.Label(f, text="Información legal", font=("Segoe UI", 11, "bold")).grid(
            row=12, column=0, sticky="w", pady=(16, 0))
        leyes = ttk.Frame(f)
        leyes.grid(row=13, column=0, columnspan=3, sticky="w", pady=(6, 0))
        for clave, nombre in (("privacidad", "Privacidad"), ("terminos", "Términos de uso"),
                              ("fuentes", "Fuentes y cookies")):
            ttk.Button(leyes, text=nombre, command=lambda c=clave: self.ventana_legal(c, v)).pack(
                side="left", padx=(0, 8))
        botones = ttk.Frame(f)
        botones.grid(row=14, column=0, columnspan=3, sticky="e", pady=(16, 0))
        ttk.Button(botones, text="Cancelar", command=v.destroy).pack(side="right")
        ttk.Button(botones, text="Guardar", command=aceptar).pack(side="right", padx=8)

    def ventana_legal(self, clave: str, padre=None):
        titulo, cuerpo = legal.texto(clave)
        v = tk.Toplevel(padre or self)
        v.title(titulo)
        v.transient(padre or self)
        v.geometry("640x520")
        f = ttk.Frame(v, padding=12)
        f.pack(fill="both", expand=True)
        barra = ttk.Scrollbar(f, orient="vertical")
        caja = tk.Text(f, wrap="word", relief="flat", highlightthickness=0, padx=10, pady=8, font=("Segoe UI", 10),
                       bg=self.p["panel"], fg=self.p["fg"], yscrollcommand=barra.set)
        barra.config(command=caja.yview)
        barra.pack(side="right", fill="y")
        caja.pack(side="left", fill="both", expand=True)
        caja.insert("1.0", f"{cuerpo}\n\n{legal.pie()}")
        caja.config(state="disabled")
        ttk.Button(v, text="Cerrar", command=v.destroy).pack(side="right", padx=12, pady=(0, 12))

    def _pintar_ahorro(self, detalle: str = ""):
        if ahorro.activo():
            self.btn_ahorro.config(text="Desactivar modo ahorro")
            self.lbl_ahorro.config(text=detalle or "Modo ahorro activo. Se desactiva solo al enchufar el cargador.")
        else:
            self.btn_ahorro.config(text="Activar modo ahorro")
            self.lbl_ahorro.config(text=detalle or "Pone el plan de ahorro de energía y baja el brillo; "
                                                   "al desactivarlo lo deja todo como estaba.")

    def alternar_ahorro(self):
        self.btn_ahorro.state(["disabled"])

        def trabajo():
            if ahorro.activo():
                ahorro.desactivar()
                detalle = "Modo ahorro desactivado: todo está como antes."
            else:
                hecho = ahorro.activar()
                detalle = "Modo ahorro activado. " + ("; ".join(hecho) if hecho else
                                                       "Este equipo no permite cambiar plan ni brillo desde aquí.")
            self.after(0, lambda: (self.btn_ahorro.state(["!disabled"]), self._pintar_ahorro(detalle)))

        threading.Thread(target=trabajo, daemon=True).start()

    def calibracion(self):
        b = self.resultado["baterias"][0] if self.resultado and self.resultado["baterias"] else None
        cfg = configuracion.cargar()
        cal = cfg.get("calibracion")
        v = tk.Toplevel(self)
        v.title("Calibrar la batería")
        v.resizable(False, False)
        v.transient(self)
        f = ttk.Frame(v, padding=16)
        f.pack()
        ttk.Label(f, wraplength=480, justify="left", text=(
            "La calibración no repara la batería: corrige la medida que hace su chip, que con el tiempo se "
            "desajusta y puede marcar menos salud de la real. Hazla como mucho cada 2 o 3 meses.\n\n"
            "1. Carga al 100 % y déjalo enchufado una o dos horas más.\n"
            "2. Desenchufa y úsalo con normalidad hasta que se apague solo (o baje al 3-5 %).\n"
            "3. Déjalo apagado unas horas y cárgalo al 100 % sin interrumpir.\n"
            "4. Abre el programa y pulsa «He terminado» para comparar.")).pack(anchor="w")
        estado = ttk.Label(f, text="", wraplength=480, justify="left")
        estado.pack(anchor="w", pady=(12, 0))
        botones = ttk.Frame(f)
        botones.pack(anchor="e", pady=(12, 0))

        def empezar():
            if not b or b.salud is None:
                estado.config(text="No se puede leer la salud de esta batería, así que no hay nada que comparar.")
                return
            cfg["calibracion"] = {"fecha": time.strftime("%Y-%m-%d"), "salud": b.salud}
            configuracion.guardar(cfg)
            estado.config(text=f"Apuntado: salud antes de calibrar {b.salud:.1f} %. Sigue los pasos.")

        def terminar():
            n_antes = self._n_analisis
            self.actualizar()

            def comparar():
                if self._n_analisis == n_antes:  # el análisis aún no ha terminado
                    v.after(1000, comparar)
                    return
                ahora = self.resultado["baterias"][0].salud if self.resultado and self.resultado["baterias"] else None
                if ahora is None or not cal:
                    return
                dif = ahora - cal["salud"]
                estado.config(text=(f"Antes ({cal['fecha']}): {cal['salud']:.1f} %   ·   Ahora: {ahora:.1f} %   ·   "
                                    f"Diferencia: {dif:+.1f} puntos. ") + (
                    "La medida estaba desajustada y ahora es más exacta." if dif >= 1 else
                    "La medida ya era correcta: este es el desgaste real."))
                cfg.pop("calibracion", None)
                configuracion.guardar(cfg)
            v.after(1000, comparar)
            estado.config(text="Midiendo…")

        ttk.Button(botones, text="Cerrar", command=v.destroy).pack(side="right")
        if cal:
            estado.config(text=f"Calibración empezada el {cal['fecha']} con {cal['salud']:.1f} % de salud.")
            ttk.Button(botones, text="He terminado: comparar", command=terminar).pack(side="right", padx=8)
        else:
            ttk.Button(botones, text="Empezar calibración", command=empezar).pack(side="right", padx=8)

    def prueba_autonomia(self):
        import prueba
        b = self.resultado["baterias"][0] if self.resultado and self.resultado["baterias"] else None
        v = tk.Toplevel(self)
        v.title("Prueba de autonomía")
        v.resizable(False, False)
        v.transient(self)
        f = ttk.Frame(v, padding=16)
        f.pack()
        ttk.Label(f, wraplength=460, justify="left", text=(
            "Mide cuánto dura tu batería con un uso fijo. Antes de empezar: desenchufa el cargador, "
            "pon el brillo de la pantalla al 50 % y cierra los programas que no necesites. "
            "No toques el portátil hasta que termine.")).grid(row=0, column=0, columnspan=3, sticky="w")
        minutos = tk.IntVar(value=prueba.DURACION_RECOMENDADA)
        ttk.Label(f, text="Duración:").grid(row=1, column=0, sticky="w", pady=(12, 0))
        ttk.Spinbox(f, from_=5, to=180, increment=5, textvariable=minutos, width=5).grid(
            row=1, column=1, sticky="w", pady=(12, 0))
        ttk.Label(f, text=f"minutos  (recomendado: {prueba.DURACION_RECOMENDADA}; más tiempo, más precisión)",
                  foreground=self.p["mut"]).grid(row=1, column=2, sticky="w", pady=(12, 0))
        cargas = {k: tr(x) for k, x in prueba.CARGAS.items()}
        carga = tk.StringVar(value=cargas["ligera"])
        ttk.Label(f, text="Tipo de uso:").grid(row=2, column=0, sticky="w", pady=(6, 0))
        ttk.Combobox(f, textvariable=carga, values=list(cargas.values()), state="readonly",
                     width=58).grid(row=2, column=1, columnspan=2, sticky="w", pady=(6, 0))
        barra = ttk.Progressbar(f, length=460, mode="determinate")
        barra.grid(row=3, column=0, columnspan=3, pady=(14, 0))
        estado = ttk.Label(f, text="", wraplength=460, justify="left")
        estado.grid(row=4, column=0, columnspan=3, sticky="w", pady=(8, 0))
        botones = ttk.Frame(f)
        botones.grid(row=5, column=0, columnspan=3, sticky="e", pady=(12, 0))
        cancelar = threading.Event()
        btn_empezar = ttk.Button(botones, text="Empezar")
        btn_empezar.pack(side="right")
        ttk.Button(botones, text="Cerrar", command=lambda: (cancelar.set(), v.destroy())).pack(side="right", padx=8)

        def empezar():
            try:
                total = int(minutos.get()) * 60
                if total < 300:
                    raise ValueError
            except (tk.TclError, ValueError):
                messagebox.showerror("Prueba de autonomía", "La duración mínima es de 5 minutos.", parent=v)
                return
            clave = next(k for k, x in cargas.items() if x == carga.get())
            btn_empezar.state(["disabled"])
            barra.configure(maximum=total, value=0)

            def progreso(restante):
                self.after(0, lambda: v.winfo_exists() and (
                    barra.configure(value=total - restante),
                    estado.config(text=f"Midiendo… quedan {int(restante // 60)} min {int(restante % 60):02d} s")))

            def trabajo():
                try:
                    r = prueba.ejecutar_prueba(total / 60, clave, b.capacidad_actual_mwh if b else None,
                                               b.capacidad_diseno_mwh if b else None, progreso, cancelar)
                    try:
                        historial.registrar_prueba(dict(r, uso=clave))
                    except OSError:
                        pass
                    texto = (f"Resultado: consume {r['vatios']} W con este uso. Una carga completa dura "
                             f"{horas_texto(r['horas_hoy'])}")
                    if r["horas_nueva"]:
                        texto += f" (cuando era nueva: {horas_texto(r['horas_nueva'])})"
                    texto += f". Precisión de la medida: {r['precision']}."
                except ValueError as e:
                    texto = str(e)
                self.after(0, lambda: v.winfo_exists() and (
                    estado.config(text=texto), btn_empezar.state(["!disabled"])))

            threading.Thread(target=trabajo, daemon=True).start()

        btn_empezar.configure(command=empezar)

    def buscar_actualizacion(self, avisar_si_no_hay: bool = False):
        cfg = configuracion.cargar()
        if not avisar_si_no_hay and (not cfg.get("buscar_actualizaciones", True)
                                     or not actualizaciones.toca_buscar(cfg)):
            return

        def trabajo():
            info = actualizaciones.buscar(VERSION)
            cfg["ultima_busqueda"] = time.time()
            try:
                configuracion.guardar(cfg)
            except OSError:
                pass
            self.after(0, ofrecer, info)

        def ofrecer(info):
            if not info:
                if avisar_si_no_hay:
                    messagebox.showinfo("Actualizaciones", f"Tienes la última versión ({VERSION}).")
                return
            if messagebox.askyesno("Actualización disponible",
                                   f"Hay una versión nueva: {info['version']} (tienes la {VERSION}).\n\n"
                                   "¿Descargarla e instalarla ahora?"):
                try:
                    if actualizaciones.instalar(info):
                        self.destroy()
                except (OSError, ValueError) as e:
                    messagebox.showerror("Actualizaciones", f"No se pudo descargar:\n{e}")

        threading.Thread(target=trabajo, daemon=True).start()

    def acerca(self):
        if messagebox.askyesno("Acerca de", f"Salud de la batería {VERSION}\n{legal.copyright()}\n\n"
                               "Mide el desgaste real de la batería con los datos que su firmware "
                               "da al sistema operativo, por eso funciona con cualquier marca de portátil.\n\n"
                               f"{legal.aviso_ia()}\n"
                               "Privacidad, términos de uso y fuentes: en Ajustes.\n\n"
                               "¿Buscar ahora si hay una versión nueva?"):
            self.buscar_actualizacion(avisar_si_no_hay=True)


def iniciar_bandeja():
    """Arranca el icono de la bandeja si no está ya funcionando (él mismo lo comprueba)."""
    extra = {"creationflags": subprocess.CREATE_NO_WINDOW} if os.name == "nt" else {}
    try:
        subprocess.Popen(configuracion.orden_bandeja(), **extra)
    except OSError:
        pass


def main():
    import multiprocessing
    multiprocessing.freeze_support()  # la prueba de autonomía usa procesos dentro del .exe
    if "--bandeja" in sys.argv:
        import bandeja
        bandeja.main()
        return
    App(demo="--demo" in sys.argv).mainloop()


if __name__ == "__main__":
    main()
