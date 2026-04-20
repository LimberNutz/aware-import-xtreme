from models.cml_row import CMLRow


def aggregate_rows(rows: list[CMLRow]) -> list[CMLRow]:
    # deduplicate by (system_path, system_name, cml)
    # precedence: most recently modified file wins
    seen: dict[tuple[str, str, str], CMLRow] = {}

    for row in rows:
        key = (row.system_path.strip(), row.system_name.strip(), row.cml.strip())

        if key not in seen:
            seen[key] = row
            continue

        existing = seen[key]

        # prefer most recently modified file
        if row.file_modified > existing.file_modified:
            seen[key] = row

    return list(seen.values())
