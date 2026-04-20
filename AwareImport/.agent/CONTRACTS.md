# Behavioral Contracts

This file defines the non-negotiable rules for the AwareImport application.
Any deviation from these rules constitutes a regression.

## 1. Parsing Contracts

### Row Inclusion (Piping)
- **Rule 1.1:** A row is considered a valid "Thickness Activity" row if and only if **Column B (CML Location)** is non-blank.
- **Rule 1.2:** The dataset ends at the last row where **Column B** is non-blank.
- **Rule 1.3:** Columns A, C, G, M, Q (or any other static data column) must **NEVER** be used to determine row inclusion.
- **Rule 1.4:** If **Column T (UT Reading)** is present but **Column B** is blank, this is a **DATA ERROR** and must be flagged, but the row itself is skipped in the dataset.
- **Rule 1.7:** **DATA ERROR** rows must be surfaced via UI validation indicator (status bar or message box) but must **NOT** appear in the Thickness Activity grid dataset.

### Header Detection
- **Rule 1.5:** The parser must auto-detect the header row by scoring rows against `EXPECTED_HEADERS`.
- **Rule 1.6:** If multiple "OD" columns exist, only the **first** occurrence (leftmost) is mapped.

## 2. Column Mapping Contracts

### Thickness Activity View (19 Columns)
The view must strictly follow this A:S layout:
- **A:** CML
- **B:** CML Location
- **C:** Component Type
- **D:** Component
- **E:** OD
- **F:** Nom.
- **G:** C.A.
- **H:** T-Min
- **I:** Mat. Spec.
- **J:** Mat. Grade
- **K:** Pressure
- **L:** Temp.
- **M-P:** (Blank placeholders)
- **Q:** UT Reading (Mapped from Excel Column T)
- **R:** Inspection Notes (Mapped from Excel Column U)
- **S:** Inspected By (Extracted from Header)

### CML Import Mapping
- Standard mapping applies (A-R, T, U).
- **Rule 2.1:** `System Name` must be extracted from the header area ("Circuit Name") or filename if missing.

## 3. Mode Separation Contracts

- **Rule 3.1:** **CML Import Mode** must always represent an **aggregated** dataset of all loaded files.
- **Rule 3.2:** **Thickness Activity Mode** must always represent a **single-file** view.
- **Rule 3.3:** Switching modes must **NOT** trigger a re-parse of the entire dataset; it should switch the active model in the `PreviewPanel`.
- **Rule 3.4:** Data mutations (edits) in one mode must be persisted to the source Excel file via "Update Sheets" to be visible in the other mode (after a reload).
- **Rule 3.5:** `CMLRow` is the canonical parsed model for the application.
- **Rule 3.6:** The Thickness Activity dataset must be a computed view derived from parsed rows and must **NOT** redefine source-of-truth parsing logic (except for view-specific formatting).

## 4. UI Contracts

- **Rule 4.1:** The **Export CSV** button must only be active or functional in **CML Import Mode**.
- **Rule 4.2:** The **Update Sheets** button must function in **both** modes, using the appropriate write-back logic for the active model.
- **Rule 4.3:** The Status Bar must reflect the row count of the **currently active** mode.

## 5. Export Contracts

### CSV Export (CML Import Only)
- **Rule 5.1:** The output CSV schema must match `AWARE_CSV_HEADERS` (39 columns) exactly.
- **Rule 5.2:** `SystemPath` must be constructed as `{Parent Path} > {System Name}`.
- **Rule 5.3:** `Joint Efficiency` (JE) must default to "1.0" for all piping rows.
- **Rule 5.4:** Material defaults depend on the UT sheet material selector (cell D4, merged D4:F4):
  - **Carbon:**
    - Component containing "Straight Pipe" (case-insensitive substring) → A106 / B
    - All others → A234 / WPB
  - **Stainless:**
    - Component containing "Straight Pipe" (case-insensitive substring) → A312 / TP304L
    - All others → A403 / WP304L
  - Defaults apply **only** when Mat Spec or Mat Grade is blank. Pre-filled values must not be overwritten.

### Material Type Extraction
- **Rule 5.8:** The material type must be extracted from cell D4 (merged D4:F4) of the UT sheet during parsing, normalized to "Carbon" or "Stainless", and stored as file-level metadata on each `CMLRow.material_type`. Default is "Carbon" if unrecognized or missing.
- **Rule 5.9:** Material defaults must be applied exclusively by the transformer layer (`services/transformer.py`). No other module (including `thickness_activity.py`) may contain material default logic.
- **Rule 5.10:** Both CML Import and Thickness Activity must display identical material defaults for the same source row. This is guaranteed by routing all rows through the single transformer.

### Baseline Inspection Threshold (Thickness Activity Only)
- **Rule 5.11:** If `UT Reading < Nom. × 0.875` and `Inspection Notes` is blank, the row must be visually flagged (light amber background) in the TA preview grid.
- **Rule 5.12:** If `Inspection Notes` is non-blank, the flag is suppressed (anomaly assumed documented).
- **Rule 5.13:** If `Nom.` is missing, zero, or non-numeric, or `UT Reading` is missing or non-numeric, do not flag. Fail silently.
- **Rule 5.14:** The flag is preview-only. It must NOT modify stored data, block any workflow, or appear in CSV export.
- **Rule 5.15:** The flag must recompute dynamically on data load and on edits to `Nom.`, `UT Reading`, or `Inspection Notes`.

### Search Dialog
- **Rule 5.16:** The Search dialog must support both single-keyword and multi-line batch paste modes. Batch mode activates automatically when >1 line is detected.
- **Rule 5.17:** The "Filename must also contain" filter (default "UT") must apply to both single-keyword and batch search modes, excluding files whose filename does not contain the filter term.
- **Rule 5.18:** Unmatched entity names in batch mode must be surfaced visually in the dialog (not silently dropped).

### Excel Write-Back
- **Rule 5.5:** Write-back must **NEVER** shift rows or columns. It must write to the exact `(source_row, source_col)` index.
- **Rule 5.6:** Only mapped columns are writable. Derived or placeholder columns (e.g., M-P in TA mode) are read-only/ignored.
- **Rule 5.7:** Any change to CSV column order, name, or count requires:
  1. A version increment.
  2. A `DIFFLOG.md` entry.
  3. An update to `STATE.md`.
