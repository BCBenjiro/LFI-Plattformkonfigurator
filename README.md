# Vertriebskonfigurator Landwirtschaft V2.9

Streamlit-Prototyp zur Entscheidungsunterstützung für den Vertrieb landwirtschaftlicher Lebensmittel/Nahrungsmittel.

## Start

```powershell
python -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

## Neu in V2.9

- Linke Sidebar entfernt; Navigation oben über die Reiter **Konfiguration** und **Methodik & Bewertungslogik**.
- Fragebogen-Fortschritt als fixierter Fortschrittsbalken oben im Fragebogen.
- Frage **3a Kühlung** erscheint nur noch bei gekühlten/tiefgekühlten Haltbarkeitsklassen.
- Antwortoptionen zeigen keine Punktwerte mehr; die Punkte werden nur intern berechnet.
- Exportfunktion erzeugt jetzt einen gestalteten **PDF-Ergebnisbericht** statt einer Markdown-Datei.
- Nach dem ersten Generieren bleibt der Ergebnisbereich inklusive PDF-Download verfügbar; die Empfehlung muss für den Download nicht erneut generiert werden.
- Antworttabelle zeigt sauber getrennt **Nr.** und **Frage**.

## Bereits enthalten aus V2.7

- Klarere Kurzdiagnose im Ergebnisbereich.
- Anbieter in Kategorien: direkt passend, passend mit Prüfung, ergänzend, später möglich, aktuell nicht passend.
- Stärker erklärtes Matchmaking pro Anbieter.
- Priorisierter Maßnahmenplan.
- Validierungswarnungen bei widersprüchlichen/riskanten Angaben.
- Bessere Behandlung, wenn keine direkte Anbieterempfehlung möglich ist.
- Eigene Methodik-Seite.
- Stärker dynamisierte Antwortoptionen.
- Robuste Logo-Anzeige auch bei SVG/JPEG/WebP mit falscher Dateiendung.

## Hinweis

Der Konfigurator ist ein Studienprojekt-Prototyp. Er ersetzt keine rechtliche, steuerliche oder betriebswirtschaftliche Einzelfallprüfung.
