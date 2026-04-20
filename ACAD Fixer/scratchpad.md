# Scratchpad

## Current Task
Improve PySide6 GUI usability with counts, filtering, sorting, bulk selection helpers, resizable sections, and an asset file side panel.

- [X] Update GUI to construct `JobManager` with the current args-based API
- [X] Retest asset loading in GUI
- [X] Verify batch run wiring still matches current pipeline
- [X] Add totals/filter/sort and bulk selection controls
- [X] Make the main sections resizable
- [X] Add asset file side panel with right-click open actions
- [X] Compact the file pane
- [X] Make file preview optional to reduce wasted space
- [ ] Relaunch and smoke test the upgraded GUI

## Lessons
- Read the file before editing it.
- Match new UI code to the existing constructor/API shapes instead of assuming helper kwargs exist.
- Preserve user selection state independently from the visible widget list when adding sort/filter controls.
- Add larger GUI features in small, exact hunks to avoid patch drift in fast-moving files.
- Optional panes are usually better than always-visible detail panels in dense desktop tools.
