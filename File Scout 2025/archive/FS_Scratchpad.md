# File Scout 3.1 - Smart Sort Integration Scratchpad

## Task Overview
Integrate Smart Sort (from FP V1.8) into File Scout 3.1, enabling preview and execution of smart sorting and keeping UI results in sync after file operations.

## Current Status
- [x] Implemented `open_smart_sort_dialog` in `FileScoutApp`
- [x] Implemented `remove_files_from_results` in `FileScoutApp`
- [x] Verified menu/context menu wiring to handler
- [ ] Manual QA pass (move/copy flows, duplicates mode, filtered view)
- [ ] Theming/polish of Smart Sort dialog (ensure consistency)
- [ ] Edge cases: permission errors, long paths, locked files, network paths

## Notes
- SmartSortDialog already exists in codebase and is compatible with PyQt6.
- `open_smart_sort_dialog` collects only visible rows (respects current filter) and uses `dir_input` as default root.
- `remove_files_from_results` removes rows bottom-up and rebuilds `matching_files` to avoid sort/filter index desync; updates file count and preview.
- Copy operations do not remove from results; move operations do.

## Test Plan
1. Run a search (Find Files) with several extensions.
2. Tools -> Smart Sort…
   - Confirm files populate and destinations look correct.
   - Execute with Move (unchecked Copy).
   - Back in main UI: rows should be removed, count updated, export disabled when empty.
3. Repeat with Copy checked: rows should remain; verify copied files exist.
4. Apply a filter in the results box and open Smart Sort: only visible rows should appear in dialog.
5. Switch to Find Duplicates mode and repeat basic checks (file column index mapping verified).

## Known Warnings
- `qt.svg: Invalid path data; path truncated.` seen at runtime (benign; unrelated to Smart Sort).

## Lessons
- When updating results after external operations, rebuild the backing list to avoid issues with sorted/filtered tables.
- Normalize paths with `Path(...).resolve().lower()` for robust matching on Windows.
- Use destination root derived from current search dir for better UX.

## Next Steps
- [ ] Manual QA and fix issues found
- [ ] Optional: Add progress feedback in Smart Sort execution when many files
- [ ] Optional: Persist last used Smart Sort root in settings

## Recycle Bin + Undo
- [x] Implemented send2trash-based delete, Undo button in status bar, and PowerShell COM restore
- [ ] Manual QA: delete a few files and Undo, confirm restore works for same session; test partial failures and messaging
- [ ] Confirm behavior in both "Find Files" and "Find Duplicates" modes
- [ ] Decide if auto-reinserting restored files into results is desired (currently not auto-refreshing)

### Notes
- Requires `send2trash`; added to requirements.txt
- Restore uses Windows (Shell.Application COM via PowerShell). On other OSes Undo will prompt and open Recycle Bin for manual action.
