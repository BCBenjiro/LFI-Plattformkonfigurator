"""Exportfunktionen für den Ergebnisbericht."""

from datetime import datetime
from io import BytesIO
from pathlib import Path
import re

from logic.scoring import build_answer_table, format_percent


def _lines_from_list(items: list[str], prefix: str = "- ") -> str:
    if not items:
        return "- Keine"
    return "\n".join(f"{prefix}{item}" for item in items)


def build_export_report(
    answers: dict,
    section_scores: dict,
    overall_readiness: dict,
    weighted_percent: float,
    main_sales_path: dict,
    provider_results: list[dict],
    prioritized_actions: dict[str, list[str]],
    validation_warnings: list[dict],
) -> str:
    """Erstellt einen Markdown-Bericht zum Download. Bleibt als Fallback erhalten."""
    now = datetime.now().strftime("%d.%m.%Y %H:%M")
    suitable = [p for p in provider_results if p["eligible"]]
    later = [p for p in provider_results if (not p["eligible"] and p["status"] == "Später möglich")]

    lines: list[str] = []
    lines.append("# Ergebnisbericht - Vertriebskonfigurator Landwirtschaft")
    lines.append(f"Erstellt am: {now}")
    lines.append("")
    lines.append("> Hinweis: Der Bericht ist eine Entscheidungsunterstützung und ersetzt keine rechtliche, steuerliche oder betriebswirtschaftliche Einzelfallprüfung.")
    lines.append("")

    lines.append("## 1. Kurzdiagnose")
    lines.append(f"- Status: {overall_readiness['status']}")
    lines.append(f"- Gewichteter Gesamtscore: {format_percent(weighted_percent)}")
    lines.append(f"- Empfohlener Vertriebsweg: {main_sales_path['title']}")
    lines.append(f"- Begründung: {main_sales_path['reason']}")
    lines.append("")

    lines.append("## 2. Bereichsscores")
    for section, values in section_scores.items():
        lines.append(f"- {section}: {format_percent(values['percent'])} ({values['points']} / {values['max_points']} Punkte)")
    lines.append("")

    lines.append("## 3. Anbieterempfehlungen")
    if suitable:
        for idx, provider in enumerate(suitable[:8], start=1):
            lines.append(f"### {idx}. {provider['name']}")
            lines.append(f"- Status: {provider['status']}")
            lines.append(f"- Fit: {format_percent(provider['fit_percent'])}")
            lines.append(f"- Typ: {provider['platform_type']}")
            lines.append(f"- Fit-Punkte: {provider['fit_points']} / {provider['fit_max_points']}")
            lines.append("- Warum passend:")
            lines.append(_lines_from_list(provider.get("matched_reasons", [])[:6], "  - "))
            if provider.get("missing_reasons"):
                lines.append("- Noch offen:")
                lines.append(_lines_from_list(provider.get("missing_reasons", [])[:6], "  - "))
            if provider.get("source_url"):
                lines.append(f"- Quelle: {provider['source_url']}")
            lines.append("")
    else:
        lines.append("Aktuell erfüllt kein Anbieter alle harten K.O.-Kriterien. Die nächsten Schritte sollten zuerst fehlende Voraussetzungen verbessern.")
        lines.append("")

    if later:
        lines.append("## 4. Später mögliche Anbieter")
        for provider in later[:8]:
            lines.append(f"### {provider['name']}")
            lines.append(f"- Potenzial: {format_percent(provider['potential_fit_percent'])}")
            lines.append("- Aktuelle Hürden:")
            lines.append(_lines_from_list(provider.get("blockers", [])[:6], "  - "))
            lines.append("")

    lines.append("## 5. Maßnahmenplan")
    for title, actions in prioritized_actions.items():
        lines.append(f"### {title}")
        lines.append(_lines_from_list(actions))
        lines.append("")

    if validation_warnings:
        lines.append("## 6. Hinweise zu widersprüchlichen/riskanten Angaben")
        for warning in validation_warnings:
            lines.append(f"- {warning['title']}: {warning['text']}")
        lines.append("")

    lines.append("## 7. Ausgewählte Antworten")
    for row in build_answer_table(answers):
        frage = row.get("Frage", "")
        lines.append(f"- {row['Nr.']} {frage} - {row['Antwort']} ({row['Punkte']})")

    return "\n".join(lines)


def _plain_text(value: object) -> str:
    """Entfernt HTML-Fragmente und problematische Zeichen für ReportLab-Standardfonts."""
    text = str(value) if value is not None else ""

    # Einige Texte können aus UI-/Markdown-Kontexten stammen. Im PDF sollen keine
    # sichtbaren Tags wie <br/> oder </b> erscheinen.
    text = re.sub(r"<br\s*/?>", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"</?b>", "", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)

    replacements = {
        "🚜": "",
        "📊": "",
        "✅": "OK",
        "⚠️": "Hinweis",
        "❌": "Nicht erfüllt",
        "→": "->",
        "–": "-",
        "—": "-",
        "‑": "-",
        "“": '"',
        "”": '"',
        "’": "'",
        "…": "...",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return re.sub(r"\s+", " ", text).strip()


def _p(text: object, style):
    from reportlab.platypus import Paragraph
    from xml.sax.saxutils import escape

    clean = escape(_plain_text(text))
    return Paragraph(clean, style)


def _bullet_items(items: list[str], styles, max_items: int | None = None):
    from reportlab.platypus import Paragraph
    from xml.sax.saxutils import escape

    values = items[:max_items] if max_items else items
    if not values:
        values = ["Keine"]
    story = []
    for item in values:
        story.append(Paragraph("• " + escape(_plain_text(item)), styles["BodyText"]))
    return story


def _logo_flowable(logo_path: str | None, styles, max_width: float, max_height: float):
    """Erzeugt ein Logo-Flowable für den PDF-Bericht oder einen neutralen Fallback."""
    from reportlab.platypus import Image as RLImage
    from reportlab.lib.utils import ImageReader

    if not logo_path:
        return _p("Logo nicht hinterlegt", styles["Small"])

    path = Path(logo_path)
    if not path.exists():
        return _p("Logo nicht gefunden", styles["Small"])

    try:
        reader = ImageReader(str(path))
        width, height = reader.getSize()
        if width <= 0 or height <= 0:
            return _p("Logo nicht lesbar", styles["Small"])
        scale = min(max_width / width, max_height / height)
        img = RLImage(str(path), width=width * scale, height=height * scale)
        img.hAlign = "CENTER"
        return img
    except Exception:
        return _p("Logo nicht lesbar", styles["Small"])


def build_export_pdf(
    answers: dict,
    section_scores: dict,
    overall_readiness: dict,
    weighted_percent: float,
    main_sales_path: dict,
    provider_results: list[dict],
    prioritized_actions: dict[str, list[str]],
    validation_warnings: list[dict],
) -> bytes:
    """Erstellt einen gestalteten PDF-Ergebnisbericht als Bytes."""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Spacer, Table, TableStyle

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=1.6 * cm,
        rightMargin=1.6 * cm,
        topMargin=1.4 * cm,
        bottomMargin=1.4 * cm,
        title="Ergebnisbericht Vertriebskonfigurator Landwirtschaft",
    )

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="Small", parent=styles["BodyText"], fontSize=8, leading=10, textColor=colors.HexColor("#475569")))
    styles.add(ParagraphStyle(name="SmallWhite", parent=styles["BodyText"], fontSize=8.5, leading=10.5, textColor=colors.white))
    styles.add(ParagraphStyle(name="SmallWhiteBold", parent=styles["BodyText"], fontSize=10, leading=12, textColor=colors.white))
    styles.add(ParagraphStyle(name="SectionHeading", parent=styles["Heading2"], fontSize=13, leading=16, spaceBefore=12, spaceAfter=6, textColor=colors.HexColor("#0f172a")))
    styles.add(ParagraphStyle(name="CardTitle", parent=styles["Heading3"], fontSize=11.5, leading=14, spaceBefore=4, spaceAfter=3, textColor=colors.HexColor("#1e3a8a")))
    styles.add(ParagraphStyle(name="TitleBlue", parent=styles["Title"], fontSize=19, leading=22, textColor=colors.white, alignment=0))
    styles.add(ParagraphStyle(name="TitleBlueSmall", parent=styles["Title"], fontSize=13, leading=16, textColor=colors.white, alignment=0))

    story = []
    now = datetime.now().strftime("%d.%m.%Y %H:%M")
    suitable = [p for p in provider_results if p["eligible"]]
    later = [p for p in provider_results if (not p["eligible"] and p["status"] == "Später möglich")]

    # Titelkarte
    title_table = Table(
        [
            [_p("Ergebnisbericht", styles["TitleBlue"]), _p("Erstellt am", styles["SmallWhite"])],
            [_p("Vertriebskonfigurator Landwirtschaft", styles["TitleBlueSmall"]), _p(now, styles["SmallWhiteBold"])],
        ],
        colWidths=[12.2 * cm, 4.4 * cm],
    )
    title_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#17324d")),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.white),
        ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#17324d")),
        ("SPAN", (0, 0), (0, 0)),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    story.append(title_table)
    story.append(Spacer(1, 0.35 * cm))

    summary_data = [
        [_p("Status", styles["Small"]), _p(overall_readiness["status"], styles["BodyText"])],
        [_p("Gesamtscore", styles["Small"]), _p(format_percent(weighted_percent), styles["BodyText"])],
        [_p("Empfohlener Vertriebsweg", styles["Small"]), _p(main_sales_path["title"], styles["BodyText"])],
        [_p("Begründung", styles["Small"]), _p(main_sales_path["reason"], styles["BodyText"])],
    ]
    summary_table = Table(summary_data, colWidths=[4.2 * cm, 12.4 * cm])
    summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#e8eef5")),
        ("BACKGROUND", (1, 0), (1, -1), colors.HexColor("#f8fafc")),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#cbd5e1")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(summary_table)

    story.append(_p("Bereichsscores", styles["SectionHeading"]))
    score_rows = [[_p("Bereich", styles["Small"]), _p("Score", styles["Small"]), _p("Punkte", styles["Small"])] ]
    for section, values in section_scores.items():
        score_rows.append([
            _p(section, styles["BodyText"]),
            _p(format_percent(values["percent"]), styles["BodyText"]),
            _p(f"{values['points']} / {values['max_points']}", styles["BodyText"]),
        ])
    score_table = Table(score_rows, colWidths=[10.0 * cm, 3.2 * cm, 3.4 * cm])
    score_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#17324d")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#ffffff")),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#cbd5e1")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(score_table)

    story.append(_p("Anbieterempfehlungen", styles["SectionHeading"]))
    if suitable:
        for idx, provider in enumerate(suitable[:5], start=1):
            story.append(_p(f"{idx}. {provider['name']} - {provider['status']}", styles["CardTitle"]))

            logo = _logo_flowable(provider.get("logo_url"), styles, max_width=2.7 * cm, max_height=1.35 * cm)
            provider_details = Table(
                [
                    [_p("Fit", styles["Small"]), _p(format_percent(provider["fit_percent"]), styles["BodyText"])],
                    [_p("Typ", styles["Small"]), _p(provider["platform_type"], styles["BodyText"])],
                    [_p("Fit-Punkte", styles["Small"]), _p(f"{provider['fit_points']} / {provider['fit_max_points']}", styles["BodyText"])],
                    [_p("Kostenmodell", styles["Small"]), _p(provider["cost_model"], styles["BodyText"])],
                ],
                colWidths=[2.7 * cm, 10.9 * cm],
            )
            provider_details.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#eff6ff")),
                ("INNERGRID", (0, 0), (-1, -1), 0.2, colors.HexColor("#dbeafe")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]))

            provider_table = Table(
                [[logo, provider_details]],
                colWidths=[3.0 * cm, 13.6 * cm],
            )
            provider_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#ffffff")),
                ("BOX", (0, 0), (-1, -1), 0.4, colors.HexColor("#bfdbfe")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]))
            story.append(provider_table)
            story.append(_p("Warum passend", styles["Small"]))
            story.extend(_bullet_items(provider.get("matched_reasons", [])[:5], styles))
            if provider.get("missing_reasons"):
                story.append(_p("Noch zu prüfen", styles["Small"]))
                story.extend(_bullet_items(provider.get("missing_reasons", [])[:4], styles))
            if provider.get("source_url"):
                story.append(_p(f"Quelle: {provider['source_url']}", styles["Small"]))
            story.append(Spacer(1, 0.15 * cm))
    else:
        story.append(_p("Aktuell erfüllt kein Anbieter alle harten K.O.-Kriterien. Priorität hat der Maßnahmenplan.", styles["BodyText"]))

    if later:
        story.append(_p("Später mögliche Anbieter", styles["SectionHeading"]))
        for provider in later[:5]:
            logo = _logo_flowable(provider.get("logo_url"), styles, max_width=2.4 * cm, max_height=1.1 * cm)
            header = Table(
                [[logo, _p(f"{provider['name']} - Potenzial {format_percent(provider['potential_fit_percent'])}", styles["CardTitle"])]],
                colWidths=[2.8 * cm, 13.8 * cm],
            )
            header.setStyle(TableStyle([
                ("BOX", (0, 0), (-1, -1), 0.3, colors.HexColor("#fde68a")),
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#fffbeb")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]))
            story.append(header)
            story.append(_p("Aktuelle Hürden", styles["Small"]))
            story.extend(_bullet_items(provider.get("blockers", [])[:5], styles))

    story.append(_p("Priorisierter Maßnahmenplan", styles["SectionHeading"]))
    for title, actions in prioritized_actions.items():
        story.append(_p(title, styles["CardTitle"]))
        story.extend(_bullet_items(actions, styles, max_items=8))

    if validation_warnings:
        story.append(_p("Hinweise zu Angaben", styles["SectionHeading"]))
        for warning in validation_warnings:
            story.append(_p(f"{warning['title']}: {warning['text']}", styles["BodyText"]))

    answer_rows = build_answer_table(answers)
    if answer_rows:
        story.append(_p("Ausgewählte Antworten", styles["SectionHeading"]))
        table_rows = [[_p("Nr.", styles["Small"]), _p("Frage", styles["Small"]), _p("Antwort", styles["Small"]), _p("Punkte", styles["Small"])] ]
        for row in answer_rows:
            table_rows.append([
                _p(row.get("Nr.", "-"), styles["Small"]),
                _p(row.get("Frage", "-"), styles["Small"]),
                _p(row.get("Antwort", "-"), styles["Small"]),
                _p(row.get("Punkte", "-"), styles["Small"]),
            ])
        answer_table = Table(table_rows, colWidths=[1.5 * cm, 4.8 * cm, 7.1 * cm, 3.2 * cm], repeatRows=1)
        answer_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#17324d")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.2, colors.HexColor("#cbd5e1")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(answer_table)

    story.append(Spacer(1, 0.25 * cm))
    story.append(_p("Hinweis: Der Konfigurator ist eine Entscheidungsunterstützung und ersetzt keine rechtliche, steuerliche oder betriebswirtschaftliche Einzelfallprüfung.", styles["Small"]))

    def footer(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#64748b"))
        canvas.drawString(1.6 * cm, 1.0 * cm, "Vertriebskonfigurator Landwirtschaft - Ergebnisbericht")
        canvas.drawRightString(A4[0] - 1.6 * cm, 1.0 * cm, f"Seite {doc.page}")
        canvas.restoreState()

    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf
