"""Diagnóstico y consejos a partir de lo que se ha medido."""

from __future__ import annotations

import platform
import re

from consumo import Proceso
from lectores import Bateria

# Las baterías de iones de litio de portátil suelen estar pensadas para
# 300-1000 ciclos hasta bajar al 80 %. Se usa 500 como referencia prudente.
CICLOS_REFERENCIA = 500


def diagnostico(b: Bateria) -> tuple[str, str]:
    """Devuelve (nivel, texto). Nivel: excelente, buena, desgastada, mala, desconocida."""
    s = b.salud
    if s is None:
        return "desconocida", ("El sistema no informa de la capacidad de fábrica de esta batería, "
                               "así que no se puede calcular su salud exacta.")
    if s >= 90:
        return "excelente", f"La batería conserva el {s:.0f} % de su capacidad original. Está como nueva."
    if s >= 80:
        return "buena", f"Conserva el {s:.0f} % de su capacidad original. Desgaste normal."
    if s >= 60:
        return "desgastada", (f"Conserva el {s:.0f} % de su capacidad original. Notarás menos autonomía; "
                              "aún no hace falta cambiarla.")
    return "mala", (f"Solo conserva el {s:.0f} % de su capacidad original. "
                    "Conviene plantearse cambiarla.")


def consejos(b: Bateria, procesos: list[Proceso], ajustes: dict[str, str]) -> list[str]:
    so = platform.system()
    c: list[str] = []
    s = b.salud

    # --- estado de la batería
    if s is not None and s < 60:
        c.append("La batería está muy desgastada: un recambio original o certificado te devolverá la autonomía. "
                 "Si se hincha (la carcasa o el touchpad se levantan), deja de usarla y cámbiala ya.")
    if b.ciclos:
        if b.ciclos > CICLOS_REFERENCIA and s is not None and s >= 80:
            c.append(f"Lleva {b.ciclos} ciclos y sigue por encima del 80 %: la estás cuidando bien.")
        elif s is not None and b.ciclos < 150 and s < 85:
            c.append(f"Solo {b.ciclos} ciclos pero ya un {100 - s:.0f} % de desgaste: suele deberse al calor "
                     "o a pasar mucho tiempo al 100 %. Revisa los consejos de carga.")
    if b.temperatura_c is not None:
        if b.temperatura_c >= 40:
            c.append(f"La batería está a {b.temperatura_c:.0f} °C. Por encima de 35-40 °C se desgasta mucho más rápido: "
                     "no tapes las rejillas, úsalo sobre una superficie dura y limpia el polvo de los ventiladores.")
        elif b.temperatura_c >= 35:
            c.append(f"Temperatura algo alta ({b.temperatura_c:.0f} °C). Evita usarlo sobre la cama o las piernas.")

    # --- hábitos de carga
    if b.enchufado and (b.porcentaje or 0) >= 95 and not b.limite_carga:
        c.append("Está enchufado y al 100 %. Si casi siempre lo usas conectado, limita la carga al 80 %: "
                 "es lo que más alarga la vida de la batería. " + _como_limitar(so))
    elif not b.limite_carga:
        c.append("Mantener la carga entre el 20 % y el 80 % alarga mucho la vida de la batería. "
                 + _como_limitar(so))
    if b.limite_carga:
        c.append(f"Tienes la carga limitada al {b.limite_carga} %. Perfecto para alargar su vida.")
    if b.porcentaje is not None and b.porcentaje <= 15 and not b.enchufado:
        c.append("Queda poca carga. Evita llegar a 0 % a menudo: las descargas completas desgastan la batería.")

    # --- ajustes del sistema
    for clave, valor in ajustes.items():
        v = valor.lower()
        if "alto rendimiento" in v or "high performance" in v or "máximo rendimiento" in v or v == "performance":
            c.append(f"{clave}: '{valor}'. Cámbialo a equilibrado o ahorro cuando no estés enchufado.")
        if clave == "Modo de bajo consumo" and v == "desactivado" and not b.enchufado:
            c.append("Activa el modo de bajo consumo cuando vayas con batería (Ajustes > Batería).")
        if clave == "Brillo de pantalla":
            n = re.search(r"\d+", valor)
            if n and int(n.group()) > 75:
                c.append(f"Brillo al {valor}. La pantalla es lo que más gasta: bajarlo al 50 % "
                         "puede darte una hora más de autonomía.")

    # --- procesos
    pesados = [p for p in procesos if p.cpu >= 20 or (p.impacto or 0) >= 20]
    if pesados:
        nombres = ", ".join(p.nombre for p in pesados[:3])
        c.append(f"Ahora mismo {nombres} está usando mucha CPU. Ciérralo si no lo necesitas.")
    for p in procesos[:5]:
        if p.consejo and p.consejo not in c:
            c.append(p.consejo)

    # --- generales
    c.append("No dejes el portátil guardado mucho tiempo al 100 % ni al 0 %: para guardarlo, déjalo al 50 %.")
    c.append("Usa el cargador original o uno certificado con la potencia correcta.")
    return c


def _como_limitar(so: str) -> str:
    if so == "Darwin":
        return "En Mac: Ajustes > Batería > Carga optimizada (o 'Límite de carga' en los modelos que lo tienen)."
    if so == "Windows":
        return ("En Windows se hace con la app del fabricante: Lenovo Vantage (Conservación de batería), "
                "MyASUS (Cuidado de batería), Dell Power Manager, HP (BIOS > Battery Care), "
                "MSI Center o Samsung Settings.")
    return ("En Linux, si existe /sys/class/power_supply/BAT0/charge_control_end_threshold, "
            "escribe 80 en él (o usa TLP); GNOME y KDE lo ofrecen en Ajustes > Energía.")
