from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QGridLayout,
    QLabel, QTextEdit, QGroupBox, QStatusBar,
)
from PySide6.QtGui import QFont

from launcher.tool_registry import get_tools
from launcher.process_manager import ProcessManager
from launcher.tool_card import ToolCard
from launcher.design_doc_dialog import DesignDocDialog


class LauncherWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Aware Toolbox")
        self.setMinimumSize(920, 660)
        self._tools: list[dict]    = get_tools()
        self._cards: dict[str, ToolCard] = {}
        self._pm = ProcessManager(self)
        self._setup_ui()
        self._connect_signals()

    # ------------------------------------------------------------------
    # UI build
    # ------------------------------------------------------------------

    def _setup_ui(self):
        root = QWidget()
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 12)

        # Title bar
        title = QLabel("◆  Aware Toolbox")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title.setStyleSheet("color: #007acc; border: none;")
        layout.addWidget(title)

        subtitle = QLabel(
            "Select a tool to launch — each runs in its own independent window."
        )
        subtitle.setStyleSheet("color: #9d9d9d; font-size: 12px; border: none;")
        layout.addWidget(subtitle)

        # 2 × 2 card grid
        grid = QGridLayout()
        grid.setSpacing(12)
        for i, tool in enumerate(self._tools):
            card = ToolCard(tool)
            card.launch_clicked.connect(self._on_launch)
            card.stop_clicked.connect(self._on_stop)
            card.dialog_requested.connect(self._on_dialog)
            self._cards[tool["id"]] = card
            grid.addWidget(card, i // 2, i % 2)
        layout.addLayout(grid, 1)

        # Activity log
        log_grp    = QGroupBox("Activity Log")
        log_layout = QVBoxLayout(log_grp)
        log_layout.setContentsMargins(6, 6, 6, 6)
        self._log = QTextEdit()
        self._log.setReadOnly(True)
        self._log.setFont(QFont("Consolas", 9))
        self._log.setFixedHeight(110)
        self._log.setStyleSheet(
            "QTextEdit { background-color: #161616; color: #9d9d9d; border: none; }"
        )
        log_layout.addWidget(self._log)
        layout.addWidget(log_grp)

        # Status bar
        sb = QStatusBar()
        self.setStatusBar(sb)
        sb.showMessage("Ready — select a tool to launch.")
        self._status_bar = sb

    # ------------------------------------------------------------------
    # Signals
    # ------------------------------------------------------------------

    def _connect_signals(self):
        self._pm.status_changed.connect(self._on_status_changed)
        self._pm.log_message.connect(self._append_log)

    # ------------------------------------------------------------------
    # Handlers
    # ------------------------------------------------------------------

    def _on_launch(self, tool_id: str):
        tool = self._tool_by_id(tool_id)
        self._pm.launch(tool_id, tool["cmd"], tool["cwd"])

    def _on_stop(self, tool_id: str):
        self._pm.stop(tool_id)

    def _on_dialog(self, tool_id: str):
        tool = self._tool_by_id(tool_id)
        dlg  = DesignDocDialog(tool["cwd"], self)
        dlg.exec()

    def _on_status_changed(self, tool_id: str, status: str):
        card = self._cards.get(tool_id)
        if card:
            card.set_status(status)
        names = {t["id"]: t["name"] for t in self._tools}
        self._status_bar.showMessage(
            f"{names.get(tool_id, tool_id)}: {status}"
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _tool_by_id(self, tool_id: str) -> dict:
        return next(t for t in self._tools if t["id"] == tool_id)

    def _append_log(self, line: str):
        self._log.append(line)
        sb = self._log.verticalScrollBar()
        sb.setValue(sb.maximum())
