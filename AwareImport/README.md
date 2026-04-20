# AwareImport — CML Batch Builder

Desktop GUI tool for batch-parsing UT (ultrasonic thickness) Excel inspection sheets and exporting Aware CML Table import CSV files.

## Quick Start

```bash
pip install -r requirements.txt
python main.py
```

## Project Blueprint

This repository includes a **Project Blueprint** system — a set of concise, LLM-optimized docs that describe the architecture, interfaces, and safe-change procedures.

### What it is

Machine-readable project documentation designed for fast LLM context loading. Includes architecture docs, interface maps, and auto-generated snapshots of the project structure.

### How to regenerate snapshots

```bash
python tools/blueprint/snapshot.py
```

This updates all files in `docs/snapshots/` with the current project state. Run this after adding/removing files or changing dependencies.

### What to feed an LLM when starting work

For **full context** (recommended for new contributors or major changes):
```
docs/00_BLUEPRINT.md          # Architecture overview
docs/INTERFACE_MAP.md         # All public interfaces
docs/SAFE_CHANGELOG.md        # How to change safely
docs/snapshots/tree.txt       # Current file tree
docs/snapshots/deps.txt       # Dependencies
```

For **quick orientation** (minor bug fixes or small features):
```
docs/00_BLUEPRINT.md          # Architecture overview
docs/snapshots/tree.txt       # Current file tree
```

### Blueprint file index

| File | Purpose |
|------|---------|
| `docs/00_BLUEPRINT.md` | Architecture overview, data flow, file inventory |
| `docs/INTERFACE_MAP.md` | Entry points, public APIs, signal map |
| `docs/DB_CONTRACT.md` | Data persistence (no DB — JSON sessions + QSettings) |
| `docs/SAFE_CHANGELOG.md` | Change checklist, high-risk areas, manual test plan |
| `docs/adr/0001-architecture-baseline.md` | Architecture Decision Record |
| `docs/snapshots/` | Auto-generated project state snapshots |
| `tools/blueprint/snapshot.py` | Snapshot generator (zero dependencies) |
| `tools/blueprint_installer/` | Portable installer for adding blueprints to other repos |
