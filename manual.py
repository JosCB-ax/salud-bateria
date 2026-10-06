"""Manual de usuario: el contenido y su versión en PDF con índice que se puede pulsar.

El mismo contenido se muestra en la pestaña «Manual» del programa y se publica en
PDF junto a las descargas (python manual.py <ruta.pdf>).
"""

from __future__ import annotations

import os
import sys

import legal

# Cada sección: (id, título, bloques). Un bloque es un párrafo (str), una lista
# de viñetas (list) o un subtítulo (("sub", texto)).
SECCIONES = [
    ("inicio", "1. Qué es Salud de la batería", [
        "Salud de la batería es un programa gratuito para portátiles que te dice cuánto se ha desgastado tu "
        "batería, cuánto te dura de verdad con tu forma de usar el equipo, qué programas gastan más y qué "
        "puedes hacer para que la batería dure más años.",
        "Funciona con cualquier marca (HP, Lenovo, Dell, ASUS, Acer, Apple, MSI…), porque no depende del "
        "fabricante: lee los datos que la propia batería entrega al sistema operativo.",
        ["Windows 10 y 11 (64 bits).",
         "macOS 11 o posterior, tanto en Mac con chip Apple (M1, M2, M3…) como con procesador Intel.",
         "Linux de 64 bits reciente: Ubuntu 22.04 o posterior, Debian 12, Fedora, Linux Mint 21 y similares."],
        "Todo se calcula en tu equipo. El programa no envía tus datos a ningún sitio y no necesita cuenta.",
    ]),
    ("descarga", "2. Descargar el programa", [
        f"Las descargas están en la página oficial: {legal.WEB}/releases/latest",
        "En el apartado «Assets» elige el archivo de tu sistema:",
        ["Windows: SaludBateria-Setup-<versión>.exe",
         "Mac con chip Apple: SaludBateria-<versión>-macOS-Apple.dmg",
         "Mac con Intel: SaludBateria-<versión>-macOS-Intel.dmg",
         "Linux: SaludBateria-<versión>-Linux.tar.gz",
         "Este manual: Manual-Salud-de-la-bateria-<versión>.pdf"],
        "Para saber qué Mac tienes, abre el menú Apple › Acerca de este Mac. Si pone «Chip Apple M…», es Apple; "
        "si pone «Procesador … Intel», es Intel.",
        "El archivo SHA256SUMS.txt contiene la huella de cada descarga. El programa la usa para comprobar que "
        "las actualizaciones no se han dañado ni manipulado; no hace falta que la descargues.",
    ]),
    ("windows", "3. Instalar en Windows", [
        ["Abre el archivo SaludBateria-Setup-<versión>.exe que has descargado.",
         "Windows puede mostrar «Windows protegió su PC», porque el programa es nuevo y no está firmado por "
         "una empresa. Pulsa «Más información» y después «Ejecutar de todas formas».",
         "Elige si quieres instalarlo para todos los usuarios del equipo (pide permiso de administrador) o "
         "solo para ti.",
         "Lee y acepta la licencia de uso.",
         "Marca, si quieres, «Iniciar con el ordenador»: así el icono de la bandeja te avisará de la carga "
         "aunque no abras la ventana. Se puede cambiar después en Ajustes.",
         "Pulsa «Instalar» y, al terminar, «Finalizar». El programa queda en el menú Inicio como "
         "«Salud de la batería»."],
        ("sub", "Actualizar"),
        "Las versiones nuevas se instalan encima de la anterior, sin desinstalar y sin perder tus ajustes ni "
        "tu historial. El propio programa avisa cuando hay una versión nueva (ver «Actualizaciones»).",
        ("sub", "Desinstalar"),
        "Configuración › Aplicaciones › Aplicaciones instaladas › Salud de la batería › Desinstalar. Tus ajustes "
        "e historial quedan en %APPDATA%\\SaludBateria; borra esa carpeta si no vas a volver a usarlo.",
    ]),
    ("macos", "4. Instalar en macOS", [
        ["Abre el archivo .dmg que corresponde a tu Mac (Apple o Intel).",
         "Arrastra el icono SaludBateria a la carpeta «Aplicaciones» que aparece al lado.",
         "Abre el programa desde Aplicaciones o Launchpad.",
         "La primera vez, macOS dirá que no puede comprobar el desarrollador, porque el programa no está "
         "firmado por Apple. Ve a Ajustes del Sistema › Privacidad y seguridad y, abajo, pulsa "
         "«Abrir igualmente». En versiones anteriores a macOS 15 también vale con hacer clic derecho sobre "
         "el programa › Abrir › Abrir.",
         "A partir de ahí se abre con normalidad."],
        ("sub", "Actualizar"),
        "Descarga el .dmg nuevo y arrastra el programa a Aplicaciones otra vez, eligiendo «Reemplazar». "
        "Tus ajustes y tu historial se conservan.",
        ("sub", "Desinstalar"),
        "Arrastra SaludBateria de Aplicaciones a la Papelera. Los datos están en "
        "~/Library/Application Support/SaludBateria; si activaste el inicio automático, desactívalo antes "
        "en Ajustes (o borra ~/Library/LaunchAgents/com.saludbateria.bandeja.plist).",
    ]),
    ("linux", "5. Instalar en Linux", [
        ["Descomprime SaludBateria-<versión>-Linux.tar.gz (doble clic en la mayoría de escritorios, o "
         "«tar xzf SaludBateria-<versión>-Linux.tar.gz» en una terminal).",
         "Entra en la carpeta y ejecuta «./instalar-linux.sh». No hace falta ser administrador: se instala "
         "solo para tu usuario, en ~/.local/share/SaludBateria.",
         "Búscalo en el menú de aplicaciones como «Salud de la batería». También se puede abrir con la orden "
         "«salud-bateria» si ~/.local/bin está en tu PATH."],
        ("sub", "Actualizar"),
        "Descarga el .tar.gz nuevo y vuelve a ejecutar «./instalar-linux.sh»: reemplaza la versión anterior y "
        "conserva tus datos.",
        ("sub", "Desinstalar"),
        "Ejecuta «./desinstalar-linux.sh» desde la carpeta descomprimida. Los datos están en "
        "~/.config/SaludBateria.",
        ("sub", "Notas"),
        ["Los avisos se muestran como notificaciones del escritorio (necesita notify-send, que viene en casi "
         "todas las distribuciones).",
         "En GNOME el icono junto al reloj solo se ve si tienes una extensión de bandeja del sistema; los "
         "avisos funcionan igualmente.",
         "El modo ahorro usa powerprofilesctl y brightnessctl si están instalados."],
    ]),
    ("ventana", "6. La ventana principal", [
        "Al abrir el programa analiza la batería durante unos segundos. Arriba verás:",
        ["El círculo de salud: el porcentaje de capacidad que conserva la batería respecto a cuando era nueva, "
         "con un color según su estado (verde, amarillo, naranja o rojo).",
         "El diagnóstico: excelente (90 % o más), buena (80–90 %), desgastada (60–80 %) o mala (menos del 60 %), "
         "con una frase que lo explica.",
         "La hora del último análisis."],
        "Debajo hay cinco pestañas (Batería, Autonomía e historial, Qué consume más, Consejos y Manual) y, abajo "
        "del todo, la barra de botones. La última línea muestra el aviso de autoría.",
        "Si el equipo no tiene batería (un ordenador de sobremesa), el programa lo indica y sigue mostrando "
        "qué programas consumen más.",
    ]),
    ("bateria", "7. Pestaña «Batería»", [
        "Una tabla con todos los datos que el sistema da sobre la batería. Según el equipo, algunos pueden "
        "no aparecer:",
        ["Salud y desgaste: capacidad actual ÷ capacidad de fábrica, y lo que se ha perdido.",
         "Capacidad de fábrica y capacidad actual (carga completa), en Wh.",
         "Ciclos de carga: cuántas veces se ha usado el equivalente a una carga completa.",
         "Nivel de carga ahora y estado (cargando, descargando, enchufado).",
         "Consumo o carga instantánea, en vatios, y tiempo restante.",
         "Temperatura (Windows casi nunca la da; macOS y Linux sí suelen).",
         "Límite de carga, si el fabricante lo tiene activado.",
         "Condición según el sistema, fabricante, modelo y química (normalmente ion de litio)."],
        ("sub", "Calibrar la batería…"),
        "Con el tiempo, el chip que mide la batería se desajusta y puede marcar menos salud de la real. La "
        "calibración no repara la batería: solo corrige esa medida. El asistente apunta la salud de antes, te "
        "guía en cuatro pasos (cargar al 100 %, gastar hasta que se apague, dejarlo apagado unas horas y volver "
        "a cargar al 100 %) y, al pulsar «He terminado: comparar», te dice si la lectura ha cambiado. Hazla "
        "como mucho cada 2 o 3 meses, porque una descarga completa también desgasta.",
    ]),
    ("autonomia", "8. Pestaña «Autonomía e historial»", [
        ("sub", "Autonomía real"),
        "En lugar de la autonomía de catálogo, el programa calcula cuánto te dura con tu equipo y tu forma de "
        "usarlo:",
        ["Con tu uso habitual: usa el consumo medio de las últimas horas que has usado el portátil con batería "
         "(en Windows, del propio registro del sistema; en todos los sistemas, también de las mediciones que "
         "va guardando el programa).",
         "Con lo que estás haciendo ahora: usa el consumo de este momento, si estás sin cargador."],
        "Para cada caso muestra cuánto dura una carga completa hoy, cuánto duraba cuando la batería era nueva y "
        "cuánto queda con la carga actual. Si estás enchufado y aún no hay mediciones, te pide que desenchufes "
        "unos minutos y pulses «Actualizar».",
        ("sub", "Evolución de la salud"),
        "Una gráfica con la salud de cada día y una línea en el 80 %, que es el límite habitual de desgaste "
        "normal. Con al menos 30 días de datos, el programa calcula a qué ritmo se desgasta tu batería al año y "
        "predice cuándo llegará al 80 % y al 60 %. Cuantos más días use el programa (o el icono de la bandeja), "
        "más fiable es la predicción.",
    ]),
    ("consumo", "9. Pestaña «Qué consume más»", [
        "Lista de los programas que más procesador y memoria usan durante unos segundos de medición, sumando "
        "todas las ventanas o procesos del mismo programa. En macOS también aparece el «impacto energético» "
        "que calcula el sistema.",
        "Selecciona un programa para ver un consejo concreto para reducir su consumo (por ejemplo, en "
        "navegadores, cerrar pestañas o activar el ahorro de memoria).",
        ("sub", "Medir consumo exacto (24 h)… (solo Windows)"),
        "Lee el registro de energía que Windows guarda por aplicación y muestra qué programas han gastado más "
        "batería en las últimas 24 horas. Windows pedirá permiso de administrador, porque ese registro está "
        "protegido.",
        ("sub", "Ajustes de energía"),
        "Muestra los ajustes del sistema que más influyen en la batería: plan o modo de energía, brillo y "
        "otros según el sistema.",
        ("sub", "Modo ahorro"),
        "Con un clic baja el consumo: en Windows activa el plan de máximo ahorro y baja el brillo al 40 %; en "
        "Linux activa el perfil «power-saver» y baja el brillo; en macOS abre los ajustes de batería para que "
        "actives el modo de bajo consumo (macOS pide la contraseña de administrador para hacerlo). Al pulsar "
        "«Desactivar modo ahorro», o al enchufar el cargador, todo vuelve a como estaba.",
    ]),
    ("consejos", "10. Pestaña «Consejos»", [
        "Consejos personalizados según el estado de tu batería, su temperatura, si estás siempre enchufado, los "
        "programas que más consumen y tus ajustes de energía. Incluye cómo activar el límite de carga en tu "
        "sistema o con la aplicación de tu fabricante (Lenovo Vantage, MyASUS, Dell Power Manager, HP…), que es "
        "lo que más alarga la vida de la batería si trabajas enchufado.",
    ]),
    ("manual", "11. Pestaña «Manual»", [
        "Muestra este mismo manual dentro del programa, con el índice al principio: pulsa un apartado para ir "
        "directamente a él. El botón «Abrir el manual en PDF» abre la versión en PDF con el visor de tu "
        "sistema, para leerla, imprimirla o guardarla.",
    ]),
    ("botones", "12. Botones de la barra inferior", [
        ["Actualizar: vuelve a analizar la batería y a medir el consumo.",
         "Exportar PDF…: guarda un informe completo en PDF (salud, datos, autonomía, gráfica, programas y "
         "consejos). Útil para enviarlo al servicio técnico o comprobar el estado antes de comprar un portátil "
         "de segunda mano.",
         "Guardar informe…: lo mismo en formato web (HTML), que se abre en el navegador.",
         "Prueba de autonomía…: ver el apartado siguiente.",
         "Acerca de: versión, autoría y opción de buscar actualizaciones.",
         "Ajustes: ver «Ajustes»."],
        "Los informes incluyen el nombre del equipo y los programas que estaban abiertos; tú decides con quién "
        "los compartes.",
    ]),
    ("prueba", "13. Prueba de autonomía guiada", [
        "Mide de forma real cuánto dura tu batería. Durante la prueba el portátil no se suspende y el "
        "programa gasta batería al ritmo que elijas:",
        ["Duración: 20 minutos recomendados (puedes elegir otra). Más tiempo da un resultado más preciso.",
         "Tipo de uso: ligero (solo la pantalla encendida, recomendado), medio (como navegar o trabajar con "
         "documentos) o intenso (procesador al máximo, como jugar o editar vídeo)."],
        "Desenchufa el cargador, pulsa «Empezar» y no toques el portátil hasta que termine. Al final verás el "
        "consumo medio en vatios, la autonomía estimada con una carga completa (hoy y con la batería nueva) y "
        "la precisión de la medida. El resultado se guarda en el historial. Puedes cancelar en cualquier "
        "momento.",
    ]),
    ("bandeja", "14. Icono de la bandeja y avisos", [
        "Junto al reloj aparece un pequeño icono que vigila la batería aunque la ventana esté cerrada. Pasando "
        "el ratón por encima ves el porcentaje; con un clic o desde su menú («Abrir Salud de la batería») abres la ventana.",
        ["Aviso para desenchufar al llegar al 80 % (o al valor que elijas).",
         "Aviso para enchufar al bajar del 20 % (o al valor que elijas).",
         "Aviso de temperatura si la batería pasa de 40 °C (si el sistema da la temperatura).",
         "Una vez al día apunta la salud de la batería y, cuando vas sin cargador, mide el consumo para la "
         "autonomía real y la gráfica."],
        "Mantener la batería entre el 20 % y el 80 % es lo que más reduce su desgaste.",
    ]),
    ("ajustes", "15. Ajustes", [
        ("sub", "Avisos de carga"),
        ["Avisarme desde la bandeja del sistema: activa o desactiva los avisos.",
         "Avisar para desenchufar al llegar a: 80 % recomendado.",
         "Avisar para enchufar al bajar de: 20 % recomendado.",
         "Restaurar recomendados: vuelve a 80 %, 20 % y 40 °C.",
         "Iniciar con el ordenador: arranca solo el icono de la bandeja al encender, sin abrir la ventana.",
         "Avisar si la batería pasa de: 40 °C recomendado."],
        ("sub", "Aspecto y actualizaciones"),
        ["Tema: automático (como el sistema), claro u oscuro.",
         "Idioma: español o inglés.",
         "Buscar versiones nuevas al abrir el programa."],
        ("sub", "Información legal"),
        "Política de privacidad, términos de uso, y fuentes de información y cookies. Pulsa «Guardar» para "
        "aplicar los cambios.",
    ]),
    ("actualizaciones", "16. Actualizaciones", [
        "Si está activado en Ajustes, una vez al día el programa pregunta a GitHub si hay una versión nueva. "
        "En Windows te ofrece descargarla e instalarla en un clic: comprueba la huella SHA-256 del instalador "
        "antes de ejecutarlo y, si no coincide, no instala nada. En macOS y Linux abre la página de descargas "
        "para que bajes la nueva versión. También puedes buscar a mano desde «Acerca de».",
    ]),
    ("privacidad", "17. Privacidad y datos", [
        ["No hay cuentas, publicidad, cookies ni estadísticas de uso.",
         "Tus datos (ajustes e historial) se guardan solo en tu equipo, en la carpeta SaludBateria de tu "
         "usuario.",
         "La única conexión a internet es la búsqueda de actualizaciones, que puedes desactivar."],
        "Los textos completos están en Ajustes › Información legal.",
    ]),
    ("problemas", "18. Problemas frecuentes", [
        ("sub", "No aparece la salud o sale «desconocida»"),
        "Algunas baterías no informan de su capacidad de fábrica. El resto de datos y funciones siguen "
        "disponibles.",
        ("sub", "La salud parece demasiado baja o cambia mucho"),
        "Puede que el medidor de la batería esté desajustado. Usa el asistente «Calibrar la batería…».",
        ("sub", "No aparece la autonomía real"),
        "Hace falta medir el consumo con batería: desenchufa el cargador unos minutos, usa el portátil como "
        "siempre y pulsa «Actualizar».",
        ("sub", "No veo el icono junto al reloj"),
        "En Windows puede estar oculto en la flecha «^» de la barra de tareas; arrástralo fuera para dejarlo "
        "siempre visible. En Linux con GNOME necesitas una extensión de bandeja del sistema.",
        ("sub", "Windows o macOS no dejan abrir el programa"),
        "Es el aviso para programas no firmados. Sigue los pasos de los apartados de instalación.",
        ("sub", "No encuentra la batería"),
        "Comprueba que la batería está bien conectada y que el sistema la muestra (por ejemplo, el icono de "
        "batería del sistema). En máquinas virtuales no suele haber batería.",
    ]),
    ("autor", "19. Autoría y licencia", [
        f"{legal.copyright()} Uso gratuito; no se permite venderlo, distribuir copias modificadas ni quitar los "
        f"avisos de autoría. Para compartirlo, comparte el enlace oficial: {legal.WEB}",
        legal.aviso_ia() + " El programa no usa inteligencia artificial mientras funciona.",
        f"Dudas y sugerencias: {legal.WEB}/issues",
    ]),
]


def texto_plano() -> list[tuple[str, str, str]]:
    """Para la pestaña Manual: [(id, título, cuerpo)]."""
    salida = []
    for clave, titulo, bloques in SECCIONES:
        partes = []
        for b in bloques:
            if isinstance(b, list):
                partes.append("\n".join(f"  •  {x}" for x in b))
            elif isinstance(b, tuple):
                partes.append(f"▸ {b[1]}")
            else:
                partes.append(b)
        salida.append((clave, titulo, "\n\n".join(partes)))
    return salida


def generar_pdf(ruta: str, version: str = "") -> None:
    from xml.sax.saxutils import escape

    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import cm
    from reportlab.platypus import (ListFlowable, ListItem, PageBreak, Paragraph, SimpleDocTemplate, Spacer)
    from reportlab.platypus.tableofcontents import TableOfContents

    est = getSampleStyleSheet()
    azul = colors.HexColor("#2f6fed")
    portada = ParagraphStyle("portada", parent=est["Title"], fontSize=30, leading=36, spaceAfter=12)
    sub = ParagraphStyle("sub", parent=est["Normal"], fontSize=13, leading=18, textColor=colors.HexColor("#555555"))
    h1 = ParagraphStyle("h1", parent=est["Heading1"], textColor=azul, spaceAfter=10)
    h3 = ParagraphStyle("h3", parent=est["Heading3"], spaceBefore=10)
    p = ParagraphStyle("p", parent=est["BodyText"], fontSize=10.5, leading=15, spaceAfter=6)

    class Doc(SimpleDocTemplate):
        def afterFlowable(self, f):
            clave = getattr(f, "_clave", None)
            if clave:
                self.canv.bookmarkPage(clave)
                self.canv.addOutlineEntry(f.getPlainText(), clave, level=0)
                self.notify("TOCEntry", (0, f.getPlainText(), self.page, clave))

    def pie(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.grey)
        canvas.drawString(2 * cm, 1.2 * cm, legal.pie())
        canvas.drawRightString(A4[0] - 2 * cm, 1.2 * cm, str(doc.page))
        canvas.restoreState()

    hist = [Spacer(1, 5 * cm), Paragraph("Salud de la batería", portada),
            Paragraph("Manual de usuario" + (f" · versión {escape(version)}" if version else ""), sub),
            Spacer(1, 0.4 * cm),
            Paragraph("Instalación en Windows, macOS y Linux, y explicación de cada función.", sub),
            Spacer(1, 6 * cm), Paragraph(escape(legal.copyright()), p), Paragraph(escape(legal.WEB), p),
            PageBreak(), Paragraph("Índice", h1),
            Paragraph("Pulsa cualquier apartado para ir a su página.", p)]
    indice = TableOfContents()
    indice.levelStyles = [ParagraphStyle("toc", parent=p, fontSize=11, leading=16, textColor=azul)]
    hist.append(indice)

    for clave, titulo, bloques in SECCIONES:
        hist.append(PageBreak())
        cab = Paragraph(escape(titulo), h1)
        cab._clave = clave
        hist.append(cab)
        for b in bloques:
            if isinstance(b, list):
                hist.append(ListFlowable([ListItem(Paragraph(escape(x), p), leftIndent=14) for x in b],
                                         bulletType="bullet", start="•", leftIndent=14))
                hist.append(Spacer(1, 4))
            elif isinstance(b, tuple):
                hist.append(Paragraph(escape(b[1]), h3))
            else:
                hist.append(Paragraph(escape(b), p))

    doc = Doc(ruta, pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm, topMargin=2 * cm, bottomMargin=2 * cm,
              title="Salud de la batería · Manual de usuario", author=legal.AUTOR)
    doc.multiBuild(hist, onLaterPages=pie)


def ruta_local(version: str) -> str:
    """Genera (una vez por versión) el PDF en la carpeta del usuario y devuelve su ruta."""
    import configuracion
    ruta = os.path.join(configuracion.carpeta(), f"Manual-Salud-de-la-bateria-{version}.pdf")
    if not os.path.exists(ruta):
        generar_pdf(ruta, version)
    return ruta


def abrir_archivo(ruta: str) -> None:
    import platform
    import subprocess
    if platform.system() == "Windows":
        os.startfile(ruta)  # noqa: S606 - abre con el visor de PDF del sistema
    elif platform.system() == "Darwin":
        subprocess.Popen(["open", ruta])
    else:
        subprocess.Popen(["xdg-open", ruta])


if __name__ == "__main__":
    generar_pdf(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "")
