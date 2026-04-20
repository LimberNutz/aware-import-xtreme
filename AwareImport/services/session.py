"""Save / load the application session state as a JSON file."""

import json
import os
from typing import Any

from models.cml_row import CMLRow, EntityInfoRow, FileEntry

SESSION_VERSION = 1


def save_session(
    path: str,
    *,
    entries: list[FileEntry],
    all_rows: list[CMLRow],
    entity_rows: list[EntityInfoRow],
    all_errors: list[str],
    entity_errors: list[str],
    system_path: str,
    pid_prefix: str,
    standard_style: bool,
    current_mode: str,
    deadleg: bool = False,
    traveler_path: str = "",
) -> None:
    """Serialise the current workspace to *path* as JSON."""
    data: dict[str, Any] = {
        "_version": SESSION_VERSION,
        "system_path": system_path,
        "pid_prefix": pid_prefix,
        "standard_style": standard_style,
        "current_mode": current_mode,
        "deadleg": deadleg,
        "traveler_path": traveler_path,
        "entries": [e.model_dump() for e in entries],
        "all_rows": [r.model_dump() for r in all_rows],
        "entity_rows": [r.model_dump() for r in entity_rows],
        "all_errors": all_errors,
        "entity_errors": entity_errors,
    }
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)


def load_session(path: str) -> dict[str, Any]:
    """Deserialise a session file and return a dict with typed objects.

    Returns
    -------
    dict with keys:
        entries       : list[FileEntry]
        all_rows      : list[CMLRow]
        entity_rows   : list[EntityInfoRow]
        all_errors    : list[str]
        entity_errors : list[str]
        system_path   : str
        pid_prefix    : str
        standard_style: bool
        current_mode  : str
    """
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)

    # Forward-compat: reject unknown future versions
    ver = data.get("_version", 0)
    if ver > SESSION_VERSION:
        raise ValueError(
            f"Session file version {ver} is newer than supported ({SESSION_VERSION}). "
            "Please update the application."
        )

    entries = [FileEntry.model_validate(d) for d in data.get("entries", [])]
    all_rows = [CMLRow.model_validate(d) for d in data.get("all_rows", [])]
    entity_rows = [EntityInfoRow.model_validate(d) for d in data.get("entity_rows", [])]

    return {
        "entries": entries,
        "all_rows": all_rows,
        "entity_rows": entity_rows,
        "all_errors": data.get("all_errors", []),
        "entity_errors": data.get("entity_errors", []),
        "system_path": data.get("system_path", ""),
        "pid_prefix": data.get("pid_prefix", ""),
        "standard_style": data.get("standard_style", True),
        "current_mode": data.get("current_mode", "CML Import"),
        "deadleg": data.get("deadleg", False),
        "traveler_path": data.get("traveler_path", ""),
    }
