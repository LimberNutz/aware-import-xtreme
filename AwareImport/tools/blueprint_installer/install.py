#!/usr/bin/env python3
"""Blueprint Installer — Add the Project Blueprint system to any repository.

Usage:
    python install.py                    # install into current directory
    python install.py /path/to/repo      # install into specified directory

What it does:
    1. Creates docs/ structure (00_BLUEPRINT.md template, INTERFACE_MAP.md, etc.)
    2. Copies the snapshot generator to tools/blueprint/snapshot.py
    3. If package.json exists, adds a "snapshot" script
    4. Prints instructions for first run

No internet access or external packages required.
"""

import os
import shutil
import sys
import json


def main():
    # Determine target directory
    if len(sys.argv) > 1:
        target = os.path.abspath(sys.argv[1])
    else:
        target = os.getcwd()

    if not os.path.isdir(target):
        print(f"Error: {target} is not a directory")
        sys.exit(1)

    print(f"Installing Project Blueprint into: {target}")
    print()

    # Create directory structure
    dirs = [
        "docs",
        "docs/adr",
        "docs/snapshots",
        "tools/blueprint",
    ]
    for d in dirs:
        path = os.path.join(target, d)
        os.makedirs(path, exist_ok=True)
        print(f"  Created: {d}/")

    # Copy snapshot.py from our sibling directory
    installer_dir = os.path.dirname(os.path.abspath(__file__))
    snapshot_src = os.path.join(installer_dir, "..", "blueprint", "snapshot.py")
    snapshot_dst = os.path.join(target, "tools", "blueprint", "snapshot.py")

    if os.path.exists(snapshot_src):
        shutil.copy2(snapshot_src, snapshot_dst)
        print(f"  Copied: tools/blueprint/snapshot.py")
    else:
        # Fallback: try to find it relative to the installer
        print(f"  Warning: snapshot.py not found at {snapshot_src}")
        print(f"  You'll need to copy it manually to tools/blueprint/snapshot.py")

    # Create template docs (only if they don't already exist)
    templates = {
        "docs/00_BLUEPRINT.md": _BLUEPRINT_TEMPLATE,
        "docs/INTERFACE_MAP.md": _INTERFACE_MAP_TEMPLATE,
        "docs/DB_CONTRACT.md": _DB_CONTRACT_TEMPLATE,
        "docs/SAFE_CHANGELOG.md": _SAFE_CHANGELOG_TEMPLATE,
        "docs/adr/0001-architecture-baseline.md": _ADR_TEMPLATE,
        "docs/snapshots/README.md": _SNAPSHOTS_README,
    }

    for rel_path, content in templates.items():
        full_path = os.path.join(target, rel_path)
        if os.path.exists(full_path):
            print(f"  Skipped (exists): {rel_path}")
        else:
            with open(full_path, "w", encoding="utf-8", newline="\n") as f:
                f.write(content)
            print(f"  Created: {rel_path}")

    # Wire up package.json if present
    pkg_json = os.path.join(target, "package.json")
    if os.path.exists(pkg_json):
        try:
            with open(pkg_json, "r", encoding="utf-8") as f:
                pkg = json.load(f)
            scripts = pkg.setdefault("scripts", {})
            if "snapshot" not in scripts:
                scripts["snapshot"] = "node tools/blueprint/snapshot.mjs || python tools/blueprint/snapshot.py"
                with open(pkg_json, "w", encoding="utf-8", newline="\n") as f:
                    json.dump(pkg, f, indent=2, ensure_ascii=False)
                    f.write("\n")
                print(f"  Added 'snapshot' script to package.json")
            else:
                print(f"  Skipped: package.json already has 'snapshot' script")
        except Exception as e:
            print(f"  Warning: Could not update package.json: {e}")

    print()
    print("Installation complete!")
    print()
    print("Next steps:")
    print("  1. Generate initial snapshots:")
    print(f"     python tools/blueprint/snapshot.py")
    print("  2. Fill in the template docs in docs/")
    print("  3. Regenerate snapshots whenever the project structure changes")


# ---------------------------------------------------------------------------
# Templates
# ---------------------------------------------------------------------------

_BLUEPRINT_TEMPLATE = """# Project Blueprint

> **Purpose**: TODO — describe what this project does.

## Repo Assessment

| Attribute | Value |
|-----------|-------|
| Language | TODO |
| Framework | TODO |
| DB / ORM | TODO |
| Tests | TODO |
| Entry point | TODO |

## Architecture Overview

```
TODO: draw the module/directory structure
```

## Data Flow

```
TODO: describe the main data flow
```

## Key Conventions

- TODO

## File Inventory

| File | Role |
|------|------|
| TODO | TODO |
"""

_INTERFACE_MAP_TEMPLATE = """# Interface Map

## Entry Points

| Type | Path | Invocation |
|------|------|-----------|
| TODO | TODO | TODO |

## Public Module Interfaces

TODO: list public functions/classes with signatures
"""

_DB_CONTRACT_TEMPLATE = """# Database Contract

## Status: TODO

TODO: document schema, migrations, invariants, or state "No Database" if none.
"""

_SAFE_CHANGELOG_TEMPLATE = """# Safe Changelog

## Before Any Change

1. Read the blueprint (`docs/00_BLUEPRINT.md`)
2. TODO: list project-specific precautions

## High-Risk Areas

| Area | Risk | Why |
|------|------|-----|
| TODO | TODO | TODO |

## Change Checklist

- [ ] TODO: project-specific checks
- [ ] Run tests
- [ ] Regenerate snapshots: `python tools/blueprint/snapshot.py`
"""

_ADR_TEMPLATE = """# ADR-0001: Architecture Baseline

**Status**: Accepted
**Date**: TODO
**Context**: Documenting the initial architecture.

## Decision

TODO: describe the architecture as-built.

## Consequences

TODO: what are the trade-offs?
"""

_SNAPSHOTS_README = """# Snapshots

Machine-generated summaries of the project state. Feed these to an LLM for quick context.

## Files

| File | Contents |
|------|----------|
| `tree.txt` | Filtered directory tree |
| `entrypoints.txt` | Detected entry points |
| `deps.txt` | Dependencies |
| `db.txt` | Database/ORM detection |
| `tests.txt` | Test infrastructure |
| `env.txt` | Environment files (key names only) |

## Regenerate

```bash
python tools/blueprint/snapshot.py
```
"""


if __name__ == "__main__":
    main()
