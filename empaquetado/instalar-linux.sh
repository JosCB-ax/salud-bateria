#!/bin/sh
# Instala Salud de la batería para el usuario actual (sin necesidad de root).
set -e
cd "$(dirname "$0")"
DESTINO="$HOME/.local/share/SaludBateria"
mkdir -p "$DESTINO" "$HOME/.local/bin" "$HOME/.local/share/applications"
cp SaludBateria icono.png "$DESTINO/"
chmod +x "$DESTINO/SaludBateria"
ln -sf "$DESTINO/SaludBateria" "$HOME/.local/bin/salud-bateria"
cat > "$HOME/.local/share/applications/salud-bateria.desktop" <<FIN
[Desktop Entry]
Type=Application
Name=Salud de la batería
Comment=Salud de la batería, consejos y qué consume más
Exec=$DESTINO/SaludBateria
Icon=$DESTINO/icono.png
Categories=Utility;System;
FIN
echo "Instalado. Búscalo en el menú de aplicaciones como «Salud de la batería»."
