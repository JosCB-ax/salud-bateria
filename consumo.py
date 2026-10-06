"""Qué está gastando batería: procesos y ajustes del sistema.

Ningún sistema da el consumo exacto en vatios por programa sin permisos de
administrador, así que se usa lo que mejor lo aproxima en cada uno:

- Todos: uso de CPU medido durante unos segundos (psutil). La CPU es, junto
  a la pantalla, lo que más energía gasta en un portátil.
- macOS: además, el "impacto energético" que calcula el propio sistema
  (columna POWER de `top`).
"""

from __future__ import annotations

import glob
import os
import platform
import re
import time
from dataclasses import dataclass

from lectores import ejecutar

# Procesos del sistema que no tiene sentido recomendar cerrar.
SISTEMA = {
    "system idle process", "system", "idle", "kernel_task", "launchd", "windowserver",
    "registry", "memory compression", "secure system", "smss.exe", "csrss.exe",
    "wininit.exe", "services.exe", "lsass.exe", "svchost.exe", "dwm.exe",
    "systemd", "kthreadd", "init", "xorg", "gnome-shell", "kwin_x11", "kwin_wayland",
}

# Programas que suelen gastar mucho y su consejo concreto.
CONOCIDOS = {
    "chrome": "Chrome abre un proceso por pestaña: cierra pestañas o activa el Ahorro de energía en Ajustes > Rendimiento.",
    "msedge": "Edge: activa 'Eficiencia' en Configuración > Sistema y rendimiento.",
    "firefox": "Firefox: cierra pestañas que no uses; about:processes muestra cuál gasta más.",
    "teams": "Teams consume mucho en segundo plano: ciérralo del todo si no estás en reunión.",
    "zoom": "Las videollamadas gastan mucho; apaga la cámara si no la necesitas.",
    "discord": "Discord con aceleración por hardware y overlay gasta bastante; desactívalos si no juegas.",
    "spotify": "Spotify: descarga las listas y desactiva la aceleración por hardware.",
    "onedrive": "OneDrive sincronizando gasta CPU y disco; pausa la sincronización con poca batería.",
    "dropbox": "Dropbox sincronizando gasta CPU y disco; pausa la sincronización con poca batería.",
    "searchindexer": "El indexador de Windows trabaja tras instalar cosas; se calma solo al terminar.",
    "msmpeng": "El antivirus de Windows está analizando; programa los análisis con el portátil enchufado.",
    "mds_stores": "Spotlight está indexando; suele pasar tras actualizar y termina solo.",
    "photoanalysisd": "Fotos está analizando la biblioteca; mejor hacerlo enchufado.",
    "steam": "Steam en segundo plano descarga y actualiza: ciérralo si no vas a jugar.",
    "docker": "Docker mantiene una máquina virtual encendida: ciérralo si no lo usas.",
    "code": "VS Code con muchas extensiones puede gastar CPU; revisa las que no uses.",
}


@dataclass
class Proceso:
    nombre: str
    cpu: float          # % de un núcleo, sumando todos los procesos con ese nombre
    memoria_mb: float
    instancias: int
    impacto: float | None = None  # impacto energético de macOS
    consejo: str | None = None


def consejo_programa(nombre: str) -> str | None:
    n = nombre.lower()
    for clave, texto in CONOCIDOS.items():
        if clave in n:
            return texto
    return None


def procesos_que_mas_consumen(segundos: float = 3.0, top: int = 10) -> list[Proceso]:
    import psutil

    procs = list(psutil.process_iter(["name", "memory_info"]))
    for p in procs:
        try:
            p.cpu_percent(None)
        except (psutil.Error, OSError):
            pass
    time.sleep(segundos)

    agrupados: dict[str, Proceso] = {}
    for p in procs:
        try:
            cpu = p.cpu_percent(None)
            nombre = p.info["name"] or "?"
            mem = (p.info["memory_info"].rss if p.info["memory_info"] else 0) / 2**20
        except (psutil.Error, OSError):
            continue
        if nombre.lower() in SISTEMA:
            continue
        clave = re.sub(r"(\.exe)$", "", nombre, flags=re.I)
        clave = re.sub(r" Helper.*$", "", clave)  # agrupa "Chrome Helper (GPU)" con Chrome
        g = agrupados.setdefault(clave, Proceso(clave, 0.0, 0.0, 0))
        g.cpu += cpu
        g.memoria_mb += mem
        g.instancias += 1

    if platform.system() == "Darwin":
        for nombre, impacto in impacto_energetico_macos().items():
            for g in agrupados.values():
                if g.nombre.lower().startswith(nombre.lower()[:15]):
                    g.impacto = (g.impacto or 0) + impacto
                    break

    lista = sorted(agrupados.values(),
                   key=lambda g: (g.impacto or 0, g.cpu, g.memoria_mb), reverse=True)
    if not any(g.impacto for g in lista):
        lista.sort(key=lambda g: (g.cpu, g.memoria_mb), reverse=True)
    for g in lista[:top]:
        g.cpu = round(g.cpu, 1)
        g.memoria_mb = round(g.memoria_mb)
        g.consejo = consejo_programa(g.nombre)
    return lista[:top]


def parse_top_macos(texto: str) -> dict[str, float]:
    """Lee la última muestra de `top -l 2 -stats command,power`."""
    muestras = texto.split("COMMAND")
    if len(muestras) < 2:
        return {}
    resultado: dict[str, float] = {}
    for linea in muestras[-1].splitlines()[1:]:
        m = re.match(r"\s*(.+?)\s+(\d+(?:\.\d+)?)\s*$", linea)
        if m:
            resultado[m.group(1)] = resultado.get(m.group(1), 0) + float(m.group(2))
    return resultado


def impacto_energetico_macos() -> dict[str, float]:
    return parse_top_macos(ejecutar(["top", "-l", "2", "-s", "2", "-o", "power", "-n", "15",
                                     "-stats", "command,power"], timeout=20))


# ------------------------------------------------- ajustes que afectan al gasto

def _cmd(cmd: list[str]) -> str:
    return ejecutar(cmd, timeout=10).strip()


def ajustes_energia() -> dict[str, str]:
    """Ajustes del sistema que influyen en la duración de la batería."""
    so = platform.system()
    a: dict[str, str] = {}
    if so == "Windows":
        plan = _cmd(["powercfg", "/getactivescheme"])
        m = re.search(r"\((.+)\)", plan)
        if m:
            a["Plan de energía"] = m.group(1)
    elif so == "Darwin":
        pm = _cmd(["pmset", "-g"])
        m = re.search(r"lowpowermode\s+(\d)", pm)
        if m:
            a["Modo de bajo consumo"] = "activado" if m.group(1) == "1" else "desactivado"
        m = re.search(r"displaysleep\s+(\d+)", pm)
        if m:
            a["Apagar pantalla tras"] = f"{m.group(1)} min"
    elif so == "Linux":
        perfil = _cmd(["powerprofilesctl", "get"])
        if perfil:
            a["Perfil de energía"] = perfil
        for d in glob.glob("/sys/class/backlight/*"):
            try:
                actual = int(open(os.path.join(d, "brightness")).read())
                maximo = int(open(os.path.join(d, "max_brightness")).read())
                a["Brillo de pantalla"] = f"{round(100 * actual / maximo)} %"
                break
            except (OSError, ValueError, ZeroDivisionError):
                continue
        gov = glob.glob("/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor")
        if gov:
            try:
                a["Gobernador de CPU"] = open(gov[0]).read().strip()
            except OSError:
                pass
    return a
