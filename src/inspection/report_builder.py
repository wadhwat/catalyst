from __future__ import annotations

from collections import defaultdict
from typing import List

from src.inspection.checklist import CHECKLIST_ITEMS
from src.inspection.schema import Finding
from src.report.schema import Report, ReportItem, ReportSummary
from src.rubric.rules import worst_status

_SEVERITY_TO_STATUS = {
    "Minor": "MONITOR",
    "Moderate": "MONITOR",
    "Critical": "FAIL",
}


def build_report(findings: List[Finding], evidence_frames: List[str]) -> Report:
    """Convert aggregated findings into the existing Report schema."""
    findings_by_item: dict[str, List[Finding]] = defaultdict(list)
    for f in findings:
        findings_by_item[f.checklist_item].append(f)

    items: List[ReportItem] = []
    statuses: List[str] = []

    for label in CHECKLIST_ITEMS:
        item_findings = findings_by_item.get(label, [])

        if not item_findings:
            items.append(
                ReportItem(
                    id=label,
                    status="PASS",
                    score=0.0,
                    notes="No defects detected.",
                    evidence=evidence_frames,
                )
            )
            statuses.append("PASS")
            continue

        item_statuses = [
            _SEVERITY_TO_STATUS.get((f.severity or "").strip().title(), "MONITOR")
            for f in item_findings
        ]
        status = worst_status(item_statuses)
        max_conf = max(f.confidence for f in item_findings)

        descriptions = "; ".join(f.description for f in item_findings)
        notes = f"{len(item_findings)} defect(s) found: {descriptions}"

        items.append(
            ReportItem(
                id=label,
                status=status,
                score=max_conf,
                notes=notes,
                evidence=evidence_frames,
            )
        )
        statuses.append(status)

    summary_status = worst_status(statuses)

    defect_types = {f.defect_type for f in findings}
    if findings:
        summary_notes = (
            f"{len(findings)} finding(s) across "
            f"{len(findings_by_item)} component(s). "
            f"Defect types: {', '.join(sorted(defect_types))}."
        )
    else:
        summary_notes = "No defects detected across all checklist items."

    return Report(
        summary=ReportSummary(status=summary_status, notes=summary_notes),
        items=items,
    )
