import os
from PySide6.QtWidgets import (
    QMainWindow, QSplitter, QFileDialog, QMessageBox, QStatusBar, QWidget, QVBoxLayout, QApplication,
)
from PySide6.QtCore import Qt, QModelIndex
from PySide6.QtGui import QFont, QShortcut, QKeySequence
from ui.controls_bar import ControlsBar
from ui.file_list_panel import FileListPanel
from ui.preview_panel import PreviewPanel
from ui.dialogs import FuzzyMatchDialog, SearchDialog
from services.worker import ParseWorker, FolderScanWorker
from services.csv_exporter import export_csv, export_inspection_freq_csv
from services.entity_info import build_entity_info_rows
from services.excel_writer import write_back_changes, write_back_ta_changes, write_back_entity_changes
from services.thickness_activity import build_thickness_activity_view
from services.excel_parser import parse_excel_file, extract_inspection_date
from services.transformer import transform_rows
from services.session import save_session, load_session
from services.traveler_parser import parse_traveler
from models.cml_row import CMLRow, EntityInfoRow


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CML Batch Builder — Aware CML Table Import CSV Generator")
        self.resize(1400, 850)
        self._worker = None
        self._scan_worker = None
        self._all_rows: list[CMLRow] = []
        self._entity_rows: list[EntityInfoRow] = []
        self._all_errors: list[str] = []
        self._entity_errors: list[str] = []
        self._pending_export = False
        self._pending_info_build = False
        self._current_mode = "CML Import"
        self._ta_parse_cache: dict[str, tuple[list, list[str]]] = {}  # file_path -> (rows, errors)
        self._traveler_data: dict[str, dict[str, str]] | None = None
        self._traveler_path: str = ""
        self._zoom_factor: float = 1.0
        self._setup_ui()
        self._connect_signals()
        self._auto_load_last_session()

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # controls bar at top
        self.controls = ControlsBar()
        main_layout.addWidget(self.controls)

        # splitter: file list (left) + preview (right)
        self.splitter = QSplitter(Qt.Horizontal)
        self.file_panel = FileListPanel()
        self.preview_panel = PreviewPanel()
        self.splitter.addWidget(self.file_panel)
        self.splitter.addWidget(self.preview_panel)
        self.splitter.setStretchFactor(0, 2)
        self.splitter.setStretchFactor(1, 3)
        main_layout.addWidget(self.splitter, 1)

        # status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready. Drag & drop files or use Add Files / Add Folder.")

        # Ctrl+0 to reset zoom
        reset_zoom = QShortcut(QKeySequence("Ctrl+0"), self)
        reset_zoom.activated.connect(self._reset_zoom)

    def _connect_signals(self):
        self.controls.add_files_clicked.connect(self._on_add_files)
        self.controls.add_folder_clicked.connect(self._on_add_folder)
        self.controls.paste_entities_clicked.connect(self._on_paste_entities)
        self.controls.search_clicked.connect(self._on_search)
        self.controls.validate_clicked.connect(self._on_validate)
        self.controls.build_info_pages_clicked.connect(self._on_build_info_pages)
        self.controls.export_clicked.connect(self._on_export)
        self.controls.update_sheets_clicked.connect(self._on_update_sheets)
        self.controls.clear_clicked.connect(self._on_clear)
        self.controls.cancel_clicked.connect(self._on_cancel)
        self.file_panel.files_changed.connect(self._update_status)
        self.file_panel.folder_dropped.connect(self._scan_folder)
        self.file_panel.traveler_dropped.connect(self._load_traveler_from_path)
        self.controls.mode_changed.connect(self._on_mode_changed)
        self.file_panel.file_selected.connect(self._on_file_selected)
        self.controls.copy_table_clicked.connect(self._on_copy_current_table)
        self.controls.save_session_clicked.connect(self._on_save_session)
        self.controls.load_session_clicked.connect(self._on_load_session)
        self.controls.deadleg_changed.connect(self._on_deadleg_changed)
        self.controls.load_traveler_clicked.connect(self._on_load_traveler)
        self.controls.clear_traveler_clicked.connect(self._on_clear_traveler)

    # --- file acquisition ---

    def _on_add_files(self):
        from PySide6.QtCore import QSettings
        settings = QSettings("CMLBatchBuilder", "AwareImport")
        last_dir = settings.value("add_files_folder", "", type=str)
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select UT Excel Files", last_dir,
            "Excel Files (*.xlsx *.xlsm);;All Files (*)",
        )
        if files:
            settings.setValue("add_files_folder", os.path.dirname(files[0]))
            self.file_panel.add_files(files)

    def _on_add_folder(self):
        from PySide6.QtCore import QSettings
        settings = QSettings("CMLBatchBuilder", "AwareImport")
        last_dir = settings.value("add_folder_folder", "", type=str)
        folder = QFileDialog.getExistingDirectory(self, "Select Parent Folder", last_dir)
        if folder:
            settings.setValue("add_folder_folder", folder)
            self._scan_folder(folder)

    def _scan_folder(self, folder: str):
        if self._scan_worker and self._scan_worker.isRunning():
            return
        self.controls.set_processing(True)
        self.status_bar.showMessage(f"Scanning {folder}...")
        self._scan_worker = FolderScanWorker(folder)
        self._scan_worker.files_found.connect(self._on_scan_progress)
        self._scan_worker.scan_done.connect(self._on_scan_done)
        self._scan_worker.cancelled.connect(self._on_cancelled)
        self._scan_worker.start()

    def _on_scan_progress(self, count: int):
        self.status_bar.showMessage(f"Scanning... {count} Excel files found so far")

    def _on_scan_done(self, files: list):
        self.controls.set_processing(False)
        if files:
            self.file_panel.add_files(files)
            self.status_bar.showMessage(f"Found {len(files)} Excel files")
        else:
            self.status_bar.showMessage("No Excel files found")

    def _on_paste_entities(self):
        dlg = FuzzyMatchDialog(self)
        if dlg.exec() and dlg.matched_files:
            self.file_panel.add_files(dlg.matched_files)
            self.status_bar.showMessage(f"Added {len(dlg.matched_files)} matched files")

    def _on_search(self):
        dlg = SearchDialog(self)
        if dlg.exec() and dlg.found_files:
            self.file_panel.add_files(dlg.found_files)
            self.status_bar.showMessage(f"Added {len(dlg.found_files)} files from search")

    # --- processing ---

    def _on_validate(self):
        entries = self.file_panel.get_entries()
        if not entries:
            QMessageBox.information(self, "No Files", "Add files to the list first.")
            return
        self._run_processing()

    def _run_processing(self):
        entries = self.file_panel.get_entries()
        if not entries:
            return

        system_path = self.controls.get_system_path()
        standard_style = self.controls.is_standard_style()

        self.controls.set_processing(True)
        self._all_rows = []
        self._entity_rows = []
        self._all_errors = []
        self._entity_errors = []

        self._worker = ParseWorker(entries, system_path, standard_style)
        self._worker.progress.connect(self._on_progress)
        self._worker.file_done.connect(self._on_file_done)
        self._worker.finished_all.connect(self._on_finished)
        self._worker.cancelled.connect(self._on_cancelled)
        self._worker.start()

    def _make_progress_cb(self, label: str):
        """Return a callback(current, total) that updates the progress bar and status bar."""
        def _cb(current: int, total: int):
            self.controls.set_progress(current, total)
            self.status_bar.showMessage(f"{label} {current} of {total}...")
            QApplication.processEvents()
        return _cb

    def _on_progress(self, current: int, total: int):
        self.controls.set_progress(current, total)
        self.status_bar.showMessage(f"Processing file {current} of {total}...")

    def _on_file_done(self, file_path: str, row_count: int, error: str, system_name: str):
        if error:
            self.file_panel.model.update_entry(file_path, "Error", 0, error)
        else:
            self.file_panel.model.update_entry(file_path, "Parsed", row_count, system_name=system_name)

    def _on_finished(self, rows: list, errors: list):
        self._all_rows = rows
        self._all_errors = errors
        if self.controls.is_deadleg():
            self._apply_deadleg(True)
        self.controls.set_processing(False)
        self.preview_panel.set_data(rows, errors)

        parsed = sum(1 for e in self.file_panel.get_entries() if e.status == "Parsed")
        failed = sum(1 for e in self.file_panel.get_entries() if e.status == "Error")
        self.status_bar.showMessage(
            f"Done. Files: {parsed} parsed, {failed} failed. "
            f"Rows: {len(rows)} extracted (after dedup)."
        )

        # if export was pending, trigger it now
        if self._pending_export:
            self._pending_export = False
            if self._all_rows:
                self._do_export()

        if self._pending_info_build:
            self._pending_info_build = False
            self._build_info_pages_from_rows()

    def _on_cancelled(self):
        self.controls.set_processing(False)
        self.status_bar.showMessage("Processing cancelled.")

    def _on_cancel(self):
        if self._scan_worker and self._scan_worker.isRunning():
            self._scan_worker.cancel()
        if self._worker and self._worker.isRunning():
            self._worker.cancel()

    # --- export ---

    def _on_export(self):
        if not self._all_rows:
            # run processing first if not done
            entries = self.file_panel.get_entries()
            if not entries:
                QMessageBox.information(self, "No Files", "Add files to the list first.")
                return
            # auto-validate then export
            self._pending_export = True
            self._run_processing()
            return

        self._do_export()

    def _do_export(self):
        from datetime import date
        default_name = f"Equip_CML_Import_{date.today().strftime('%m-%d-%Y')}.csv"
        path, _ = QFileDialog.getSaveFileName(
            self, "Export CSV", default_name,
            "CSV Files (*.csv);;All Files (*)",
        )
        if not path:
            return

        # Refresh system_path on every row using the *current* UI value
        # so the CSV always reflects the active System Path Parent.
        current_sys_path = self.controls.get_system_path()
        for row in self._all_rows:
            if current_sys_path and row.system_name:
                row.system_path = f"{current_sys_path} > {row.system_name}"
            elif current_sys_path:
                row.system_path = current_sys_path
        for erow in self._entity_rows:
            if current_sys_path and erow.system_name:
                erow.system_path = f"{current_sys_path} > {erow.system_name}"
            elif current_sys_path:
                erow.system_path = current_sys_path

        self.controls.set_processing(True)
        try:
            rows_written, errors = export_csv(
                self._all_rows, path, self._entity_rows,
                progress_callback=self._make_progress_cb("Exporting system"),
            )
        finally:
            self.controls.set_processing(False)
        if errors:
            QMessageBox.warning(self, "Export Errors", "\n".join(errors))
        else:
            self.status_bar.showMessage(f"Exported {rows_written} rows to {path}")
            msg = f"Successfully exported {rows_written} rows to:\n{path}"

            # Optional inspection frequency CSV (same output directory)
            if self.controls.is_insp_freq_export() and self._entity_rows:
                freq_path = self._build_insp_freq_path(path)
                freq_written, freq_errors = export_inspection_freq_csv(
                    self._entity_rows, freq_path,
                )
                # If the auto-derived path failed, let the user pick a name
                freq_real = [e for e in freq_errors if "manual/client" not in e]
                if freq_real:
                    fallback_path, _ = QFileDialog.getSaveFileName(
                        self, "Save Inspection Frequency CSV",
                        freq_path, "CSV Files (*.csv);;All Files (*)",
                    )
                    if fallback_path:
                        freq_path = fallback_path
                        freq_written, freq_errors = export_inspection_freq_csv(
                            self._entity_rows, freq_path,
                        )
                        freq_real = [e for e in freq_errors if "manual/client" not in e]
                # Separate real errors from informational warnings
                freq_warns = [e for e in freq_errors if "manual/client" in e]
                if freq_real:
                    msg += f"\n\nInspection Frequency CSV errors:\n" + "\n".join(freq_real)
                else:
                    msg += f"\n\nInspection Frequency CSV: {freq_written} rows to:\n{freq_path}"
                if freq_warns:
                    msg += "\n\nFrequency warnings:\n" + "\n".join(freq_warns)
            elif self.controls.is_insp_freq_export() and not self._entity_rows:
                msg += "\n\nInspection Frequency CSV skipped — run Build Info Pages first."

            QMessageBox.information(self, "Export Complete", msg)

    def _build_insp_freq_path(self, main_csv_path: str) -> str:
        """Derive the inspection frequency CSV path by replacing 'CML' with 'InspFreq' in the main filename."""
        output_dir = os.path.dirname(main_csv_path) or "."
        basename = os.path.basename(main_csv_path)
        if "CML" in basename:
            freq_name = basename.replace("CML", "InspFreq", 1)
        else:
            # Fallback if user removed 'CML' from the name entirely
            root, ext = os.path.splitext(basename)
            freq_name = f"{root}_InspFreq{ext}"
        return os.path.join(output_dir, freq_name)

    def _on_build_info_pages(self):
        if self._current_mode != "Info Page Builder":
            self.controls.mode_combo.setCurrentText("Info Page Builder")
        if not self._all_rows:
            entries = self.file_panel.get_entries()
            if not entries:
                QMessageBox.information(self, "No Files", "Add files to the list first.")
                return
            self._pending_info_build = True
            self._run_processing()
            return
        self._build_info_pages_from_rows()

    def _build_info_pages_from_rows(self):
        self.controls.set_processing(True)
        try:
            self._entity_rows, self._entity_errors = build_entity_info_rows(
                self._all_rows,
                pid_prefix=self.controls.get_pid_prefix(),
                progress_callback=self._make_progress_cb("Building entity"),
                traveler_data=self._traveler_data,
            )
        finally:
            self.controls.set_processing(False)
        if self.controls.is_deadleg():
            self._apply_deadleg_entity(True)
        self.preview_panel.set_entity_data(self._entity_rows, self._entity_errors)
        self.controls.mode_combo.setCurrentText("Info Page Builder")
        if self._entity_rows:
            flagged = sum(1 for row in self._entity_rows if row.warnings)
            self.status_bar.showMessage(
                f"Info Page Builder — built {len(self._entity_rows)} entity row(s); flagged {flagged}."
            )
        else:
            self.status_bar.showMessage("Info Page Builder — no entity rows built.")

    # --- traveler ---

    def _on_load_traveler(self):
        from PySide6.QtCore import QSettings
        settings = QSettings("CMLBatchBuilder", "AwareImport")
        last_dir = settings.value("traveler_folder", "", type=str)
        path, _ = QFileDialog.getOpenFileName(
            self, "Select API-570 Traveler Spreadsheet", last_dir,
            "Excel Files (*.xlsx *.xlsm);;All Files (*)",
        )
        if not path:
            return
        settings.setValue("traveler_folder", os.path.dirname(path))
        self._load_traveler_from_path(path)

    def _load_traveler_from_path(self, path: str):
        data, errors = parse_traveler(path)
        if errors:
            for e in errors:
                if "not found" in e.lower() or "no '" in e.lower() or "failed" in e.lower():
                    QMessageBox.warning(self, "Traveler Error", "\n".join(errors))
                    return
        self._traveler_data = data if data else None
        self._traveler_path = path if data else ""
        basename = os.path.basename(path)
        self.controls.set_traveler_label(basename if data else "")
        if data:
            self.status_bar.showMessage(
                f"Traveler loaded: {basename} — {len(data)} entities. "
                f"Click Build Info Pages to apply."
            )
        else:
            self.status_bar.showMessage(f"Traveler loaded but contained no entity rows: {basename}")

    def _on_clear_traveler(self):
        self._traveler_data = None
        self._traveler_path = ""
        self.controls.set_traveler_label("")
        self.status_bar.showMessage("Traveler removed.")

    # --- deadleg toggle ---

    _DEADLEG_SUFFIX = " Deadleg"

    def _on_deadleg_changed(self, checked: bool):
        """Toggle the ' Deadleg' suffix on every loaded row and refresh views."""
        self._apply_deadleg(checked)
        self._apply_deadleg_entity(checked)
        # Refresh whichever view is active
        if self._all_rows and self._current_mode == "CML Import":
            self.preview_panel.set_data(self._all_rows, self._all_errors)
        if self._entity_rows and self._current_mode == "Info Page Builder":
            self.preview_panel.set_entity_data(self._entity_rows, self._entity_errors)
        # Invalidate TA cache since system_name changed
        self._ta_parse_cache.clear()

    def _apply_deadleg(self, add: bool):
        """Append or strip ' Deadleg' on system_name / equipment_id of CMLRows."""
        suffix = self._DEADLEG_SUFFIX
        sys_path_parent = self.controls.get_system_path()
        for row in self._all_rows:
            if add:
                if row.system_name and not row.system_name.endswith(suffix):
                    row.system_name += suffix
                if row.equipment_id and not row.equipment_id.endswith(suffix):
                    row.equipment_id += suffix
            else:
                if row.system_name.endswith(suffix):
                    row.system_name = row.system_name[: -len(suffix)]
                if row.equipment_id.endswith(suffix):
                    row.equipment_id = row.equipment_id[: -len(suffix)]
            # Rebuild system_path to match
            if sys_path_parent and row.system_name:
                row.system_path = f"{sys_path_parent} > {row.system_name}"
            elif sys_path_parent:
                row.system_path = sys_path_parent

    def _apply_deadleg_entity(self, add: bool):
        """Append or strip ' Deadleg' on system_name / equipment_id of EntityInfoRows."""
        suffix = self._DEADLEG_SUFFIX
        sys_path_parent = self.controls.get_system_path()
        for row in self._entity_rows:
            if add:
                if row.system_name and not row.system_name.endswith(suffix):
                    row.system_name += suffix
                if row.equipment_id and not row.equipment_id.endswith(suffix):
                    row.equipment_id += suffix
            else:
                if row.system_name.endswith(suffix):
                    row.system_name = row.system_name[: -len(suffix)]
                if row.equipment_id.endswith(suffix):
                    row.equipment_id = row.equipment_id[: -len(suffix)]
            # Rebuild system_path to match
            if sys_path_parent and row.system_name:
                row.system_path = f"{sys_path_parent} > {row.system_name}"
            elif sys_path_parent:
                row.system_path = sys_path_parent

    # --- update sheets ---

    def _on_update_sheets(self):
        if self._current_mode == "Thickness Activity":
            model = self.preview_panel.ta_model
        elif self._current_mode == "Info Page Builder":
            model = self.preview_panel.entity_model
        else:
            model = self.preview_panel.model

        if not model.has_changes():
            QMessageBox.information(self, "No Changes", "No cells have been edited.")
            return

        rows = model.rows()
        changed = set(model.changed_cells())

        affected_files = set()
        for row_idx, _ in changed:
            if row_idx < len(rows):
                r = rows[row_idx]
                if isinstance(r, dict):
                    affected_files.add(os.path.basename(r.get("_source_file", "?")))
                else:
                    affected_files.add(os.path.basename(r.source_file))

        reply = QMessageBox.question(
            self, "Update Source Sheets",
            f"Write {len(changed)} changed cell(s) back to {len(affected_files)} file(s)?\n\n"
            + "\n".join(sorted(affected_files)),
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return

        self.controls.set_processing(True)
        try:
            progress_cb = self._make_progress_cb("Updating file")
            if self._current_mode == "Thickness Activity":
                errors = write_back_ta_changes(rows, changed, progress_callback=progress_cb)
            elif self._current_mode == "Info Page Builder":
                errors = write_back_entity_changes(rows, changed, progress_callback=progress_cb)
            else:
                errors = write_back_changes(rows, changed, progress_callback=progress_cb)
        finally:
            self.controls.set_processing(False)

        # Separate real errors from informational messages
        info_msgs = [e for e in errors if e.startswith("INFO:")]
        real_errors = [e for e in errors if not e.startswith("INFO:")]

        if real_errors:
            QMessageBox.warning(
                self, "Update Errors",
                f"{len(real_errors)} error(s):\n" + "\n".join(real_errors),
            )
        else:
            model.clear_changes()
            for cached_path in list(self._ta_parse_cache.keys()):
                if os.path.basename(cached_path) in affected_files:
                    self._ta_parse_cache.pop(cached_path, None)
            msg = f"Updated {len(changed)} cell(s) in {len(affected_files)} file(s)."
            if info_msgs:
                msg += "\n\n" + "\n".join(info_msgs)
            self.status_bar.showMessage(
                f"Successfully updated {len(changed)} cell(s) in {len(affected_files)} file(s)"
            )
            QMessageBox.information(self, "Update Complete", msg)

    # --- mode switching ---

    def _on_mode_changed(self, mode: str):
        self._current_mode = mode
        if mode != "Thickness Activity":
            self.controls.set_inspection_date("")
        self.controls.set_mode_ui(mode)
        self.preview_panel.set_mode(mode)
        if mode == "Thickness Activity":
            self.status_bar.showMessage("Thickness Activity mode — click a file to view.")
        elif mode == "Info Page Builder":
            if self._entity_rows:
                self.preview_panel.set_entity_data(self._entity_rows, self._entity_errors)
                self.status_bar.showMessage(
                    f"Info Page Builder mode — {len(self._entity_rows)} entity row(s) loaded."
                )
            else:
                self.status_bar.showMessage("Info Page Builder mode — click Build Info Pages to create entity rows.")
        else:
            if self._all_rows:
                self.preview_panel.set_data(self._all_rows, self._all_errors)
                self.status_bar.showMessage(
                    f"CML Import mode — {len(self._all_rows)} rows loaded."
                )
            else:
                self.status_bar.showMessage("CML Import mode.")

    def _on_file_selected(self, file_path: str):
        if self._current_mode != "Thickness Activity":
            return

        cached = self._ta_parse_cache.get(file_path)
        if cached is not None:
            parsed_rows, parse_errors = cached
        else:
            self.status_bar.showMessage(f"Parsing {os.path.basename(file_path)}...")
            QApplication.processEvents()
            parsed_rows, _sys_name, parse_errors = parse_excel_file(file_path)
            sys_path = self.controls.get_system_path()
            std_style = self.controls.is_standard_style()
            parsed_rows = transform_rows(parsed_rows, sys_path, std_style)
            self._ta_parse_cache[file_path] = (parsed_rows, parse_errors)

        ta_rows, ta_errors = build_thickness_activity_view(parsed_rows)

        # --- CML vs Thickness row count comparison ---
        # The CML Import table and Thickness Activity table are derived from the
        # same source, so they should always have the same number of rows.
        # Count CML rows that have a non-blank location (same filter as TA builder).
        cml_location_count = sum(1 for r in parsed_rows if r.cml_location)
        ta_count = len(ta_rows)
        count_mismatch_errors: list[str] = []
        if cml_location_count != ta_count:
            count_mismatch_errors.append(
                f"⚠ Row count mismatch: CML Import has {cml_location_count} location row(s) "
                f"but Thickness Activity has {ta_count} row(s). "
                f"Some CMLs may be missing from one table — check source data."
            )

        all_errors = parse_errors + ta_errors + count_mismatch_errors
        self.preview_panel.set_thickness_data(ta_rows, all_errors)

        insp_date = extract_inspection_date(file_path)
        self.controls.set_inspection_date(insp_date)

        basename = os.path.basename(file_path)
        if ta_rows:
            msg = f"Thickness Activity — {basename}: {len(ta_rows)} rows"
            if ta_errors:
                msg += f"  |  {len(ta_errors)} DATA ERROR(s)"
            self.status_bar.showMessage(msg)
        elif all_errors:
            self.status_bar.showMessage(
                f"Thickness Activity — {basename}: {len(all_errors)} error(s)"
            )
        else:
            self.status_bar.showMessage(
                f"Thickness Activity — {basename}: no rows found"
            )

    def _on_copy_current_table(self):
        model = self.preview_panel._active_model()
        rows = model.rows()
        if not rows:
            self.status_bar.showMessage("Nothing to copy — no table data loaded.")
            return

        columns = model.COLUMNS
        lines = []
        for row_idx, row in enumerate(rows):
            if isinstance(row, dict):
                vals = [str(row.get(col, "")) for col in columns]
            else:
                vals = [str(model.data(model.index(row_idx, col_idx), Qt.DisplayRole) or "") for col_idx, _ in enumerate(columns)]
            lines.append("\t".join(vals))

        QApplication.clipboard().setText("\n".join(lines))
        self.status_bar.showMessage(f"Copied {len(rows)} row(s) to clipboard.")

    # --- session save / load ---

    def _on_save_session(self):
        from PySide6.QtCore import QSettings
        settings = QSettings("CMLBatchBuilder", "AwareImport")
        last_dir = settings.value("session_folder", "", type=str)
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Session", os.path.join(last_dir, "session.json") if last_dir else "session.json",
            "Session Files (*.json);;All Files (*)",
        )
        if not path:
            return
        settings.setValue("session_folder", os.path.dirname(path))
        try:
            save_session(
                path,
                entries=self.file_panel.get_entries(),
                all_rows=self._all_rows,
                entity_rows=self._entity_rows,
                all_errors=self._all_errors,
                entity_errors=self._entity_errors,
                system_path=self.controls.get_system_path(),
                pid_prefix=self.controls.get_pid_prefix(),
                standard_style=self.controls.is_standard_style(),
                current_mode=self._current_mode,
                deadleg=self.controls.is_deadleg(),
                traveler_path=self._traveler_path,
            )
            settings.setValue("last_session_path", path)
            self.status_bar.showMessage(f"Session saved to {path}")
        except Exception as e:
            QMessageBox.warning(self, "Save Session Failed", str(e))

    def _on_load_session(self):
        from PySide6.QtCore import QSettings
        settings = QSettings("CMLBatchBuilder", "AwareImport")
        last_dir = settings.value("session_folder", "", type=str)
        path, _ = QFileDialog.getOpenFileName(
            self, "Load Session", last_dir,
            "Session Files (*.json);;All Files (*)",
        )
        if not path:
            return
        settings.setValue("session_folder", os.path.dirname(path))
        self._restore_session(path)

    def _auto_load_last_session(self):
        from PySide6.QtCore import QSettings
        settings = QSettings("CMLBatchBuilder", "AwareImport")
        last_path = settings.value("last_session_path", "", type=str)
        if last_path and os.path.isfile(last_path):
            self._restore_session(last_path, quiet=True)

    def _restore_session(self, path: str, quiet: bool = False):
        try:
            data = load_session(path)
        except Exception as e:
            if not quiet:
                QMessageBox.warning(self, "Load Session Failed", str(e))
            return

        self.file_panel.clear()
        self.preview_panel.clear()
        self._all_rows = []
        self._entity_rows = []
        self._all_errors = []
        self._entity_errors = []
        self._ta_parse_cache.clear()
        self._traveler_data = None
        self._traveler_path = ""
        self.controls.set_traveler_label("")
        self.controls.set_inspection_date("")

        self.controls.system_path_input.setText(data["system_path"])
        self.controls.pid_prefix_input.setText(data.get("pid_prefix", ""))
        self.controls.cml_style_checkbox.setChecked(data["standard_style"])
        self.controls.deadleg_checkbox.setChecked(data.get("deadleg", False))

        entries = data["entries"]
        if entries:
            model = self.file_panel.model
            model.beginInsertRows(QModelIndex(), 0, len(entries) - 1)
            model._entries = entries
            model.endInsertRows()
            model.refresh_existence()

        self._all_rows = data["all_rows"]
        self._entity_rows = data.get("entity_rows", [])
        self._all_errors = data["all_errors"]
        self._entity_errors = data.get("entity_errors", [])
        if self._all_rows:
            self.preview_panel.set_data(self._all_rows, self._all_errors)
        if self._entity_rows:
            self.preview_panel.set_entity_data(self._entity_rows, self._entity_errors)

        mode = data["current_mode"]
        self.controls.mode_combo.setCurrentText(mode)
        self._current_mode = mode

        # Restore traveler if path is still valid
        traveler_path = data.get("traveler_path", "")
        if traveler_path and os.path.isfile(traveler_path):
            self._load_traveler_from_path(traveler_path)
        else:
            self._traveler_data = None
            self._traveler_path = ""
            self.controls.set_traveler_label("")

        from PySide6.QtCore import QSettings
        QSettings("CMLBatchBuilder", "AwareImport").setValue("last_session_path", path)

        file_count = len(entries)
        row_count = len(self._all_rows)
        self.status_bar.showMessage(
            f"Session restored: {file_count} file(s), {row_count} parsed row(s)  —  {path}"
        )

    # --- clear ---

    def _on_clear(self):
        self.file_panel.clear()
        self.preview_panel.clear()
        self._all_rows = []
        self._entity_rows = []
        self._all_errors = []
        self._entity_errors = []
        self._ta_parse_cache.clear()
        self._traveler_data = None
        self._traveler_path = ""
        self.controls.set_traveler_label("")
        self.controls.set_inspection_date("")
        self.status_bar.showMessage("List cleared.")

    # --- zoom ---

    _ZOOM_MIN = 0.5
    _ZOOM_MAX = 2.5
    _ZOOM_STEP = 0.1

    def wheelEvent(self, event):
        if event.modifiers() & Qt.ControlModifier:
            delta = event.angleDelta().y()
            if delta > 0:
                self._zoom_factor = min(self._ZOOM_MAX, self._zoom_factor + self._ZOOM_STEP)
            elif delta < 0:
                self._zoom_factor = max(self._ZOOM_MIN, self._zoom_factor - self._ZOOM_STEP)
            self._apply_zoom()
            event.accept()
            return
        super().wheelEvent(event)

    def _apply_zoom(self):
        from main import build_stylesheet, BASE_FONT_PT
        app = QApplication.instance()
        app.setStyleSheet(build_stylesheet(self._zoom_factor))
        scaled_pt = max(6, round(BASE_FONT_PT * self._zoom_factor))
        font = QFont("Segoe UI", scaled_pt)
        app.setFont(font)
        pct = round(self._zoom_factor * 100)
        self.status_bar.showMessage(f"Zoom: {pct}%")

    def _reset_zoom(self):
        self._zoom_factor = 1.0
        self._apply_zoom()

    # --- status ---

    def _update_status(self):
        count = len(self.file_panel.get_entries())
        self.status_bar.showMessage(f"{count} file(s) in list.")
