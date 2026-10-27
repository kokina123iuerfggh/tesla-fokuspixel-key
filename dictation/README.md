# Diktat für den Mac

Ein kleines Diktierwerkzeug nach dem Push-to-talk-Prinzip: Taste gedrückt halten, sprechen, loslassen. Der Text wird lokal erkannt und an der Cursorposition eingefügt. Es läuft ohne Cloud-Dienst.

## Einrichtung (einmalig)

1. Python 3.11 oder neuer installieren, zum Beispiel über Homebrew: `brew install python`
2. Im Ordner `dictation` eine virtuelle Umgebung anlegen und die Pakete installieren:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. Berechtigungen in den Systemeinstellungen erteilen (Datenschutz & Sicherheit):
   - **Mikrofon:** das Terminal-Programm, mit dem du das Skript startest
   - **Bedienungshilfen:** dasselbe Programm, damit das Einfügen funktioniert
   - **Eingabeüberwachung:** dasselbe Programm, damit die Taste erkannt wird

   Danach das Terminal neu starten.

## Starten

```bash
source .venv/bin/activate
python dictate.py
```

Beim ersten Start wird das Sprachmodell heruntergeladen. Das dauert einen Moment.

Optionen:

| Option | Standard | Bedeutung |
|---|---|---|
| `--key` | `f5` | Taste zum Halten, z. B. `f6` oder `alt_r` |
| `--model` | `small` | `tiny` (schnell, ungenauer) bis `large-v3` (genau, langsam) |
| `--language` | `de` | Sprachcode, z. B. `en` |

Beispiel: `python dictate.py --model medium --key f6`

## Hinweise

- Das Skript wurde hier in einer Linux-Umgebung ohne Mikrofon erstellt. Das Aufnehmen und Einfügen habe ich dort nicht testen können. Bitte prüfe es einmal auf dem Mac.
- Beim Einfügen wird der bisherige Inhalt der Zwischenablage überschrieben.
- Die Erkennung läuft lokal. Es werden keine Audiodaten an einen Server geschickt.
