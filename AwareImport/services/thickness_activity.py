"""Thickness Activity dataset builder.

Derived directly from the canonical CMLRow parsed models.
No second parsing pass is performed.
Material defaults are applied by the transformer layer before rows reach this module.
"""

from models.cml_row import CMLRow

# Thickness Activity output columns (A:S)
TA_COLUMNS = [
    "CML",                  # A
    "CML Location",         # B
    "Component Type",       # C
    "Component",            # D
    "OD",                   # E
    "Nom.",                 # F
    "C.A.",                 # G
    "T-Min",                # H
    "Mat. Spec.",           # I
    "Mat. Grade",           # J
    "Pressure",             # K
    "Temp.",                # L
    "First Insp Date",      # M  (blank placeholder)
    "First UT Reading",     # N  (blank placeholder)
    "Last Insp Date",       # O  (blank placeholder)
    "Last UT Reading",      # P  (blank placeholder)
    "UT Reading",           # Q
    "Inspection Notes",     # R
    "Inspected By",         # S
]


def build_thickness_activity_view(rows: list[CMLRow]) -> tuple[list[dict], list[str]]:
    """Build Thickness Activity view from already-parsed CMLRows.

    Args:
        rows: List of CMLRow objects belonging to a single file.

    Returns:
        (rows, errors) where each row is a dict keyed by TA_COLUMNS field names,
        and errors is a list of warning/error strings.
    """
    ta_rows: list[dict] = []
    errors: list[str] = []

    if not rows:
        return ta_rows, errors

    # Rule 1.2: The dataset ends at the last row where Column B is non-blank.
    # We must find the cut-off index in the provided rows list.
    last_b_index = -1
    for i, row in enumerate(rows):
        if row.cml_location:
            last_b_index = i

    if last_b_index == -1:
        # No rows with location found
        return ta_rows, errors

    # Truncate list to the last valid location row
    # This excludes trailing rows that might have only UT readings (Rule 1.2)
    subset = rows[:last_b_index + 1]

    for row in subset:
        # Rule 1.4: If Column T (UT Reading) is present but Column B is blank -> DATA ERROR
        if row.ut_reading and not row.cml_location:
            # Rule 1.7: Surface as error, do not include in dataset
            errors.append(
                f"Row {row.source_row}: UT Reading present but CML Location (Col B) is blank — DATA ERROR"
            )
            continue

        # Rule 1.1: Include row IFF Column B (CML Location) is non-blank
        if not row.cml_location:
            continue

        # Map CMLRow fields to TA Columns
        # Material defaults already applied by transformer layer
        ta_row = {
            "_source_file": row.source_file,
            "_source_sheet": row.source_sheet,
            "_source_row": row.source_row,
            "CML": row.cml,                              # A
            "CML Location": row.cml_location,            # B
            "Component Type": row.component_type,        # C
            "Component": row.component,                  # D
            "OD": row.od,                                # E
            "Nom.": row.nom,                             # F
            "C.A.": row.ca,                              # G
            "T-Min": row.tmin,                           # H
            "Mat. Spec.": row.mat_spec,                  # I
            "Mat. Grade": row.mat_grade,                 # J
            "Pressure": row.pressure,                    # K
            "Temp.": row.temp,                           # L
            "First Insp Date": "",                       # M (blank)
            "First UT Reading": "",                      # N (blank)
            "Last Insp Date": "",                        # O (blank)
            "Last UT Reading": "",                       # P (blank)
            "UT Reading": row.ut_reading,                # Q
            "Inspection Notes": row.inspection_notes,    # R
            "Inspected By": row.inspected_by,            # S
        }
        ta_rows.append(ta_row)

    return ta_rows, errors
