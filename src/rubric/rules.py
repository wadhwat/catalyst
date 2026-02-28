from __future__ import annotations

PASS_THRESHOLD = 0.3
MONITOR_THRESHOLD = 0.6


def status_from_score(score: float) -> str:
    if score >= MONITOR_THRESHOLD:
        return 'FAIL'
    if score >= PASS_THRESHOLD:
        return 'MONITOR'
    return 'PASS'


def worst_status(statuses: list[str]) -> str:
    order = {'PASS': 0, 'MONITOR': 1, 'FAIL': 2, 'UNKNOWN': 3}
    if not statuses:
        return 'UNKNOWN'
    return max(statuses, key=lambda s: order.get(s, 3))
