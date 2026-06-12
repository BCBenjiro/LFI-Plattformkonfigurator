from data.questions import QUESTIONS, SECTION_WEIGHTS


def get_answer_score(answer: dict) -> int | None:
    """Gibt den Score einer Antwort zurück. Bei Mehrfachauswahl zählt der höchste ausgewählte Reifegrad."""
    if not answer:
        return None

    if "selected_options" in answer:
        scores = [opt.get("score") for opt in answer["selected_options"] if opt.get("score") is not None]
        return max(scores) if scores else None

    score = answer.get("score")
    return int(score) if score is not None else None


def get_answer_value(answer: dict) -> str:
    if not answer:
        return ""
    return str(answer.get("value", ""))


def get_answer_labels(answer: dict) -> str:
    if not answer:
        return "-"
    if "selected_options" in answer:
        labels = [opt["label"] for opt in answer["selected_options"]]
        return ", ".join(labels) if labels else "-"
    return answer.get("label", "-")


def format_percent(value: float) -> str:
    return f"{value:.1f} %"


def _is_scored_question(question: dict, answers: dict) -> bool:
    if not question.get("scored", False):
        return False
    if question["key"] not in answers:
        return False
    return get_answer_score(answers[question["key"]]) is not None


def calculate_section_scores(answers: dict) -> dict:
    """
    Berechnet pro Bewertungsbereich nur die echten Reifegradfragen.
    Filterfragen, K.O.-Fragen und Präferenzfragen werden nicht in den Bereichsscore gezählt.
    """
    section_scores = {
        section: {"points": 0, "max_points": 0, "percent": 0.0}
        for section in SECTION_WEIGHTS.keys()
    }

    for question in QUESTIONS:
        if not _is_scored_question(question, answers):
            continue

        section = question["section"]
        key = question["key"]
        score = get_answer_score(answers[key])

        section_scores[section]["points"] += score
        section_scores[section]["max_points"] += 5

    for section, values in section_scores.items():
        if values["max_points"] > 0:
            values["percent"] = values["points"] / values["max_points"] * 100
        else:
            values["percent"] = 0.0

    return section_scores


def calculate_raw_total(section_scores: dict) -> tuple[int, int, float]:
    total_points = sum(values["points"] for values in section_scores.values())
    max_points = sum(values["max_points"] for values in section_scores.values())
    raw_percent = total_points / max_points * 100 if max_points else 0.0
    return total_points, max_points, raw_percent


def calculate_weighted_total(section_scores: dict) -> float:
    weighted_percent = 0.0

    for section, weight in SECTION_WEIGHTS.items():
        weighted_percent += section_scores[section]["percent"] * weight

    return weighted_percent


def classify_overall_readiness(weighted_percent: float, section_scores: dict) -> dict:
    """
    Bewertet, ob ein digitaler/kooperativer Vertriebsweg aktuell realistisch ist.
    Wichtig: Das ist noch keine Anbieterempfehlung.
    """
    product_percent = section_scores["Produkt- und Regulierungsfit"]["percent"]
    operations_percent = section_scores["Operative Verkaufsfähigkeit"]["percent"]

    if product_percent <= 33:
        return {
            "level": "low",
            "is_recommended": False,
            "status": "Vertrieb aktuell nur eingeschränkt empfehlenswert",
            "recommendation": "Zuerst Produkt-, Kennzeichnungs- und Qualitätsvoraussetzungen klären.",
            "reason": (
                "Der Produkt- und Regulierungsfit ist sehr niedrig. Das bedeutet: Kennzeichnung, "
                "Produktdaten, Qualitätssicherung oder Handelstauglichkeit sind noch nicht ausreichend vorbereitet."
            ),
            "next_steps": [
                "Zielprodukt und Haltbarkeit klar festlegen",
                "Kennzeichnung, Herkunft, MHD und Allergene vorbereiten",
                "Zertifizierungen oder Qualitätssiegel prüfen",
                "bei professionellem Handel EAN/GTIN und Produktstammdaten vorbereiten",
                "danach Anbieter-Fit erneut bewerten",
            ],
        }

    if operations_percent <= 33:
        return {
            "level": "low",
            "is_recommended": False,
            "status": "Vertrieb aktuell organisatorisch riskant",
            "recommendation": "Zuerst operative Verkaufsfähigkeit verbessern.",
            "reason": (
                "Die operative Verkaufsfähigkeit ist sehr niedrig. Ohne Produktfotos, Verpackung, Logistik, "
                "Personal oder Lieferzuverlässigkeit ist eine professionelle Plattformnutzung riskant."
            ),
            "next_steps": [
                "Produktfotos und Produkttexte vorbereiten",
                "Verpackung und Übergabeprozess definieren",
                "Zeit- und Personalverantwortung klären",
                "kleinen Test mit Abholung oder Sichtbarkeitsplattform starten",
                "später professionellere Anbieter prüfen",
            ],
        }

    if weighted_percent <= 33:
        return {
            "level": "low",
            "is_recommended": False,
            "status": "Vertriebsplattform aktuell nicht empfehlenswert",
            "recommendation": "Voraussetzungen aufbauen und zunächst mit einfachen Sichtbarkeitskanälen starten.",
            "reason": "Der gewichtete Gesamtscore liegt im unteren Bereich.",
            "next_steps": [
                "kritische Bereiche identifizieren",
                "niedrigschwellige Sichtbarkeit prüfen",
                "Beratung und Fördermöglichkeiten prüfen",
                "nach Verbesserungen erneut bewerten",
            ],
        }

    if weighted_percent <= 66:
        return {
            "level": "medium",
            "is_recommended": True,
            "status": "Vertriebsweg möglich, aber Voraussetzungen verbessern",
            "recommendation": "Bestehende Anbieter mit niedriger Einstiegshürde oder Pilotphase nutzen.",
            "reason": "Der gewichtete Gesamtscore liegt im mittleren Bereich. Einige Voraussetzungen sind vorhanden, andere noch ausbaufähig.",
            "next_steps": [
                "Top-Anbieter prüfen",
                "fehlende K.O.-Kriterien gezielt verbessern",
                "kleinen Pilot mit realen Produkten starten",
                "nach 1–3 Monaten erneut bewerten",
            ],
        }

    return {
        "level": "high",
        "is_recommended": True,
        "status": "Vertriebsweg grundsätzlich empfehlenswert",
        "recommendation": "Konkrete Anbieter können kontaktiert und ein Pilot kann gestartet werden.",
        "reason": "Der gewichtete Gesamtscore liegt im oberen Bereich. Produkt, Vertrieb, operative Fähigkeit und Kooperation sind gut vorbereitet.",
        "next_steps": [
            "Top-Anbieter kontaktieren",
            "Produktdaten und Unterlagen finalisieren",
            "Pilot mit begrenztem Sortiment starten",
            "Ergebnisse messen und Anbieter-Fit nachschärfen",
        ],
    }


def get_critical_factors(section_scores: dict) -> list[str]:
    critical_factors = []

    for section, values in section_scores.items():
        if values["max_points"] == 0:
            continue
        percent = values["percent"]
        if percent <= 33:
            critical_factors.append(f"{section}: kritisch niedrig ({format_percent(percent)})")
        elif percent <= 66:
            critical_factors.append(f"{section}: verbesserungswürdig ({format_percent(percent)})")

    return critical_factors


def build_weighting_table(section_scores: dict) -> list[dict]:
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
                "Beitrag zum Gesamtscore": format_percent(contribution),
            }
        )

    return rows


def build_answer_table(answers: dict) -> list[dict]:
    rows = []

    for question in QUESTIONS:
        key = question["key"]
        if key not in answers:
            continue
        answer = answers[key]
        score = get_answer_score(answer)
        rows.append(
            {
                "Nr.": question["title"],
                "Bereich": question["section"],
                "Antwort": get_answer_labels(answer),
                "Punkte": score if score is not None else "Filter / K.O. / Präferenz",
            }
        )

    return rows
