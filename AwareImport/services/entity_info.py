import logging
import os
import re
import warnings
from collections import Counter, defaultdict

from models.cml_row import CMLRow, EntityInfoRow
from services.excel_parser import _find_best_sheet, _extract_material_type
from utils.helpers import safe_str, temp_open_workbook

# Suppress pypdf warnings about duplicate dictionary entries
warnings.filterwarnings("ignore", category=UserWarning, module="pypdf", message="Multiple definitions in dictionary")
logging.getLogger("pypdf").setLevel(logging.ERROR)


_WORKBOOK_FIELD_LABELS = {
    "system_name": ("pipe circuit name", "vessel name", "circuit name"),
    "equipment_description": ("description", "circuit description"),
    "pid_number": ("p&id page", "p&id page number", "pid number", "pid page number"),
    "inspection_date": ("date", "inspection date"),
}


def build_entity_info_rows(
    rows: list[CMLRow],
    pid_prefix: str = "",
    progress_callback=None,
    traveler_data: dict[str, dict[str, str]] | None = None,
) -> tuple[list[EntityInfoRow], list[str]]:
    grouped: dict[tuple[str, str], list[CMLRow]] = defaultdict(list)
    for row in rows:
        key = (row.system_path.strip(), row.system_name.strip() or row.equipment_id.strip())
        if not key[1]:
            continue
        grouped[key].append(row)

    entity_rows: list[EntityInfoRow] = []
    errors: list[str] = []
    sorted_keys = sorted(grouped.keys())
    total = len(sorted_keys)

    # Track which traveler entities were matched so we can warn about unmatched
    matched_traveler_keys: set[str] = set()

    for idx, key in enumerate(sorted_keys):
        if progress_callback:
            progress_callback(idx + 1, total)
        entity, entity_errors = _build_entity_row(grouped[key], pid_prefix, traveler_data)
        entity_rows.append(entity)
        errors.extend(entity_errors)
        if traveler_data:
            lookup_key = key[1].upper()  # system_name
            if lookup_key in traveler_data:
                matched_traveler_keys.add(lookup_key)

    # Warn about traveler entities that didn't match any parsed entity
    if traveler_data:
        unmatched = set(traveler_data.keys()) - matched_traveler_keys
        for name in sorted(unmatched):
            errors.append(f"[Traveler] Entity '{name}' not matched to any parsed UT sheet entity")

    return entity_rows, errors


def _build_entity_row(
    rows: list[CMLRow],
    pid_prefix: str,
    traveler_data: dict[str, dict[str, str]] | None = None,
) -> tuple[EntityInfoRow, list[str]]:
    first = rows[0]
    system_path = first.system_path.strip()
    system_name = first.system_name.strip() or first.equipment_id.strip()
    source_file = _pick_primary_source_file(rows)
    workbook_info, workbook_errors = _extract_workbook_info(source_file)
    pdf_path, pdf_text = _extract_pdf_text(source_file, system_name)
    pdf_info = _extract_pdf_info(pdf_text, system_name)
    material_type = _resolve_material_type(rows, workbook_info, pdf_text)
    diameter = _most_common_value([r.od for r in rows if r.od.strip()])

    entity = EntityInfoRow(
        source_file=source_file,
        source_pdf=pdf_path,
        system_path=system_path,
        system_name=system_name,
        system_type="",
        equipment_id=system_name,
        joint_efficiency="",
        in_service="",
        class_name="",
        pid_drawing="",
        pfd="",
        psm_covered="",
    )

    _set_field(entity, "system_type", "Process Piping", "default")
    _set_field(entity, "joint_efficiency", "1.0", "default")
    _set_field(entity, "in_service", "Yes", "default")
    _set_field(entity, "pfd", "No", "default")
    _set_field(entity, "psm_covered", "Yes", "default")
    _set_field(entity, "diameter", diameter, "derived")

    # --- Traveler data (highest priority — applied first) ---
    if traveler_data:
        trav = traveler_data.get(system_name.upper(), {})
        _set_field(entity, "equipment_description", trav.get("equipment_description", ""), "traveler")
        _set_field(entity, "pid_number", trav.get("pid_number", ""), "traveler")
        _set_field(entity, "class_name", trav.get("class_name", ""), "traveler")

    # --- UT sheet workbook data (fallback) ---
    _set_field(entity, "equipment_description", workbook_info.get("equipment_description", ""), "workbook")
    _set_field(entity, "equipment_description", pdf_info.get("equipment_description", ""), "pdf")
    _set_field(entity, "pid_number", workbook_info.get("pid_number", ""), "workbook")
    _set_field(entity, "pid_number", pdf_info.get("pid_number", ""), "pdf")
    entity.pid_number = _apply_pid_prefix(entity.pid_number, pid_prefix)
    if entity.pid_number:
        entity.field_sources["pid_number"] = entity.field_sources.get("pid_number", "manual")
    _set_field(entity, "process_service", workbook_info.get("process_service", ""), "workbook")
    _set_field(entity, "process_service", pdf_info.get("process_service", ""), "pdf")
    _set_field(entity, "class_name", workbook_info.get("class_name", ""), "workbook")
    _set_field(entity, "class_name", pdf_info.get("class_name", ""), "pdf")
    _set_field(entity, "year_built", workbook_info.get("year_built", ""), "workbook")
    _set_field(entity, "year_built", pdf_info.get("year_built", ""), "pdf")

    # Fallback: derive year_built from the most common year in CML install_date fields
    if not entity.year_built:
        cml_year = _extract_year_from_install_dates(rows)
        if cml_year:
            _set_field(entity, "year_built", cml_year, "cml_install_date")

    if not entity.class_name:
        _set_field(entity, "class_name", "Class 2", "default")

    if entity.pid_number:
        entity.pid_drawing = "Yes"
        entity.field_sources["pid_drawing"] = "derived"

    stress_table = _derive_stress_table(material_type, workbook_info, pdf_text)
    _set_field(entity, "stress_table_used", stress_table, "derived")

    # Always format in_service_date as 01/01/YYYY based on year_built
    if entity.year_built:
        year = _parse_year(entity.year_built)
        if year:
            _set_field(entity, "in_service_date", f"01/01/{year}", "derived")

    warnings = list(workbook_errors)
    if not entity.equipment_description:
        warnings.append(f"[{system_name}] Missing Equipment Description")
    if not entity.year_built:
        warnings.append(f"[{system_name}] Missing Year Built")
        entity.is_valid = False
    if not entity.stress_table_used:
        warnings.append(f"[{system_name}] Missing Stress Table Used")
    if not entity.diameter:
        warnings.append(f"[{system_name}] Missing Diameter")
    if not entity.pid_number:
        warnings.append(f"[{system_name}] PID not found; PID Drawing defaulted to No")
    if not pdf_path:
        warnings.append(f"[{system_name}] No matching PDF found for fallback extraction")

    entity.warnings = warnings
    return entity, warnings


def _pick_primary_source_file(rows: list[CMLRow]) -> str:
    counts = Counter(r.source_file for r in rows if r.source_file)
    if not counts:
        return ""
    return counts.most_common(1)[0][0]


def _extract_workbook_info(file_path: str) -> tuple[dict[str, str], list[str]]:
    info: dict[str, str] = {}
    errors: list[str] = []
    if not file_path or not os.path.exists(file_path):
        return info, errors
    try:
        with temp_open_workbook(file_path, data_only=True, read_only=True) as wb:
            sheet = _find_best_sheet(wb, errors)
            if sheet is None:
                return info, errors
            header_rows = list(sheet.iter_rows(min_row=1, max_row=4, values_only=True))
            for field_name, labels in _WORKBOOK_FIELD_LABELS.items():
                value = _find_labeled_value(header_rows, labels)
                if value:
                    info[field_name] = value
            material = _extract_material_type(sheet)
            if material:
                info["material_type"] = material
    except Exception as exc:
        errors.append(f"[{os.path.basename(file_path)}] Workbook info extraction failed: {exc}")
    return info, errors


def _find_labeled_value(rows: list[tuple], labels: tuple[str, ...]) -> str:
    for row in rows:
        cells = [safe_str(cell) for cell in row]
        lowered = [cell.lower().strip().rstrip(":") for cell in cells]
        for idx, cell in enumerate(lowered):
            if any(label in cell for label in labels):
                # Only scan the next 4 cells — label/value pairs are always
                # adjacent in these header rows.  Scanning the full row causes
                # false matches when the target cell is blank and a *different*
                # label (e.g. "Technician:") sits further along the same row.
                for next_idx in range(idx + 1, min(idx + 5, len(cells))):
                    value = cells[next_idx].strip()
                    if not value:
                        continue
                    # Skip cells that are themselves labels (end with ":").
                    if value.endswith(":"):
                        break
                    return value
    return ""


def _extract_pdf_text(source_file: str, system_name: str) -> tuple[str, str]:
    """Return (path, text) of the best matching PDF.

    Prefers CAD PDFs (contain 'cad' or 'model' in filename) over API
    sketch PDFs because CAD title blocks have clean, unambiguous fields
    (e.g. DESIGN CODE) while API sketches have boilerplate prompts like
    'B31.3 or B31.4 or B31.8 (circle)' that confuse text extraction.
    """
    if not source_file:
        return "", ""
    folder = os.path.dirname(source_file)
    if not os.path.isdir(folder):
        return "", ""
    candidates = []
    system_token = _normalize_token(system_name)
    for name in os.listdir(folder):
        if not name.lower().endswith(".pdf"):
            continue
        score = 0
        norm = _normalize_token(name)
        name_lower = name.lower()
        if system_token and system_token in norm:
            score += 10
        # Strongly prefer CAD-produced PDFs over API sketches
        if "cad" in name_lower or "model" in name_lower:
            score += 20
        if "iso" in name_lower:
            score += 2
        candidates.append((score, os.path.join(folder, name)))
    if not candidates:
        return "", ""
    candidates.sort(key=lambda item: (-item[0], item[1]))
    for _score, path in candidates:
        text = _read_pdf_text(path)
        if text:
            return path, text
    return "", ""


def _read_pdf_text(path: str) -> str:
    try:
        from pypdf import PdfReader
    except Exception:
        return ""
    try:
        reader = PdfReader(path)
        text = "\n".join((page.extract_text() or "") for page in reader.pages)
        return " ".join(text.split())
    except Exception:
        return ""


def _extract_pdf_info(text: str, system_name: str) -> dict[str, str]:
    if not text:
        return {}
    info: dict[str, str] = {}
    upper_text = text.upper()

    year_match = re.search(r"YEAR BUILT\s+(\d{4})", upper_text)
    if year_match:
        info["year_built"] = year_match.group(1)

    pid_match = re.search(r"K[0-9A-Z\-\/]+PID[0-9A-Z\-\/]*", upper_text)
    if pid_match:
        info["pid_number"] = pid_match.group(0)

    desc_match = re.search(r"(F\-[0-9A-Z\-\/ ]+TO[ A-Z0-9\-/]+)", upper_text)
    if desc_match:
        info["equipment_description"] = desc_match.group(1).strip()

    packed_match = re.search(
        re.escape(system_name.upper().strip()) + r"\s+([A-Z /\-]+?)(\d)([YN])(\d{4})",
        upper_text,
    )
    if packed_match:
        process_service = packed_match.group(1).strip(" -/")
        if process_service:
            info["process_service"] = process_service.title()
        info["class_name"] = f"Class {packed_match.group(2)}"
        info["year_built"] = packed_match.group(4)

    system_token = system_name.upper().strip()
    pos = upper_text.find(system_token)
    if pos != -1 and "process_service" not in info:
        after = upper_text[pos + len(system_token):].strip()
        tokens = after.split()
        process_tokens: list[str] = []
        idx = 0
        while idx < len(tokens):
            token = tokens[idx]
            if token in {"1", "2", "3", "4"}:
                break
            if token == "INJECTION":
                break
            if re.fullmatch(r"\d{4}", token):
                break
            if re.search(r"\d", token):
                break
            if token in {"Y", "N"}:
                break
            process_tokens.append(token)
            idx += 1
        if process_tokens:
            info["process_service"] = " ".join(process_tokens).title()
        if idx < len(tokens):
            token = tokens[idx]
            if token == "INJECTION":
                info["class_name"] = "Injection Point"
            elif token in {"1", "2", "3", "4"}:
                info["class_name"] = f"Class {token}"

    class_match = re.search(r"\bCLASS\s+(\d)\b", upper_text)
    if class_match:
        info["class_name"] = f"Class {class_match.group(1)}"

    return info


def _resolve_material_type(rows: list[CMLRow], workbook_info: dict[str, str], pdf_text: str) -> str:
    material = workbook_info.get("material_type", "")
    if material:
        return material
    for row in rows:
        if row.material_type:
            return row.material_type
    upper_text = pdf_text.upper()
    if "STAINLESS" in upper_text or "SS" in upper_text:
        return "Stainless"
    return "Carbon"


def _derive_stress_table(material_type: str, workbook_info: dict[str, str], pdf_text: str) -> str:
    upper_text = pdf_text.upper()

    # 1. Best source: CAD title block "DESIGN CODE" field (unambiguous)
    design_code_match = re.search(r"DESIGN\s+CODE\s+(B31[\. ]?\d)", upper_text)
    if design_code_match:
        code = design_code_match.group(1).replace(" ", ".").upper()
        # Normalise e.g. "B318" -> "B31.8"
        if "." not in code:
            code = code[:3] + "." + code[3:]
        if code == "B31.8":
            return "B31.8"
        if code in ("B31.3", "B31.4"):
            if material_type.lower().startswith("stainless"):
                return "2014 B31.3 (Stainless Steel)"
            return "2014 B31.3 (Carbon Steel)"

    # 2. Fallback: substring search, but skip if this is an API sketch form.
    #    API sketch PDFs contain a boilerplate selection prompt like
    #    "B31.3 or B31.4 or B31.8 (circle)" — pypdf garbles the spacing,
    #    making regex stripping unreliable.  The word "(circle)" never
    #    appears in CAD title blocks, so it's a reliable sentinel.
    is_sketch_form = "(CIRCLE)" in upper_text
    if not is_sketch_form:
        if "B31.8" in upper_text:
            return "B31.8"
        if "B31.3" in upper_text:
            if material_type.lower().startswith("stainless"):
                return "2014 B31.3 (Stainless Steel)"
            return "2014 B31.3 (Carbon Steel)"

    # 3. Material-type fallback (workbook had a material_type so B31.3 applies)
    if workbook_info.get("material_type"):
        if material_type.lower().startswith("stainless"):
            return "2014 B31.3 (Stainless Steel)"
        return "2014 B31.3 (Carbon Steel)"
    return ""


def _set_field(entity: EntityInfoRow, field_name: str, value: str, source: str) -> None:
    value = safe_str(value)
    if not value:
        return
    current = safe_str(getattr(entity, field_name, ""))
    if current and current != value:
        return
    setattr(entity, field_name, value)
    entity.field_sources[field_name] = source


def _most_common_value(values: list[str]) -> str:
    cleaned = [safe_str(v) for v in values if safe_str(v)]
    if not cleaned:
        return ""
    counts = Counter(cleaned)
    return counts.most_common(1)[0][0]


def _normalize_token(value: str) -> str:
    return re.sub(r"[^A-Z0-9]", "", value.upper())


def _apply_pid_prefix(pid_number: str, pid_prefix: str) -> str:
    pid_number = safe_str(pid_number)
    pid_prefix = safe_str(pid_prefix)
    if not pid_number or not pid_prefix:
        return pid_number
    if pid_number.upper().startswith(pid_prefix.upper()):
        return pid_number
    if "PID" in pid_number.upper():
        suffix_match = re.search(r"(\d[0-9A-Z\-\/]*)$", pid_number)
        if suffix_match:
            return f"{pid_prefix}{suffix_match.group(1)}"
    return f"{pid_prefix}{pid_number}"


def _parse_year(value: str) -> str:
    """Extract a 4-digit year string from a date or bare-year string.

    Handles formats like '2004', '01/01/2004', '12/13/2004', '2004-01-01', etc.
    Returns the 4-digit year as a string, or '' if none found.
    """
    if not value:
        return ""
    # Bare 4-digit year
    if re.fullmatch(r"\d{4}", value.strip()):
        return value.strip()
    # MM/DD/YYYY or M/D/YYYY
    m = re.match(r"\d{1,2}/\d{1,2}/(\d{4})$", value.strip())
    if m:
        return m.group(1)
    # YYYY-MM-DD
    m = re.match(r"(\d{4})-\d{2}-\d{2}", value.strip())
    if m:
        return m.group(1)
    # Last-resort: grab any 4-digit sequence
    m = re.search(r"\b(\d{4})\b", value)
    if m:
        return m.group(1)
    return ""


def _extract_year_from_install_dates(rows: list[CMLRow]) -> str:
    """Return the most common 4-digit year found across install_date fields.

    Skips missing / non-parseable dates.  Returns '' when nothing is found.
    """
    years: list[str] = []
    for r in rows:
        y = _parse_year(r.install_date.strip())
        if y:
            years.append(y)
    if not years:
        return ""
    return Counter(years).most_common(1)[0][0]
