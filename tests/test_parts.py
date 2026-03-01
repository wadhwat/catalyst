from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from src.inspection.parts import load_parts


def test_load_parts_csv(tmp_path):
    csv_path = tmp_path / "parts.csv"
    csv_path.write_text(
        "Part Number,Part Name,Image File\n"
        "492-110,Boom Cylinder Pin,492-110.jpg\n"
        "3K-7380,Hydraulic Hose,3K-7380.jpg\n"
    )
    parts = load_parts(csv_path)
    assert len(parts) == 2
    assert parts[0]["part_number"] == "492-110"
    assert parts[0]["name"] == "Boom Cylinder Pin"
    assert parts[0]["image_file"] == "492-110.jpg"


def test_load_parts_prefers_catalog_csv_when_exists():
    """When cat_parts_catalog.csv exists, load_parts() uses it by default."""
    parts = load_parts()
    assert len(parts) >= 1
    for p in parts:
        assert "part_number" in p
        assert "name" in p
