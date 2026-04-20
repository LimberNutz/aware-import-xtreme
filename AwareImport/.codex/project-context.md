# Project Context

## Snapshot
- Project: AwareImport (CML Batch Builder desktop GUI).
- Last updated (UTC): 2026-03-17T21:45.
- Maintainer/session: Bootstrap generated with `$project-context-memory`.
- Primary goal: Parse UT Excel sheets (`.xlsx/.xlsm`) into canonical CML rows, review in GUI, and export Aware-import CSV files.

## Quick Start
- Install: `pip install -r requirements.txt`
- Run: `python main.py`
- Refresh blueprint snapshots: `python tools/blueprint/snapshot.py`

## Directory Map
- `main.py`: Qt app bootstrap and stylesheet.
- `app/`: domain constants and app config (`app/constants.py` is high impact).
- `models/`: Pydantic canonical models (`CMLRow`, `EntityInfoRow`, `FileEntry`).
- `services/`: parse/transform/aggregate/export/writeback/session/worker logic.
- `ui/`: Main window orchestration and widgets.
- `utils/`: helpers (`temp_open_workbook`, CML formatting, safety helpers).
- `docs/`: blueprint docs and snapshots used for fast context loading.
- `tools/`: blueprint maintenance and installer helpers.

## Critical Files
- `models/cml_row.py`: Canonical schema; all services depend on this contract.
- `app/constants.py`: CSV headers, Excel column maps, defaults, sheet detection.
- `services/excel_parser.py`: Reads UT sheets; parser changes can silently corrupt downstream output.
- `services/transformer.py`: Applies defaults and normalizes row fields.
- `services/aggregator.py`: Deduplicates by `(system_path, system_name, cml)`.
- `services/entity_info.py`: Builds entity rows and PDF/workbook-derived metadata.
- `services/csv_exporter.py`: Writes grouped entity + CML rows to Aware CSV format.
- `services/excel_writer.py`: Writes edits back to source Excel files (destructive if wrong).
- `services/session.py`: JSON session persistence with schema versioning.
- `ui/main_window.py`: Central signal wiring and mode orchestration.
- `docs/00_BLUEPRINT.md`: High-signal architecture reference for fast onboarding.
- `docs/SAFE_CHANGELOG.md`: Required guardrails and manual validation checklist.

## Architecture and Flows
- Primary flow: Excel files -> `services/excel_parser.py` -> `services/transformer.py` -> `services/aggregator.py` -> `services/csv_exporter.py`.
- Secondary flow (TA mode): Parsed rows -> `services/thickness_activity.py` -> per-file Thickness Activity table.
- Writeback flow: edited grid cells -> `services/excel_writer.py` -> source workbook updates.
- Session flow: in-memory state -> `services/session.py` JSON save/load.
- UI flow: `ui/main_window.py` coordinates workers (`services/worker.py`) and panel updates.

## Constraints and Invariants
- Treat `CMLRow` as canonical data model; when fields change, update parser, transformer, exporter, writeback maps, and session handling.
- Keep CSV header order aligned with `AWARE_CSV_HEADERS` and exporter mapping keys.
- Maintain parser/writeback column mapping parity (`PIPING_COLUMN_MAP`, writer column maps).
- Preserve dedupe behavior keyed on `(system_path, system_name, cml)` unless a migration is intentional.
- Assume no automated test safety net; rely on manual regression checks in `docs/SAFE_CHANGELOG.md`.

## Current Risks
- No automated tests; regressions are likely unless manual checks are run on real UT files.
- `services/excel_writer.py` modifies source files; mistakes are user-impacting.
- Parser and constants are tightly coupled; small constant drift can break parsing/export correctness.
- Git currently tracks `__pycache__` artifacts, causing noisy diffs and accidental churn.

## Recent Changes
- 2026-03-17 (`6b082e9`): Updated CSV header format and executable permissions; touched `services/entity_info.py`, `services/excel_writer.py`, and UI files.
- 2026-03-10 (`77baab3`): Added entity info export with PDF metadata support; broad repo updates including docs and service modules.

## Open Questions
- Should `__pycache__/` artifacts be removed from tracking and ignored going forward?
- Should project memory live in `.codex/` or a repo-writable fallback path due local ACL constraints?
- Are there fixture workbooks available for repeatable parser/export regression checks?

## Next Session Plan
- First files to inspect: `services/csv_exporter.py`, `app/constants.py`, `services/entity_info.py`, `services/excel_writer.py`, `ui/main_window.py`.
- Expected change area: CSV/entity mapping correctness and writeback safety.
- Validation checklist:
  - Parse known workbook and compare expected row count.
  - Export CSV and verify header alignment and row grouping.
  - Edit one preview cell and verify source workbook update behavior.
  - Save and reload session to ensure compatibility.
