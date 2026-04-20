import csv
import os
from collections import OrderedDict
from models.cml_row import CMLRow, EntityInfoRow
from app.constants import AWARE_CSV_HEADERS


def export_csv(
    rows: list[CMLRow],
    output_path: str,
    entity_rows: list[EntityInfoRow] | None = None,
    progress_callback=None,
) -> tuple[int, list[str]]:
    # write rows to CSV with Aware header order
    # returns (rows_written, errors)
    errors: list[str] = []
    rows_written = 0
    rows_skipped = 0
    entity_map = _build_entity_map(entity_rows or [])
    grouped_rows = _group_rows_by_entity(rows)
    total_groups = len(grouped_rows)

    try:
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=AWARE_CSV_HEADERS, extrasaction="ignore")
            writer.writeheader()

            for group_idx, (entity_key, entity_rows_for_system) in enumerate(grouped_rows.items()):
                if progress_callback:
                    progress_callback(group_idx + 1, total_groups)
                entity = entity_map.get(entity_key)
                writer.writerow(_map_entity_row_to_csv(entity_rows_for_system[0], entity))
                rows_written += 1

                for row in entity_rows_for_system:
                    # Skip blank/spacer rows that have no CML Location
                    # (e.g. empty rows between component groups in UT sheets).
                    # This only affects the CSV output — source data is untouched.
                    if not row.cml_location.strip():
                        rows_skipped += 1
                        continue
                    writer.writerow(_map_cml_row_to_csv(row))
                    rows_written += 1

    except Exception as e:
        errors.append(f"CSV export error: {e}")

    if rows_skipped:
        errors.append(f"INFO: Skipped {rows_skipped} blank row(s) with no CML Location.")

    return rows_written, errors


def _build_entity_map(entity_rows: list[EntityInfoRow]) -> dict[tuple[str, str], EntityInfoRow]:
    mapped: dict[tuple[str, str], EntityInfoRow] = {}
    for row in entity_rows:
        mapped[_entity_key(row.system_path, row.system_name)] = row
    return mapped


def _entity_key(system_path: str, system_name: str) -> tuple[str, str]:
    return system_path.strip(), system_name.strip()


def _row_entity_key(row: CMLRow) -> tuple[str, str]:
    return _entity_key(row.system_path, row.system_name)


def _group_rows_by_entity(rows: list[CMLRow]) -> OrderedDict[tuple[str, str], list[CMLRow]]:
    grouped: OrderedDict[tuple[str, str], list[CMLRow]] = OrderedDict()
    for row in rows:
        key = _row_entity_key(row)
        grouped.setdefault(key, []).append(row)
    return grouped


def _blank_csv_row() -> dict[str, str]:
    return {header: "" for header in AWARE_CSV_HEADERS}


def _map_entity_row_to_csv(row: CMLRow, entity: EntityInfoRow | None = None) -> dict[str, str]:
    csv_row = _blank_csv_row()
    csv_row.update({
        "SystemPath": row.system_path,
        "SystemName": entity.system_name if entity else row.system_name,
        "SystemType": entity.system_type if entity else row.system_type,
        "Equipment ID": entity.equipment_id if entity else row.equipment_id,
        "National Board Number": "",
        "Serial Number": "",
        "Model Number": "",
        "Manufacturer Drawing": "",
        "U-1 Form": "",
        "Name Plate": "",
        "Code Stamp": "",
        "Joint Efficiency": "1.0",
        "Year Built": entity.year_built if entity else "",
        "InService": entity.in_service if entity else "",
        "InService Date": entity.in_service_date if entity else "",
        "Class": entity.class_name if entity else "",
        "Stress Table Used": entity.stress_table_used if entity else "",
        "PID Drawing": entity.pid_drawing if entity else "",
        "PFD": entity.pfd if entity else "",
        "PID Number": entity.pid_number if entity else "",
        "PFD Number": entity.pfd_number if entity else "",
        "PSM Covered": entity.psm_covered if entity else "",
        "Height / Length": "",
        "Diameter": entity.diameter if entity else "",
        "Test Pressure": "",
        "Number of Shell Courses": "",
        "Number of Heads/Covers": "",
        "Number of Nozzles": "",
        "Internal Entry Possible": "",
        "Equipment Description": entity.equipment_description if entity else "",
    })
    return csv_row


def _map_cml_row_to_csv(row: CMLRow) -> dict[str, str]:
    csv_row = _blank_csv_row()
    csv_row.update({
        "SystemPath": row.system_path,
        "CML Locations.CML": row.cml,
        "CML Locations.CML Location": row.cml_location,
        "CML Locations.Component Type": row.component_type,
        "CML Locations.Component": row.component,
        "CML Locations.Outside Diameter": row.od,
        "CML Locations.Nominal Thickness": row.nom,
        "CML Locations.Corrosion Allowance": row.ca,
        "CML Locations.T-Min ": row.tmin,
        "CML Locations.Material Spec": row.mat_spec,
        "CML Locations.Material Grade": row.mat_grade,
        "CML Locations.CML Pressure": row.pressure,
        "CML Locations.CML Temperature": row.temp,
        "CML Locations.CML Joint Efficiency": "1.0",
        "CML Locations.CML Access": row.access,
        "CML Locations.Insulation": row.insulation,
        "CML Locations.CML Installed On": row.install_date,
        "CML Locations.CML Status": row.status,
        "CML Locations.NDE Type": row.nde,
        "CML Locations.First Insp Date": "",
        "CML Locations.First UT Reading": "",
        "CML Locations.Last Insp Date": "",
        "CML Locations.Last UT Reading": "",
    })
    return csv_row


def _map_row_to_csv(row: CMLRow, entity: EntityInfoRow | None = None) -> dict[str, str]:
    return {
        "SystemPath": row.system_path,
        "National Board Number": "",
        "Serial Number": "",
        "Model Number": "",
        "Manufacturer Drawing": "",
        "U-1 Form": "",
        "Name Plate": "",
        "Code Stamp": "",
        "Joint Efficiency": "1.0",
        "Year Built": entity.year_built if entity else "",
        "InService": entity.in_service if entity else "",
        "InService Date": entity.in_service_date if entity else "",
        "Class": entity.class_name if entity else "",
        "Stress Table Used": entity.stress_table_used if entity else "",
        "PID Drawing": entity.pid_drawing if entity else "",
        "PFD": entity.pfd if entity else "",
        "PID Number": entity.pid_number if entity else "",
        "PFD Number": entity.pfd_number if entity else "",
        "PSM Covered": entity.psm_covered if entity else "",
        "Height / Length": "",
        "Diameter": entity.diameter if entity else "",
        "Test Pressure": "",
        "Number of Shell Courses": "",
        "Number of Heads/Covers": "",
        "Number of Nozzles": "",
        "Internal Entry Possible": "",
        "": "",
        "Equipment Description": entity.equipment_description if entity else "",
        "CML Locations.CML": row.cml,
        "CML Locations.CML Location": row.cml_location,
        "CML Locations.Component Type": row.component_type,
        "CML Locations.Component": row.component,
        "CML Locations.Outside Diameter": row.od,
        "CML Locations.Nominal Thickness": row.nom,
        "CML Locations.Corrosion Allowance": row.ca,
        "CML Locations.T-Min ": row.tmin,
        "CML Locations.Material Spec": row.mat_spec,
        "CML Locations.Material Grade": row.mat_grade,
        "CML Locations.CML Pressure": row.pressure,
        "CML Locations.CML Temperature": row.temp,
        "CML Locations.CML Joint Efficiency": "1.0",
        "CML Locations.CML Access": row.access,
        "CML Locations.Insulation": row.insulation,
        "CML Locations.CML Installed On": row.install_date,
        "CML Locations.CML Status": row.status,
        "CML Locations.NDE Type": row.nde,
        "CML Locations.First Insp Date": "",
        "CML Locations.First UT Reading": "",
        "CML Locations.Last Insp Date": "",
        "CML Locations.Last UT Reading": "",
    }


# --- Inspection Frequency CSV export ---

# Column headers for the Aware inspection frequency import file
_INSP_FREQ_HEADERS = [
    "SystemPath",
    "SystemName",
    "Inspection Frequencies.Insp Frequency (yrs)",
    "Inspection Frequencies.Inspection Type",
]

# Class-based frequency mapping: class_name -> [(frequency, inspection_type), ...]
# Class 4 is intentionally omitted — those systems are skipped during export.
_CLASS_FREQ_MAP = {
    "Class 1": [
        ("5", "External Inspection"),
        ("5", "Thickness Measurements"),
    ],
    "Class 2": [
        ("5", "External Inspection"),
        ("10", "Thickness Measurements"),
    ],
    "Class 3": [
        ("10", "External Inspection"),
        ("10", "Thickness Measurements"),
    ],
}


def build_inspection_freq_rows(
    entity_rows: list[EntityInfoRow],
) -> tuple[list[dict[str, str]], list[str]]:
    """Build inspection frequency rows from entity data.

    Returns (rows, warnings) where each row is a dict with the 4 frequency columns.
    Class 4 systems are skipped and flagged in warnings.
    """
    freq_rows: list[dict[str, str]] = []
    warnings: list[str] = []

    for entity in entity_rows:
        class_name = entity.class_name.strip()
        system_path = entity.system_path.strip()
        system_name = entity.system_name.strip()

        if not system_name:
            continue

        freq_entries = _CLASS_FREQ_MAP.get(class_name)

        if freq_entries is None:
            # Class 4 or unrecognised class — skip and warn
            warnings.append(
                f"[{system_name}] Class '{class_name}' has no auto-assigned "
                f"inspection frequency — requires manual/client input."
            )
            continue

        # Two rows per system: External Inspection + Thickness Measurements
        for frequency, insp_type in freq_entries:
            freq_rows.append({
                "SystemPath": system_path,
                "SystemName": system_name,
                "Inspection Frequencies.Insp Frequency (yrs)": frequency,
                "Inspection Frequencies.Inspection Type": insp_type,
            })

    return freq_rows, warnings


def export_inspection_freq_csv(
    entity_rows: list[EntityInfoRow],
    output_path: str,
) -> tuple[int, list[str]]:
    """Write a standalone inspection frequency CSV for Aware import.

    Returns (rows_written, errors/warnings).
    """
    freq_rows, warnings = build_inspection_freq_rows(entity_rows)
    errors: list[str] = list(warnings)
    rows_written = 0

    if not freq_rows:
        errors.append("No inspection frequency rows to export (no qualifying entities).")
        return 0, errors

    try:
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=_INSP_FREQ_HEADERS)
            writer.writeheader()
            for row in freq_rows:
                writer.writerow(row)
                rows_written += 1
    except Exception as e:
        errors.append(f"Inspection frequency CSV export error: {e}")

    return rows_written, errors
