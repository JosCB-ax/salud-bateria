"""Modo bandeja: icono junto al reloj que avisa al llegar a los límites de carga.

Se lanza con `SaludBateria.exe --bandeja` (o `python app.py --bandeja`), que es
lo que arranca el sistema al iniciar sesión si está activado. Va en un proceso
aparte de la ventana porque en macOS el icono necesita el hilo principal.
"""

from __future__ import annotations

import os
import platform
import socket
import subprocess
import sys
import threading
import time

import configuracion
from lectores import ejecutar

PUERTO_UNICO = 47231  # impide abrir dos iconos a la vez
MARGEN = 3            # puntos que hay que alejarse del límite para volver a avisar


def decidir_aviso(estado: dict, porcentaje: float, enchufado: bool, cfg: dict) -> str | None:
    """Devuelve el aviso que toca mostrar (o None). `estado` recuerda qué se ha avisado."""
    if not cfg.get("avisos", True):
        return None
    alto, bajo = cfg["umbral_alto"], cfg["umbral_bajo"]
    if enchufado and porcentaje >= alto and not estado.get("alto"):
        estado["alto"] = True
        return f"Batería al {porcentaje:.0f} %. Desenchufa el cargador para alargar su vida."
    if not enchufado and porcentaje <= bajo and not estado.get("bajo"):
        estado["bajo"] = True
        return f"Batería al {porcentaje:.0f} %. Enchufa el cargador: bajar de aquí la desgasta."
    if not enchufado or porcentaje < alto - MARGEN:
        estado["alto"] = False
    if enchufado or porcentaje > bajo + MARGEN:
        estado["bajo"] = False
    return None


def notificar(icono, mensaje: str) -> None:
    so = platform.system()
    titulo = "Salud de la batería"
    if so == "Darwin":
        texto = mensaje.replace('"', "'")
        ejecutar(["osascript", "-e", f'display notification "{texto}" with title "{titulo}"'])
    elif so == "Linux" and ejecutar(["which", "notify-send"]).strip():
        ejecutar(["notify-send", titulo, mensaje])
    else:
        icono.notify(mensaje, titulo)


def abrir_ventana() -> None:
    orden = [p for p in configuracion.orden_bandeja() if p != "--bandeja"]
    extra = {"creationflags": subprocess.CREATE_NO_WINDOW} if os.name == "nt" else {}
    subprocess.Popen(orden, **extra)


def main() -> None:
    try:
        candado = socket.socket()
        candado.bind(("127.0.0.1", PUERTO_UNICO))
    except OSError:
        return  # ya hay un icono funcionando

    import psutil
    import pystray
    from PIL import Image

    def salir(icono, _item):
        parar.set()
        icono.stop()

    icono = pystray.Icon("SaludBateria", Image.open(configuracion.recurso("icono.ico")), "Salud de la batería",
                         menu=pystray.Menu(
                             pystray.MenuItem("Abrir Salud de la batería", lambda *_: abrir_ventana(),
                                              default=True),
                             pystray.MenuItem("Salir", salir)))
    parar = threading.Event()

    def apuntar_historial(ultimo_dia: list, vuelta: int) -> None:
        """Salud una vez al día y consumo real cada 10 minutos si va con batería."""
        import historial
        from lectores import leer_baterias, lectura_rapida
        try:
            hoy = time.strftime("%Y-%m-%d")
            if ultimo_dia[0] != hoy:
                bats = leer_baterias()
                if bats:
                    historial.registrar(bats[0])
                ultimo_dia[0] = hoy
            elif vuelta % 10 == 0:
                rapida = lectura_rapida()
                if rapida and not rapida.enchufado:
                    historial.registrar(rapida)
        except Exception:  # noqa: BLE001 - el icono nunca debe caerse por esto
            pass

    def vigilar():
        estado: dict = {}
        ultimo_dia = [""]
        vuelta = 0
        while not parar.is_set():
            vuelta += 1
            apuntar_historial(ultimo_dia, vuelta)
            b = psutil.sensors_battery()
            if b is not None:
                icono.title = f"Salud de la batería · {b.percent:.0f} %" + (" · cargando" if b.power_plugged else "")
                aviso = decidir_aviso(estado, b.percent, bool(b.power_plugged), configuracion.cargar())
                if aviso:
                    notificar(icono, aviso)
            parar.wait(60)

    def al_arrancar(icono):
        icono.visible = True
        threading.Thread(target=vigilar, daemon=True).start()

    icono.run(setup=al_arrancar)
    candado.close()


if __name__ == "__main__":
    sys.exit(main())
