# Database Contract

## Status: No Database

This project has **no database**. All data is transient (in-memory) during a session.

### Persistence mechanisms

| Mechanism | Format | Location |
|-----------|--------|----------|
| Session file | JSON | User-chosen path (`.json`) |
| QSettings | Windows Registry | `HKCU\Software\CMLBatchBuilder\AwareImport` |
| Source Excel files | `.xlsx` / `.xlsm` | User's filesystem (read + optional write-back) |
| Exported CSV | `.csv` | User-chosen path |

### Session file schema (v1)

```json
{
  "_version": 1,
  "system_path": "str",
  "standard_style": true,
  "current_mode": "CML Import | Thickness Activity",
  "entries": [ FileEntry.model_dump() ],
  "all_rows": [ CMLRow.model_dump() ],
  "all_errors": [ "str" ]
}
```

### QSettings keys

| Key | Type | Purpose |
|-----|------|---------|
| `system_path` | str | Last-used system path parent |
| `add_files_folder` | str | Last browse dir for Add Files |
| `add_folder_folder` | str | Last browse dir for Add Folder |
| `session_folder` | str | Last browse dir for session save/load |
| `last_session_path` | str | Auto-load session on startup |
| `search_folder` | str | Last search folder in dialogs |

### Invariants

- Session version must be `<= SESSION_VERSION` (currently 1) or load is rejected.
- `FileEntry.status` enum: `Pending`, `Parsed`, `Error`, `Missing`.
- Deduplication key: `(system_path.strip(), system_name.strip(), cml.strip())`.
- Write-back requires non-empty `source_file`, `source_sheet`, and `source_row > 0`.
