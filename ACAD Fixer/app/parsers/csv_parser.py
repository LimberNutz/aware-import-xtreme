import csv
import logging
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class CMLRow:
    pressure: Optional[str] = None
    temperature: Optional[str] = None
    material_grade: str = ""


@dataclass
class AssetRecord:
    equipment_id: str
    equipment_description: str = ""
    year_built: str = ""
    pipe_class: str = ""
    stress_table_used: str = ""
    pid_number: str = ""
    diameter_od: str = ""
    cml_rows: List[CMLRow] = field(default_factory=list)


def _get(row: dict, *keys, default: str = "") -> str:
    """Fetch first present key from row with case-insensitive fallback."""
    for k in keys:
        if k in row and row[k] is not None:
            return str(row[k]).strip()
    lowered = {k.lower(): v for k, v in row.items() if k}
    for k in keys:
        v = lowered.get(k.lower())
        if v is not None:
            return str(v).strip()
    return default


class GGCSVParser:
    """Parses GG CML import CSV.

    Header row: Equipment ID == asset_id -> captures header-level fields.
    Child rows: Equipment ID blank, typically contain CML Pressure/Temperature/Material Grade.
    Stops when a new non-empty Equipment ID appears.
    """

    def __init__(self, csv_path: str, asset_id: str):
        self.csv_path = csv_path
        self.asset_id = asset_id

    def parse(self) -> Optional[AssetRecord]:
        logging.info(f"Parsing CSV: {self.csv_path} for Asset: {self.asset_id}")
        try:
            with open(self.csv_path, mode="r", encoding="utf-8-sig", newline="") as f:
                reader = csv.DictReader(f)
                record: Optional[AssetRecord] = None
                collecting = False
                for row in reader:
                    eid = _get(row, "Equipment ID")
                    if eid == self.asset_id:
                        record = AssetRecord(
                            equipment_id=eid,
                            equipment_description=_get(row, "Equipment Description"),
                            year_built=_get(row, "Year Built"),
                            pipe_class=_get(row, "Class"),
                            stress_table_used=_get(row, "Stress Table Used", "Stress Table"),
                            pid_number=_get(row, "P&ID Number", "PID Number", "P&ID"),
                            diameter_od=_get(row, "CML Outside Diameter", "Diameter", "OD"),
                        )
                        collecting = True
                        self._add_cml_row(record, row)
                        continue
                    if collecting:
                        if eid and eid != self.asset_id:
                            break
                        self._add_cml_row(record, row)
                return record
        except Exception as e:
            logging.error(f"Failed to parse CSV: {e}")
            return None

    def _add_cml_row(self, record: AssetRecord, row: dict) -> None:
        pressure = _get(row, "CML Pressure", "CML Locations.CML Pressure", "Pressure")
        temp = _get(row, "CML Temperature", "CML Locations.CML Temperature", "Temperature")
        mat = _get(row, "Material Grade", "CML Locations.Material Grade", "CML Material Grade")
        if pressure or temp or mat:
            record.cml_rows.append(CMLRow(pressure=pressure, temperature=temp, material_grade=mat))
