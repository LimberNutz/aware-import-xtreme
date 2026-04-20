# Safe Changelog

## Before Any Change

1. Read the blueprint (`docs/00_BLUEPRINT.md`)
2. Check `docs/snapshots/rehydrate_bundle.txt` for project context
3. Verify config.yaml paths (cad_root, oda_exe) are correct for your environment
4. Test with --dry-run flag before executing on production files
5. Backup original DWG/DXF files before running full pipeline

## High-Risk Areas

| Area | Risk | Why |
|------|------|-----|
| CAD file modification | High | Directly modifies DWG/DXF files; backups essential |
| PDF stamping | Medium | Alters PDF content; verify stamp placement and content |
| ODA File Converter | High | External dependency; must be in PATH or configured correctly |
| CML CSV parsing | Medium | Malformed CSV can cause job failures; validate input format |
| QSettings registry writes | Low | Writes to Windows Registry; requires appropriate permissions |

## Change Checklist

- [ ] Verify config.yaml paths exist and are accessible
- [ ] Test ODA File Converter availability (run `oda --version` or similar)
- [ ] Validate CML CSV format matches expected schema
- [ ] Run with --dry-run first to preview changes
- [ ] Ensure backups exist for target CAD/PDF files
- [ ] Run tests
- [ ] Regenerate snapshots: `python tools/blueprint/snapshot.py`
  - This updates architecture, API surface, config patterns, integrations, data flow, and docs index
