import streamlit as st

from data.questions import QUESTIONS, SECTION_WEIGHTS
from logic.scoring import (
    build_answer_table,
    build_weighting_table,
    calculate_raw_total,
    calculate_section_scores,
    calculate_weighted_total,
    classify_overall_readiness,
    format_percent,
    get_critical_factors,
)
from logic.provider_matching import (
    get_blocked_providers,
    get_top_recommendations,
    match_providers,
)
from logic.recommendations import build_general_actions, classify_main_sales_path

# -------------------------------------------------
# LFI Plattformkonfigurator V2.2
# Fokus:
# - Verkauf landwirtschaftlicher Produkte
# - Zusammenarbeit beim Vertrieb
# - reale Anbieterempfehlungen
# - 1-5 Scorelogik nur dort, wo sie fachlich Sinn ergibt
# -------------------------------------------------

st.set_page_config(
    page_title="LFI Plattformkonfigurator",
    page_icon="🚜",
    layout="wide",
)


def format_option(option: dict, show_score: bool) -> str:
    if show_score and option.get("score") is not None:
        return f"{option['label']} → {option['score']} Punkte"
    return option["label"]


def answer_values(answers: dict, key: str) -> list[str]:
    answer = answers.get(key)
    if not answer:
        return []
    if "values" in answer:
        return [value for value in answer["values"] if value is not None]
    value = answer.get("value")
    return [] if value is None else [value]


def question_is_visible(question: dict, answers: dict) -> bool:
    condition = question.get("show_if")
    if not condition:
        return True

    key = condition["key"]
    values = answer_values(answers, key)

    if "values" in condition:
        return bool(set(values).intersection(condition["values"]))

    if "not_values" in condition:
        return bool(values) and not bool(set(values).intersection(condition["not_values"]))

    if "not_only" in condition:
        return bool(values) and not (len(values) == 1 and values[0] == condition["not_only"])

    return True


def show_score_bar(label: str, percent: float):
    st.write(f"**{label}:** {format_percent(percent)}")
    st.progress(min(max(percent / 100, 0), 1))


def render_provider_card(provider: dict, rank: int | None = None):
    title_prefix = f"{rank}. " if rank is not None else ""

    with st.container(border=True):
        col_a, col_b = st.columns([3, 1])

        with col_a:
            st.subheader(f"{title_prefix}{provider['name']}")
            st.write(f"**Typ:** {provider['platform_type']}")
            st.write(provider["description"])

        with col_b:
            if provider["eligible"]:
                st.metric("Fit", format_percent(provider["fit_percent"]))
                if provider["status"] == "Sehr passend":
                    st.success(provider["status"])
                elif provider["status"] == "Passend mit Prüfung":
                    st.info(provider["status"])
                else:
                    st.warning(provider["status"])
            else:
                st.metric("Potenzial", format_percent(provider["potential_fit_percent"]))
                if provider["status"] == "Später möglich":
                    st.warning(provider["status"])
                else:
                    st.error(provider["status"])

        st.write(f"**Kostenmodell:** {provider['cost_model']}")

        if provider["source_url"]:
            st.link_button("Anbieterseite öffnen", provider["source_url"])

        if provider["matched_reasons"]:
            with st.expander("Erfüllte Kriterien anzeigen", expanded=False):
                for reason in provider["matched_reasons"]:
                    st.write(f"✅ {reason}")

        if provider["blockers"]:
            with st.expander("Warum aktuell nicht? / K.O.-Gründe", expanded=False):
                for blocker in provider["blockers"]:
                    st.write(f"❌ {blocker}")

        if provider["missing_reasons"]:
            with st.expander("Nicht erfüllte Fit-Kriterien anzeigen", expanded=False):
                for reason in provider["missing_reasons"]:
                    st.write(f"⚠️ {reason}")

        if provider["improvement_actions"]:
            with st.expander("Maßnahmen zur Verbesserung", expanded=False):
                for action in provider["improvement_actions"]:
                    st.write(f"• {action}")


# -------------------------------------------------
# Oberfläche
# -------------------------------------------------

st.title("🚜 LFI Plattformkonfigurator")
st.subheader("Entscheidungsunterstützung für Vertrieb und Verkaufskooperationen in der Landwirtschaft")

st.info(
    "Diese Version bewertet Produktfit, Vertriebskanal, operative Verkaufsfähigkeit, Kooperation und Finanzierung. "
    "Nicht jede Frage erhält Punkte: Produktgruppe, Zielkunden, Zertifikate oder Kostenmodell sind Filter-, K.O.- oder Präferenzfragen."
)

with st.expander("Methodik kurz erklärt", expanded=False):
    st.write(
        """
        Der Konfigurator arbeitet in drei Schritten:

        **1. Grundbewertung:**  
        Nur echte Reifegradfragen werden mit **1 bis 5 Punkten** bewertet.
        Filterfragen wie Produktgruppe oder Zielkunden geben keine Punkte.

        **2. Anbieter-Matching:**  
        Jeder reale Anbieter besitzt harte K.O.-Kriterien und Fit-Kriterien.  
        K.O.-Kriterien werden vor dem normalen Score geprüft.

        **3. Ergebnis:**  
        Das Tool zeigt geeignete Anbieter, Status, Prozentwert, ausgeschlossene Anbieter, erfüllte Kriterien, fehlende Kriterien und nächste Maßnahmen.
        """
    )

    st.write("**Bewertungsbereiche:**")
    st.table(
        [
            {"Bereich": section, "Gewichtung": format_percent(weight * 100)}
            for section, weight in SECTION_WEIGHTS.items()
        ]
    )

st.divider()

# -------------------------------------------------
# Fragenkatalog
# -------------------------------------------------

st.header("Fragenkatalog V2.2")

answers = {}
visible_questions = []
questions_by_section = {}

for question in QUESTIONS:
    questions_by_section.setdefault(question["section"], []).append(question)

for section, section_questions in questions_by_section.items():
    with st.expander(section, expanded=True):
        for question in section_questions:
            if not question_is_visible(question, answers):
                continue

            visible_questions.append(question)
            st.write(f"**{question['title']}**")
            st.write(question["question"])

            question_type = question.get("type", "single")
            show_score = bool(question.get("scored", False))

            if question_type == "multiselect":
                selected_options = st.multiselect(
                    label="Antworten auswählen",
                    options=question["options"],
                    format_func=lambda opt, show_score=show_score: format_option(opt, show_score),
                    key=question["key"],
                    help=question.get("help"),
                    placeholder="Auswählen",
                )
                answers[question["key"]] = {
                    "label": ", ".join(opt["label"] for opt in selected_options),
                    "values": [opt["value"] for opt in selected_options],
                    "selected_options": selected_options,
                }
            else:
                options_with_placeholder = [
                    {"label": "Bitte auswählen", "value": None, "score": None}
                ] + question["options"]

                selected_option = st.selectbox(
                    label="Antwort auswählen",
                    options=options_with_placeholder,
                    format_func=lambda opt, show_score=show_score: (
                        opt["label"] if opt["value"] is None else format_option(opt, show_score)
                    ),
                    key=question["key"],
                    help=question.get("help"),
                    placeholder="Auswählen",
                )

                answers[question["key"]] = selected_option

            st.write("")

st.divider()

# -------------------------------------------------
# Auswertung
# -------------------------------------------------

if st.button("Empfehlung generieren", type="primary"):
    missing_questions = []

    for question in visible_questions:
        selected_answer = answers.get(question["key"])

        if question.get("type") == "multiselect":
            if not selected_answer or not selected_answer.get("selected_options"):
                missing_questions.append(question["title"])
        else:
            if not selected_answer or selected_answer.get("value") is None:
                missing_questions.append(question["title"])

    if missing_questions:
        st.warning("Bitte beantworte zuerst alle sichtbaren Fragen.")
        st.write("Noch offen:")
        for missing in missing_questions:
            st.write(f"• {missing}")
        st.stop()

    section_scores = calculate_section_scores(answers)
    raw_total_points, raw_max_points, raw_percent = calculate_raw_total(section_scores)
    weighted_percent = calculate_weighted_total(section_scores)
    overall_readiness = classify_overall_readiness(weighted_percent, section_scores)
    critical_factors = get_critical_factors(section_scores)

    provider_results = match_providers(answers)
    top_recommendations = get_top_recommendations(provider_results, limit=5)
    blocked_providers = get_blocked_providers(provider_results)
    main_sales_path = classify_main_sales_path(provider_results)
    general_actions = build_general_actions(section_scores, answers)

    # -------------------------------------------------
    # Ergebnisübersicht
    # -------------------------------------------------

    st.header("📊 Ergebnis")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Rohpunkte", f"{raw_total_points} / {raw_max_points}")

    with col2:
        st.metric("Gewichteter Gesamtscore", format_percent(weighted_percent))

    with col3:
        st.metric("Geeignete Anbieter", len(top_recommendations))

    st.divider()

    # -------------------------------------------------
    # Grundbewertung
    # -------------------------------------------------

    st.subheader("1. Grundbewertung")

    if overall_readiness["level"] == "low":
        st.error(overall_readiness["status"])
    elif overall_readiness["level"] == "medium":
        st.warning(overall_readiness["status"])
    else:
        st.success(overall_readiness["status"])

    st.write(f"**Empfehlung:** {overall_readiness['recommendation']}")
    st.write(f"**Begründung:** {overall_readiness['reason']}")

    st.write("**Nächste Schritte aus der Grundbewertung:**")
    for step in overall_readiness["next_steps"]:
        st.write(f"• {step}")

    st.divider()

    # -------------------------------------------------
    # Vertriebsweg
    # -------------------------------------------------

    st.subheader("2. Empfohlener Vertriebsweg")
    st.info(f"**{main_sales_path['title']}**")
    st.write(main_sales_path["reason"])

    st.divider()

    # -------------------------------------------------
    # Anbieterempfehlungen
    # -------------------------------------------------

    st.subheader("3. Konkrete Anbieterempfehlungen")

    if top_recommendations:
        for index, provider in enumerate(top_recommendations, start=1):
            render_provider_card(provider, rank=index)
    else:
        st.warning("Aktuell erfüllt kein Anbieter alle harten K.O.-Kriterien.")
        st.write("Das bedeutet nicht, dass kein Vertrieb möglich ist. Die App zeigt unten, welche Voraussetzungen zuerst verbessert werden sollten.")

    with st.expander("Warum andere Anbieter aktuell nicht passen", expanded=False):
        if blocked_providers:
            for provider in blocked_providers:
                render_provider_card(provider)
        else:
            st.success("Keine Anbieter wurden durch harte K.O.-Kriterien ausgeschlossen.")

    st.divider()

    # -------------------------------------------------
    # Detailauswertung
    # -------------------------------------------------

    st.subheader("4. Detailauswertung nach Bereichen")

    for section in SECTION_WEIGHTS.keys():
        show_score_bar(section, section_scores[section]["percent"])

    if critical_factors:
        st.write("**Auffällige Bereiche:**")
        for factor in critical_factors:
            st.write(f"• {factor}")
    else:
        st.success("Keine kritisch niedrigen Bereiche erkannt.")

    st.divider()

    # -------------------------------------------------
    # Maßnahmenplan
    # -------------------------------------------------

    st.subheader("5. Maßnahmenplan")

    if general_actions:
        for action in general_actions:
            st.write(f"• {action}")
    else:
        st.success("Die wichtigsten Grundvoraussetzungen sind gut vorbereitet.")

    st.divider()

    # -------------------------------------------------
    # Transparenz
    # -------------------------------------------------

    with st.expander("Transparenz der Berechnung anzeigen", expanded=False):
        st.write("### Rohscore")
        st.write(f"Gesamt: **{raw_total_points} / {raw_max_points} Punkte**")
        st.write(f"Ungewichteter Score: **{format_percent(raw_percent)}**")

        st.write("### Gewichteter Score")
        st.code(
            "Gesamtscore = Produktfit × 0.25 + Zielkundenfit × 0.20 + Operative Fähigkeit × 0.25 + Kooperation × 0.20 + Finanzierung × 0.10",
            language="text",
        )
        st.table(build_weighting_table(section_scores))
        st.write(f"Gewichteter Gesamtscore: **{format_percent(weighted_percent)}**")

        st.write("### Anbieter-Matching")
        st.write(
            "Jeder Anbieter hat harte K.O.-Regeln und Fit-Regeln. "
            "K.O.-Regeln schließen Anbieter aktuell aus. Fit-Regeln bestimmen danach die Reihenfolge geeigneter Anbieter. "
            "Filter- und Präferenzfragen wie Produktgruppe, Zielkunden oder Kostenmodell beeinflussen Anbieter, aber nicht immer den Grundscore."
        )

    with st.expander("Ausgewählte Antworten anzeigen", expanded=False):
        st.table(build_answer_table(answers))

    st.caption(
        "Hinweis: Der Konfigurator ist eine Entscheidungsunterstützung. "
        "Er ersetzt keine rechtliche, steuerliche oder betriebswirtschaftliche Einzelfallprüfung."
    )
