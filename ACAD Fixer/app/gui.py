#!/usr/bin/env python
"""PySide6 GUI for ACAD Fixer utility."""
import logging
import os
import sys
from types import SimpleNamespace
from pathlib import Path
from typing import List

from PySide6.QtCore import QThread, Signal, Qt, QUrl
from PySide6.QtGui import QAction, QDesktopServices
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QFileDialog, QListWidget, QListWidgetItem,
    QCheckBox, QTextEdit, QProgressBar, QMessageBox, QGroupBox, QSplitter,
    QComboBox, QAbstractItemView, QMenu
)

from app.config import AppConfig
from app.pipeline.run_job import JobManager


logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')


class BatchWorker(QThread):
    """Worker thread to run batch processing without freezing UI."""
    log_signal = Signal(str)
    finished_signal = Signal(dict)
    error_signal = Signal(str)

    def __init__(self, csv_path: str, cad_root: str, exclusions: List[str], dry_run: bool):
        super().__init__()
        self.csv_path = csv_path
        self.cad_root = cad_root
        self.exclusions = exclusions
        self.dry_run = dry_run

    def run(self):
        """Run batch processing in background thread."""
        handler = None
        try:
            # Redirect logging to signal
            class LogHandler(logging.Handler):
                def __init__(self, signal):
                    super().__init__()
                    self.signal = signal

                def emit(self, record):
                    self.signal.emit(self.format(record))

            handler = LogHandler(self.log_signal)
            handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s'))
            logging.getLogger().addHandler(handler)

            args = SimpleNamespace(
                config=None,
                csv=self.csv_path,
                exclude=",".join(self.exclusions),
                dry_run=self.dry_run,
                asset=None,
                lookup=None,
                file=None,
            )
            manager = JobManager(args)
            manager.config.cad_root = self.cad_root

            # Get all assets
            all_assets = manager._get_all_assets()
            # Filter exclusions
            assets_to_process = [a for a in all_assets if a not in self.exclusions]

            self.log_signal.emit(f"Starting batch: {len(assets_to_process)} assets, exclusions: {self.exclusions}")
            self.log_signal.emit(f"Dry run: {self.dry_run}")

            results = {'processed': 0, 'skipped': 0, 'failed': 0}

            for asset_id in assets_to_process:
                self.log_signal.emit(f"=== Processing: {asset_id} ===")
                try:
                    record = manager._get_record_for_asset(asset_id)
                    if not record:
                        self.log_signal.emit(f"No record found for {asset_id}")
                        results['failed'] += 1
                        continue
                    ok = manager._process_asset(record)
                    if ok:
                        results['processed'] += 1
                    else:
                        results['failed'] += 1
                except Exception as e:
                    self.log_signal.emit(f"Failed to process {asset_id}: {e}")
                    results['failed'] += 1

            self.log_signal.emit(f"Batch complete: {results}")
            self.finished_signal.emit(results)

        except Exception as e:
            self.error_signal.emit(str(e))
        finally:
            if handler is not None:
                logging.getLogger().removeHandler(handler)


class ACADFixerGUI(QMainWindow):
    """Main GUI window for ACAD Fixer."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("ACAD Fixer - Title Block Automation")
        self.setMinimumSize(900, 700)
        self.worker = None
        self.all_assets: List[str] = []
        self.checked_assets = set()
        self.related_files: List[Path] = []

        self._init_ui()
        self._load_defaults()

    def _init_ui(self):
        """Initialize UI components."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        main_splitter = QSplitter(Qt.Vertical)
        main_layout.addWidget(main_splitter)

        top_widget = QWidget()
        top_layout = QVBoxLayout(top_widget)

        input_group = QGroupBox("Configuration")
        input_layout = QVBoxLayout()

        # CSV Path
        csv_layout = QHBoxLayout()
        csv_layout.addWidget(QLabel("CSV File:"))
        self.csv_path_edit = QLineEdit()
        csv_layout.addWidget(self.csv_path_edit)
        csv_browse_btn = QPushButton("Browse...")
        csv_browse_btn.clicked.connect(self._browse_csv)
        csv_layout.addWidget(csv_browse_btn)
        input_layout.addLayout(csv_layout)

        # CAD Root Path
        cad_layout = QHBoxLayout()
        cad_layout.addWidget(QLabel("CAD Root:"))
        self.cad_root_edit = QLineEdit()
        cad_layout.addWidget(self.cad_root_edit)
        cad_browse_btn = QPushButton("Browse...")
        cad_browse_btn.clicked.connect(self._browse_cad_root)
        cad_layout.addWidget(cad_browse_btn)
        input_layout.addLayout(cad_layout)

        input_group.setLayout(input_layout)
        top_layout.addWidget(input_group)

        content_splitter = QSplitter(Qt.Horizontal)

        asset_group = QGroupBox("Asset Selection")
        asset_layout = QVBoxLayout()

        asset_info_layout = QHBoxLayout()
        self.asset_counts_label = QLabel("Total: 0 | Selected: 0 | Excluded: 0 | Showing: 0")
        asset_info_layout.addWidget(self.asset_counts_label)
        asset_info_layout.addStretch()
        asset_layout.addLayout(asset_info_layout)

        asset_controls_layout = QHBoxLayout()
        asset_controls_layout.addWidget(QLabel("Filter:"))
        self.filter_edit = QLineEdit()
        self.filter_edit.setPlaceholderText("Type to filter asset IDs")
        self.filter_edit.textChanged.connect(self._apply_asset_filter)
        asset_controls_layout.addWidget(self.filter_edit)

        asset_controls_layout.addWidget(QLabel("Sort:"))
        self.sort_combo = QComboBox()
        self.sort_combo.addItems(["A → Z", "Z → A", "Selected First", "Excluded First"])
        self.sort_combo.currentTextChanged.connect(self._refresh_asset_list)
        asset_controls_layout.addWidget(self.sort_combo)
        asset_layout.addLayout(asset_controls_layout)

        self.asset_list = QListWidget()
        self.asset_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.asset_list.itemChanged.connect(self._on_asset_item_changed)
        self.asset_list.currentItemChanged.connect(self._on_asset_selection_changed)
        asset_layout.addWidget(self.asset_list)

        asset_btn_layout = QHBoxLayout()
        self.load_assets_btn = QPushButton("Load Assets from CSV")
        self.load_assets_btn.clicked.connect(self._load_assets)
        asset_btn_layout.addWidget(self.load_assets_btn)

        self.select_all_btn = QPushButton("Select All")
        self.select_all_btn.clicked.connect(self._select_all_assets)
        asset_btn_layout.addWidget(self.select_all_btn)

        self.deselect_all_btn = QPushButton("Deselect All")
        self.deselect_all_btn.clicked.connect(self._deselect_all_assets)
        asset_btn_layout.addWidget(self.deselect_all_btn)

        self.select_marked_btn = QPushButton("Select Highlighted")
        self.select_marked_btn.clicked.connect(self._select_marked_assets)
        asset_btn_layout.addWidget(self.select_marked_btn)

        self.deselect_marked_btn = QPushButton("Deselect Highlighted")
        self.deselect_marked_btn.clicked.connect(self._deselect_marked_assets)
        asset_btn_layout.addWidget(self.deselect_marked_btn)

        self.select_visible_btn = QPushButton("Select Visible")
        self.select_visible_btn.clicked.connect(self._select_visible_assets)
        asset_btn_layout.addWidget(self.select_visible_btn)

        self.deselect_visible_btn = QPushButton("Deselect Visible")
        self.deselect_visible_btn.clicked.connect(self._deselect_visible_assets)
        asset_btn_layout.addWidget(self.deselect_visible_btn)

        self.invert_visible_btn = QPushButton("Invert Visible")
        self.invert_visible_btn.clicked.connect(self._invert_visible_assets)
        asset_btn_layout.addWidget(self.invert_visible_btn)

        asset_layout.addLayout(asset_btn_layout)
        asset_group.setLayout(asset_layout)

        file_group = QGroupBox("Asset Files")
        file_layout = QVBoxLayout()
        self.file_summary_label = QLabel("Select an asset to view related files")
        file_layout.addWidget(self.file_summary_label)

        file_toolbar_layout = QHBoxLayout()
        self.preview_toggle = QCheckBox("Show Preview")
        self.preview_toggle.setChecked(False)
        self.preview_toggle.toggled.connect(self._toggle_file_preview)
        file_toolbar_layout.addWidget(self.preview_toggle)
        file_toolbar_layout.addStretch()
        file_layout.addLayout(file_toolbar_layout)

        self.file_list = QListWidget()
        self.file_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.file_list.customContextMenuRequested.connect(self._show_file_context_menu)
        self.file_list.currentItemChanged.connect(self._on_file_selection_changed)
        file_layout.addWidget(self.file_list)

        self.file_preview = QTextEdit()
        self.file_preview.setReadOnly(True)
        self.file_preview.setVisible(False)
        file_layout.addWidget(self.file_preview)
        file_group.setLayout(file_layout)

        content_splitter.addWidget(asset_group)
        content_splitter.addWidget(file_group)
        content_splitter.setSizes([700, 220])
        top_layout.addWidget(content_splitter)

        options_group = QGroupBox("Options")
        options_layout = QHBoxLayout()

        self.dry_run_checkbox = QCheckBox("Dry Run (no file modifications)")
        self.dry_run_checkbox.setChecked(True)
        options_layout.addWidget(self.dry_run_checkbox)

        options_group.setLayout(options_layout)
        top_layout.addWidget(options_group)

        action_layout = QHBoxLayout()

        self.run_btn = QPushButton("Run Batch")
        self.run_btn.clicked.connect(self._run_batch)
        self.run_btn.setMinimumHeight(40)
        action_layout.addWidget(self.run_btn)

        top_layout.addLayout(action_layout)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        top_layout.addWidget(self.progress_bar)

        log_group = QGroupBox("Log Output")
        log_layout = QVBoxLayout()
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)
        log_group.setLayout(log_layout)

        main_splitter.addWidget(top_widget)
        main_splitter.addWidget(log_group)
        main_splitter.setSizes([480, 220])

    def _load_defaults(self):
        """Load default paths from config."""
        try:
            config = AppConfig.load()
            if config.default_csv:
                self.csv_path_edit.setText(config.default_csv)

            if config.cad_root:
                self.cad_root_edit.setText(config.cad_root)
        except Exception as e:
            self._log(f"Failed to load config defaults: {e}")

    def _browse_csv(self):
        """Browse for CSV file."""
        path, _ = QFileDialog.getOpenFileName(
            self, "Select CSV File", "", "CSV Files (*.csv);;All Files (*)"
        )
        if path:
            self.csv_path_edit.setText(path)

    def _browse_cad_root(self):
        """Browse for CAD root directory."""
        path = QFileDialog.getExistingDirectory(self, "Select CAD Root Directory")
        if path:
            self.cad_root_edit.setText(path)

    def _load_assets(self):
        """Load assets from CSV into list."""
        csv_path = self.csv_path_edit.text()
        if not csv_path:
            QMessageBox.warning(self, "Warning", "Please select a CSV file first.")
            return

        try:
            args = SimpleNamespace(
                config=None,
                csv=csv_path,
                exclude="",
                dry_run=True,
                asset=None,
                lookup=None,
                file=None,
            )
            manager = JobManager(args)
            assets = manager._get_all_assets()

            self.all_assets = sorted(assets)
            self.checked_assets = set(self.all_assets)
            self._refresh_asset_list()
            self.related_files = []
            self.file_list.clear()
            self.file_preview.clear()
            self.file_summary_label.setText("Select an asset to view related files")

            self._log(f"Loaded {len(assets)} assets from CSV")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load assets: {e}")
            self._log(f"Error loading assets: {e}")

    def _select_all_assets(self):
        """Select all assets."""
        self.checked_assets = set(self.all_assets)
        self._refresh_asset_list()

    def _deselect_all_assets(self):
        """Deselect all assets."""
        self.checked_assets.clear()
        self._refresh_asset_list()

    def _select_marked_assets(self):
        for item in self.asset_list.selectedItems():
            self.checked_assets.add(item.text())
        self._refresh_asset_list()

    def _deselect_marked_assets(self):
        for item in self.asset_list.selectedItems():
            self.checked_assets.discard(item.text())
        self._refresh_asset_list()

    def _select_visible_assets(self):
        for i in range(self.asset_list.count()):
            item = self.asset_list.item(i)
            if not item.isHidden():
                self.checked_assets.add(item.text())
        self._refresh_asset_list()

    def _deselect_visible_assets(self):
        for i in range(self.asset_list.count()):
            item = self.asset_list.item(i)
            if not item.isHidden():
                self.checked_assets.discard(item.text())
        self._refresh_asset_list()

    def _invert_visible_assets(self):
        for i in range(self.asset_list.count()):
            item = self.asset_list.item(i)
            if item.isHidden():
                continue
            if item.text() in self.checked_assets:
                self.checked_assets.discard(item.text())
            else:
                self.checked_assets.add(item.text())
        self._refresh_asset_list()

    def _on_asset_item_changed(self, item: QListWidgetItem):
        if item.checkState() == Qt.Checked:
            self.checked_assets.add(item.text())
        else:
            self.checked_assets.discard(item.text())
        self._update_asset_counts()

    def _refresh_asset_list(self):
        filter_text = self.filter_edit.text().strip().lower() if hasattr(self, "filter_edit") else ""
        assets = list(self.all_assets)
        current_asset = self.asset_list.currentItem().text() if self.asset_list.currentItem() else ""

        sort_mode = self.sort_combo.currentText() if hasattr(self, "sort_combo") else "A → Z"
        if sort_mode == "Z → A":
            assets.sort(reverse=True)
        elif sort_mode == "Selected First":
            assets.sort(key=lambda asset: (asset not in self.checked_assets, asset))
        elif sort_mode == "Excluded First":
            assets.sort(key=lambda asset: (asset in self.checked_assets, asset))
        else:
            assets.sort()

        self.asset_list.blockSignals(True)
        self.asset_list.clear()
        restored_item = None
        for asset in assets:
            item = QListWidgetItem(asset)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Checked if asset in self.checked_assets else Qt.Unchecked)
            self.asset_list.addItem(item)
            if filter_text and filter_text not in asset.lower():
                item.setHidden(True)
            if asset == current_asset:
                restored_item = item
        if restored_item is not None and not restored_item.isHidden():
            self.asset_list.setCurrentItem(restored_item)
        elif self.asset_list.count() and self.asset_list.currentItem() is None:
            for i in range(self.asset_list.count()):
                if not self.asset_list.item(i).isHidden():
                    self.asset_list.setCurrentItem(self.asset_list.item(i))
                    break
        self.asset_list.blockSignals(False)
        self._update_asset_counts()

    def _apply_asset_filter(self):
        filter_text = self.filter_edit.text().strip().lower()
        for i in range(self.asset_list.count()):
            item = self.asset_list.item(i)
            item.setHidden(bool(filter_text) and filter_text not in item.text().lower())
        self._update_asset_counts()

    def _update_asset_counts(self):
        total = len(self.all_assets) if self.all_assets else self.asset_list.count()
        selected = len(self.checked_assets)
        excluded = max(total - selected, 0)
        showing = 0
        for i in range(self.asset_list.count()):
            item = self.asset_list.item(i)
            if not item.isHidden():
                showing += 1
        self.asset_counts_label.setText(
            f"Total: {total} | Selected: {selected} | Excluded: {excluded} | Showing: {showing}"
        )

    def _get_selected_assets(self) -> List[str]:
        """Get list of selected asset IDs."""
        return sorted(self.checked_assets)

    def _get_excluded_assets(self) -> List[str]:
        """Get list of unchecked (excluded) asset IDs."""
        return sorted(set(self.all_assets) - self.checked_assets)

    def _on_asset_selection_changed(self, current: QListWidgetItem, previous: QListWidgetItem):
        asset_id = current.text() if current else ""
        self._load_related_files(asset_id)

    def _load_related_files(self, asset_id: str):
        self.related_files = []
        self.file_list.clear()
        self.file_preview.clear()
        if not asset_id:
            self.file_summary_label.setText("Select an asset to view related files")
            return

        cad_root_text = self.cad_root_edit.text().strip()
        if not cad_root_text:
            self.file_summary_label.setText(f"{asset_id}: CAD root not set")
            return

        cad_root = Path(cad_root_text)
        if not cad_root.exists():
            self.file_summary_label.setText(f"{asset_id}: CAD root not found")
            return

        matches: List[Path] = []
        for ext in (".dwg", ".dxf", ".pdf", ".txt"):
            matches.extend(sorted(p for p in cad_root.rglob(f"*{ext}") if asset_id.upper() in p.name.upper()))
        self.related_files = sorted(matches)
        self.file_summary_label.setText(f"{asset_id}: {len(self.related_files)} related file(s)")
        for path in self.related_files:
            item = QListWidgetItem(f"{path.name}    [{path.suffix.lower() or 'file'}]")
            item.setData(Qt.UserRole, str(path))
            self.file_list.addItem(item)
        if self.file_list.count():
            self.file_list.setCurrentRow(0)
        else:
            self.file_preview.setPlainText("No related files found for the selected asset.")

    def _on_file_selection_changed(self, current: QListWidgetItem, previous: QListWidgetItem):
        path = Path(current.data(Qt.UserRole)) if current and current.data(Qt.UserRole) else None
        self._preview_file(path)

    def _toggle_file_preview(self, checked: bool):
        self.file_preview.setVisible(checked)
        current = self.file_list.currentItem()
        if checked and current is not None:
            path = Path(current.data(Qt.UserRole)) if current.data(Qt.UserRole) else None
            self._preview_file(path)

    def _preview_file(self, path):
        if path is None:
            self.file_preview.clear()
            return
        if not self.preview_toggle.isChecked():
            return

        details = [
            f"Name: {path.name}",
            f"Path: {path}",
        ]
        try:
            stat = path.stat()
            details.append(f"Size: {stat.st_size} bytes")
        except OSError as exc:
            self.file_preview.setPlainText(f"Failed to read file details: {exc}")
            return

        text_suffixes = {".txt", ".csv", ".log", ".yaml", ".yml", ".py"}
        if path.suffix.lower() in text_suffixes:
            try:
                preview_text = path.read_text(encoding="utf-8", errors="replace")[:4000]
                self.file_preview.setPlainText("\n".join(details) + "\n\nPreview:\n" + preview_text)
                return
            except OSError as exc:
                details.append(f"Preview unavailable: {exc}")

        if path.suffix.lower() == ".pdf":
            details.append("Preview: PDF preview not rendered in-app yet. Use right-click to open.")
        elif path.suffix.lower() in {".dwg", ".dxf"}:
            details.append("Preview: CAD preview not rendered in-app yet. Use right-click to open.")
        else:
            details.append("Preview: No inline preview available for this file type.")
        self.file_preview.setPlainText("\n".join(details))

    def _show_file_context_menu(self, position):
        item = self.file_list.itemAt(position)
        if item is None:
            return
        path_text = item.data(Qt.UserRole)
        if not path_text:
            return
        path = Path(path_text)

        menu = QMenu(self)
        open_action = QAction("Open File", self)
        reveal_action = QAction("Show in Explorer", self)
        copy_action = QAction("Copy Path", self)
        open_action.triggered.connect(lambda: self._open_file(path))
        reveal_action.triggered.connect(lambda: self._reveal_file(path))
        copy_action.triggered.connect(lambda: QApplication.clipboard().setText(str(path)))
        menu.addAction(open_action)
        menu.addAction(reveal_action)
        menu.addAction(copy_action)
        menu.exec(self.file_list.mapToGlobal(position))

    def _open_file(self, path: Path):
        if not path.exists():
            QMessageBox.warning(self, "Warning", f"File not found: {path}")
            return
        os.startfile(str(path))

    def _reveal_file(self, path: Path):
        if not path.exists():
            QMessageBox.warning(self, "Warning", f"File not found: {path}")
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(path.parent)))

    def _run_batch(self):
        """Run batch processing."""
        csv_path = self.csv_path_edit.text()
        cad_root = self.cad_root_edit.text()

        if not csv_path or not cad_root:
            QMessageBox.warning(self, "Warning", "Please select CSV file and CAD root directory.")
            return

        selected_assets = self._get_selected_assets()
        if not selected_assets:
            QMessageBox.warning(self, "Warning", "No assets selected.")
            return

        exclusions = self._get_excluded_assets()

        self._log(f"Starting batch with {len(selected_assets)} assets...")
        self._log(f"Exclusions: {exclusions}")
        self._log(f"Dry run: {self.dry_run_checkbox.isChecked()}")

        # Disable UI during run
        self.run_btn.setEnabled(False)
        self.load_assets_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate

        # Start worker thread
        self.worker = BatchWorker(
            csv_path=csv_path,
            cad_root=cad_root,
            exclusions=exclusions,
            dry_run=self.dry_run_checkbox.isChecked()
        )
        self.worker.log_signal.connect(self._log)
        self.worker.finished_signal.connect(self._on_batch_finished)
        self.worker.error_signal.connect(self._on_batch_error)
        self.worker.start()

    def _on_batch_finished(self, results: dict):
        """Handle batch completion."""
        self.progress_bar.setVisible(False)
        self.run_btn.setEnabled(True)
        self.load_assets_btn.setEnabled(True)

        self._log(f"Batch complete: {results}")
        QMessageBox.information(
            self, "Complete",
            f"Batch complete!\nProcessed: {results['processed']}\nFailed: {results['failed']}"
        )

    def _on_batch_error(self, error: str):
        """Handle batch error."""
        self.progress_bar.setVisible(False)
        self.run_btn.setEnabled(True)
        self.load_assets_btn.setEnabled(True)

        self._log(f"Error: {error}")
        QMessageBox.critical(self, "Error", f"Batch failed: {error}")

    def _log(self, message: str):
        """Append message to log text area."""
        self.log_text.append(message)


def main():
    """Main entry point for GUI."""
    app = QApplication(sys.argv)
    window = ACADFixerGUI()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
