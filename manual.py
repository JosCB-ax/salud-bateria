"""Manual de usuario: el contenido y su versión en PDF con índice que se puede pulsar.

El mismo contenido se muestra en la pestaña «Manual» del programa y se publica en
PDF junto a las descargas (python manual.py <ruta.pdf>).
"""

from __future__ import annotations

import os
import sys

import idioma
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
         "Este manual: Manual-Salud-de-la-bateria-<versión>.pdf (en inglés: User-Manual-Battery-Health-<versión>.pdf)"],
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
        "Muestra este mismo manual dentro del programa, en el idioma del programa, con el índice al principio: pulsa un apartado para ir "
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
        f"© {legal.ANIO} {legal.AUTOR}. Todos los derechos reservados. Uso gratuito; no se permite venderlo, distribuir copias modificadas ni quitar los "
        f"avisos de autoría. Para compartirlo, comparte el enlace oficial: {legal.WEB}",
        "Desarrollado con ayuda de herramientas de IA. El programa no usa inteligencia artificial mientras funciona.",
        f"Dudas y sugerencias: {legal.WEB}/issues",
    ]),
]

SECCIONES_EN = [
    ("inicio", "1. What Battery Health is", [
        "Battery Health is a free program for laptops that tells you how worn your battery is, how long it "
        "really lasts with the way you use your computer, which programs use the most power and what you can "
        "do to make the battery last more years.",
        "It works with any brand (HP, Lenovo, Dell, ASUS, Acer, Apple, MSI…), because it does not depend on "
        "the manufacturer: it reads the data the battery itself reports to the operating system.",
        ["Windows 10 and 11 (64-bit).",
         "macOS 11 or later, on Macs with Apple chips (M1, M2, M3…) and with Intel processors.",
         "Recent 64-bit Linux: Ubuntu 22.04 or later, Debian 12, Fedora, Linux Mint 21 and similar."],
        "Everything is calculated on your computer. The program does not send your data anywhere and needs "
        "no account.",
    ]),
    ("descarga", "2. Downloading the program", [
        f"Downloads are on the official page: {legal.WEB}/releases/latest",
        "Under «Assets», pick the file for your system:",
        ["Windows: SaludBateria-Setup-<version>.exe",
         "Mac with Apple chip: SaludBateria-<version>-macOS-Apple.dmg",
         "Mac with Intel: SaludBateria-<version>-macOS-Intel.dmg",
         "Linux: SaludBateria-<version>-Linux.tar.gz",
         "This manual: User-Manual-Battery-Health-<version>.pdf (Spanish: Manual-Salud-de-la-bateria-<version>.pdf)"],
        "To find out which Mac you have, open the Apple menu › About This Mac. If it says «Chip Apple M…», it "
        "is Apple; if it says «Processor … Intel», it is Intel.",
        "The SHA256SUMS.txt file contains the fingerprint of each download. The program uses it to check that "
        "updates have not been damaged or tampered with; you don't need to download it.",
    ]),
    ("windows", "3. Installing on Windows", [
        ["Open the SaludBateria-Setup-<version>.exe file you downloaded.",
         "Windows may show «Windows protected your PC», because the program is new and not signed by a "
         "company. Click «More info» and then «Run anyway».",
         "Choose whether to install it for all users of the computer (asks for administrator permission) or "
         "just for you.",
         "Read and accept the licence (in Spanish first, then in English).",
         "Tick «Start with the computer» if you like: the tray icon will then alert you about charging even "
         "if you don't open the window. You can change it later in Settings.",
         "Click «Install» and, when it finishes, «Finish». The program appears in the Start menu as "
         "«Salud de la batería»."],
        ("sub", "Updating"),
        "New versions install over the previous one, without uninstalling and without losing your settings or "
        "history. The program itself tells you when a new version is available (see «Updates»).",
        ("sub", "Uninstalling"),
        "Settings › Apps › Installed apps › Salud de la batería › Uninstall. Your settings and history stay in "
        "%APPDATA%\\SaludBateria; delete that folder if you won't use it again.",
    ]),
    ("macos", "4. Installing on macOS", [
        ["Open the .dmg file for your Mac (Apple or Intel).",
         "Drag the SaludBateria icon onto the «Applications» folder shown next to it.",
         "Open the program from Applications or Launchpad.",
         "The first time, macOS will say it cannot verify the developer, because the program is not signed by "
         "Apple. Go to System Settings › Privacy & Security and, at the bottom, click «Open Anyway». On "
         "versions before macOS 15 you can also right-click the program › Open › Open.",
         "From then on it opens normally."],
        ("sub", "Updating"),
        "Download the new .dmg and drag the program to Applications again, choosing «Replace». Your settings "
        "and history are kept.",
        ("sub", "Uninstalling"),
        "Drag SaludBateria from Applications to the Bin. The data is in ~/Library/Application Support/"
        "SaludBateria; if you turned on start with the computer, turn it off first in Settings (or delete "
        "~/Library/LaunchAgents/com.saludbateria.bandeja.plist).",
    ]),
    ("linux", "5. Installing on Linux", [
        ["Extract SaludBateria-<version>-Linux.tar.gz (double-click in most desktops, or "
         "«tar xzf SaludBateria-<version>-Linux.tar.gz» in a terminal).",
         "Go into the folder and run «./instalar-linux.sh». You don't need to be an administrator: it installs "
         "for your user only, in ~/.local/share/SaludBateria.",
         "Find it in the applications menu as «Salud de la batería». You can also start it with the "
         "«salud-bateria» command if ~/.local/bin is in your PATH."],
        ("sub", "Updating"),
        "Download the new .tar.gz and run «./instalar-linux.sh» again: it replaces the previous version and "
        "keeps your data.",
        ("sub", "Uninstalling"),
        "Run «./desinstalar-linux.sh» from the extracted folder. The data is in ~/.config/SaludBateria.",
        ("sub", "Notes"),
        ["Alerts are shown as desktop notifications (needs notify-send, included in almost every distribution).",
         "On GNOME the icon next to the clock only shows if you have a system tray extension; alerts work "
         "anyway.",
         "Saver mode uses powerprofilesctl and brightnessctl if they are installed."],
    ]),
    ("ventana", "6. The main window", [
        "When it opens, the program analyses the battery for a few seconds. At the top you will see:",
        ["The health circle: the percentage of capacity the battery keeps compared with when it was new, "
         "coloured by its condition (green, yellow, orange or red).",
         "The diagnosis: excellent (90 % or more), good (80–90 %), worn (60–80 %) or poor (below 60 %), with a "
         "sentence explaining it.",
         "The time of the last analysis."],
        "Below are five tabs (Battery, Battery life & history, What uses most, Tips and Manual) and, at the very "
        "bottom, the button bar. The last line shows the authorship notice.",
        "If the computer has no battery (a desktop), the program says so and still shows which programs use "
        "the most.",
    ]),
    ("bateria", "7. «Battery» tab", [
        "A table with all the data the system gives about the battery. Depending on the computer, some may "
        "be missing:",
        ["Health and wear: current capacity ÷ design capacity, and what has been lost.",
         "Design capacity and current capacity (full charge), in Wh.",
         "Charge cycles: how many times the equivalent of a full charge has been used.",
         "Current charge level and state (charging, discharging, plugged in).",
         "Instant power draw or charge rate, in watts, and time remaining.",
         "Temperature (Windows rarely reports it; macOS and Linux usually do).",
         "Charge limit, if the manufacturer has one turned on.",
         "Condition according to the system, manufacturer, model and chemistry (usually lithium-ion)."],
        ("sub", "Calibrate battery…"),
        "Over time, the chip that measures the battery drifts and may report less health than it really has. "
        "Calibration does not repair the battery: it only corrects that reading. The assistant records the "
        "health before, guides you through four steps (charge to 100 %, use it until it switches off, leave it "
        "off for a few hours and charge to 100 % again) and, when you press «I'm done: compare», tells you "
        "whether the reading has changed. Do it at most every 2 or 3 months, because a full discharge also "
        "causes wear.",
    ]),
    ("autonomia", "8. «Battery life & history» tab", [
        ("sub", "Real battery life"),
        "Instead of the brochure figure, the program calculates how long the battery lasts on your computer "
        "with the way you use it:",
        ["With your usual use: uses the average power draw from the last hours you used the laptop on battery "
         "(on Windows, from the system's own log; on every system, also from the measurements the program "
         "keeps).",
         "With what you are doing now: uses the current power draw, if you are unplugged."],
        "For each case it shows how long a full charge lasts today, how long it lasted when the battery was "
        "new and how much is left with the current charge. If you are plugged in and there are no measurements "
        "yet, it asks you to unplug for a few minutes and press «Refresh».",
        ("sub", "Health over time"),
        "A chart with the health for each day and a line at 80 %, the usual limit of normal wear. With at least "
        "30 days of data, the program calculates how fast your battery wears per year and predicts when it "
        "will reach 80 % and 60 %. The more days you use the program (or the tray icon), the more reliable the "
        "prediction.",
    ]),
    ("consumo", "9. «What uses most» tab", [
        "A list of the programs using the most processor and memory during a few seconds of measurement, "
        "adding up all the windows or processes of the same program. On macOS the «energy impact» calculated "
        "by the system is also shown.",
        "Select a program to see a specific tip to reduce its consumption (for example, in browsers, closing "
        "tabs or turning on memory saver).",
        ("sub", "Measure exact use (24 h)… (Windows only)"),
        "Reads the per-app energy log Windows keeps and shows which programs have used the most battery in the "
        "last 24 hours. Windows will ask for administrator permission, because that log is protected.",
        ("sub", "Power settings"),
        "Shows the system settings that most affect the battery: power plan or mode, brightness and others "
        "depending on the system.",
        ("sub", "Saver mode"),
        "Cuts power use with one click: on Windows it turns on the maximum power saving plan and lowers "
        "brightness to 40 %; on Linux it turns on the «power-saver» profile and lowers brightness; on macOS it "
        "opens the battery settings so you can turn on Low Power Mode (macOS asks for the administrator "
        "password to do it). When you press «Turn off saver mode», or plug in the charger, everything goes "
        "back to how it was.",
    ]),
    ("consejos", "10. «Tips» tab", [
        "Personalised tips based on your battery's condition, its temperature, whether you are always plugged "
        "in, the programs that use the most and your power settings. It includes how to turn on the charge "
        "limit in your system or with your manufacturer's app (Lenovo Vantage, MyASUS, Dell Power Manager, "
        "HP…), which is what extends battery life the most if you work plugged in.",
    ]),
    ("manual", "11. «Manual» tab", [
        "Shows this same manual inside the program, in the program's language, with the index at the start: "
        "click a section to go straight to it. The «Open the manual as PDF» button opens the PDF version with "
        "your system's viewer, to read, print or save it.",
    ]),
    ("botones", "12. Bottom bar buttons", [
        ["Refresh: analyses the battery and measures power use again.",
         "Export PDF…: saves a full report as PDF (health, data, battery life, chart, programs and tips). Useful "
         "to send to technical support or to check a second-hand laptop before buying it.",
         "Save report…: the same as a web page (HTML), which opens in the browser.",
         "Battery life test…: see the next section.",
         "About: version, authorship and the option to check for updates.",
         "Settings: see «Settings»."],
        "Reports include the computer name and the programs that were open; you decide who to share them with.",
    ]),
    ("prueba", "13. Guided battery life test", [
        "Measures for real how long your battery lasts. During the test the laptop does not sleep and the "
        "program uses battery at the rate you choose:",
        ["Duration: 20 minutes recommended (you can choose another). Longer gives a more accurate result.",
         "Type of use: light (screen on only, recommended), medium (like browsing or working on documents) or "
         "heavy (processor at full load, like gaming or video editing)."],
        "Unplug the charger, press «Start» and don't touch the laptop until it finishes. At the end you will see "
        "the average power draw in watts, the estimated battery life on a full charge (today and with a new "
        "battery) and the accuracy of the measurement. The result is saved in the history. You can cancel at "
        "any time.",
    ]),
    ("bandeja", "14. Tray icon and alerts", [
        "A small icon next to the clock keeps an eye on the battery even when the window is closed. Hover over "
        "it to see the percentage; click it or use its menu («Open Battery Health») to open the window.",
        ["Alert to unplug when reaching 80 % (or the value you choose).",
         "Alert to plug in when dropping below 20 % (or the value you choose).",
         "Temperature alert if the battery goes above 40 °C (if the system reports temperature).",
         "Once a day it records the battery health and, when you are unplugged, measures power use for the "
         "real battery life and the chart."],
        "Keeping the battery between 20 % and 80 % is what reduces its wear the most.",
    ]),
    ("ajustes", "15. Settings", [
        ("sub", "Charge alerts"),
        ["Alert me from the system tray: turns alerts on or off.",
         "Alert to unplug when reaching: 80 % recommended.",
         "Alert to plug in when dropping below: 20 % recommended.",
         "Restore recommended: goes back to 80 %, 20 % and 40 °C.",
         "Start with the computer: starts only the tray icon when you switch on, without opening the window.",
         "Alert if the battery goes above: 40 °C recommended."],
        ("sub", "Appearance and updates"),
        ["Theme: automatic (like the system), light or dark.",
         "Language: Spanish or English.",
         "Check for new versions when opening the program."],
        ("sub", "Legal information"),
        "Privacy policy, terms of use, and information sources and cookies. Press «Save» to apply changes.",
    ]),
    ("actualizaciones", "16. Updates", [
        "If turned on in Settings, once a day the program asks GitHub whether there is a new version. On "
        "Windows it offers to download and install it in one click: it checks the installer's SHA-256 "
        "fingerprint before running it and, if it doesn't match, installs nothing. On macOS and Linux it opens "
        "the downloads page so you can get the new version. You can also check manually from «About».",
    ]),
    ("privacidad", "17. Privacy and data", [
        ["No accounts, advertising, cookies or usage statistics.",
         "Your data (settings and history) is stored only on your computer, in the SaludBateria folder of your "
         "user profile.",
         "The only internet connection is the update check, which you can turn off."],
        "The full texts are in Settings › Legal information.",
    ]),
    ("problemas", "18. Common problems", [
        ("sub", "Health doesn't show or says «unknown»"),
        "Some batteries don't report their design capacity. The rest of the data and features are still "
        "available.",
        ("sub", "Health seems too low or changes a lot"),
        "The battery gauge may be out of calibration. Use the «Calibrate battery…» assistant.",
        ("sub", "Real battery life doesn't show"),
        "Power use needs to be measured on battery: unplug the charger for a few minutes, use the laptop as "
        "usual and press «Refresh».",
        ("sub", "I can't see the icon next to the clock"),
        "On Windows it may be hidden under the «^» arrow on the taskbar; drag it out to keep it always visible. "
        "On Linux with GNOME you need a system tray extension.",
        ("sub", "Windows or macOS won't let me open the program"),
        "That is the warning for unsigned programs. Follow the steps in the installation sections.",
        ("sub", "It can't find the battery"),
        "Check that the battery is properly connected and that the system shows it (for example, the system's "
        "battery icon). Virtual machines usually have no battery.",
    ]),
    ("autor", "19. Authorship and licence", [
        f"© {legal.ANIO} {legal.AUTOR}. All rights reserved. Free to use; selling it, distributing modified copies or removing the authorship "
        f"notices is not allowed. To share it, share the official link: {legal.WEB}",
        "Developed with the help of AI tools. The program does not use artificial intelligence while it runs.",
        f"Questions and suggestions: {legal.WEB}/issues",
    ]),
]


def secciones(lang: str | None = None) -> list:
    return SECCIONES_EN if (lang or idioma.actual()) == "en" else SECCIONES


def texto_plano() -> list[tuple[str, str, str]]:
    """Para la pestaña Manual, en el idioma del programa: [(id, título, cuerpo)]."""
    salida = []
    for clave, titulo, bloques in secciones():
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


def generar_pdf(ruta: str, version: str = "", lang: str | None = None) -> None:
    antes = idioma.actual()
    idioma.fijar(lang or antes)  # el pie y la portada salen en el idioma del manual
    try:
        _generar_pdf(ruta, version, idioma.actual())
    finally:
        idioma.fijar(antes)


def _generar_pdf(ruta: str, version: str, lang: str) -> None:
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

    en = lang == "en"
    nombre = "Battery Health" if en else "Salud de la batería"
    hist = [Spacer(1, 5 * cm), Paragraph(nombre, portada),
            Paragraph(("User manual" if en else "Manual de usuario")
                      + (f" · {'version' if en else 'versión'} {escape(version)}" if version else ""), sub),
            Spacer(1, 0.4 * cm),
            Paragraph("Installing on Windows, macOS and Linux, and every feature explained." if en else
                      "Instalación en Windows, macOS y Linux, y explicación de cada función.", sub),
            Spacer(1, 6 * cm), Paragraph(escape(legal.copyright()), p), Paragraph(escape(legal.WEB), p),
            PageBreak(), Paragraph("Contents" if en else "Índice", h1),
            Paragraph("Click any section to go to its page." if en else
                      "Pulsa cualquier apartado para ir a su página.", p)]
    indice = TableOfContents()
    indice.levelStyles = [ParagraphStyle("toc", parent=p, fontSize=11, leading=16, textColor=azul)]
    hist.append(indice)

    for clave, titulo, bloques in secciones(lang):
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
              title=f"{nombre} · {'User manual' if en else 'Manual de usuario'}", author=legal.AUTOR)
    doc.multiBuild(hist, onLaterPages=pie)


def nombre_pdf(version: str, lang: str) -> str:
    return (f"User-Manual-Battery-Health-{version}.pdf" if lang == "en"
            else f"Manual-Salud-de-la-bateria-{version}.pdf")


def ruta_local(version: str) -> str:
    """Genera (una vez por versión e idioma) el PDF en la carpeta del usuario y devuelve su ruta."""
    import configuracion
    ruta = os.path.join(configuracion.carpeta(), nombre_pdf(version, idioma.actual()))
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
    # python manual.py <carpeta> <versión>: crea el manual en español y en inglés
    for _lang in ("es", "en"):
        generar_pdf(os.path.join(sys.argv[1], nombre_pdf(sys.argv[2], _lang)), sys.argv[2], _lang)
