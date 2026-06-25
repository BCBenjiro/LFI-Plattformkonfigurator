"""Dynamische Antwortoptionen für den Vertriebskonfigurator.

Die Funktion blendet Antwortmöglichkeiten aus, wenn sie fachlich durch frühere Antworten
nicht sinnvoll sind. Wichtig: Es werden nur sehr sichere Regeln genutzt, damit keine
realistischen Sonderfälle zu früh ausgeschlossen werden.
"""


def _answer_values(answers: dict, key: str) -> list[str]:
    answer = answers.get(key)
    if not answer:
        return []
    if "values" in answer:
        return [value for value in answer["values"] if value is not None]
    value = answer.get("value")
    return [] if value is None else [value]


def _answer_value(answers: dict, key: str, default: str = "") -> str:
    values = _answer_values(answers, key)
    return values[0] if values else default


def get_visible_options(question: dict, answers: dict) -> list[dict]:
    """Gibt die sichtbaren Antwortoptionen abhängig von bereits gegebenen Antworten zurück."""
    options = list(question.get("options", []))
    key = question.get("key")

    product_group = _answer_value(answers, "product_group")
    cold_chain = _answer_value(answers, "cold_chain")
    shelf_life = _answer_value(answers, "shelf_life")
    target_customers = set(_answer_values(answers, "target_customers"))
    sales_area = _answer_value(answers, "sales_area")

    hidden_values: set[str] = set()

    # Verarbeitung: Schlachtung/Zerlegung ist nur bei Fleisch/Fisch/Wild sinnvoll.
    if key == "special_processing" and product_group != "meat_fish_wild":
        hidden_values.update({"slaughter", "cutting"})

    # Übergabe/Logistik: Normaler Paketversand wird bei Kühlpflicht oder Fleisch/Fisch/Wild ausgeblendet.
    # Kühlversand und externe Logistik bleiben sichtbar.
    if key == "handover":
        requires_cooling = cold_chain in {"chilled", "frozen", "mixed"} or shelf_life in {
            "chilled_few_days",
            "chilled_weeks",
            "frozen",
        }
        clearly_no_cooling = cold_chain == "none" or shelf_life in {"ambient_weeks", "ambient_6_months"}

        if product_group == "meat_fish_wild" or requires_cooling:
            hidden_values.add("parcel_shipping")
        if clearly_no_cooling:
            hidden_values.add("cold_shipping")
        if sales_area == "local":
            hidden_values.update({"parcel_shipping", "external_logistics"})
        if product_group in {"beverages", "preserves_ready_meals", "other_shelf_stable", "grain_products"} and clearly_no_cooling:
            hidden_values.add("cold_shipping")

    # Verbesserungsbedarf: B2B-Zugang ist nur sinnvoll, wenn solche Zielkunden überhaupt genannt wurden.
    if key == "platform_needs" and target_customers and "unclear" not in target_customers:
        if not target_customers.intersection({"gastronomy", "large_kitchens", "retail", "business_gifts"}):
            hidden_values.add("b2b_access")

    # Zukünftige Vertriebsformen: Lokal-only und reine Hofladenlogik sollen keine sehr entfernten Optionen erzwingen.
    # Die Regeln bleiben bewusst vorsichtig: Zukunftsoptionen werden nur bei klaren Widersprüchen versteckt.
    if key == "sales_channels_possible" and sales_area == "local" and target_customers == {"farm_shop"}:
        hidden_values.update({"retail", "gastronomy_large_kitchens"})

    # Kostenmodell: Gemeinsame Investition ist nur sinnvoll, wenn Zusammenarbeit grundsätzlich vorstellbar ist.
    if key == "cost_model":
        cooperation_model = _answer_value(answers, "cooperation_model")
        sales_channels = set(_answer_values(answers, "sales_channels_possible"))
        platform_needs = set(_answer_values(answers, "platform_needs"))
        cooperation_relevant = cooperation_model not in {"", "alone"} or "joint_farms" in sales_channels or bool(
            platform_needs.intersection({"joint_quantities", "joint_brand_origin", "shared_processing"})
        )
        if not cooperation_relevant:
            hidden_values.add("shared_investment")

    return [option for option in options if option.get("value") not in hidden_values]
