# LFI Plattformkonfigurator

Streamlit-Prototyp zur Entscheidungsunterstützung für den Vertrieb landwirtschaftlicher Produkte und Verkaufskooperationen in Österreich.

## Funktionen

- Bewertet Produktfit, Vertriebskanal, operative Verkaufsfähigkeit, Kooperation und Finanzierung.
- Nutzt 1–5-Punkte nur bei echten Reifegradfragen.
- Nutzt Filter-, K.O.- und Präferenzfragen ohne Punkteskala, z. B. Produktgruppe, Zielkunden oder Zertifizierungen.
- Empfiehlt reale Anbieter mit Status und Prozentwert.
- Zeigt erfüllte Kriterien, fehlende Kriterien, K.O.-Gründe und Maßnahmenplan.
- Versteckt Folgefragen, wenn sie nicht relevant sind, z. B. Kooperationsfragen oder Förderfragen.

## Installation

```powershell
python -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Starten

```powershell
python -m streamlit run app.py
```
