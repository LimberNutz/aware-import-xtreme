import os
import threading

from PySide6.QtCore import QThread, Signal
from models.cml_row import CMLRow, FileEntry
from services.excel_parser import parse_excel_file
from services.transformer import transform_rows
from services.aggregator import aggregate_rows
from app.constants import SUPPORTED_EXTENSIONS


class ParseWorker(QThread):
    # signals
    progress = Signal(int, int)        # (current, total)
    file_done = Signal(str, int, str, str)  # (file_path, row_count, error_or_empty, system_name)
    finished_all = Signal(list, list)  # (all_rows, all_errors)
    cancelled = Signal()

    def __init__(
        self,
        file_entries: list[FileEntry],
        system_path: str,
        standard_style: bool,
        parent=None,
    ):
        super().__init__(parent)
        self._file_entries = file_entries
        self._system_path = system_path
        self._standard_style = standard_style
        self._cancel_event = threading.Event()

    def cancel(self):
        self._cancel_event.set()

    def run(self):
        all_rows: list[CMLRow] = []
        all_errors: list[str] = []
        total = len(self._file_entries)

        for idx, entry in enumerate(self._file_entries):
            if self._cancel_event.is_set():
                self.cancelled.emit()
                return

            self.progress.emit(idx + 1, total)

            rows, system_name, errors = parse_excel_file(entry.file_path)

            if errors and not rows:
                all_errors.extend([f"[{entry.filename}] {e}" for e in errors])
                self.file_done.emit(entry.file_path, 0, "; ".join(errors), "")
            else:
                if errors:
                    all_errors.extend([f"[{entry.filename}] {e}" for e in errors])
                # apply system name override if user set one
                if entry.system_name:
                    for r in rows:
                        r.system_name = entry.system_name
                elif system_name:
                    for r in rows:
                        if not r.system_name:
                            r.system_name = system_name

                # transform
                rows = transform_rows(rows, self._system_path, self._standard_style)
                all_rows.extend(rows)
                # resolve the system name that was applied to rows
                resolved_name = entry.system_name or system_name or ""
                self.file_done.emit(entry.file_path, len(rows), "", resolved_name)

        # aggregate
        all_rows = aggregate_rows(all_rows)
        self.finished_all.emit(all_rows, all_errors)


class FolderScanWorker(QThread):
    # signals
    files_found = Signal(int)       # emitted periodically with count so far
    scan_done = Signal(list)        # list of file paths found
    cancelled = Signal()

    def __init__(self, folder: str, parent=None):
        super().__init__(parent)
        self._folder = folder
        self._cancel_event = threading.Event()

    def cancel(self):
        self._cancel_event.set()

    def run(self):
        results = []
        if not os.path.isdir(self._folder):
            self.scan_done.emit(results)
            return

        for dirpath, _dirnames, filenames in os.walk(self._folder):
            if self._cancel_event.is_set():
                self.cancelled.emit()
                return
            for fname in filenames:
                ext = os.path.splitext(fname)[1].lower()
                if ext in SUPPORTED_EXTENSIONS and not fname.startswith("~$"):
                    results.append(os.path.join(dirpath, fname))
            # emit progress every directory
            self.files_found.emit(len(results))

        self.scan_done.emit(sorted(results))
