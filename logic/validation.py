"""Validierungswarnungen für widersprüchliche oder riskante Angaben."""


def answer_values(answers: dict, key: str) -> list[str]:
    answer = answers.get(key)
    if not answer:
        return []
    if "values" in answer:
        return [value for value in answer["values"] if value is not None]
    value = answer.get("value")
    return [] if value is None else [str(value)]


def answer_value(answers: dict, key: str, default: str = "") -> str:
    values = answer_values(answers, key)
    return values[0] if values else default


def has_any(answers: dict, key: str, values: list[str]) -> bool:
    return bool(set(answer_values(answers, key)).intersection(values))


def answer_score(answers: dict, key: str, default: int = 0) -> int:
    answer = answers.get(key)
    if not answer:
        return default
    if "selected_options" in answer:
        scores = [opt.get("score") for opt in answer["selected_options"] if opt.get("score") is not None]
        return max(scores) if scores else default
    score = answer.get("score")
    return int(score) if score is not None else default


def build_validation_warnings(answers: dict) -> list[dict]:
    """Erzeugt Hinweise, wenn Antworten fachlich widersprüchlich oder riskant wirken."""
    warnings: list[dict] = []

    def add(title: str, text: str, severity: str = "warning"):
        item = {"title": title, "text": text, "severity": severity}
        if item not in warnings:
            warnings.append(item)

    product_group = answer_value(answers, "product_group")
    shelf_life = answer_value(answers, "shelf_life")
    cold_chain = answer_value(answers, "cold_chain")
    processing_organizer = answer_value(answers, "processing_organizer")
    timeline = answer_value(answers, "timeline")
    offer_regularity = answer_value(answers, "offer_regularity")
    cooperation_model = answer_value(answers, "cooperation_model")

    # Kühlung/Haltbarkeit/Logistik
    if cold_chain == "none" and shelf_life in {"chilled_few_days", "chilled_weeks", "frozen"}:
        add(
            "Kühlung und Haltbarkeit passen nicht zusammen",
            "Es wurde keine Kühlung angegeben, die Haltbarkeit beschreibt aber gekühlte oder tiefgekühlte Ware. Bitte Angaben prüfen.",
        )

    if cold_chain in {"chilled", "frozen", "mixed"} and has_any(answers, "handover", ["parcel_shipping"]):
        add(
            "Paketversand bei Kühlpflicht",
            "Bei Kühlpflicht sollte normaler Paketversand nicht als Übergabeform genutzt werden. Kühlversand oder externe Logistik ist passender.",
        )

    if cold_chain == "none" and has_any(answers, "handover", ["cold_shipping"]):
        add(
            "Kühlversand trotz keiner Kühlpflicht",
            "Es wurde keine Kühlung angegeben, aber Kühlversand ausgewählt. Prüfe, ob Kühlung wirklich notwendig ist.",
            severity="info",
        )

    # Fleisch/Fisch/Wild braucht meistens klare Verarbeitung/Verpackung
    if product_group == "meat_fish_wild" and processing_organizer == "none":
        add(
            "Verarbeitung bei Fleisch/Fisch/Wild prüfen",
            "Bei Fleisch, Fisch oder Wild ist meist Schlachtung, Zerlegung, Vakuumierung oder Kühlkette relevant. Wenn das bereits durch einen Partner gelöst ist, sollte dies angegeben werden.",
        )

    if product_group == "meat_fish_wild" and answer_score(answers, "packaging") <= 2:
        add(
            "Verpackung bei Fleisch/Fisch/Wild noch schwach",
            "Für Fleisch, Fisch oder Wild erwarten viele Vertriebswege verkaufsfertige, vakuumierte oder gekühlte Verpackung.",
        )

    # B2B braucht Planbarkeit und Zuverlässigkeit
    if has_any(answers, "target_customers", ["large_kitchens", "gastronomy", "retail"]) and offer_regularity in {"irregular"}:
        add(
            "B2B-Zielgruppe und unregelmäßiges Angebot",
            "Gastronomie, Großküchen und Handel benötigen meist planbare Mengen und Liefertermine. Ein sehr unregelmäßiges Angebot erschwert diese Vertriebswege.",
        )

    if has_any(answers, "target_customers", ["large_kitchens", "gastronomy", "retail"]) and answer_score(answers, "reliable_delivery") <= 2:
        add(
            "Lieferzuverlässigkeit für B2B kritisch",
            "Bei Gastronomie, Großküchen oder Handel ist geringe Lieferzuverlässigkeit ein Risiko. Dafür sollten Ersatz- oder Partnerstrukturen geprüft werden.",
        )

    # Sofortige Umsetzung mit niedriger Vorbereitung
    if timeline == "immediately" and answer_score(answers, "labeling_ready") <= 2:
        add(
            "Sofortstart trotz schwacher Kennzeichnung",
            "Für einen sofortigen Start sollten Kennzeichnung, Herkunft, MHD und Allergene mindestens für den Direktverkauf vorbereitet sein.",
        )

    if timeline == "immediately" and answer_score(answers, "photos_texts") <= 2:
        add(
            "Sofortstart trotz schwacher Produktpräsentation",
            "Für digitale Anbieter sind Produktfotos und Produkttexte wichtig. Bei sofortigem Start eher einfache Sichtbarkeit oder Abholung nutzen.",
            severity="info",
        )

    # Kooperationen
    if cooperation_model != "alone" and answer_value(answers, "common_rules") in {"no", "rather_no"}:
        add(
            "Kooperation ohne gemeinsame Regeln schwierig",
            "Gemeinsame Vermarktung benötigt mindestens grundlegende Qualitäts-, Liefer- oder Preisregeln.",
        )

    return warnings
