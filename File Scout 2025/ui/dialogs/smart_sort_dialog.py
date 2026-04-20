from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (QApplication, QButtonGroup, QCheckBox, QComboBox,
                             QDialog, QDialogButtonBox, QFileDialog, QGridLayout,
                             QGroupBox, QHBoxLayout, QHeaderView, QLabel, QLineEdit,
                             QMessageBox, QPushButton, QRadioButton,
                             QTableWidget, QTableWidgetItem, QVBoxLayout,
                             QWidget)
from features.smart_sort.fuzzy_matcher import fuzzy_match_folder
from features.smart_sort.pattern_matcher import (extract_pattern_from_filename,
                                                 ext_folder, scan_folders,
                                                 suggest_destination)
from features.smart_sort.sort_executor import execute_sort_operations


class SmartSortDialog(QDialog):
    """Enhanced Smart Sort dialog with pattern-matching to folders and preview functionality."""
    def __init__(self, parent, files, default_root, zoom_level=100):
        super().__init__(parent)
        self.setWindowTitle("Smart Sort - Enhanced")
        self.setMinimumSize(1000, 600)
        self.parent_app = parent
        self.files = files  # list of file_info dicts
        self.default_root = default_root
        self.zoom_level = zoom_level

        # Enhanced features data
        self.folder_cache = {}
        self.unmatched_files = []  # Track unmatched files
        self.multiple_matches = {}  # Track files with multiple folder matches

        main_layout = QVBoxLayout(self)

        # === ENHANCED CONTROLS ===
        ctrl_box = QGroupBox("Options")
        ctrl_layout = QGridLayout()

        # Destination Root
        ctrl_layout.addWidget(QLabel("Destination Root:"), 0, 0)
        self.root_edit = QLineEdit(self.default_root)
        browse_btn = QPushButton("Browse…")
        browse_btn.clicked.connect(self._browse_root)
        ctrl_layout.addWidget(self.root_edit, 0, 1)
        ctrl_layout.addWidget(browse_btn, 0, 2)

        # Sort Mode Selection
        ctrl_layout.addWidget(QLabel("Sort Mode:"), 1, 0)
        self.sort_mode_group = QButtonGroup()
        self.extension_radio = QRadioButton("By Extension")
        self.pattern_radio = QRadioButton("By Pattern Match")
        self.sort_mode_group.addButton(self.extension_radio, 0)
        self.sort_mode_group.addButton(self.pattern_radio, 1)
        self.pattern_radio.setChecked(True)  # Default to enhanced mode
        ctrl_layout.addWidget(self.extension_radio, 1, 1)
        ctrl_layout.addWidget(self.pattern_radio, 1, 2)

        # Folder Search Depth
        ctrl_layout.addWidget(QLabel("Search Depth:"), 2, 0)
        self.depth_combo = QComboBox()
        self.depth_combo.addItems(["1 level", "2 levels", "3 levels", "5 levels", "Unlimited"])
        self.depth_combo.setCurrentText("3 levels")
        ctrl_layout.addWidget(self.depth_combo, 2, 1)

        # Copy instead of Move
        self.copy_checkbox = QCheckBox("Copy instead of Move")
        ctrl_layout.addWidget(self.copy_checkbox, 2, 2)

        ctrl_box.setLayout(ctrl_layout)
        main_layout.addWidget(ctrl_box)

        # === PREVIEW & SELECTION CONTROLS ===
        controls_layout = QHBoxLayout()

        preview_btn = QPushButton("Preview Destinations")
        preview_btn.clicked.connect(self._preview_destinations)
        controls_layout.addWidget(preview_btn)

        controls_layout.addStretch()

        select_all_btn = QPushButton("Select All")
        select_all_btn.clicked.connect(self._select_all)
        controls_layout.addWidget(select_all_btn)

        deselect_all_btn = QPushButton("Deselect All")
        deselect_all_btn.clicked.connect(self._deselect_all)
        controls_layout.addWidget(deselect_all_btn)

        main_layout.addLayout(controls_layout)

        # === ENHANCED TABLE ===
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["Include", "File", "Current Path", "Matched Folder", "Proposed Destination", "Status"])

        # Enable multi-row selection (Ctrl+Click, Shift+Click)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)

        # Allow user-resizable columns with sensible initial sizing
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setStretchLastSection(False)
        # Set reasonable initial widths
        header.resizeSection(0, 60)    # Include (checkbox)
        header.resizeSection(1, 200)   # File
        header.resizeSection(2, 250)   # Current Path
        header.resizeSection(3, 120)   # Matched Folder
        header.resizeSection(4, 280)   # Proposed Destination
        header.resizeSection(5, 80)    # Status

        # Enable column sorting
        self.table.setSortingEnabled(True)
        self.table.horizontalHeader().setSortIndicatorShown(True)

        # Enable tooltips for full paths
        self.table.setMouseTracking(True)
        self.table.cellEntered.connect(self._show_cell_tooltip)

        # Connect cellClicked so clicking Include column toggles all selected rows
        self.table.cellClicked.connect(self._on_cell_clicked)

        # Selection help label
        selection_help = QLabel("Tip: Ctrl+Click or Shift+Click to select multiple rows, then Space or click Include to toggle them.")
        selection_help.setStyleSheet("color: #888; font-size: 11px; font-style: italic;")
        main_layout.addWidget(selection_help)

        self._populate_table()
        main_layout.addWidget(self.table)

        # === BUTTONS ===
        btn_box = QDialogButtonBox()
        self.exec_btn = btn_box.addButton("Execute Sort", QDialogButtonBox.ButtonRole.AcceptRole)
        self.cancel_btn = btn_box.addButton(QDialogButtonBox.StandardButton.Cancel)
        self.exec_btn.clicked.connect(self._execute)
        self.cancel_btn.clicked.connect(self.reject)
        main_layout.addWidget(btn_box)

        # Connect signals
        self.root_edit.textChanged.connect(self._recompute_destinations)
        self.depth_combo.currentTextChanged.connect(self._recompute_destinations)
        self.sort_mode_group.buttonToggled.connect(self._recompute_destinations)

        # Apply zoom from parent window AFTER UI is created
        if zoom_level != 100:
            self._apply_zoom()

    def _apply_zoom(self):
        """Apply zoom level to all dialog elements"""
        # Calculate new font size based on zoom
        base_font_size = 9
        new_font_size = int(base_font_size * (self.zoom_level / 100))

        # Create font for the dialog
        app_font = self.font()
        app_font.setPointSize(new_font_size)

        # Apply to dialog and all widgets
        self.setFont(app_font)

        # Update all child widgets
        for widget in self.findChildren(QWidget):
            widget.setFont(app_font)

        # Special handling for tables to adjust row heights
        for table in self.findChildren(QTableWidget):
            table.verticalHeader().setDefaultSectionSize(int(25 * (self.zoom_level / 100)))

    def _show_cell_tooltip(self, row, column):
        """Show full path in tooltip when hovering over path columns"""
        if column in [2, 4]:
            item = self.table.item(row, column)
            if item:
                self.table.setToolTip(item.text())

    def _browse_root(self):
        d = QFileDialog.getExistingDirectory(self, "Select Destination Root", self.root_edit.text() or str(Path.home()))
        if d:
            self.root_edit.setText(d)

    def _get_search_depth(self):
        """Convert search depth text to numeric value"""
        depth_text = self.depth_combo.currentText()
        if "Unlimited" in depth_text:
            return 999
        return int(depth_text.split()[0])

    def _scan_folders(self, root_path, max_depth):
        """Scan folders up to max_depth and cache results"""
        return scan_folders(root_path, max_depth, self.folder_cache)

    def _extract_pattern_from_filename(self, filename):
        """Extract the longest matching folder pattern from filename"""
        folders = self._scan_folders(self.root_edit.text(), self._get_search_depth())
        return extract_pattern_from_filename(filename, folders)

    def _fuzzy_match_folder(self, filename):
        """Find fuzzy match for unmatched files"""
        return fuzzy_match_folder(filename, self.root_edit.text(), self._get_search_depth(), self.folder_cache)

    def _suggest_destination(self, file_info):
        """Suggest destination based on selected sort mode"""
        return suggest_destination(
            file_info,
            self.root_edit.text(),
            self.extension_radio.isChecked(),
            self._get_search_depth(),
            self.folder_cache,
        )

    def _ext_folder(self, ext: str) -> str:
        """Convert extension to folder name (original method)"""
        return ext_folder(ext)

    def _select_all(self):
        """Check all Include checkboxes"""
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item:
                item.setCheckState(Qt.CheckState.Checked)

    def _deselect_all(self):
        """Uncheck all Include checkboxes"""
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item:
                item.setCheckState(Qt.CheckState.Unchecked)

    def _on_cell_clicked(self, row, column):
        """Handle cell click — if Include column is clicked, toggle all selected rows."""
        if column != 0:
            return

        # Get the clicked item's new check state (it already toggled)
        clicked_item = self.table.item(row, 0)
        if not clicked_item:
            return
        new_state = clicked_item.checkState()

        # Apply the same state to all other selected rows
        selected_rows = set()
        for idx in self.table.selectionModel().selectedRows():
            selected_rows.add(idx.row())

        # Always include the clicked row
        selected_rows.add(row)

        if len(selected_rows) > 1:
            for sel_row in selected_rows:
                item = self.table.item(sel_row, 0)
                if item:
                    item.setCheckState(new_state)

    def _populate_table(self):
        """Populate table with files and their proposed destinations"""
        # Disable sorting during population to avoid issues with row insertion
        self.table.setSortingEnabled(False)
        self.table.setRowCount(0)
        self.unmatched_files = []
        self.multiple_matches = {}

        for fi in self.files:
            row = self.table.rowCount()
            self.table.insertRow(row)

            # Include checkbox
            include_item = QTableWidgetItem()
            include_item.setFlags(include_item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            include_item.setCheckState(Qt.CheckState.Checked)
            include_item.setData(Qt.ItemDataRole.UserRole, fi)
            self.table.setItem(row, 0, include_item)

            # File name
            self.table.setItem(row, 1, QTableWidgetItem(fi.get('filename', '')))

            # Current path
            current_path = Path(fi['full_path']).parent.as_posix()
            self.table.setItem(row, 2, QTableWidgetItem(current_path))

            # Determine destination
            if self.pattern_radio.isChecked():
                dest_result = self._suggest_destination(fi)
                if dest_result[0] is None:
                    # Unmatched file
                    self.table.setItem(row, 3, QTableWidgetItem(""))
                    self.table.setItem(row, 4, QTableWidgetItem(""))
                    status_item = QTableWidgetItem("Unmatched")
                    status_item.setBackground(QColor('#ffcccc'))  # Light red background
                    self.table.setItem(row, 5, status_item)
                    self.unmatched_files.append((row, fi))
                else:
                    dest_path, folder_name, status = dest_result
                    self.table.setItem(row, 3, QTableWidgetItem(folder_name))
                    self.table.setItem(row, 4, QTableWidgetItem(dest_path.as_posix()))
                    status_item = QTableWidgetItem(status)
                    status_item.setBackground(QColor('#ccffcc'))  # Light green background
                    self.table.setItem(row, 5, status_item)
            else:
                # Extension-based sorting
                dest_path = self._suggest_destination(fi)
                self.table.setItem(row, 3, QTableWidgetItem(""))
                self.table.setItem(row, 4, QTableWidgetItem(dest_path.as_posix()))
                self.table.setItem(row, 5, QTableWidgetItem("Ready"))

        # Re-enable sorting after population
        self.table.setSortingEnabled(True)

    def _recompute_destinations(self):
        """Recompute all destinations when settings change"""
        self._populate_table()

    def _preview_destinations(self):
        """Show preview dialog with unmatched files handling"""
        # First, populate to get current state
        self._populate_table()

        if not self.unmatched_files:
            QMessageBox.information(self, "Preview", "All files have matching folders!")
            return

        # Create unmatched files dialog
        preview_dialog = QDialog(self)
        preview_dialog.setWindowTitle("Unmatched Files - Preview")
        preview_dialog.setMinimumSize(800, 500)

        layout = QVBoxLayout(preview_dialog)

        # Info label
        info_label = QLabel(f"Found {len(self.unmatched_files)} unmatched files. Review suggestions below:")
        layout.addWidget(info_label)

        # Table for unmatched files
        unmatched_table = QTableWidget(len(self.unmatched_files), 4)
        unmatched_table.setHorizontalHeaderLabels(["File", "Suggested Folder", "Accept", "Confidence"])
        unmatched_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        unmatched_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        unmatched_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        unmatched_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)

        # Populate unmatched files with suggestions
        suggestions = {}
        for idx, (row, fi) in enumerate(self.unmatched_files):
            filename = fi.get('filename', '')
            unmatched_table.setItem(idx, 0, QTableWidgetItem(filename))

            # Get fuzzy match
            fuzzy_match = self._fuzzy_match_folder(filename)
            if fuzzy_match:
                unmatched_table.setItem(idx, 1, QTableWidgetItem(fuzzy_match['name']))
                unmatched_table.setItem(idx, 3, QTableWidgetItem("Medium"))

                # Add checkbox for acceptance
                checkbox = QTableWidgetItem()
                checkbox.setFlags(checkbox.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                checkbox.setCheckState(Qt.CheckState.Unchecked)
                unmatched_table.setItem(idx, 2, checkbox)

                suggestions[idx] = fuzzy_match
            else:
                unmatched_table.setItem(idx, 1, QTableWidgetItem("No suggestion"))
                unmatched_table.setItem(idx, 3, QTableWidgetItem("None"))

                # Disabled checkbox
                checkbox = QTableWidgetItem()
                checkbox.setFlags(checkbox.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                checkbox.setCheckState(Qt.CheckState.Unchecked)
                checkbox.setFlags(checkbox.flags() & ~Qt.ItemFlag.ItemIsEnabled)
                unmatched_table.setItem(idx, 2, checkbox)

        layout.addWidget(unmatched_table)

        # Buttons
        btn_box = QDialogButtonBox()
        apply_btn = btn_box.addButton("Apply Suggestions", QDialogButtonBox.ButtonRole.AcceptRole)
        cancel_btn = btn_box.addButton(QDialogButtonBox.StandardButton.Cancel)
        btn_box.addButton("Leave Unmatched", QDialogButtonBox.ButtonRole.RejectRole)

        layout.addWidget(btn_box)

        # Handle button clicks
        def apply_suggestions():
            # Apply accepted suggestions to main table
            for idx, (row, fi) in enumerate(self.unmatched_files):
                if idx in suggestions:
                    checkbox = unmatched_table.item(idx, 2)
                    if checkbox and checkbox.checkState() == Qt.CheckState.Checked:
                        # Update the main table with the suggested destination
                        folder = suggestions[idx]
                        dest_path = folder['full_path'] / fi['filename']
                        self.table.item(row, 3).setText(folder['name'])
                        self.table.item(row, 4).setText(dest_path.as_posix())
                        self.table.item(row, 5).setText("Suggested")
                        self.table.item(row, 5).setBackground(QColor('#ffffcc'))  # Light yellow

            preview_dialog.accept()

        def leave_unmatched():
            preview_dialog.accept()

        apply_btn.clicked.connect(apply_suggestions)
        cancel_btn.clicked.connect(preview_dialog.reject)
        btn_box.rejected.connect(leave_unmatched)

        preview_dialog.exec()

    def keyPressEvent(self, event):
        """Handle key press events"""
        # Space toggles include for selected rows
        if event.key() == Qt.Key.Key_Space:
            for idx in self.table.selectionModel().selectedRows():
                item = self.table.item(idx.row(), 0)
                if item.checkState() == Qt.CheckState.Checked:
                    item.setCheckState(Qt.CheckState.Unchecked)
                else:
                    item.setCheckState(Qt.CheckState.Checked)
            event.accept()
            return
        super().keyPressEvent(event)

    def _execute(self):
        """Execute the smart sort operation"""
        root = Path(self.root_edit.text())
        if not root.exists():
            try:
                root.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not create destination root:\n{e}")
                return

        # Check for unmatched files
        unmatched_count = len([r for r in range(self.table.rowCount())
                              if self.table.item(r, 5) and self.table.item(r, 5).text() == "Unmatched"])

        if unmatched_count > 0:
            reply = QMessageBox.question(
                self, "Unmatched Files",
                f"There are {unmatched_count} unmatched files. Do you want to:\n\n"
                "Yes - Skip unmatched files and continue\n"
                "No - Cancel and review unmatched files",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                return

        do_copy = self.copy_checkbox.isChecked()
        operations = []

        # Process files
        for row in range(self.table.rowCount()):
            inc_item = self.table.item(row, 0)
            if inc_item.checkState() != Qt.CheckState.Checked:
                continue

            # Skip unmatched files
            status_item = self.table.item(row, 5)
            if status_item and status_item.text() == "Unmatched":
                continue

            fi = inc_item.data(Qt.ItemDataRole.UserRole)
            src = Path(fi['full_path'])
            dest_text = self.table.item(row, 4).text()

            if not dest_text:
                continue

            operations.append({
                'row_index': row,
                'source_path': str(src),
                'destination_path': dest_text,
            })

        execution_result = execute_sort_operations(
            operations,
            do_copy,
            self.parent_app._generate_unique_dest_path,
            process_events=QApplication.processEvents,
        )

        success = execution_result['success_count']
        errors = execution_result['errors']
        moved_paths = execution_result['moved_paths']

        for row_result in execution_result['row_results']:
            status_item = self.table.item(row_result['row_index'], 5)
            if status_item:
                status_item.setText(row_result['status'])
                status_item.setBackground(QColor(row_result['background']))

        # Show summary
        summary = f"Smart Sort complete.\n{'Copied' if do_copy else 'Moved'} {success} item(s)."
        if errors:
            summary += f"\nFailed: {len(errors)} item(s)."
        if unmatched_count > 0:
            summary += f"\nSkipped: {unmatched_count} unmatched item(s)."

        QMessageBox.information(self, "Smart Sort Complete", summary)

        # Update parent table if we moved files
        if moved_paths:
            self.parent_app.remove_files_from_results(moved_paths)

        self.accept()
