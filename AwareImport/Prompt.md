# ROLE

You are a senior Python engineer building a Windows desktop utility for an inspection data team. Produce production-quality code, not pseudocode. Prioritize correctness, resilience, and a clean UX. Keep the UI sleek and rely on right click context menus for file operations.

# PROJECT NAME

**CML Batch Builder (Aware CML Table Import CSV Generator)**

# PRIMARY OUTCOME

Create a single combined CML table import CSV from multiple individual UT Excel sheets (`.xlsx` / `.xlsm`) stored across many folders. The tool must also auto-populate common blank cells with configurable default values and enforce a selectable CML numbering style (standard `1.01` vs client-specific `1.1`).

# USER CONTEXT

- Files are UT thickness table spreadsheets for inspected equipment.
- The user currently imports UT into a working sheet (Excel macro workflow) then exports a CSV for import into Aware/IDMS.
- We want to eliminate the manual import step by reading UT sheets directly, aggregating rows, applying defaults/cleanup, and exporting the final CSV.

# REFERENCE ASSETS

- **Working macro workbook (reference only):** `Equip_CMLTable WORKING.xlsm`
- **Screenshot reference:** Shows the “Piping” tab table structure and column meanings.

---

# KEY FUNCTIONAL REQUIREMENTS

## 1) UI REQUIREMENTS (Windows Desktop)

Choose a modern desktop stack: **PySide6** (preferred) or **PyQt6**.

The UI must be clean and minimal:

- **Left side:** File list panel (`QListView` / `QTableView`) with drag and drop support.
- **Right side:** Preview panel showing aggregated rows (table preview) and validation messages.
- **Top area:** Inputs and toggles:
  - **System Path input (text box):** Example: `XCEL > Diversified > Buckeye > Unit > Piping > REFG-010`
  - **Optional:** Facility / client metadata fields if needed later, but do not overbuild now.
  - **CML numbering style checkbox:**
    - **Checked:** Standard style `1.01`, `1.02`, `2.01`, etc (always two digits after decimal)
    - **Unchecked:** Client style `1.1`, `1.2`, etc (variable digit style)
  - **Buttons:** “Export CSV”, “Validate” (or auto-validate), “Clear List”.

### File Acquisition Features:

- Drag and drop files into the list.
- Add files via file picker (multi-select).
- Add a parent folder and search recursively for candidate files.
- Paste a list of entity names (one per line) and fuzzy match to filenames within a chosen parent folder.
- Search for keywords or strings within filenames AND optionally inside Excel content to locate candidate UT sheets.

## 2) FILE LIST OPERATIONS

A right-click context menu on the file list is required. Provide:

- Open file / Open containing folder
- Copy full path / Copy filename
- Rename / Move to... / Copy to...
- Delete (send to recycle bin if feasible, otherwise confirm hard delete)
- Remove from list (does not delete)
- Sort (by name, folder, modified time)
- De-duplicate (same path)
- Refresh file existence status (missing files flagged)

> [!NOTE]
> UI should visually flag missing/unreadable files and continue processing others.

## 3) INPUT FILE DETECTION LOGIC

The app must detect UT sheet files containing thickness tables. Strategies:

- **Primary detection:** Known sheet/tab names like "Piping", "Vessels", "LWN SHEET" (do not hard fail if missing).
- **Secondary detection:** Scan worksheets for expected header cells such as:
  - "CML", "CML Location", "Component Type", "Component", "OD", "Nom.", "C.A.", "T-Min", "Mat. Spec.", "Grade", "Pressure", "Temp.", "J.E.", "Access", "Insulation", "Install Date", "Status", "NDE", "Prev. Reading", "UT Reading"
- If multiple matching tables exist, choose the best match using a scoring approach.

### Implementation Details:

- Support both `.xlsx` and `.xlsm`.
- Read values only; do not rely on Excel being installed.
- Use `openpyxl` for reading. For formula cells, use cached values.

## 4) DATA EXTRACTION MAPPING (Piping table baseline)

Assume the table begins at row 6 with headers on row 5.

**Expected Piping table columns (Excel):**
| Col | Field | Col | Field |
| :--- | :--- | :--- | :--- |
| **A** | CML | **K** | Pressure |
| **B** | CML Location | **L** | Temp. |
| **C** | Component Type | **M** | J.E. |
| **D** | Component | **N** | Access |
| **E** | OD | **O** | Insulation |
| **F** | Nom. | **P** | Install Date |
| **G** | C.A. | **Q** | Status |
| **H** | T-Min | **R** | NDE |
| **I** | Mat. Spec. | **S** | Prev. Reading |
| **J** | Mat. Grade | **T** | UT Reading |

**Stop conditions:**

- Stop after 10 consecutive blank CML cells OR end of sheet used range.
- Skip rows where CML, UT Reading, and Component are all blank.
- Keep rows where CML exists even if UT Reading is blank (but flag).

## 5) DEFAULTS AND CLEANUP

Implement defaulting rules matching current macro behavior:

### CML Formatting:

1. **Standard 1.01 style:** Normalize `1.1` to `1.01`, `2.4` to `2.04`.
2. **Client 1.1 style:** Keep as `1.1`, `1.2`. Reduce leading/trailing zeros if appropriate.

- **Validation:** If suffix > `05` (e.g., `1.06`), flag as warning.

### Material Defaults (when blank):

- If **Component** == "Straight Pipe": `Mat. Spec. = "A106"`, `Mat. Grade = "B"`.
- Else: `Mat. Spec. = "A234"`, `Mat. Grade = "WPB"`.
- Do not overwrite non-blank values.

### UT Reading Cleanup:

- Remove placeholders: `N/A`, `NA`, `N\A`, `N.A.`
- Remove dash-dot patterns: `--.---`, `---.---`, or strings containing only `-`, `.`, and spaces.

### Other Defaults:

- **J.E.:** 1.0 (if blank).
- **Status:** "Active".
- **NDE:** "UT".
- **C.A.:** 0.
- **Component Type:** "Piping".

## 6) SYSTEM PATH AND SYSTEM NAME

- **SystemPath:** Entered in UI and applied to all rows.
- **SystemName:** Derived from entity name for each file.
  - Parse from header cell (e.g., “Pipe Circuit Name”) or filename token (e.g., `REFG-010`).
  - Allow inline editing in UI.

## 7) OUTPUT CSV FORMAT

Generate a single CSV matching the Aware import schema.

**Required header order:**
`SystemPath`, `SystemName`, `SystemType`, `Equipment Type`, `Equipment ID`, `Manufacturer`, `Serial Number`, `National Board Number`, `Model Number`, `Year Built`, `Name Plate`, `U-1 Form`, `PSM Covered`, `Code Stamp`, `PID Drawing`, `PFD`, `PID Number`, `PFD Number`, `Shutdown Level`, `Criticality`, `Equipment Description`, `Code`, `CML Locations.CML`, `CML Locations.CML Location`, `CML Locations.Component Type`, `CML Locations.Component`, `CML Locations.Outside Diameter`, `CML Locations.Nominal Thickness`, `CML Locations.Corrosion Allowance`, `CML Locations.T-min`, `CML Locations.Material Spec`, `CML Locations.Material Grade`, `CML Locations.CML Pressure`, `CML Locations.CML Temperature`, `CML Location.CML Joint Efficiency`, `CML Locations.CML Access`, `CML Locations.Insulation`, `CML Locations.CML Installed On`, `CML Locations.CML Status`, `CML Locations.NDE Type`

## 8) AGGREGATION AND DEDUPLICATION

- De-duplicate using key: `(SystemPath, SystemName, CML)`.
- **Precedence:** 1. Non-blank UT Reading, 2. Most recently modified file.

## 9) VALIDATION + REPORTING

Show in UI:

- Counts: Files loaded/failed, Rows extracted/exported.
- Warnings: CML suffix > 05, Missing CML/OD/Nom, Non-numeric readings, Bad dates.

## 10) PERFORMANCE

- Handle hundreds of files using worker threads.
- Provide progress indicator and cancel button.

## 11) DELIVERABLES

- **Runnable Python application** with structured codebase (`/app`, `/ui`, `/services`, `/models`, `/utils`).
- **requirements.txt** and clear run instructions.

## 12) IMPLEMENTATION NOTES

- Use single-line comments only.
- Avoid Excel COM automation.
- Use type hints and pydantic/dataclasses.
- Non-fatal file parsing; continue on error.

# ACCEPTANCE CRITERIA

- Drag & Drop support.
- Entity name fuzzy matching.
- Right-click context menus.
- Correct parsing, cleaning, and normalization.
- Combined CSV export with correct headers.

# FIRST MILESTONE

1. UI skeleton (file list, context menu, controls).
2. File discovery (drag/drop, picker, recursive).
3. Excel parsing (header detection, row extraction).
4. Transformer (defaults, cleanup, formatting).
5. Preview & Validation panel.
6. CSV Exporter.
7. Fuzzy matching.
