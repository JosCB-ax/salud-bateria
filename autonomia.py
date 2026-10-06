"""Autonomía real: cuántas horas da la batería con el consumo de este equipo.

No usa cifras del fabricante. Divide la energía que cabe hoy en la batería
entre lo que gasta este portátil de verdad, con su brillo, sus programas y su
plan de energía:

- Uso habitual: consumo medio con el portátil desenchufado en las últimas
  semanas (historial de Windows).
- Ahora mismo: consumo instantáneo medido, si está funcionando con batería.
"""

from __future__ import annotations

from dataclasses import dataclass

from lectores import Bateria


@dataclass
class Escenario:
    titulo: str
    detalle: str
    vatios: float
    horas_hoy: float            # carga completa con la capacidad actual
    horas_nueva: float | None   # carga completa cuando era nueva
    horas_carga_actual: float | None  # con la carga que tiene ahora


def calcular(b: Bateria) -> list[Escenario]:
    if not b.capacidad_actual_mwh:
        return []
    escenarios = []
    if b.consumo_medio_w and b.consumo_medio_w > 0.5:
        escenarios.append(_escenario(
            b, "Con tu uso habitual", b.consumo_medio_w,
            f"consumo medio con batería en las últimas {b.horas_medidas:.0f} h de uso"))
    if not b.enchufado and b.potencia_w and b.potencia_w > 0.5:
        escenarios.append(_escenario(
            b, "Con lo que estás haciendo ahora", b.potencia_w, "consumo medido en este momento"))
    return escenarios


def _escenario(b: Bateria, titulo: str, vatios: float, detalle: str) -> Escenario:
    h = lambda mwh: round(mwh / 1000 / vatios, 1) if mwh else None  # noqa: E731
    return Escenario(titulo, detalle, round(vatios, 1), h(b.capacidad_actual_mwh),
                     h(b.capacidad_diseno_mwh), h(b.carga_actual_mwh))


def horas_texto(h: float | None) -> str:
    if h is None:
        return "—"
    return f"{int(h)} h {round((h % 1) * 60):02d} min"


def sin_datos_texto(b: Bateria) -> str:
    if b.enchufado:
        return ("Para calcular tu autonomía real hace falta medir el consumo con batería: "
                "desenchufa el cargador unos minutos, usa el portátil como siempre y pulsa Actualizar.")
    return "El sistema no informa del consumo de la batería, así que no se puede calcular la autonomía."
