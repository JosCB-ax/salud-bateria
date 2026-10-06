"""Predicción del desgaste: cuándo llegará la batería al 80 % y al 60 % al ritmo actual."""

from __future__ import annotations

import datetime as dt

DIAS_MINIMOS = 30   # con menos historial el ritmo no es fiable
DIAS_VENTANA = 365  # se usa el último año, que refleja el uso actual
UMBRALES = (80, 60)


def ritmo_anual(historial: list[tuple[str, float]], hoy: dt.date | None = None) -> float | None:
    """Puntos de salud que pierde al año (regresión lineal del último año), o None."""
    puntos = []
    for fecha, salud in historial:
        try:
            puntos.append((dt.date.fromisoformat(fecha[:10]), salud))
        except ValueError:
            continue
    if not puntos:
        return None
    hoy = hoy or max(d for d, _ in puntos)
    puntos = [(d, s) for d, s in puntos if (hoy - d).days <= DIAS_VENTANA]
    if len(puntos) < 2 or (max(d for d, _ in puntos) - min(d for d, _ in puntos)).days < DIAS_MINIMOS:
        return None
    xs = [d.toordinal() for d, _ in puntos]
    ys = [s for _, s in puntos]
    mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
    var = sum((x - mx) ** 2 for x in xs)
    if not var:
        return None
    pendiente = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / var  # puntos por día
    return round(-pendiente * 365, 1)


def predecir(salud_actual: float | None, historial, hoy: dt.date | None = None) -> dict | None:
    """{"ritmo": puntos/año, "meses": {80: m, 60: m}} (meses None si ya se ha pasado)."""
    ritmo = ritmo_anual(historial, hoy)
    if salud_actual is None or ritmo is None:
        return None
    meses = {}
    for u in UMBRALES:
        if salud_actual <= u:
            meses[u] = None
        elif ritmo <= 0.1:
            meses[u] = float("inf")
        else:
            meses[u] = round((salud_actual - u) / ritmo * 12)
    return {"ritmo": ritmo, "meses": meses}


def _plazo(meses: float) -> str:
    if meses == float("inf"):
        return "no se prevé con el ritmo actual"
    if meses < 1:
        return "en menos de un mes"
    if meses < 2:
        return "en un mes aproximadamente"
    if meses < 24:
        return f"en unos {int(meses)} meses"
    return f"en unos {meses / 12:.1f} años".replace(".", ",")


def texto(pred: dict | None) -> str:
    if not pred:
        return ("Aún no hay historial suficiente para predecir el desgaste "
                f"(hace falta al menos {DIAS_MINIMOS} días de datos).")
    partes = [f"Pierde {pred['ritmo']:.1f} puntos de salud al año.".replace(".", ",", 1)]
    for u, m in pred["meses"].items():
        if m is None:
            partes.append(f"Ya está por debajo del {u} %.")
        else:
            partes.append(f"Llegará al {u} % {_plazo(m)}.")
    return " ".join(partes)
