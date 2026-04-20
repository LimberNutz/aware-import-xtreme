# Pre-Merge Verification Checklist

> Walk through this before declaring any change "done". Designed for both human and LLM review.

## Functional Correctness

- [ ] The change does what the request asked for — no more, no less
- [ ] No unrelated files were modified
- [ ] No placeholder / TODO code left behind (unless explicitly deferred)
- [ ] Edge cases considered (empty inputs, missing files, malformed data)

## Contract Preservation

- [ ] Public function signatures unchanged (or intentionally updated + documented)
- [ ] `CMLRow` fields unchanged (or change reflected in all consumers)
- [ ] CSV export headers unchanged (or `AWARE_CSV_HEADERS` + `_map_row_to_csv` updated together)
- [ ] Column mappings consistent: `PIPING_COLUMN_MAP` ↔ `_FIELD_TO_COL` ↔ `_TA_COL_TO_EXCEL`
- [ ] Session schema unchanged (or `SESSION_VERSION` bumped)
- [ ] Qt signal/slot connections not broken

## Data Safety

- [ ] No secrets, credentials, or PII in committed files
- [ ] No hardcoded file paths that only work on one machine
- [ ] Write-back operations still target correct Excel cells
- [ ] temp_open_workbook pattern preserved (no file-locking regressions)

## Consistency

- [ ] Import statements sorted and correct
- [ ] No circular imports introduced
- [ ] No dead code or unused imports added
- [ ] Naming follows existing conventions (snake_case functions, PascalCase classes)

## Documentation

- [ ] `docs/00_BLUEPRINT.md` still accurate (update if architecture changed)
- [ ] `docs/INTERFACE_MAP.md` still accurate (update if interfaces changed)
- [ ] `docs/SAFE_CHANGELOG.md` checklist still valid
- [ ] Snapshots regenerated: `python tools/blueprint/snapshot.py`

## Manual Smoke Test (if no automated tests)

- [ ] App launches: `python main.py`
- [ ] Can add files to the list (drag-drop or Add Files button)
- [ ] Validate produces rows in the preview table
- [ ] Export CSV writes a valid file
- [ ] Mode switch between CML Import and Thickness Activity works
- [ ] (Skip items not relevant to your change)
