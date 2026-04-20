# CSV header order for Aware CML Table Import
AWARE_CSV_HEADERS = [
    "SystemPath",
    "SystemName",
    "SystemType",
    "Equipment ID",
    "Equipment Description",
    "National Board Number",
    "Serial Number",
    "Model Number",
    "Manufacturer Drawing",
    "U-1 Form",
    "Name Plate",
    "Code Stamp",
    "Joint Efficiency",
    "Year Built",
    "InService",
    "InService Date",
    "Class",
    "Stress Table Used",
    "PID Drawing",
    "PID Number",
    "PFD",
    "PFD Number",
    "PSM Covered",
    "Height / Length",
    "Diameter",
    "Test Pressure",
    "Number of Shell Courses",
    "Number of Heads/Covers",
    "Number of Nozzles",
    "Internal Entry Possible",
    "",
    "",
    "CML Locations.CML",
    "CML Locations.CML Location",
    "CML Locations.Component Type",
    "CML Locations.Component",
    "CML Locations.Outside Diameter",
    "CML Locations.Nominal Thickness",
    "CML Locations.Corrosion Allowance",
    "CML Locations.T-Min",
    "CML Locations.Material Spec",
    "CML Locations.Material Grade",
    "CML Locations.CML Pressure",
    "CML Locations.CML Temperature",
    "CML Locations.CML Joint Efficiency",
    "CML Locations.CML Access",
    "CML Locations.Insulation",
    "CML Locations.CML Installed On",
    "CML Locations.CML Status",
    "CML Locations.NDE Type",
    "CML Locations.First Insp Date",
    "CML Locations.First UT Reading",
    "CML Locations.Last Insp Date",
    "CML Locations.Last UT Reading",
]

ENTITY_INFO_HEADERS = [
    "SystemPath",
    "SystemName",
    "SystemType",
    "Equipment ID",
    "Equipment Description",
    "Joint Efficiency",
    "Year Built",
    "InService",
    "InService Date",
    "Class",
    "Stress Table Used",
    "PID Drawing",
    "PID Number",
    "PFD",
    "PFD Number",
    "PSM Covered",
    "Diameter",
    "Process Service",
]

# Known sheet/tab names to look for (priority order)
KNOWN_SHEET_NAMES = [
    "Piping",
    "Vessels",
    "LWN SHEET",
]

# Expected header cells for scoring sheet detection
EXPECTED_HEADERS = [
    "CML",
    "CML Location",
    "Component Type",
    "Component",
    "OD",
    "Nom.",
    "C.A.",
    "T-Min",
    "Mat. Spec.",
    "Grade",
    "Pressure",
    "Temp.",
    "J.E.",
    "Access",
    "Insulation",
    "Install Date",
    "Status",
    "NDE",
    "UT Reading",
]

# Column mapping: Excel column letter -> field name (0-indexed)
PIPING_COLUMN_MAP = {
    0: "cml",                # A
    1: "cml_location",       # B
    2: "component_type",     # C
    3: "component",          # D
    4: "od",                 # E
    5: "nom",                # F
    6: "ca",                 # G
    7: "tmin",               # H
    8: "mat_spec",           # I
    9: "mat_grade",          # J
    10: "pressure",          # K
    11: "temp",              # L
    12: "je",                # M
    13: "access",            # N
    14: "insulation",        # O
    15: "install_date",      # P
    16: "status",            # Q
    17: "nde",               # R
    18: "inspected_by",      # S
    19: "ut_reading",        # T
    20: "inspection_notes",  # U
}

# Default values for blank cells
DEFAULTS = {
    "je": "1.0",
    "status": "Active",
    "nde": "UT",
    "ca": "0",
    "component_type": "Piping",
}

# Material defaults based on component and material type
MATERIAL_DEFAULTS = {
    "Carbon": {
        "Straight Pipe": {"mat_spec": "A106", "mat_grade": "B"},
        "_other": {"mat_spec": "A234", "mat_grade": "WPB"},
    },
    "Stainless": {
        "Straight Pipe": {"mat_spec": "A312", "mat_grade": "TP304L"},
        "_other": {"mat_spec": "A403", "mat_grade": "WP304L"},
    },
}

# Header row info in UT sheets
HEADER_ROW = 5       # 1-indexed row where column headers live
DATA_START_ROW = 6   # 1-indexed row where data begins
MAX_BLANK_CML_RUN = 10  # stop after this many consecutive blank CML cells

# Supported file extensions
SUPPORTED_EXTENSIONS = {".xlsx", ".xlsm"}

