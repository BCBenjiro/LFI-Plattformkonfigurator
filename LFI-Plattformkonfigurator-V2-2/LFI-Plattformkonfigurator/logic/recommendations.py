from logic.provider_matching import answer_value, has_any


def classify_main_sales_path(provider_results: list[dict]) -> dict:
    """Leitet aus den besten geeigneten Anbietern einen Haupt-Vertriebsweg ab."""
    eligible = [provider for provider in provider_results if provider["eligible"]]

    if not eligible:
        return {
            "title": "Noch kein konkreter Anbieter aktuell geeignet",
            "reason": "Mehrere harte Voraussetzungen fehlen. Der Konfigurator zeigt deshalb zuerst Maßnahmen zur Verbesserung.",
        }

    # Vertriebsweg anhand der besten Anbieterklasse ableiten
    top = eligible[0]
    top_type = top["platform_type"]

    if top_type == "Kooperative Vermarktungsorganisation":
        return {
            "title": "Kooperative Vermarktungsorganisation",
            "reason": (
                f"Der beste aktuelle Anbieter-Fit liegt bei {top['name']} ({top['fit_percent']:.1f} %). "
                "Das spricht für gemeinsame Vermarktung über eine bestehende Erzeugerorganisation, Genossenschaft oder ähnliche Struktur."
            ),
        }

    if top_type == "Partnerbasiertes Vertriebsnetzwerk":
        return {
            "title": "Partnerbasiertes Vertriebsnetzwerk",
            "reason": (
                f"Der beste aktuelle Anbieter-Fit liegt bei {top['name']} ({top['fit_percent']:.1f} %). "
                "Das spricht dafür, Vertrieb, Sichtbarkeit, Logistik, B2B-Zugang oder Qualitätskommunikation nicht komplett allein aufzubauen."
            ),
        }

    return {
        "title": "Online-Marktplatz / Direktvermarktungsplattform",
        "reason": (
            f"Der beste aktuelle Anbieter-Fit liegt bei {top['name']} ({top['fit_percent']:.1f} %). "
            "Das spricht für eine bestehende Plattform zur Direktvermarktung oder zum digitalen Produktvertrieb."
        ),
    }


def build_general_actions(section_scores: dict, answers: dict) -> list[str]:
    """Ergänzende Maßnahmen unabhängig von einem konkreten Anbieter."""
    actions = []

    def add(action: str):
        if action not in actions:
            actions.append(action)

    if section_scores["Produkt- und Regulierungsfit"]["percent"] <= 66:
        add("Produktangaben, Kennzeichnung, Qualitätssiegel und Produktstammdaten weiter vorbereiten.")

    if section_scores["Operative Verkaufsfähigkeit"]["percent"] <= 66:
        add("Produktfotos, Produkttexte, Verpackung, Übergabeprozess und Lieferzuverlässigkeit verbessern.")

    if section_scores["Kooperations- und Bündelungsfähigkeit"]["percent"] <= 66:
        add("Kooperationsbereitschaft, gemeinsame Qualitätsregeln und mögliche Partnerbetriebe klären.")

    if section_scores["Finanzierungs- und Entwicklungsfähigkeit"]["percent"] <= 66:
        add("Kleine Einstiegsvarianten, bestehende Plattformen und gegebenenfalls Fördermöglichkeiten prüfen.")

    if answer_value(answers, "budget") in ["lt500", "500_2500"]:
        add("Bei niedrigem Budget zuerst Sichtbarkeit/Leadplattformen oder bestehende Marktplätze nutzen statt eigene Plattform aufzubauen.")

    if answer_value(answers, "funding_willingness") in ["funding", "funding_equity", "credit_possible"]:
        add("Förderberatung vorbereiten: Investitionsbedarf, Zielgruppe, Produktliste und erwarteten Mehrwert dokumentieren.")

    if has_any(answers, "platform_needs", ["shared_processing"]):
        add("Zusammenarbeit bei Schlachtung, Zerlegung oder Vakuumierung prüfen: mögliche Partnerbetriebe oder Dienstleister identifizieren.")

    if answer_value(answers, "timeline") == "immediately" and section_scores["Produkt- und Regulierungsfit"]["percent"] <= 66:
        add("Bei sofortigem Start und fehlenden Voraussetzungen zunächst einfache Sichtbarkeitskanäle statt komplexer Verkaufsplattform nutzen.")

    return actions
