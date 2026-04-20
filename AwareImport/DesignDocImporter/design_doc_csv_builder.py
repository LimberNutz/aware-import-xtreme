#!/usr/bin/env python3
"""
Design Document CSV Builder for Aware IDMS Import
=================================================
Recursively searches a directory for CAD (.dwg) and PDF (.pdf) files
matching a list of entity names, then generates a CSV formatted for
Aware IDMS Design Documents import.

Supports two modes:
1. Config file mode:
   python design_doc_csv_builder.py job_config.txt

2. Interactive mode:
   python design_doc_csv_builder.py

Config file format example:

ROOT_DIR=C:\Projects\Golden Grain\Drawings
SYSTEM_PATH_BASE=XCEL > Kinetik > Kings Landing > Unit > Piping >
MAX_DEPTH=10
OUTPUT_DIR=C:\Projects\Golden Grain\Exports
OUTPUT_FILENAME=Equip_DesignDocs_GoldenGrain.csv

[ENTITIES]
ET-15110
ET-15111
CRYO-003
CRYO-003-INJ
"""

import os
import sys
import csv
from datetime import datetime
from pathlib import Path
from collections import defaultdict


VALID_EXTENSIONS = {'.pdf', '.dwg'}
DEFAULT_MAX_DEPTH = 10
DOC_TYPE = "Inspection Drawing"
DOC_TYPE_PDF = "Inspection Drawing PDF"


def parse_config_file(config_path: str) -> dict:
    """
    Parse a plain text config file.

    Supported keys:
        ROOT_DIR=
        SYSTEM_PATH_BASE=
        MAX_DEPTH=
        OUTPUT_DIR=
        OUTPUT_FILENAME=

    Entities must be listed under:
        [ENTITIES]
    """
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
        "ENTITIES": [],
    }

    in_entities = False
    seen = set()

    with open(path, "r", encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.strip()

            # Skip blanks and comments
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

    if not config["ROOT_DIR"]:
        print("[ERROR] ROOT_DIR is required in the config file.")
        sys.exit(1)

    if not config["SYSTEM_PATH_BASE"]:
        print("[ERROR] SYSTEM_PATH_BASE is required in the config file.")
        sys.exit(1)

    if not config["ENTITIES"]:
        print("[ERROR] No entities found in config file under [ENTITIES].")
        sys.exit(1)

    return config


def find_files_for_entities(root_dir: str, entities: list[str], max_depth: int = DEFAULT_MAX_DEPTH) -> dict[str, list[str]]:
    """
    Recursively search root_dir for .pdf/.dwg files whose names start with
    an entity name. Stops descending into subdirectories for a given entity
    once matches are found at a shallower level.

    Returns:
        dict mapping entity_name -> list of matched filenames (basename only)
    """
    root = Path(root_dir).resolve()
    if not root.is_dir():
        print(f"[ERROR] Directory not found: {root}")
        sys.exit(1)

    entities_sorted = sorted(entities, key=len, reverse=True)

    entity_files: dict[str, list[tuple[int, str]]] = defaultdict(list)
    entity_found_depth: dict[str, int] = {}

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

            fname_upper = fname.upper()

            for entity in entities_sorted:
                entity_upper = entity.upper()

                if not fname_upper.startswith(entity_upper):
                    continue

                rest = fname[len(entity):]
                if rest and rest[0].isalnum():
                    continue

                if entity in entity_found_depth and depth > entity_found_depth[entity]:
                    break

                entity_found_depth[entity] = depth
                entity_files[entity].append((depth, fname))
                break

    result: dict[str, list[str]] = {}
    for entity in entities:
        if entity not in entity_files:
            result[entity] = []
            continue

        min_depth = entity_found_depth[entity]
        result[entity] = sorted(
            set(fname for d, fname in entity_files[entity] if d == min_depth)
        )

    return result


def build_csv_rows(entity_files: dict[str, list[str]], system_path_base: str) -> list[dict]:
    """Build CSV row dicts in Aware IDMS import format."""
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

            # Preserving original logic from uploaded script
            doc_type = DOC_TYPE_PDF if stem.upper().endswith("MODEL") else DOC_TYPE

            rows.append({
                "SystemPath": sys_path,
                "Design Documents.Document": fname,
                "Design Documents.Document Type": doc_type,
                "Design Documents.Document Description": stem,
            })

    return rows


def load_entities_from_file(filepath: str) -> list[str]:
    """Load entity names from a text file, one per line."""
    p = Path(filepath)
    if not p.is_file():
        print(f"[ERROR] Entity list file not found: {filepath}")
        sys.exit(1)

    entities = []
    seen = set()

    with open(p, "r", encoding="utf-8") as f:
        for line in f:
            name = line.strip()
            if name and name.upper() not in seen:
                entities.append(name)
                seen.add(name.upper())

    return entities


def prompt_entities_manual() -> list[str]:
    """Prompt user to paste entity names, one per line, blank line to finish."""
    print("\nPaste entity names (one per line). Press Enter on a blank line when done:")

    entities = []
    seen = set()

    while True:
        line = input().strip()
        if not line:
            break
        if line.upper() not in seen:
            entities.append(line)
            seen.add(line.upper())

    return entities


def get_output_path(output_dir: str = "", output_filename: str = "") -> Path:
    """Build the output CSV path."""
    if output_filename:
        filename = output_filename
    else:
        timestamp = datetime.now().strftime("%Y-%m-%d")
        filename = f"Equip_DesignDocs_{timestamp}.csv"

    if output_dir:
        out_dir = Path(output_dir).resolve()
        out_dir.mkdir(parents=True, exist_ok=True)
        return out_dir / filename

    return Path.cwd() / filename


def write_csv(rows: list[dict], out_path: Path) -> None:
    """Write rows to CSV."""
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


def run_job(root_dir: str, system_path_base: str, entities: list[str], max_depth: int, output_dir: str = "", output_filename: str = "") -> None:
    """Execute the search/build/write job."""
    print(f"\n[INFO] {len(entities)} unique entities loaded.")
    print(f"[INFO] Searching: {root_dir}")
    print(f"[INFO] Max depth: {max_depth}")

    entity_files = find_files_for_entities(root_dir, entities, max_depth=max_depth)

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

    out_path = get_output_path(output_dir=output_dir, output_filename=output_filename)
    write_csv(rows, out_path)

    print(f"\n[DONE] CSV written: {out_path}")
    print(f"       {len(rows)} rows across {len(found)} entities.")


def interactive_mode() -> None:
    """Run the original interactive prompt flow."""
    print("=" * 65)
    print("  Design Document CSV Builder — Aware IDMS Import")
    print("=" * 65)

    root_dir = input("\nRoot search directory (where CAD/PDF files are stored):\n> ").strip()
    if not root_dir:
        print("[ERROR] No directory provided.")
        sys.exit(1)

    print("\nSystemPath base (e.g., 'XCEL > Kinetik > Kings Landing > Unit > Piping >'):")
    system_path_base = input("> ").strip()
    if not system_path_base:
        print("[ERROR] No SystemPath provided.")
        sys.exit(1)

    print("\nEntity list source:")
    print("  [1] Load from text file (.txt, one entity per line)")
    print("  [2] Paste manually")
    choice = input("> ").strip()

    if choice == "1":
        entity_file = input("Path to entity list file:\n> ").strip()
        entities = load_entities_from_file(entity_file)
    elif choice == "2":
        entities = prompt_entities_manual()
    else:
        print("[ERROR] Invalid choice.")
        sys.exit(1)

    if not entities:
        print("[ERROR] No entities provided.")
        sys.exit(1)

    run_job(
        root_dir=root_dir,
        system_path_base=system_path_base,
        entities=entities,
        max_depth=DEFAULT_MAX_DEPTH,
    )


def config_file_mode(config_path: str) -> None:
    """Run using a single text config file."""
    print("=" * 65)
    print("  Design Document CSV Builder — Config File Mode")
    print("=" * 65)
    print(f"[INFO] Reading config: {config_path}")

    config = parse_config_file(config_path)

    run_job(
        root_dir=config["ROOT_DIR"],
        system_path_base=config["SYSTEM_PATH_BASE"],
        entities=config["ENTITIES"],
        max_depth=config["MAX_DEPTH"],
        output_dir=config["OUTPUT_DIR"],
        output_filename=config["OUTPUT_FILENAME"],
    )


def main():
    if len(sys.argv) > 1:
        config_path = sys.argv[1]
        config_file_mode(config_path)
    else:
        interactive_mode()


if __name__ == "__main__":
    main()