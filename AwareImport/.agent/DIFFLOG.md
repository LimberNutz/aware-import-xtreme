# Update Discipline Rules

For every future patch:

1. Update DIFFLOG.md with:
   - Intent
   - Files modified
   - Behavior changes
   - Data model changes
   - UI changes
   - New invariants introduced

2. Update STATE.md if:
   - User-visible behavior changed
   - Architecture changed

3. Update CONTRACTS.md if:
   - New non-negotiable logic introduced
   - Row inclusion rules modified
   - Column mappings altered
   - Export schema changed

4. Never modify these three files silently.

---

# Diff Log

## Entry: Initial Snapshot Baseline
**Date:** 2026-02-15

### Files Analyzed
- `main.py`
- `app/` (config, constants)
- `models/` (cml_row)
- `services/` (parser, transformer, aggregator, exporter, writer, worker, thickness_activity)
- `ui/` (main_window, panels, dialogs)
- `utils/` (helpers)

### Architecture Summary
- **MVC Pattern:** Strict separation of UI (`ui/`), Data (`models/`), and Business Logic (`services/`).
- **Dual Mode:** 
  - **CML Import:** Aggregated multi-file view with 39-col CSV export.
  - **Thickness Activity:** Single-file historical view (A:S) with write-back.
- **Async Processing:** `QThread` workers for parsing and scanning to keep UI responsive.

### Governance Layer Established
- `STATE.md`: Captures the current system snapshot.
- `CONTRACTS.md`: Defines non-negotiable behavioral rules (parsing, mapping, export).
- `DIFFLOG.md`: Established continuous update discipline.

### Changes
- **No functional code changes made.** This entry represents the creation of the `.agent` folder and governance documentation.

---

## Entry: Align Thickness Activity with Rules 3.5 / 3.6
**Date:** 2026-02-15

### Intent
Eliminate the duplicate Excel parsing path in `thickness_activity.py`. TA must derive its dataset from the canonical `excel_parser` output (`CMLRow`), not from a second independent `openpyxl` read.

### Files Modified
- `services/thickness_activity.py` — Rewrote entirely. Removed all `openpyxl` / direct Excel I/O. New public function `build_thickness_activity_view(rows: list[CMLRow])` accepts pre-parsed canonical rows and returns TA dicts. Material defaults applied locally without mutating source CMLRow objects.
- `ui/main_window.py` — Replaced `build_thickness_activity(file_path)` call with `parse_excel_file` (canonical parser) + `build_thickness_activity_view`. Added `_ta_parse_cache` dict for per-file parse result caching. Cache invalidated on write-back and clear.
- `.agent/STATE.md` — Updated Data Flow Summary to reflect TA derivation from canonical parse.

### Behavior Changes
- **None user-visible.** TA preview displays identical rows/values. DATA ERROR validation unchanged. Write-back unchanged. CSV export unchanged.

### Data Model Changes
- `thickness_activity.py` no longer owns any parsing logic. It is now a pure mapping/filter layer over `CMLRow`.
- `inspected_by` is stored on each `CMLRow` by `excel_parser` (was already present).

### New Invariants
- **Rule 3.5 enforced:** `CMLRow` is the sole canonical parsed model.
- **Rule 3.6 enforced:** TA dataset is a computed view; no independent parsing path exists.

---

## Entry: Search / Add Files UX Improvements
**Date:** 2026-02-15

### Intent
Improve file acquisition dialogs: persist folder selection across sessions, fix layout order in Search dialog, and make "Add Selected" respect actual row selection.

### Files Modified
- `ui/dialogs.py` — Added `_load_search_folder` / `_save_search_folder` QSettings helpers. `FuzzyMatchDialog` and `SearchDialog` both restore and save the last-used search folder. Swapped SearchDialog layout so Search Folder is first, Keyword second. Fixed `_accept_results` to only add selected rows (shows info message if none selected instead of silently adding all).
- `ui/main_window.py` — `_on_add_files` and `_on_add_folder` now persist their last-used directory via QSettings keys `add_files_folder` and `add_folder_folder`.

### Behavior Changes
- **Folder persistence:** All file/folder picker dialogs now remember their last-used directory between sessions.
- **Search dialog layout:** Search Folder field is now above the Keyword field (was reversed).
- **Add Selected:** No longer adds all results when nothing is selected; prompts user to select files first.

### UI Changes
- SearchDialog field order: Search Folder (top) → Keyword (second).
- "Add Selected" button requires explicit row selection.

### New Invariants
- All folder-picker dialogs use `QSettings("CMLBatchBuilder", "AwareImport")` for persistence, consistent with existing `system_path` persistence in `controls_bar.py`.

---

## Entry: Fix Material Defaults for Straight Pipe Variants
**Date:** 2026-02-15

### Intent
Components like "Straight Pipe-Bleeder" and "Straight Pipe-Vent" were incorrectly getting A234/WPB defaults instead of A106/B because the match was exact (`== "straight pipe"`) rather than prefix-based.

### Files Modified
- `services/transformer.py` — Changed `== "straight pipe"` to `.startswith("straight pipe")`.
- `services/thickness_activity.py` — Same fix in the TA view builder's local material defaults logic.
- `.agent/CONTRACTS.md` — Updated Rule 5.4 to specify prefix-match semantics.

### Behavior Changes
- All "Straight Pipe*" variants now correctly receive A106/B defaults (was A234/WPB for anything other than exact "Straight Pipe").

### New Invariants
- **Rule 5.4 (updated):** Material defaults use prefix match (`startswith`) for "Straight Pipe", not exact match.

---

## Entry: Carbon/Stainless Material Defaults from UT Sheet Selector
**Date:** 2026-02-15

### Intent
Support Stainless vs Carbon piping material defaults based on the UT sheet material selector dropdown in cell D4 (merged D4:F4). Material type flows from parser → CMLRow → transformer → both modes.

### Files Modified
- `models/cml_row.py` — Added `material_type: str = "Carbon"` field to CMLRow.
- `services/excel_parser.py` — Added `_extract_material_type(sheet)` to read D4, normalize to "Carbon"/"Stainless", pass to each CMLRow.
- `app/constants.py` — Restructured `MATERIAL_DEFAULTS` from flat dict to nested `{material_type: {component_key: {mat_spec, mat_grade}}}`.
- `services/transformer.py` — `_apply_material_defaults` now reads `row.material_type` and selects the correct defaults table.
- `services/thickness_activity.py` — **Removed** duplicate material defaults logic. TA now reads `mat_spec`/`mat_grade` directly from CMLRow (already set by transformer).
- `ui/main_window.py` — TA path now runs `transform_rows` on parsed rows before building TA view, ensuring material defaults are applied.
- `.agent/CONTRACTS.md` — Updated Rule 5.4 with full Carbon/Stainless tables. Added Rules 5.8–5.10 for extraction, single-source-of-truth, and mode parity.

### Data Model Changes
- `CMLRow.material_type` added (default "Carbon"). No CSV schema change — field is metadata only.
- `MATERIAL_DEFAULTS` structure changed from flat to nested by material type.

### Behavior Changes
- **Stainless sheets:** Straight Pipe → A312/TP304L, others → A403/WP304L.
- **Carbon sheets:** Straight Pipe → A106/B, others → A234/WPB (unchanged).
- Both modes display identical defaults for the same row.

### New Invariants
- **Rule 5.8:** Material type extracted from D4 during parsing, stored on CMLRow.
- **Rule 5.9:** Material defaults applied exclusively by transformer. No other module may contain this logic.
- **Rule 5.10:** CML Import and TA must display identical defaults (guaranteed by single transformer path).

### No Schema Changes
- CSV export headers unchanged (39 columns).
- TA view columns unchanged (19 columns).
- Write-back mapping unchanged.

---

## Entry: Baseline Inspection Threshold Flagging (87.5% Rule)
**Date:** 2026-02-15

### Intent
Flag TA rows where `UT Reading < Nom. × 0.875` with a light amber row highlight for engineering review. Suppressed if Inspection Notes is non-blank. Preview-only — no data mutation.

### Files Modified
- `ui/preview_panel.py` — Added `_BASELINE_THRESHOLD_FACTOR`, `_FLAG_BG_COLOR`, `_is_row_flagged()` function. `ThicknessActivityModel` now maintains `_flagged_rows` set, recomputed on `set_rows()` and on edits to Nom./UT Reading/Inspection Notes. `data()` returns amber `BackgroundRole` and descriptive `ToolTipRole` for flagged rows. `set_thickness_data` surfaces flagged count in summary label.
- `.agent/CONTRACTS.md` — Added Rules 5.11–5.15 (baseline threshold, notes override, edge cases, preview-only, dynamic recompute).

### Behavior Changes
- **New:** Rows in TA preview with UT reading below 87.5% of nominal (and no inspection notes) show light amber background highlight and tooltip.
- **Summary label** now shows "Flagged: N" count when flags are present.
- No popups, no blocking, no data changes.

### No Schema Changes
- CSV export unchanged.
- TA column layout unchanged.
- Write-back unchanged.
- Stored data not modified.

---

## Entry: Smart Column Resize + Text Elide
**Date:** 2026-02-15

### Files Modified
- `ui/preview_panel.py` — Removed `header.setStretchLastSection(True)`. Added `setWordWrap(False)` and `setTextElideMode(Qt.ElideRight)`. Added `_resize_columns_smart()` method (auto-fits all columns to content except "Inspection Notes", 350px cap). Called at end of `set_data()` and `set_thickness_data()`.

---

## Entry: Delegate BackgroundRole Paint Fix
**Date:** 2026-02-15

### Intent
Fix amber row highlighting not rendering due to QSS stylesheet overriding `Qt.BackgroundRole`.

### Files Modified
- `ui/preview_panel.py` — Added `paint()` override to `PreviewDelegate` that calls `painter.fillRect()` with the model's `BackgroundRole` color AFTER `super().paint()`, overlaying the amber tint on top of QSS-painted backgrounds. Removed broken `initStyleOption` override that used non-existent PySide6 `HasDecoration` attribute.

---

## Entry: Inspection Notes Header Detection Fix
**Date:** 2026-02-15

### Intent
Fix Inspection Notes column not populating when Excel header says "Comments" instead of "Inspection Notes" or "Notes".

### Files Modified
- `services/excel_parser.py` — Added `"comments": "inspection_notes"` to the `header_to_field` mapping in `_detect_columns()`.

---

## Entry: Update Sheets Cell Count Fix
**Date:** 2026-02-15

### Intent
Fix "Updated 0 cell(s)" message showing wrong count after writing changes back.

### Root Cause
`model.changed_cells()` returned a reference to the internal set. `model.clear_changes()` emptied it before the count was displayed.

### Files Modified
- `ui/main_window.py` — Changed `changed = model.changed_cells()` to `changed = set(model.changed_cells())` to copy the set before clearing.

---

## Entry: Batch Search + Filename Filter in SearchDialog
**Date:** 2026-02-16

### Intent
Allow pasting a list of entity names from Excel into the Search dialog and filtering results to only UT files (or any other type).

### Files Modified
- `services/file_discovery.py` — Added `batch_search_files(keywords, root_folder, name_filter)`. Also added `name_filter` parameter to `search_files_by_keyword()`. Both skip files whose filename doesn't contain the filter term.
- `ui/dialogs.py` — `SearchDialog`: replaced `QLineEdit` keyword input with `QTextEdit` for multi-line paste. Auto-detects batch mode when >1 line. Added "Filename must also contain" filter field (defaults to "UT"). Results table now 3 columns (Matched Term, Filename, Path). Added orange unmatched-names label. Added "Add All" button alongside "Add Selected".

### Behavior Changes
- **New:** Paste a list of entity names → batch substring search on filenames.
- **New:** Filename filter (default "UT") excludes VT, MT, CAD, etc.
- **New:** Unmatched names shown in orange summary.
- **New:** "Add All" button for quick accept.
- Single-keyword mode unchanged (backward compatible).
