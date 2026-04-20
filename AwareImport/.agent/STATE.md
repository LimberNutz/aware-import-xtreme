# Project Snapshot (Initial Baseline)

## 1. Architecture Overview
- **Pattern:** MVC-style with dedicated Service Layer.
- **Entry Point:** `main.py` -> `ui.main_window.MainWindow`.
- **Threading:** Heavy operations (parsing, scanning) run in `QThread` workers (`services.worker`).
- **Data Flow:**
  1. **Ingestion:** File/Folder drag-and-drop -> `FileDiscovery` -> `FileListModel`.
  2. **Parsing:** `ParseWorker` -> `excel_parser` -> `CMLRow` objects.
  3. **Transformation:** `transformer` applies defaults (e.g., Material) and formatting.
  4. **Aggregation:** `aggregator` dedupes rows by (SystemPath, SystemName, CML).
  5. **Presentation:** `PreviewPanel` displays data via `PreviewTableModel` (CML Import) or `ThicknessActivityModel` (TA).
  6. **Export:** `csv_exporter` (to CSV) or `excel_writer` (write-back to Excel).

### Ownership Map
- `excel_parser.py` = source-of-truth parsing
- `transformer.py` = default injection layer
- `aggregator.py` = deduplication layer
- `thickness_activity.py` = derived view layer
- `csv_exporter.py` = export layer
- `excel_writer.py` = persistence layer

## 2. Functional Capabilities (Current)
- **File Ingestion:** Drag-and-drop, recursive folder scan, fuzzy matching, keyword search.
- **Parsing:** Auto-detects "Piping" sheets, scores headers, extracts system/technician names.
- **CML Import Mode:**
  - Aggregates multiple files.
  - Validates rows (CML, OD, Nom required).
  - Exports strict 39-column CSV for IDMS.
- **Thickness Activity Mode:**
  - Single-file view.
  - Displays 19-column "Data Team Historicals" format (A:S).
  - Includes rows with non-blank Column B.
  - **Editable:** Supports write-back to source Excel (A-L, T, U).
- **Export/Write-back:**
  - CSV Export: "Equip_CML_Import.csv" (CML Import only).
  - Update Sheets: Writes changes in Preview grid back to source .xlsx files.

## 3. Data Flow Summary
- **CML Import:** Excel -> `excel_parser` -> `CMLRow` -> `transformer` -> `aggregator` -> `PreviewTableModel`.
- **Thickness Activity:** Excel -> `excel_parser` -> `CMLRow` (cached per-file) -> `thickness_activity.build_thickness_activity_view` -> `dict` -> `ThicknessActivityModel`.
- **Preview Edit** -> `undo_stack` -> `excel_writer` -> **Source Excel**.
- **Key:** Both modes use `excel_parser` as the single canonical parsing path. TA applies only material defaults (not full transformer). Per-file parse results are cached in `MainWindow._ta_parse_cache`; cache is invalidated on write-back and clear.

## 4. Current Invariants (Short Summary)
- **CML Import:** Row valid only if CML, OD, Nom present.
- **Thickness Activity:** Row included if Column B non-blank.
- **Material Defaults:** If blank, "Straight Pipe" -> A106/B, else A234/WPB.
- **Write-back:** Only mapped columns can be written; derived columns (e.g., formulas) ignored.

## 5. Known Limitations
- **Memory:** Loads all parsed rows into memory; may struggle with extremely large datasets (100k+ rows).
- **Excel Dependencies:** Relies on `openpyxl` `data_only=True`; formulas are lost in read (but preserved in write-back if not overwritten).
- **Concurrency:** Write-back is synchronous and blocking.
