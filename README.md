# Aware Toolbox

A unified launcher for four inspection / engineering utilities that previously lived as separate projects:

| Tool | Purpose |
|------|---------|
| **ACAD Fixer** | Automate CAD (DWG/DXF) + PDF title block updates from CML reports |
| **AwareImport** | Batch-parse UT Excel inspection sheets → Aware CML import CSVs |
| **File Scout 2025** | Find, audit, and organize files across directories (search, dedup, smart sort, Drive audit) |
| **Design Doc Importer** | Build Aware IDMS design document import CSVs from a CAD folder |

---

## Quick Start

```bash
pip install -r requirements.txt
python launcher.py
```

Each tool also has its own `requirements.txt` inside its subfolder — install those the first time you launch the corresponding tool.

---

## Architecture

```
Aware Import Xtreme/
├─ launcher.py                 # entry point (PySide6, dark theme)
├─ launcher/
│  ├─ tool_registry.py         # tool definitions + local-venv auto-detection
│  ├─ process_manager.py       # subprocess lifecycle + poll + graceful shutdown
│  ├─ tool_card.py             # card widget (hover, status pill, right-click menu)
│  ├─ main_window.py           # 2×2 card grid + activity log + QSettings geometry
│  └─ design_doc_dialog.py     # in-process GUI for Design Doc Importer
├─ ACAD Fixer/                 # subprocess (PySide6, main.py --gui)
├─ AwareImport/                # subprocess (PySide6, main.py)
│  └─ DesignDocImporter/       # imported directly by the launcher dialog
└─ File Scout 2025/            # subprocess (PyQt6, uses .venv if present)
```

### Why subprocess isolation?

**File Scout 2025 uses PyQt6**, while ACAD Fixer and AwareImport use **PySide6**. These two bindings are binary-incompatible and cannot coexist in one Python process, so each tool is spawned as a separate subprocess. This also means:

- A crash in any tool never affects the launcher or the other tools.
- Each tool keeps its own `sys.path`, working directory, and (optionally) its own `.venv`.

The Design Doc Importer is the exception — it has no Qt dependency at all, so the launcher imports `design_doc_csv_builder2.py` directly via `importlib` and runs it in a `QThread`.

### Python interpreter resolution

`tool_registry._python_for()` looks for a `.venv/Scripts/python.exe` inside each tool's folder and uses it if present, otherwise falls back to the interpreter running the launcher itself. This is how File Scout 2025 automatically runs against its bundled PyQt6 venv.

---

## Launcher features

- **Card hub** — each tool has its own card with icon, features, status pill, and Launch/Stop/Relaunch button
- **Right-click context menu** — Launch/Stop + "Open Tool Folder in Explorer"
- **Activity log** — timestamped launch, exit, and error messages (capped at 500 lines)
- **Graceful shutdown** — closing the launcher terminates every running tool
- **Remembers window geometry** — restores the last size and position via `QSettings`
- **Pre-flight checks** — verifies the working directory and entry script exist before calling `subprocess.Popen`, with clear error messages in the activity log
- **Hover feedback** — card border turns accent-blue on mouseover
- **Dark theme** — reuses the VS Code-inspired palette from AwareImport

---

## Design Doc Importer dialog

Runs in-process as a `QDialog`. Fields are organized into three clearly-labelled sections:

- **Required ✱** — CAD Root Dir, System Path Base (with descriptive hints under each)
- **Output** — Output Dir, Project Name, Filename Override (all optional)
- **Scan Options** — Max Depth, Auto-discover entities, Ignore `_recover` files, Prefer DWG for entity discovery

Config file controls:
- **Load** — populate all fields from an existing `job_config.txt`
- **Save Config** — write the current fields to a commented, self-documenting `.txt`
- **New / Clear** — reset to defaults for a fresh config

If `job_config.txt` exists in the `DesignDocImporter` folder, it's loaded automatically when the dialog opens.

---

## Development

Syntax-check all launcher files:

```bash
python -m py_compile launcher.py launcher/*.py
```
