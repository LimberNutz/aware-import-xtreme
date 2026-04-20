# Safe Changelog — How to Change This Project Safely

## Before Any Change

1. **Read the blueprint** (`docs/00_BLUEPRINT.md`) to understand the data flow.
2. **Check `app/constants.py`** — most domain logic is driven by these constants.
3. **Understand `CMLRow`** — it is THE canonical data model; all services consume it.

## High-Risk Areas

| Area | Risk | Why |
|------|------|-----|
| `app/constants.py` | HIGH | Changing `AWARE_CSV_HEADERS` or `PIPING_COLUMN_MAP` breaks CSV export and write-back |
| `services/excel_parser.py` | HIGH | Incorrect parsing silently corrupts data |
| `services/excel_writer.py` | HIGH | Write-back modifies user's source Excel files |
| `models/cml_row.py` | MEDIUM | Adding/removing fields affects all services + session compat |
| `services/session.py` | MEDIUM | Schema changes break saved sessions; bump `SESSION_VERSION` |

## Change Checklist

- [ ] If modifying `CMLRow` fields: update `PIPING_COLUMN_MAP`, `FIELD_MAP`, `_map_row_to_csv`, `_TA_COL_TO_EXCEL`, and TA builder
- [ ] If modifying CSV headers: update `AWARE_CSV_HEADERS` in constants and `_map_row_to_csv` in csv_exporter
- [ ] If modifying session schema: bump `SESSION_VERSION` in `services/session.py`
- [ ] If adding new columns to TA view: update `TA_COLUMNS`, `_TA_VIEW_COL_TO_NAME`, `_TA_COL_TO_EXCEL`
- [ ] If changing column mappings: verify both read (parser) and write (excel_writer) paths
- [ ] Test with real UT Excel sheets before deploying — automated tests do not exist yet

## Required Manual Checks

Since there are no automated tests:

1. Load a known-good Excel file → verify parsed row count matches expected
2. Export CSV → open in Excel → verify column headers and data alignment
3. Edit a cell in preview → Update Sheets → reopen source file → verify change persisted
4. Save session → close → reopen → load session → verify state restored
5. Test both CML Import and Thickness Activity modes

## Adding Tests (Recommended)

```
tests/
  test_parser.py      # parse known fixture .xlsx → assert CMLRow fields
  test_transformer.py  # transform → assert defaults, CML formatting
  test_aggregator.py   # dedup logic
  test_csv_exporter.py # export → read back CSV → assert headers + values
```

Run with: `python -m pytest tests/`

## Regenerating Snapshots After Changes

```bash
python tools/blueprint/snapshot.py
```

This updates `docs/snapshots/` so the blueprint stays current.
