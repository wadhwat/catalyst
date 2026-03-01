"""
Generate a PDF report matching Caterpillar "EN_Mini_HEX_Safety & Maint. Inspection" format.
Stored under data/inspections/{inspection_id}/report.pdf.
Uses green/yellow/red status indicators (PASS/MONITOR/FAIL).
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Tuple

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from src.inspection.checklist import (
    ENGINE_COMPARTMENT,
    FROM_GROUND,
    INSIDE_CAB,
    WHAT_TO_LOOK_FOR,
)
from src.report.schema import Report

logger = logging.getLogger(__name__)

CHECK = "\u2713"  # ✓
CROSS = "\u2717"  # ✗
WARN = "\u0021"  # !

# Caterpillar-style status colors (green / yellow / red)
COLOR_PASS = colors.HexColor("#00A651")      # Green
COLOR_MONITOR = colors.HexColor("#FFB81C")   # Yellow/amber
COLOR_FAIL = colors.HexColor("#E31837")      # Red
COLOR_PASS_BG = colors.HexColor("#E6F7ED")   # Light green
COLOR_MONITOR_BG = colors.HexColor("#FFF8E6")  # Light yellow
COLOR_FAIL_BG = colors.HexColor("#FFE8E8")   # Light red
CAT_YELLOW = colors.HexColor("#FFCD11")      # Caterpillar yellow (header accent)


def _items_by_id(report: Report) -> Dict[str, Any]:
    return {item.id: item for item in report.items}


def _status_symbol(status: str) -> str:
    if status == "PASS":
        return CHECK
    if status == "FAIL":
        return CROSS
    return WARN  # MONITOR


def _row(
    label: str,
    item: Any | None,
    criteria: str,
) -> Tuple[List[str], str]:
    """Build a row: [What are you inspecting?, √, What are you looking for?, status symbol, Evaluator Comments].
    Returns (row_data, status) for styling."""
    inspected = CHECK  # Always checked (we performed the inspection)
    status = (item.status if item else "PASS")
    symbol = _status_symbol(status)
    raw_notes = (item.notes or "—") if item else "—"
    notes = raw_notes[:120] + ("…" if len(raw_notes) > 120 else "")
    return ([label, inspected, criteria, symbol, notes], status)


def generate_report_pdf(
    report: Report,
    inspection_id: str,
    vin: str,
    observed_at: str | None,
    output_path: Path,
) -> Path | None:
    """
    Generate a PDF report matching Caterpillar form layout and save to output_path.
    Returns the path if successful, None on failure (logs but does not raise).
    """
    try:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=letter,
            rightMargin=0.6 * inch,
            leftMargin=0.6 * inch,
            topMargin=0.6 * inch,
            bottomMargin=0.6 * inch,
        )
        story = []
        styles = getSampleStyleSheet()

        # Header — Caterpillar style
        story.append(Paragraph("HYDRAULIC EXCAVATOR", ParagraphStyle("H1", parent=styles["Heading1"], fontSize=14)))
        story.append(Paragraph("Safety &amp; Maintenance Inspection (300.9-308)", styles["Heading2"]))
        story.append(Spacer(1, 0.15 * inch))

        date_str = (observed_at or "—")[:19] if observed_at else "—"
        summary_status = report.summary.status
        status_color = COLOR_PASS if summary_status == "PASS" else (COLOR_FAIL if summary_status == "FAIL" else COLOR_MONITOR)
        status_bg = COLOR_PASS_BG if summary_status == "PASS" else (COLOR_FAIL_BG if summary_status == "FAIL" else COLOR_MONITOR_BG)

        meta = [
            ["Operator/Inspector", "CATalyst", "Date", date_str[:10] if date_str != "—" else "—", "Time", date_str[11:19] if len(date_str) > 11 else "—"],
            ["Serial Number", vin or "—", "Machine Hours", "—", "Overall Status", summary_status],
        ]
        meta_t = Table(meta, colWidths=[1.1 * inch, 1.6 * inch, 0.7 * inch, 1.2 * inch, 0.5 * inch, 1.4 * inch])
        meta_t.setStyle(TableStyle([
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("BACKGROUND", (4, 1), (5, 1), status_bg),
            ("TEXTCOLOR", (5, 1), (5, 1), status_color),
            ("FONTNAME", (5, 1), (5, 1), "Helvetica-Bold"),
        ]))
        story.append(meta_t)
        story.append(Spacer(1, 0.15 * inch))

        bullets = (
            "• A thorough, regular visual inspection of the machine is necessary to maintain machine performance, "
            "availability, and safety. Make the inspection at the beginning of every shift or after every 10 hours."
        )
        story.append(Paragraph(bullets, ParagraphStyle("Bullet", parent=styles["Normal"], fontSize=8, spaceAfter=4)))
        story.append(Spacer(1, 0.1 * inch))

        # Table header
        table_header = ["What are you inspecting?", "√", "What are you looking for?", "Status", "Evaluator Comments"]
        items_by_id = _items_by_id(report)

        def add_section(header: str, labels: List[str]) -> None:
            story.append(Paragraph(
                header,
                ParagraphStyle("Section", parent=styles["Heading2"], fontSize=10, spaceAfter=6, textColor=colors.HexColor("#1a1a1a"), backColor=CAT_YELLOW, borderPadding=6),
            ))
            rows: List[List[str]] = [table_header]
            row_statuses: List[str] = ["header"]
            for label in labels:
                item = items_by_id.get(label)
                criteria = WHAT_TO_LOOK_FOR.get(label, "—")
                row_data, status = _row(label, item, criteria)
                rows.append(row_data)
                row_statuses.append(status)
            t = Table(rows, colWidths=[1.8 * inch, 0.35 * inch, 1.9 * inch, 0.5 * inch, 2.0 * inch])
            cmds: List[Tuple[Any, ...]] = [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2A2A2A")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("ALIGN", (0, 0), (2, -1), "LEFT"),
                ("ALIGN", (3, 0), (3, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ]
            for i, status in enumerate(row_statuses[1:], start=1):
                if status == "PASS":
                    cmds.append(("BACKGROUND", (0, i), (-1, i), COLOR_PASS_BG))
                    cmds.append(("TEXTCOLOR", (3, i), (3, i), COLOR_PASS))
                elif status == "FAIL":
                    cmds.append(("BACKGROUND", (0, i), (-1, i), COLOR_FAIL_BG))
                    cmds.append(("TEXTCOLOR", (3, i), (3, i), COLOR_FAIL))
                else:
                    cmds.append(("BACKGROUND", (0, i), (-1, i), COLOR_MONITOR_BG))
                    cmds.append(("TEXTCOLOR", (3, i), (3, i), COLOR_MONITOR))
            t.setStyle(TableStyle(cmds))
            story.append(t)
            story.append(Spacer(1, 0.2 * inch))

        add_section("FROM THE GROUND", FROM_GROUND)
        add_section("ENGINE COMPARTMENT OR PLATFORMS", ENGINE_COMPARTMENT)
        add_section("INSIDE THE CAB", INSIDE_CAB)

        # Notes and footer
        story.append(Paragraph("NOTES:", ParagraphStyle("NotesHeader", parent=styles["Heading2"], fontSize=10)))
        if report.summary.notes:
            story.append(Paragraph(report.summary.notes, styles["Normal"]))
        story.append(Spacer(1, 0.15 * inch))
        story.append(Paragraph(
            f"Inspected by: CATalyst — Inspection ID: {inspection_id} — Date: {date_str}",
            ParagraphStyle("Footer", parent=styles["Normal"], fontSize=8),
        ))
        story.append(Spacer(1, 0.1 * inch))
        story.append(Paragraph(
            "© Caterpillar. CAT, CATERPILLAR, and their respective logos are trademarks of Caterpillar. "
            "Generated by CATalyst.",
            ParagraphStyle("Legal", parent=styles["Normal"], fontSize=7, textColor=colors.grey),
        ))

        doc.build(story)
        logger.info("PDF report saved to %s", output_path)
        return output_path
    except Exception as exc:
        logger.warning("PDF generation failed: %s", exc)
        return None
