import base64
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

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
from logic.option_visibility import get_visible_options
from logic.validation import build_validation_warnings
from logic.report_export import build_export_pdf

# -------------------------------------------------
# Vertriebskonfigurator Landwirtschaft V2.9
# Fokus:
# - Verkauf landwirtschaftlicher Lebensmittel/Nahrungsmittel
# - reale Anbieterempfehlungen
# - dynamische Antwortoptionen
# - transparente Matchmaking-Logik
# -------------------------------------------------

st.set_page_config(
    page_title="Vertriebskonfigurator Landwirtschaft",
    page_icon="🚜",
    layout="wide",
)


def format_option(option: dict, show_score: bool) -> str:
    """Antwortoptionen werden bewusst ohne Punktwerte angezeigt.

    Die Scores bleiben intern erhalten, damit der Fragebogen für Nutzende nicht wie
    eine reine Punktejagd wirkt.
    """
    return option["label"]


def answer_values(answers: dict, key: str) -> list[str]:
    answer = answers.get(key)
    if not answer:
        return []
    if "values" in answer:
        return [value for value in answer["values"] if value is not None]
    value = answer.get("value")
    return [] if value is None else [value]


def answer_value(answers: dict, key: str, default: str = "") -> str:
    values = answer_values(answers, key)
    return values[0] if values else default


def inject_german_multiselect_labels():
    """Übersetzt Streamlit-interne Multiselect-Texte wie 'Select all'."""
    components.html(
        """
        <script>
        const replacements = new Map([
          ["Select all", "Alle auswählen"],
          ["Clear all", "Auswahl löschen"],
          ["No results found", "Keine Ergebnisse gefunden"],
          ["No options", "Keine Optionen"],
          ["Search", "Suchen"],
          ["Choose options", "Bitte auswählen"],
          ["Choose an option", "Bitte auswählen"]
        ]);

        function replaceTextNodes(root) {
          const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
          let node;
          while ((node = walker.nextNode())) {
            const trimmed = node.nodeValue.trim();
            if (replacements.has(trimmed)) {
              node.nodeValue = node.nodeValue.replace(trimmed, replacements.get(trimmed));
            }
          }
        }

        function runReplacement() {
          try {
            if (window.parent && window.parent.document && window.parent.document.body) {
              replaceTextNodes(window.parent.document.body);
            }
          } catch (error) {
            // Falls der Browser den Zugriff blockiert, bleibt nur der englische interne Streamlit-Text sichtbar.
          }
        }

        runReplacement();
        setInterval(runReplacement, 400);
        </script>
        """,
        height=0,
        width=0,
    )


def clean_multiselect_selection(question: dict, selected_options: list[dict]) -> list[dict]:
    """Entfernt widersprüchliche Optionen nach 'Alle auswählen'."""
    if len(selected_options) <= 1:
        return selected_options

    exclusive_values = set(question.get("exclusive_values", []))
    cleaned = [option for option in selected_options if option.get("value") not in exclusive_values]
    return cleaned if cleaned else selected_options


def clean_multiselect_state(key: str, question: dict):
    """Bereinigt widersprüchliche Multiselect-Auswahlen direkt nach Änderung."""
    current = st.session_state.get(key, [])
    cleaned = clean_multiselect_selection(question, current)
    if cleaned != current:
        st.session_state[key] = cleaned


def sanitize_session_state_for_options(key: str, visible_options: list[dict]):
    """Entfernt alte, inzwischen ausgeblendete Optionen aus der Session."""
    if key not in st.session_state:
        return

    visible_values = {option.get("value") for option in visible_options}
    current_value = st.session_state[key]

    if isinstance(current_value, list):
        sanitized = [option for option in current_value if isinstance(option, dict) and option.get("value") in visible_values]
        if sanitized != current_value:
            st.session_state[key] = sanitized
            st.rerun()
    elif isinstance(current_value, dict):
        if current_value.get("value") not in visible_values:
            del st.session_state[key]
            st.rerun()


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


def detect_image_mime(path: Path) -> str | None:
    """Erkennt gängige Bildtypen unabhängig von der Dateiendung."""
    try:
        data = path.read_bytes()
    except OSError:
        return None

    stripped = data[:500].lstrip().lower()
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if data.startswith(b"GIF87a") or data.startswith(b"GIF89a"):
        return "image/gif"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    if stripped.startswith(b"<svg") or b"<svg" in stripped:
        return "image/svg+xml"
    return None


def render_logo(logo_path: str, alt_text: str):
    """Zeigt Logos robust an, auch wenn z. B. SVG fälschlich als .png gespeichert wurde."""
    if not logo_path:
        return

    path = Path(logo_path)
    if not path.exists():
        st.caption("Logo-Datei nicht gefunden")
        return

    mime = detect_image_mime(path)
    if not mime:
        st.caption("Logo-Datei konnte nicht erkannt werden")
        return

    encoded = base64.b64encode(path.read_bytes()).decode("utf-8")
    st.markdown(
        f"""
        <div style="height:68px; display:flex; align-items:center; margin-bottom:0.45rem;">
          <img src="data:{mime};base64,{encoded}" alt="{alt_text}" style="max-width:130px; max-height:62px; object-fit:contain;" />
        </div>
        """,
        unsafe_allow_html=True,
    )


def status_badge(status: str) -> str:
    color = {
        "Sehr passend": "#107c41",
        "Passend mit Prüfung": "#2563eb",
        "Eingeschränkt passend": "#b45309",
        "Später möglich": "#b45309",
        "Nicht passend": "#6b7280",
    }.get(status, "#6b7280")
    return f'<span style="background:{color};color:white;border-radius:999px;padding:0.2rem 0.55rem;font-size:0.8rem;white-space:nowrap;">{status}</span>'


def render_provider_card(provider: dict, rank: int | None = None, compact: bool = False):
    title_prefix = f"{rank}. " if rank is not None else ""

    with st.container(border=True):
        col_a, col_b = st.columns([3.4, 1])

        with col_a:
            render_logo(provider.get("logo_url", ""), provider["name"])
            st.markdown(f"### {title_prefix}{provider['name']}")
            st.markdown(status_badge(provider["status"]), unsafe_allow_html=True)
            st.write(f"**Typ:** {provider['platform_type']}")
            st.write(provider["description"])

        with col_b:
            if provider["eligible"]:
                st.metric("Fit", format_percent(provider["fit_percent"]))
                st.progress(min(max(provider["fit_percent"] / 100, 0), 1))
            else:
                st.metric("Potenzial", format_percent(provider["potential_fit_percent"]))
                st.progress(min(max(provider["potential_fit_percent"] / 100, 0), 1))

            if provider.get("fit_max_points"):
                st.caption(f"{provider['fit_points']} von {provider['fit_max_points']} Fit-Punkten erfüllt")

        if provider["matched_reasons"]:
            st.write("**Warum dieser Anbieter passt:**")
            for reason in provider["matched_reasons"][:4]:
                st.write(f"✅ {reason}")

        if provider["missing_reasons"] and provider["eligible"]:
            st.write("**Noch zu prüfen:**")
            for reason in provider["missing_reasons"][:3]:
                st.write(f"⚠️ {reason}")

        st.write(f"**Kostenmodell:** {provider['cost_model']}")

        if provider["source_url"]:
            st.link_button("Anbieterseite öffnen", provider["source_url"])

        if not compact:
            with st.expander("Matchmaking nachvollziehen", expanded=False):
                st.write(
                    "Zuerst werden harte K.O.-Kriterien geprüft. Danach bewertet der Fit-Score, "
                    "wie gut Produkt, Zielkunden, Logistik, Kostenmodell und operative Voraussetzungen zum Anbieter passen."
                )
                st.write(f"**Fit-Punkte:** {provider['fit_points']} / {provider['fit_max_points']}")

                if provider["matched_reasons"]:
                    st.write("**Erfüllte Kriterien:**")
                    for reason in provider["matched_reasons"]:
                        st.write(f"✅ {reason}")

                if provider["missing_reasons"]:
                    st.write("**Nicht erfüllte Fit-Kriterien:**")
                    for reason in provider["missing_reasons"]:
                        st.write(f"⚠️ {reason}")

                if provider["blockers"]:
                    st.write("**K.O.-Gründe:**")
                    for blocker in provider["blockers"]:
                        st.write(f"❌ {blocker}")
        elif provider["blockers"]:
            st.write("**Aktuelle Hürden:**")
            for blocker in provider["blockers"][:4]:
                st.write(f"❌ {blocker}")

        if provider["improvement_actions"] and not compact:
            with st.expander("Maßnahmen zur Verbesserung", expanded=False):
                for action in provider["improvement_actions"]:
                    st.write(f"• {action}")


def categorize_providers(provider_results: list[dict]) -> dict[str, list[dict]]:
    """Ordnet Anbieter in nachvollziehbare Ergebnisgruppen."""
    categories = {
        "Direkt passend": [],
        "Passend mit Prüfung": [],
        "Als Ergänzung / eingeschränkt passend": [],
        "Später möglich": [],
        "Aktuell nicht passend": [],
    }

    for provider in provider_results:
        if provider["eligible"] and provider["fit_percent"] >= 75:
            categories["Direkt passend"].append(provider)
        elif provider["eligible"] and provider["fit_percent"] >= 55:
            categories["Passend mit Prüfung"].append(provider)
        elif provider["eligible"]:
            categories["Als Ergänzung / eingeschränkt passend"].append(provider)
        elif provider["status"] == "Später möglich":
            categories["Später möglich"].append(provider)
        else:
            categories["Aktuell nicht passend"].append(provider)

    return categories


def deduplicate(items: list[str]) -> list[str]:
    seen = set()
    result = []
    for item in items:
        if item and item not in seen:
            result.append(item)
            seen.add(item)
    return result


def prioritize_actions(general_actions: list[str], provider_results: list[dict], validation_warnings: list[dict]) -> dict[str, list[str]]:
    """Priorisiert allgemeine und anbieterbezogene Maßnahmen."""
    top_providers = [p for p in provider_results if p["eligible"]][:3]
    later_providers = [p for p in provider_results if p["status"] == "Später möglich"][:2]

    source_actions = list(general_actions)
    for provider in top_providers + later_providers:
        source_actions.extend(provider.get("improvement_actions", [])[:4])

    sofort_keywords = [
        "Kennzeichnung", "MHD", "Allergene", "Produktfotos", "Produkttexte", "Verpackung", "Übergabeprozess",
        "Lieferzuverlässigkeit", "Produktdaten", "EAN", "GTIN", "Bio-Zertifizierung", "Schlachtung", "Zerlegung",
        "Vakuumierung", "K.O.", "klären"
    ]
    pruefen_keywords = ["Anbieter", "Kontakt", "Planbare", "Lieferintervalle", "Qualitäts", "Regeln", "Partner"]
    optional_keywords = ["Förder", "Budget", "Kooperation", "gemeinsame", "Marke", "später", "Beratung"]

    sofort: list[str] = []
    vor_anfrage: list[str] = []
    optional: list[str] = []

    for warning in validation_warnings:
        sofort.append(f"Angabe prüfen: {warning['title']} – {warning['text']}")

    for action in source_actions:
        lower = action.lower()
        if any(keyword.lower() in lower for keyword in sofort_keywords):
            sofort.append(action)
        elif any(keyword.lower() in lower for keyword in pruefen_keywords):
            vor_anfrage.append(action)
        elif any(keyword.lower() in lower for keyword in optional_keywords):
            optional.append(action)
        else:
            vor_anfrage.append(action)

    return {
        "Sofort erledigen / zuerst klären": deduplicate(sofort),
        "Vor Anbieter-Anfrage prüfen": deduplicate(vor_anfrage),
        "Optional / später ausbauen": deduplicate(optional),
    }


def render_prioritized_actions(prioritized_actions: dict[str, list[str]]):
    any_action = any(prioritized_actions.values())
    if not any_action:
        st.success("Die wichtigsten Grundvoraussetzungen sind gut vorbereitet.")
        return

    for title, actions in prioritized_actions.items():
        with st.container(border=True):
            st.write(f"**{title}**")
            if actions:
                for action in actions:
                    st.write(f"• {action}")
            else:
                st.caption("Keine Punkte in dieser Priorität.")


def render_methodology_page():
    st.header("Methodik & Bewertungslogik")
    st.write(
        "Der Prototyp kombiniert drei Logiken: strukturierte Reifegradbewertung, harte K.O.-Kriterien und "
        "anbieterbezogene Fit-Regeln. Dadurch soll nicht nur ein Score entstehen, sondern eine nachvollziehbare Beratung."
    )

    st.subheader("1. Warum nicht jede Frage Punkte bekommt")
    st.write(
        "Punkte werden nur bei Reifegradfragen genutzt, etwa Kennzeichnung, Produktdaten, Verpackung, Zeit, Personal "
        "oder Lieferzuverlässigkeit. Produktgruppe, Zertifizierung, Zielkunden oder Kühlpflicht sind dagegen Filter- "
        "oder K.O.-Merkmale. Eine Bio-Zertifizierung ist zum Beispiel nicht 'mehr Punkte', sondern bei bestimmten Anbietern "
        "eine Voraussetzung."
    )

    st.subheader("2. Bewertungsbereiche")
    st.table(
        [
            {"Bereich": section, "Gewichtung": format_percent(weight * 100)}
            for section, weight in SECTION_WEIGHTS.items()
        ]
    )

    st.subheader("3. Anbieter-Matching")
    st.write(
        "Für jeden Anbieter werden zuerst harte Ausschlussregeln geprüft. Danach werden Fit-Regeln gezählt. "
        "Ein Anbieter kann deshalb trotz hohem Potenzial als 'später möglich' erscheinen, wenn eine harte Voraussetzung fehlt."
    )
    st.code(
        "1. Antworten erfassen\n2. Unpassende Antwortoptionen dynamisch ausblenden\n3. K.O.-Kriterien je Anbieter prüfen\n4. Fit-Punkte je Anbieter berechnen\n5. Anbieter nach Status und Fit sortieren\n6. Fehlende Punkte in Maßnahmen übersetzen",
        language="text",
    )

    st.subheader("4. Statuslogik")
    st.table(
        [
            {"Status": "Sehr passend", "Bedeutung": "K.O.-Kriterien erfüllt und hoher Fit."},
            {"Status": "Passend mit Prüfung", "Bedeutung": "Grundsätzlich geeignet, einzelne Punkte prüfen."},
            {"Status": "Eingeschränkt passend", "Bedeutung": "Geeignet, aber eher als Ergänzung oder mit Vorbereitung."},
            {"Status": "Später möglich", "Bedeutung": "Fit wäre vorhanden, aber harte Voraussetzung fehlt noch."},
            {"Status": "Nicht passend", "Bedeutung": "Aktuell zu viele harte Ausschlussgründe."},
        ]
    )

    st.subheader("5. Grenzen des Prototyps")
    st.write(
        "Der Konfigurator ersetzt keine Einzelfallberatung. Anbieterbedingungen, Förderbedingungen, Rechtslage und "
        "Produktanforderungen können sich ändern. Die Quellen sollten vor echter Kontaktaufnahme erneut geprüft werden."
    )


def build_progress_text(visible_questions: list[dict], answers: dict) -> tuple[int, int, float]:
    total = len(visible_questions)
    answered = 0
    for question in visible_questions:
        answer = answers.get(question["key"])
        if question.get("type") == "multiselect":
            if answer and answer.get("selected_options"):
                answered += 1
        else:
            if answer and answer.get("value") is not None:
                answered += 1
    progress = answered / total if total else 0
    return answered, total, progress


def render_sticky_progress(container, answered: int, total: int, progress: float):
    """Zeigt den Fragebogen-Fortschritt fixiert am oberen Bildschirmrand an."""
    percent = int(round(progress * 100)) if total else 0
    container.markdown(
        f"""
        <style>
        .sticky-progress-box {{
            position: fixed;
            top: 3.35rem;
            left: max(1rem, calc((100vw - 1180px) / 2));
            right: max(1rem, calc((100vw - 1180px) / 2));
            z-index: 1000;
            background: #17324d;
            color: #ffffff !important;
            border: 1px solid #234764;
            border-radius: 0.65rem;
            padding: 0.72rem 0.95rem;
            box-shadow: 0 6px 18px rgba(15, 23, 42, 0.24);
        }}
        .sticky-progress-text {{
            color: #ffffff !important;
            font-size: 0.95rem;
            font-weight: 700;
            margin-bottom: 0.45rem;
            line-height: 1.25;
        }}
        .sticky-progress-track {{
            width: 100%;
            height: 0.55rem;
            background: rgba(255,255,255,0.28);
            border-radius: 999px;
            overflow: hidden;
        }}
        .sticky-progress-fill {{
            width: {percent}%;
            height: 100%;
            background: #ffffff;
            border-radius: 999px;
        }}
        .sticky-progress-spacer {{
            height: 5.1rem;
        }}
        @media (max-width: 900px) {{
            .sticky-progress-box {{
                top: 3.2rem;
                left: 0.6rem;
                right: 0.6rem;
            }}
            .sticky-progress-spacer {{
                height: 5.5rem;
            }}
        }}
        </style>
        <div class="sticky-progress-box">
            <div class="sticky-progress-text">Fragebogen-Fortschritt: {answered} von {total} sichtbaren Fragen beantwortet ({percent} %)</div>
            <div class="sticky-progress-track"><div class="sticky-progress-fill"></div></div>
        </div>
        <div class="sticky-progress-spacer"></div>
        """,
        unsafe_allow_html=True,
    )


# -------------------------------------------------
# Oberfläche
# -------------------------------------------------

st.title("🚜 Vertriebskonfigurator Landwirtschaft")
st.subheader("Entscheidungsunterstützung für Lebensmittelvertrieb und Verkaufskooperationen")

st.info(
    "Der Prototyp ist auf Lebensmittel/Nahrungsmittel aus landwirtschaftlicher Vermarktung ausgelegt. "
    "Nicht betrachtet werden Holz, Heu, Tierfutter oder andere Agrarrohstoffe. "
    "Bewertet werden Produktfit, Vertriebskanal, operative Verkaufsfähigkeit, Kooperation und Finanzierung."
)

inject_german_multiselect_labels()

tab_config, tab_methodology = st.tabs(["Konfiguration", "Methodik & Bewertungslogik"])

with tab_methodology:
    render_methodology_page()

with tab_config:
    # -------------------------------------------------
    # Fragenkatalog
    # -------------------------------------------------

    st.header("Fragenkatalog")
    progress_container = st.container()

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
                visible_options_for_question = get_visible_options(question, answers)
                sanitize_session_state_for_options(question["key"], visible_options_for_question)

                if question_type == "multiselect":
                    selected_options = st.multiselect(
                        label="Antworten auswählen",
                        options=visible_options_for_question,
                        format_func=lambda opt, show_score=show_score: format_option(opt, show_score),
                        key=question["key"],
                        help=question.get("help"),
                        placeholder="Bitte auswählen",
                        on_change=clean_multiselect_state,
                        args=(question["key"], question),
                    )
                    selected_options = clean_multiselect_selection(question, selected_options)

                    answers[question["key"]] = {
                        "label": ", ".join(opt["label"] for opt in selected_options),
                        "values": [opt["value"] for opt in selected_options],
                        "selected_options": selected_options,
                    }
                else:
                    selected_option = st.selectbox(
                        label="Antwort auswählen",
                        options=visible_options_for_question,
                        index=None,
                        format_func=lambda opt, show_score=show_score: format_option(opt, show_score),
                        key=question["key"],
                        help=question.get("help"),
                        placeholder="Bitte auswählen",
                    )

                    answers[question["key"]] = selected_option

                st.write("")

    answered_count, visible_count, progress_value = build_progress_text(visible_questions, answers)
    render_sticky_progress(progress_container, answered_count, visible_count, progress_value)

    validation_warnings = build_validation_warnings(answers)
    if validation_warnings:
        with st.expander("Hinweise zu widersprüchlichen oder riskanten Angaben", expanded=True):
            for warning in validation_warnings:
                if warning["severity"] == "info":
                    st.info(f"**{warning['title']}** – {warning['text']}")
                else:
                    st.warning(f"**{warning['title']}** – {warning['text']}")

    st.divider()

    # -------------------------------------------------
    # Auswertung
    # -------------------------------------------------

    generate_clicked = st.button("Empfehlung generieren", type="primary")
    if generate_clicked:
        st.session_state["recommendation_generated"] = True

    if st.session_state.get("recommendation_generated", False):
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
        provider_categories = categorize_providers(provider_results)
        prioritized_actions = prioritize_actions(general_actions, provider_results, validation_warnings)

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
            st.metric("Geeignete Anbieter", len([p for p in provider_results if p["eligible"]]))

        st.subheader("Kurzdiagnose")
        if top_recommendations:
            best = top_recommendations[0]
            st.success(
                f"Der Betrieb passt aktuell am stärksten zu **{main_sales_path['title']}**. "
                f"Der beste konkrete Anbieter ist **{best['name']}** mit {format_percent(best['fit_percent'])} Fit."
            )
        else:
            st.warning(
                "Aktuell erfüllt kein Anbieter alle harten Voraussetzungen. Das ist keine Sackgasse: "
                "Der Konfigurator zeigt unten, welche Voraussetzungen zuerst verbessert werden sollten und welche Anbieter später möglich wären."
            )

        diagnosis_points = []
        for section, score in section_scores.items():
            if score["max_points"] == 0:
                continue
            if score["percent"] >= 67:
                diagnosis_points.append(f"{section} ist gut vorbereitet ({format_percent(score['percent'])}).")
            elif score["percent"] <= 33:
                diagnosis_points.append(f"{section} ist aktuell kritisch niedrig ({format_percent(score['percent'])}).")
            else:
                diagnosis_points.append(f"{section} ist teilweise vorbereitet ({format_percent(score['percent'])}).")

        with st.expander("Kurzdiagnose im Detail", expanded=True):
            st.write(f"**Empfohlener Vertriebsweg:** {main_sales_path['title']}")
            st.write(main_sales_path["reason"])
            for point in diagnosis_points:
                st.write(f"• {point}")

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

        with st.expander("Nächste Schritte aus der Grundbewertung", expanded=False):
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
        # Anbieterempfehlungen nach Kategorien
        # -------------------------------------------------

        st.subheader("3. Konkrete Anbieterempfehlungen")

        if not top_recommendations:
            st.warning("Keine direkte Anbieterempfehlung möglich")
            st.write(
                "Aktuell passt kein Anbieter vollständig. Priorität hat daher der Maßnahmenplan: "
                "fehlende K.O.-Kriterien verbessern, danach Anbieter erneut prüfen."
            )

            later = provider_categories["Später möglich"]
            if later:
                st.write("**Später mögliche Anbieter:**")
                for provider in later[:3]:
                    render_provider_card(provider, compact=True)
        else:
            category_explanations = {
                "Direkt passend": "Diese Anbieter erfüllen die K.O.-Kriterien und haben einen hohen Fit.",
                "Passend mit Prüfung": "Diese Anbieter passen grundsätzlich, einzelne Voraussetzungen sollten geprüft werden.",
                "Als Ergänzung / eingeschränkt passend": "Diese Anbieter können ergänzend sinnvoll sein, sind aber nicht die stärkste Hauptempfehlung.",
                "Später möglich": "Diese Anbieter haben Potenzial, aber aktuell fehlt mindestens eine harte Voraussetzung.",
            }

            for category_name in ["Direkt passend", "Passend mit Prüfung", "Als Ergänzung / eingeschränkt passend", "Später möglich"]:
                providers = provider_categories[category_name]
                if not providers:
                    continue
                st.markdown(f"### {category_name} ({len(providers)})")
                st.caption(category_explanations[category_name])
                for index, provider in enumerate(providers[:5], start=1):
                    render_provider_card(provider, rank=index)

        with st.expander("Warum andere Anbieter aktuell nicht passen", expanded=False):
            not_matching = provider_categories["Aktuell nicht passend"]
            if not_matching:
                for provider in not_matching:
                    render_provider_card(provider, compact=True)
            elif blocked_providers:
                for provider in blocked_providers:
                    render_provider_card(provider, compact=True)
            else:
                st.success("Keine Anbieter wurden durch harte K.O.-Kriterien ausgeschlossen.")

        st.divider()

        # -------------------------------------------------
        # Anbieter-Vergleichstabelle
        # -------------------------------------------------

        st.subheader("4. Anbieter-Vergleich")
        comparison_rows = []
        for provider in provider_results:
            comparison_rows.append(
                {
                    "Anbieter": provider["name"],
                    "Status": provider["status"],
                    "Fit/Potenzial": format_percent(provider["fit_percent"] if provider["eligible"] else provider["potential_fit_percent"]),
                    "Typ": provider["platform_type"],
                    "Hauptgrund / Hürde": (provider["matched_reasons"][:1] or provider["blockers"][:1] or ["-"])[0],
                }
            )
        st.dataframe(comparison_rows, use_container_width=True, hide_index=True)

        st.divider()

        # -------------------------------------------------
        # Detailauswertung
        # -------------------------------------------------

        st.subheader("5. Detailauswertung nach Bereichen")

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

        st.subheader("6. Priorisierter Maßnahmenplan")
        render_prioritized_actions(prioritized_actions)

        st.divider()

        # -------------------------------------------------
        # Export
        # -------------------------------------------------

        st.subheader("7. Export")
        st.write(
            "Der Ergebnisbericht wird als PDF erzeugt und bleibt nach dem ersten Generieren verfügbar. "
            "Beim Download muss die Empfehlung nicht erneut generiert werden."
        )
        try:
            pdf_report = build_export_pdf(
                answers=answers,
                section_scores=section_scores,
                overall_readiness=overall_readiness,
                weighted_percent=weighted_percent,
                main_sales_path=main_sales_path,
                provider_results=provider_results,
                prioritized_actions=prioritized_actions,
                validation_warnings=validation_warnings,
            )
            st.download_button(
                label="Ergebnisbericht als PDF herunterladen",
                data=pdf_report,
                file_name="vertriebskonfigurator_ergebnisbericht.pdf",
                mime="application/pdf",
            )
        except Exception as error:
            st.error("Der PDF-Export konnte nicht erstellt werden.")
            st.caption(f"Technischer Hinweis: {error}")

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
