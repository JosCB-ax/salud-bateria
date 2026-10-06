"""Historial propio: el programa guarda sus mediciones para no depender del sistema.

Se guarda en historial.json, en la carpeta de ajustes del usuario:
- salud: una entrada por día con la capacidad y los ciclos.
- consumo: muestras del consumo real con el portátil desenchufado.
- pruebas: resultados de la prueba de autonomía guiada.
Así la gráfica y la autonomía de "uso habitual" funcionan también en Mac y Linux.
"""

from __future__ import annotations

import datetime as dt
import json
import os

import configuracion

MAX_MUESTRAS = 5000
DIAS_CONSUMO = 30


def _ruta() -> str:
    return os.path.join(configuracion.carpeta(), "historial.json")


def cargar() -> dict:
    try:
        with open(_ruta(), encoding="utf-8") as f:
            datos = json.load(f)
    except (OSError, ValueError):
        datos = {}
    for k in ("salud", "consumo", "pruebas"):
        datos.setdefault(k, [])
    return datos


def _guardar(datos: dict) -> None:
    tmp = _ruta() + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(datos, f)
    os.replace(tmp, _ruta())


def registrar(b, ahora: dt.datetime | None = None) -> None:
    """Apunta la salud de hoy y, si está desenchufado, una muestra de consumo."""
    ahora = ahora or dt.datetime.now()
    datos = cargar()
    if b.salud is not None:
        hoy = ahora.date().isoformat()
        datos["salud"] = [s for s in datos["salud"] if s["fecha"] != hoy]
        datos["salud"].append({"fecha": hoy, "salud": b.salud, "ciclos": b.ciclos,
                               "capacidad": b.capacidad_actual_mwh})
        datos["salud"].sort(key=lambda s: s["fecha"])
    if not b.enchufado and b.potencia_w and b.potencia_w > 0.5:
        datos["consumo"].append({"t": ahora.isoformat(timespec="minutes"), "w": b.potencia_w})
        datos["consumo"] = datos["consumo"][-MAX_MUESTRAS:]
    _guardar(datos)


def registrar_prueba(resultado: dict) -> None:
    datos = cargar()
    datos["pruebas"].append(resultado)
    _guardar(datos)


def completar(b, ahora: dt.datetime | None = None) -> None:
    """Rellena lo que el sistema no da (historial, consumo medio) con lo guardado."""
    datos = cargar()
    if len(b.historial) < 2 and len(datos["salud"]) >= 2:
        b.historial = [(s["fecha"], s["salud"]) for s in datos["salud"]]
    if not b.consumo_medio_w:
        limite = ((ahora or dt.datetime.now()) - dt.timedelta(days=DIAS_CONSUMO)).isoformat()
        muestras = [m["w"] for m in datos["consumo"] if m["t"] >= limite]
        if len(muestras) >= 6:  # al menos una hora de muestras cada 10 min
            b.consumo_medio_w = round(sum(muestras) / len(muestras), 2)
            b.horas_medidas = round(len(muestras) / 6, 1)
