"""Comprueba si hay una versión nueva en GitHub y la instala."""

from __future__ import annotations

import json
import os
import platform
import re
import subprocess
import tempfile
import time
import urllib.request

REPO = "JosCB-ax/salud-bateria"
API = f"https://api.github.com/repos/{REPO}/releases/latest"
PAGINA = f"https://github.com/{REPO}/releases/latest"


def _tupla(version: str) -> tuple[int, ...]:
    return tuple(int(x) for x in re.findall(r"\d+", version)[:3])


def es_mas_nueva(remota: str, local: str) -> bool:
    return _tupla(remota) > _tupla(local)


def buscar(version_local: str) -> dict | None:
    """Devuelve {"version", "url_instalador", "notas"} si hay una versión nueva; si no, None."""
    try:
        peticion = urllib.request.Request(API, headers={"Accept": "application/vnd.github+json",
                                                        "User-Agent": "SaludBateria"})
        with urllib.request.urlopen(peticion, timeout=10) as r:
            datos = json.load(r)
    except (OSError, ValueError):
        return None  # sin internet o repositorio privado: no se molesta al usuario
    version = (datos.get("tag_name") or "").lstrip("v")
    if not version or not es_mas_nueva(version, version_local):
        return None
    exe = next((a["browser_download_url"] for a in datos.get("assets", [])
                if a.get("name", "").lower().endswith(".exe")), None)
    return {"version": version, "url_instalador": exe, "notas": datos.get("body") or ""}


def toca_buscar(cfg: dict, horas: float = 24) -> bool:
    return time.time() - cfg.get("ultima_busqueda", 0) > horas * 3600


def instalar(info: dict) -> bool:
    """Descarga el instalador y lo lanza. Devuelve True si hay que cerrar el programa."""
    if platform.system() != "Windows" or not info.get("url_instalador"):
        import webbrowser
        webbrowser.open(PAGINA)
        return False
    ruta = os.path.join(tempfile.gettempdir(), f"SaludBateria-Setup-{info['version']}.exe")
    urllib.request.urlretrieve(info["url_instalador"], ruta)
    subprocess.Popen([ruta, "/SILENT", "/SP-", "/CLOSEAPPLICATIONS"])
    return True
