"""
Ask GPT-4 (text-only) to turn our findings list into a structured report JSON.
Cheaper than vision calls — we already have the defect mappings from Qwen.
"""
from __future__ import annotations

import json
import logging
import os
import time
from typing import List

from openai import AsyncOpenAI

from src.inspection.checklist import CHECKLIST_ITEMS
from src.inspection.schema import Finding
from src.report.schema import Report, ReportItem, ReportSummary

logger = logging.getLogger(__name__)

_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI()
    return _client


def _get_model() -> str:
    return os.getenv("OPENAI_MODEL", "gpt-4o")


REPORT_SYSTEM_PROMPT = (
    "ROLE: You are a Heavy Equipment Safety Inspection Report Generator. "
    "You receive anomaly findings from an inspection and produce a structured report.\n\n"
    "SEVERITY MAPPING (align with protocol):\n"
    "- CRITICAL → status FAIL, do not operate. Structural cracks, missing hardware, "
    "pressure-hose failure, shining/rust streaks on load-bearing fasteners.\n"
    "- MODERATE → status MONITOR. Heavy wear, debris, minor pitting, minor chafing.\n"
    "- NORMAL → status PASS. Structurally sound, no actionable defect.\n\n"
    "REPORT RULES:\n"
    "- Output EVERY checklist item. No findings = PASS, score 0.0, notes \"No defects detected.\"\n"
    "- For items with findings: use worst severity, highest confidence as score, "
    "notes summarizing the defect with specific visual tells (e.g., dry rot, shining).\n"
    "- Summary status: FAIL if any CRITICAL, else MONITOR if any MODERATE, else PASS.\n"
    "- Summary notes: If CRITICAL exists, include Lock-out/Tag-out (LOTO) and repair priority. "
    "If all NORMAL, provide a Ready to Operate summary. Otherwise state finding count and risk areas.\n\n"
    "Allowed checklist items:\n"
    + "\n".join(f"- {item}" for item in CHECKLIST_ITEMS)
)

REPORT_RESPONSE_SCHEMA = {
    "type": "json_schema",
    "json_schema": {
        "name": "inspection_report",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "summary": {
                    "type": "object",
                    "properties": {
                        "status": {
                            "type": "string",
                            "enum": ["PASS", "MONITOR", "FAIL"],
                        },
                        "notes": {"type": "string"},
                    },
                    "required": ["status", "notes"],
                    "additionalProperties": False,
                },
                "items": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "status": {
                                "type": "string",
                                "enum": ["PASS", "MONITOR", "FAIL"],
                            },
                            "score": {"type": "number"},
                            "notes": {"type": "string"},
                        },
                        "required": ["id", "status", "score", "notes"],
                        "additionalProperties": False,
                    },
                },
            },
            "required": ["summary", "items"],
            "additionalProperties": False,
        },
    },
}


def _findings_to_text(findings: List[Finding]) -> str:
    if not findings:
        return "No defect findings. All checklist items should be PASS."
    lines: list[str] = []
    for i, f in enumerate(findings, 1):
        lines.append(
            f"{i}. [{f.checklist_item}] {f.defect_type} — "
            f"severity={f.severity}, confidence={f.confidence:.2f}, "
            f"frame={f.frame_index}: {f.description}"
        )
    return "\n".join(lines)


async def generate_report_via_llm(
    findings: List[Finding],
    evidence_frames: List[str],
) -> tuple[Report, float]:
    """
    Feed findings to GPT-4 and get back a clean Report. Uses structured output
    so we get valid JSON every time. Routes fall back to report_builder if this fails.
    """
    findings_text = _findings_to_text(findings)
    user_message = (
        f"Here are the inspection findings:\n\n{findings_text}\n\n"
        f"Generate the full inspection report JSON covering all "
        f"{len(CHECKLIST_ITEMS)} checklist items. Apply the protocol: "
        f"CRITICAL → LOTO and repair priority in summary; all NORMAL → Ready to Operate."
    )

    t0 = time.perf_counter()
    try:
        client = _get_client()
        response = await client.chat.completions.create(
            model=_get_model(),
            messages=[
                {"role": "system", "content": REPORT_SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            response_format=REPORT_RESPONSE_SCHEMA,
            temperature=0.1,
            max_tokens=4096,
        )
        elapsed_ms = (time.perf_counter() - t0) * 1000
        logger.info("GPT-4 report generation: %.0f ms", elapsed_ms)

        raw = response.choices[0].message.content
        if not raw:
            raise ValueError("Empty GPT-4 response")

        parsed = json.loads(raw)

        items = [
            ReportItem(
                id=item["id"],
                status=item["status"],
                score=item["score"],
                notes=item["notes"],
                evidence=evidence_frames,
            )
            for item in parsed["items"]
        ]

        report = Report(
            summary=ReportSummary(
                status=parsed["summary"]["status"],
                notes=parsed["summary"]["notes"],
            ),
            items=items,
        )

        return report, elapsed_ms

    except Exception as exc:
        elapsed_ms = (time.perf_counter() - t0) * 1000
        logger.error("GPT-4 report generation failed after %.0f ms: %s", elapsed_ms, exc)
        raise
