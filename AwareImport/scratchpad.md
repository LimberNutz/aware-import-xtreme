# AwareImport — Bug Fix Plan

## Lessons
- Info Page Builder uses workbook-first extraction with PDF fallback, and requires `pypdf` at runtime.
- P&ID numbers can be normalized with a manual `P&ID Prefix` setting saved in app settings and sessions.
- Avoid running `resizeColumnToContents()` from `resizeEvent`; it makes window resizing noticeably laggy.
- For launch-time preview sizing, fitting visible columns to the viewport is better than content-based auto-resize; hide `System Path` by default in Info Page Builder so the rest of the columns fit.
- The accepted Aware export header is `CML Locations.T-Min` with no trailing space; do not re-add a trailing space there.
- The search dialog filename filter should treat comma-separated terms as separate OR matches, e.g. `UT, DR`.
- `system_path` is baked into CMLRow/EntityInfoRow at parse time; always re-apply the current UI value before CSV export so stale paths from previous projects don't leak into output.
- Added exact word matching option to search functionality using regex word boundaries to prevent partial matches like "DR" matching "Drain".
- PDF selection for Info Page Builder must strongly prefer CAD PDFs (+20 score for "cad"/"model" in filename) over API sketch PDFs. API sketches contain boilerplate "B31.3 or B31.4 or B31.8 (circle)" text that causes false matches. CAD title blocks have a clean "DESIGN CODE B31.3" field. pypdf garbles sketch PDF text (no spaces, missing characters), so regex stripping is unreliable. Use "(CIRCLE)" as a sentinel — if present, skip all B31 substring extraction and fall through to material-type-based default.
- CML Status defaults to "Active" but must be overridden to "Inactive" when ut_reading is empty (in _apply_defaults after setting the default).
- Ctrl+Scroll zoom: stylesheet in main.py uses build_stylesheet(zoom) to scale all px values. MainWindow.wheelEvent checks Ctrl modifier. Ctrl+0 resets. Range 50%-250%.

## Current Task: Align Rows header in file list

The `Rows` column header in the file list should align left so it visually matches the returned row-count values.

- [x] Locate the file list model and header rendering logic
- [x] Update the `Rows` header alignment to left

## Completed Task: Enhance snapshot.py comprehensiveness

Improved `tools/blueprint/snapshot.py` to expose more project-rehydration context without Git state:

- [x] Added architecture pattern detection
- [x] Added key classes / public API surface summary
- [x] Added configuration and QSettings pattern detection
- [x] Added external integration / file I/O pattern detection
- [x] Added import-based data flow hints
- [x] Added documentation index with short summaries
- [x] Added synthesized "How this app works" section (6-8 bullets)
- [x] Regenerated snapshots and verified improvements

New snapshots: `architecture.txt`, `api_surface.txt`, `config_patterns.txt`, `integrations.txt`, `data_flow.txt`, `docs_index.txt`, `how_it_works.txt`

## Current Task: API-570 Traveler Spreadsheet Integration

Upload an API-570 Traveler spreadsheet to pre-populate P&ID, Class, and Description fields
in the Info Page Builder. The traveler is the **primary trusted source** with the following
priority chain: Traveler → UT Sheet (workbook) → PDF → Defaults.

**Traveler tab layout** ("API-570 Traveler" sheet, headers in row 6, data from row 7):
Columns detected by **header name** (case-insensitive) — not by position — so inserted/reordered columns are tolerated.
- ENTITY → lookup key (matched case-insensitively to `system_name`)
- SERVICE → ignored (not mapped to `process_service` for now)
- DESCRIPTION → `equipment_description`
- P&ID → `pid_number` (left as-is, P&ID prefix still applies)
- CLASS → `class_name`
- TECH / UTDATE → if "N/A", entity has no UT sheet
- DR BY / DR DATE → if both populated, entity has a DR Thickness sheet

Some traveler cell values are formula-computed — we use `data_only=True` to read resolved values.

- [x] Create `services/traveler_parser.py` — header-based column detection, returns dict keyed by entity name
- [x] Add UT/DR sheet detection from TECH/UTDATE/DR BY/DR DATE columns
- [x] Drag-and-drop support — files with "API-570 Traveler" sheet auto-load as traveler
- [x] Modify `services/entity_info.py` — accept `traveler_data` param, apply as first `_set_field` calls
- [x] Modify `ui/controls_bar.py` — add "Load Traveler" button (teal), filename label, × clear button
- [x] Modify `ui/main_window.py` — wire load/clear/session, pass `traveler_data` to `build_entity_info_rows`
- [x] Modify `services/session.py` — persist `traveler_path` in sessions
- [x] Warn about unmatched traveler entities (entities in traveler not found in parsed UT sheets)
- [x] Syntax and import verification passed

## Previous Task: Add optional Inspection Frequency CSV export

- [x] Add "Export Inspection Frequency CSV" checkbox to ControlsBar (row 1, after Deadleg)
- [x] Add getter `is_insp_freq_export()` and QSettings persistence
- [x] Create `build_inspection_freq_rows()` in csv_exporter.py (Class 1-3 mapping, Class 4 skipped with warning)
- [x] Create `export_inspection_freq_csv()` in csv_exporter.py (writes 4-column CSV)
- [x] Hook into `_do_export` in MainWindow — generates second CSV in same output dir if checkbox enabled
- [x] Add `_build_insp_freq_path()` helper — pattern: Equip_InspFreq_Import_YYYY-MM-DD.csv
- [x] Syntax verification passed

## Previous Task: Add exact word matching option to search functionality

- [x] Added "Exact word match" checkbox to SearchDialog
- [x] Updated search functions to support exact_match parameter
- [x] Implemented regex-based whole word matching using word boundaries
- [x] Updated both single keyword and batch search modes

## Current Task: Improve file search keyword filtering

- [x] Locate the search dialog and filename filter logic
- [x] Add comma-separated filename filter support for single and batch search
- [x] Run validation and summarize the behavior change

## Current Task: Add Info Page Builder mode

- [x] Define entity-level info model and export merge path
- [x] Add a third preview mode and an explicit Build Info Pages action
- [x] Implement workbook-first extraction with PDF fallback and flagging
- [x] Finish validation and polish any extraction edge cases

## Current Task: Add configurable P&ID prefix

- [x] Add a persistent P&ID prefix field in the controls bar
- [x] Apply the prefix during entity info build without double-prefixing full page numbers
- [x] Save and restore the prefix with sessions

## Current Task: Fix all 7 bugs from code review

Each fix below includes the exact file, the exact old code to find, and the exact new code to replace it with. All fixes are independent and can be applied in any order.

---

### Fix 1 & 2 (HIGH): Undo / clear-cells / context-menu must be mode-aware
**File:** `ui/preview_panel.py`

The `_undo`, `_clear_selected_cells`, and `_show_copy_menu` methods always reference `self.model` (CML Import). They must check `self._current_mode` and use `self.ta_model` when in Thickness Activity mode.

**Add a helper method** right after `_setup_ui` (before `set_data`):

```python
    def _active_model(self):
        """Return the model currently driving the table."""
        if self._current_mode == "Thickness Activity":
            return self.ta_model
        return self.model
```

**Then apply 4 edits:**

**Edit 1a** — `_show_copy_menu`: change `self.model.can_undo()` to `self._active_model().can_undo()`

OLD:
```python
        undo_action.setEnabled(self.model.can_undo())
```
NEW:
```python
        undo_action.setEnabled(self._active_model().can_undo())
```

**Edit 1b** — `_undo`: change `self.model.undo()` to `self._active_model().undo()`

OLD:
```python
    def _undo(self):
        self.model.undo()
```
NEW:
```python
    def _undo(self):
        self._active_model().undo()
```

**Edit 1c** — `_clear_selected_cells`: use active model's editable columns and setData

OLD:
```python
    def _clear_selected_cells(self):
        selection = self.table.selectionModel().selectedIndexes()
        if not selection:
            return
        for idx in selection:
            if idx.column() in self.model.FIELD_MAP:
                self.model.setData(idx, "", Qt.EditRole)
```
NEW:
```python
    def _clear_selected_cells(self):
        selection = self.table.selectionModel().selectedIndexes()
        if not selection:
            return
        active = self._active_model()
        editable = active.FIELD_MAP if hasattr(active, 'FIELD_MAP') else active.EDITABLE_COLS
        for idx in selection:
            if idx.column() in editable:
                active.setData(idx, "", Qt.EditRole)
```

**Status:** [x] Done

---

### Fix 8 (HIGH): Worker discards rows when parse returns both rows AND errors
**File:** `services/worker.py`

The `if errors:` branch skips rows entirely. It should only skip rows if there are ZERO rows returned (i.e., a real failure).

OLD (lines 49-67):
```python
            if errors:
                all_errors.extend([f"[{entry.filename}] {e}" for e in errors])
                self.file_done.emit(entry.file_path, 0, "; ".join(errors), "")
            else:
```
NEW:
```python
            if errors and not rows:
                all_errors.extend([f"[{entry.filename}] {e}" for e in errors])
                self.file_done.emit(entry.file_path, 0, "; ".join(errors), "")
            else:
                if errors:
                    all_errors.extend([f"[{entry.filename}] {e}" for e in errors])
```

Note: the indented block after `else:` (lines 53-67) stays exactly the same.

**Status:** [x] Done

---

### Fix 9 (MEDIUM): `je` default unconditionally overwrites user/sheet values
**File:** `services/transformer.py`

OLD (line 65):
```python
    row.je = DEFAULTS["je"]  # always 1.0 for piping
```
NEW:
```python
    if not row.je:
        row.je = DEFAULTS["je"]
```

**Status:** [x] Done

---

### Fix 6 (MEDIUM): Cache invalidation has dead variable and redundant loop
**File:** `ui/main_window.py`

OLD (lines 285-289):
```python
            for fname in affected_files:
                for cached_path in list(self._ta_parse_cache.keys()):
                    if os.path.basename(cached_path) in affected_files:
                        self._ta_parse_cache.pop(cached_path, None)
```
NEW:
```python
            for cached_path in list(self._ta_parse_cache.keys()):
                if os.path.basename(cached_path) in affected_files:
                    self._ta_parse_cache.pop(cached_path, None)
```

**Status:** [x] Done

---

### Fix 5 (LOW): Add column S (index 18) for `inspected_by` to PIPING_COLUMN_MAP
**File:** `app/constants.py`

OLD (lines 94-96):
```python
    17: "nde",               # R
    19: "ut_reading",        # T
```
NEW:
```python
    17: "nde",               # R
    18: "inspected_by",      # S
    19: "ut_reading",        # T
```

Also add "inspected by" to the auto-detect header mapping in `services/excel_parser.py`.

In the `header_to_field` dict inside `_detect_columns`, add after the "comments" entry:

OLD:
```python
            "comments": "inspection_notes",
        }
```
NEW:
```python
            "comments": "inspection_notes",
            "inspected by": "inspected_by",
            "technician": "inspected_by",
            "inspector": "inspected_by",
        }
```

Also update `_PREVIEW_COL_TO_FIELD` in `services/excel_writer.py` to include index 18:

OLD:
```python
    15: "install_date", 16: "status", 17: "nde",
}
```
NEW:
```python
    15: "install_date", 16: "status", 17: "nde", 18: "inspected_by",
}
```

**Status:** [x] Done

---

### Fix 10 (LOW): Add .gitignore and remove __pycache__ from tracking
**File:** `.gitignore` (new file at project root)

Create `C:\Users\cherr\Desktop\Codes\AwareImport\.gitignore` with:
```
__pycache__/
*.pyc
*.pyo
*.egg-info/
dist/
build/
*.spec
.env
*.db
```

Then run:
```bash
git rm -r --cached __pycache__ app/__pycache__ models/__pycache__ services/__pycache__ ui/__pycache__ utils/__pycache__
git add .gitignore
git commit -m "Add .gitignore, remove __pycache__ from tracking"
```

**Status:** [x] Done

---

### Fix 3 (LOW): Lambda closures in context menu capture by reference
**File:** `ui/file_list_panel.py`

Change all lambdas in `_show_context_menu` to use default-argument capture.

OLD:
```python
            open_file_action.triggered.connect(lambda: self._open_file(entry.file_path))
```
NEW:
```python
            open_file_action.triggered.connect(lambda _=None, p=entry.file_path: self._open_file(p))
```

Apply the same pattern to ALL lambdas in the method:
- `lambda: self._open_file(entry.file_path)` → `lambda _=None, p=entry.file_path: self._open_file(p)`
- `lambda: self._open_folder(entry.file_path)` → `lambda _=None, p=entry.file_path: self._open_folder(p)`
- `lambda: self._copy_to_clipboard(entry.file_path)` → `lambda _=None, p=entry.file_path: self._copy_to_clipboard(p)`
- `lambda: self._copy_to_clipboard(entry.filename)` → `lambda _=None, n=entry.filename: self._copy_to_clipboard(n)`
- `lambda: self._rename_file(row_idx)` → `lambda _=None, r=row_idx: self._rename_file(r)`
- `lambda: self._move_file(row_idx)` → `lambda _=None, r=row_idx: self._move_file(r)`
- `lambda: self._copy_file(row_idx)` → `lambda _=None, r=row_idx: self._copy_file(r)`
- `lambda: self._remove_from_list(indices)` → `lambda _=None, idx=indices: self._remove_from_list(idx)`
- `lambda: self._delete_files(indices)` → `lambda _=None, idx=indices: self._delete_files(idx)`

**Status:** [x] Done

---

## Progress
- [x] Fix 1 & 2
- [x] Fix 8
- [x] Fix 9
- [x] Fix 6
- [x] Fix 5
- [x] Fix 10
- [x] Fix 3

## Current Task: Add Deadleg checkbox toggle

- [x] Add "Deadleg" checkbox to ControlsBar (row 1, between CML style and P&ID prefix)
- [x] Add `deadleg_changed` signal, `is_deadleg()` getter, persistence via QSettings
- [x] Add `_on_deadleg_changed`, `_apply_deadleg`, `_apply_deadleg_entity` in MainWindow
- [x] Apply suffix on toggle (append/strip " Deadleg" to system_name, equipment_id, system_path)
- [x] Apply suffix after `_on_finished` (validate) and `_build_info_pages_from_rows`
- [x] Save/restore deadleg state in session (session.py + main_window restore)
- [x] Invalidate TA cache on toggle since system_name changes
- [x] Import verified OK

## Previous Task: Add column header sorting to all three table modes

- [x] Add `SortFilterProxy(QSortFilterProxyModel)` with numeric-aware `lessThan`
- [x] Wire proxy in `_setup_ui`: table shows proxy, sorting enabled, dynamic sort off
- [x] `set_mode` swaps `_sort_proxy.setSourceModel()` instead of `table.setModel()`; resets sort indicator on mode switch
- [x] Fix `_clear_selected_cells` — map proxy indexes to source via `mapToSource`
- [x] Fix `_paste_selection` — use `proxy.setData()` / `proxy.index()` for all view-facing operations
- [x] Fix `_copy_all_rows` — iterate proxy for sorted output order
- [x] Fix `FindReplaceDialog._do_find` and `_replace` — use proxy for index creation, data reads, setData
- [x] `_replace_all` left unchanged (iterates source model directly, no view interaction)
- [x] Import verified OK

## Previous Task: Info Page Builder improvements

### Issue 1: Year Built → InService Date transposition bug
- [x] Fixed in `preview_panel.py` EntityInfoModel.setData() — uses value directly if "/" present
- [x] Fixed in `preview_panel.py` EntityInfoModel.undo()
- [x] Fixed in `entity_info.py` _build_entity_row()

### Issue 2: Write-back for Info Page Builder
- [x] Created `write_back_entity_changes()` in excel_writer.py (writes equipment_description, pid_number to header)
- [x] Updated _on_update_sheets in main_window.py to route Info Page Builder to new function
- [x] INFO messages for non-writable fields (year_built, class_name, etc.)

### Issue 3: System Name in file list — confirmed program-only
- [x] Verified: FileListModel.setData() only updates in-memory entry.system_name
