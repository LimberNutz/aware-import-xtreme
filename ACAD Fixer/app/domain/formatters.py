import logging
import re
from typing import Dict, Optional


class MaterialClassifier:
    """Classifies ASTM material grades into Carbon (C), Stainless (SS), or C/SS."""

    CARBON_PATTERNS = [
        r"\bA106\b", r"\bA53\b", r"\bA234\b", r"WPB", r"WPA", r"WPC",
        r"\bGR\.?\s*B\b", r"\bGR\.?\s*A\b", r"\bGR\.?\s*C\b", r"CARBON",
        r"\bB\b",  # ASTM grade B
    ]
    SS_PATTERNS = [
        r"\bA312\b", r"\bA403\b", r"TP304", r"TP316", r"TP321", r"TP347",
        r"WP304", r"WP316", r"\b304L?\b", r"\b316L?\b", r"\bSS\b",
        r"STAINLESS",
    ]

    @classmethod
    def classify(cls, material_grades: str) -> str:
        if not material_grades:
            return ""
        grades = material_grades.upper()
        is_carbon = any(re.search(p, grades) for p in cls.CARBON_PATTERNS)
        is_ss = any(re.search(p, grades) for p in cls.SS_PATTERNS)
        if is_carbon and is_ss:
            return "C/SS"
        if is_carbon:
            return "C"
        if is_ss:
            return "SS"
        return "Unknown"


class ODConverter:
    """Maps OD (inches) to nominal pipe size labels."""

    MAPPINGS = {
        0.840: '1/2"',
        1.050: '3/4"',
        1.315: '1"',
        1.660: '1-1/4"',
        1.900: '1-1/2"',
        2.375: '2"',
        2.875: '2-1/2"',
        3.500: '3"',
        4.000: '3-1/2"',
        4.500: '4"',
        5.563: '5"',
        6.625: '6"',
        8.625: '8"',
        10.750: '10"',
        12.750: '12"',
        14.000: '14"',
        16.000: '16"',
    }

    @classmethod
    def to_nominal(cls, od_str: str) -> str:
        if not od_str:
            return ""
        cleaned = str(od_str).replace('"', "").strip()
        try:
            val = float(cleaned)
        except ValueError:
            return od_str
        # Tolerate small float drift
        for od_val, nominal in cls.MAPPINGS.items():
            if abs(od_val - val) < 0.005:
                return nominal
        return f'{val}"'


class TemperatureFormatter:
    """Formats temperature values for DWG (NNN%%D) and PDF (NNN°)."""

    @staticmethod
    def _num(val: str) -> Optional[str]:
        if val is None:
            return None
        s = str(val).strip()
        if not s:
            return None
        m = re.search(r"-?\d+(?:\.\d+)?", s)
        if not m:
            return None
        try:
            f = float(m.group(0))
            return str(int(f)) if f.is_integer() else str(f)
        except ValueError:
            return None

    @classmethod
    def for_dwg(cls, val: str) -> str:
        n = cls._num(val)
        return f"{n}%%D" if n else ""

    @classmethod
    def for_pdf(cls, val: str) -> str:
        n = cls._num(val)
        return f"{n}\u00B0" if n else ""


class DesignCodeExtractor:
    """Extracts B31 suffix from stress table text (e.g. '2014 B31.3 (Carbon Steel)' -> '3')."""

    @staticmethod
    def extract(stress_table: str) -> str:
        if not stress_table:
            return ""
        m = re.search(r"B31\.(\d+)", stress_table)
        return m.group(1) if m else ""


class ClassCleaner:
    """Strip 'Class ' prefix from Class column."""

    @staticmethod
    def clean(val: str) -> str:
        if not val:
            return ""
        return re.sub(r"^\s*Class\s+", "", str(val), flags=re.IGNORECASE).strip()


def to_max_numeric(values) -> str:
    """Return string of max numeric value from iterable (ignoring blanks/non-numeric)."""
    best = None
    for v in values:
        if v is None:
            continue
        s = str(v).strip()
        if not s:
            continue
        m = re.search(r"-?\d+(?:\.\d+)?", s)
        if not m:
            continue
        try:
            f = float(m.group(0))
        except ValueError:
            continue
        if best is None or f > best:
            best = f
    if best is None:
        return ""
    return str(int(best)) if best.is_integer() else str(best)

