"""Lectura del estado real de la batería, por sistema operativo.

La salud de la batería no depende de la marca del portátil (Dell, HP, Lenovo,
Asus, Apple...), sino de lo que el firmware de la batería informa al sistema
operativo. Por eso hay un lector por sistema:

- Windows: informe de `powercfg /batteryreport` (y WMI como respaldo).
- macOS:   `ioreg -rn AppleSmartBattery` y `system_profiler SPPowerDataType`.
- Linux:   `/sys/class/power_supply/BAT*`.

Cada lector devuelve una lista de `Bateria` (algunos portátiles tienen dos).
Las funciones `parse_*` son puras para poder probarlas sin el hardware.
"""

from __future__ import annotations

import glob
import json
import os
import platform
import re
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field


@dataclass
class Bateria:
    nombre: str = "Batería"
    fabricante: str | None = None
    modelo: str | None = None
    quimica: str | None = None
    capacidad_diseno_mwh: float | None = None   # cuando era nueva
    capacidad_actual_mwh: float | None = None   # carga completa hoy
    carga_actual_mwh: float | None = None
    porcentaje: float | None = None             # nivel de carga ahora
    ciclos: int | None = None
    temperatura_c: float | None = None
    enchufado: bool | None = None
    estado: str | None = None                   # cargando / descargando / llena
    potencia_w: float | None = None             # consumo o carga instantánea
    minutos_restantes: int | None = None
    limite_carga: int | None = None             # p. ej. 80 % si está configurado
    condicion_so: str | None = None             # lo que dice el propio SO
    salud_so: float | None = None               # % que da el SO, si lo da
    unidad: str = "mWh"
    notas: list[str] = field(default_factory=list)
    historial: list[tuple[str, float]] = field(default_factory=list)  # (fecha, salud %)
    consumo_medio_w: float | None = None        # consumo medio real en batería
    horas_medidas: float | None = None          # horas de uso en que se basa esa media

    @property
    def salud(self) -> float | None:
        """Capacidad actual frente a la de fábrica, en %."""
        if self.capacidad_diseno_mwh and self.capacidad_actual_mwh:
            return round(100 * self.capacidad_actual_mwh / self.capacidad_diseno_mwh, 1)
        return self.salud_so

    @property
    def desgaste(self) -> float | None:
        s = self.salud
        return None if s is None else round(max(0.0, 100 - s), 1)


def ejecutar(cmd: list[str], timeout: int = 30) -> str:
    """Ejecuta una orden y devuelve su salida, sin abrir ventanas de consola."""
    extra = {}
    if os.name == "nt":  # en el .exe con ventana, evita que parpadee una consola
        extra["creationflags"] = subprocess.CREATE_NO_WINDOW
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout,
                             errors="replace", stdin=subprocess.DEVNULL, **extra)
        return out.stdout
    except (OSError, subprocess.SubprocessError):
        return ""




def _num(texto) -> float | None:
    if texto is None:
        return None
    m = re.search(r"-?\d+(?:\.\d+)?", str(texto))
    return float(m.group()) if m else None


# --------------------------------------------------------------------- Linux

def _leer(path: str) -> str | None:
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            return f.read().strip()
    except OSError:
        return None


def leer_linux(raiz: str = "/sys/class/power_supply") -> list[Bateria]:
    baterias = []
    for d in sorted(glob.glob(os.path.join(raiz, "*"))):
        if (_leer(os.path.join(d, "type")) or "").lower() != "battery":
            continue
        if _leer(os.path.join(d, "scope")) == "Device":  # ratón, mando...
            continue
        v = lambda n: _leer(os.path.join(d, n))  # noqa: E731
        b = Bateria(nombre=os.path.basename(d), fabricante=v("manufacturer"),
                    modelo=v("model_name"), quimica=v("technology"))
        volt_diseno = _num(v("voltage_min_design")) or _num(v("voltage_now"))
        if v("energy_full_design"):  # µWh
            b.capacidad_diseno_mwh = _num(v("energy_full_design")) / 1000
            b.capacidad_actual_mwh = (_num(v("energy_full")) or 0) / 1000 or None
            b.carga_actual_mwh = (_num(v("energy_now")) or 0) / 1000 or None
        elif v("charge_full_design"):  # µAh -> mWh usando el voltaje
            if volt_diseno:
                f = volt_diseno / 1e6 / 1000
                b.capacidad_diseno_mwh = _num(v("charge_full_design")) * f
                b.capacidad_actual_mwh = (_num(v("charge_full")) or 0) * f or None
                b.carga_actual_mwh = (_num(v("charge_now")) or 0) * f or None
            else:
                b.unidad = "mAh"
                b.capacidad_diseno_mwh = _num(v("charge_full_design")) / 1000
                b.capacidad_actual_mwh = (_num(v("charge_full")) or 0) / 1000 or None
        b.porcentaje = _num(v("capacity"))
        ciclos = _num(v("cycle_count"))
        b.ciclos = int(ciclos) if ciclos else None  # 0 suele significar "no lo informa"
        estado = (v("status") or "").lower()
        b.estado = {"charging": "cargando", "discharging": "descargando",
                    "full": "llena", "not charging": "enchufado sin cargar"}.get(estado, estado or None)
        b.enchufado = estado in ("charging", "full", "not charging")
        if v("power_now"):
            b.potencia_w = round(_num(v("power_now")) / 1e6, 2)
        elif v("current_now") and v("voltage_now"):
            b.potencia_w = round(_num(v("current_now")) * _num(v("voltage_now")) / 1e12, 2)
        temp = _num(v("temp"))
        if temp:
            b.temperatura_c = temp / 10
        limite = _num(v("charge_control_end_threshold"))
        if limite:
            b.limite_carga = int(limite)
        if b.condicion_so is None and v("health"):
            b.condicion_so = v("health")
        baterias.append(b)
    return baterias


# ------------------------------------------------------------------- Windows

def parse_battery_report_xml(xml_texto: str) -> list[Bateria]:
    """Interpreta el XML de `powercfg /batteryreport /xml`."""
    raiz = ET.fromstring(xml_texto)
    ns = re.match(r"\{(.*)\}", raiz.tag)
    p = (lambda t: f"{{{ns.group(1)}}}{t}") if ns else (lambda t: t)
    baterias = []
    for i, nodo in enumerate(raiz.iter(p("Battery")), 1):
        g = lambda t: (nodo.findtext(p(t)) or "").strip() or None  # noqa: E731
        b = Bateria(nombre=g("Id") or f"Batería {i}", fabricante=g("Manufacturer"),
                    modelo=g("Id"), quimica=g("Chemistry"))
        b.capacidad_diseno_mwh = _num(g("DesignCapacity"))
        b.capacidad_actual_mwh = _num(g("FullChargeCapacity"))
        ciclos = _num(g("CycleCount"))
        b.ciclos = int(ciclos) if ciclos else None
        baterias.append(b)
    return baterias


def _duracion_horas(texto: str | None) -> float:
    """Convierte una duración ISO 8601 (p. ej. "PT2H30M") a horas."""
    m = re.fullmatch(r"P(?:(\d+)D)?(?:T(?:(\d+)H)?(?:(\d+)M)?(?:([\d.]+)S)?)?", (texto or "").strip())
    if not m:
        return 0.0
    d, h, mi, s = (float(x) if x else 0.0 for x in m.groups())
    return d * 24 + h + mi / 60 + s / 3600


def parse_historial_xml(xml_texto: str, entradas_consumo: int = 14):
    """Historial de capacidad y consumo medio real en batería del informe de powercfg.

    Devuelve (historial, consumo_medio_w, horas_medidas). El historial es una
    lista de (fecha, salud %). El consumo sale de la energía gastada con el
    portátil desenchufado (ActiveDcEnergy) entre el tiempo de uso (ActiveDcTime)
    de los últimos periodos, así que refleja la configuración y el uso reales.
    """
    raiz = ET.fromstring(xml_texto)
    filas = []
    for el in raiz.iter():
        if not el.tag.endswith("HistoryEntry"):
            continue
        a = el.attrib
        fecha = (a.get("LocalEndDate") or a.get("EndDate") or a.get("LocalStartDate") or "")[:10]
        diseno, actual = _num(a.get("DesignCapacity")), _num(a.get("FullChargeCapacity"))
        filas.append((fecha, diseno, actual, _num(a.get("ActiveDcEnergy")) or 0,
                      _duracion_horas(a.get("ActiveDcTime"))))
    filas.sort(key=lambda f: f[0])

    historial = [(f, round(100 * act / dis, 1)) for f, dis, act, _, _ in filas if f and dis and act]

    con_uso = [(e, h) for _, _, _, e, h in filas if e > 0 and h > 0][-entradas_consumo:]
    energia = sum(e for e, _ in con_uso)
    horas = sum(h for _, h in con_uso)
    consumo = round(energia / 1000 / horas, 2) if horas >= 0.5 else None
    return historial, consumo, (round(horas, 1) if consumo else None)


def _ps_json(script: str):
    salida = ejecutar(["powershell", "-NoProfile", "-Command",
                   script + " | ConvertTo-Json -Compress"])
    try:
        datos = json.loads(salida) if salida.strip() else None
    except json.JSONDecodeError:
        return []
    if datos is None:
        return []
    return datos if isinstance(datos, list) else [datos]


def _estado_windows(baterias: list[Bateria]) -> None:
    """Carga, consumo y enchufe en este momento (WMI BatteryStatus)."""
    estado = _ps_json(r"Get-CimInstance -Namespace root\wmi -ClassName BatteryStatus "
                      "| Select RemainingCapacity,ChargeRate,DischargeRate,PowerOnline,Charging")
    if not baterias and estado:
        baterias.append(Bateria())
    for b, e in zip(baterias, estado):
        if e.get("RemainingCapacity"):
            b.carga_actual_mwh = e["RemainingCapacity"]
        rate = e.get("DischargeRate") or e.get("ChargeRate")
        if rate:
            b.potencia_w = round(rate / 1000, 2)
        b.enchufado = bool(e.get("PowerOnline"))
        b.estado = "cargando" if e.get("Charging") else ("enchufado" if b.enchufado else "descargando")


def leer_windows() -> list[Bateria]:
    baterias: list[Bateria] = []
    xml_informe = ""
    with tempfile.TemporaryDirectory() as tmp:
        ruta = os.path.join(tmp, "battery.xml")
        ejecutar(["powercfg", "/batteryreport", "/xml", "/output", ruta], timeout=60)
        if os.path.exists(ruta):
            with open(ruta, encoding="utf-8", errors="replace") as f:
                xml_informe = f.read()
            try:
                baterias = parse_battery_report_xml(xml_informe)
            except ET.ParseError:
                baterias = []

    if not baterias:  # respaldo por WMI (a veces necesita administrador)
        est = _ps_json(r"Get-CimInstance -Namespace root\wmi -ClassName BatteryStaticData "
                       "| Select DesignedCapacity,ManufactureName,DeviceName,Chemistry")
        full = _ps_json(r"Get-CimInstance -Namespace root\wmi -ClassName BatteryFullChargedCapacity "
                        "| Select FullChargedCapacity")
        cic = _ps_json(r"Get-CimInstance -Namespace root\wmi -ClassName BatteryCycleCount "
                       "| Select CycleCount")
        for i, e in enumerate(est):
            b = Bateria(nombre=e.get("DeviceName") or f"Batería {i + 1}",
                        fabricante=e.get("ManufactureName"))
            b.capacidad_diseno_mwh = e.get("DesignedCapacity")
            if i < len(full):
                b.capacidad_actual_mwh = full[i].get("FullChargedCapacity")
            if i < len(cic) and cic[i].get("CycleCount"):
                b.ciclos = int(cic[i]["CycleCount"])
            baterias.append(b)

    _estado_windows(baterias)
    if baterias and xml_informe:
        try:
            b = baterias[0]
            b.historial, b.consumo_medio_w, b.horas_medidas = parse_historial_xml(xml_informe)
        except ET.ParseError:
            pass
    return baterias


# --------------------------------------------------------------------- macOS

def parse_ioreg(texto: str) -> dict:
    """Saca pares "Clave" = valor de `ioreg -rn AppleSmartBattery`."""
    datos = {}
    for m in re.finditer(r'"(\w+)"\s*=\s*(Yes|No|-?\d+|"[^"]*")', texto):
        k, v = m.group(1), m.group(2)
        if k in datos:  # la primera aparición es la de nivel superior
            continue
        if v in ("Yes", "No"):
            datos[k] = v == "Yes"
        elif v.startswith('"'):
            datos[k] = v.strip('"')
        else:
            n = int(v)
            datos[k] = n - 2**64 if n >= 2**63 else n  # amperajes negativos
    return datos


def bateria_desde_ioreg(d: dict) -> Bateria:
    b = Bateria(nombre="Batería interna", fabricante=d.get("Manufacturer"),
                modelo=d.get("DeviceName"))
    volt = (d.get("Voltage") or 11_000) / 1000  # mV -> V, para pasar mAh a mWh
    diseno = d.get("DesignCapacity")
    # En Apple Silicon "MaxCapacity" es un %, y la cifra real está en AppleRawMaxCapacity.
    actual = d.get("AppleRawMaxCapacity") or d.get("NominalChargeCapacity")
    if not actual and (d.get("MaxCapacity") or 0) > 100:
        actual = d.get("MaxCapacity")
    if diseno:
        b.capacidad_diseno_mwh = round(diseno * volt, 0)
    if actual:
        b.capacidad_actual_mwh = round(actual * volt, 0)
    cur = d.get("AppleRawCurrentCapacity")
    if cur:
        b.carga_actual_mwh = round(cur * volt, 0)
    if d.get("CurrentCapacity") is not None and (d.get("CurrentCapacity") or 0) <= 100:
        b.porcentaje = d["CurrentCapacity"]
    elif cur and actual:
        b.porcentaje = round(100 * cur / actual)
    b.ciclos = d.get("CycleCount")
    if d.get("Temperature"):
        b.temperatura_c = round(d["Temperature"] / 100, 1)
    b.enchufado = d.get("ExternalConnected")
    b.estado = ("cargando" if d.get("IsCharging") else
                "llena" if d.get("FullyCharged") else
                "enchufado" if b.enchufado else "descargando")
    amp = d.get("InstantAmperage") or d.get("Amperage")
    if amp and d.get("Voltage"):
        b.potencia_w = round(abs(amp) * d["Voltage"] / 1e6, 2)
    t = d.get("TimeRemaining") or d.get("AvgTimeToEmpty")
    if t and t < 65535:
        b.minutos_restantes = t
    return b


def leer_macos() -> list[Bateria]:
    d = parse_ioreg(ejecutar(["ioreg", "-rn", "AppleSmartBattery"]))
    if not d:
        return []
    b = bateria_desde_ioreg(d)
    perfil = ejecutar(["system_profiler", "SPPowerDataType"])
    m = re.search(r"Condition:\s*(.+)", perfil)
    if m:
        b.condicion_so = m.group(1).strip()
    m = re.search(r"Maximum Capacity:\s*(\d+)\s*%", perfil)
    if m:
        b.salud_so = float(m.group(1))
    if "Optimized Battery Charging" in perfil or "optimizedcharging" in perfil.lower():
        b.notas.append("Carga optimizada disponible en Ajustes > Batería.")
    return [b]


# ------------------------------------------------------------------- general

def leer_baterias() -> list[Bateria]:
    so = platform.system()
    if so == "Windows":
        baterias = leer_windows()
    elif so == "Darwin":
        baterias = leer_macos()
    elif so == "Linux":
        baterias = leer_linux()
    else:
        baterias = []
    _completar_con_psutil(baterias)
    return baterias


def lectura_rapida() -> Bateria | None:
    """Solo carga, enchufe y consumo actuales, sin el informe completo (para la bandeja)."""
    so = platform.system()
    baterias: list[Bateria] = []
    if so == "Windows":
        _estado_windows(baterias)
    elif so == "Darwin":
        d = parse_ioreg(ejecutar(["ioreg", "-rn", "AppleSmartBattery"]))
        if d:
            baterias.append(bateria_desde_ioreg(d))
    elif so == "Linux":
        baterias = leer_linux()
    _completar_con_psutil(baterias)
    return baterias[0] if baterias else None


def _completar_con_psutil(baterias: list[Bateria]) -> None:
    """psutil da nivel, enchufe y tiempo restante en todos los sistemas."""
    try:
        import psutil
        s = psutil.sensors_battery()
    except Exception:  # sin psutil o sin sensor
        return
    if s is None:
        return
    if not baterias:
        baterias.append(Bateria(notas=["El sistema solo informa del nivel de carga; "
                                       "no expone la capacidad de diseño."]))
    b = baterias[0]
    if b.porcentaje is None:
        b.porcentaje = round(s.percent, 1)
    if b.enchufado is None:
        b.enchufado = s.power_plugged
    if b.minutos_restantes is None and s.secsleft not in (None, -1, -2) and s.secsleft > 0:
        b.minutos_restantes = int(s.secsleft // 60)
