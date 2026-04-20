import sys
import os
import warnings

# Suppress openpyxl Data Validation extension warning
warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")
# Suppress pypdf duplicate-dictionary warnings from malformed PDFs
warnings.filterwarnings("ignore", category=UserWarning, module="pypdf")

# ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont
from ui.main_window import MainWindow

# Base sizes at 100% zoom
BASE_FONT_PT = 10
_BASE_FONT_PX = 13
_BASE_ITEM_PAD = 4
_BASE_HDR_PAD = 6
_BASE_INPUT_PAD = 5
_BASE_BTN_PAD_V = 6
_BASE_BTN_PAD_H = 16
_BASE_CB_SIZE = 16
_BASE_CB_SPACE = 5
_BASE_MENU_PAD_V = 6
_BASE_MENU_PAD_H = 24


def build_stylesheet(zoom: float = 1.0) -> str:
    """Return the application stylesheet scaled by *zoom* (1.0 = 100%)."""
    def px(base):
        return max(1, round(base * zoom))

    font = px(_BASE_FONT_PX)
    item_pad = px(_BASE_ITEM_PAD)
    hdr_pad = px(_BASE_HDR_PAD)
    inp_pad = px(_BASE_INPUT_PAD)
    btn_v = px(_BASE_BTN_PAD_V)
    btn_h = px(_BASE_BTN_PAD_H)
    cb = px(_BASE_CB_SIZE)
    cb_sp = px(_BASE_CB_SPACE)
    menu_v = px(_BASE_MENU_PAD_V)
    menu_h = px(_BASE_MENU_PAD_H)

    return f"""
/* Main Window & General Widget */
QMainWindow, QDialog {{
    background-color: #1e1e1e;
}}
QWidget {{
    color: #e0e0e0;
    font-size: {font}px;
    background-color: #1e1e1e;
}}

/* Tables */
QTableView {{
    background-color: #252526;
    alternate-background-color: #2d2d30;
    gridline-color: #3e3e42;
    selection-background-color: #094771;
    selection-color: #ffffff;
    border: 1px solid #3e3e42;
    outline: none;
}}
QTableView::item {{
    padding: {item_pad}px;
    border: none;
}}
QTableView::item:selected {{
    background-color: #094771;
    color: #ffffff;
}}

/* Header View */
QHeaderView::section {{
    background-color: #333337;
    color: #f0f0f0;
    padding: {hdr_pad}px;
    border: none;
    border-right: 1px solid #252526;
    border-bottom: 1px solid #252526;
    font-weight: bold;
}}
QHeaderView::section:checked {{
    background-color: #094771;
}}

/* Input Fields */
QLineEdit, QTextEdit, QPlainTextEdit {{
    background-color: #3c3c3c;
    color: #f0f0f0;
    border: 1px solid #3e3e42;
    border-radius: 2px;
    padding: {inp_pad}px;
    selection-background-color: #264f78;
}}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
    border: 1px solid #007acc;
    background-color: #3c3c3c;
}}

/* Buttons */
QPushButton {{
    background-color: #3c3c3c;
    color: #f0f0f0;
    border: 1px solid #3e3e42;
    border-radius: 2px;
    padding: {btn_v}px {btn_h}px;
}}
QPushButton:hover {{
    background-color: #4e4e50;
}}
QPushButton:pressed {{
    background-color: #252526;
}}
QPushButton:disabled {{
    background-color: #252526;
    color: #6d6d6d;
    border: 1px solid #333333;
}}

/* Scrollbars */
QScrollBar:vertical {{
    border: none;
    background-color: #1e1e1e;
    width: 14px;
    margin: 0px;
}}
QScrollBar::handle:vertical {{
    background-color: #424242;
    min-height: 20px;
    border-radius: 0px;
}}
QScrollBar::handle:vertical:hover {{
    background-color: #4f4f4f;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    border: none;
    background: none;
    height: 0px;
}}
QScrollBar:horizontal {{
    border: none;
    background-color: #1e1e1e;
    height: 14px;
    margin: 0px;
}}
QScrollBar::handle:horizontal {{
    background-color: #424242;
    min-width: 20px;
    border-radius: 0px;
}}
QScrollBar::handle:horizontal:hover {{
    background-color: #4f4f4f;
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    border: none;
    background: none;
    width: 0px;
}}

/* Splitter */
QSplitter::handle {{
    background-color: #3e3e42;
    width: 2px;
}}

/* Progress Bar */
QProgressBar {{
    background-color: #252526;
    border: 1px solid #3e3e42;
    border-radius: 2px;
    text-align: center;
    color: #f0f0f0;
}}
QProgressBar::chunk {{
    background-color: #007acc;
    width: 20px;
}}

/* Menus */
QMenu {{
    background-color: #252526;
    border: 1px solid #3e3e42;
    padding: 4px;
}}
QMenu::item {{
    background-color: transparent;
    padding: {menu_v}px {menu_h}px;
    color: #f0f0f0;
}}
QMenu::item:selected {{
    background-color: #094771;
    color: #ffffff;
}}
QMenu::separator {{
    height: 1px;
    background-color: #3e3e42;
    margin: 4px 8px;
}}

/* Status Bar */
QStatusBar {{
    background-color: #007acc;
    color: #ffffff;
}}
QStatusBar::item {{
    border: none;
}}

/* Labels */
QLabel {{
    color: #e0e0e0;
}}

/* Checkbox */
QCheckBox {{
    color: #e0e0e0;
    spacing: {cb_sp}px;
}}
QCheckBox::indicator {{
    width: {cb}px;
    height: {cb}px;
    border: 1px solid #3e3e42;
    background-color: #3c3c3c;
}}
QCheckBox::indicator:unchecked:hover {{
    border: 1px solid #007acc;
}}
QCheckBox::indicator:checked {{
    background-color: #007acc;
    border: 1px solid #007acc;
    image: url(data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxMiIgaGVpZ2h0PSIxMiIgdmlld0JveD0iMCAwIDEyIDEyIj48cGF0aCBmaWxsPSIjZmZmZmZmIiBkPSJNMi41IDZMNSA4LjUgOS41IDQiLz48L3N2Zz4=);
}}
"""


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(build_stylesheet(1.0))

    font = QFont("Segoe UI", BASE_FONT_PT)
    app.setFont(font)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
