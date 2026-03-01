"""
Caterpillar Mini Hydraulic Excavator inspection checklist. VLM output must
map to one of these labels; anything else gets normalized to "Overall machine".
"""
from __future__ import annotations

CHECKLIST_ITEMS: list[str] = [
    # Exterior / walkaround
    "Bucket/GET",
    "Bucket cylinder & linkage",
    "Stick, cylinder",
    "Boom, cylinders",
    "Underneath of machine",
    "Final drive leaks/swing drive leaks area",
    "Carbody",
    "Camera",
    "Undercarriage",
    "Steps & handholds",
    "Batteries & hold downs",
    "Windshield wipers & washers",
    "Fire extinguisher",
    "Engine coolant",
    "Primary fuel filter",
    "Air filter",
    "Hydraulic oil tank",
    "Hydraulic pilot oil filter",
    "Radiator",
    "Hydraulic oil cooler",
    "AC condenser",
    "Lights",
    "Mirrors",
    "Engine oil filter",
    "Hydraulic oil filters",
    "Overall machine",
    # Engine compartment or platforms
    "Engine oil",
    "Swing gear oil",
    "Fuel tank",
    "All hoses",
    "All belts",
    "Overall engine compartment",
    # Inside the cab
    "Seat",
    "Seat belt & mounting",
    "Horn/travel alarm/lights",
    "Indicators",
    "Monitor panel",
    "Switches",
    "Travel controls",
    "Mirrors",
    "Heating system",
    "ROPS",
    "Cooling system",
    "Overall cab interior",
]

CHECKLIST_SET: frozenset[str] = frozenset(CHECKLIST_ITEMS)
