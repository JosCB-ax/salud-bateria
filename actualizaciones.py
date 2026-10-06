"""Comprueba si hay una versión nueva en GitHub y la instala."""

from __future__ import annotations

import hashlib
import json
import os
import platform
import re
import subprocess
import tempfile
import time
import urllib.request
from urllib.parse import urlparse

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
    archivos = {a.get("name", ""): a.get("browser_download_url") for a in datos.get("assets", [])}
    exe = next((u for n, u in archivos.items() if n.lower().endswith(".exe")), None)
    return {"version": version, "url_instalador": exe, "url_sumas": archivos.get("SHA256SUMS.txt"),
            "notas": datos.get("body") or ""}


def _de_github(url: str | None) -> bool:
    """Solo se descargan cosas de las direcciones oficiales de GitHub y por HTTPS."""
    u = urlparse(url or "")
    return u.scheme == "https" and u.hostname == "github.com" and u.path.startswith(f"/{REPO}/releases/download/")


def suma_esperada(sumas: str, nombre: str) -> str | None:
    for linea in sumas.splitlines():
        partes = linea.split()
        if len(partes) == 2 and partes[1].lstrip("*") == nombre and re.fullmatch(r"[0-9a-f]{64}", partes[0]):
            return partes[0]
    return None


def toca_buscar(cfg: dict, horas: float = 24) -> bool:
    return time.time() - cfg.get("ultima_busqueda", 0) > horas * 3600


def instalar(info: dict) -> bool:
    """Descarga el instalador y lo lanza. Devuelve True si hay que cerrar el programa."""
    url, url_sumas = info.get("url_instalador"), info.get("url_sumas")
    if platform.system() != "Windows" or not (_de_github(url) and _de_github(url_sumas)):
        import webbrowser
        webbrowser.open(PAGINA)
        return False
    with urllib.request.urlopen(url_sumas, timeout=30) as r:
        esperada = suma_esperada(r.read().decode("utf-8", "replace"), url.rsplit("/", 1)[-1])
    # carpeta nueva y privada: nadie puede dejar ahí otro archivo con el mismo nombre
    ruta = os.path.join(tempfile.mkdtemp(prefix="SaludBateria-"), url.rsplit("/", 1)[-1])
    urllib.request.urlretrieve(url, ruta)
    with open(ruta, "rb") as f:
        real = hashlib.sha256(f.read()).hexdigest()
    if not esperada or real != esperada:
        os.remove(ruta)  # descarga dañada o manipulada: no se ejecuta
        raise ValueError("El instalador descargado no coincide con el publicado. No se ha instalado nada.")
    subprocess.Popen([ruta, "/SILENT", "/SP-", "/CLOSEAPPLICATIONS"])
    return True
