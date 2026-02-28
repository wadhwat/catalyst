from __future__ import annotations

from src.report.generate_baseline import ITEM_IDS, generate_baseline
from src.rubric.rules import MONITOR_THRESHOLD, PASS_THRESHOLD, status_from_score, worst_status


def test_status_from_score_boundaries() -> None:
    assert status_from_score(PASS_THRESHOLD - 0.01) == 'PASS'
    assert status_from_score(PASS_THRESHOLD) == 'MONITOR'
    assert status_from_score(MONITOR_THRESHOLD - 0.01) == 'MONITOR'
    assert status_from_score(MONITOR_THRESHOLD) == 'FAIL'


def test_worst_status() -> None:
    assert worst_status(['PASS', 'MONITOR']) == 'MONITOR'
    assert worst_status(['PASS', 'FAIL']) == 'FAIL'
    assert worst_status([]) == 'UNKNOWN'


def test_generate_baseline_structure() -> None:
    scores = {item_id: 0.0 for item_id in ITEM_IDS}
    scores['cooling_airflow'] = MONITOR_THRESHOLD
    scores['hoses_lines_leaks'] = MONITOR_THRESHOLD + 0.1

    report = generate_baseline(scores, evidence_frames=['frame_001.jpg'])
    assert report.summary.status == 'FAIL'
    assert len(report.items) == len(ITEM_IDS)

    item_ids = [item.id for item in report.items]
    assert item_ids == list(ITEM_IDS)

    for item in report.items:
        assert item.notes
        assert item.evidence == ['frame_001.jpg']
