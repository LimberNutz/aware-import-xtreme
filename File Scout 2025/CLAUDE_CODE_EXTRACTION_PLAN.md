# File Scout 3.2 Extraction Plan for Claude Code

## Overview

This plan breaks down the monolithic File Scout 3.2.py (4583 lines) into manageable modules optimized for Claude Code's execution model.

## Key Findings

1. **Signal Contract**: SearchEngine only emits `progress_update`, while FileSearchWorker has 4 signals (lines 1039-1042). The worker translates engine results into UI signals.
2. **FileAuditDialog**: Already externalized - keep it separate.
3. **Preview System**: Clean handlers with base class - ideal first extraction.
4. **SmartSortDialog**: Mixes UI and algorithms - needs two-phase extraction.

## Phase 0: Interface Freeze (Critical First Step)

### Task: Create Interface Contracts

Create these stub files first to define exact interfaces:

```python
# core/interfaces.py
from PyQt6.QtCore import QObject, pyqtSignal
from typing import Dict, List, Generator, Any

class SearchInterface(QObject):
    progress_update = pyqtSignal(int, str)

    def stop(self): pass
    def find_files(self, params: Dict) -> Generator[Dict, None, None]: pass
    def find_duplicates(self, params: Dict) -> Generator[List[Dict], None, None]: pass

class WorkerInterface(QObject):
    progress_update = pyqtSignal(int, str)
    search_complete = pyqtSignal(bool, str)
    live_result = pyqtSignal(dict)
    duplicate_group_found = pyqtSignal(list)

    def stop(self): pass
    def run(self): pass
```

## Phase 1: Zero-Risk Extractions (Batch Together)

### Task 1.1: Extract Constants and Config

```python
# config/constants.py
SETTINGS_ORG = "SBC-SoftwareByChris"
SETTINGS_APP = "FileScout"
LARGE_DIR_THRESHOLD = 100_000
MAX_RESULTS = 50_000
# ... all other constants
```

### Task 1.2: Extract Utility Widgets

```python
# ui/widgets/custom_widgets.py
class DropLineEdit(QLineEdit):
    # Already self-contained (lines 113-128)
```

### Task 1.3: Extract Excel Exporter

```python
# utils/excel_exporter.py
class ExcelExporter:
    # Already self-contained (lines 129-662)
```

### Task 1.4: Extract Theme Utilities

```python
# utils/themes.py
def apply_theme(app, theme_name): ...
def get_icon(name): ...
# Extract theme-related functions from main window
```

## Phase 2: Preview Subsystem (Cleanest Extraction)

### Task 2.1: Extract All Preview Handlers Together

```python
# features/preview/handlers.py
class PreviewHandler:
    """Base class (lines 1657-1672)"""

class TextPreviewHandler(PreviewHandler):
    # Lines 1673-1696

class CodePreviewHandler(PreviewHandler):
    # Lines 1697-1725

# ... extract ALL handlers in one file
```

### Task 2.2: Extract Preview Manager

```python
# features/preview/manager.py
class PreviewManager:
    # Lines 2107-2143
    # Already clean - just needs handler imports
```

## Phase 3: Profile Manager (Contained Dialog)

### Task 3.1: Extract Profile Dialog

```python
# ui/dialogs/profile_manager.py
class ProfileManagerDialog(QDialog):
    # Lines 1076-1157
    # Only depends on QSettings and constants
```

## Phase 4: Core Search (Critical Path)

### Task 4.1: Extract SearchEngine

```python
# core/search_engine.py
class SearchEngine(SearchInterface):
    # Lines 663-1036
    # Keep exactly as-is - don't fix signals yet
```

### Task 4.2: Extract FileSearchWorker

```python
# core/file_scanner.py
class FileSearchWorker(QThread, WorkerInterface):
    # Lines 1037-1075
    # Import SearchEngine from core.search_engine
```

## Phase 5: Smart Sort (Two-Phase)

### Task 5.1: Move Dialog As-Is

```python
# ui/dialogs/smart_sort_dialog.py
class SmartSortDialog(QDialog):
    # Lines 1158-1656
    # Move without changes first
```

### Task 5.2: Extract Algorithm Components (Later)

```python
# features/smart_sort/pattern_matcher.py
# features/smart_sort/fuzzy_matcher.py
# features/smart_sort/sort_executor.py
```

## Phase 6: File Audit (Already Separate)

### Task 6.1: Update Import Path

```python
# Just change import in main window:
from ui.dialogs.file_audit_dialog import FileAuditDialog
```

## Phase 7: Main Window (Final Step)

### Task 7.1: Extract FileScoutApp

```python
# ui/main_window.py
class FileScoutApp(QMainWindow):
    # Lines 2646-4583
    # Update all imports to new module paths
```

## Execution Strategy for Claude Code

### 1. Batch Processing

- Extract all preview handlers in ONE operation
- Extract all utilities in ONE operation
- Minimize context switching

### 2. Smoke Tests

After each phase, run:

```bash
python -c "import config.constants; import ui.widgets.custom_widgets; import utils.excel_exporter"
```

### 3. Import Path Updates

Keep a running list of imports to update:

- `from file_audit_dialog import` → `from ui.dialogs.file_audit_dialog import`
- Add new module imports as they're created

### 4. Critical Order

1. Interfaces first (prevents breakage)
2. Constants before anything that uses them
3. Preview before main window (depends on it)
4. Search engine before worker
5. Main window last (depends on everything)

## Common Pitfalls to Avoid

1. **Don't split SmartSortDialog's algorithms yet** - move as one unit first
2. **Don't "fix" SearchEngine signals** - keep working contract intact
3. **Don't move FileAuditDialog** - it's already working separately
4. **Don't extract main window early** - it's the integration point

## Testing Checklist

After each extraction:

- [ ] File launches without import errors
- [ ] Theme applies correctly
- [ ] Preview works for supported types
- [ ] Profiles save/load
- [ ] Search returns results
- [ ] Smart Sort dialog opens
- [ ] File Audit dialog opens

## Final Structure

```
File Scout 2025/
├── main.py (new entry point)
├── config/
│   ├── __init__.py
│   └── constants.py
├── core/
│   ├── __init__.py
│   ├── interfaces.py
│   ├── search_engine.py
│   └── file_scanner.py
├── ui/
│   ├── __init__.py
│   ├── main_window.py
│   ├── dialogs/
│   │   ├── __init__.py
│   │   ├── profile_manager.py
│   │   ├── smart_sort_dialog.py
│   │   └── file_audit_dialog.py (imported)
│   └── widgets/
│       ├── __init__.py
│       └── custom_widgets.py
├── features/
│   ├── __init__.py
│   ├── preview/
│   │   ├── __init__.py
│   │   ├── handlers.py
│   │   └── manager.py
│   └── smart_sort/ (phase 5.2)
└── utils/
    ├── __init__.py
    ├── themes.py
    ├── excel_exporter.py
    └── file_utils.py
```

This plan maximizes Claude Code's efficiency by batching related extractions and minimizing cross-module dependencies during the refactoring process.
