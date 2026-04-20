# ADR-0001: Architecture Baseline

**Status**: Accepted
**Date**: 2026-02-26
**Context**: Documenting the initial architecture of AwareImport as-found.

## Decision

AwareImport is a single-process desktop GUI application using:

- **PySide6** for the UI (Qt Widgets, not QML)
- **Pydantic v2** for data models (CMLRow, FileEntry)
- **openpyxl** for Excel read/write
- **thefuzz** for entity name fuzzy matching
- **send2trash** for safe file deletion
- No database; in-memory state with optional JSON session persistence

## Architecture Pattern

**MVC-ish with service layer**:
- `ui/` = View layer (Qt widgets, models, delegates)
- `services/` = Business logic (parsing, transforming, exporting, I/O)
- `models/` = Data models (Pydantic)
- `app/` = Configuration and constants
- `utils/` = Shared utilities

`MainWindow` acts as the controller, wiring UI signals to service calls.

## Key Constraints

- **No internet access required** — fully offline desktop tool
- **Windows-only** — uses `os.startfile`, Explorer subprocess, Windows registry QSettings
- **File locking avoidance** — temp-copy pattern for reading Excel files
- **Write-back is destructive** — modifies source Excel files; no undo at file level

## Consequences

- Adding a backend/server would require extracting `services/` into a standalone layer
- No automated tests exist; manual testing is the only validation
- Session file versioning (`SESSION_VERSION`) provides forward-compatibility guard
- QSettings stored in registry means settings don't travel with the project

## Alternatives Considered

Not documented — this ADR captures the as-built state, not a deliberate selection process.
