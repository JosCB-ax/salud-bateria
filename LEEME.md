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

## Usarlo desde Python (para desarrollo)

Necesitas Python 3.10 o posterior:

```bash
pip install psutil
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
- **Ajustes de energía**: plan de energía, brillo, modo de bajo consumo.

## Archivos

| Archivo | Para qué |
|---|---|
| `app.py` | la ventana del programa (lo que abre el acceso directo) |
| `salud_bateria.py` | versión de terminal y opciones de la línea de órdenes |
| `lectores.py` | lectura de la batería, un lector por sistema operativo |
| `consumo.py` | procesos que más consumen y ajustes de energía |
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
