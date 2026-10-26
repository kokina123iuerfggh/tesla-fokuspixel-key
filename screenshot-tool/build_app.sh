#!/usr/bin/env bash
# Baut aus dem Werkzeug eine Mac-App in dist/Bildschirm-Werkzeug.app (auf dem Mac ausführen).
set -euo pipefail
cd "$(dirname "$0")"

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt pyinstaller

pyinstaller --noconfirm --windowed --name "Bildschirm-Werkzeug" app.py

APP="dist/Bildschirm-Werkzeug.app"
# Kein Dock-Symbol, nur das Symbol in der Menüleiste
plutil -insert LSUIElement -bool true "$APP/Contents/Info.plist"
# Ad-hoc-Signatur, damit macOS die erteilten Berechtigungen behält
codesign --force --deep --sign - "$APP"

echo "Fertig: $APP"
echo "In den Ordner Programme ziehen, mit Rechtsklick > Öffnen starten."
