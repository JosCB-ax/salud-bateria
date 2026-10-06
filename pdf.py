"""Exportación del análisis a PDF (reportlab)."""

from __future__ import annotations

from autonomia import calcular, horas_texto, sin_datos_texto
from informe import COLORES, _filas

AZUL = "#2f6fed"


def exportar_pdf(r: dict, ruta: str) -> None:
    from reportlab.graphics.shapes import Drawing, Line, PolyLine, String
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import cm
    from reportlab.platypus import ListFlowable, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    est = getSampleStyleSheet()
    h1, h2, p = est["Title"], est["Heading2"], est["BodyText"]
    from reportlab.lib.styles import ParagraphStyle
    grande = ParagraphStyle("grande", parent=p, leading=28, spaceBefore=6)
    tabla_estilo = TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#555555")),
        ("LINEBELOW", (0, 0), (-1, -1), 0.25, colors.HexColor("#e4e6ea")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ])
    hist = []
    ancho = A4[0] - 4 * cm

    hist.append(Paragraph("Salud de la batería", h1))
    hist.append(Paragraph(f"Informe del {r['fecha']}", p))

    for b, (nivel, diag) in zip(r["baterias"], r["diagnosticos"]):
        color = COLORES[nivel]
        salud = f"{b.salud:.0f} %" if b.salud is not None else "?"
        hist.append(Paragraph(f'<font color="{color}" size="20"><b>{salud}</b></font>'
                              f'&nbsp;&nbsp;<font color="{color}"><b>{nivel.upper()}</b></font>', grande))
        hist.append(Spacer(1, 4))
        hist.append(Paragraph(diag, p))
        filas = [[k, v] for k, v in _filas(b) if v != "—"]
        t = Table(filas, colWidths=[ancho * 0.45, ancho * 0.55])
        t.setStyle(tabla_estilo)
        hist += [Spacer(1, 6), t]

        hist.append(Paragraph("Autonomía real con la configuración de este equipo", h2))
        escenarios = calcular(b)
        if not escenarios:
            hist.append(Paragraph(sin_datos_texto(b), p))
        for e in escenarios:
            linea = f"<b>{e.titulo}</b> ({e.vatios:.1f} W): carga completa hoy {horas_texto(e.horas_hoy)}"
            if e.horas_nueva:
                linea += f", cuando era nueva {horas_texto(e.horas_nueva)}"
            hist.append(Paragraph(linea + ".", p))

        if len(b.historial) > 1:
            hist.append(Paragraph("Evolución de la salud", h2))
            alto = 150
            d = Drawing(ancho, alto)
            vals = [v for _, v in b.historial]
            y_min, y_max = min(70, int(min(vals) // 10 * 10)), 100
            x = lambda i: 30 + (ancho - 40) * i / (len(vals) - 1)  # noqa: E731
            y = lambda v: 20 + (alto - 30) * (v - y_min) / (y_max - y_min)  # noqa: E731
            for v in range(y_min, y_max + 1, 10):
                d.add(Line(30, y(v), ancho - 10, y(v), strokeColor=colors.HexColor("#eeeeee")))
                d.add(String(0, y(v) - 3, f"{v} %", fontSize=7, fillColor=colors.grey))
            d.add(Line(30, y(80), ancho - 10, y(80), strokeColor=colors.HexColor("#e6a100"),
                       strokeDashArray=[3, 2]))
            d.add(PolyLine([c for i, v in enumerate(vals) for c in (x(i), y(v))],
                           strokeColor=colors.HexColor(AZUL), strokeWidth=1.8))
            d.add(String(30, 4, b.historial[0][0], fontSize=7, fillColor=colors.grey))
            d.add(String(ancho - 10, 4, f"{b.historial[-1][0]} · {vals[-1]:.0f} %", fontSize=7,
                         fillColor=colors.grey, textAnchor="end"))
            hist.append(d)

    if r["procesos"]:
        hist.append(Paragraph("Programas que más consumían", h2))
        filas = [["Programa", "CPU", "Memoria"]] + [
            [pr.nombre, f"{pr.cpu:.1f} %", f"{pr.memoria_mb:.0f} MB"] for pr in r["procesos"]]
        t = Table(filas, colWidths=[ancho * 0.6, ancho * 0.2, ancho * 0.2])
        t.setStyle(tabla_estilo)
        hist.append(t)

    hist.append(Paragraph("Consejos", h2))
    hist.append(ListFlowable([Paragraph(c, p) for c in r["consejos"]], bulletType="1"))

    SimpleDocTemplate(ruta, pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm,
                      topMargin=1.8 * cm, bottomMargin=1.8 * cm,
                      title="Salud de la batería").build(hist)
