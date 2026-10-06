#!/bin/sh
pkill -f "SaludBateria/SaludBateria" 2>/dev/null || true
rm -rf "$HOME/.local/share/SaludBateria" "$HOME/.local/bin/salud-bateria" \
       "$HOME/.local/share/applications/salud-bateria.desktop" "$HOME/.config/autostart/salud-bateria.desktop"
echo "Salud de la batería se ha desinstalado."
