from __future__ import annotations

from typing import Dict, List, Optional

from src.report.schema import Report, ReportItem, ReportSummary
from src.rubric.rules import status_from_score, worst_status


ITEM_IDS = (
    'tires_wheels',
    'bucket_attachment',
    'lift_arms_pins',
    'hoses_lines_leaks',
    'articulation_driveline',
    'undercarriage_leaks',
    'cooling_airflow',
    'cab_body_glass',
    'steps_holds',
    'engine_bay_leaks_debris',
)

NOTES = {
    'tires_wheels': {
        'PASS': 'Tires and wheels appear intact with no obvious cuts, debris, or loose lugs.',
        'MONITOR': 'Possible tire damage or debris in tread/sidewall; recheck inflation and lugs.',
        'FAIL': 'Severe tire damage, missing lugs, or visible leaks detected.',
    },
    'bucket_attachment': {
        'PASS': 'Bucket cutting edge and attachment points look normal.',
        'MONITOR': 'Wear or minor damage visible on bucket or cutting edge.',
        'FAIL': 'Cracks, missing parts, or major bucket damage detected.',
    },
    'lift_arms_pins': {
        'PASS': 'Lift arms and pins show no visible wear or loose fittings.',
        'MONITOR': 'Possible wear at pins or grease fittings; inspect closely.',
        'FAIL': 'Broken fittings or significant wear visible on lift arms or pins.',
    },
    'hoses_lines_leaks': {
        'PASS': 'No visible hose leaks; couplings and clamps look secure.',
        'MONITOR': 'Possible seepage or loose clamps visible; inspect hoses and fittings.',
        'FAIL': 'Active leak or damaged hose/line detected.',
    },
    'articulation_driveline': {
        'PASS': 'Articulation area and driveline show no obvious damage.',
        'MONITOR': 'Signs of wear around the articulation area; monitor condition.',
        'FAIL': 'Visible damage or misalignment in articulation/driveline area.',
    },
    'undercarriage_leaks': {
        'PASS': 'No visible leaks or damage under the machine.',
        'MONITOR': 'Possible seepage under the machine; inspect further.',
        'FAIL': 'Visible leaks or significant damage under the machine.',
    },
    'cooling_airflow': {
        'PASS': 'Screens, radiator, and fan area appear clear and undamaged.',
        'MONITOR': 'Some debris or minor fin damage visible; clean and recheck.',
        'FAIL': 'Heavy blockage, bent fins, or fan damage detected.',
    },
    'cab_body_glass': {
        'PASS': 'Cab glass and body panels appear intact.',
        'MONITOR': 'Minor glass damage or body wear visible.',
        'FAIL': 'Broken glass or significant cab/body damage detected.',
    },
    'steps_holds': {
        'PASS': 'Steps and handholds appear clean and intact.',
        'MONITOR': 'Debris or minor damage on steps/handholds; clean or tighten.',
        'FAIL': 'Broken or missing steps/handholds detected.',
    },
    'engine_bay_leaks_debris': {
        'PASS': 'Engine bay looks clean with no visible leaks.',
        'MONITOR': 'Some debris or minor seepage visible; inspect components.',
        'FAIL': 'Heavy debris buildup or clear leaks in the engine bay.',
    },
}


def generate_baseline(
    scores: Dict[str, float],
    evidence_frames: Optional[List[str]] = None,
) -> Report:
    evidence_frames = evidence_frames or []
    items: List[ReportItem] = []
    statuses: List[str] = []

    for item_id in ITEM_IDS:
        score = float(scores.get(item_id, 0.0))
        status = status_from_score(score)
        statuses.append(status)
        notes = NOTES.get(item_id, {}).get(status, 'No notes available.')
        items.append(
            ReportItem(
                id=item_id,
                status=status,
                score=score,
                notes=notes,
                evidence=evidence_frames,
            )
        )

    summary_status = worst_status(statuses)
    summary_notes = 'Baseline rubric (no VLM/LLM reasoning yet).'
    summary = ReportSummary(status=summary_status, notes=summary_notes)
    return Report(summary=summary, items=items)
