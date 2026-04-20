# File Scout 3.2 Refactoring Plan

## Current Task
Refactor complete. All phases implemented and stabilization pass done. App is runnable.

## Progress
[X] Analyze current code structure and identify module boundaries
[X] Create detailed extraction plan with Claude Code in mind
[X] Review scratchpad and align current prompt-planning task
[X] Draft ordered Claude Code prompts for each refactor phase
[X] Provide batching guidance for Claude Code paste workflow
[X] Implement Phase 0: Freeze interfaces
[X] Implement Phase 1: Zero-risk extractions
[X] Implement Phase 2: Preview subsystem
[X] Implement Phase 3: Profiles
[X] Implement Phase 4A: Extract SearchEngine
[X] Implement Phase 4B: Extract FileSearchWorker
[X] Implement Phase 4: Core search
[X] Implement Phase 5A: Extract SmartSortDialog
[X] Implement Phase 5B: Extract Smart Sort helpers
[X] Implement Phase 5: Smart Sort
[X] Implement Phase 6: File Audit
[X] Implement Phase 7: Main window
[X] Final stabilization and cleanup pass

## Key Insights
- FileScoutApp is the main orchestrator
- Signal contract: SearchEngine only emits `progress_update`, FileSearchWorker has 4 signals and translates
- FileAuditDialog already externalized
- Preview system is cleanest extraction target (base class + handlers)
- SmartSortDialog mixes UI and algorithmic logic - needs two-phase extraction

---

## Interface Control Document (Phase 0)

### Canonical Worker Signals (FileSearchWorker)
| Signal | Signature | Direction |
|---|---|---|
| `progress_update` | `pyqtSignal(int, str)` | worker → UI |
| `search_complete` | `pyqtSignal(bool, str)` | worker → UI |
| `live_result` | `pyqtSignal(dict)` | worker → UI (file search mode) |
| `duplicate_group_found` | `pyqtSignal(list)` | worker → UI (duplicate mode) |

Internal bridge: `SearchEngine.progress_update` connected signal-to-signal → `FileSearchWorker.progress_update` (line ~500).

### Canonical Engine Public Methods (SearchEngine)
| Method | Signature | Notes |
|---|---|---|
| `find_files` | `(params: dict) → Generator[dict]` | Yields file_info dicts |
| `find_duplicates` | `(params: dict) → Generator[list[dict]]` | Yields groups of file_info dicts |
| `stop` | `() → None` | Sets self.stopped = True |
| `get_result_summary` | `() → dict` | Returns `{'match_count': int, 'group_count': int}` |

### Canonical Preview Manager API
| Method | Signature | Location | Notes |
|---|---|---|---|
| `PreviewManager.generate_preview` | `(file_path, max_size=1048576) → PreviewResult` | `features/preview/manager.py` | Wraps handler tuples at boundary |
| `PreviewManager.get_handler` | `(file_path) → PreviewHandler \| None` | `features/preview/manager.py` | First matching handler |
| `PreviewHandler.can_handle` | `(file_path) → bool` | `features/preview/handlers.py` | Extension-based check |
| `PreviewHandler.generate_preview` | `(file_path, max_size) → tuple(content_type, data, metadata)` | `features/preview/handlers.py` | Raw tuple; manager wraps to PreviewResult |

`PreviewResult = namedtuple('PreviewResult', ['content_type', 'data', 'metadata'])` — defined in `constants.py`, backward-compatible with tuple unpacking.

**Preview API assumptions future phases must preserve:**
- `generate_preview()` always returns a PreviewResult (never None, never raises)
- `content_type` is one of: `"text"`, `"html"`, `"pdf_dual"`, `"error"`
- `metadata` is always a dict (may be empty)
- Handlers own their optional-dependency checks; callers never check lib availability
- `get_handler()` returns None for unsupported types; `generate_preview()` returns error PreviewResult
- PDFViewerWidget in monolith still imports `fitz`/`PYMUPDF_AVAILABLE` directly — not via preview module

### Temporary Compatibility Aliases
| What | Where | Status | Remove when |
|---|---|---|---|
| `QSettings(SETTINGS_ORG, SETTINGS_APP)` direct calls | Main window settings access | Resolved — `FileScoutApp` now uses `config.get_settings()` in `ui/main_window.py` | Completed in Phase 7 |
| `fitz`/`PYMUPDF_AVAILABLE` import duplication | `ui/main_window.py` and preview handlers | Reduced to extracted main-window ownership plus preview handler optional import | Cleanup only if future preview/main-window convergence needs it |

### UI Callsites Depending on Frozen Interfaces
**Worker signals → FileScoutApp slots:**
- `search_worker.progress_update` → `self.update_progress`
- `search_worker.search_complete` → `self.search_finished`
- `search_worker.duplicate_group_found` → `self.add_duplicate_group_to_table`
- `search_worker.live_result` → `self.add_result_to_table`

**Engine methods (called from FileSearchWorker.run):**
- `self.engine.find_duplicates(self.params)`
- `self.engine.find_files(self.params)`
- `self.engine.get_result_summary()`
- `self.engine.stop()`

**Engine methods (CLI path):**
- `engine.progress_update.connect(...)`
- `engine.find_files(params)`

**Preview manager (called from FileScoutApp):**
- `self.preview_manager.generate_preview(str(file_path))` — via `from features.preview.manager import PreviewManager`
- `self.preview_manager.get_handler(file_path)` — for properties tab handler info

---

## Phase 1 Extracted Modules
- `constants.py` — APP_NAME, APP_VERSION, SETTINGS_*, MAX_*, PreviewResult, ICON_*, EXCLUDED_EXTENSIONS, FILE_TYPE_MAPPINGS
- `config.py` — get_settings() helper (available for future phases; monolith still uses QSettings directly)
- `utils/themes.py` — THEME_COLORS dict (33 themes)
- `utils/excel_exporter.py` — ExcelExporter class
- `ui/widgets/custom_widgets.py` — DropLineEdit class
- Monolith reduced from 4591 to 4037 lines (~554 lines extracted)

## Phase 2 Extracted Modules
- `features/preview/handlers.py` — PreviewHandler base + 11 concrete handlers + all optional dependency imports
- `features/preview/manager.py` — PreviewManager class
- Preview-only optional imports removed from monolith (pygments, docx, pptx, mutagen, openpyxl, xlrd)
- `fitz`/`PYMUPDF_AVAILABLE` kept in monolith for PDFViewerWidget (dual import, see compat aliases)
- Monolith reduced from 4037 to 3511 lines (~526 lines extracted)

## Phase 3 Extracted Modules
- `ui/dialogs/profile_manager.py` — ProfileManagerDialog class
- Dialog now uses `config.get_settings()` instead of `QSettings(SETTINGS_ORG, SETTINGS_APP)` directly
- Monolith reduced from 3511 to 3429 lines (~82 lines extracted)
- QSettings direct-call compat shim reduced from 2 callsites to 1 (FileScoutApp only)

## Phase 4A Extracted Modules
- `core/search_engine.py` — SearchEngine class
- Monolith now imports `SearchEngine` from `core.search_engine`
- `FileSearchWorker` remains in the monolith and keeps the same UI-facing signal contract
- CLI search path now uses imported `SearchEngine` with no callsite change
- Monolith reduced from 3429 to 3005 lines (~424 lines extracted)

## Phase 4B Extracted Modules
- `core/file_scanner.py` — FileSearchWorker class
- Monolith now imports `FileSearchWorker` from `core.file_scanner`
- `FileSearchWorker` still owns the thread boundary, engine wiring, stop lifecycle, and UI-safe worker signals
- Main-window search orchestration callsites remain unchanged beyond the import path
- Search-specific Qt imports and search-only constants were removed from the monolith import surface

## Phase 5A Extracted Modules
- `ui/dialogs/smart_sort_dialog.py` — SmartSortDialog class
- Monolith now imports `SmartSortDialog` from `ui.dialogs.smart_sort_dialog`
- Main-window callsite remains `SmartSortDialog(self, files, default_root, zoom_level=self.zoom_level)`
- Dialog behavior is preserved, including zoom handling, unmatched-file preview flow, and execute/copy-or-move actions
- Current parent callback contract is unchanged: `parent_app._generate_unique_dest_path()` and `parent_app.remove_files_from_results()`
- Phase 5B should separate Smart Sort algorithm/file-operation helpers from the dialog after this UI extraction stabilizes

## Phase 5B Extracted Modules
- `features/smart_sort/pattern_matcher.py` — folder scanning, pattern matching, extension mapping, and destination suggestion helpers
- `features/smart_sort/fuzzy_matcher.py` — fuzzy folder suggestion helpers for unmatched files
- `features/smart_sort/sort_executor.py` — non-UI file operation executor for copy/move processing
- `features/smart_sort/__init__.py` — package exports for the Smart Sort feature area
- `ui/dialogs/smart_sort_dialog.py` now delegates non-UI matching and execution logic to `features.smart_sort`
- Smart Sort UI remains responsible for table rendering, confirmation prompts, unmatched-file preview acceptance, and parent callback wiring

## Phase 6 Extracted Modules
- `ui/dialogs/file_audit_dialog.py` — canonical File Audit dialog import path for the UI layer
- `file_audit_dialog.py` remains the implementation module for now to preserve existing file-relative behavior
- `ui/dialogs/file_audit_dialog.py` is currently a thin bridge that re-exports `FileAuditDialog` and related File Audit symbols from the root module
- Monolith now imports `FileAuditDialog` from `ui.dialogs.file_audit_dialog`
- Main-window File Audit callsite remains `FileAuditDialog(self, theme=self.current_theme, zoom_level=self.zoom_level)`

## Phase 7 Extracted Modules
- `ui/main_window.py` — `PDFViewerWidget`, `FileScoutApp`, and the `main()` entrypoint
- `File Scout 3.2.py` now acts as a legacy wrapper that imports from `ui.main_window`
- Main-window settings initialization now uses `config.get_settings()` instead of direct `QSettings(SETTINGS_ORG, SETTINGS_APP)` construction
- The extracted module now imports `SearchEngine` explicitly for the preserved CLI search path
- Tray icon lookup was rebased to `Path(__file__).resolve().parent.parent / "filescout.png"` so the moved module still finds the root asset

### Phase 7 Checkpoint Results
- [X] No duplicate class defs remain in the monolith for `PDFViewerWidget` or `FileScoutApp`
- [X] `ui/main_window.py` compiles clean
- [X] `File Scout 3.2.py` compiles clean as the legacy wrapper entrypoint
- [X] Runtime imports resolve for `from ui.main_window import FileScoutApp, PDFViewerWidget, main`
- [X] The legacy wrapper exports the same `FileScoutApp` and `PDFViewerWidget` objects as `ui.main_window`
- [X] `FileScoutApp` now uses `config.get_settings()` in the extracted module
- [X] No `QSettings(SETTINGS_ORG, SETTINGS_APP)` call remains in `File Scout 3.2.py`
- [X] CLI search path remains intact in the extracted module via explicit `SearchEngine` import
- [X] The moved tray icon path resolves from the new module location

### Phase 7 Final State
- [X] `ui/main_window.py` is the canonical home for `PDFViewerWidget`, `FileScoutApp`, and `main()`
- [X] `File Scout 3.2.py` is now a compatibility wrapper around the extracted main-window module
- [X] Phase 7 complete

---

## Final Stabilization Pass (Post-Phase 7)
[X] Scanned full project tree and import graph — no broken or circular imports found
[X] Stripped `File Scout 3.2.py` from 78-line monolith copy to 18-line minimal wrapper
[X] Removed 8 dead imports from `ui/main_window.py`: `time`, `struct`, `base64`, `zipfile`, `xml.etree.ElementTree`, `SETTINGS_ORG`, `SETTINGS_APP`, `PreviewHandler`
[X] Cleaned `# <-- ADDED IMPORT` dev comment artifact
[X] Verified all 18 modules pass `py_compile`
[X] Verified all extracted-module runtime imports resolve cleanly
[X] Confirmed package boundaries are clean — no cross-layer imports, no circular deps

### Remaining Technical Debt
1. **`file_audit_dialog.py` still at repo root** — `ui/dialogs/file_audit_dialog.py` is a thin bridge re-exporting from the root module. Moving the implementation requires rebasing `__file__`-relative credential file lookup (`google_credentials.json`, `google_token.pickle`). Low risk to leave; move when File Audit gets its own config.
2. **`fitz`/`PYMUPDF_AVAILABLE` dual import** — imported in both `ui/main_window.py` (for `PDFViewerWidget`) and `features/preview/handlers.py` (for `PDFPreviewHandler`). Harmless; resolve only if `PDFViewerWidget` is ever extracted to the preview subsystem.
3. **`SmartSortDialog` parent coupling** — still depends on `parent_app._generate_unique_dest_path()` and `parent_app.remove_files_from_results()`. Could be replaced with dependency injection but works fine as-is.
4. **`SearchEngine` params dict is untyped** — the `params` dict flowing through `find_files`/`find_duplicates` has no schema. Document or type it when the engine gets its own tests.
5. **`features/smart_sort/__init__.py` re-exports are unused** — `smart_sort_dialog.py` imports directly from sub-modules. The `__init__.py` exports exist for public API convenience but have no consumer today.
6. **`ui/main_window.py` Qt import block is broad** — imports many PyQt6 symbols. A full audit of which are used was deferred (2500-line UI file). Low risk; only cosmetic.
7. **No automated test suite** — `test_import_fix.py` and `test_smart_sort_enhanced.py` exist but are ad-hoc. A proper pytest suite covering the validation targets below would catch regressions.

---

## Lessons
- Normalize signal names before extraction
- Keep feature modules returning data, not UI mutations
- Don't split stable externalized modules early
- Batch related extractions to minimize context switching
- Extract interfaces first to prevent breakage
- FileSearchWorker.run() was reading engine.match_count/group_count directly — decoupled via get_result_summary() before extraction
- Signal names between SearchEngine and FileSearchWorker are already aligned (both use `progress_update`) — no bridge needed
- Preview handlers return bare tuples internally; PreviewManager wraps to PreviewResult at the boundary — handlers don't need updating during extraction
- The `params` dict flowing through SearchEngine is implicit (no schema) — future phases should document its keys when extracting SearchEngine
- Base64 icon strings are fragile to copy/paste — always read exact bytes from file before editing lines containing them
- config.py provides get_settings() but monolith still uses QSettings(SETTINGS_ORG, SETTINGS_APP) directly in two places — can migrate later without risk
- Always run the checkpoint protocol before declaring a phase complete — catches lingering defs and broken imports before they compound
- When a library (fitz) is shared between extracted module and remaining monolith code, accept dual imports as temporary state — document in compat aliases and resolve when the consumer moves
- Optional dependency gating belongs inside feature modules, not at the app root — keeps the monolith's import section honest about what IT actually needs
- Phase 4A is safest when `FileSearchWorker` stays put and only swaps its `SearchEngine` import — isolates the extraction from UI signal risk
- `SearchEngine` depends on `constants.py` plus stdlib/PyQt core only after extraction; that boundary is clean enough for Phase 4B to build on
- The CLI search path is an easy regression check for `SearchEngine` extraction because it instantiates the engine outside the worker
- Phase 4B is low-risk when the main window keeps constructing `FileSearchWorker(params)` exactly the same way and only the import path changes
- After extracting both search classes, the monolith import block becomes a useful cleanup checkpoint — dead Qt imports and search-only constants should be removed immediately
- The stable worker contract now lives naturally at the `core.file_scanner` boundary, which makes Phase 5 less likely to accidentally re-entangle UI and search logic
- Phase 5A is safe as a straight UI extraction because `SmartSortDialog` only depends on two parent callbacks: `_generate_unique_dest_path()` and `remove_files_from_results()`
- Keep the Smart Sort dialog constructor and callsite unchanged during Phase 5A; defer constructor cleanup and algorithm decomposition to Phase 5B to avoid mixing concerns across one extraction
- Phase 5B is cleanest when the split follows responsibility boundaries, not method count: folder scanning/matching and file execution move out, while Qt tables and dialogs remain local to the UI module
- Keeping thin wrapper methods in `SmartSortDialog` for extracted helpers preserves the dialog's internal shape and reduces blast radius for future UI changes
- For path-sensitive modules like `file_audit_dialog.py`, a thin bridge under the target package path is safer than moving the implementation immediately because `__file__`-relative resource lookup can change silently
- When extracting the main window, move `PDFViewerWidget`, `FileScoutApp`, and `main()` together because the preview, tray, and CLI entrypoints form one integration boundary
- Module moves that rely on `__file__`-relative assets need explicit path rebasing; `filescout.png` had to move from `Path(__file__).parent` logic to a repo-root lookup from `ui/main_window.py`
- For large mechanical UI extractions, source-driven scripted moves followed immediately by compile/import verification are safer than manual copy/paste edits
- A final stabilization pass after all extractions catches dead imports that accumulated across phases — each phase leaves behind imports its code no longer needs
- Entry-point wrappers with spaces in the filename can't be imported as Python modules — re-exports from them are dead code and should be stripped
- Run both `py_compile` (syntax) AND runtime import checks (resolution) — `py_compile` alone won't catch missing modules
- `setdefault` env vars in both the wrapper and the target module is harmless redundancy — the entry point wins, the target is a no-op
- When cleaning imports, verify usage with targeted grep before removing — some stdlib modules (e.g. `hashlib`, `mimetypes`) are easy to miss in a large UI file
- Zoom scaling requires a QScrollArea around panels with many group boxes — without it Qt compresses widgets vertically instead of allowing scroll. Also, all stylesheet pixel values (padding, margin, indicator sizes) must scale with zoom_factor; fixed pixel constants cause squishing at high zoom
