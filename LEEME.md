# Salud de la batería

Analiza la batería de un portátil: cuánta capacidad ha perdido desde que era
nueva, cuántos ciclos lleva, qué programas están gastando energía ahora mismo y
qué puedes hacer para que dure más. Genera un informe que se abre en el
navegador y también funciona en la terminal.

## Sobre las marcas

La salud de la batería no la da el fabricante del portátil, sino el firmware de
la propia batería, que informa al sistema operativo de su capacidad de fábrica y
de la que admite hoy. Por eso el programa está organizado por sistema operativo
y funciona igual en un Lenovo, un HP, un Dell, un Asus o un MacBook:

| Sistema | De dónde saca los datos |
|---|---|
| Windows | `powercfg /batteryreport /xml`, y WMI (`root\wmi`) como respaldo |
| macOS | `ioreg -rn AppleSmartBattery` y `system_profiler SPPowerDataType` |
| Linux | `/sys/class/power_supply/BAT*` |

Lo único que sí depende de la marca es *limitar la carga al 80 %* en Windows:
eso lo hace la app del fabricante (Lenovo Vantage, MyASUS, Dell Power Manager,
HP en la BIOS, MSI Center, Samsung Settings). El programa lo dice en los consejos.

## Instalarlo como un programa más (Windows)

0. Lo normal es descargar el instalador ya hecho desde la sección Releases de
   GitHub, que se genera solo con cada cambio. Para crearlo a mano:
1. Haz doble clic en `construir_instalador.bat`. Instala lo que necesita
   (PyInstaller e Inno Setup), crea el programa y al final abre la carpeta
   `instalador` con `SaludBateria-Setup-1.0.0.exe`.
2. Ese archivo es el instalador: cópialo a cualquier portátil con Windows 10 u
   11 y ejecútalo. No hace falta tener Python en ese portátil.
3. Queda instalado en Archivos de programa, con icono en el menú Inicio (y en
   el escritorio si lo marcas), y se desinstala desde Configuración >
   Aplicaciones como cualquier otro.

Como el instalador no está firmado digitalmente, la primera vez Windows puede
mostrar "Windows protegió su PC". Pulsa **Más información > Ejecutar de todas
formas**.

Para sacar una versión nueva, cambia el número en `instalador.iss`,
`version.txt` y `app.py`, y vuelve a ejecutar el `.bat`.

## macOS y Linux

En [Releases](https://github.com/JosCB-ax/salud-bateria/releases/latest) también están:

- **macOS** (`SaludBateria-<versión>-macOS-Apple.dmg` para Macs con chip Apple, `-macOS-Intel.dmg` para los Intel): abre el .dmg y arrastra
  SaludBateria a Aplicaciones. La primera vez macOS dirá que no puede verificar al desarrollador
  (el programa no está firmado): ve a Ajustes del Sistema › Privacidad y seguridad › «Abrir igualmente».
- **Linux** (`SaludBateria-<versión>-Linux.tar.gz`): descomprímelo y ejecuta `./instalar-linux.sh`.
  Aparece en el menú de aplicaciones; `./desinstalar-linux.sh` lo quita.

## Usarlo desde Python (para desarrollo)

Necesitas Python 3.10 o posterior:

```bash
pip install -r requirements.txt
```

`psutil` sirve para medir los programas que más consumen y el nivel de carga.
Sin él el resto sigue funcionando.

## Cómo probarlo

```bash
cd salud-bateria

python salud_bateria.py            # analiza y abre el informe en el navegador
python salud_bateria.py --consola  # solo texto en la terminal
python salud_bateria.py --demo     # datos de ejemplo, sin tocar el hardware
python salud_bateria.py --json      # datos en JSON, para guardar un historial
python -m unittest discover -s tests   # pruebas
```

Empieza por `--demo`: así ves el informe completo aunque estés en un ordenador
sin batería. Después lánzalo sin opciones en tu portátil.

En Windows, si el informe sale sin ciclos ni capacidades, abre la consola como
administrador: `powercfg` necesita permisos para escribir el informe.

## Qué te dice

- **Salud** = capacidad de carga completa de hoy ÷ capacidad de fábrica. Por
  encima del 80 % es desgaste normal; por debajo del 60 % conviene plantearse
  el recambio.
- **Ciclos**: una batería de portátil suele estar pensada para entre 300 y 1000
  ciclos antes de bajar al 80 %.
- **Temperatura**: el calor desgasta más que los ciclos. Por encima de 35-40 °C
  el programa te avisa.
- **Programas que más consumen**: uso de CPU medido durante unos segundos,
  agrupando todos los procesos de un mismo programa (Chrome abre uno por
  pestaña). En macOS añade además el impacto energético que calcula el sistema.
  Ningún sistema reparte los vatios por programa sin permisos de
  administrador, así que esto es la mejor aproximación.
- **Autonomía real**: horas que da una carga completa hoy y cuando era nueva,
  calculadas con el consumo medio real de este equipo con batería (historial de
  Windows) y con el consumo de este momento si está desenchufado.
- **Evolución de la salud**: gráfica del historial de capacidad que guarda Windows.
- **Avisos de carga**: un icono junto al reloj avisa al llegar al 80 % (desenchufa)
  y al 20 % (enchufa). Los límites se cambian en Ajustes, y puede iniciarse solo
  con el ordenador (Windows, macOS y Linux).
- **Consumo exacto por programa** (Windows): reparto de la energía de las
  últimas 24 h según el registro de Windows; pide permiso de administrador.
- **Prueba de autonomía guiada**: mide durante 20 minutos (o el tiempo que
  elijas) cuánto gasta el portátil con un uso fijo: ligero, medio o intenso.
- **Historial propio**: el programa guarda la salud cada día y el consumo real
  con batería, así la gráfica y la autonomía funcionan también en Mac y Linux.
- **Modo oscuro**: automático según el sistema, o fijo claro u oscuro en Ajustes.
- **Actualizaciones**: al abrirse busca versiones nuevas en GitHub (una vez al
  día) y se ofrece a instalarlas.
- **Predicción del desgaste**: al ritmo de desgaste del último año, cuándo llegará
  al 80 % y al 60 %.
- **Aviso de temperatura**: el icono avisa si la batería pasa de 40 °C (editable),
  en los equipos cuyo sistema informa de la temperatura de la batería.
- **Modo ahorro con un clic**: plan de ahorro y brillo bajo; se deshace solo al enchufar.
- **Asistente de calibración**: guía los pasos y compara la salud antes y después.
- **Idiomas**: español e inglés (Ajustes > Idioma).
- **Exportar a PDF**: el informe completo con la gráfica.
- **Ajustes de energía**: plan de energía, brillo, modo de bajo consumo.

## Archivos

| Archivo | Para qué |
|---|---|
| `app.py` | la ventana del programa (lo que abre el acceso directo) |
| `salud_bateria.py` | versión de terminal y opciones de la línea de órdenes |
| `lectores.py` | lectura de la batería, un lector por sistema operativo |
| `consumo.py` | procesos que más consumen y ajustes de energía |
| `autonomia.py` | autonomía real con el consumo medido |
| `bandeja.py` | icono de la bandeja y avisos de carga |
| `configuracion.py` | ajustes del usuario e inicio automático |
| `pdf.py` | exportación a PDF |
| `historial.py` | historial propio de salud, consumo y pruebas |
| `prueba.py` | prueba de autonomía guiada |
| `tema.py` | tema claro u oscuro |
| `actualizaciones.py` | búsqueda e instalación de versiones nuevas |
| `prediccion.py` | predicción del desgaste |
| `ahorro.py` | modo ahorro con un clic |
| `idioma.py` | traducción al inglés |
| `consejos.py` | diagnóstico y consejos a partir de lo medido |
| `informe.py` | informe HTML y salida de texto |
| `construir_instalador.bat` | crea el instalador de Windows |
| `instalador.iss` | configuración del instalador (Inno Setup) |
| `version.txt`, `icono.ico` | versión e icono del .exe |
| `tests/` | pruebas con salidas reales de Windows, macOS y Linux |

Las funciones que interpretan la salida de cada sistema (`parse_battery_report_xml`,
`parse_ioreg`, `leer_linux`, `parse_top_macos`) son puras y están probadas con
ejemplos reales, así que se puede trabajar en el programa desde cualquier
sistema sin tener el hardware delante.

## Licencia

© 2026 JosCB. Todos los derechos reservados. Uso gratuito; no se permite venderlo, redistribuir copias
modificadas ni quitar los avisos de autoría. Condiciones completas en [LICENCIA.txt](LICENCIA.txt);
privacidad, términos y fuentes, dentro del programa en Ajustes › Información legal.
Desarrollado con ayuda de herramientas de inteligencia artificial, bajo la dirección y revisión del autor.
