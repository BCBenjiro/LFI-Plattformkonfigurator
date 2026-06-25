# Vertriebskonfigurator Landwirtschaft

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

## Aktueller Funktionsstand

- Navigation oben über die Reiter **Konfiguration** und **Methodik & Bewertungslogik**.
- Fragebogen-Fortschritt als fixierter Fortschrittsbalken oben im Fragebogen.
- Durchgängige Nummerierung: Hauptfragen sind fortlaufend nummeriert, abhängige Folgefragen erhalten Buchstaben, z. B. **1a**, **2a**, **19a**.
- Antwortoptionen zeigen keine Punktwerte mehr; die Punkte werden nur intern berechnet.
- Dynamische Antwortoptionen und Folgefragen je nach vorherigen Angaben.
- Exportfunktion erzeugt einen gestalteten **PDF-Ergebnisbericht**.
- Anbieterlogos werden robust angezeigt, auch bei SVG/JPEG/WebP mit falscher Dateiendung.
- Antworttabelle zeigt sauber getrennt **Nr.** und **Frage**.
- Klarere Kurzdiagnose im Ergebnisbereich.
- Anbieter in Kategorien: direkt passend, passend mit Prüfung, ergänzend, später möglich, aktuell nicht passend.
- Stärker erklärtes Matchmaking pro Anbieter.
- Priorisierter Maßnahmenplan.
- Validierungswarnungen bei widersprüchlichen/riskanten Angaben.
- Bessere Behandlung, wenn keine direkte Anbieterempfehlung möglich ist.
- Eigene Methodik-Seite.

## Hinweis

Der Konfigurator ist ein Studienprojekt-Prototyp. Er ersetzt keine rechtliche, steuerliche oder betriebswirtschaftliche Einzelfallprüfung.
