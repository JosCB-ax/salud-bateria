"""Autoría, aviso de IA y textos legales (privacidad, términos, fuentes y cookies).

Los textos van completos en cada idioma en lugar de pasar por idioma.t(),
porque son largos y tienen que leerse exactamente como están escritos.
"""

from __future__ import annotations

import idioma

AUTOR = "JosCB"
ANIO = 2026
WEB = "https://github.com/JosCB-ax/salud-bateria"


def copyright() -> str:
    if idioma.actual() == "en":
        return f"© {ANIO} {AUTOR}. All rights reserved."
    return f"© {ANIO} {AUTOR}. Todos los derechos reservados."


def aviso_ia() -> str:
    if idioma.actual() == "en":
        return "Developed with the help of AI tools."
    return "Desarrollado con ayuda de herramientas de IA."


def pie() -> str:
    """Línea fija que aparece en la ventana, los informes y el PDF."""
    return f"{copyright()} · {aviso_ia()}"

_IA_ES = ("Este programa se ha desarrollado con ayuda de herramientas de inteligencia artificial, bajo la "
          f"dirección, revisión y decisión de su autor, {AUTOR}. El programa no usa inteligencia artificial "
          "mientras funciona: todos los cálculos se hacen en tu equipo con reglas fijas, y no genera ni "
          "envía contenido a ningún servicio de IA. Se informa de ello por transparencia, en la línea del "
          "Reglamento europeo de Inteligencia Artificial (UE) 2024/1689.")

_IA_EN = ("This program was developed with the help of artificial intelligence tools, under the direction, "
          f"review and decisions of its author, {AUTOR}. The program does not use artificial intelligence while "
          "it runs: all calculations are done on your computer with fixed rules, and it neither generates nor "
          "sends content to any AI service. This is stated for transparency, in line with the EU Artificial "
          "Intelligence Act (Regulation (EU) 2024/1689).")


_ES = {
    "privacidad": ("Política de privacidad", f"""\
Última actualización: 6 de octubre de {ANIO}

1. Quién es el responsable
Salud de la batería es un programa gratuito desarrollado por {AUTOR}. La vía de contacto es la página del proyecto: {WEB} (apartado «Issues»).

2. Qué datos trata el programa
El programa lee en tu propio equipo:
• Datos de la batería: capacidad de fábrica y actual, ciclos, carga, temperatura y consumo.
• Los programas en marcha y cuánto procesador y memoria usan, solo mientras analizas.
• Algunos ajustes de energía del sistema (plan de energía, brillo).
• Si pulsas «Medir consumo exacto» en Windows, el registro de energía por aplicación que guarda Windows (SRUM). Para eso Windows te pide permiso de administrador.
Ninguno de estos datos sale de tu equipo. No hay cuentas de usuario, ni telemetría, ni estadísticas de uso, ni publicidad.

3. Qué se guarda y dónde
• config.json: tus ajustes (avisos, tema, idioma…).
• historial.json: la salud de la batería una vez al día y muestras de consumo, para la gráfica y la predicción.
Están en la carpeta de usuario «SaludBateria» (en Windows, %APPDATA%\\SaludBateria). Puedes borrarlos cuando quieras; el programa vuelve a empezar desde cero.

4. Conexiones a internet
La única conexión es la búsqueda de actualizaciones: una vez al día el programa pregunta a GitHub (de GitHub Inc.) cuál es la última versión y, si aceptas, descarga el instalador desde allí. Como en cualquier visita a una web, GitHub recibe tu dirección IP; el desarrollador no recibe ningún dato. Puedes desactivarlo en Ajustes › «Buscar actualizaciones automáticamente».

5. Informes que compartes
Los informes en PDF o HTML incluyen el nombre del equipo y los programas que estaban en marcha. Solo se crean cuando tú los pides y tú decides con quién compartirlos.

6. Tus derechos
Como el desarrollador no recibe ni guarda datos tuyos, no hay datos suyos que consultar, corregir o borrar: todo está en tu equipo y bajo tu control. Si crees que se ha vulnerado tu derecho a la protección de datos, puedes reclamar ante la Agencia Española de Protección de Datos (www.aepd.es).

7. Cambios
Si esta política cambia, la nueva versión vendrá con la actualización del programa y la fecha de arriba lo indicará."""),

    "terminos": ("Términos de uso", f"""\
Última actualización: 6 de octubre de {ANIO}

1. Autor y licencia
Salud de la batería es una obra de {AUTOR}, protegida por la Ley de Propiedad Intelectual. {copyright()}
Puedes descargar, instalar y usar el programa gratis, en casa o en el trabajo, en todos los equipos que quieras. No está permitido venderlo, distribuir copias modificadas, quitar o cambiar los avisos de autoría, ni presentarlo como obra propia, salvo permiso por escrito del autor. Para compartirlo, comparte el enlace oficial: {WEB}

2. Qué hace y qué no
El programa muestra la información que la batería y el sistema operativo dan sobre sí mismos. La salud, la autonomía y las predicciones son estimaciones: dependen de la calidad de esos datos y pueden no coincidir con las de otras herramientas o con las del fabricante. No sustituye a un diagnóstico técnico ni a la garantía del fabricante.

3. Funciones que cambian tu equipo
• Modo ahorro: cambia el plan de energía y el brillo, y los devuelve como estaban al desactivarlo o al enchufar el cargador.
• Prueba de autonomía: gasta batería a propósito durante el tiempo que elijas.
• Calibración: consiste en cargar y descargar la batería del todo, por eso se recomienda solo de vez en cuando.
• Consumo exacto (Windows): ejecuta una herramienta de Windows con permiso de administrador, solo cuando tú lo pides.
Usa estas funciones bajo tu criterio, sobre todo si la batería está muy desgastada o se calienta.

4. Garantía y responsabilidad
El programa se ofrece gratis y «tal cual», sin garantía de que esté libre de errores. En la medida en que la ley lo permite, el autor no responde de daños derivados de su uso. Esto no limita los derechos que la ley te reconoce como consumidor ni la responsabilidad por dolo o culpa grave.

5. Uso de inteligencia artificial
{_IA_ES}

6. Ley aplicable
Estos términos se rigen por la ley española. Al usar el programa los aceptas; si no estás de acuerdo, desinstálalo."""),

    "fuentes": ("Fuentes de información y cookies", """\
Cookies
Este programa no usa cookies, ni ninguna técnica parecida de seguimiento: no es una página web, no muestra publicidad y no contiene herramientas de analítica. La única conexión a internet es la búsqueda de actualizaciones en GitHub (ver la Política de privacidad).

De dónde salen los datos de la batería
Se leen del propio equipo, con las herramientas que trae cada sistema; por eso sirve para cualquier marca:
• Windows: informe de batería de Windows («powercfg /batteryreport»), las clases de batería de WMI (BatteryStatus, BatteryStaticData, BatteryFullChargedCapacity, BatteryCycleCount) y, para el consumo exacto, el registro SRUM («powercfg /srumutil»).
• macOS: «ioreg» (AppleSmartBattery), «system_profiler SPPowerDataType» y «top» (impacto energético).
• Linux: /sys/class/power_supply, que publica el núcleo del sistema.
• En todos: la librería psutil para el porcentaje de carga y los programas en marcha.

De dónde salen los consejos
Son recomendaciones generales y aceptadas sobre baterías de iones de litio: evitar el calor, no tenerla mucho tiempo al 100 % ni dejarla vaciar del todo, y usar el límite de carga cuando el equipo lo ofrece (por ejemplo «Carga optimizada» de Apple, «Modo de conservación» de Lenovo Vantage o los límites de carga de Dell, HP o ASUS). Los umbrales 20–80 % y 40 °C son valores prudentes recomendados; puedes cambiarlos en Ajustes. Las estimaciones de autonomía y desgaste se calculan con tus propios datos, con fórmulas propias del programa.

Programas de terceros incluidos
• Python — licencia PSF
• Tcl/Tk (ventanas) — licencia BSD
• psutil — licencia BSD de 3 cláusulas
• pystray (icono junto al reloj) — licencia LGPL v3
• Pillow (imágenes) — licencia MIT-CMU
• ReportLab (PDF) — licencia BSD
• PyInstaller (empaquetado) — GPL con excepción para programas empaquetados
Gracias a sus autores. Sus licencias permiten incluirlos en este programa; los textos completos están en la web de cada proyecto."""),
}


_EN = {
    "privacidad": ("Privacy policy", f"""\
Last updated: 6 October {ANIO}

1. Who is responsible
Battery Health is free software developed by {AUTOR}. You can get in touch through the project page: {WEB} ("Issues").

2. What data the program handles
The program reads, on your own computer:
• Battery data: design and current capacity, cycles, charge, temperature and power draw.
• The programs that are running and how much CPU and memory they use, only while analysing.
• Some system power settings (power plan, brightness).
• If you press "Measure exact use" on Windows, the per-app energy log Windows keeps (SRUM). Windows asks for administrator permission for this.
None of this data leaves your computer. There are no user accounts, no telemetry, no usage statistics and no advertising.

3. What is stored and where
• config.json: your settings (alerts, theme, language…).
• historial.json: battery health once a day and power samples, for the chart and the prediction.
They are in the "SaludBateria" folder of your user profile (on Windows, %APPDATA%\\SaludBateria). You can delete them at any time; the program simply starts again from scratch.

4. Internet connections
The only connection is the update check: once a day the program asks GitHub (GitHub Inc.) for the latest version and, if you agree, downloads the installer from there. As with any website visit, GitHub receives your IP address; the developer receives no data. You can turn this off in Settings › "Check for updates automatically".

5. Reports you share
PDF and HTML reports include the computer name and the programs that were running. They are only created when you ask, and you decide who to share them with.

6. Your rights
Since the developer neither receives nor keeps any of your data, there is nothing held by them to access, correct or delete: everything is on your computer and under your control. If you believe your data protection rights have been infringed, you can complain to the Spanish Data Protection Agency (www.aepd.es) or the authority of your country.

7. Changes
If this policy changes, the new version will come with the program update and the date above will show it."""),

    "terminos": ("Terms of use", f"""\
Last updated: 6 October {ANIO}

1. Author and licence
Battery Health is a work by {AUTOR}, protected by copyright law. {copyright()}
You may download, install and use the program free of charge, at home or at work, on as many computers as you like. You may not sell it, distribute modified copies, remove or change the authorship notices, or present it as your own work, without the author's written permission. To share it, share the official link: {WEB}

2. What it does and what it doesn't
The program shows the information the battery and the operating system report about themselves. Health, battery life and predictions are estimates: they depend on the quality of that data and may differ from other tools or from the manufacturer's figures. It does not replace a technical diagnosis or the manufacturer's warranty.

3. Features that change your computer
• Power saving mode: changes the power plan and brightness, and restores them when you turn it off or plug in the charger.
• Battery life test: deliberately uses battery for the time you choose.
• Calibration: means fully charging and discharging the battery, so it is only recommended occasionally.
• Measure exact use (Windows): runs a Windows tool with administrator permission, only when you ask.
Use these features at your own discretion, especially if the battery is very worn or gets hot.

4. Warranty and liability
The program is provided free of charge and "as is", with no guarantee that it is error-free. To the extent permitted by law, the author is not liable for damage arising from its use. This does not limit your statutory rights as a consumer or liability for wilful misconduct or gross negligence.

5. Use of artificial intelligence
{_IA_EN}

6. Governing law
These terms are governed by Spanish law. By using the program you accept them; if you do not agree, uninstall it."""),

    "fuentes": ("Information sources and cookies", """\
Cookies
This program does not use cookies or any similar tracking technique: it is not a website, shows no advertising and contains no analytics tools. The only internet connection is the update check on GitHub (see the Privacy policy).

Where the battery data comes from
It is read from the computer itself, with the tools each system provides; that is why it works with any brand:
• Windows: the Windows battery report ("powercfg /batteryreport"), the WMI battery classes (BatteryStatus, BatteryStaticData, BatteryFullChargedCapacity, BatteryCycleCount) and, for exact use, the SRUM log ("powercfg /srumutil").
• macOS: "ioreg" (AppleSmartBattery), "system_profiler SPPowerDataType" and "top" (energy impact).
• Linux: /sys/class/power_supply, published by the system kernel.
• On all of them: the psutil library for the charge level and running programs.

Where the tips come from
They are general, widely accepted recommendations for lithium-ion batteries: avoid heat, don't keep the battery at 100 % for long or let it run completely flat, and use the charge limit when the computer offers one (for example Apple's "Optimised Battery Charging", Lenovo Vantage's "Conservation mode" or the charge limits of Dell, HP or ASUS). The 20–80 % and 40 °C thresholds are cautious recommended values; you can change them in Settings. Battery life and wear estimates are calculated from your own data, with the program's own formulas.

Third-party software included
• Python — PSF licence
• Tcl/Tk (windows) — BSD licence
• psutil — 3-clause BSD licence
• pystray (tray icon) — LGPL v3
• Pillow (images) — MIT-CMU licence
• ReportLab (PDF) — BSD licence
• PyInstaller (packaging) — GPL with an exception for bundled programs
Thanks to their authors. Their licences allow them to be included in this program; the full texts are on each project's website."""),
}


def texto(clave: str) -> tuple[str, str]:
    """(título, cuerpo) de «privacidad», «terminos» o «fuentes» en el idioma actual."""
    return (_EN if idioma.actual() == "en" else _ES)[clave]
