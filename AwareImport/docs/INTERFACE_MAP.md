# Interface Map

## Entry Points

| Type | Path | Invocation |
|------|------|-----------|
| GUI app | `main.py` | `python main.py` |

## Public Module Interfaces

### models/cml_row.py
- `CMLRow(BaseModel)` — canonical row model (20+ fields, Pydantic v2)
- `FileEntry(BaseModel)` — file list entry (file_path, status, row_count, etc.)

### services/excel_parser.py
- `parse_excel_file(file_path) → (list[CMLRow], str, list[str])` — main parser
- `extract_inspection_date(file_path) → str` — UT date from cell K1

### services/transformer.py
- `transform_rows(rows, system_path, standard_style) → list[CMLRow]`

### services/aggregator.py
- `aggregate_rows(rows) → list[CMLRow]` — dedup by (path, name, cml)

### services/csv_exporter.py
- `export_csv(rows, output_path) → (int, list[str])` — write Aware CSV

### services/excel_writer.py
- `write_back_changes(rows, changed_cells) → list[str]` — CML Import write-back
- `write_back_ta_changes(rows, changed_cells) → list[str]` — TA write-back

### services/thickness_activity.py
- `build_thickness_activity_view(rows) → (list[dict], list[str])`

### services/file_discovery.py
- `find_excel_files(root_folder) → list[str]`
- `fuzzy_match_files(entity_names, root_folder, threshold=60) → list[tuple]`
- `batch_search_files(keywords, root_folder, name_filter="") → (list[tuple], list[str])`
- `search_files_by_keyword(keyword, root_folder, search_content=False, name_filter="") → list[str]`

### services/session.py
- `save_session(path, *, entries, all_rows, all_errors, system_path, standard_style, current_mode)`
- `load_session(path) → dict`

### services/worker.py
- `ParseWorker(QThread)` — signals: progress, file_done, finished_all, cancelled
- `FolderScanWorker(QThread)` — signals: files_found, scan_done, cancelled

### utils/helpers.py
- `temp_open_workbook(file_path, **kwargs)` — context manager
- `format_cml_standard(cml_raw) → str`
- `format_cml_client(cml_raw) → str`
- `cml_suffix_value(cml) → int`
- `safe_str(value) → str`
- `is_numeric(value) → bool`
- `extract_system_name_from_filename(filename) → str`

### app/constants.py
- `AWARE_CSV_HEADERS` — 38-element list defining CSV column order
- `PIPING_COLUMN_MAP` — Excel col index → field name mapping
- `DEFAULTS` — default cell values
- `MATERIAL_DEFAULTS` — Carbon/Stainless material lookup
- `KNOWN_SHEET_NAMES`, `EXPECTED_HEADERS` — sheet detection
- `HEADER_ROW=5`, `DATA_START_ROW=6`, `MAX_BLANK_CML_RUN=10`
- `SUPPORTED_EXTENSIONS = {".xlsx", ".xlsm"}`

## UI Signal Map

### ControlsBar signals
| Signal | Trigger |
|--------|---------|
| `add_files_clicked` | Add Files button |
| `add_folder_clicked` | Add Folder button |
| `paste_entities_clicked` | Paste Entities button |
| `search_clicked` | Search button |
| `validate_clicked` | Validate button |
| `export_clicked` | Export CSV button |
| `update_sheets_clicked` | Update Sheets button |
| `clear_clicked` | Clear List button |
| `cancel_clicked` | Cancel button |
| `copy_table_clicked` | Copy Table button (TA mode) |
| `save_session_clicked` | Save Session button |
| `load_session_clicked` | Load Session button |
| `mode_changed(str)` | Mode combo change |

### FileListPanel signals
| Signal | Trigger |
|--------|---------|
| `files_changed` | File list modified |
| `folder_dropped(str)` | Folder dropped via drag-and-drop |
| `file_selected(str)` | Single file row selected |
