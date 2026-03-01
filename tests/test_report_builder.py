from __future__ import annotations

from src.inspection.checklist import CHECKLIST_ITEMS
from src.inspection.report_builder import build_report
from src.inspection.schema import Finding


def _make_finding(
    checklist_item: str = "Boom, cylinders",
    defect_type: str = "corrosion",
    severity: str = "Moderate",
    confidence: float = 0.85,
    frame_index: int = 0,
) -> Finding:
    return Finding(
        checklist_item=checklist_item,
        defect_type=defect_type,
        severity=severity,
        description=f"Test {defect_type} on {checklist_item}",
        bbox=[0.5, 0.5, 0.1, 0.1],
        confidence=confidence,
        frame_index=frame_index,
    )


class TestBuildReport:
    def test_no_findings_all_pass(self):
        report = build_report([], ["frame_001.jpg"])
        assert report.summary.status == "PASS"
        assert len(report.items) == len(CHECKLIST_ITEMS)
        assert all(item.status == "PASS" for item in report.items)
        assert all(item.score == 0.0 for item in report.items)
        assert "No defects" in report.summary.notes

    def test_single_minor_finding_gives_monitor(self):
        findings = [_make_finding(severity="Minor")]
        report = build_report(findings, [])
        boom_item = next(i for i in report.items if i.id == "Boom, cylinders")
        assert boom_item.status == "MONITOR"

    def test_single_moderate_finding_gives_monitor(self):
        findings = [_make_finding(severity="Moderate")]
        report = build_report(findings, [])
        boom_item = next(i for i in report.items if i.id == "Boom, cylinders")
        assert boom_item.status == "MONITOR"

    def test_single_critical_finding_gives_fail(self):
        findings = [_make_finding(severity="Critical")]
        report = build_report(findings, [])
        boom_item = next(i for i in report.items if i.id == "Boom, cylinders")
        assert boom_item.status == "FAIL"

    def test_summary_uses_worst_status(self):
        findings = [
            _make_finding(checklist_item="Boom, cylinders", severity="Minor"),
            _make_finding(checklist_item="Radiator", severity="Critical"),
        ]
        report = build_report(findings, [])
        assert report.summary.status == "FAIL"

    def test_unaffected_items_are_pass(self):
        findings = [_make_finding(checklist_item="Boom, cylinders")]
        report = build_report(findings, [])
        bucket_item = next(i for i in report.items if i.id == "Bucket/GET")
        assert bucket_item.status == "PASS"
        assert bucket_item.score == 0.0

    def test_multiple_findings_same_item(self):
        findings = [
            _make_finding(checklist_item="Radiator", severity="Minor", confidence=0.6),
            _make_finding(checklist_item="Radiator", severity="Critical", confidence=0.95),
        ]
        report = build_report(findings, [])
        radiator = next(i for i in report.items if i.id == "Radiator")
        assert radiator.status == "FAIL"
        assert radiator.score == 0.95
        assert "2 defect(s)" in radiator.notes

    def test_evidence_frames_attached(self):
        frames = ["frame_001.jpg", "frame_002.jpg"]
        report = build_report([], frames)
        for item in report.items:
            assert item.evidence == frames

    def test_summary_notes_include_defect_types(self):
        findings = [
            _make_finding(defect_type="corrosion"),
            _make_finding(checklist_item="Radiator", defect_type="wear"),
        ]
        report = build_report(findings, [])
        assert "corrosion" in report.summary.notes
        assert "wear" in report.summary.notes

    def test_all_checklist_items_represented(self):
        findings = [_make_finding()]
        report = build_report(findings, [])
        report_ids = {item.id for item in report.items}
        for label in CHECKLIST_ITEMS:
            assert label in report_ids, f"Missing checklist item: {label}"

    def test_confidence_score_is_max(self):
        findings = [
            _make_finding(checklist_item="Carbody", confidence=0.4),
            _make_finding(checklist_item="Carbody", confidence=0.9),
            _make_finding(checklist_item="Carbody", confidence=0.6),
        ]
        report = build_report(findings, [])
        carbody = next(i for i in report.items if i.id == "Carbody")
        assert carbody.score == 0.9
