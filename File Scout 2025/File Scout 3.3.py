"""
File Scout
----------
Legacy entry-point wrapper.  All application code lives in ui.main_window.
Run this file directly (or via PyInstaller) to launch the app.
"""

import os

# Quiet benign Qt logs and stabilize HiDPI before any PyQt6 import
os.environ.setdefault("QT_LOGGING_RULES", "qt.qpa.screen=false;qt.svg.warning=false")
os.environ.setdefault("QT_SCALE_FACTOR_ROUNDING_POLICY", "RoundPreferFloor")

from ui.main_window import main

if __name__ == "__main__":
    main()
