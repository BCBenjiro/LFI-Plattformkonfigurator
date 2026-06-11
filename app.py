import streamlit as st

# -------------------------------------------------
# LFI Plattformkonfigurator
# Verbesserte Version:
# - 11 Fragen aus dem Fragenkatalog
# - Skala von 1 bis 5 Punkten
# - keine vorausgewählten Antworten
# - Rohscore nach 55-Punkte-System
# - gewichteter Gesamtscore
# - K.O.-Regeln
# - Plattformfähigkeit und Plattformtyp getrennt
# - Plattformtyp aus Governance-Score Frage 8 bis 11
# -------------------------------------------------

st.set_page_config(
    page_title="LFI Plattformkonfigurator",
    page_icon="🚜",
    layout="centered"
)

# -------------------------------------------------
# 1. KONFIGURATION
# -------------------------------------------------

SECTION_WEIGHTS = {
    "Readiness": 0.35,
    "Marktpotenzial": 0.40,
    "Governance": 0.25
}

QUESTIONS = [
    # -------------------------------------------------
    # STUFE 1 – READINESS
    # -------------------------------------------------
    {
        "key": "budget",
        "section": "Readiness",
        "title": "1. Budget",
        "question": "Welches Budget steht für Aufbau und Betrieb der Plattform in den nächsten 12 Monaten zur Verfügung?",
        "options": [
            ("< 2.500 €", 1),
            ("2.500 – 5.000 €", 2),
            ("5.000 – 10.000 €", 3),
            ("10.000 – 25.000 €", 4),
            ("> 25.000 €", 5),
        ],
        "why": "Prüft, ob die Organisation finanziell überhaupt in der Lage ist, Aufbau und Betrieb einer Plattform zu tragen."
    },
    {
        "key": "personal",
        "section": "Readiness",
        "title": "2. Personalressourcen",
        "question": "Wie viele Stunden pro Woche können dauerhaft für Betrieb, Betreuung und Weiterentwicklung der Plattform eingeplant werden?",
        "options": [
            ("< 2 Stunden", 1),
            ("2 – 5 Stunden", 2),
            ("5 – 10 Stunden", 3),
            ("10 – 20 Stunden", 4),
            ("> 20 Stunden", 5),
        ],
        "why": "Plattformen benötigen laufende Betreuung, Pflege, Support und Weiterentwicklung."
    },
    {
        "key": "digital_knowhow",
        "section": "Readiness",
        "title": "3. Digitales Know-how",
        "question": "Wie viele digitale Werkzeuge werden bereits aktiv genutzt?",
        "description": "Beispiele: CRM-System, Newsletter-Tool, Online-Buchungssystem, Mitgliederportal, ERP-System.",
        "options": [
            ("0 Systeme", 1),
            ("1 System", 2),
            ("2 – 3 Systeme", 3),
            ("4 Systeme", 4),
            ("5 oder mehr Systeme", 5),
        ],
        "why": "Zeigt, ob digitale Grundkompetenzen und digitale Prozesse bereits vorhanden sind."
    },

    # -------------------------------------------------
    # STUFE 2 – MARKTPOTENZIAL
    # -------------------------------------------------
    {
        "key": "anbieter",
        "section": "Marktpotenzial",
        "title": "4. Anbieter",
        "question": "Wie viele potenzielle Anbieter könnten die Plattform aktiv nutzen?",
        "options": [
            ("< 10", 1),
            ("10 – 25", 2),
            ("26 – 50", 3),
            ("51 – 100", 4),
            ("> 100", 5),
        ],
        "why": "Eine Plattform braucht eine ausreichend große Angebotsseite."
    },
    {
        "key": "nachfrager",
        "section": "Marktpotenzial",
        "title": "5. Nachfrager",
        "question": "Wie viele potenzielle Nachfrager können realistisch erreicht werden?",
        "options": [
            ("< 50", 1),
            ("50 – 100", 2),
            ("101 – 250", 3),
            ("251 – 500", 4),
            ("> 500", 5),
        ],
        "why": "Eine Plattform braucht eine ausreichend große Nachfrageseite."
    },
    {
        "key": "interaktion",
        "section": "Marktpotenzial",
        "title": "6. Interaktionshäufigkeit",
        "question": "Wie häufig würden Anbieter und Nachfrager voraussichtlich miteinander interagieren?",
        "options": [
            ("seltener als jährlich", 1),
            ("jährlich", 2),
            ("quartalsweise", 3),
            ("monatlich", 4),
            ("wöchentlich oder häufiger", 5),
        ],
        "why": "Je häufiger Interaktionen stattfinden, desto eher lohnt sich ein Plattformmodell."
    },
    {
        "key": "skalierung",
        "section": "Marktpotenzial",
        "title": "7. Skalierungspotenzial",
        "question": "Wie stark könnte die Nutzerzahl innerhalb von drei Jahren wachsen?",
        "options": [
            ("< 10 %", 1),
            ("10 – 25 %", 2),
            ("26 – 50 %", 3),
            ("51 – 100 %", 4),
            ("> 100 %", 5),
        ],
        "why": "Plattformen profitieren stark von Wachstum und Netzwerkeffekten."
    },

    # -------------------------------------------------
    # STUFE 3 – VERTRAUEN & GOVERNANCE
    # -------------------------------------------------
    {
        "key": "datenhoheit",
        "section": "Governance",
        "title": "8. Datenhoheit",
        "question": "Wie wichtig ist es, dass die Organisation Eigentümer und Kontrolleure aller Plattformdaten bleibt?",
        "options": [
            ("unwichtig", 1),
            ("eher unwichtig", 2),
            ("neutral", 3),
            ("wichtig", 4),
            ("sehr wichtig", 5),
        ],
        "why": "Hohe Datenhoheit spricht eher für kontrollierte, verbandliche oder kooperative Plattformmodelle."
    },
    {
        "key": "vertrauen",
        "section": "Governance",
        "title": "9. Vertrauen",
        "question": "Wie wichtig ist gegenseitiges Vertrauen zwischen den Plattformteilnehmern für den Erfolg der Plattform?",
        "options": [
            ("unwichtig", 1),
            ("eher unwichtig", 2),
            ("neutral", 3),
            ("wichtig", 4),
            ("sehr wichtig", 5),
        ],
        "why": "Vertrauen ist besonders relevant, wenn sensible Daten oder langfristige Zusammenarbeit betroffen sind."
    },
    {
        "key": "mitbestimmung",
        "section": "Governance",
        "title": "10. Governance / Mitbestimmung",
        "question": "Wie wichtig ist Mitbestimmung der Mitglieder bei Entscheidungen zur Plattform?",
        "options": [
            ("unwichtig", 1),
            ("eher unwichtig", 2),
            ("neutral", 3),
            ("wichtig", 4),
            ("sehr wichtig", 5),
        ],
        "why": "Starke Mitbestimmung spricht eher für ein Konsortialmodell oder eine kooperative Plattform."
    },
    {
        "key": "datenschutz",
        "section": "Governance",
        "title": "11. Datenschutz",
        "question": "Wie sensibel sind die Daten, die über die Plattform verarbeitet werden sollen?",
        "options": [
            ("öffentliche Informationen", 1),
            ("Kontaktinformationen", 2),
            ("Mitgliederdaten", 3),
            ("Betriebsdaten", 4),
            ("sensible Betriebs-/Finanzdaten", 5),
        ],
        "why": "Je sensibler die Daten, desto wichtiger sind Datenschutz, Kontrolle und klare Governance-Regeln."
    },
]


# -------------------------------------------------
# 2. HILFSFUNKTIONEN
# -------------------------------------------------

def get_score(answer):
    """
    Eine Antwort besteht aus:
    ("Antworttext", Punktzahl)

    Diese Funktion gibt die Punktzahl zurück.
    """
    return answer[1]


def format_percent(value):
    """
    Formatiert Prozentwerte einheitlich.
    """
    return f"{value:.1f} %"


def calculate_section_scores(answers):
    """
    Berechnet pro Bereich:
    - erreichte Punkte
    - maximale Punkte
    - Prozentwert
    """

    section_scores = {}

    for question in QUESTIONS:
        section = question["section"]
        key = question["key"]
        score = get_score(answers[key])

        if section not in section_scores:
            section_scores[section] = {
                "points": 0,
                "max_points": 0,
                "percent": 0
            }

        section_scores[section]["points"] += score
        section_scores[section]["max_points"] += 5

    for section in section_scores:
        points = section_scores[section]["points"]
        max_points = section_scores[section]["max_points"]
        section_scores[section]["percent"] = points / max_points * 100

    return section_scores


def calculate_raw_total(section_scores):
    """
    Berechnet die ungewichtete Gesamtbewertung nach dem 55-Punkte-System.
    """

    total_points = 0
    max_points = 0

    for section in section_scores:
        total_points += section_scores[section]["points"]
        max_points += section_scores[section]["max_points"]

    raw_percent = total_points / max_points * 100

    return total_points, max_points, raw_percent


def calculate_weighted_total(section_scores):
    """
    Berechnet den gewichteten Gesamtscore.

    Formel:
    Readiness-Prozent * 0.35
    + Marktpotenzial-Prozent * 0.40
    + Governance-Prozent * 0.25
    """

    weighted_percent = 0

    for section, weight in SECTION_WEIGHTS.items():
        section_percent = section_scores[section]["percent"]
        weighted_percent += section_percent * weight

    return weighted_percent


def classify_platform_readiness(weighted_percent, section_scores):
    """
    Bewertet, ob eine Plattform aktuell grundsätzlich empfehlenswert ist.

    Wichtig:
    Das ist NICHT der Plattformtyp.
    Hier wird nur geprüft, ob eine Plattform insgesamt sinnvoll erscheint.
    """

    readiness_percent = section_scores["Readiness"]["percent"]
    market_percent = section_scores["Marktpotenzial"]["percent"]

    if readiness_percent <= 33:
        return {
            "level": "low",
            "is_platform_recommended": False,
            "status": "Plattform aktuell nicht empfehlenswert",
            "recommendation": "Zuerst Basis-Digitalisierung und organisatorische Voraussetzungen schaffen.",
            "reason": (
                "Die organisatorische Readiness ist sehr niedrig. Das bedeutet, dass Budget, Personal "
                "oder digitales Know-how aktuell nicht ausreichen, um eine Plattform realistisch aufzubauen "
                "und dauerhaft zu betreiben."
            ),
            "risk": "Hohes Risiko für Fehlinvestition, weil die Umsetzungskapazität fehlt.",
            "next_steps": [
                "Budgetrahmen klären",
                "verantwortliche Personen festlegen",
                "digitale Grundprozesse aufbauen",
                "kleinen Informations-Prototyp testen",
                "Readiness zu einem späteren Zeitpunkt erneut bewerten"
            ],
            "rule": "K.O.-Regel: Readiness ≤ 33 % → keine Plattformempfehlung."
        }

    if market_percent <= 33:
        return {
            "level": "low",
            "is_platform_recommended": False,
            "status": "Komplexes Plattformmodell aktuell nicht empfehlenswert",
            "recommendation": "Zunächst Informations- oder Content-Plattform prüfen.",
            "reason": (
                "Das Marktpotenzial ist sehr niedrig. Für ein zweiseitiges Plattformmodell fehlen aktuell "
                "ausreichend Anbieter, Nachfrager oder regelmäßige Interaktionen."
            ),
            "risk": "Chicken-and-Egg-Problem: Ohne genügend Nutzer auf beiden Seiten entstehen keine stabilen Netzwerkeffekte.",
            "next_steps": [
                "Zielgruppen genauer abgrenzen",
                "Anbieter- und Nachfrageseite getrennt analysieren",
                "Nutzerbedarf validieren",
                "Pilot mit kleiner Zielgruppe durchführen",
                "erst danach Vermittlungs- oder Transaktionsmodell prüfen"
            ],
            "rule": "K.O.-Regel: Marktpotenzial ≤ 33 % → keine komplexe zweiseitige Plattformempfehlung."
        }

    if weighted_percent <= 33:
        return {
            "level": "low",
            "is_platform_recommended": False,
            "status": "Plattform aktuell nicht empfehlenswert",
            "recommendation": "Voraussetzungen schaffen, bevor ein Plattformmodell umgesetzt wird.",
            "reason": (
                "Der gewichtete Gesamtscore liegt im unteren Bereich. Die Voraussetzungen sind insgesamt "
                "noch nicht ausreichend."
            ),
            "risk": "Hohe Wahrscheinlichkeit, dass die Plattform nicht genug genutzt oder nicht dauerhaft betrieben wird.",
            "next_steps": [
                "kritische Schwachstellen identifizieren",
                "interne Ressourcen verbessern",
                "digitale Basisprozesse stärken",
                "kleinen Prototyp ohne komplexe Plattformlogik testen",
                "Bewertung nach Verbesserungen wiederholen"
            ],
            "rule": "Tertile-Auswertung: Gesamtscore ≤ 33 % → Plattform aktuell nicht empfehlenswert."
        }

    elif weighted_percent <= 66:
        return {
            "level": "medium",
            "is_platform_recommended": True,
            "status": "Plattform möglich, aber Voraussetzungen verbessern",
            "recommendation": "Schrittweise Umsetzung mit Pilotphase.",
            "reason": (
                "Der gewichtete Gesamtscore liegt im mittleren Bereich. Eine Plattform ist grundsätzlich denkbar, "
                "aber einzelne Voraussetzungen müssen noch verbessert werden."
            ),
            "risk": "Mittleres Risiko: Ohne gezielte Vorbereitung könnten Akzeptanz, Nutzung oder Betrieb problematisch werden.",
            "next_steps": [
                "Pilotgruppe definieren",
                "wichtigste Plattformfunktionen priorisieren",
                "Governance-Regeln formulieren",
                "Marktseiten gezielt aufbauen",
                "nach Pilotphase Bewertung wiederholen"
            ],
            "rule": "Tertile-Auswertung: 34–66 % → Plattform möglich, Voraussetzungen verbessern."
        }

    else:
        return {
            "level": "high",
            "is_platform_recommended": True,
            "status": "Plattform grundsätzlich empfehlenswert",
            "recommendation": "Plattformmodell kann konkret geplant und pilotiert werden.",
            "reason": (
                "Der gewichtete Gesamtscore liegt im oberen Bereich. Die organisatorischen Voraussetzungen, "
                "das Marktpotenzial und die Governance-Anforderungen sind grundsätzlich ausreichend geklärt."
            ),
            "risk": "Restrisiko liegt vor allem in Umsetzung, Akzeptanz und laufender Pflege.",
            "next_steps": [
                "konkretes Plattformmodell auswählen",
                "technischen Prototyp planen",
                "Governance und Datenschutz dokumentieren",
                "Pilot mit echten Nutzern durchführen",
                "Ergebnisse messen und iterativ verbessern"
            ],
            "rule": "Tertile-Auswertung: 67–100 % → Plattform grundsätzlich empfehlenswert."
        }


def classify_platform_type(section_scores):
    """
    Leitet den Plattformtyp aus dem Governance-Score ab.

    Genutzt werden die Fragen:
    8. Datenhoheit
    9. Vertrauen
    10. Mitbestimmung
    11. Datenschutz
    """

    governance_percent = section_scores["Governance"]["percent"]

    if governance_percent <= 33:
        return {
            "type": "Transaktionsplattform",
            "governance_percent": governance_percent,
            "reason": (
                "Der Governance-Score ist niedrig. Datenhoheit, Mitbestimmung und Datenschutzanforderungen "
                "sind vergleichsweise gering ausgeprägt. Dadurch kann eine eher offene Transaktionsplattform "
                "passend sein."
            ),
            "example": "Beispiel: Plattform zur einfachen Vermittlung von Angeboten und Nachfragen.",
            "warning": None
        }

    elif governance_percent <= 66:
        return {
            "type": "Hybrid-/Konsortialmodell",
            "governance_percent": governance_percent,
            "reason": (
                "Der Governance-Score liegt im mittleren Bereich. Es gibt einen gewissen Bedarf an Kontrolle, "
                "Vertrauen und Mitbestimmung, aber keine vollständige Abschottung. Ein gemeinsames Modell "
                "mehrerer Organisationen oder Verbände kann daher passend sein."
            ),
            "example": "Beispiel: Plattform, die von mehreren Verbänden gemeinsam getragen und gesteuert wird.",
            "warning": None
        }

    else:
        return {
            "type": "Kooperative Plattform",
            "governance_percent": governance_percent,
            "reason": (
                "Der Governance-Score ist hoch. Datenhoheit, Vertrauen, Mitbestimmung und Datenschutz "
                "sind sehr wichtig. Deshalb passt eher ein geschlossenes oder genossenschaftlich organisiertes Modell."
            ),
            "example": "Beispiel: Verbandsinterne oder kooperative Plattform, bei der Mitglieder Kontrolle über Daten und Regeln behalten.",
            "warning": (
                "Public-Third-Party-Plattformen sollten hier kritisch geprüft oder ausgeschlossen werden, "
                "weil die Anforderungen an Kontrolle und Datenhoheit hoch sind."
            )
        }


def get_critical_factors(section_scores):
    """
    Erkennt schwache Bereiche und gibt Hinweise für die Ergebnisinterpretation.
    """

    critical_factors = []

    for section, values in section_scores.items():
        percent = values["percent"]

        if percent <= 33:
            critical_factors.append(
                f"{section}: kritisch niedrig ({format_percent(percent)})"
            )
        elif percent <= 66:
            critical_factors.append(
                f"{section}: verbesserungswürdig ({format_percent(percent)})"
            )

    return critical_factors


def show_score_bar(label, percent):
    """
    Zeigt einen Score mit Progressbar.
    """

    st.write(f"**{label}:** {format_percent(percent)}")
    st.progress(min(max(percent / 100, 0), 1))


def build_weighting_table(section_scores):
    """
    Erstellt eine Tabelle für die transparente Gewichtung.
    """

    rows = []

    for section, weight in SECTION_WEIGHTS.items():
        percent = section_scores[section]["percent"]
        contribution = percent * weight

        rows.append(
            {
                "Bereich": section,
                "Punkte": f"{section_scores[section]['points']} / {section_scores[section]['max_points']}",
                "Prozent": format_percent(percent),
                "Gewichtung": format_percent(weight * 100),
                "Beitrag zum Gesamtscore": format_percent(contribution)
            }
        )

    return rows


def build_answer_table(answers):
    """
    Erstellt eine Tabelle mit allen ausgewählten Antworten.
    """

    rows = []

    for question in QUESTIONS:
        key = question["key"]
        answer_text, score = answers[key]

        rows.append(
            {
                "Nr.": question["title"],
                "Bereich": question["section"],
                "Antwort": answer_text,
                "Punkte": score
            }
        )

    return rows


# -------------------------------------------------
# 3. OBERFLÄCHE
# -------------------------------------------------

st.title("🚜 LFI Plattformkonfigurator")
st.subheader("Digitale Entscheidungsunterstützung für Plattformmodelle")

st.info(
    "Dieser Prototyp bewertet die Plattformfähigkeit anhand eines gewichteten Fragenkatalogs. "
    "Zusätzlich wird ein passender Plattformtyp aus den Governance-Anforderungen abgeleitet."
)

st.divider()

with st.expander("Methodik kurz erklärt", expanded=False):
    st.write(
        """
        Der Konfigurator trennt zwei Entscheidungen:

        **1. Plattformfähigkeit:**  
        Ist eine Plattform aktuell grundsätzlich sinnvoll und realistisch?

        **2. Plattformtyp:**  
        Falls eine Plattform sinnvoll ist: Welcher Plattformtyp passt zu den Governance-Anforderungen?

        Bewertet werden drei Bereiche:

        - **Readiness:** Budget, Personal und digitales Know-how
        - **Marktpotenzial:** Anbieter, Nachfrager, Interaktion und Skalierung
        - **Governance:** Datenhoheit, Vertrauen, Mitbestimmung und Datenschutz

        Zusätzlich verhindern K.O.-Regeln, dass trotz sehr niedriger Readiness oder sehr niedrigem Marktpotenzial
        eine unrealistische Plattformempfehlung ausgegeben wird.
        """
    )

st.header("Fragenkatalog")

answers = {}
current_section = None

for question in QUESTIONS:
    section = question["section"]

    if section != current_section:
        current_section = section
        st.subheader(section)

    st.write(f"**{question['title']}**")
    st.write(question["question"])

    if "description" in question:
        st.caption(question["description"])

    options_with_placeholder = [("Bitte auswählen", None)] + question["options"]

    selected_option = st.selectbox(
        label="Antwort auswählen",
        options=options_with_placeholder,
        format_func=lambda option: option[0] if option[1] is None else f"{option[0]} → {option[1]} Punkte",
        key=question["key"],
        help=question["why"]
    )

    answers[question["key"]] = selected_option

    st.write("")

st.divider()

# -------------------------------------------------
# 4. AUSWERTUNG
# -------------------------------------------------

if st.button("Empfehlung generieren", type="primary"):

    missing_questions = []

    for question in QUESTIONS:
        key = question["key"]
        selected_answer = answers[key]

        if selected_answer[1] is None:
            missing_questions.append(question["title"])

    if missing_questions:
        st.warning("Bitte beantworte zuerst alle Fragen.")
        st.write("Noch offen:")
        for missing in missing_questions:
            st.write(f"• {missing}")
        st.stop()

    section_scores = calculate_section_scores(answers)
    raw_total_points, raw_max_points, raw_percent = calculate_raw_total(section_scores)
    weighted_percent = calculate_weighted_total(section_scores)

    platform_readiness = classify_platform_readiness(weighted_percent, section_scores)
    platform_type = classify_platform_type(section_scores)
    critical_factors = get_critical_factors(section_scores)

    # -------------------------------------------------
    # Ergebnisübersicht
    # -------------------------------------------------

    st.header("📊 Ergebnis")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            label="Rohpunkte",
            value=f"{raw_total_points} / {raw_max_points}"
        )

    with col2:
        st.metric(
            label="Gewichteter Score",
            value=format_percent(weighted_percent)
        )

    with col3:
        st.metric(
            label="Governance-Score",
            value=format_percent(platform_type["governance_percent"])
        )

    st.divider()

    # -------------------------------------------------
    # Plattformfähigkeit
    # -------------------------------------------------

    st.subheader("1. Plattformfähigkeit")

    if platform_readiness["level"] == "low":
        st.error(platform_readiness["status"])
    elif platform_readiness["level"] == "medium":
        st.warning(platform_readiness["status"])
    else:
        st.success(platform_readiness["status"])

    st.write(f"**Empfehlung:** {platform_readiness['recommendation']}")

    st.write("**Begründung:**")
    st.write(platform_readiness["reason"])

    st.write("**Hauptrisiko:**")
    st.write(platform_readiness["risk"])

    with st.expander("Angewendete Bewertungsregel"):
        st.write(platform_readiness["rule"])

    # -------------------------------------------------
    # Plattformtyp
    # -------------------------------------------------

    st.subheader("2. Plattformtyp")

    if platform_readiness["is_platform_recommended"]:
        st.info(f"Empfohlener Plattformtyp: **{platform_type['type']}**")
    else:
        st.info(f"Langfristig passender Plattformtyp bei verbesserten Voraussetzungen: **{platform_type['type']}**")

    st.write("**Begründung:**")
    st.write(platform_type["reason"])

    st.write("**Beispiel:**")
    st.write(platform_type["example"])

    if platform_type["warning"] is not None:
        st.warning(platform_type["warning"])

    with st.expander("Berechnung des Plattformtyps"):
        st.write(
            "Der Plattformtyp wird aus dem gesamten Governance-Score berechnet, also aus den Fragen 8 bis 11:"
        )
        st.write("• Datenhoheit")
        st.write("• Vertrauen")
        st.write("• Governance / Mitbestimmung")
        st.write("• Datenschutz")

        st.write("")
        st.write("Einteilung:")
        st.write("• 0–33 %: Transaktionsplattform")
        st.write("• 34–66 %: Hybrid-/Konsortialmodell")
        st.write("• 67–100 %: Kooperative Plattform")

    # -------------------------------------------------
    # Detailauswertung
    # -------------------------------------------------

    st.subheader("3. Detailauswertung")

    show_score_bar("Readiness", section_scores["Readiness"]["percent"])
    show_score_bar("Marktpotenzial", section_scores["Marktpotenzial"]["percent"])
    show_score_bar("Governance", section_scores["Governance"]["percent"])

    if critical_factors:
        st.write("**Auffällige Bereiche:**")
        for factor in critical_factors:
            st.write(f"• {factor}")
    else:
        st.success("Keine kritisch niedrigen Bereiche erkannt.")

    # -------------------------------------------------
    # Nächste Schritte
    # -------------------------------------------------

    st.subheader("4. Nächste Schritte")

    for step in platform_readiness["next_steps"]:
        st.write(f"• {step}")

    # -------------------------------------------------
    # Transparenz der Berechnung
    # -------------------------------------------------

    with st.expander("Transparenz der Berechnung anzeigen"):

        st.write("### Rohscore nach 55-Punkte-System")

        st.write(f"Readiness: {section_scores['Readiness']['points']} / {section_scores['Readiness']['max_points']} Punkte")
        st.write(f"Marktpotenzial: {section_scores['Marktpotenzial']['points']} / {section_scores['Marktpotenzial']['max_points']} Punkte")
        st.write(f"Governance: {section_scores['Governance']['points']} / {section_scores['Governance']['max_points']} Punkte")

        st.write("")
        st.write(f"Gesamt: **{raw_total_points} / {raw_max_points} Punkte**")
        st.write(f"Ungewichteter Score: **{format_percent(raw_percent)}**")

        st.write("### Gewichteter Score")

        st.write(
            "Für die finale Plattformfähigkeit wird zusätzlich ein gewichteter Score berechnet. "
            "Dadurch kann Marktpotenzial stärker berücksichtigt werden, weil Plattformen ohne Anbieter, "
            "Nachfrager und Interaktion nicht funktionieren."
        )

        st.code(
            "Gesamtscore = Readiness% × 0.35 + Marktpotenzial% × 0.40 + Governance% × 0.25",
            language="text"
        )

        st.table(build_weighting_table(section_scores))

        st.write(f"Gewichteter Gesamtscore: **{format_percent(weighted_percent)}**")

        st.write("### Interpretation")

        st.write("• 0–33 %: Plattform aktuell nicht empfehlenswert")
        st.write("• 34–66 %: Plattform möglich, Voraussetzungen verbessern")
        st.write("• 67–100 %: Plattform grundsätzlich empfehlenswert")

        st.write("")
        st.caption(
            "Hinweis: Da jede Frage mindestens 1 Punkt erhält, liegt der niedrigste praktisch erreichbare Rohscore "
            "bei 11 von 55 Punkten. Die Prozentbereiche bleiben trotzdem als Reifegradlogik nutzbar."
        )

    # -------------------------------------------------
    # Antworten anzeigen
    # -------------------------------------------------

    with st.expander("Ausgewählte Antworten anzeigen"):
        st.table(build_answer_table(answers))

    st.divider()

    st.caption(
        "Hinweis: Der Plattformkonfigurator ist eine Entscheidungsunterstützung. "
        "Er macht die Bewertungslogik transparent, ersetzt aber keine fachliche Einzelfallprüfung."
    )
