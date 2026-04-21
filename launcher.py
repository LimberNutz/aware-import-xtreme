import sys
import os

os.environ.setdefault("QT_LOGGING_RULES", "qt.qpa.screen=false;qt.svg.warning=false")

# IMPORTANT: HiDPI rounding policy must be configured BEFORE QApplication
# is constructed. We set it via the explicit API (not the env var, which
# Qt 6 processes late and warns about) and do it at import time so any
# downstream module that instantiates QApplication still sees it.
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QGuiApplication
from PySide6.QtWidgets import QApplication

QGuiApplication.setHighDpiScaleFactorRoundingPolicy(
    Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
)

from launcher.main_window import LauncherWindow


_STYLESHEET = """
QMainWindow, QDialog {
    background-color: #1e1e1e;
}
QWidget {
    color: #e0e0e0;
    font-size: 13px;
    background-color: #1e1e1e;
}
QGroupBox {
    color: #9d9d9d;
    border: 1px solid #3e3e42;
    border-radius: 3px;
    margin-top: 8px;
    padding-top: 4px;
    font-size: 11px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 8px;
    padding: 0 4px;
}
QPushButton {
    background-color: #3c3c3c;
    color: #f0f0f0;
    border: 1px solid #3e3e42;
    border-radius: 2px;
    padding: 5px 14px;
}
QPushButton:hover {
    background-color: #4e4e50;
}
QPushButton:disabled {
    background-color: #252526;
    color: #6d6d6d;
    border: 1px solid #333333;
}
QLineEdit, QPlainTextEdit, QSpinBox {
    background-color: #3c3c3c;
    color: #f0f0f0;
    border: 1px solid #3e3e42;
    border-radius: 2px;
    padding: 4px;
    selection-background-color: #264f78;
}
QLineEdit:focus, QPlainTextEdit:focus, QSpinBox:focus {
    border: 1px solid #007acc;
}
QTextEdit {
    background-color: #3c3c3c;
    color: #f0f0f0;
    border: 1px solid #3e3e42;
    border-radius: 2px;
    selection-background-color: #264f78;
}
QTextEdit:focus {
    border: 1px solid #007acc;
}
QCheckBox {
    color: #e0e0e0;
    spacing: 5px;
}
QCheckBox::indicator {
    width: 14px;
    height: 14px;
    border: 1px solid #3e3e42;
    background-color: #3c3c3c;
    border-radius: 2px;
}
QCheckBox::indicator:hover {
    border: 1px solid #007acc;
}
QCheckBox::indicator:checked {
    background-color: #007acc;
    border: 1px solid #007acc;
}
QSpinBox::up-button, QSpinBox::down-button {
    background-color: #4e4e50;
    border: none;
    width: 16px;
}
QSpinBox::up-button:hover, QSpinBox::down-button:hover {
    background-color: #5e5e60;
}
QScrollBar:vertical {
    border: none;
    background-color: #1e1e1e;
    width: 12px;
    margin: 0px;
}
QScrollBar::handle:vertical {
    background-color: #424242;
    min-height: 20px;
    border-radius: 0px;
}
QScrollBar::handle:vertical:hover {
    background-color: #4f4f4f;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
    border: none;
    background: none;
}
QScrollBar:horizontal {
    border: none;
    background-color: #1e1e1e;
    height: 12px;
    margin: 0px;
}
QScrollBar::handle:horizontal {
    background-color: #424242;
    min-width: 20px;
}
QScrollBar::handle:horizontal:hover {
    background-color: #4f4f4f;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
    border: none;
    background: none;
}
QStatusBar {
    background-color: #007acc;
    color: #ffffff;
    font-size: 12px;
}
QStatusBar::item {
    border: none;
}
QLabel {
    color: #e0e0e0;
    border: none;
}
QMessageBox {
    background-color: #252526;
}
QMessageBox QLabel {
    color: #e0e0e0;
}
"""


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(_STYLESHEET)
    app.setFont(QFont("Segoe UI", 10))

    window = LauncherWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
