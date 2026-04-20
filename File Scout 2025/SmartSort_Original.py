"""
Original SmartSortDialog class backup - for revert purposes
Extracted from File Scout 3.2.py lines 1157-1328
"""

class SmartSortDialog(QDialog):
    """Preview and execute Smart Sort operations based on file extensions."""
    def __init__(self, parent, files, default_root, zoom_level=100):
        super().__init__(parent)
        self.setWindowTitle("Smart Sort")
        self.setMinimumSize(800, 500)
        self.parent_app = parent
        self.files = files  # list of file_info dicts
        self.default_root = default_root
        self.zoom_level = zoom_level

        main_layout = QVBoxLayout(self)

        # Controls
        ctrl_box = QGroupBox("Options")
        ctrl_layout = QGridLayout()
        ctrl_layout.addWidget(QLabel("Destination Root:"), 0, 0)
        self.root_edit = QLineEdit(self.default_root)
        browse_btn = QPushButton("Browse…")
        browse_btn.clicked.connect(self._browse_root)
        ctrl_layout.addWidget(self.root_edit, 0, 1)
        ctrl_layout.addWidget(browse_btn, 0, 2)
        self.copy_checkbox = QCheckBox("Copy instead of Move")
        ctrl_layout.addWidget(self.copy_checkbox, 1, 1)
        ctrl_box.setLayout(ctrl_layout)
        main_layout.addWidget(ctrl_box)

        # Table
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Include", "File", "Current Path", "Ext", "Destination"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self._populate_table()
        main_layout.addWidget(self.table)

        # Buttons
        btn_box = QDialogButtonBox()
        self.exec_btn = btn_box.addButton("Execute Sort", QDialogButtonBox.ButtonRole.AcceptRole)
        self.cancel_btn = btn_box.addButton(QDialogButtonBox.StandardButton.Cancel)
        self.exec_btn.clicked.connect(self._execute)
        self.cancel_btn.clicked.connect(self.reject)
        main_layout.addWidget(btn_box)

        # Recompute destinations when root changes
        self.root_edit.textChanged.connect(self._recompute_destinations)
        
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

    def _browse_root(self):
        d = QFileDialog.getExistingDirectory(self, "Select Destination Root", self.root_edit.text() or str(Path.home()))
        if d:
            self.root_edit.setText(d)

    def _ext_folder(self, ext: str) -> str:
        if not ext:
            return "Unsorted"
        return ext.lstrip('.').upper()

    def _suggest_destination(self, file_info) -> Path:
        root = Path(self.root_edit.text())
        ext = file_info.get('extension', '')
        folder = self._ext_folder(ext)
        return root / folder / file_info['filename']

    def _populate_table(self):
        self.table.setRowCount(0)
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
            self.table.setItem(row, 2, QTableWidgetItem(Path(fi['full_path']).parent.as_posix()))
            # Ext
            self.table.setItem(row, 3, QTableWidgetItem(fi.get('extension', '')))
            # Destination
            dest_path = self._suggest_destination(fi)
            self.table.setItem(row, 4, QTableWidgetItem(dest_path.as_posix()))

    def _recompute_destinations(self):
        for row in range(self.table.rowCount()):
            fi = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
            dest_path = self._suggest_destination(fi)
            self.table.item(row, 4).setText(dest_path.as_posix())

    def keyPressEvent(self, event):
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
        root = Path(self.root_edit.text())
        if not root.exists():
            try:
                root.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not create destination root:\n{e}")
                return

        do_copy = self.copy_checkbox.isChecked()
        success = 0
        errors = []
        moved_paths = []
        for row in range(self.table.rowCount()):
            inc_item = self.table.item(row, 0)
            if inc_item.checkState() != Qt.CheckState.Checked:
                continue
            fi = inc_item.data(Qt.ItemDataRole.UserRole)
            src = Path(fi['full_path'])
            dest = Path(self.table.item(row, 4).text())
            try:
                dest.parent.mkdir(parents=True, exist_ok=True)
                final_dest = self.parent_app._generate_unique_dest_path(dest)
                if do_copy:
                    shutil.copy2(src, final_dest)
                else:
                    src.rename(final_dest)
                    moved_paths.append(src)
                success += 1
            except Exception as e:
                errors.append((str(src), str(e)))
            if success % 10 == 0:
                QApplication.processEvents()

        summary = f"Smart Sort complete. {'Copied' if do_copy else 'Moved'} {success} item(s)."
        if errors:
            summary += f" Failed: {len(errors)}."
        QMessageBox.information(self, "Smart Sort", summary)
        # Update parent table if we moved files
        if moved_paths:
            self.parent_app.remove_files_from_results(moved_paths)
        self.accept()
