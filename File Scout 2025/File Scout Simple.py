"""
File Scout - Simple Entry Point
Alternative entry point that imports all modules explicitly
to help PyInstaller detect dependencies.
"""

import os
import sys

# Add current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Quiet Qt logs
os.environ.setdefault("QT_LOGGING_RULES", "qt.qpa.screen=false;qt.svg.warning=false")
os.environ.setdefault("QT_SCALE_FACTOR_ROUNDING_POLICY", "RoundPreferFloor")

# Explicit imports to help PyInstaller
import ui.main_window
import ui.dialogs.file_audit_dialog
import ui.dialogs.profile_manager
import ui.dialogs.smart_sort_dialog
import ui.widgets.custom_widgets
import core.file_scanner
import core.search_engine
import features.preview.manager
import features.preview.handlers
import features.smart_sort.fuzzy_matcher
import features.smart_sort.pattern_matcher
import features.smart_sort.sort_executor
import utils.themes
import utils.excel_exporter
import config
import constants

if __name__ == "__main__":
    ui.main_window.main()
