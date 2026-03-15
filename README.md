# filament-calibrator (Deutsche Version)

[![Tests](https://github.com/hyiger/filament-calibrator/actions/workflows/test.yml/badge.svg)](https://github.com/hyiger/filament-calibrator/actions/workflows/test.yml)

> **Hinweis:** Dies ist ein inoffizieller Fork von [hyiger/filament-calibrator](https://github.com/hyiger/filament-calibrator) mit deutscher Benutzeroberfläche.

CLI-Tool-Suite zur Filamentkalibrierung für Prusa-Drucker — mit vollständig **deutscher GUI**.

## Kalibrierungswerkzeuge

- **Temperaturturm** — optimale Drucktemperatur für ein Filament ermitteln
- **Extrusionsmultiplikator** — Wandstärke messen und korrekten EM berechnen
- **Volumetrischer Durchfluss** — maximale Fließrate für Filament/Hotend-Kombination bestimmen
- **Pressure Advance** — optimalen PA/Linear-Advance-Wert finden (Turm- oder Chevron-Methode)
- **Retraktionstest** — optimale Retraktionslänge durch Stringing-Vergleich ermitteln
- **Retraktionsgeschwindigkeit** — optimale Retraktionsgeschwindigkeit bei fester Länge finden
- **Schwundtest** — Achsenschwund (X/Y/Z) mit einem 3-Achsen-Kreuz messen
- **Toleranztest** — Loch-/Zapfenmaßgenauigkeit mit Messschieber prüfen
- **Brückentest** — Brückenqualität bei zunehmenden Spannweiten beurteilen
- **Überhangtest** — Überhangqualität bei zunehmenden Winkeln beurteilen (ohne Stützen)
- **Kühltest** — optimale Lüftergeschwindigkeit durch Variation je Höhenstufe finden

## Schnellstart — Windows (empfohlen)

1. Neueste Version unter [Releases](https://github.com/jandslay/filament-calibrator/releases) herunterladen
2. ZIP entpacken
3. `FilamentCalibrator.exe` starten
4. Browser öffnet sich automatisch auf `http://localhost:8501`

Kein Python-Install erforderlich. **PrusaSlicer** muss installiert sein.

## Installation aus dem Quellcode

Erfordert **Python 3.10 oder 3.12** sowie **PrusaSlicer** im PATH:

```bash
pip install -e ".[gui]"
filament-calibrator-gui
```

## Sprache

Die Benutzeroberfläche erkennt die Systemsprache automatisch.  
Deutsch wird geladen wenn Windows auf Deutsch eingestellt ist.  
Englisch wird als Fallback verwendet wenn keine Übersetzung gefunden wird.

## Unterschiede zum Original

| | Original | Dieser Fork |
|---|---|---|
| Sprache | Englisch | Deutsch (automatisch) |
| Windows-Binary | ✓ | ✓ |
| Funktionsumfang | vollständig | identisch |

## Entwicklung

```bash
pip install -e ".[dev]"
pytest tests/ --cov=src/filament_calibrator --cov-report=term-missing \
  --cov-fail-under=100
```

## Lizenz

GPL-3.0-only — basierend auf [hyiger/filament-calibrator](https://github.com/hyiger/filament-calibrator)
