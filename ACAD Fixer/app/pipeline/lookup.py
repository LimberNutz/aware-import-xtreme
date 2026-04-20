"""Lookup generation and file I/O."""
import logging
from pathlib import Path
from typing import Dict

from app.parsers.csv_parser import AssetRecord
from app.domain.formatters import (
    MaterialClassifier,
    ODConverter,
    TemperatureFormatter,
    DesignCodeExtractor,
    ClassCleaner,
    to_max_numeric,
)


def build_lookup(record: AssetRecord) -> Dict[str, str]:
    """Build lookup dict keyed by DXF attribute tags."""
    mat_grades = ", ".join(
        r.material_grade for r in record.cml_rows if r.material_grade
    )
    material = MaterialClassifier.classify(mat_grades)
    design_press = to_max_numeric(r.pressure for r in record.cml_rows)
    design_temp_raw = to_max_numeric(r.temperature for r in record.cml_rows)

    desc = record.equipment_description or ""
    # Only split if description is too long for one line (>40 chars).
    # Prefer splitting on '/' if present, else hard wrap at 40 chars.
    LINE_MAX = 40
    if len(desc) <= LINE_MAX:
        circuit1, circuit2 = desc.strip(), ""
    elif "/" in desc:
        d1, _, d2 = desc.partition("/")
        circuit1, circuit2 = d1.strip(), d2.strip()
    else:
        circuit1, circuit2 = desc[:LINE_MAX].strip(), desc[LINE_MAX:80].strip()

    return {
        "EQUIPMENT_ID": record.equipment_id,
        "CIRCUIT_DESC1": circuit1,
        "CIRCUIT_DESC2": circuit2,
        "YEAR_BLT": record.year_built,
        "CLASS": ClassCleaner.clean(record.pipe_class),
        "B31_TYPE": DesignCodeExtractor.extract(record.stress_table_used),
        "PID_NUMBER": record.pid_number,
        "OD_IN": ODConverter.to_nominal(record.diameter_od),
        "PRESSURE": design_press,
        "TEMPERATURE": TemperatureFormatter.for_dwg(design_temp_raw),
        "TEMPERATURE_PDF": TemperatureFormatter.for_pdf(design_temp_raw),
        "PRESSURE_RAW": design_press,
        "MATERIAL": material,
    }


def write_lookup_file(lookup: Dict[str, str], out_dir: Path, asset_id: str) -> Path:
    """Write GG_<ASSET_ID>_lookup.txt KEY=VALUE file."""
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"GG_{asset_id}_lookup.txt"
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        for k, v in lookup.items():
            f.write(f"{k}={v}\n")
    logging.info(f"Wrote lookup: {path}")
    return path


def read_lookup_file(path: Path) -> Dict[str, str]:
    result: Dict[str, str] = {}
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n").rstrip("\r")
            if not line or line.startswith("#"):
                continue
            k, _, v = line.partition("=")
            result[k.strip()] = v
    return result
