"""Presentación del resultado: texto para la consola e informe HTML."""

from __future__ import annotations

import datetime as dt
import html
import platform

from autonomia import calcular, horas_texto, sin_datos_texto
from consejos import diagnostico

COLORES = {"excelente": "#1a9e5c", "buena": "#4caf50", "desgastada": "#e6a100",
           "mala": "#d93b3b", "desconocida": "#888"}


def _fmt(v, unidad="", dec=0):
    if v is None:
        return "—"
    return f"{v:,.{dec}f}".replace(",", ".") + (f" {unidad}" if unidad else "")


def _filas(b) -> list[tuple[str, str]]:
    return [
        ("Salud", _fmt(b.salud, "%", 1)),
        ("Desgaste", _fmt(b.desgaste, "%", 1)),
        ("Capacidad de fábrica", _fmt(b.capacidad_diseno_mwh, b.unidad)),
        ("Capacidad actual (carga completa)", _fmt(b.capacidad_actual_mwh, b.unidad)),
        ("Ciclos de carga", _fmt(b.ciclos)),
        ("Nivel de carga ahora", _fmt(b.porcentaje, "%")),
        ("Estado", b.estado or ("enchufado" if b.enchufado else "—")),
        ("Consumo / carga instantánea", _fmt(b.potencia_w, "W", 1)),
        ("Tiempo restante", f"{b.minutos_restantes // 60} h {b.minutos_restantes % 60} min"
         if b.minutos_restantes else "—"),
        ("Temperatura", _fmt(b.temperatura_c, "°C", 1)),
        ("Límite de carga", _fmt(b.limite_carga, "%") if b.limite_carga else "no configurado"),
        ("Condición según el sistema", b.condicion_so or "—"),
        ("Fabricante / modelo", " ".join(x for x in (b.fabricante, b.modelo) if x) or "—"),
        ("Química", b.quimica or "—"),
    ]


def _autonomia_lineas(b) -> list[str]:
    escenarios = calcular(b)
    if not escenarios:
        return [sin_datos_texto(b)]
    lineas = []
    for e in escenarios:
        l = f"{e.titulo} ({e.vatios:.1f} W): carga completa hoy {horas_texto(e.horas_hoy)}"
        if e.horas_nueva:
            l += f", cuando era nueva {horas_texto(e.horas_nueva)}"
        lineas.append(l + ".")
    return lineas


def _svg_historial(datos) -> str:
    if len(datos) < 2:
        return ""
    vals = [v for _, v in datos]
    y_min, y_max = min(70, int(min(vals) // 10 * 10)), 100
    pts = " ".join(f"{40 + 540 * i / (len(datos) - 1):.1f},{10 + 160 * (y_max - v) / (y_max - y_min):.1f}"
                   for i, v in enumerate(vals))
    y80 = 10 + 160 * (y_max - 80) / (y_max - y_min)
    return (f'<svg viewBox="0 0 600 200" style="width:100%;max-width:600px">'
            f'<line x1="40" x2="580" y1="{y80:.1f}" y2="{y80:.1f}" stroke="#e6a100" stroke-dasharray="4 3"/>'
            f'<text x="44" y="{y80 + 14:.1f}" font-size="11" fill="#e6a100">80 %</text>'
            f'<polyline points="{pts}" fill="none" stroke="var(--acc)" stroke-width="2.5"/>'
            f'<text x="40" y="195" font-size="11" fill="currentColor">{html.escape(datos[0][0])}</text>'
            f'<text x="580" y="195" font-size="11" text-anchor="end" fill="currentColor">'
            f'{html.escape(datos[-1][0])} · {datos[-1][1]:.0f} %</text></svg>')


def texto(r: dict) -> str:
    l = [f"=== Salud de la batería · {platform.system()} · {r['fecha']} ===", ""]
    if not r["baterias"]:
        l.append("No se ha encontrado ninguna batería (¿es un ordenador de sobremesa?).")
    for b, (nivel, diag) in zip(r["baterias"], r["diagnosticos"]):
        l.append(f"[{b.nombre}]  {nivel.upper()}: {diag}")
        for k, v in _filas(b):
            if v not in ("—",):
                l.append(f"  {k:<36}{v}")
        l.extend(f"  · {n}" for n in b.notas)
        l.append("  Autonomía real:")
        l.extend(f"    {x}" for x in _autonomia_lineas(b))
        l.append("")
    if r["ajustes"]:
        l.append("Ajustes de energía:")
        l.extend(f"  {k:<36}{v}" for k, v in r["ajustes"].items())
        l.append("")
    l.append("Programas que más consumen ahora:")
    l.append(f"  {'Programa':<30}{'CPU %':>8}{'RAM MB':>9}{'Impacto':>9}")
    for p in r["procesos"]:
        imp = _fmt(p.impacto, dec=1) if p.impacto is not None else ""
        l.append(f"  {p.nombre[:29]:<30}{p.cpu:>8.1f}{p.memoria_mb:>9.0f}{imp:>9}")
    l.append("")
    l.append("Consejos:")
    l.extend(f"  {i}. {c}" for i, c in enumerate(r["consejos"], 1))
    return "\n".join(l)


def html_informe(r: dict) -> str:
    e = html.escape
    bloques = []
    for b, (nivel, diag) in zip(r["baterias"], r["diagnosticos"]):
        salud = b.salud
        color = COLORES[nivel]
        filas = "".join(f"<tr><th>{e(k)}</th><td>{e(v)}</td></tr>" for k, v in _filas(b) if v != "—")
        notas = "".join(f"<p class='nota'>{e(n)}</p>" for n in b.notas)
        bloques.append(f"""
<section class="card">
  <div class="gauge" style="--p:{salud or 0};--c:{color}">
    <div><strong>{_fmt(salud, '%', 0) if salud is not None else '?'}</strong><span>salud</span></div>
  </div>
  <div class="resumen">
    <h2>{e(b.nombre)} <span class="tag" style="background:{color}">{e(nivel)}</span></h2>
    <p>{e(diag)}</p>
    <table>{filas}</table>{notas}
  </div>
</section>""")
    if not bloques:
        bloques.append("<section class='card'><p>No se ha encontrado ninguna batería.</p></section>")

    maxcpu = max([p.cpu for p in r["procesos"]] + [1])
    procs = "".join(
        f"<tr><td>{e(p.nombre)}<small>{' ×' + str(p.instancias) if p.instancias > 1 else ''}</small>"
        f"{'<div class=consejo>' + e(p.consejo) + '</div>' if p.consejo else ''}</td>"
        f"<td><div class=bar><i style='width:{min(100, 100 * p.cpu / maxcpu):.0f}%'></i></div>{p.cpu:.1f} %</td>"
        f"<td>{p.memoria_mb:.0f} MB</td>"
        f"<td>{_fmt(p.impacto, dec=1) if p.impacto is not None else ''}</td></tr>"
        for p in r["procesos"])
    impacto_col = any(p.impacto is not None for p in r["procesos"])
    ajustes = "".join(f"<tr><th>{e(k)}</th><td>{e(v)}</td></tr>" for k, v in r["ajustes"].items())
    autonomia = ""
    if r["baterias"]:
        b0 = r["baterias"][0]
        autonomia = ('<div class="card"><h2>Autonomía real con la configuración de este equipo</h2>'
                     + "".join(f"<p>{e(x)}</p>" for x in _autonomia_lineas(b0))
                     + (f"<h2>Evolución de la salud</h2>{_svg_historial(b0.historial)}" if len(b0.historial) > 1 else "")
                     + "</div>")
    consejos = "".join(f"<li>{e(c)}</li>" for c in r["consejos"])

    return f"""<!doctype html>
<html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Salud de la batería</title>
<style>
:root{{--bg:#f6f7f9;--card:#fff;--fg:#1d2330;--mut:#667;--line:#e4e6ea;--acc:#2f6fed}}
@media (prefers-color-scheme:dark){{:root{{--bg:#14161b;--card:#1d2027;--fg:#e8eaf0;--mut:#99a;--line:#2c3039;--acc:#6d9bff}}}}
body{{margin:0;background:var(--bg);color:var(--fg);font:15px/1.5 system-ui,-apple-system,Segoe UI,sans-serif}}
main{{max-width:900px;margin:auto;padding:24px 16px}}
h1{{margin:0 0 4px}} .sub{{color:var(--mut);margin:0 0 20px}}
.card{{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:20px;margin-bottom:16px}}
section.card{{display:flex;gap:24px;flex-wrap:wrap}}
.gauge{{width:150px;height:150px;border-radius:50%;flex:none;display:grid;place-items:center;
  background:conic-gradient(var(--c) calc(var(--p)*1%),var(--line) 0)}}
.gauge>div{{width:118px;height:118px;border-radius:50%;background:var(--card);display:grid;place-content:center;text-align:center}}
.gauge strong{{font-size:30px}} .gauge span{{color:var(--mut);font-size:13px}}
.resumen{{flex:1;min-width:250px}} h2{{margin:0 0 6px;font-size:19px}}
.tag{{color:#fff;font-size:12px;padding:2px 8px;border-radius:99px;vertical-align:middle;text-transform:uppercase}}
table{{width:100%;border-collapse:collapse}} th,td{{text-align:left;padding:6px 4px;border-top:1px solid var(--line);vertical-align:top}}
th{{color:var(--mut);font-weight:500}}
.procs td:nth-child(2){{width:30%}} .bar{{height:6px;background:var(--line);border-radius:3px;margin:6px 0 2px}}
.bar i{{display:block;height:100%;background:var(--acc);border-radius:3px}}
.consejo{{color:var(--mut);font-size:13px}} small{{color:var(--mut)}}
ol li{{margin-bottom:8px}} .nota{{color:var(--mut);font-size:13px}}
.scroll{{overflow-x:auto}}
</style></head><body><main>
<h1>Salud de la batería</h1>
<p class="sub">{e(platform.system())} · {e(platform.node())} · {e(r['fecha'])}</p>
{''.join(bloques)}
{autonomia}
<div class="card"><h2>Programas que más consumen ahora</h2>
<p class="nota">Medido durante {r['segundos']:.0f} s. CPU en % de un núcleo, sumando todas las ventanas o procesos del mismo programa.
{'"Impacto" es el impacto energético que calcula macOS.' if impacto_col else ''}</p>
<div class="scroll"><table class="procs"><tr><th>Programa</th><th>CPU</th><th>Memoria</th><th>{'Impacto' if impacto_col else ''}</th></tr>{procs}</table></div></div>
{'<div class="card"><h2>Ajustes de energía</h2><table>' + ajustes + '</table></div>' if ajustes else ''}
<div class="card"><h2>Consejos para cuidar la batería</h2><ol>{consejos}</ol></div>
<p class="nota">La salud se calcula como capacidad actual ÷ capacidad de fábrica, según lo que el firmware de la batería informa al sistema. Es igual para cualquier marca de portátil.</p>
</main></body></html>"""


def ahora() -> str:
    return dt.datetime.now().strftime("%d/%m/%Y %H:%M")
