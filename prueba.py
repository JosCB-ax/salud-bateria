"""Prueba de autonomía guiada: mide cuánto gasta el portátil con un uso fijo.

Se deja el portátil desenchufado unos minutos con una carga de trabajo
conocida, se mide cuánta energía ha salido de la batería y se calcula cuántas
horas daría una carga completa con ese uso. Sirve para comparar portátiles o
comprobar uno de segunda mano.
"""

from __future__ import annotations

import multiprocessing as mp
import os
import platform
import subprocess
import time

from lectores import lectura_rapida

DURACION_RECOMENDADA = 20  # minutos: bastante para que la medida sea fiable sin hacerse eterna
CARGAS = {
    "ligera": "Uso ligero: solo la pantalla encendida (recomendado)",
    "media": "Uso medio: como navegar o trabajar con documentos",
    "alta": "Uso intenso: procesador al máximo, como jugar o editar vídeo",
}


def calcular_resultado(inicio: dict, fin: dict, segundos: float,
                       cap_actual: float | None, cap_diseno: float | None) -> dict:
    """inicio/fin: {"porcentaje": %, "carga_mwh": mWh o None}."""
    if inicio.get("carga_mwh") and fin.get("carga_mwh"):
        energia = inicio["carga_mwh"] - fin["carga_mwh"]
        precision = "alta"
    elif inicio.get("porcentaje") is not None and fin.get("porcentaje") is not None and cap_actual:
        caida = inicio["porcentaje"] - fin["porcentaje"]
        energia = caida / 100 * cap_actual
        precision = "media" if caida >= 5 else "baja"
    else:
        raise ValueError("El sistema no informa de la carga de la batería.")
    if energia <= 0 or segundos <= 0:
        raise ValueError("La batería no ha bajado lo suficiente para medir. Prueba con más tiempo.")
    vatios = energia / 1000 / (segundos / 3600)
    horas = lambda mwh: round(mwh / 1000 / vatios, 2) if mwh else None  # noqa: E731
    return {"fecha": time.strftime("%Y-%m-%d %H:%M"), "minutos": round(segundos / 60),
            "vatios": round(vatios, 1), "horas_hoy": horas(cap_actual), "horas_nueva": horas(cap_diseno),
            "precision": precision}


def _trabajo(ocupacion: float, parar) -> None:
    """Proceso que ocupa la CPU una fracción del tiempo."""
    while not parar.is_set():
        fin = time.perf_counter() + 0.1 * ocupacion
        while time.perf_counter() < fin:
            pass
        time.sleep(0.1 * (1 - ocupacion))


class _SinSuspender:
    """Evita que la pantalla se apague o el equipo se suspenda durante la prueba."""

    def __enter__(self):
        self.proc = None
        so = platform.system()
        if so == "Windows":
            import ctypes
            ctypes.windll.kernel32.SetThreadExecutionState(0x80000000 | 0x00000002 | 0x00000001)
        elif so == "Darwin":
            self.proc = subprocess.Popen(["caffeinate", "-d", "-i"])
        else:
            try:
                self.proc = subprocess.Popen(["systemd-inhibit", "--what=idle:sleep", "--why=Prueba de autonomía",
                                              "sleep", "infinity"])
            except OSError:
                pass
        return self

    def __exit__(self, *_):
        if platform.system() == "Windows":
            import ctypes
            ctypes.windll.kernel32.SetThreadExecutionState(0x80000000)
        if self.proc:
            self.proc.terminate()


def _lectura() -> dict | None:
    b = lectura_rapida()
    if b is None:
        return None
    return {"porcentaje": b.porcentaje, "carga_mwh": b.carga_actual_mwh, "enchufado": b.enchufado}


def ejecutar_prueba(minutos: float, carga: str, cap_actual, cap_diseno, progreso, cancelar) -> dict:
    """Lanza la prueba (en un hilo). `progreso(segundos_restantes)`; `cancelar` es un Event."""
    inicio = _lectura()
    if inicio is None:
        raise ValueError("No se puede leer la batería de este equipo.")
    if inicio["enchufado"]:
        raise ValueError("Desenchufa el cargador antes de empezar la prueba.")

    ocupacion = {"ligera": 0, "media": 0.25, "alta": 1.0}[carga]
    nucleos = 1 if carga == "media" else max(1, (os.cpu_count() or 2) // 2)
    parar = mp.Event()
    procesos = [mp.Process(target=_trabajo, args=(ocupacion, parar), daemon=True)
                for _ in range(nucleos if ocupacion else 0)]
    total = minutos * 60
    t0 = time.monotonic()
    with _SinSuspender():
        for p in procesos:
            p.start()
        try:
            while (transcurrido := time.monotonic() - t0) < total:
                if cancelar.is_set():
                    raise ValueError("Prueba cancelada.")
                if int(transcurrido) % 30 == 0 and transcurrido > 1:
                    actual = _lectura()
                    if actual and actual["enchufado"]:
                        raise ValueError("Se ha enchufado el cargador: la prueba se ha detenido.")
                progreso(total - transcurrido)
                time.sleep(1)
        finally:
            parar.set()
            for p in procesos:
                p.join(timeout=2)
    fin = _lectura()
    return calcular_resultado(inicio, fin, time.monotonic() - t0, cap_actual, cap_diseno)
