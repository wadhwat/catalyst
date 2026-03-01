"""
Load scraped parts inventory for GPT report generation.
Supports CSV (Part Number, Part Name, Image File) or JSON.
Defaults to cat_parts_catalog.csv when present.
"""
from __future__ import annotations

import csv
import json
import logging
import os
from pathlib import Path
from typing import Any, List

logger = logging.getLogger(__name__)

_DEFAULT_CSV_PATH = Path("cat_parts_catalog.csv")
_DEFAULT_JSON_PATH = Path("data") / "parts.json"


def load_parts(path: str | Path | None = None) -> List[dict[str, Any]]:
    """
    Load parts inventory from CSV or JSON.
    Returns empty list if no file found or invalid.
    CSV format: Part Number, Part Name, Image File (e.g. scraped_cat_parts/7K-1181.jpg)
    JSON format: [{"part_number": "...", "name": "...", ...}, ...]
    """
    if path is not None:
        p = Path(path)
    elif os.getenv("PARTS_CSV_PATH"):
        p = Path(os.getenv("PARTS_CSV_PATH"))
    elif os.getenv("PARTS_JSON_PATH"):
        p = Path(os.getenv("PARTS_JSON_PATH"))
    elif _DEFAULT_CSV_PATH.exists():
        p = _DEFAULT_CSV_PATH
    else:
        p = _DEFAULT_JSON_PATH

    if not p.exists():
        logger.debug("Parts file not found: %s", p)
        return []

    suffix = p.suffix.lower()
    if suffix == ".csv":
        return _load_parts_csv(p)
    return _load_parts_json(p)


def _load_parts_csv(p: Path) -> List[dict[str, Any]]:
    """Parse CSV with columns: Part Number, Part Name, Image File."""
    try:
        with open(p, encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        out: List[dict[str, Any]] = []
        for r in rows:
            pn = r.get("Part Number", r.get("part_number", "")).strip()
            name = r.get("Part Name", r.get("name", r.get("Part Name", ""))).strip()
            img = r.get("Image File", r.get("image_file", "")).strip()
            if pn and name:
                part: dict[str, Any] = {"part_number": pn, "name": name}
                if img:
                    part["image_file"] = img
                out.append(part)
        return out
    except Exception as exc:
        logger.warning("Failed to load parts CSV from %s: %s", p, exc)
        return []


def _load_parts_json(p: Path) -> List[dict[str, Any]]:
    """Parse JSON array of part objects."""
    try:
        with open(p, encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list):
            logger.warning("Parts JSON must be an array, got %s", type(data).__name__)
            return []
        out: List[dict[str, Any]] = []
        for item in data:
            if isinstance(item, dict):
                pn = item.get("part_number", item.get("partNumber", ""))
                name = item.get("name", item.get("description", ""))
                if pn or name:
                    out.append({"part_number": str(pn), "name": str(name), **item})
        return out
    except Exception as exc:
        logger.warning("Failed to load parts from %s: %s", p, exc)
        return []
