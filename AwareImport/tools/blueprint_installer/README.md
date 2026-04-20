# Blueprint Installer

Portable installer that adds the Project Blueprint system to any repository.

## Requirements

- Python 3.8+ (no external packages needed)
- OR: a shell with `bash` available (fallback)

## Usage

```bash
# Install into the current repo
python tools/blueprint_installer/install.py

# Install into a different repo
python tools/blueprint_installer/install.py /path/to/other/repo
```

## What It Does

1. Creates the `docs/` directory structure with template files
2. Copies `tools/blueprint/snapshot.py` (the snapshot generator)
3. If `package.json` exists, adds a `"snapshot"` npm script
4. Prints next-step instructions

## After Installation

1. Run `python tools/blueprint/snapshot.py` to generate initial snapshots
2. Fill in the template docs in `docs/` with project-specific information
3. Regenerate snapshots whenever the project structure changes

## What Gets Created

```
docs/
  00_BLUEPRINT.md          # Main architecture doc (template)
  INTERFACE_MAP.md         # Module interfaces (template)
  DB_CONTRACT.md           # Database contract (template)
  SAFE_CHANGELOG.md        # Change safety guide (template)
  adr/
    0001-architecture-baseline.md  # ADR template
  snapshots/
    README.md              # Snapshot docs
tools/
  blueprint/
    snapshot.py            # Snapshot generator script
```

## Re-running

Safe to re-run — existing files are never overwritten (skipped with a message).
