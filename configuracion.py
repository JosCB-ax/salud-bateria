"""Ajustes del usuario y arranque automático al iniciar sesión.

Los ajustes se guardan en un JSON en la carpeta de configuración del usuario.
El arranque automático usa el mecanismo propio de cada sistema:

- Windows: valor en HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run
- macOS:   ~/Library/LaunchAgents/com.saludbateria.bandeja.plist
- Linux:   ~/.config/autostart/salud-bateria.desktop
"""

from __future__ import annotations

import json
import os
import platform
import sys

POR_DEFECTO = {"avisos": True, "umbral_alto": 80, "umbral_bajo": 20}
NOMBRE_RUN = "SaludBateria"
PLIST = os.path.expanduser("~/Library/LaunchAgents/com.saludbateria.bandeja.plist")
DESKTOP = os.path.expanduser("~/.config/autostart/salud-bateria.desktop")


def carpeta() -> str:
    so = platform.system()
    if so == "Windows":
        base = os.environ.get("APPDATA") or os.path.expanduser("~")
    elif so == "Darwin":
        base = os.path.expanduser("~/Library/Application Support")
    else:
        base = os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config")
    ruta = os.path.join(base, "SaludBateria")
    os.makedirs(ruta, exist_ok=True)
    return ruta


def cargar() -> dict:
    datos = dict(POR_DEFECTO)
    try:
        with open(os.path.join(carpeta(), "config.json"), encoding="utf-8") as f:
            datos.update(json.load(f))
    except (OSError, ValueError):
        pass
    return datos


def guardar(datos: dict) -> None:
    with open(os.path.join(carpeta(), "config.json"), "w", encoding="utf-8") as f:
        json.dump(datos, f, indent=2)


def recurso(nombre: str) -> str:
    """Ruta a un archivo incluido en el programa (también dentro del .exe)."""
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, nombre)


def orden_bandeja() -> list[str]:
    """Cómo lanzar el programa en modo bandeja (vale para el .exe y para Python)."""
    if getattr(sys, "frozen", False):
        return [sys.executable, "--bandeja"]
    return [sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), "app.py"), "--bandeja"]


def arranque_activado() -> bool:
    so = platform.system()
    if so == "Windows":
        import winreg
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                r"Software\Microsoft\Windows\CurrentVersion\Run") as k:
                winreg.QueryValueEx(k, NOMBRE_RUN)
            return True
        except OSError:
            return False
    return os.path.exists(PLIST if so == "Darwin" else DESKTOP)


def fijar_arranque(activar: bool) -> None:
    so = platform.system()
    orden = orden_bandeja()
    if so == "Windows":
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run",
                            0, winreg.KEY_SET_VALUE) as k:
            if activar:
                winreg.SetValueEx(k, NOMBRE_RUN, 0, winreg.REG_SZ, " ".join(f'"{p}"' for p in orden))
            else:
                try:
                    winreg.DeleteValue(k, NOMBRE_RUN)
                except FileNotFoundError:
                    pass
        return
    ruta = PLIST if so == "Darwin" else DESKTOP
    if not activar:
        if os.path.exists(ruta):
            os.remove(ruta)
        return
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    with open(ruta, "w", encoding="utf-8") as f:
        if so == "Darwin":
            args = "".join(f"<string>{p}</string>" for p in orden)
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n'
                    '<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" '
                    '"http://www.apple.com/DTDs/PropertyList-1.0.dtd">\n'
                    '<plist version="1.0"><dict><key>Label</key><string>com.saludbateria.bandeja</string>'
                    f'<key>ProgramArguments</key><array>{args}</array>'
                    '<key>RunAtLoad</key><true/></dict></plist>\n')
        else:
            f.write("[Desktop Entry]\nType=Application\nName=Salud de la batería\n"
                    f"Exec={' '.join(f'"{p}"' if ' ' in p else p for p in orden)}\n"
                    "X-GNOME-Autostart-enabled=true\n")
