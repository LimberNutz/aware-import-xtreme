from PySide6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Signal
from PySide6.QtGui import QFont


_BORDER_NORMAL = "#3e3e42"
_BORDER_HOVER  = "#007acc"

_STATUS_STYLE = {
    "stopped": "color: #6d6d6d;",
    "running": "color: #4caf50; font-weight: bold;",
    "crashed": "color: #f44336; font-weight: bold;",
}
_STATUS_TEXT = {
    "stopped": "⬤  Stopped",
    "running": "⬤  Running",
    "crashed": "⬤  Crashed",
}
_BTN_STYLE = {
    "stopped": (
        "QPushButton { background-color: #2d7d32; color: #fff; border: none; "
        "border-radius: 3px; padding: 8px 20px; font-weight: bold; }"
        "QPushButton:hover { background-color: #388e3c; }"
    ),
    "running": (
        "QPushButton { background-color: #c62828; color: #fff; border: none; "
        "border-radius: 3px; padding: 8px 20px; font-weight: bold; }"
        "QPushButton:hover { background-color: #d32f2f; }"
    ),
    "crashed": (
        "QPushButton { background-color: #e65100; color: #fff; border: none; "
        "border-radius: 3px; padding: 8px 20px; font-weight: bold; }"
        "QPushButton:hover { background-color: #f57c00; }"
    ),
}
_BTN_TEXT = {
    "stopped": "Launch",
    "running": "Stop",
    "crashed": "Relaunch",
}


def _card_sheet(border: str) -> str:
    return (
        f"QFrame#tool_card {{ border: 1px solid {border}; border-radius: 4px; }}"
    )


class ToolCard(QFrame):
    launch_clicked   = Signal(str)   # tool_id
    stop_clicked     = Signal(str)   # tool_id
    dialog_requested = Signal(str)   # tool_id

    def __init__(self, tool: dict, parent=None):
        super().__init__(parent)
        self._tool   = tool
        self._status = "stopped"
        self.setObjectName("tool_card")
        self.setStyleSheet(_card_sheet(_BORDER_NORMAL))
        self.setMinimumSize(300, 250)
        self._build_ui()

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(6)
        layout.setContentsMargins(16, 14, 16, 14)

        # Header: emoji icon + tool name
        header = QHBoxLayout()
        icon_lbl = QLabel(self._tool["icon"])
        icon_lbl.setFont(QFont("Segoe UI Emoji", 20))
        icon_lbl.setStyleSheet("border: none;")
        header.addWidget(icon_lbl)

        name_lbl = QLabel(self._tool["name"])
        name_lbl.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        name_lbl.setStyleSheet("color: #f0f0f0; border: none;")
        header.addWidget(name_lbl, 1)
        layout.addLayout(header)

        # Tagline
        tagline = QLabel(self._tool["tagline"])
        tagline.setStyleSheet("color: #9d9d9d; border: none; font-size: 12px;")
        tagline.setWordWrap(True)
        layout.addWidget(tagline)

        # Thin separator
        sep = QLabel()
        sep.setFixedHeight(1)
        sep.setStyleSheet("background-color: #3e3e42; border: none; margin: 2px 0px;")
        layout.addWidget(sep)

        # Feature list
        for feat in self._tool.get("features", []):
            fl = QLabel(f"  •  {feat}")
            fl.setStyleSheet("color: #c0c0c0; border: none; font-size: 12px;")
            layout.addWidget(fl)

        layout.addStretch()

        # Status indicator
        self._status_lbl = QLabel(_STATUS_TEXT["stopped"])
        self._status_lbl.setStyleSheet(_STATUS_STYLE["stopped"] + " border: none; font-size: 12px;")
        layout.addWidget(self._status_lbl)

        # Launch / Stop / Relaunch button
        self._btn = QPushButton(_BTN_TEXT["stopped"])
        self._btn.setStyleSheet(_BTN_STYLE["stopped"])
        self._btn.setMinimumHeight(34)
        self._btn.clicked.connect(self._on_btn_clicked)
        layout.addWidget(self._btn)

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def _on_btn_clicked(self):
        tid  = self._tool["id"]
        mode = self._tool.get("launch_mode", "subprocess")
        if self._status == "running":
            self.stop_clicked.emit(tid)
        elif mode == "dialog":
            self.dialog_requested.emit(tid)
        else:
            self.launch_clicked.emit(tid)

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def set_status(self, status: str):
        self._status = status
        self._status_lbl.setText(_STATUS_TEXT.get(status, _STATUS_TEXT["stopped"]))
        self._status_lbl.setStyleSheet(
            _STATUS_STYLE.get(status, _STATUS_STYLE["stopped"]) + " border: none; font-size: 12px;"
        )
        self._btn.setText(_BTN_TEXT.get(status, _BTN_TEXT["stopped"]))
        self._btn.setStyleSheet(_BTN_STYLE.get(status, _BTN_STYLE["stopped"]))

    # ------------------------------------------------------------------
    # Hover effect — border colour only
    # ------------------------------------------------------------------

    def enterEvent(self, event):
        self.setStyleSheet(_card_sheet(_BORDER_HOVER))
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.setStyleSheet(_card_sheet(_BORDER_NORMAL))
        super().leaveEvent(event)
