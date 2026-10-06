#!/usr/bin/env python3
"""Salud de la batería: analiza la batería de cualquier portátil.

Uso:
    python salud_bateria.py              # analiza y abre el informe en el navegador
    python salud_bateria.py --consola    # solo texto en la terminal
    python salud_bateria.py --json       # datos en JSON (para guardar un historial)
    python salud_bateria.py --demo       # datos de ejemplo, sin leer el hardware
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import os
import sys
import webbrowser

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from consejos import consejos, diagnostico  # noqa: E402
from consumo import Proceso, ajustes_energia, consejo_programa, procesos_que_mas_consumen  # noqa: E402
from informe import ahora, html_informe, texto  # noqa: E402
from lectores import Bateria, leer_baterias  # noqa: E402


def datos_demo():
    b = Bateria(nombre="BAT0", fabricante="Ejemplo", modelo="DEMO-45", quimica="Li-ion",
                capacidad_diseno_mwh=57000, capacidad_actual_mwh=46170, porcentaje=100,
                ciclos=312, temperatura_c=36.5, enchufado=True, estado="llena", potencia_w=0)
    procs = [Proceso("chrome", 48.2, 1830, 23), Proceso("Teams", 12.5, 640, 6),
             Proceso("OneDrive", 6.1, 120, 1), Proceso("python3", 2.0, 40, 1)]
    for p in procs:
        p.consejo = consejo_programa(p.nombre)
    return [b], procs, {"Plan de energía": "Alto rendimiento", "Brillo de pantalla": "90 %"}


def analizar(segundos: float, demo: bool) -> dict:
    if demo:
        baterias, procesos, ajustes = datos_demo()
    else:
        baterias = leer_baterias()
        try:
            procesos = procesos_que_mas_consumen(segundos)
        except ImportError:
            procesos = []
            if sys.stderr:  # en el .exe con ventana no hay consola
                print("Aviso: instala psutil (pip install psutil) para ver los programas que más consumen.",
                      file=sys.stderr)
        ajustes = ajustes_energia()
    principal = baterias[0] if baterias else Bateria()
    return {
        "fecha": ahora(),
        "segundos": segundos,
        "baterias": baterias,
        "diagnosticos": [diagnostico(b) for b in baterias],
        "procesos": procesos,
        "ajustes": ajustes,
        "consejos": consejos(principal, procesos, ajustes),
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Analiza la salud de la batería del portátil.")
    ap.add_argument("--consola", action="store_true", help="solo texto, sin abrir el navegador")
    ap.add_argument("--json", action="store_true", help="imprime los datos en JSON")
    ap.add_argument("--demo", action="store_true", help="usa datos de ejemplo")
    ap.add_argument("--segundos", type=float, default=3, help="tiempo midiendo procesos (3 por defecto)")
    ap.add_argument("--salida", default=None, help="ruta del informe HTML")
    args = ap.parse_args(argv)

    if not args.json:
        print(f"Analizando la batería y midiendo el consumo durante {args.segundos:.0f} s...")
    r = analizar(args.segundos, args.demo)

    if args.json:
        datos = {k: v for k, v in r.items() if k not in ("baterias", "procesos")}
        datos["baterias"] = [dict(dataclasses.asdict(b), salud=b.salud, desgaste=b.desgaste)
                             for b in r["baterias"]]
        datos["procesos"] = [dataclasses.asdict(p) for p in r["procesos"]]
        print(json.dumps(datos, ensure_ascii=False, indent=2))
        return 0

    print(texto(r))
    if not args.consola:
        ruta = os.path.abspath(args.salida or os.path.join(os.path.expanduser("~"), "salud_bateria.html"))
        with open(ruta, "w", encoding="utf-8") as f:
            f.write(html_informe(r))
        print(f"\nInforme guardado en {ruta}")
        webbrowser.open("file://" + ruta)
    return 0


if __name__ == "__main__":
    sys.exit(main())
