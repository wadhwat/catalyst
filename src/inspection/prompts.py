from __future__ import annotations

from src.inspection.checklist import CHECKLIST_ITEMS

VLM_SYSTEM_PROMPT = (
    "You are an expert heavy-equipment inspector specializing in Caterpillar "
    "Mini Hydraulic Excavators. You will receive an image of the machine along "
    "with YOLO-detected bounding boxes for corrosion-like defects. For each "
    "detection:\n"
    "1. Assign exactly ONE checklist_item from the allowed list below. If the "
    "component is ambiguous, use \"Overall machine\".\n"
    "2. Confirm whether corrosion or a defect is truly visible at that location "
    "(confirmed: true/false).\n"
    "3. Assign severity: \"Minor\", \"Moderate\", or \"Critical\".\n"
    "4. Write a concise one-sentence description of the defect.\n\n"
    "Return ONLY valid JSON matching the schema. No extra text.\n\n"
    "Allowed checklist items:\n"
    + "\n".join(f"- {item}" for item in CHECKLIST_ITEMS)
)

VLM_RESPONSE_SCHEMA = {
    "type": "json_schema",
    "json_schema": {
        "name": "vlm_defect_mapping",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "mapped_defects": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "detection_id": {"type": "integer"},
                            "checklist_item": {"type": "string"},
                            "defect_type": {"type": "string"},
                            "confirmed": {"type": "boolean"},
                            "severity": {
                                "type": "string",
                                "enum": ["Minor", "Moderate", "Critical"],
                            },
                            "description": {"type": "string"},
                            "bbox": {
                                "type": "array",
                                "items": {"type": "number"},
                            },
                        },
                        "required": [
                            "detection_id",
                            "checklist_item",
                            "defect_type",
                            "confirmed",
                            "severity",
                            "description",
                            "bbox",
                        ],
                        "additionalProperties": False,
                    },
                },
            },
            "required": ["mapped_defects"],
            "additionalProperties": False,
        },
    },
}


def build_vlm_user_message(
    detections_text: str,
) -> str:
    return (
        "YOLO detections on this frame:\n"
        f"{detections_text}\n\n"
        "Map each detection to the appropriate checklist item and assess "
        "the defect. Return the JSON."
    )


def format_detections_block(
    detections: list[dict],
) -> str:
    lines: list[str] = []
    for det in detections:
        bbox_str = "[" + ", ".join(f"{v:.4f}" for v in det["bbox"]) + "]"
        lines.append(
            f"det_{det['detection_id']}: "
            f"class={det['class_name']}, "
            f"conf={det['confidence']:.2f}, "
            f"bbox={bbox_str}"
        )
    return "\n".join(lines)
