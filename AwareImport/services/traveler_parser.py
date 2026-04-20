"""Parse an API-570 Traveler spreadsheet to extract entity-level metadata.

The traveler workbook contains a sheet named "API-570 Traveler" with headers
in row 6 and data starting at row 7.  Columns are identified by header name
(case-insensitive) so the parser tolerates inserted/reordered columns.

Required headers (used for Info Page Builder):
    ENTITY       → lookup key (upper-cased)
    DESCRIPTION  → equipment_description
    P&ID         → pid_number
    CLASS        → class_name

Optional headers (used for UT/DR sheet detection):
    TECH         → if "N/A" → no UT sheet for this entity
    UTDATE       → if "N/A" → no UT sheet for this entity
    DR BY        → if populated → entity has a DR Thickness sheet
    DR DATE      → if populated → entity has a DR Thickness sheet

Returns a lookup dict keyed by upper-cased entity name.
"""

import os
from utils.helpers import safe_str, temp_open_workbook

# Stop reading after this many consecutive blank entity names
_MAX_BLANK_RUN = 5

# Target sheet name (case-insensitive)
_SHEET_NAME = "api-570 traveler"

# Header names → dict keys (all compared lower-cased)
_HEADER_MAP = {
    "entity": "entity",
    "description": "description",
    "p&id": "pid_number",
    "class": "class_name",
    "tech": "tech",
    "utdate": "utdate",
    "dr by": "dr_by",
    "dr date": "dr_date",
}


def parse_traveler(file_path: str) -> tuple[dict[str, dict[str, str]], list[str]]:
    """Parse the traveler spreadsheet and return entity metadata.

    Parameters
    ----------
    file_path : str
        Path to the .xlsx / .xlsm workbook.

    Returns
    -------
    tuple[dict, list[str]]
        - dict mapping UPPER-CASED entity name → {
              "equipment_description": str,
              "pid_number": str,
              "class_name": str,
              "has_ut_sheet": bool,
              "has_dr_sheet": bool,
          }
        - list of warning/error strings
    """
    data: dict[str, dict[str, str]] = {}
    errors: list[str] = []

    if not file_path or not os.path.exists(file_path):
        errors.append(f"Traveler file not found: {file_path}")
        return data, errors

    try:
        with temp_open_workbook(file_path, data_only=True, read_only=True) as wb:
            sheet = _find_traveler_sheet(wb)
            if sheet is None:
                errors.append(
                    f"No '{_SHEET_NAME}' sheet found in {os.path.basename(file_path)}. "
                    f"Available sheets: {', '.join(wb.sheetnames)}"
                )
                return data, errors

            # --- Detect columns from header row (row 6) ---
            col_map = _detect_header_columns(sheet)
            if "entity" not in col_map:
                errors.append(
                    f"No 'ENTITY' header found in row 6 of the traveler sheet. "
                    f"Cannot parse entity data."
                )
                return data, errors

            entity_col = col_map["entity"]

            # --- Read data rows starting at row 7 ---
            blank_run = 0
            for row in sheet.iter_rows(min_row=7, values_only=True):
                entity_name = _cell(row, entity_col).strip()

                if not entity_name:
                    blank_run += 1
                    if blank_run >= _MAX_BLANK_RUN:
                        break
                    continue
                else:
                    blank_run = 0

                description = _cell(row, col_map.get("description"))
                pid_number = _cell(row, col_map.get("pid_number"))
                class_name = _cell(row, col_map.get("class_name"))
                tech = _cell(row, col_map.get("tech"))
                utdate = _cell(row, col_map.get("utdate"))
                dr_by = _cell(row, col_map.get("dr_by"))
                dr_date = _cell(row, col_map.get("dr_date"))

                # UT sheet detection: N/A in TECH or UTDATE means no UT sheet
                has_ut = not (
                    tech.upper() == "N/A" or utdate.upper() == "N/A"
                )

                # DR sheet detection: DR BY and DR DATE both populated
                has_dr = bool(dr_by) and bool(dr_date)

                key = entity_name.upper()
                data[key] = {
                    "equipment_description": description,
                    "pid_number": pid_number,
                    "class_name": class_name,
                    "has_ut_sheet": has_ut,
                    "has_dr_sheet": has_dr,
                }

    except Exception as exc:
        errors.append(f"Failed to parse traveler: {exc}")

    return data, errors


def _find_traveler_sheet(wb):
    """Find the API-570 Traveler sheet by case-insensitive name match."""
    for sheet_name in wb.sheetnames:
        if sheet_name.strip().lower() == _SHEET_NAME:
            return wb[sheet_name]
    return None


def _detect_header_columns(sheet) -> dict[str, int]:
    """Read row 6 and return a mapping of field key → column index."""
    col_map: dict[str, int] = {}
    for row in sheet.iter_rows(min_row=6, max_row=6, values_only=True):
        for idx, cell in enumerate(row):
            header = safe_str(cell).strip().lower()
            if header in _HEADER_MAP:
                field = _HEADER_MAP[header]
                # Only take the first occurrence of each field
                if field not in col_map:
                    col_map[field] = idx
    return col_map


def _cell(row: tuple, col_idx: int | None) -> str:
    """Safely extract a string value from a row tuple at the given index."""
    if col_idx is None:
        return ""
    if col_idx >= len(row):
        return ""
    return safe_str(row[col_idx]).strip()
