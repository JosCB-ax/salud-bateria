"""Modo ahorro con un clic: plan de ahorro de energía y brillo bajo, y vuelta atrás.

Guarda cómo estaba todo antes de activarlo para dejarlo igual al desactivarlo
(a mano o automáticamente al enchufar el cargador, desde el icono de la bandeja).

- Windows: plan "Economizador" (powercfg SCHEME_MAX) y brillo por WMI.
- Linux:   perfil "power-saver" (powerprofilesctl) y brillo con brightnessctl.
- macOS:   el modo de bajo consumo pide contraseña de administrador, así que se
           abre la pantalla de ajustes de Batería para activarlo allí.
"""

from __future__ import annotations

import platform
import re

import configuracion
from lectores import _ps_json, ejecutar

BRILLO_AHORRO = 40  # %
PLAN_AHORRO = "a1841308-3541-4fab-bc81-f71556f20b4a"  # SCHEME_MAX, el "Economizador" de Windows


def activo() -> bool:
    return bool(configuracion.cargar().get("ahorro"))


def _brillo_windows() -> int | None:
    d = _ps_json(r"Get-CimInstance -Namespace root\wmi -ClassName WmiMonitorBrightness | Select CurrentBrightness")
    return d[0].get("CurrentBrightness") if d else None


def _fijar_brillo_windows(nivel: int) -> None:
    ejecutar(["powershell", "-NoProfile", "-Command",
              r"Get-CimInstance -Namespace root\wmi -ClassName WmiMonitorBrightnessMethods | "
              f"Invoke-CimMethod -MethodName WmiSetBrightness -Arguments @{{Timeout=1; Brightness={int(nivel)}}}"])


def activar() -> list[str]:
    """Activa el ahorro. Devuelve la lista de cambios hechos, para enseñárselos al usuario."""
    so = platform.system()
    antes: dict = {}
    hecho: list[str] = []
    if so == "Windows":
        m = re.search(r"([0-9a-f]{8}-[0-9a-f-]{27})", ejecutar(["powercfg", "/getactivescheme"]), re.I)
        if m:
            antes["plan"] = m.group(1)
            ejecutar(["powercfg", "/setactive", PLAN_AHORRO])
            if PLAN_AHORRO in ejecutar(["powercfg", "/getactivescheme"]).lower():
                hecho.append("Plan de energía: Economizador")
        brillo = _brillo_windows()
        if brillo is not None and brillo > BRILLO_AHORRO:
            antes["brillo"] = brillo
            _fijar_brillo_windows(BRILLO_AHORRO)
            hecho.append(f"Brillo: {brillo} % → {BRILLO_AHORRO} %")
    elif so == "Linux":
        perfil = ejecutar(["powerprofilesctl", "get"]).strip()
        if perfil:
            antes["perfil"] = perfil
            ejecutar(["powerprofilesctl", "set", "power-saver"])
            hecho.append("Perfil de energía: ahorro")
        m = re.search(r"\((\d+)%\)", ejecutar(["brightnessctl", "info"]))
        if m and int(m.group(1)) > BRILLO_AHORRO:
            antes["brillo"] = int(m.group(1))
            ejecutar(["brightnessctl", "set", f"{BRILLO_AHORRO}%"])
            hecho.append(f"Brillo: {antes['brillo']} % → {BRILLO_AHORRO} %")
    elif so == "Darwin":
        ejecutar(["open", "x-apple.systempreferences:com.apple.preference.battery"])
        hecho.append("Se han abierto los ajustes de Batería: activa allí el modo de bajo consumo.")
    cfg = configuracion.cargar()
    cfg["ahorro"] = antes or {"activo": True}
    configuracion.guardar(cfg)
    return hecho


def desactivar() -> None:
    cfg = configuracion.cargar()
    antes = cfg.get("ahorro") or {}
    so = platform.system()
    if so == "Windows":
        if antes.get("plan"):
            ejecutar(["powercfg", "/setactive", antes["plan"]])
        if antes.get("brillo") is not None:
            _fijar_brillo_windows(antes["brillo"])
    elif so == "Linux":
        if antes.get("perfil"):
            ejecutar(["powerprofilesctl", "set", antes["perfil"]])
        if antes.get("brillo") is not None:
            ejecutar(["brightnessctl", "set", f"{antes['brillo']}%"])
    cfg["ahorro"] = None
    configuracion.guardar(cfg)
