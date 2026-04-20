# AwareImport — Project Blueprint

> **Purpose**: CML Batch Builder — a desktop GUI tool that batch-parses UT (ultrasonic thickness) Excel inspection sheets and exports them as CSV files formatted for import into the Aware CML Table system. Also supports a "Thickness Activity" per-file review mode.

## Repo Assessment

| Attribute | Value |
|-----------|-------|
| Language | Python 3.12 |
| GUI Framework | PySide6 (Qt for Python) |
| Data Models | Pydantic v2 (`models/cml_row.py`) |
| Excel I/O | openpyxl (read & write-back) |
| Fuzzy matching | thefuzz |
| File deletion | send2trash |
| DB / ORM | **None** — no database; all state is in-memory or JSON session files |
| Tests | **None detected** — no test directory or test runner configured |
| Package manager | pip + `requirements.txt` |
| Entry point | `python main.py` |
| Platform | Windows (uses `os.startfile`, Explorer subprocess, QSettings registry) |

## Architecture Overview

```
main.py                          # QApplication bootstrap + dark-theme QSS
├── ui/
│   ├── main_window.py           # MainWindow — orchestrator, signal wiring
│   ├── controls_bar.py          # Top toolbar: inputs, buttons, mode combo
│   ├── file_list_panel.py       # Left panel: drag-drop file table
│   ├── preview_panel.py         # Right panel: CML preview + TA tables
│   └── dialogs.py               # FuzzyMatchDialog, SearchDialog
├── services/
│   ├── excel_parser.py          # Parse .xlsx/.xlsm UT sheets → CMLRow list
│   ├── transformer.py           # Apply defaults, CML formatting, validation
│   ├── aggregator.py            # Deduplicate rows by (path, name, cml)
│   ├── csv_exporter.py          # Write Aware-format CSV
│   ├── excel_writer.py          # Write-back edited cells to source Excel
│   ├── thickness_activity.py    # Build per-file TA view from CMLRows
│   ├── file_discovery.py        # Recursive find, fuzzy match, batch search
│   ├── session.py               # JSON save/load of workspace state
│   └── worker.py                # QThread workers: ParseWorker, FolderScanWorker
├── models/
│   └── cml_row.py               # CMLRow (Pydantic), FileEntry (Pydantic)
├── app/
│   ├── config.py                # AppConfig dataclass
│   └── constants.py             # CSV headers, column maps, defaults, thresholds
└── utils/
    └── helpers.py               # safe_str, CML formatting, temp workbook opener
```

## Data Flow

```
Excel files (.xlsx/.xlsm)
  │
  ▼  excel_parser.parse_excel_file()
CMLRow[]  (raw parsed rows)
  │
  ▼  transformer.transform_rows()
CMLRow[]  (defaults applied, CML formatted, validated)
  │
  ├──▶ aggregator.aggregate_rows() ──▶ csv_exporter.export_csv() ──▶ .csv
  │
  └──▶ thickness_activity.build_thickness_activity_view() ──▶ TA table (per-file)
```

## Two Modes

1. **CML Import** (default) — batch parse all files → aggregate → preview → export CSV for Aware import.
2. **Thickness Activity** — select a single file → view per-CML row data with baseline threshold flagging (UT < 87.5% of Nominal).

## Key Conventions

- **CMLRow** is the canonical data model; all services operate on it.
- Excel files are opened via `temp_open_workbook()` (copy-to-temp pattern to avoid file locking).
- Write-back modifies source Excel files in-place via openpyxl.
- Session state serialised as JSON (versioned with `SESSION_VERSION`).
- QSettings persists UI state (last folder, system path) in Windows registry under `CMLBatchBuilder/AwareImport`.
- Material defaults cascade: Carbon vs Stainless, Straight Pipe vs other.
- Deduplication key: `(system_path, system_name, cml)` — most-recent file wins.

## File Inventory

| File | Lines | Role |
|------|-------|------|
| `main.py` | ~220 | App bootstrap + QSS stylesheet |
| `app/config.py` | ~15 | AppConfig dataclass |
| `app/constants.py` | ~127 | All domain constants |
| `models/cml_row.py` | ~69 | CMLRow + FileEntry models |
| `services/excel_parser.py` | ~302 | Core parsing logic |
| `services/transformer.py` | ~129 | Defaults + validation |
| `services/aggregator.py` | ~23 | Row deduplication |
| `services/csv_exporter.py` | ~83 | CSV export |
| `services/excel_writer.py` | ~171 | Write-back to Excel |
| `services/thickness_activity.py` | ~107 | TA view builder |
| `services/file_discovery.py` | ~141 | File search + fuzzy match |
| `services/session.py` | ~71 | Session save/load |
| `services/worker.py` | ~106 | QThread workers |
| `ui/main_window.py` | ~492 | Main window orchestrator |
| `ui/controls_bar.py` | ~223 | Toolbar widget |
| `ui/file_list_panel.py` | ~415 | File list widget |
| `ui/preview_panel.py` | ~610 | Preview tables + models |
| `ui/dialogs.py` | ~272 | Fuzzy match + search dialogs |
| `utils/helpers.py` | ~100 | Utility functions |
