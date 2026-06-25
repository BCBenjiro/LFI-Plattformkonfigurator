from data.providers import PROVIDERS


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


def answer_score(answers: dict, key: str, default: int = 1) -> int:
    answer = answers.get(key)
    if not answer:
        return default

    if "selected_options" in answer:
        scores = [opt.get("score") for opt in answer["selected_options"] if opt.get("score") is not None]
        return max(scores) if scores else default

    score = answer.get("score")
    return int(score) if score is not None else default


def get_hard_blockers(provider: dict, answers: dict) -> list[str]:
    """Anbieter-spezifische K.O.-Regeln. Diese Regeln laufen vor dem Score."""
    provider_id = provider["id"]
    blockers = []

    product_group = answer_value(answers, "product_group")
    animal_origin = answer_value(answers, "animal_origin")
    cold_chain = answer_value(answers, "cold_chain")
    shelf_life = answer_value(answers, "shelf_life")
    ean_data = answer_value(answers, "ean_data")
    sales_area = answer_value(answers, "sales_area")
    offer_regularity = answer_value(answers, "offer_regularity")
    cooperation_model = answer_value(answers, "cooperation_model")
    product_similarity = answer_value(answers, "product_similarity")
    common_rules = answer_value(answers, "common_rules")
    packaging = answer_value(answers, "packaging")

    if provider_id == "nahgenuss":
        if product_group != "meat_fish_wild":
            blockers.append("nahgenuss passt nur für Fleisch, Fisch oder Wild.")
        if not has_any(answers, "certification", ["bio"]) and animal_origin != "wild_free":
            blockers.append("Für Fleisch/Fisch ist bei nahgenuss ein Bio-Zertifikat erforderlich. Wild aus freier Wildbahn ist eine mögliche Ausnahme.")
        if packaging in ["none", "loose"]:
            blockers.append("Für nahgenuss fehlt eine geeignete küchenfertige oder verkaufsfertige Verpackung.")

    elif provider_id == "myproduct":
        if cold_chain != "none":
            blockers.append("myProduct Fulfillment ist ungeeignet, weil die Ware Kühlung benötigt.")
        if shelf_life != "ambient_6_months":
            blockers.append("myProduct Fulfillment setzt ungekühlte Ware mit mindestens 6 Monaten Restlaufzeit voraus.")
        if ean_data != "complete":
            blockers.append("Für myProduct müssen EAN/GTIN und Produktstammdaten vollständig vorhanden sein.")

    elif provider_id == "jazunah":
        if not has_any(answers, "target_customers", ["large_kitchens", "gastronomy"]):
            blockers.append("JA ZU NAH passt primär zu Großküchen, Kantinen oder Gastronomie.")
        if offer_regularity == "irregular":
            blockers.append("Für JA ZU NAH ist ein völlig unregelmäßiges Angebot zu wenig planbar.")
        if answer_score(answers, "reliable_delivery") <= 2:
            blockers.append("Für JA ZU NAH ist die Lieferzuverlässigkeit aktuell zu niedrig.")

    elif provider_id == "paradeisa":
        if sales_area not in ["local", "regional"]:
            blockers.append("Paradeisa passt vor allem zu lokalem oder regionalem Vertrieb.")
        if not has_any(answers, "handover", ["farm_pickup", "pickup_market", "regional_delivery"]) and not has_any(answers, "platform_needs", ["pickup"]):
            blockers.append("Für Paradeisa fehlt aktuell ein passendes Abhol- oder Regionalübergabemodell.")

    elif provider_id == "gutes_vom_bauernhof":
        if not has_any(answers, "target_customers", ["end_customers", "farm_shop"]):
            blockers.append("Gutes vom Bauernhof passt primär zur bäuerlichen Direktvermarktung an Endkunden/Hofladenkunden.")
        if not has_any(answers, "certification", ["ama_qhs", "gutes_vom_bauernhof", "regional_origin"]):
            blockers.append("Für Gutes vom Bauernhof fehlen aktuell passende Qualitäts-/Herkunftsvoraussetzungen wie AMA/QHS oder vergleichbare Nachweise.")
        if common_rules in ["no", "rather_no"]:
            blockers.append("Für Gutes vom Bauernhof muss der Betrieb Qualitätsregeln, Betriebs-Check und Kontrolle akzeptieren.")

    elif provider_id == "biomaps":
        if not has_any(answers, "certification", ["bio"]):
            blockers.append("Biomaps passt nur für Bio-Betriebe beziehungsweise Bio-Direktvermarkter.")
        if not has_any(answers, "target_customers", ["end_customers", "farm_shop"]):
            blockers.append("Biomaps setzt Direktverkauf/Sichtbarkeit Richtung Endkunden voraus.")

    elif provider_id == "abhof":
        if not has_any(answers, "target_customers", ["end_customers", "farm_shop"]):
            blockers.append("AbHof passt primär zu Direktvermarktung an Endkunden oder Hofladenkunden.")
        if not has_any(answers, "platform_needs", ["visibility", "contact_preorder", "pickup", "online_order", "online_payment"]):
            blockers.append("AbHof ist eher Sichtbarkeit, Kontakt, Vorbestellung oder Direktvermarktung, nicht primär B2B/Kooperation.")

    elif provider_id == "direkt_regional":
        if sales_area not in ["local", "regional"]:
            blockers.append("Direkt Regional passt vor allem zu lokalem/regionalem Verkauf.")
        if not has_any(answers, "platform_needs", ["visibility", "contact_preorder"]):
            blockers.append("Direkt Regional ist eher eine Sichtbarkeits-/Leadplattform als ein vollständiger Marktplatz.")

    elif provider_id == "fleischbox":
        if product_group != "meat_fish_wild":
            blockers.append("Fleischbox passt nur zu Fleisch/Fisch-Produkten.")
        if not has_any(answers, "certification", ["bio"]):
            blockers.append("Fleischbox ist auf Bio-Fleisch/Bio-Fisch ausgerichtet; Bio-Zertifizierung fehlt.")

    elif provider_id == "berglandmilch":
        if product_group != "dairy":
            blockers.append("Berglandmilch/Molkereigenossenschaft passt nur für Milch beziehungsweise Milchprodukte.")

    elif provider_id == "lgv":
        if product_group != "fruit_veg":
            blockers.append("LGV Sonnengemüse passt vor allem für Gemüse- beziehungsweise Obst/Gemüse-Betriebe.")
        if offer_regularity not in ["weekly", "daily"]:
            blockers.append("Für LGV-artige Vermarktung fehlen regelmäßige Mengen.")

    elif provider_id == "opst":
        if product_group != "fruit_veg":
            blockers.append("OPST passt vor allem für Obstbetriebe; die Produktgruppe Obst/Gemüse ist nur eine grobe Vorauswahl.")
        if cooperation_model == "alone":
            blockers.append("OPST ist eine Erzeugerorganisation; dafür braucht es grundsätzlich Kooperations-/Organisationsbereitschaft.")

    elif provider_id == "rinderboerse":
        if product_group != "meat_fish_wild":
            blockers.append("Rinderbörse/ARGE Rind passt nur für Rinder/Kälber beziehungsweise Tiervermarktung.")
        if cooperation_model == "alone" and not has_any(answers, "sales_channels_possible", ["joint_farms", "retail", "gastronomy_large_kitchens"]):
            blockers.append("Für die Rinderbörse ist gebündelte beziehungsweise professionelle Tiervermarktung relevanter als reiner Einzel-Endkundenverkauf.")

    # Allgemeine Kooperationsblocker nur bei kooperativen Organisationen
    if provider.get("platform_type") == "Kooperative Vermarktungsorganisation":
        if common_rules in ["no", "rather_no"]:
            blockers.append("Kooperative Vermarktung braucht gemeinsame Qualitäts- und Lieferregeln.")
        if cooperation_model != "alone" and product_similarity == "no":
            blockers.append("Die Produkte sind aktuell zu unterschiedlich, um sauber gemeinsam vermarktet zu werden.")

    return blockers


def calculate_provider_fit(provider: dict, answers: dict) -> tuple[float, int, int, list[str], list[str]]:
    """
    Berechnet den Anbieter-Fit auf Basis der Fit-Regeln.
    Gibt zurück: Prozentwert, erreichte Fit-Punkte, maximale Fit-Punkte, erfüllte Kriterien, nicht erfüllte Fit-Kriterien.
    """
    max_weight = 0
    reached_weight = 0
    matched_reasons = []
    missing_reasons = []

    for rule in provider["fit_rules"]:
        max_weight += rule["weight"]
        selected_values = set(answer_values(answers, rule["key"]))
        allowed_values = set(rule["values"])

        if selected_values.intersection(allowed_values):
            reached_weight += rule["weight"]
            matched_reasons.append(rule["reason"])
        else:
            missing_reasons.append(rule["reason"])

    if max_weight == 0:
        return 0.0, 0, 0, matched_reasons, missing_reasons

    return reached_weight / max_weight * 100, reached_weight, max_weight, matched_reasons, missing_reasons


def build_dynamic_actions(provider: dict, answers: dict, blockers: list[str], missing_reasons: list[str]) -> list[str]:
    """Erzeugt Maßnahmen nur aus tatsächlich fehlenden oder schwachen Punkten."""
    actions = []
    provider_id = provider["id"]

    def add(action: str):
        if action not in actions:
            actions.append(action)

    # K.O.-Gründe als konkrete Verbesserungsrichtung aufgreifen
    for blocker in blockers:
        add(blocker)

    # Allgemeine operative Lücken
    if answer_value(answers, "labeling_ready") in ["none", "partial"]:
        add("Kennzeichnung, Herkunft, MHD, Allergene und rechtliche Angaben vervollständigen.")

    if answer_value(answers, "photos_texts") in ["none", "basic"]:
        add("Produktfotos und Produkttexte verbessern.")

    if answer_value(answers, "packaging") in ["none", "loose", "simple"]:
        add("Verpackung für Verkauf, Abholung oder Versand professionalisieren.")

    if answer_value(answers, "handover") == "not_organized" or has_any(answers, "handover", ["not_organized"]):
        add("Übergabeprozess klären: Abholung, Lieferung, Versand oder externe Logistik festlegen.")

    # Anbieter-spezifische Maßnahmen nur dann, wenn wirklich relevant
    if provider_id in ["nahgenuss", "fleischbox"]:
        if not has_any(answers, "certification", ["bio"]) and answer_value(answers, "animal_origin") != "wild_free":
            add("Bio-Zertifizierung prüfen oder Anbieter ohne Bio-Pflicht wählen.")
        if answer_value(answers, "processing_organizer") in ["", "not_organized"] and has_any(answers, "special_processing", ["slaughter", "cutting", "vacuum_packaging"]):
            add("Schlachtung, Zerlegung und Vakuumierung organisatorisch klären.")

    if provider_id == "myproduct":
        if answer_value(answers, "ean_data") != "complete":
            add("EAN/GTIN und vollständige Produktstammdaten organisieren.")
        if answer_value(answers, "shelf_life") != "ambient_6_months":
            add("Für myProduct nur ungekühlte Ware mit mindestens 6 Monaten Restlaufzeit einplanen.")
        if answer_value(answers, "cold_chain") != "none":
            add("Bei Kühlware eher regionale Abholung, Spezialplattform oder Partnernetzwerk prüfen.")

    if provider_id == "jazunah":
        if answer_value(answers, "offer_regularity") in ["irregular", "seasonal"]:
            add("Planbare Mengen und Lieferintervalle für B2B-Abnehmer vorbereiten.")
        if answer_score(answers, "reliable_delivery") <= 3:
            add("Lieferzuverlässigkeit und Ersatz-/Partnerstruktur verbessern.")

    if provider.get("platform_type") == "Kooperative Vermarktungsorganisation":
        if answer_value(answers, "cooperation_model") == "alone":
            add("Potenzielle Partnerbetriebe identifizieren, falls kooperative Vermarktung gewünscht ist.")
        if answer_value(answers, "common_rules") in ["no", "rather_no", "partial"]:
            add("Gemeinsame Qualitäts- und Lieferregeln mit möglichen Partnerbetrieben klären.")
        if answer_value(answers, "product_similarity") in ["unknown", "partial"]:
            add("Prüfen, welche Produkte der beteiligten Betriebe gemeinsam bündelbar sind.")
        if answer_value(answers, "common_brand") in ["no", "maybe_later"]:
            add("Prüfen, ob gemeinsame Marke oder Herkunftskommunikation überhaupt gewünscht ist.")

    return actions


def provider_status(eligible: bool, fit_percent: float, potential_fit_percent: float) -> str:
    if eligible and fit_percent >= 75:
        return "Sehr passend"
    if eligible and fit_percent >= 55:
        return "Passend mit Prüfung"
    if eligible:
        return "Eingeschränkt passend"
    if potential_fit_percent >= 60:
        return "Später möglich"
    return "Nicht passend"


def match_providers(answers: dict) -> list[dict]:
    """Bewertet alle Anbieter inkl. K.O.-Regeln, Fit-Score, Status und dynamischen Maßnahmen."""
    results = []

    for provider in PROVIDERS:
        blockers = get_hard_blockers(provider, answers)
        fit_percent, fit_points, fit_max_points, matched_reasons, missing_reasons = calculate_provider_fit(provider, answers)
        eligible = len(blockers) == 0
        actions = build_dynamic_actions(provider, answers, blockers, missing_reasons)

        results.append(
            {
                "id": provider["id"],
                "name": provider["name"],
                "platform_type": provider["platform_type"],
                "provider_class": provider["provider_class"],
                "description": provider["description"],
                "source_url": provider["source_url"],
                "cost_model": provider["cost_model"],
                "logo_url": provider.get("logo_url", ""),
                "logo_note": provider.get("logo_note", ""),
                "eligible": eligible,
                "fit_percent": fit_percent if eligible else 0.0,
                "potential_fit_percent": fit_percent,
                "status": provider_status(eligible, fit_percent if eligible else 0.0, fit_percent),
                "fit_points": fit_points,
                "fit_max_points": fit_max_points,
                "blockers": blockers,
                "matched_reasons": matched_reasons,
                "missing_reasons": missing_reasons,
                "improvement_actions": actions,
            }
        )

    results.sort(key=lambda item: (item["eligible"], item["fit_percent"], item["potential_fit_percent"]), reverse=True)
    return results


def get_top_recommendations(provider_results: list[dict], limit: int = 5) -> list[dict]:
    return [result for result in provider_results if result["eligible"]][:limit]


def get_blocked_providers(provider_results: list[dict]) -> list[dict]:
    return [result for result in provider_results if not result["eligible"]]
