# Bildschirm-Werkzeug für den Mac

Ein Symbol in der Menüleiste mit zwei Funktionen:

1. **Screenshot aufnehmen und bearbeiten:** Bereich oder ganzen Bildschirm aufnehmen, dann mit Rahmen, Kreis, Pfeil, Linie, Stift, Textmarker und Text markieren und als PNG speichern oder in die Zwischenablage kopieren.
2. **Mauszeiger hervorheben:** Ein gelber Leuchtkreis folgt dem Mauszeiger, damit Zuschauer ihn bei Bildschirmübertragungen besser sehen. Beim Klicken wird der Kreis rot.

Alles läuft lokal auf dem Mac, ohne Claude und ohne Internet.

## Einrichtung (einmalig)

```bash
cd screenshot-tool
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Alternativ als normale App bauen (kein Terminal mehr nötig):

```bash
./build_app.sh
```

Danach liegt `dist/Bildschirm-Werkzeug.app` im Ordner. In den Ordner Programme ziehen und beim ersten Start mit Rechtsklick > Öffnen starten, weil die App nicht von Apple signiert ist.

## Berechtigungen (Systemeinstellungen > Datenschutz & Sicherheit)

| Berechtigung | Wofür |
|---|---|
| Bildschirm- und Systemaudioaufnahme | Screenshots |
| Eingabeüberwachung | Tastenkürzel und rote Klick-Anzeige |

Nach dem Erteilen die App neu starten. Ohne Eingabeüberwachung funktionieren Menü und Leuchtkreis trotzdem, nur die Tastenkürzel und die Klick-Farbe nicht.

## Bedienung

- **Menüleistensymbol:** Bereich aufnehmen, ganzen Bildschirm aufnehmen, Mauszeiger hervorheben, Ordner öffnen, Beenden.
- **Tastenkürzel:** `Ctrl+Alt+S` Bereich aufnehmen, `Ctrl+Alt+M` Mauszeiger-Hervorhebung ein/aus. Mit `--no-hotkeys` abschaltbar.
- **Editor:** Werkzeug oben wählen und im Bild ziehen. Farbe und Stärke einstellbar. `Cmd+Z` macht den letzten Schritt rückgängig, `Cmd+S` speichert, `Cmd+C` kopiert.
- **Speicherort:** Standardmäßig `~/Pictures/Screenshots`, änderbar mit `--save-dir ORDNER`.

## Bekannte Grenzen

- Der Leuchtkreis erscheint nicht über Programmen im macOS-Vollbildmodus. Für Bildschirmübertragungen ein Fenster nicht im Vollbild, sondern maximiert nutzen.
- Entwickelt in einer Linux-Umgebung ohne Mac. Getestet sind hier nur der Editor (Zeichnen, Rückgängig, Speichern) und der Leuchtkreis ohne Bildschirm. Aufnahme mit `screencapture`, Tastenkürzel, Menüleistensymbol und das Bauen der App sind auf dem Mac noch zu prüfen.

## Tests

```bash
QT_QPA_PLATFORM=offscreen python -m unittest discover -s tests -v
```
