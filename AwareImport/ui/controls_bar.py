from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLineEdit, QCheckBox,
    QPushButton, QProgressBar, QLabel, QFrame, QComboBox,
)
from PySide6.QtCore import Signal, QSettings


class ControlsBar(QWidget):
    # signals
    add_files_clicked = Signal()
    add_folder_clicked = Signal()
    paste_entities_clicked = Signal()
    search_clicked = Signal()
    validate_clicked = Signal()
    build_info_pages_clicked = Signal()
    export_clicked = Signal()
    update_sheets_clicked = Signal()
    clear_clicked = Signal()
    cancel_clicked = Signal()
    copy_table_clicked = Signal()
    save_session_clicked = Signal()
    load_session_clicked = Signal()
    load_traveler_clicked = Signal()
    clear_traveler_clicked = Signal()
    mode_changed = Signal(str)  # "CML Import", "Thickness Activity", "Info Page Builder"
    deadleg_changed = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 4)
        main_layout.setSpacing(6)

        # row 1: system path + CML style
        row1 = QHBoxLayout()
        row1.setSpacing(8)

        path_label = QLabel("System Path Parent:")
        path_label.setStyleSheet("font-weight: bold;")
        row1.addWidget(path_label)

        self.system_path_input = QLineEdit()
        self.system_path_input.setPlaceholderText("XCEL > Diversified > Buckeye > Unit > Piping")
        self.system_path_input.setMinimumWidth(400)
        # restore last-used system path
        settings = QSettings("CMLBatchBuilder", "AwareImport")
        saved_path = settings.value("system_path", "", type=str)
        if saved_path:
            self.system_path_input.setText(saved_path)
        self.system_path_input.textChanged.connect(self._save_system_path)
        row1.addWidget(self.system_path_input, 1)

        self.cml_style_checkbox = QCheckBox("Standard CML (1.01)")
        self.cml_style_checkbox.setChecked(True)
        self.cml_style_checkbox.setToolTip(
            "Checked: Standard style 1.01, 1.02\nUnchecked: Client style 1.1, 1.2"
        )
        row1.addWidget(self.cml_style_checkbox)

        self.deadleg_checkbox = QCheckBox("Deadleg")
        self.deadleg_checkbox.setChecked(False)
        self.deadleg_checkbox.setToolTip(
            "Append ' Deadleg' to System Name and Equipment ID\n"
            "for piping circuits that contain deadleg CMLs."
        )
        saved_deadleg = settings.value("deadleg", False, type=bool)
        self.deadleg_checkbox.setChecked(saved_deadleg)
        self.deadleg_checkbox.toggled.connect(self._on_deadleg_toggled)
        row1.addWidget(self.deadleg_checkbox)

        self.insp_freq_checkbox = QCheckBox("Export Inspection Frequency CSV")
        self.insp_freq_checkbox.setChecked(False)
        self.insp_freq_checkbox.setToolTip(
            "When checked, export generates an additional CSV\n"
            "formatted for Aware inspection frequency import."
        )
        saved_insp_freq = settings.value("insp_freq_export", False, type=bool)
        self.insp_freq_checkbox.setChecked(saved_insp_freq)
        self.insp_freq_checkbox.toggled.connect(self._save_insp_freq)
        row1.addWidget(self.insp_freq_checkbox)

        pid_prefix_label = QLabel("P&ID Prefix:")
        pid_prefix_label.setStyleSheet("font-weight: bold;")
        row1.addWidget(pid_prefix_label)

        self.pid_prefix_input = QLineEdit()
        self.pid_prefix_input.setPlaceholderText("Example: K1GP-PID-")
        self.pid_prefix_input.setMinimumWidth(180)
        saved_pid_prefix = settings.value("pid_prefix", "", type=str)
        if saved_pid_prefix:
            self.pid_prefix_input.setText(saved_pid_prefix)
        self.pid_prefix_input.textChanged.connect(self._save_pid_prefix)
        row1.addWidget(self.pid_prefix_input)

        # separator before mode toggle
        sep_mode = QFrame()
        sep_mode.setFrameShape(QFrame.VLine)
        sep_mode.setFrameShadow(QFrame.Sunken)
        row1.addWidget(sep_mode)

        mode_label = QLabel("Mode:")
        mode_label.setStyleSheet("font-weight: bold;")
        row1.addWidget(mode_label)

        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["CML Import", "Thickness Activity", "Info Page Builder"])
        self.mode_combo.setToolTip(
            "CML Import: aggregated CSV export\n"
            "Thickness Activity: per-entity historicals view\n"
            "Info Page Builder: build and review entity-level info rows"
        )
        self.mode_combo.currentTextChanged.connect(self.mode_changed.emit)
        row1.addWidget(self.mode_combo)

        main_layout.addLayout(row1)

        # row 2: buttons
        row2 = QHBoxLayout()
        row2.setSpacing(6)

        self.add_files_btn = QPushButton("Add Files")
        self.add_files_btn.clicked.connect(self.add_files_clicked.emit)
        row2.addWidget(self.add_files_btn)

        self.add_folder_btn = QPushButton("Add Folder")
        self.add_folder_btn.clicked.connect(self.add_folder_clicked.emit)
        row2.addWidget(self.add_folder_btn)

        self.paste_btn = QPushButton("Paste Entities")
        self.paste_btn.clicked.connect(self.paste_entities_clicked.emit)
        row2.addWidget(self.paste_btn)

        self.search_btn = QPushButton("Search")
        self.search_btn.clicked.connect(self.search_clicked.emit)
        row2.addWidget(self.search_btn)

        # separator
        sep = QFrame()
        sep.setFrameShape(QFrame.VLine)
        sep.setFrameShadow(QFrame.Sunken)
        row2.addWidget(sep)

        self.validate_btn = QPushButton("Validate")
        self.validate_btn.setStyleSheet("QPushButton { font-weight: bold; }")
        self.validate_btn.clicked.connect(self.validate_clicked.emit)
        row2.addWidget(self.validate_btn)

        self.build_info_pages_btn = QPushButton("Build Info Pages")
        self.build_info_pages_btn.setStyleSheet(
            "QPushButton { font-weight: bold; background-color: #8e44ad; color: white; padding: 4px 16px; }"
            "QPushButton:hover { background-color: #9b59b6; }"
        )
        self.build_info_pages_btn.setVisible(False)
        self.build_info_pages_btn.clicked.connect(self.build_info_pages_clicked.emit)
        row2.addWidget(self.build_info_pages_btn)

        self.load_traveler_btn = QPushButton("Load Traveler")
        self.load_traveler_btn.setStyleSheet(
            "QPushButton { font-weight: bold; background-color: #16a085; color: white; padding: 4px 14px; }"
            "QPushButton:hover { background-color: #1abc9c; }"
        )
        self.load_traveler_btn.setToolTip(
            "Load an API-570 Traveler spreadsheet to pre-populate\n"
            "P&ID, Class, and Description fields (highest priority source)"
        )
        self.load_traveler_btn.setVisible(False)
        self.load_traveler_btn.clicked.connect(self.load_traveler_clicked.emit)
        row2.addWidget(self.load_traveler_btn)

        self.traveler_label = QLabel("")
        self.traveler_label.setStyleSheet(
            "QLabel { font-size: 12px; color: #1abc9c; padding: 0 4px; }"
        )
        self.traveler_label.setVisible(False)
        row2.addWidget(self.traveler_label)

        self.clear_traveler_btn = QPushButton("\u00d7")
        self.clear_traveler_btn.setFixedSize(22, 22)
        self.clear_traveler_btn.setStyleSheet(
            "QPushButton { font-weight: bold; font-size: 14px; color: #e74c3c; border: none; }"
            "QPushButton:hover { color: #ff6b6b; }"
        )
        self.clear_traveler_btn.setToolTip("Remove loaded traveler")
        self.clear_traveler_btn.setVisible(False)
        self.clear_traveler_btn.clicked.connect(self.clear_traveler_clicked.emit)
        row2.addWidget(self.clear_traveler_btn)

        self.export_btn = QPushButton("Export CSV")
        self.export_btn.setStyleSheet(
            "QPushButton { font-weight: bold; background-color: #27ae60; color: white; padding: 4px 16px; }"
            "QPushButton:hover { background-color: #2ecc71; }"
        )
        self.export_btn.clicked.connect(self.export_clicked.emit)
        row2.addWidget(self.export_btn)

        self.update_sheets_btn = QPushButton("Update Sheets")
        self.update_sheets_btn.setStyleSheet(
            "QPushButton { font-weight: bold; background-color: #e67e22; color: white; padding: 4px 16px; }"
            "QPushButton:hover { background-color: #f39c12; }"
        )
        self.update_sheets_btn.setToolTip("Push edited cells back to the source Excel files")
        self.update_sheets_btn.clicked.connect(self.update_sheets_clicked.emit)
        row2.addWidget(self.update_sheets_btn)

        self.clear_btn = QPushButton("Clear List")
        self.clear_btn.clicked.connect(self.clear_clicked.emit)
        row2.addWidget(self.clear_btn)

        # separator before session buttons
        sep_session = QFrame()
        sep_session.setFrameShape(QFrame.VLine)
        sep_session.setFrameShadow(QFrame.Sunken)
        row2.addWidget(sep_session)

        self.save_session_btn = QPushButton("Save Session")
        self.save_session_btn.setToolTip("Save the current file list, parsed data, and settings to a session file")
        self.save_session_btn.clicked.connect(self.save_session_clicked.emit)
        row2.addWidget(self.save_session_btn)

        self.load_session_btn = QPushButton("Load Session")
        self.load_session_btn.setToolTip("Restore a previously saved session")
        self.load_session_btn.clicked.connect(self.load_session_clicked.emit)
        row2.addWidget(self.load_session_btn)

        # UT Inspection Date (shown in Thickness Activity mode)
        self.inspection_date_label = QLabel("")
        self.inspection_date_label.setStyleSheet(
            "QLabel { font-weight: bold; font-size: 13px; color: #f1c40f; padding: 0 12px; }"
        )
        self.inspection_date_label.setVisible(False)
        row2.addWidget(self.inspection_date_label)

        # Copy Table button (shown alongside inspection date in TA mode)
        self.copy_table_btn = QPushButton("Copy Table")
        self.copy_table_btn.setStyleSheet(
            "QPushButton { font-weight: bold; background-color: #2980b9; color: white; padding: 4px 12px; }"
            "QPushButton:hover { background-color: #3498db; }"
        )
        self.copy_table_btn.setToolTip("Copy the Thickness Activity table to clipboard for pasting into IDMS")
        self.copy_table_btn.setVisible(False)
        self.copy_table_btn.clicked.connect(self.copy_table_clicked.emit)
        row2.addWidget(self.copy_table_btn)

        row2.addStretch()

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.clicked.connect(self.cancel_clicked.emit)
        row2.addWidget(self.cancel_btn)

        main_layout.addLayout(row2)

        # row 3: progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumHeight(16)
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)

    def _save_system_path(self, text: str):
        settings = QSettings("CMLBatchBuilder", "AwareImport")
        settings.setValue("system_path", text.strip())

    def _save_pid_prefix(self, text: str):
        settings = QSettings("CMLBatchBuilder", "AwareImport")
        settings.setValue("pid_prefix", text)

    def _on_deadleg_toggled(self, checked: bool):
        settings = QSettings("CMLBatchBuilder", "AwareImport")
        settings.setValue("deadleg", checked)
        self.deadleg_changed.emit(checked)

    def _save_insp_freq(self, checked: bool):
        settings = QSettings("CMLBatchBuilder", "AwareImport")
        settings.setValue("insp_freq_export", checked)

    def is_insp_freq_export(self) -> bool:
        return self.insp_freq_checkbox.isChecked()

    def get_system_path(self) -> str:
        return self.system_path_input.text().strip()

    def get_pid_prefix(self) -> str:
        return self.pid_prefix_input.text().strip()

    def is_standard_style(self) -> bool:
        return self.cml_style_checkbox.isChecked()

    def is_deadleg(self) -> bool:
        return self.deadleg_checkbox.isChecked()

    def current_mode(self) -> str:
        return self.mode_combo.currentText()

    def set_inspection_date(self, date_str: str):
        """Show the UT inspection date in the button bar. Pass empty string to hide."""
        if date_str:
            self.inspection_date_label.setText(f"UT Inspection Date: {date_str}")
            self.inspection_date_label.setVisible(True)
            self.copy_table_btn.setVisible(True)
        else:
            self.inspection_date_label.setText("")
            self.inspection_date_label.setVisible(False)
            self.copy_table_btn.setVisible(False)

    def set_mode_ui(self, mode: str):
        is_info = mode == "Info Page Builder"
        self.build_info_pages_btn.setVisible(is_info)
        self.load_traveler_btn.setVisible(is_info)
        # Traveler label/clear are visible only if loaded AND in info mode
        has_traveler = bool(self.traveler_label.text())
        self.traveler_label.setVisible(is_info and has_traveler)
        self.clear_traveler_btn.setVisible(is_info and has_traveler)
        if mode == "Thickness Activity":
            self.copy_table_btn.setToolTip("Copy the Thickness Activity table to clipboard for pasting into IDMS")
        elif is_info:
            self.copy_table_btn.setVisible(True)
            self.copy_table_btn.setToolTip("Copy the Info Page Builder table to the clipboard")
        else:
            self.copy_table_btn.setToolTip("Copy the current table to the clipboard")
            if not self.inspection_date_label.isVisible():
                self.copy_table_btn.setVisible(False)

    def set_traveler_label(self, filename: str):
        """Show/hide the traveler filename indicator."""
        if filename:
            self.traveler_label.setText(f"\u2705 {filename}")
            self.traveler_label.setVisible(True)
            self.clear_traveler_btn.setVisible(True)
        else:
            self.traveler_label.setText("")
            self.traveler_label.setVisible(False)
            self.clear_traveler_btn.setVisible(False)

    def set_processing(self, active: bool):
        # toggle UI state during processing
        self.add_files_btn.setEnabled(not active)
        self.add_folder_btn.setEnabled(not active)
        self.paste_btn.setEnabled(not active)
        self.search_btn.setEnabled(not active)
        self.validate_btn.setEnabled(not active)
        self.build_info_pages_btn.setEnabled(not active)
        self.export_btn.setEnabled(not active)
        self.update_sheets_btn.setEnabled(not active)
        self.clear_btn.setEnabled(not active)
        self.save_session_btn.setEnabled(not active)
        self.load_session_btn.setEnabled(not active)
        self.cancel_btn.setEnabled(active)
        self.progress_bar.setVisible(active)
        if active:
            self.progress_bar.setValue(0)

    def set_progress(self, current: int, total: int):
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)
