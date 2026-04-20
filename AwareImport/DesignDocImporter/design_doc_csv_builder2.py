#!/usr/bin/env python3

import os
import re
import sys
import csv
from datetime import datetime
from pathlib import Path
from collections import defaultdict

VALID_EXTENSIONS = {".pdf", ".dwg"}
DEFAULT_MAX_DEPTH = 10
DOC_TYPE = "Inspection Drawing"
DOC_TYPE_PDF = "Inspection Drawing PDF"

# Examples matched:
# GG-DIS-01 CAD SHT 1.dwg
# GG-DIS-04 CAD.dwg
# GG-DIS-10 CAD SHT 1_recover.dwg
ENTITY_PATTERN = re.compile(r"^([A-Z0-9]+(?:-[A-Z0-9]+)+)", re.IGNORECASE)


def parse_bool(value: str, default: bool = False) -> bool:
    if value is None:
        return default

    value = value.strip().lower()

    if value in {"1", "true", "yes", "y", "on"}:
        return True
    if value in {"0", "false", "no", "n", "off"}:
        return False

    return default


def parse_config_file(config_path: str) -> dict:
    path = Path(config_path)

    if not path.is_file():
        print(f"[ERROR] Config file not found: {config_path}")
        sys.exit(1)

    config = {
        "ROOT_DIR": "",
        "SYSTEM_PATH_BASE": "",
        "MAX_DEPTH": DEFAULT_MAX_DEPTH,
        "OUTPUT_DIR": "",
        "OUTPUT_FILENAME": "",
        "PROJECT_NAME": "",
        "ENTITIES": [],
        "AUTO_DISCOVER_ENTITIES": True,
        "IGNORE_RECOVER_FILES": True,
        "PREFER_DWG_FOR_ENTITY_DISCOVERY": True,
    }

    in_entities = False
    seen = set()

    with open(path, "r", encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.strip()

            if not line or line.startswith("#") or line.startswith("//"):
                continue

            if line.upper() == "[ENTITIES]":
                in_entities = True
                continue

            if in_entities:
                entity = line.strip()
                if entity and entity.upper() not in seen:
                    config["ENTITIES"].append(entity)
                    seen.add(entity.upper())
                continue

            if "=" in line:
                key, value = line.split("=", 1)
                key = key.strip().upper()
                value = value.strip()

                if key == "ROOT_DIR":
                    config["ROOT_DIR"] = value
                elif key == "SYSTEM_PATH_BASE":
                    config["SYSTEM_PATH_BASE"] = value
                elif key == "MAX_DEPTH":
                    try:
                        config["MAX_DEPTH"] = int(value)
                    except ValueError:
                        print(f"[ERROR] Invalid MAX_DEPTH value: {value}")
                        sys.exit(1)
                elif key == "OUTPUT_DIR":
                    config["OUTPUT_DIR"] = value
                elif key == "OUTPUT_FILENAME":
                    config["OUTPUT_FILENAME"] = value
                elif key == "PROJECT_NAME":
                    config["PROJECT_NAME"] = value
                elif key == "AUTO_DISCOVER_ENTITIES":
                    config["AUTO_DISCOVER_ENTITIES"] = parse_bool(value, True)
                elif key == "IGNORE_RECOVER_FILES":
                    config["IGNORE_RECOVER_FILES"] = parse_bool(value, True)
                elif key == "PREFER_DWG_FOR_ENTITY_DISCOVERY":
                    config["PREFER_DWG_FOR_ENTITY_DISCOVERY"] = parse_bool(value, True)

    if not config["ROOT_DIR"]:
        print("[ERROR] ROOT_DIR is required in the config file.")
        sys.exit(1)

    if not config["SYSTEM_PATH_BASE"]:
        print("[ERROR] SYSTEM_PATH_BASE is required in the config file.")
        sys.exit(1)

    return config


def extract_entity_from_filename(filename: str) -> str | None:
    stem = Path(filename).stem
    stem = re.sub(r"_recover$", "", stem, flags=re.IGNORECASE)

    match = ENTITY_PATTERN.match(stem)
    if not match:
        return None

    return match.group(1).upper()


def discover_entities(
    root_dir: str,
    max_depth: int = DEFAULT_MAX_DEPTH,
    ignore_recover_files: bool = True,
    prefer_dwg: bool = True,
) -> list[str]:
    root = Path(root_dir).resolve()

    if not root.is_dir():
        print(f"[ERROR] Directory not found: {root}")
        sys.exit(1)

    discovered = set()
    discovered_from_dwg = set()

    for dirpath, dirnames, filenames in os.walk(root):
        rel = Path(dirpath).relative_to(root)
        depth = len(rel.parts) if str(rel) != "." else 0

        if depth > max_depth:
            dirnames.clear()
            continue

        for fname in filenames:
            ext = Path(fname).suffix.lower()
            if ext not in VALID_EXTENSIONS:
                continue

            if ignore_recover_files and "_recover" in Path(fname).stem.lower():
                continue

            entity = extract_entity_from_filename(fname)
            if not entity:
                continue

            discovered.add(entity)

            if ext == ".dwg":
                discovered_from_dwg.add(entity)

    if prefer_dwg and discovered_from_dwg:
        return sorted(discovered_from_dwg)

    return sorted(discovered)


def find_files_for_entities(
    root_dir: str,
    entities: list[str],
    max_depth: int = DEFAULT_MAX_DEPTH,
    ignore_recover_files: bool = True,
) -> dict[str, list[str]]:
    root = Path(root_dir).resolve()

    if not root.is_dir():
        print(f"[ERROR] Directory not found: {root}")
        sys.exit(1)

    entities_sorted = sorted(entities, key=len, reverse=True)
    entity_files: dict[str, set[str]] = defaultdict(set)

    for dirpath, dirnames, filenames in os.walk(root):
        rel = Path(dirpath).relative_to(root)
        depth = len(rel.parts) if str(rel) != "." else 0

        if depth > max_depth:
            dirnames.clear()
            continue

        for fname in filenames:
            ext = Path(fname).suffix.lower()
            if ext not in VALID_EXTENSIONS:
                continue

            if ignore_recover_files and "_recover" in Path(fname).stem.lower():
                continue

            fname_upper = fname.upper()

            for entity in entities_sorted:
                entity_upper = entity.upper()

                if not fname_upper.startswith(entity_upper):
                    continue

                rest = fname[len(entity):]
                if rest and rest[0].isalnum():
                    continue

                entity_files[entity].add(fname)
                break

    result: dict[str, list[str]] = {}
    for entity in entities:
        result[entity] = sorted(entity_files.get(entity, set()), key=sort_key_for_docs)

    return result


def sort_key_for_docs(filename: str):
    path = Path(filename)
    stem_upper = path.stem.upper()
    ext = path.suffix.lower()

    # Put PDFs before DWGs when they are companion files
    is_model_pdf = ext == ".pdf" and stem_upper.endswith("-MODEL")
    is_pdf = ext == ".pdf"

    return (
        0 if is_model_pdf else 1 if is_pdf else 2,
        path.stem.upper(),
        path.name.upper(),
    )


def get_document_type(filename: str) -> str:
    path = Path(filename)
    stem_upper = path.stem.upper()
    ext = path.suffix.lower()

    if ext == ".pdf" and stem_upper.endswith("-MODEL"):
        return DOC_TYPE_PDF

    return DOC_TYPE


def build_csv_rows(entity_files: dict[str, list[str]], system_path_base: str) -> list[dict]:
    rows = []

    base = system_path_base.rstrip()
    if not base.endswith(">"):
        base = base.rstrip() + " >"
    base += " "

    for entity in sorted(entity_files.keys()):
        files = entity_files[entity]

        if not files:
            continue

        sys_path = f"{base}{entity}"

        for fname in files:
            stem = Path(fname).stem
            doc_type = get_document_type(fname)

            rows.append(
                {
                    "SystemPath": sys_path,
                    "Design Documents.Document": fname,
                    "Design Documents.Document Type": doc_type,
                    "Design Documents.Document Description": stem,
                }
            )

    return rows


def sanitize_project_name(project_name: str) -> str:
    project_name = project_name.strip()
    if not project_name:
        return "Project"

    project_name = re.sub(r'[<>:"/\\|?*]', "", project_name)
    project_name = re.sub(r"\s+", "", project_name)

    return project_name or "Project"


def get_output_path(output_dir: str = "", output_filename: str = "", project_name: str = "") -> Path:
    short_date = datetime.now().strftime("%Y%m%d")

    if output_filename:
        filename = output_filename
    else:
        safe_project_name = sanitize_project_name(project_name)
        filename = f"Equip_CADimport_{safe_project_name}_{short_date}.csv"

    if output_dir:
        out_dir = Path(output_dir).resolve()
        out_dir.mkdir(parents=True, exist_ok=True)
        return out_dir / filename

    return Path.cwd() / filename


def write_csv(rows: list[dict], out_path: Path) -> None:
    fieldnames = [
        "SystemPath",
        "Design Documents.Document",
        "Design Documents.Document Type",
        "Design Documents.Document Description",
    ]

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def run_job(
    root_dir: str,
    system_path_base: str,
    entities: list[str],
    max_depth: int,
    output_dir: str = "",
    output_filename: str = "",
    project_name: str = "",
    ignore_recover_files: bool = True,
) -> None:
    print(f"\n[INFO] {len(entities)} unique entities loaded.")
    print(f"[INFO] Searching: {root_dir}")
    print(f"[INFO] Max depth: {max_depth}")

    entity_files = find_files_for_entities(
        root_dir=root_dir,
        entities=entities,
        max_depth=max_depth,
        ignore_recover_files=ignore_recover_files,
    )

    found = {e: f for e, f in entity_files.items() if f}
    missing = [e for e, f in entity_files.items() if not f]

    print(f"[INFO] Entities with files found: {len(found)} / {len(entities)}")

    if missing:
        print(f"[WARN] {len(missing)} entities with NO matching files:")
        for m in missing:
            print(f"       - {m}")

    total_files = sum(len(f) for f in entity_files.values())
    print(f"[INFO] Total file matches: {total_files}")

    if total_files == 0:
        print("[ERROR] No files found. Check your search directory and entity names.")
        sys.exit(1)

    rows = build_csv_rows(entity_files, system_path_base)

    out_path = get_output_path(
        output_dir=output_dir,
        output_filename=output_filename,
        project_name=project_name,
    )

    write_csv(rows, out_path)

    print(f"\n[DONE] CSV written: {out_path}")
    print(f"       {len(rows)} rows across {len(found)} entities.")


def interactive_mode() -> None:
    print("=" * 65)
    print("  Design Document CSV Builder — Auto Entity Mode")
    print("=" * 65)

    root_dir = input("\nRoot search directory:\n> ").strip()
    if not root_dir:
        print("[ERROR] No directory provided.")
        sys.exit(1)

    system_path_base = input("\nSystemPath base:\n> ").strip()
    if not system_path_base:
        print("[ERROR] No SystemPath provided.")
        sys.exit(1)

    project_name = input("\nProject name for output filename:\n> ").strip()

    entities = discover_entities(
        root_dir=root_dir,
        max_depth=DEFAULT_MAX_DEPTH,
        ignore_recover_files=True,
        prefer_dwg=True,
    )

    if not entities:
        print("[ERROR] No entities auto-discovered.")
        sys.exit(1)

    print(f"\n[INFO] Auto-discovered {len(entities)} entities:")
    for entity in entities:
        print(f"       - {entity}")

    run_job(
        root_dir=root_dir,
        system_path_base=system_path_base,
        entities=entities,
        max_depth=DEFAULT_MAX_DEPTH,
        output_dir="",
        output_filename="",
        project_name=project_name,
        ignore_recover_files=True,
    )


def config_file_mode(config_path: str) -> None:
    print("=" * 65)
    print("  Design Document CSV Builder — Config File Mode")
    print("=" * 65)
    print(f"[INFO] Reading config: {config_path}")

    config = parse_config_file(config_path)

    entities = config["ENTITIES"]

    if config["AUTO_DISCOVER_ENTITIES"] and not entities:
        entities = discover_entities(
            root_dir=config["ROOT_DIR"],
            max_depth=config["MAX_DEPTH"],
            ignore_recover_files=config["IGNORE_RECOVER_FILES"],
            prefer_dwg=config["PREFER_DWG_FOR_ENTITY_DISCOVERY"],
        )
        print(f"[INFO] Auto-discovered {len(entities)} entities from filenames.")

    if not entities:
        print("[ERROR] No entities supplied or discovered.")
        sys.exit(1)

    run_job(
        root_dir=config["ROOT_DIR"],
        system_path_base=config["SYSTEM_PATH_BASE"],
        entities=entities,
        max_depth=config["MAX_DEPTH"],
        output_dir=config["OUTPUT_DIR"],
        output_filename=config["OUTPUT_FILENAME"],
        project_name=config["PROJECT_NAME"],
        ignore_recover_files=config["IGNORE_RECOVER_FILES"],
    )


def main():
    if len(sys.argv) > 1:
        config_file_mode(sys.argv[1])
    else:
        interactive_mode()


if __name__ == "__main__":
    main()