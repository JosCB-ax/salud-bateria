"""Traducción de la interfaz. El programa se escribe en español y aquí se traduce.

`t(texto)` busca la frase exacta y, si no está, una plantilla con {} para las
partes variables (números, nombres). Los textos compuestos (varias líneas,
partes separadas por " · " o varias frases) se traducen por trozos.
"""

from __future__ import annotations

import re

_idioma = "es"

EN = {
    # --- ventana
    "Salud de la batería": "Battery Health",
    "Salud de la batería {}": "Battery Health {}",
    "Salud de la batería: {}": "Battery health: {}",
    "Salud de la batería · {} %": "Battery Health · {} %",
    "Salud de la batería · {} % · cargando": "Battery Health · {} % · charging",
    "Analizando la batería…": "Analyzing the battery…",
    "salud": "health",
    "Batería": "Battery",
    "Autonomía e historial": "Battery life & history",
    "Qué consume más": "What uses most",
    "Consejos": "Tips",
    "Dato": "Item", "Valor": "Value", "Programa": "Program", "CPU": "CPU", "Memoria": "Memory",
    "Procesos": "Processes",
    "Actualizar": "Refresh", "Exportar PDF…": "Export PDF…", "Guardar informe…": "Save report…",
    "Ajustes": "Settings", "Acerca de": "About", "Prueba de autonomía…": "Battery life test…",
    "Prueba de autonomía": "Battery life test", "Calibrar la batería…": "Calibrate battery…",
    "Calibrar la batería": "Calibrate battery",
    "Actualizado: {}": "Updated: {}",
    "Midiendo el consumo durante 3 segundos…": "Measuring power use for 3 seconds…",
    "No se pudo analizar la batería:\n{}": "The battery could not be analyzed:\n{}",
    "Excelente": "Excellent", "Buena": "Good", "Desgastada": "Worn", "Mala": "Poor", "Sin datos": "No data",
    "{} ciclos": "{} cycles", "carga al {} %": "{} % charged", "quedan {} h {} min": "{} h {} min left",
    "No se ha encontrado ninguna batería": "No battery found",
    "¿Es un ordenador de sobremesa? El resto del análisis sigue disponible.":
        "Is this a desktop computer? The rest of the analysis is still available.",
    "Selecciona un programa para ver cómo reducir su consumo.": "Select a program to see how to reduce its power use.",
    "{}: si no lo estás usando, ciérralo para ahorrar batería.": "{}: if you are not using it, close it to save battery.",
    "Ajustes de energía:  {}": "Power settings:  {}",
    "Medir consumo exacto (24 h)…": "Measure exact use (24 h)…",
    "Usa el registro de energía de Windows; pide permiso de administrador.":
        "Uses the Windows energy log; asks for administrator permission.",
    "Acepta el permiso de Windows y espera unos segundos…": "Accept the Windows prompt and wait a few seconds…",
    "No se pudo leer: hace falta aceptar el permiso de administrador.":
        "Could not read it: the administrator prompt must be accepted.",
    "Windows no tiene datos de energía por programa de las últimas 24 h.":
        "Windows has no per-program energy data for the last 24 h.",
    "Energía gastada en las últimas 24 h:  {}": "Energy used in the last 24 h:  {}",
    "Autonomía real con la configuración de este equipo": "Real battery life with this computer's settings",
    "Evolución de la salud": "Health over time",
    "No hay batería.": "No battery.",
    "{} ({} W, {}):": "{} ({} W, {}):",
    "Con tu uso habitual": "With your usual use",
    "Con lo que estás haciendo ahora": "With what you are doing now",
    "consumo medio con batería en las últimas {} h de uso": "average use on battery over the last {} h of use",
    "consumo medido en este momento": "power measured right now",
    "Carga completa hoy: {}": "Full charge today: {}",
    "cuando era nueva: {}": "when new: {}",
    "con la carga actual: {}": "with the current charge: {}",
    "El desgaste te cuesta {} de autonomía por carga.": "Wear costs you {} of battery life per charge.",
    "Última prueba guiada ({}, uso {}): {} W, carga completa {}.": "Last guided test ({}, {} use): {} W, full charge {}.",
    "{} h {} min": "{} h {} min",
    "Windows aún no tiene historial suficiente de esta batería.": "There is not enough history for this battery yet.",
    "80 %: límite de desgaste normal": "80 %: normal wear limit",
    "Para calcular tu autonomía real hace falta medir el consumo con batería: desenchufa el cargador unos minutos, "
    "usa el portátil como siempre y pulsa Actualizar.":
        "To calculate your real battery life, power use must be measured on battery: unplug the charger for a few "
        "minutes, use the laptop as usual and press Refresh.",
    "El sistema no informa del consumo de la batería, así que no se puede calcular la autonomía.":
        "The system does not report battery power use, so battery life cannot be calculated.",
    # --- predicción
    "Pierde {} puntos de salud al año.": "It loses {} health points per year.",
    "Ya está por debajo del {} %.": "It is already below {} %.",
    "Llegará al {} % {}.": "It will reach {} % {}.",
    "en menos de un mes": "in less than a month", "en un mes aproximadamente": "in about a month",
    "en unos {} meses": "in about {} months", "en unos {} años": "in about {} years",
    "no se prevé con el ritmo actual": "not expected at the current rate",
    "Aún no hay historial suficiente para predecir el desgaste (hace falta al menos {} días de datos).":
        "There is not enough history to predict wear yet (at least {} days of data are needed).",
    # --- ajustes
    "Avisos de carga": "Charge alerts",
    "Avisarme desde la bandeja del sistema": "Alert me from the system tray",
    "Avisar para desenchufar al llegar a:": "Alert to unplug when reaching:",
    "Avisar para enchufar al bajar de:": "Alert to plug in when dropping below:",
    "%  (recomendado: {})": "%  (recommended: {})", "°C  (recomendado: {})": "°C  (recommended: {})",
    "Restaurar recomendados": "Restore recommended",
    "Iniciar con el ordenador (solo el icono de la bandeja)": "Start with the computer (tray icon only)",
    "Avisar si la batería pasa de": "Alert if the battery goes above",
    "Aspecto y actualizaciones": "Appearance and updates", "Tema:": "Theme:", "Idioma:": "Language:",
    "Automático (como el sistema)": "Automatic (like the system)", "Claro": "Light", "Oscuro": "Dark",
    "Buscar versiones nuevas al abrir el programa": "Check for new versions when opening the program",
    "Guardar": "Save", "Cancelar": "Cancel", "Cerrar": "Close", "Empezar": "Start",
    "Información legal": "Legal information", "Privacidad": "Privacy", "Términos de uso": "Terms of use",
    "Fuentes y cookies": "Sources and cookies",
    "Abrir el manual en PDF": "Open the manual as PDF",
    "Pulsa un apartado del índice para ir a él.": "Click a section in the index to jump to it (the manual is in Spanish).",
    "Privacidad, términos de uso y fuentes: en Ajustes.": "Privacy, terms of use and sources: in Settings.",
    "El instalador descargado no coincide con el publicado. No se ha instalado nada.":
        "The downloaded installer does not match the published one. Nothing has been installed.",
    "Los porcentajes deben ser números.": "Percentages must be numbers.",
    "El aviso para enchufar debe ser menor que el de desenchufar.":
        "The plug-in alert must be lower than the unplug alert.",
    "No se pudo cambiar el inicio automático:\n{}": "Could not change automatic startup:\n{}",
    # --- ahorro
    "Activar modo ahorro": "Turn on saver mode", "Desactivar modo ahorro": "Turn off saver mode",
    "Modo ahorro activo. Se desactiva solo al enchufar el cargador.":
        "Saver mode is on. It turns off by itself when you plug in the charger.",
    "Pone el plan de ahorro de energía y baja el brillo; al desactivarlo lo deja todo como estaba.":
        "Switches to the power saver plan and lowers brightness; turning it off restores everything.",
    "Modo ahorro desactivado: todo está como antes.": "Saver mode off: everything is back as it was.",
    "Modo ahorro activado. {}": "Saver mode on. {}",
    "Este equipo no permite cambiar plan ni brillo desde aquí.":
        "This computer does not allow changing the plan or brightness from here.",
    "Plan de energía: Economizador": "Power plan: Power saver", "Perfil de energía: ahorro": "Power profile: saver",
    "Brillo: {} % → {} %": "Brightness: {} % → {} %",
    "Se han abierto los ajustes de Batería: activa allí el modo de bajo consumo.":
        "Battery settings have been opened: turn on Low Power Mode there.",
    "Cargador conectado: el modo ahorro se ha desactivado y todo está como antes.":
        "Charger connected: saver mode has been turned off and everything is back as it was.",
    # --- calibración
    "La calibración no repara la batería: corrige la medida que hace su chip, que con el tiempo se desajusta y "
    "puede marcar menos salud de la real. Hazla como mucho cada 2 o 3 meses.":
        "Calibration does not repair the battery: it corrects the measurement made by its chip, which drifts over "
        "time and can show less health than the real one. Do it at most every 2 or 3 months.",
    "1. Carga al 100 % y déjalo enchufado una o dos horas más.":
        "1. Charge to 100 % and leave it plugged in for one or two more hours.",
    "2. Desenchufa y úsalo con normalidad hasta que se apague solo (o baje al 3-5 %).":
        "2. Unplug it and use it normally until it shuts down by itself (or drops to 3-5 %).",
    "3. Déjalo apagado unas horas y cárgalo al 100 % sin interrumpir.":
        "3. Leave it off for a few hours and charge it to 100 % without interruption.",
    "4. Abre el programa y pulsa «He terminado» para comparar.": "4. Open the program and press «I'm done» to compare.",
    "Empezar calibración": "Start calibration", "He terminado: comparar": "I'm done: compare",
    "No se puede leer la salud de esta batería, así que no hay nada que comparar.":
        "This battery's health cannot be read, so there is nothing to compare.",
    "Apuntado: salud antes de calibrar {} %. Sigue los pasos.": "Saved: health before calibrating {} %. Follow the steps.",
    "Calibración empezada el {} con {} % de salud.": "Calibration started on {} with {} % health.",
    "Midiendo…": "Measuring…",
    "Antes ({}): {} %": "Before ({}): {} %", "Ahora: {} %": "Now: {} %", "Diferencia: {} puntos.": "Difference: {} points.",
    "Diferencia: {} puntos. La medida estaba desajustada y ahora es más exacta.":
        "Difference: {} points. The measurement was off and is now more accurate.",
    "Diferencia: {} puntos. La medida ya era correcta: este es el desgaste real.":
        "Difference: {} points. The measurement was already correct: this is the real wear.",
    # --- prueba de autonomía
    "Mide cuánto dura tu batería con un uso fijo. Antes de empezar: desenchufa el cargador, pon el brillo de la "
    "pantalla al 50 % y cierra los programas que no necesites. No toques el portátil hasta que termine.":
        "Measures how long your battery lasts with a fixed workload. Before starting: unplug the charger, set screen "
        "brightness to 50 % and close the programs you don't need. Don't touch the laptop until it finishes.",
    "Duración:": "Duration:", "Tipo de uso:": "Type of use:",
    "minutos  (recomendado: {}; más tiempo, más precisión)": "minutes  (recommended: {}; longer is more accurate)",
    "Uso ligero: solo la pantalla encendida (recomendado)": "Light use: screen on only (recommended)",
    "Uso medio: como navegar o trabajar con documentos": "Medium use: like browsing or working on documents",
    "Uso intenso: procesador al máximo, como jugar o editar vídeo": "Heavy use: processor at full load, like gaming or video editing",
    "La duración mínima es de 5 minutos.": "The minimum duration is 5 minutes.",
    "Midiendo… quedan {} min {} s": "Measuring… {} min {} s left",
    "Resultado: consume {} W con este uso. Una carga completa dura {}": "Result: it uses {} W with this workload. A full charge lasts {}",
    "Resultado: consume {} W con este uso. Una carga completa dura {} (cuando era nueva: {}). Precisión de la medida: {}.":
        "Result: it uses {} W with this workload. A full charge lasts {} (when new: {}). Measurement accuracy: {}.",
    "Resultado: consume {} W con este uso. Una carga completa dura {}. Precisión de la medida: {}.":
        "Result: it uses {} W with this workload. A full charge lasts {}. Measurement accuracy: {}.",
    "alta": "high", "media": "medium", "baja": "low", "ligera": "light",
    "La batería no ha bajado lo suficiente para medir. Prueba con más tiempo.":
        "The battery has not dropped enough to measure. Try a longer duration.",
    "No se puede leer la batería de este equipo.": "This computer's battery cannot be read.",
    "Desenchufa el cargador antes de empezar la prueba.": "Unplug the charger before starting the test.",
    "El sistema no informa de la carga de la batería.": "The system does not report the battery charge.",
    "Prueba cancelada.": "Test cancelled.",
    "Se ha enchufado el cargador: la prueba se ha detenido.": "The charger was plugged in: the test has stopped.",
    # --- actualizaciones y acerca de
    "Actualizaciones": "Updates", "Actualización disponible": "Update available",
    "Tienes la última versión ({}).": "You have the latest version ({}).",
    "Hay una versión nueva: {} (tienes la {}).\n\n¿Descargarla e instalarla ahora?":
        "A new version is available: {} (you have {}).\n\nDownload and install it now?",
    "No se pudo descargar:\n{}": "Could not download:\n{}",
    "Mide el desgaste real de la batería con los datos que su firmware da al sistema operativo, por eso funciona "
    "con cualquier marca de portátil.":
        "Measures the battery's real wear from the data its firmware gives the operating system, so it works with "
        "any laptop brand.",
    "¿Buscar ahora si hay una versión nueva?": "Check for a new version now?",
    "Exportar a PDF": "Export to PDF", "Guardar informe": "Save report", "Informe HTML": "HTML report",
    "No se pudo crear el PDF:\n{}": "The PDF could not be created:\n{}",
    "Informe del {}": "Report of {}", "Programas que más consumían": "Programs using the most",
    "Autonomía real:": "Real battery life:",
    "{} ({} W): carga completa hoy {}, cuando era nueva {}.": "{} ({} W): full charge today {}, when new {}.",
    "{} ({} W): carga completa hoy {}.": "{} ({} W): full charge today {}.",
    "Ajustes de energía": "Power settings",
    "Consejos para cuidar la batería": "Tips to care for your battery",
    "Programas que más consumen ahora": "Programs using the most right now",
    # --- tabla de datos (informe.py)
    "Salud": "Health", "Desgaste": "Wear", "Capacidad de fábrica": "Design capacity",
    "Capacidad actual (carga completa)": "Current capacity (full charge)", "Ciclos de carga": "Charge cycles",
    "Nivel de carga ahora": "Charge level now", "Estado": "Status", "Consumo / carga instantánea": "Current power draw",
    "Tiempo restante": "Time remaining", "Temperatura": "Temperature", "Límite de carga": "Charge limit",
    "no configurado": "not set", "Condición según el sistema": "Condition reported by the system",
    "Fabricante / modelo": "Manufacturer / model", "Química": "Chemistry",
    "cargando": "charging", "descargando": "discharging", "llena": "full", "enchufado": "plugged in",
    "enchufado sin cargar": "plugged in, not charging", "Batería interna": "Internal battery",
    "Plan de energía": "Power plan", "Modo de bajo consumo": "Low Power Mode", "activado": "on",
    "desactivado": "off", "Apagar pantalla tras": "Turn off display after", "Perfil de energía": "Power profile",
    "Brillo de pantalla": "Screen brightness", "Gobernador de CPU": "CPU governor",
    # --- diagnóstico y consejos
    "excelente": "excellent", "buena": "good", "desgastada": "worn", "mala": "poor", "desconocida": "unknown",
    "La batería conserva el {} % de su capacidad original. Está como nueva.":
        "The battery keeps {} % of its original capacity. It is like new.",
    "Conserva el {} % de su capacidad original. Desgaste normal.": "It keeps {} % of its original capacity. Normal wear.",
    "Conserva el {} % de su capacidad original. Notarás menos autonomía; aún no hace falta cambiarla.":
        "It keeps {} % of its original capacity. You will notice less battery life; it does not need replacing yet.",
    "Solo conserva el {} % de su capacidad original. Conviene plantearse cambiarla.":
        "It only keeps {} % of its original capacity. Consider replacing it.",
    "El sistema no informa de la capacidad de fábrica de esta batería, así que no se puede calcular su salud exacta.":
        "The system does not report this battery's design capacity, so its exact health cannot be calculated.",
    "La batería está muy desgastada: un recambio original o certificado te devolverá la autonomía. Si se hincha "
    "(la carcasa o el touchpad se levantan), deja de usarla y cámbiala ya.":
        "The battery is very worn: an original or certified replacement will restore your battery life. If it swells "
        "(the case or touchpad lifts), stop using it and replace it now.",
    "Lleva {} ciclos y sigue por encima del 80 %: la estás cuidando bien.":
        "It has {} cycles and is still above 80 %: you are taking good care of it.",
    "Solo {} ciclos pero ya un {} % de desgaste: suele deberse al calor o a pasar mucho tiempo al 100 %. "
    "Revisa los consejos de carga.":
        "Only {} cycles but already {} % wear: this is usually caused by heat or spending a lot of time at 100 %. "
        "Check the charging tips.",
    "La batería está a {} °C. Por encima de 35-40 °C se desgasta mucho más rápido: no tapes las rejillas, úsalo "
    "sobre una superficie dura y limpia el polvo de los ventiladores.":
        "The battery is at {} °C. Above 35-40 °C it wears much faster: don't cover the vents, use it on a hard "
        "surface and clean the dust from the fans.",
    "Temperatura algo alta ({} °C). Evita usarlo sobre la cama o las piernas.":
        "Temperature somewhat high ({} °C). Avoid using it on the bed or on your lap.",
    "Está enchufado y al 100 %. Si casi siempre lo usas conectado, limita la carga al 80 %: es lo que más alarga "
    "la vida de la batería.":
        "It is plugged in and at 100 %. If you almost always use it plugged in, limit charging to 80 %: it is what "
        "extends battery life the most.",
    "Mantener la carga entre el 20 % y el 80 % alarga mucho la vida de la batería.":
        "Keeping the charge between 20 % and 80 % greatly extends battery life.",
    "Tienes la carga limitada al {} %. Perfecto para alargar su vida.": "Charging is limited to {} %. Perfect for extending its life.",
    "Queda poca carga. Evita llegar a 0 % a menudo: las descargas completas desgastan la batería.":
        "Battery is low. Avoid reaching 0 % often: full discharges wear the battery.",
    "{}: '{}'. Cámbialo a equilibrado o ahorro cuando no estés enchufado.":
        "{}: '{}'. Switch it to balanced or power saver when not plugged in.",
    "Activa el modo de bajo consumo cuando vayas con batería (Ajustes > Batería).":
        "Turn on Low Power Mode when running on battery (Settings > Battery).",
    "Brillo al {}. La pantalla es lo que más gasta: bajarlo al 50 % puede darte una hora más de autonomía.":
        "Brightness at {}. The screen uses the most power: lowering it to 50 % can give you an extra hour.",
    "Ahora mismo {} está usando mucha CPU. Ciérralo si no lo necesitas.":
        "Right now {} is using a lot of CPU. Close it if you don't need it.",
    "No dejes el portátil guardado mucho tiempo al 100 % ni al 0 %: para guardarlo, déjalo al 50 %.":
        "Don't store the laptop for long at 100 % or 0 %: to store it, leave it at 50 %.",
    "Usa el cargador original o uno certificado con la potencia correcta.":
        "Use the original charger or a certified one with the correct power rating.",
    "En Mac: Ajustes > Batería > Carga optimizada (o 'Límite de carga' en los modelos que lo tienen).":
        "On Mac: Settings > Battery > Optimized Charging (or 'Charge Limit' on models that have it).",
    "En Windows se hace con la app del fabricante: Lenovo Vantage (Conservación de batería), MyASUS (Cuidado de "
    "batería), Dell Power Manager, HP (BIOS > Battery Care), MSI Center o Samsung Settings.":
        "On Windows this is done with the manufacturer's app: Lenovo Vantage (Conservation Mode), MyASUS (Battery "
        "Care), Dell Power Manager, HP (BIOS > Battery Care), MSI Center or Samsung Settings.",
    "En Linux, si existe /sys/class/power_supply/BAT0/charge_control_end_threshold, escribe 80 en él (o usa TLP); "
    "GNOME y KDE lo ofrecen en Ajustes > Energía.":
        "On Linux, if /sys/class/power_supply/BAT0/charge_control_end_threshold exists, write 80 to it (or use TLP); "
        "GNOME and KDE offer it in Settings > Power.",
    "Carga optimizada disponible en Ajustes > Batería.": "Optimized Charging available in Settings > Battery.",
    "El sistema solo informa del nivel de carga; no expone la capacidad de diseño.":
        "The system only reports the charge level; it does not expose the design capacity.",
    # --- consejos por programa
    "Chrome abre un proceso por pestaña: cierra pestañas o activa el Ahorro de energía en Ajustes > Rendimiento.":
        "Chrome opens a process per tab: close tabs or turn on Energy Saver in Settings > Performance.",
    "Edge: activa 'Eficiencia' en Configuración > Sistema y rendimiento.": "Edge: turn on 'Efficiency mode' in Settings > System and performance.",
    "Firefox: cierra pestañas que no uses; about:processes muestra cuál gasta más.":
        "Firefox: close tabs you don't use; about:processes shows which one uses the most.",
    "Teams consume mucho en segundo plano: ciérralo del todo si no estás en reunión.":
        "Teams uses a lot in the background: quit it completely if you are not in a meeting.",
    "Las videollamadas gastan mucho; apaga la cámara si no la necesitas.": "Video calls use a lot; turn off the camera if you don't need it.",
    "Discord con aceleración por hardware y overlay gasta bastante; desactívalos si no juegas.":
        "Discord with hardware acceleration and overlay uses quite a lot; turn them off if you are not gaming.",
    "Spotify: descarga las listas y desactiva la aceleración por hardware.": "Spotify: download your playlists and turn off hardware acceleration.",
    "OneDrive sincronizando gasta CPU y disco; pausa la sincronización con poca batería.":
        "OneDrive syncing uses CPU and disk; pause syncing when the battery is low.",
    "Dropbox sincronizando gasta CPU y disco; pausa la sincronización con poca batería.":
        "Dropbox syncing uses CPU and disk; pause syncing when the battery is low.",
    "El indexador de Windows trabaja tras instalar cosas; se calma solo al terminar.":
        "The Windows indexer works after installing things; it calms down when it finishes.",
    "El antivirus de Windows está analizando; programa los análisis con el portátil enchufado.":
        "Windows antivirus is scanning; schedule scans for when the laptop is plugged in.",
    "Spotlight está indexando; suele pasar tras actualizar y termina solo.": "Spotlight is indexing; this usually happens after updating and ends by itself.",
    "Fotos está analizando la biblioteca; mejor hacerlo enchufado.": "Photos is analyzing the library; better to do it plugged in.",
    "Steam en segundo plano descarga y actualiza: ciérralo si no vas a jugar.":
        "Steam downloads and updates in the background: close it if you are not going to play.",
    "Docker mantiene una máquina virtual encendida: ciérralo si no lo usas.": "Docker keeps a virtual machine running: close it if you don't use it.",
    "VS Code con muchas extensiones puede gastar CPU; revisa las que no uses.": "VS Code with many extensions can use CPU; review the ones you don't use.",
    # --- bandeja
    "Abrir Salud de la batería": "Open Battery Health", "Salir": "Quit",
    "Batería al {} %. Desenchufa el cargador para alargar su vida.": "Battery at {} %. Unplug the charger to extend its life.",
    "Batería al {} %. Enchufa el cargador: bajar de aquí la desgasta.": "Battery at {} %. Plug in the charger: going lower wears it.",
    "La batería está a {} °C. Deja respirar las rejillas y evita usarlo sobre la cama o las piernas: el calor la "
    "desgasta mucho.":
        "The battery is at {} °C. Let the vents breathe and avoid using it on the bed or your lap: heat wears it a lot.",
}

_PLANTILLAS: list[tuple[re.Pattern, str]] = []


def fijar(idioma: str) -> None:
    global _idioma
    _idioma = idioma if idioma in ("es", "en") else "es"


def actual() -> str:
    return _idioma


def _plantillas():
    if not _PLANTILLAS:
        # Las plantillas con más texto fijo primero: son las más concretas.
        for es, en in sorted(EN.items(), key=lambda par: -len(par[0].replace("{}", ""))):
            if "{}" in es:
                patron = "^" + re.escape(es).replace(r"\{\}", "(.+?)") + "$"
                _PLANTILLAS.append((re.compile(patron, re.S), en))
    return _PLANTILLAS


def _uno(texto: str) -> str | None:
    if texto in EN:
        return EN[texto]
    for patron, en in _plantillas():
        m = patron.match(texto)
        if m:
            return en.format(*(t(g) for g in m.groups()))
    return None


def t(texto):
    """Traduce `texto` al idioma elegido (en español lo devuelve igual)."""
    if _idioma == "es" or not isinstance(texto, str) or not texto.strip():
        return texto
    limpio = texto.strip()
    previo, final = texto[: len(texto) - len(texto.lstrip())], texto[len(texto.rstrip()):]
    r = _uno(limpio)
    if r is not None:
        return previo + r + final
    for sep in ("\n", "   ·   ", " · "):
        if sep in limpio:
            return previo + sep.join(t(p) for p in limpio.split(sep)) + final
    frases = re.split(r"(?<=[.!?])\s+(?=[A-ZÁÉÍÓÚ¿0-9])", limpio)
    if len(frases) > 1:
        return previo + " ".join(_por_frases(frases)) + final
    if "; " in limpio:
        return previo + "; ".join(t(p) for p in limpio.split("; ")) + final
    clave, sep, valor = limpio.partition(": ")
    if sep and clave in EN:  # "Plan de energía: Equilibrado"
        return previo + EN[clave] + sep + t(valor) + final
    return texto


def _por_frases(frases: list[str]) -> list[str]:
    """Traduce agrupando frases seguidas: algunas entradas tienen más de una frase."""
    salida, i = [], 0
    while i < len(frases):
        for j in range(len(frases), i, -1):
            junto = " ".join(frases[i:j])
            # Varias frases juntas solo si son una entrada exacta; las plantillas, frase a frase.
            r = EN.get(junto) if j > i + 1 else _uno(junto)
            if r is not None:
                salida.append(r)
                i = j
                break
        else:
            salida.append(t(frases[i]) if len(frases) > 1 else frases[i])
            i += 1
    return salida
