import re
from datetime import datetime
from models.cml_row import CMLRow
from app.constants import DEFAULTS, MATERIAL_DEFAULTS
from utils.helpers import (
    format_cml_standard,
    format_cml_client,
    cml_suffix_value,
    is_numeric,
)


def transform_rows(rows: list[CMLRow], system_path: str, standard_style: bool) -> list[CMLRow]:
    # For mixed circuits: resolve which material is which before row-by-row processing
    _resolve_mixed_circuit_material(rows)

    # apply defaults, cleanup, and formatting to all rows
    transformed = []
    for row in rows:
        row = _apply_system_path(row, system_path)
        row = _format_cml(row, standard_style)
        row = _apply_material_defaults(row)
        row = _apply_defaults(row)
        row = _validate_row(row, standard_style)
        transformed.append(row)
    return transformed


def _apply_system_path(row: CMLRow, parent_path: str) -> CMLRow:
    # SystemPath = "{parent_path} > {SystemName}"
    if parent_path and row.system_name:
        row.system_path = f"{parent_path} > {row.system_name}"
    elif parent_path:
        row.system_path = parent_path
    return row


def _format_cml(row: CMLRow, standard_style: bool) -> CMLRow:
    if not row.cml:
        return row
    if standard_style:
        row.cml = format_cml_standard(row.cml)
    else:
        row.cml = format_cml_client(row.cml)
    return row


def _apply_material_defaults(row: CMLRow) -> CMLRow:
    # By the time this runs, material_type has already been resolved to
    # "Carbon" or "Stainless" (the Mixed pre-pass handles mixed circuits).
    # Only fill blank fields.
    if row.mat_spec and row.mat_grade:
        return row

    mat_table = MATERIAL_DEFAULTS.get(row.material_type, MATERIAL_DEFAULTS["Carbon"])
    component = row.component.strip()
    if component.lower().startswith("straight pipe"):
        defaults = mat_table["Straight Pipe"]
    else:
        defaults = mat_table["_other"]

    if not row.mat_spec:
        row.mat_spec = defaults["mat_spec"]
    if not row.mat_grade:
        row.mat_grade = defaults["mat_grade"]
    return row


# ASTM spec number prefixes that indicate Stainless Steel material
_SS_SPEC_PREFIXES = (
    "A312", "A358", "A376", "A403", "A409",
    "A813", "A814", "A182", "A240", "A276",
)

# Grade substring fragments that indicate Stainless Steel.
# Checked case-insensitively; handles TP304L, 304L, TP316, WP304L, WP316L, etc.
_SS_GRADE_KEYWORDS = (
    "304", "316", "321", "347", "310", "317", "904",
)


def _infer_material_from_existing(row: CMLRow) -> str:
    """Inspect a row's mat_spec / mat_grade to determine if it is Stainless or Carbon."""
    spec = row.mat_spec.strip().upper()
    grade = row.mat_grade.strip().upper()

    for prefix in _SS_SPEC_PREFIXES:
        if spec.startswith(prefix):
            return "Stainless"

    for kw in _SS_GRADE_KEYWORDS:
        if kw in grade:
            return "Stainless"

    return "Carbon"


def _resolve_mixed_circuit_material(rows: list[CMLRow]) -> None:
    """Pre-pass for Mixed circuits: determines which material was manually
    entered and assigns the *opposite* type to all blank rows.

    Logic:
      - Collect rows where material_type == "Mixed".
      - Split into filled (has mat_spec or mat_grade) vs blank (neither).
      - Infer what the filled rows represent (Carbon or Stainless).
      - Blank rows get the opposite type. Filled rows keep the detected type
        so _apply_material_defaults can complete any partially-filled fields.
      - If both CS and SS fills are present, resolves each row individually.
      - If nothing is filled, defaults all rows to Carbon.

    Modifies rows in-place.
    """
    mixed = [r for r in rows if r.material_type == "Mixed"]
    if not mixed:
        return

    filled = [r for r in mixed if r.mat_spec.strip() or r.mat_grade.strip()]
    blank  = [r for r in mixed if not r.mat_spec.strip() and not r.mat_grade.strip()]

    if not filled:
        # Nothing manually entered — cannot infer; default all to Carbon.
        for r in blank:
            r.material_type = "Carbon"
        return

    # Count how many filled rows are SS vs CS
    ss_filled = [r for r in filled if _infer_material_from_existing(r) == "Stainless"]
    cs_filled = [r for r in filled if _infer_material_from_existing(r) == "Carbon"]

    if ss_filled and not cs_filled:
        # All manually-entered rows are Stainless → blanks are Carbon
        for r in filled:
            r.material_type = "Stainless"
        for r in blank:
            r.material_type = "Carbon"

    elif cs_filled and not ss_filled:
        # All manually-entered rows are Carbon → blanks are Stainless
        for r in filled:
            r.material_type = "Carbon"
        for r in blank:
            r.material_type = "Stainless"

    else:
        # Both CS and SS fills present (ambiguous) — resolve each row individually.
        for r in filled:
            r.material_type = _infer_material_from_existing(r)
        for r in blank:
            r.material_type = "Carbon"  # safe fallback


def _apply_defaults(row: CMLRow) -> CMLRow:
    row.je = "1.0"
    if not row.status:
        row.status = DEFAULTS["status"]
    if not row.nde:
        row.nde = DEFAULTS["nde"]
    if not row.ca:
        row.ca = DEFAULTS["ca"]
    if not row.component_type:
        row.component_type = DEFAULTS["component_type"]
    # No UT reading → mark the CML as Inactive
    if not row.ut_reading.strip():
        row.status = "Inactive"
    return row


def _validate_row(row: CMLRow, standard_style: bool) -> CMLRow:
    warnings = []

    # CML suffix > 05 warning
    if row.cml:
        suffix = cml_suffix_value(row.cml)
        if suffix > 5:
            warnings.append(f"CML suffix > 05: {row.cml}")

    # A UT reading is only meaningful if it is numeric.
    # Non-numeric values (N/A, NA, etc.) should not trigger missing-field warnings.
    has_real_reading = bool(row.ut_reading) and is_numeric(row.ut_reading)

    # missing critical fields
    if not row.cml:
        warnings.append("Missing CML number")
        row.is_valid = False
    if not row.od and has_real_reading:
        warnings.append("Missing OD")
    if not row.nom and has_real_reading:
        warnings.append("Missing Nominal thickness")

    # OD must be a plain decimal number — flag anything that looks like a date or free text
    if row.od and not is_numeric(row.od):
        warnings.append(f"Invalid OD format (expected a number, got '{row.od}')")
        row.is_valid = False

    # install date: warn if missing on a real CML, or if format is unrecognised
    if not row.install_date:
        if row.cml:
            warnings.append("Missing Install Date")
    else:
        formatted_date = _format_date(row.install_date)
        if formatted_date:
            row.install_date = formatted_date
        else:
            if not re.match(r"^\d{1,2}/\d{1,2}/\d{2,4}$", row.install_date):
                if not re.match(r"^\d{4}-\d{2}-\d{2}$", row.install_date):
                    warnings.append(f"Invalid Install Date format: '{row.install_date}'")

    # validity check: If there is a numeric reading, a location is required
    if has_real_reading and not row.cml_location:
        warnings.append("UT Reading present but CML Location is missing")
        row.is_valid = False

    row.warnings = warnings
    return row


def _format_date(date_str: str) -> str:
    # try to convert various date formats to MM/DD/YYYY
    date_str = date_str.strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%m/%d/%y", "%d/%m/%y"):
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.strftime("%m/%d/%Y")
        except ValueError:
            continue
    return ""
